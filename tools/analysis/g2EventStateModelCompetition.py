#!/usr/bin/env python3
"""Event-state diagnostics and held-out-seed G2 model competition.

M1: predict HF history from recorded shared/fragment initial state only.
M2: M1 plus one predeclared nonlinear TXE×TKE interaction.
M3: M2 plus LF history summaries (incremental opposite-fragment history).
M0: intercept-only baseline.

This is a predictive comparison, not a causal test. TKE is a nonrelativistic
proxy from stored fragment momenta and A*u masses; TXE is the sum of stored
initial fragment excitation energies. Both are derived conventional diagnostics.
"""
import argparse
import csv
import json
import math
import random
from pathlib import Path

SCHEMA = "cgmf.g2.mixed-history.v1"
U_MEV_C2 = 931.49410242
TARGETS = ["HF_neutron_count", "HF_neutron_total_E_lab_MeV",
           "HF_gamma_count", "HF_gamma_total_E_cm_MeV"]


def finite(x, label):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{label} must be finite")
    return float(x)


def norm(v):
    return math.sqrt(sum(x*x for x in v))


def load(path):
    events = {}
    for line_no, line in enumerate(path.open(encoding="utf-8"), 1):
        if not line.strip():
            raise ValueError(f"{path}:{line_no}: blank line")
        row = json.loads(line)
        if row.get("schema") != SCHEMA:
            raise ValueError(f"{path}:{line_no}: wrong schema")
        eid, side = row.get("event_id"), row.get("fragment_side")
        if isinstance(eid, bool) or not isinstance(eid, int) or eid < 1 or side not in ("LF", "HF"):
            raise ValueError(f"{path}:{line_no}: invalid event identity")
        pair = events.setdefault(eid, {})
        if side in pair:
            raise ValueError(f"{path}:{line_no}: duplicate side")
        pair[side] = row
    if not events:
        raise ValueError(f"{path}: no records")
    return events


def history(row):
    n = [t for t in row["transitions"] if t["particle_type"] == "neutron"]
    g = [t for t in row["transitions"] if t["particle_type"] == "gamma"]
    ic = sum(t["particle_type"] == "internal_conversion" for t in row["transitions"])
    en = [finite(t["neutron_kinematics"]["energy_lab_MeV"], "neutron Lab energy") for t in n]
    eg = [finite(t["energy_cm_MeV"], "gamma CM energy") for t in g]
    return [float(len(n)), sum(en), float(len(g)), sum(eg), float(ic)]



def read_seed_audit(jsonl_path, events):
    audit_path = jsonl_path.parent / "rng-audit.tsv"
    if not audit_path.is_file():
        raise ValueError(f"{jsonl_path}: missing sibling rng-audit.tsv; independent-seed validation requires audited seeds")
    with audit_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not reader.fieldnames or not {"event", "seed"}.issubset(reader.fieldnames):
            raise ValueError(f"{audit_path}: missing event/seed columns")
        rows = list(reader)
    mapping = {}
    for row in rows:
        try:
            event, seed = int(row["event"]), int(row["seed"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{audit_path}: malformed event/seed row") from exc
        if event in mapping or seed < 0:
            raise ValueError(f"{audit_path}: duplicate event or negative seed")
        mapping[event] = seed
    if set(mapping) != set(events):
        raise ValueError(f"{audit_path}: audited event IDs do not exactly match sidecar event IDs")
    seeds = list(mapping.values())
    if len(seeds) != len(set(seeds)):
        raise ValueError(f"{audit_path}: repeated RNG seeds within run")
    return set(seeds)


def contiguous_ranges(values):
    xs=sorted(values)
    if not xs: return []
    out=[]; start=prev=xs[0]
    for x in xs[1:]:
        if x==prev+1: prev=x
        else: out.append([start,prev]); start=prev=x
    out.append([start,prev])
    return out


def make_record(eid, sides, run_label, run_id):
    if set(sides) != {"LF", "HF"}:
        return None
    L, H = sides["LF"]["initial_fragment"], sides["HF"]["initial_fragment"]
    for side, x in (("LF", L), ("HF", H)):
        for k in ("A", "Z", "parity_index"):
            if isinstance(x.get(k), bool) or not isinstance(x.get(k), int):
                raise ValueError(f"event {eid}: invalid {side}.{k}")
        finite(x.get("excitation_MeV"), f"{side} excitation")
        finite(x.get("spin_stored"), f"{side} stored spin")
    pL = [finite(v, "LF momentum") for v in L["pre_fragment_momentum_MeV_c"]]
    pH = [finite(v, "HF momentum") for v in H["pre_fragment_momentum_MeV_c"]]
    if len(pL) != 3 or len(pH) != 3:
        raise ValueError(f"event {eid}: momentum must be 3-vectors")
    pLn, pHn = norm(pL), norm(pH)
    closure = norm([a+b for a,b in zip(pL,pH)])
    # Approximate rest masses as A*u; this is a diagnostic proxy only.
    tke_proxy = pLn*pLn/(2.0*L["A"]*U_MEV_C2) + pHn*pHn/(2.0*H["A"]*U_MEV_C2)
    txe = finite(L["excitation_MeV"], "LF excitation") + finite(H["excitation_MeV"], "HF excitation")
    asym = (L["excitation_MeV"]-H["excitation_MeV"])/(txe or 1.0)
    hx, hy = history(sides["LF"]), history(sides["HF"])
    # M1 controls recorded initial conditions on both fragments. M2 adds
    # shared energy-budget coordinates and their one physically motivated interaction.
    # M1 uses raw recorded state coordinates only. Magnitudes and closure are
    # retained as diagnostics, not duplicated as deterministic feature columns.
    m1 = [L["A"],L["Z"],H["A"],H["Z"],L["parity_index"],H["parity_index"],
          L["excitation_MeV"],H["excitation_MeV"],L["spin_stored"],H["spin_stored"],
          *pL,*pH]
    # TXE, TKE proxy and asymmetry are deterministic functions of M1 inputs.
    # Adding them as extra linear columns would duplicate information and alter
    # ridge regularization. The only new M2 basis term is the predeclared
    # nonlinear interaction TXE*TKE.
    m2 = m1 + [txe*tke_proxy]  # raw interaction; orthogonalized on training data in fit_predict
    return {
        "run": run_label, "run_id": run_id, "event_id": eid,
        "diagnostics": {"TXE_sum_initial_fragment_excitation_MeV":txe,
                        "TKE_nonrel_proxy_MeV":tke_proxy,
                        "momentum_closure_MeV_c":closure,
                        "p_L_MeV_c":pLn,"p_H_MeV_c":pHn},
        "m1": m1, "m2": m2, "energy_interaction_raw": txe*tke_proxy, "lf_history": hx,
        "target": hy[:4],
    }


def solve(A, b, ridge):
    n = len(b)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for i in range(n):
        M[i][i] += ridge
    for col in range(n):
        pivot = max(range(col,n), key=lambda r:abs(M[r][col]))
        if abs(M[pivot][col]) < 1e-12:
            M[pivot][col] += 1e-8
        M[col],M[pivot]=M[pivot],M[col]
        q=M[col][col]
        for j in range(col,n+1): M[col][j]/=q
        for r in range(n):
            if r==col: continue
            q=M[r][col]
            for j in range(col,n+1): M[r][j]-=q*M[col][j]
    return [M[i][n] for i in range(n)]


def fit_predict(train, test, model, ridge):
    if model == 0:
        Xtr=[[] for _ in train]; Xte=[[] for _ in test]
    elif model == 1:
        Xtr=[r["m1"] for r in train]; Xte=[r["m1"] for r in test]
    else:
        # Remove the component of TXE*TKE that is linearly predictable from
        # M1, using training data only. This isolates the added nonlinear basis
        # term and avoids crediting duplicate linear information to M2.
        base_tr=[r["m1"] for r in train]; base_te=[r["m1"] for r in test]
        p=len(base_tr[0])
        means=[sum(x[j] for x in base_tr)/len(base_tr) for j in range(p)]
        scales=[math.sqrt(sum((x[j]-means[j])**2 for x in base_tr)/len(base_tr)) or 1.0 for j in range(p)]
        Ztr=[[1.0]+[(x[j]-means[j])/scales[j] for j in range(p)] for x in base_tr]
        Zte=[[1.0]+[(x[j]-means[j])/scales[j] for j in range(p)] for x in base_te]
        gram=[[sum(z[i]*z[j] for z in Ztr) for j in range(p+1)] for i in range(p+1)]
        raw=[r["energy_interaction_raw"] for r in train]
        rhs=[sum(Ztr[n][i]*raw[n] for n in range(len(raw))) for i in range(p+1)]
        beta=solve(gram,rhs,1e-8)
        resid_tr=[raw[i]-sum(a*b for a,b in zip(Ztr[i],beta)) for i in range(len(train))]
        resid_te=[r["energy_interaction_raw"]-sum(a*b for a,b in zip(Zte[i],beta)) for i,r in enumerate(test)]
        Xtr=[]; Xte=[]
        for i,r in enumerate(train):
            v=r["m1"]+[resid_tr[i]]
            if model==3: v+=r["lf_history"]
            Xtr.append(v)
        for i,r in enumerate(test):
            v=r["m1"]+[resid_te[i]]
            if model==3: v+=r["lf_history"]
            Xte.append(v)
    p=len(Xtr[0]); q=len(TARGETS)
    means=[sum(x[j] for x in Xtr)/len(Xtr) for j in range(p)]
    scales=[]
    for j in range(p):
        s=math.sqrt(sum((x[j]-means[j])**2 for x in Xtr)/len(Xtr))
        scales.append(s if s>1e-10 else 1.0)
    Ztr=[[1.0]+[(x[j]-means[j])/scales[j] for j in range(p)] for x in Xtr]
    Zte=[[1.0]+[(x[j]-means[j])/scales[j] for j in range(p)] for x in Xte]
    ymeans=[sum(r["target"][k] for r in train)/len(train) for k in range(q)]
    yscales=[]
    for k in range(q):
        s=math.sqrt(sum((r["target"][k]-ymeans[k])**2 for r in train)/len(train))
        yscales.append(s if s>1e-10 else 1.0)
    predictions=[]
    for k in range(q):
        y=[(r["target"][k]-ymeans[k])/yscales[k] for r in train]
        gram=[[sum(z[i]*z[j] for z in Ztr) for j in range(p+1)] for i in range(p+1)]
        rhs=[sum(Ztr[n][i]*y[n] for n in range(len(y))) for i in range(p+1)]
        beta=solve(gram,rhs,ridge)
        predictions.append([sum(a*b for a,b in zip(z,beta))*yscales[k]+ymeans[k] for z in Zte])
    metrics={}
    rmses=[]
    event_loss=[[0.0 for _ in range(q)] for _ in test]
    for k,name in enumerate(TARGETS):
        err=[predictions[k][i]-test[i]["target"][k] for i in range(len(test))]
        rmse=math.sqrt(sum(e*e for e in err)/len(err))
        denom=math.sqrt(sum((r["target"][k]-ymeans[k])**2 for r in test)/len(test)) or 1.0
        metrics[name]={"RMSE":rmse,"train_SD_normalized_RMSE":rmse/yscales[k],"test_SD_normalized_RMSE":rmse/denom}
        rmses.append(rmse/yscales[k])
        for i,e in enumerate(err): event_loss[i][k] = (e/yscales[k])**2
    return {"targets":metrics,"mean_train_SD_normalized_RMSE":sum(rmses)/len(rmses),"_event_normalized_squared_error_by_target":event_loss}


def paired_bootstrap_deltas(results, comparisons, n_boot=2000, seed=20261119):
    rng = random.Random(seed)
    out = {}
    for model, base_model in comparisons:
        base = results[base_model]["_event_normalized_squared_error_by_target"]
        other = results[model]["_event_normalized_squared_error_by_target"]
        n = len(base)
        deltas = []
        for _ in range(n_boot):
            ids = [rng.randrange(n) for _ in range(n)]
            rmse0 = sum(math.sqrt(sum(base[i][k] for i in ids)/n) for k in range(len(TARGETS)))/len(TARGETS)
            rmse1 = sum(math.sqrt(sum(other[i][k] for i in ids)/n) for k in range(len(TARGETS)))/len(TARGETS)
            deltas.append(rmse1-rmse0)
        deltas.sort()
        point = sum(math.sqrt(sum(row[k] for row in other)/n) for k in range(len(TARGETS)))/len(TARGETS) - sum(math.sqrt(sum(row[k] for row in base)/n) for k in range(len(TARGETS)))/len(TARGETS)
        out[f"{model}_vs_{base_model}"] = {
            "delta_mean_train_SD_normalized_RMSE": point,
            "paired_event_bootstrap_95pct_CI": [deltas[int(0.025*n_boot)],deltas[min(n_boot-1,int(0.975*n_boot))]],
            "bootstrap_replicates":n_boot,"bootstrap_unit":"held-out complete LF/HF event pair"}
    return out


def validate_disjoint_seed_sets(train_seeds, test_seeds):
    overlap=set(train_seeds)&set(test_seeds)
    if overlap: raise ValueError(f"train/test RNG seed overlap: {sorted(overlap)[:20]}; independent seed holdout is invalid")

def validate_disjoint_runs(train_run_ids, test_run_ids):
    overlap = set(train_run_ids) & set(test_run_ids)
    if overlap:
        raise ValueError(f"train/test run_id overlap: {sorted(overlap)}; split by independent seeds")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train",nargs="+",required=True,help="training JSONL files; independent runs are pooled")
    ap.add_argument("--test",nargs="+",required=True,help="held-out JSONL files; never used for fitting")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--ridge",type=float,default=1.0)
    args=ap.parse_args()
    if args.ridge<=0: raise ValueError("ridge must be positive")
    train=[]; test=[]; diagnostics=[]
    split_run_ids={"train":set(),"test":set()}
    split_rng_seeds={"train":set(),"test":set()}
    for label,paths,dest in (("train",args.train,train),("test",args.test,test)):
        for raw in paths:
            path=Path(raw); ev=load(path); complete=0
            audited_seeds=read_seed_audit(path, ev)
            if split_rng_seeds[label] & audited_seeds:
                raise ValueError(f"{label}: overlapping RNG seeds across input runs; use disjoint audited seed ranges")
            split_rng_seeds[label].update(audited_seeds)
            run_label=None
            for eid,sides in sorted(ev.items()):
                if set(sides)!={"LF","HF"}: continue
                rid=sides["LF"].get("run_id")
                if run_label is None: run_label=rid
                if rid!=run_label or sides["HF"].get("run_id")!=rid:
                    raise ValueError(f"{path}: inconsistent run_id")
                r=make_record(eid,sides,path.stem,rid)
                dest.append(r); complete+=1
                if label=="test": diagnostics.append(r["diagnostics"])
            if complete==0: raise ValueError(f"{path}: no complete LF/HF events")
            if run_label in split_run_ids[label]: raise ValueError(f"{label}: duplicate run_id {run_label}; do not double-count a seed")
            split_run_ids[label].add(run_label)
    validate_disjoint_runs(split_run_ids["train"], split_run_ids["test"])
    validate_disjoint_seed_sets(split_rng_seeds["train"],split_rng_seeds["test"])
    if len(train)<20 or len(test)<20: raise ValueError("need at least 20 complete events in both train and test")
    # Model sizes are bounded by sample size; report, do not hide, feature count.
    results={}
    for model in (0,1,2,3):
        results[f"M{model}"]=fit_predict(train,test,model,args.ridge)
    bootstrap=paired_bootstrap_deltas(results, [("M1","M0"),("M2","M1"),("M3","M2")])
    for value in results.values(): value.pop("_event_normalized_squared_error_by_target",None)
    diag_keys=list(diagnostics[0])
    diag_summary={k:{"mean":sum(d[k] for d in diagnostics)/len(diagnostics),
                     "sd":math.sqrt(sum((d[k]-sum(x[k] for x in diagnostics)/len(diagnostics))**2 for d in diagnostics)/len(diagnostics))}
                  for k in diag_keys}
    output={"schema":"cgmf.g2.event-state-model-competition.v1",
      "train_files":[str(x) for x in args.train],"test_files":[str(x) for x in args.test],
      "n_train_events":len(train),"n_test_events":len(test),
      "train_run_ids":sorted(split_run_ids["train"]),"test_run_ids":sorted(split_run_ids["test"]),
      "train_rng_seed_ranges":contiguous_ranges(split_rng_seeds["train"]),
      "test_rng_seed_ranges":contiguous_ranges(split_rng_seeds["test"]),
      "ridge_lambda":args.ridge,
      "target_features":TARGETS,
      "models":{
        "M0":"intercept-only training-mean baseline",
        "M1":"recorded LF/HF initial state only (A/Z, parity, excitation, stored spin and raw momentum vectors); derived magnitudes/closure are diagnostics only",
        "M2":"M1 plus the training-residualized nonlinear TXE*TKE interaction; its linearly predictable component is removed using training data only",
        "M3":"M2 plus LF neutron/gamma/internal-conversion history summaries"},
      "results":results,"paired_event_bootstrap":bootstrap,
      "heldout_test_event_state_diagnostics":diag_summary,
      "relative_error_change_vs_M0":{m:(results[m]["mean_train_SD_normalized_RMSE"]/results["M0"]["mean_train_SD_normalized_RMSE"]-1.0) for m in ("M1","M2","M3")},
      "sequential_relative_error_change":{ "M2_vs_M1":results["M2"]["mean_train_SD_normalized_RMSE"]/results["M1"]["mean_train_SD_normalized_RMSE"]-1.0, "M3_vs_M2":results["M3"]["mean_train_SD_normalized_RMSE"]/results["M2"]["mean_train_SD_normalized_RMSE"]-1.0},
      "derived_quantity_definitions":{
        "TXE_sum_initial_fragment_excitation_MeV":"E*_L + E*_H from stored initial_fragment.excitation_MeV",
        "TKE_nonrel_proxy_MeV":"|p_L|^2/(2 A_L u) + |p_H|^2/(2 A_H u), u=931.49410242 MeV/c^2; approximate nonrelativistic diagnostic only",
        "momentum_closure_MeV_c":"|p_L + p_H| from stored pre-fragment momentum vectors"},
      "limitations":["TXE and TKE are derived conventional simulation diagnostics, not primitive 气论 state variables.",
        "TKE is a proxy using A*u masses; it is not a validated CGMF event TKE observable.",
        "M2 tests only the nonlinear component of TXE*TKE not linearly predictable from M1; TXE and TKE proxy are deterministic transforms of M1 inputs, not independent state observations.",
        "M3 incremental prediction does not prove direct LF-to-HF causation; omitted common causes remain.",
        "The split must be by disjoint audited RNG seeds, not merely distinct run_id labels or random events from one run.",
        "Linear ridge is a baseline model class; nonlinear model families require separate preregistration.",
        "Only complete event pairs are included; event_id is local to each input file."]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print(f"wrote {args.output}; train={len(train)} test={len(test)}")

if __name__=="__main__": main()

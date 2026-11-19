#!/usr/bin/env python3
"""Ablate LF/HF initial-state information on independent audited RNG seeds.

HF state includes A/Z plus parity, excitation, and stored spin. LF fields are
split into conserved-complement A/Z and intrinsic parity, excitation, spin.
Kinematic block remains separate because momentum vectors are constraint-linked.
All comparisons use fixed ridge lambda=1 and complete held-out LF/HF event pairs.
"""
import argparse
import csv
import json
import math
import random
from pathlib import Path

SCHEMA = "cgmf.g2.mixed-history.v1"
TARGETS = ["HF_neutron_count", "HF_neutron_total_E_lab_MeV",
           "HF_gamma_count", "HF_gamma_total_E_cm_MeV"]
RIDGE_DEFAULT = 1.0
BOOTSTRAP_DEFAULT = 2000
BOOTSTRAP_SEED_DEFAULT = 20261119


def load(path):
    events = {}
    with Path(path).open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
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


def read_seed_audit(jsonl_path, events):
    audit_path = Path(jsonl_path).parent / "rng-audit.tsv"
    if not audit_path.is_file():
        raise ValueError(f"{jsonl_path}: missing sibling rng-audit.tsv")
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


def make_record(eid, sides, run_label, run_id):
    L, H = sides["LF"]["initial_fragment"], sides["HF"]["initial_fragment"]
    for side, frag in (("LF", L), ("HF", H)):
        for key in ("A", "Z", "parity_index"):
            if isinstance(frag.get(key), bool) or not isinstance(frag.get(key), int):
                raise ValueError(f"event {eid}: invalid {side}.{key}")
        for key in ("excitation_MeV", "spin_stored"):
            if not isinstance(frag.get(key), (int, float)) or not math.isfinite(frag[key]):
                raise ValueError(f"event {eid}: invalid {side}.{key}")
        momentum = frag.get("pre_fragment_momentum_MeV_c")
        if not isinstance(momentum, list) or len(momentum) != 3:
            raise ValueError(f"event {eid}: invalid {side} momentum vector")
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in momentum):
            raise ValueError(f"event {eid}: non-finite {side} momentum component")
    ns = [t for t in sides["HF"].get("transitions", []) if t["particle_type"] == "neutron"]
    gs = [t for t in sides["HF"].get("transitions", []) if t["particle_type"] == "gamma"]
    target = [float(len(ns)),
              sum(float(t["neutron_kinematics"]["energy_lab_MeV"]) for t in ns),
              float(len(gs)), sum(float(t["energy_cm_MeV"]) for t in gs)]
    pL, pH = L["pre_fragment_momentum_MeV_c"], H["pre_fragment_momentum_MeV_c"]
    closure = math.sqrt(sum((float(a) + float(b)) ** 2 for a, b in zip(pL, pH)))
    return {
        "run": run_label, "run_id": run_id, "event_id": eid, "target": target,
        "diagnostics": {
            "TXE_sum_initial_fragment_excitation_MeV": float(L["excitation_MeV"] + H["excitation_MeV"]),
            "momentum_closure_MeV_c": closure,
        },
    }


def validate_disjoint_runs(train, test):
    overlap = set(train) & set(test)
    if overlap:
        raise ValueError(f"train/test run_id overlap: {sorted(overlap)}")


def validate_disjoint_seed_sets(train, test):
    overlap = set(train) & set(test)
    if overlap:
        raise ValueError(f"train/test RNG seed overlap: {sorted(overlap)[:20]}")


def local_state(fragment):
    """Full fragment state, retained for the HF conditioning block."""
    return [float(fragment[k]) for k in
            ("A", "Z", "parity_index", "excitation_MeV", "spin_stored")]


def lf_intrinsic_state(fragment):
    """LF-local state excluding A/Z, which are conserved complements."""
    return [float(fragment[k]) for k in ("parity_index", "excitation_MeV", "spin_stored")]


def lf_conserved_az(fragment):
    return [float(fragment[k]) for k in ("A", "Z")]


def read_split(paths):
    records, run_ids, seeds, diagnostics = [], set(), set(), []
    for raw_path in paths:
        path = Path(raw_path)
        events = load(path)
        audited = read_seed_audit(path, events)
        if seeds & audited:
            raise ValueError(f"{path}: overlapping audited RNG seeds within split")
        seeds.update(audited)
        run_id = None
        for eid, sides in sorted(events.items()):
            if set(sides) != {"LF", "HF"}:
                continue
            rid = sides["LF"].get("run_id")
            if run_id is None:
                run_id = rid
            if rid != run_id or sides["HF"].get("run_id") != rid:
                raise ValueError(f"{path}: inconsistent run_id")
            record = make_record(eid, sides, path.stem, rid)
            L, H = sides["LF"]["initial_fragment"], sides["HF"]["initial_fragment"]
            pL = [float(x) for x in L["pre_fragment_momentum_MeV_c"]]
            pH = [float(x) for x in H["pre_fragment_momentum_MeV_c"]]
            record.update({
                "L_full": local_state(L),
                "L_AZ": lf_conserved_az(L),
                "L_intrinsic": lf_intrinsic_state(L),
                "L_parity": [float(L["parity_index"])],
                "L_excitation": [float(L["excitation_MeV"])],
                "L_spin": [float(L["spin_stored"])],
                "H_local": local_state(H),
                "shared_kinematics": pL + pH,
            })
            records.append(record)
            diagnostics.append(record["diagnostics"])
        if run_id is None:
            raise ValueError(f"{path}: no complete LF/HF event pairs")
        if run_id in run_ids:
            raise ValueError(f"{path}: duplicate run_id {run_id}")
        run_ids.add(run_id)
    if not records:
        raise ValueError("split has no complete LF/HF event pairs")
    return records, run_ids, seeds, diagnostics


def solve(A, b, ridge):
    n = len(b)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for i in range(n):
        M[i][i] += ridge
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[pivot][col]) < 1e-12:
            M[pivot][col] += 1e-8
        M[col], M[pivot] = M[pivot], M[col]
        q = M[col][col]
        for j in range(col, n + 1):
            M[col][j] /= q
        for r in range(n):
            if r == col:
                continue
            q = M[r][col]
            for j in range(col, n + 1):
                M[r][j] -= q * M[col][j]
    return [M[i][n] for i in range(n)]


def fit_predict(train, test, feature_name, ridge=RIDGE_DEFAULT):
    Xtr = [r[feature_name] for r in train]
    Xte = [r[feature_name] for r in test]
    p, q = len(Xtr[0]), len(TARGETS)
    means = [sum(x[j] for x in Xtr) / len(Xtr) for j in range(p)]
    scales = []
    for j in range(p):
        s = math.sqrt(sum((x[j] - means[j]) ** 2 for x in Xtr) / len(Xtr))
        scales.append(s if s > 1e-10 else 1.0)
    Ztr = [[1.0] + [(x[j] - means[j]) / scales[j] for j in range(p)] for x in Xtr]
    Zte = [[1.0] + [(x[j] - means[j]) / scales[j] for j in range(p)] for x in Xte]
    ymeans = [sum(r["target"][k] for r in train) / len(train) for k in range(q)]
    yscales = []
    for k in range(q):
        s = math.sqrt(sum((r["target"][k] - ymeans[k]) ** 2 for r in train) / len(train))
        yscales.append(s if s > 1e-10 else 1.0)
    errors2, target_metrics, normalized_rmses = [[0.0] * q for _ in test], {}, []
    for k, target in enumerate(TARGETS):
        y = [(r["target"][k] - ymeans[k]) / yscales[k] for r in train]
        gram = [[sum(z[i] * z[j] for z in Ztr) for j in range(p + 1)] for i in range(p + 1)]
        rhs = [sum(Ztr[n][i] * y[n] for n in range(len(y))) for i in range(p + 1)]
        beta = solve(gram, rhs, ridge)
        pred = [sum(a * b for a, b in zip(z, beta)) * yscales[k] + ymeans[k] for z in Zte]
        err = [pred[i] - test[i]["target"][k] for i in range(len(test))]
        rmse = math.sqrt(sum(e * e for e in err) / len(err))
        normalized_rmses.append(rmse / yscales[k])
        target_metrics[target] = {"RMSE": rmse, "train_SD_normalized_RMSE": rmse / yscales[k]}
        for i, e in enumerate(err):
            errors2[i][k] = (e / yscales[k]) ** 2
    return {"mean_train_SD_normalized_RMSE": sum(normalized_rmses) / q,
            "targets": target_metrics, "_event_error2": errors2}


def mean_target_rmse(error2, indices):
    n, q = len(indices), len(TARGETS)
    return sum(math.sqrt(sum(error2[i][k] for i in indices) / n) for k in range(q)) / q


def paired_bootstrap_delta(candidate, reference, n_boot=BOOTSTRAP_DEFAULT,
                            seed=BOOTSTRAP_SEED_DEFAULT):
    """Return candidate-reference delta; negative values favor candidate."""
    A, B = candidate["_event_error2"], reference["_event_error2"]
    if len(A) != len(B):
        raise ValueError("paired bootstrap requires the same held-out event pairs")
    n = len(A)
    point = mean_target_rmse(A, list(range(n))) - mean_target_rmse(B, list(range(n)))
    rng, deltas = random.Random(seed), []
    for _ in range(n_boot):
        ids = [rng.randrange(n) for _ in range(n)]
        deltas.append(mean_target_rmse(A, ids) - mean_target_rmse(B, ids))
    deltas.sort()
    return {
        "delta_candidate_minus_reference": point,
        "paired_event_bootstrap_95pct_CI": [
            deltas[int(.025 * n_boot)], deltas[min(n_boot - 1, int(.975 * n_boot))]
        ],
        "bootstrap_replicates": n_boot,
        "bootstrap_unit": "held-out complete LF/HF event pair",
    }


def contiguous_ranges(values):
    xs = sorted(values)
    if not xs:
        return []
    out, start, prev = [], xs[0], xs[0]
    for x in xs[1:]:
        if x != prev + 1:
            out.append([start, prev])
            start = x
        prev = x
    out.append([start, prev])
    return out


def run(train_paths, test_paths, output, ridge=RIDGE_DEFAULT,
        n_boot=BOOTSTRAP_DEFAULT, bootstrap_seed=BOOTSTRAP_SEED_DEFAULT):
    train, train_runs, train_seeds, _ = read_split(train_paths)
    test, test_runs, test_seeds, diagnostics = read_split(test_paths)
    validate_disjoint_runs(train_runs, test_runs)
    validate_disjoint_seed_sets(train_seeds, test_seeds)
    if len(train) < 20 or len(test) < 20:
        raise ValueError("need at least 20 complete events in train and test")
    feature_builders = {
        "H_local": lambda r: r["H_local"],
        "L_AZ_only": lambda r: r["L_AZ"],
        "L_intrinsic_only": lambda r: r["L_intrinsic"],
        "H+L_AZ": lambda r: r["H_local"] + r["L_AZ"],
        "H+L_intrinsic": lambda r: r["H_local"] + r["L_intrinsic"],
        "H+L_parity": lambda r: r["H_local"] + r["L_parity"],
        "H+L_excitation": lambda r: r["H_local"] + r["L_excitation"],
        "H+L_spin": lambda r: r["H_local"] + r["L_spin"],
        "H_local+K": lambda r: r["H_local"] + r["shared_kinematics"],
        "H+L_intrinsic+K": lambda r: r["H_local"] + r["L_intrinsic"] + r["shared_kinematics"],
    }
    fits, models = {}, {}
    for name, builder in feature_builders.items():
        for record in train + test:
            record[name] = builder(record)
        fits[name] = fit_predict(train, test, name, ridge)
        models[name] = {
            "feature_count": len(train[0][name]),
            "mean_train_SD_normalized_RMSE": fits[name]["mean_train_SD_normalized_RMSE"],
            "targets": fits[name]["targets"],
        }
    comparisons = {
        "H+L_intrinsic_vs_H": paired_bootstrap_delta(fits["H+L_intrinsic"], fits["H_local"], n_boot, bootstrap_seed),
        "H+L_intrinsic+K_vs_H+K": paired_bootstrap_delta(fits["H+L_intrinsic+K"], fits["H_local+K"], n_boot, bootstrap_seed),
        "H+L_parity_vs_H": paired_bootstrap_delta(fits["H+L_parity"], fits["H_local"], n_boot, bootstrap_seed),
        "H+L_excitation_vs_H": paired_bootstrap_delta(fits["H+L_excitation"], fits["H_local"], n_boot, bootstrap_seed),
        "H+L_spin_vs_H": paired_bootstrap_delta(fits["H+L_spin"], fits["H_local"], n_boot, bootstrap_seed),
        "H+L_AZ_vs_H": paired_bootstrap_delta(fits["H+L_AZ"], fits["H_local"], n_boot, bootstrap_seed),
        "H_local+K_vs_H_local": paired_bootstrap_delta(fits["H_local+K"], fits["H_local"], n_boot, bootstrap_seed),
        "L_intrinsic_only_vs_H": paired_bootstrap_delta(fits["L_intrinsic_only"], fits["H_local"], n_boot, bootstrap_seed),
    }
    diag_keys = list(diagnostics[0])
    diag_summary = {
        k: {
            "mean": sum(d[k] for d in diagnostics) / len(diagnostics),
            "sd": math.sqrt(sum((d[k] - sum(x[k] for x in diagnostics) / len(diagnostics)) ** 2
                                for d in diagnostics) / len(diagnostics)),
        }
        for k in diag_keys
    }
    result = {
        "schema": "cgmf.g2.fragment-state-ablation.v2",
        "train_files": [str(x) for x in train_paths],
        "test_files": [str(x) for x in test_paths],
        "n_train_events": len(train), "n_test_events": len(test),
        "train_run_ids": sorted(train_runs), "test_run_ids": sorted(test_runs),
        "train_rng_seed_ranges": contiguous_ranges(train_seeds),
        "test_rng_seed_ranges": contiguous_ranges(test_seeds),
        "ridge_lambda": ridge, "bootstrap_replicates": n_boot, "bootstrap_seed": bootstrap_seed,
        "targets": TARGETS,
        "feature_groups": {
            "H_local": ["HF A", "HF Z", "HF parity_index", "HF excitation_MeV", "HF spin_stored"],
            "L_conserved_complement": ["LF A", "LF Z"],
            "L_intrinsic": ["LF parity_index", "LF excitation_MeV", "LF spin_stored"],
            "K": ["LF pre_fragment_momentum vector (3 components)", "HF pre_fragment_momentum vector (3 components)"],
        },
        "models": models, "paired_bootstrap_comparisons": comparisons,
        "heldout_event_state_diagnostics": diag_summary,
        "interpretation_limits": [
            "LF A/Z are reported as a separate conserved-complement block and are not counted as independent LF intrinsic information.",
            "Primary H+L_intrinsic versus H comparisons add only LF parity, excitation, and stored spin beyond the same HF state.",
            "Single-field LF additions are exploratory decomposition of the same predeclared feature groups, not independent confirmatory tests.",
            "K is a separate shared/constraint-related kinematic block, not an independent LF-to-HF mechanism.",
            "A predictive increment is conditional information/association, not direct cross-fragment causation; omitted common causes remain possible.",
            "TXE and TKE proxy are not included as separate features because they are deterministic transforms of the recorded state fields.",
            "All fits use training-only standardization, fixed ridge lambda, and no test-driven tuning.",
        ],
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for fit_result in fits.values():
        fit_result.pop("_event_error2", None)
    print(f"wrote {output}; train={len(train)} test={len(test)}; ridge={ridge}")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train", nargs="+", required=True)
    ap.add_argument("--test", nargs="+", required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--ridge", type=float, default=RIDGE_DEFAULT)
    ap.add_argument("--bootstrap", type=int, default=BOOTSTRAP_DEFAULT)
    ap.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED_DEFAULT)
    args = ap.parse_args()
    if args.ridge <= 0 or args.bootstrap < 100:
        raise ValueError("ridge must be positive and bootstrap count must be >=100")
    run(args.train, args.test, args.output, args.ridge, args.bootstrap, args.bootstrap_seed)


if __name__ == "__main__":
    main()

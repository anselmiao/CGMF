#!/usr/bin/env python3
"""Matched-pair conditional permutation for multivariate CGMF G2 histories."""
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

SCHEMA = "cgmf.g2.mixed-history.v1"
FEATURES = [
    "neutron_count", "neutron_mean_E_lab", "neutron_sd_E_lab",
    "neutron_max_E_lab", "neutron_total_E_lab", "neutron_mean_E_cm",
    "neutron_first_E_lab", "neutron_last_E_lab",
    "mean_cos_to_fragment_motion", "mean_cos2_to_fragment_motion",
    "gamma_count", "gamma_total_E_cm", "internal_conversion_count",
    "valid_timestamp_count",
]
COVARIATES = [
    "excitation_L_MeV", "excitation_H_MeV",
    "spin_L_stored", "spin_H_stored",
    "momentum_L_MeV_c", "momentum_H_MeV_c",
]


def finite(x, label):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{label} must be finite")
    return float(x)


def load_events(path):
    events = defaultdict(dict)
    for line_no, line in enumerate(path.open(encoding="utf-8"), 1):
        if not line.strip():
            raise ValueError(f"blank line {line_no}")
        row = json.loads(line)
        if row.get("schema") != SCHEMA:
            raise ValueError(f"line {line_no}: wrong schema")
        eid, side = row.get("event_id"), row.get("fragment_side")
        if not isinstance(eid, int) or isinstance(eid, bool) or eid < 1:
            raise ValueError(f"line {line_no}: invalid event id")
        if side not in ("LF", "HF") or side in events[eid]:
            raise ValueError(f"line {line_no}: invalid or duplicate side")
        initial, transitions = row.get("initial_fragment"), row.get("transitions")
        if not isinstance(initial, dict) or not isinstance(transitions, list):
            raise ValueError(f"line {line_no}: missing initial state/history")
        for k in ("A", "Z", "excitation_MeV", "spin_stored", "parity_index",
                  "pre_fragment_momentum_MeV_c"):
            if k not in initial:
                raise ValueError(f"line {line_no}: missing initial_fragment.{k}")
        if not isinstance(initial["A"], int) or not isinstance(initial["Z"], int):
            raise ValueError(f"line {line_no}: A/Z must be integers")
        finite(initial["excitation_MeV"], "excitation")
        finite(initial["spin_stored"], "spin")
        p = initial["pre_fragment_momentum_MeV_c"]
        if not isinstance(p, list) or len(p) != 3:
            raise ValueError(f"line {line_no}: invalid momentum vector")
        [finite(v, "momentum") for v in p]
        for i, tr in enumerate(transitions):
            if tr.get("emission_index") != i:
                raise ValueError(f"line {line_no}: transition order mismatch")
            if tr.get("particle_type") not in ("neutron", "gamma", "internal_conversion"):
                raise ValueError(f"line {line_no}: unsupported transition")
        events[eid][side] = row
    return events


def features(row):
    initial = row["initial_fragment"]
    p = [float(x) for x in initial["pre_fragment_momentum_MeV_c"]]
    pn = math.sqrt(sum(x*x for x in p))
    axis = [x/pn for x in p] if pn else [0.0, 0.0, 0.0]
    ns, gs = [], []
    ic = times = 0
    for tr in row["transitions"]:
        if tr.get("timestamp_valid") is True and "timestamp_s" in tr:
            times += 1
        kind = tr["particle_type"]
        if kind == "neutron":
            kin = tr.get("neutron_kinematics")
            if not isinstance(kin, dict):
                raise ValueError("neutron lacks kinematics")
            el = finite(kin.get("energy_lab_MeV"), "neutron Lab energy")
            ec = finite(kin.get("energy_cm_MeV"), "neutron CM energy")
            d = kin.get("direction_lab")
            if not isinstance(d, list) or len(d) != 3:
                raise ValueError("neutron direction must be a 3-vector")
            d = [finite(v, "direction") for v in d]
            dn = math.sqrt(sum(v*v for v in d))
            if abs(dn-1.0) > 1e-5:
                raise ValueError("neutron direction is not unit-normalized")
            ns.append((el, ec, sum(a*b for a,b in zip(axis,d))))
        elif kind == "gamma":
            gs.append(finite(tr.get("energy_cm_MeV"), "gamma energy"))
        else:
            ic += 1
    el = [n[0] for n in ns]
    ec = [n[1] for n in ns]
    co = [n[2] for n in ns]
    n = len(ns)
    mean = sum(el)/n if n else 0.0
    sd = math.sqrt(sum((x-mean)**2 for x in el)/n) if n else 0.0
    return [
        float(n), mean, sd, max(el, default=0.0), sum(el),
        sum(ec)/n if n else 0.0, el[0] if n else 0.0, el[-1] if n else 0.0,
        sum(co)/n if n else 0.0, sum(x*x for x in co)/n if n else 0.0,
        float(len(gs)), sum(gs), float(ic), float(times),
    ]


def build_records(events):
    records = []
    incomplete = 0
    for eid, sides in sorted(events.items()):
        if set(sides) != {"LF", "HF"}:
            incomplete += 1
            continue
        lf, hf = sides["LF"], sides["HF"]
        L, H = lf["initial_fragment"], hf["initial_fragment"]
        pL = math.sqrt(sum(float(x)**2 for x in L["pre_fragment_momentum_MeV_c"]))
        pH = math.sqrt(sum(float(x)**2 for x in H["pre_fragment_momentum_MeV_c"]))
        key = (L["A"], L["Z"], H["A"], H["Z"], L["parity_index"], H["parity_index"])
        cov = [
            float(L["excitation_MeV"]), float(H["excitation_MeV"]),
            float(L["spin_stored"]), float(H["spin_stored"]), pL, pH,
        ]
        records.append({
            "event_id": eid, "group": key, "cov": cov,
            "x": features(lf), "y": features(hf),
        })
    return records, incomplete


def greedy_pairs(records):
    if not records:
        return []
    d = len(COVARIATES)
    means = [sum(r["cov"][j] for r in records)/len(records) for j in range(d)]
    scales = []
    for j in range(d):
        var = sum((r["cov"][j]-means[j])**2 for r in records)/len(records)
        scales.append(math.sqrt(var) or 1.0)
    groups = defaultdict(list)
    for r in records:
        z = [(r["cov"][j]-means[j])/scales[j] for j in range(d)]
        r["z_cov"] = z
        groups[r["group"]].append(r)
    pairs = []
    for key, group in groups.items():
        candidates = []
        for i in range(len(group)):
            for j in range(i+1, len(group)):
                dist = math.sqrt(sum((a-b)**2 for a,b in zip(group[i]["z_cov"], group[j]["z_cov"]))/d)
                candidates.append((dist, group[i]["event_id"], group[j]["event_id"], i, j))
        candidates.sort()
        used = set()
        for dist, eid1, eid2, i, j in candidates:
            if i not in used and j not in used:
                pairs.append((dist, group[i], group[j]))
                used.add(i)
                used.add(j)
    return sorted(pairs, key=lambda p: (p[0], p[1]["event_id"], p[2]["event_id"]))


def test_pairs(pairs, caliper, permutations, seed):
    selected = [(d,a,b) for d,a,b in pairs if d <= caliper]
    if not selected:
        return {
            "caliper_standardized_rms": caliper, "matched_pairs": 0,
            "matched_events": 0, "omnibus_statistic": None,
            "permutation_p_upper_tail": None,
        }
    m = len(FEATURES)
    dx = [[a["x"][j]-b["x"][j] for j in range(m)] for _,a,b in selected]
    dy = [[a["y"][j]-b["y"][j] for j in range(m)] for _,a,b in selected]
    sx = [math.sqrt(sum(row[j]**2 for row in dx)/len(dx)) or 1.0 for j in range(m)]
    sy = [math.sqrt(sum(row[j]**2 for row in dy)/len(dy)) or 1.0 for j in range(m)]
    dx = [[row[j]/sx[j] for j in range(m)] for row in dx]
    dy = [[row[j]/sy[j] for j in range(m)] for row in dy]

    def statistic(yrows):
        total = 0.0
        n = len(dx)
        for i in range(m):
            for j in range(m):
                c = sum(dx[k][i]*yrows[k][j] for k in range(n))/n
                total += c*c
        return total

    observed = statistic(dy)
    rng = random.Random(seed)
    extreme = 0
    for _ in range(permutations):
        yp = [[v if rng.random() < 0.5 else -v for v in row] for row in dy]
        if statistic(yp) >= observed:
            extreme += 1
    distances = [d for d,_,_ in selected]
    feature_corr = []
    for i, name_x in enumerate(FEATURES):
        xs = [row[i] for row in dx]
        for j, name_y in enumerate(FEATURES):
            ys = [row[j] for row in dy]
            mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
            vx = sum((v-mx)**2 for v in xs)
            vy = sum((v-my)**2 for v in ys)
            if vx > 0 and vy > 0:
                corr = sum((a-mx)*(b-my) for a,b in zip(xs,ys))/math.sqrt(vx*vy)
                feature_corr.append((abs(corr), corr, name_x, name_y))
    feature_corr.sort(reverse=True)
    return {
        "caliper_standardized_rms": caliper,
        "matched_pairs": len(selected),
        "matched_events": 2*len(selected),
        "unmatched_complete_events": None,
        "median_match_distance": sorted(distances)[len(distances)//2],
        "maximum_match_distance": max(distances),
        "omnibus_statistic": observed,
        "permutation_p_upper_tail": (1+extreme)/(1+permutations),
        "top_absolute_feature_correlations": [
            {"LF_feature_difference": a, "HF_feature_difference": b, "correlation": r}
            for _, r, a, b in feature_corr[:10]
        ],
        "permutations": permutations,
        "seed": seed,
        "permutation_unit": "within-pair LF/HF event-label swap (whole multivariate history vector)",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mixed_jsonl", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--calipers", default="1.5,2.5")
    ap.add_argument("--permutations", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261119)
    args = ap.parse_args()
    calipers = [float(x) for x in args.calipers.split(",") if x.strip()]
    if not calipers or any(x <= 0 for x in calipers) or args.permutations < 1:
        raise ValueError("positive calipers and permutation count required")
    events = load_events(args.mixed_jsonl)
    records, incomplete = build_records(events)
    pairs = greedy_pairs(records)
    results = [test_pairs(pairs, c, args.permutations, args.seed) for c in calipers]
    for result in results:
        if result["matched_pairs"]:
            result["unmatched_complete_events"] = len(records)-result["matched_events"]
    output = {
        "schema": "cgmf.g2.matched-conditional-history.v1",
        "events_in_file": len(events),
        "complete_event_pairs": len(records),
        "incomplete_events": incomplete,
        "exact_matching_coordinates": ["A_L","Z_L","A_H","Z_H","parity_L","parity_H"],
        "continuous_matching_covariates": COVARIATES,
        "history_features": FEATURES,
        "greedy_disjoint_candidate_pairs_before_caliper": len(pairs),
        "results": results,
        "interpretation": (
            "Exploratory matched conditional association test. A small p-value is residual "
            "LF/HF history association under the selected matching covariates and caliper; "
            "it does not prove direct cross-fragment causation. Matching is approximate, "
            "greedy, and may leave residual confounding."
        ),
        "limitations": [
            "Matching is exact on A/Z and parity, approximate on excitation, stored spin, and momentum magnitude.",
            "The greedy matching is deterministic but not globally optimal.",
            "No explicit scission configuration or independent event TKE/TXE variable is available in this sidecar.",
            "The test uses whole event-level history summaries, not the full ordered path distribution.",
            "No detector response is applied.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}; complete event pairs={len(records)}; matched candidate pairs={len(pairs)}")


if __name__ == "__main__":
    main()

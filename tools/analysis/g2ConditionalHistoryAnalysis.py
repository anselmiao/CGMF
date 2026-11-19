#!/usr/bin/env python3
"""Conditional full-history LF/HF dependence analysis for CGMF G2 mixed-history JSONL.

Uses event-level multivariate fragment-history summaries and permutes whole HF
feature vectors within coarsened initial-state strata. Standard library only.
This is a conditional-association diagnostic, not a causal interaction test.
"""
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


def number(x, label):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{label} must be a finite number")
    return float(x)


def unit_vector(v, label):
    if not isinstance(v, list) or len(v) != 3:
        raise ValueError(f"{label} must be a 3-vector")
    a = [number(x, label) for x in v]
    norm = math.sqrt(sum(x*x for x in a))
    if norm <= 0 or abs(norm - 1.0) > 1e-5:
        raise ValueError(f"{label} must be unit-normalized")
    return a


def load_events(path):
    events = defaultdict(dict)
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                raise ValueError(f"blank line {line_no}")
            row = json.loads(line)
            if row.get("schema") != SCHEMA:
                raise ValueError(f"line {line_no}: unsupported schema")
            eid, side = row.get("event_id"), row.get("fragment_side")
            if not isinstance(eid, int) or isinstance(eid, bool) or eid < 1:
                raise ValueError(f"line {line_no}: invalid event_id")
            if side not in ("LF", "HF") or side in events[eid]:
                raise ValueError(f"line {line_no}: invalid or duplicate fragment side")
            initial = row.get("initial_fragment")
            transitions = row.get("transitions")
            if not isinstance(initial, dict) or not isinstance(transitions, list):
                raise ValueError(f"line {line_no}: missing initial state/history")
            for key in ("A", "Z", "excitation_MeV", "pre_fragment_momentum_MeV_c"):
                if key not in initial:
                    raise ValueError(f"line {line_no}: missing initial_fragment.{key}")
            if not isinstance(initial["A"], int) or not isinstance(initial["Z"], int):
                raise ValueError(f"line {line_no}: A/Z must be integers")
            number(initial["excitation_MeV"], "initial excitation")
            p = initial["pre_fragment_momentum_MeV_c"]
            if not isinstance(p, list) or len(p) != 3:
                raise ValueError(f"line {line_no}: invalid pre-fragment momentum")
            [number(x, "pre-fragment momentum") for x in p]
            for i, tr in enumerate(transitions):
                if tr.get("emission_index") != i:
                    raise ValueError(f"line {line_no}: mixed transition order/index mismatch")
                if tr.get("particle_type") not in ("neutron", "gamma", "internal_conversion"):
                    raise ValueError(f"line {line_no}: unsupported particle type")
                number(tr.get("energy_cm_MeV"), "transition energy")
            events[eid][side] = row
    if not events:
        raise ValueError("no events")
    return events


def fragment_features(row):
    initial = row["initial_fragment"]
    p = [float(x) for x in initial["pre_fragment_momentum_MeV_c"]]
    pn = math.sqrt(sum(x*x for x in p))
    axis = [x/pn for x in p] if pn else [0.0, 0.0, 0.0]
    neutrons, gammas = [], []
    ic_count = 0
    valid_times = 0
    for tr in row["transitions"]:
        kind = tr["particle_type"]
        if tr.get("timestamp_valid") is True and "timestamp_s" in tr:
            valid_times += 1
        if kind == "neutron":
            kin = tr.get("neutron_kinematics")
            if not isinstance(kin, dict):
                raise ValueError("neutron missing kinematics")
            elab = number(kin.get("energy_lab_MeV"), "neutron Lab energy")
            ecm = number(kin.get("energy_cm_MeV"), "neutron CM energy")
            direction = unit_vector(kin.get("direction_lab"), "neutron direction")
            cosine = sum(a*b for a, b in zip(axis, direction))
            neutrons.append((elab, ecm, cosine))
        elif kind == "gamma":
            gammas.append(number(tr["energy_cm_MeV"], "gamma CM energy"))
        else:
            ic_count += 1
    elab = [x[0] for x in neutrons]
    ecm = [x[1] for x in neutrons]
    cosines = [x[2] for x in neutrons]
    n = len(neutrons)
    mean = sum(elab)/n if n else 0.0
    sd = math.sqrt(sum((x-mean)**2 for x in elab)/n) if n else 0.0
    return [
        float(n), mean, sd, max(elab, default=0.0), sum(elab),
        sum(ecm)/n if n else 0.0, elab[0] if n else 0.0,
        elab[-1] if n else 0.0, sum(cosines)/n if n else 0.0,
        sum(x*x for x in cosines)/n if n else 0.0,
        float(len(gammas)), sum(gammas), float(ic_count), float(valid_times),
    ]


def pearson(x, y):
    n = len(x)
    if n < 2:
        return None
    mx, my = sum(x)/n, sum(y)/n
    xx = sum((v-mx)**2 for v in x)
    yy = sum((v-my)**2 for v in y)
    if xx <= 0 or yy <= 0:
        return None
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(xx*yy)


def make_rows(events, excitation_width):
    rows = []
    incomplete = 0
    for eid, sides in sorted(events.items()):
        if set(sides) != {"LF", "HF"}:
            incomplete += 1
            continue
        lf, hf = sides["LF"], sides["HF"]
        li, hi = lf["initial_fragment"], hf["initial_fragment"]
        key = (
            li["A"], li["Z"], hi["A"], hi["Z"],
            math.floor(float(li["excitation_MeV"])/excitation_width),
            math.floor(float(hi["excitation_MeV"])/excitation_width),
        )
        rows.append({
            "event_id": eid, "stratum": key,
            "x": fragment_features(lf), "y": fragment_features(hf),
        })
    return rows, incomplete


def center_and_scale(groups, feature_count):
    eligible = [r for g in groups for r in g]
    xcols = [[r["x"][j] for r in eligible] for j in range(feature_count)]
    ycols = [[r["y"][j] for r in eligible] for j in range(feature_count)]
    sx = [math.sqrt(sum((v-sum(c)/len(c))**2 for v in c)/len(c)) for c in xcols]
    sy = [math.sqrt(sum((v-sum(c)/len(c))**2 for v in c)/len(c)) for c in ycols]
    # Center separately inside each stratum, then scale by pooled eligible SD.
    xc, yc = [], []
    for g in groups:
        mx = [sum(r["x"][j] for r in g)/len(g) for j in range(feature_count)]
        my = [sum(r["y"][j] for r in g)/len(g) for j in range(feature_count)]
        for r in g:
            xc.append([(r["x"][j]-mx[j])/sx[j] if sx[j] else 0.0 for j in range(feature_count)])
            yc.append([(r["y"][j]-my[j])/sy[j] if sy[j] else 0.0 for j in range(feature_count)])
    return xc, yc


def statistic(xc, yc, feature_count):
    n = len(xc)
    total = 0.0
    for i in range(feature_count):
        for j in range(feature_count):
            c = sum(xc[k][i]*yc[k][j] for k in range(n))/n
            total += c*c
    return total


def run_width(rows, width, permutations, seed):
    grouped = defaultdict(list)
    for r in rows:
        # Re-bin from the unrounded excitations retained in the row's hidden fields.
        grouped[r["stratum"]].append(r)
    groups = [g for g in grouped.values() if len(g) >= 2]
    singleton = sum(len(g) == 1 for g in grouped.values())
    if not groups:
        return {
            "excitation_bin_MeV": width, "eligible_events": 0,
            "eligible_strata": 0, "singleton_strata": singleton,
            "omnibus_cross_covariance_norm2": None, "permutation_p": None,
        }
    m = len(FEATURES)
    xc, yc = center_and_scale(groups, m)
    observed = statistic(xc, yc, m)
    rng = random.Random(seed)
    extreme = 0
    valid = 0
    offsets = []
    pos = 0
    for g in groups:
        offsets.append((pos, pos+len(g)))
        pos += len(g)
    for _ in range(permutations):
        yp = []
        for start, end in offsets:
            block = [v[:] for v in yc[start:end]]
            rng.shuffle(block)
            yp.extend(block)
        s = statistic(xc, yp, m)
        valid += 1
        if s >= observed:
            extreme += 1
    pair_corr = []
    for i, name_x in enumerate(FEATURES):
        for j, name_y in enumerate(FEATURES):
            colx = [v[i] for v in xc]
            coly = [v[j] for v in yc]
            r = pearson(colx, coly)
            if r is not None:
                pair_corr.append((abs(r), r, name_x, name_y))
    pair_corr.sort(reverse=True)
    return {
        "excitation_bin_MeV": width,
        "eligible_events": len(xc),
        "eligible_strata": len(groups),
        "singleton_strata": singleton,
        "omnibus_cross_covariance_norm2": observed,
        "permutation_p_one_sided_upper_tail": (1+extreme)/(1+valid),
        "permutations": valid,
        "seed": seed,
        "top_absolute_feature_correlations": [
            {"LF_feature": a, "HF_feature": b, "correlation": r}
            for _, r, a, b in pair_corr[:10]
        ],
        "permutation_unit": "whole HF event feature vector within each stratum",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mixed_jsonl", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--excitation-bins-MeV", default="1,2,4")
    ap.add_argument("--permutations", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261119)
    args = ap.parse_args()
    widths = [float(x) for x in args.excitation_bins_MeV.split(",") if x.strip()]
    if not widths or any(x <= 0 for x in widths) or args.permutations < 1:
        raise ValueError("positive excitation bins and permutation count required")
    events = load_events(args.mixed_jsonl)
    results = []
    for width in widths:
        rows, incomplete = make_rows(events, width)
        result = run_width(rows, width, args.permutations, args.seed)
        result["complete_event_pairs"] = len(rows)
        result["incomplete_events"] = incomplete
        result["conditioning"] = [
            "exact LF/HF A and Z",
            f"LF and HF initial excitation separately binned at {width:g} MeV",
        ]
        result["conditioning_not_available_or_not_used"] = [
            "TKE/TXE as explicit event variables",
            "scission configuration and neck state",
            "full event angular-momentum coupling",
            "other latent common causes",
        ]
        results.append(result)
    output = {
        "schema": "cgmf.g2.conditional-full-history.v1",
        "input_schema": SCHEMA,
        "events_in_file": len(events),
        "features_per_fragment": FEATURES,
        "results_by_excitation_bin": results,
        "interpretation": (
            "The omnibus statistic measures conditional cross-covariance of multivariate "
            "fragment-history summaries. A small permutation p-value indicates residual "
            "association under the stated coarsened conditioning, not direct cross-fragment "
            "causation. Bin-width sensitivity and omitted common causes must be examined."
        ),
        "limitations": [
            "History summaries retain more structure than a single mean but are not the full path distribution.",
            "Only complete LF/HF event pairs are used; zero-neutron sides are retained as zero-valued features.",
            "The permutation assumes exchangeability of whole HF event vectors within each coarse stratum.",
            "No detector response is applied.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}; events={len(events)}; bin widths={widths}")


if __name__ == "__main__":
    main()

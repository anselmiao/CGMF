#!/usr/bin/env python3
"""Three-layer descriptive analysis for CGMF G2 mixed-history JSONL.

Layer 1: within-fragment ordered neutron cascade summaries.
Layer 2: LF/HF event-level dependence after coarse conditioning on initial
         fragment A, Z and excitation; full HF histories are permuted within
         strata, never neutron-by-neutron.
Layer 3: an explicitly simplified detector projection (threshold + energy-
         dependent efficiency + angular acceptance). This is NOT a Bai or
         Schuster detector model and excludes dead time, pile-up, trigger logic,
         resolution smearing and correlated multi-hit effects.

Only the Python standard library is required. No local simulation data are
bundled or assumed.
"""
import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

SCHEMA = "cgmf.g2.mixed-history.v1"


def finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite finite-number")


def vec3(value, label):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must be a 3-vector")
    for i, x in enumerate(value):
        finite(x, f"{label}[{i}]")
    return tuple(float(x) for x in value)


def read_records(path):
    records = {}
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"blank JSONL line {line_no}")
            row = json.loads(line)
            if not isinstance(row, dict) or row.get("schema") != SCHEMA:
                raise ValueError(f"line {line_no}: expected {SCHEMA}")
            event_id, side = row.get("event_id"), row.get("fragment_side")
            if isinstance(event_id, bool) or not isinstance(event_id, int) or event_id < 1:
                raise ValueError(f"line {line_no}: invalid event_id")
            if side not in ("LF", "HF"):
                raise ValueError(f"line {line_no}: invalid fragment_side")
            key = (event_id, side)
            if key in records:
                raise ValueError(f"duplicate fragment record {key}")
            records[key] = row
    if not records:
        raise ValueError("no mixed-history records")
    return records


def validate_fragment(row):
    initial = row.get("initial_fragment")
    transitions = row.get("transitions")
    if not isinstance(initial, dict) or not isinstance(transitions, list):
        raise ValueError("missing initial_fragment or transitions")
    for field in ("A", "Z"):
        value = initial.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"initial_fragment.{field} must be an integer")
    if initial["A"] < 1 or initial["Z"] < 0 or initial["Z"] > initial["A"]:
        raise ValueError("invalid initial nuclide")
    finite(initial.get("excitation_MeV"), "initial excitation")
    neutrons = []
    for index, tr in enumerate(transitions):
        if not isinstance(tr, dict) or tr.get("emission_index") != index:
            raise ValueError("transition list is not in contiguous original order")
        kind = tr.get("particle_type")
        if kind not in ("neutron", "gamma", "internal_conversion"):
            raise ValueError(f"unsupported transition type: {kind}")
        finite(tr.get("energy_cm_MeV"), f"transition {index} energy")
        if kind == "neutron":
            kin = tr.get("neutron_kinematics")
            if not isinstance(kin, dict):
                raise ValueError("neutron transition lacks neutron_kinematics")
            e = kin.get("energy_lab_MeV")
            finite(e, "neutron Lab energy")
            if e < 0:
                raise ValueError("negative neutron Lab energy")
            direction = vec3(kin.get("direction_lab"), "neutron Lab direction")
            norm = math.sqrt(sum(x*x for x in direction))
            if not math.isclose(norm, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError("neutron Lab direction is not unit-normalized")
            neutrons.append({
                "index": index,
                "energy": float(e),
                "direction": direction,
                "transition": tr,
            })
    return {
        "event_id": row["event_id"],
        "side": row["fragment_side"],
        "A": initial["A"],
        "Z": initial["Z"],
        "excitation": float(initial["excitation_MeV"]),
        "transitions": transitions,
        "neutrons": neutrons,
    }


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs)/n, sum(ys)/n
    dx, dy = [x-mx for x in xs], [y-my for y in ys]
    vx, vy = sum(x*x for x in dx), sum(y*y for y in dy)
    if vx <= 0 or vy <= 0:
        return None
    return sum(x*y for x, y in zip(dx, dy)) / math.sqrt(vx*vy)


def intra_fragment(fragments):
    adjacent = []
    by_gap = defaultdict(list)
    counts = {"neutron": 0, "gamma": 0, "internal_conversion": 0}
    for frag in fragments:
        trs = frag["transitions"]
        for tr in trs:
            counts[tr["particle_type"]] += 1
        ns = frag["neutrons"]
        for left, right in zip(ns, ns[1:]):
            gap = right["index"] - left["index"] - 1
            intervening = trs[left["index"]+1:right["index"]]
            gamma_n = sum(t["particle_type"] == "gamma" for t in intervening)
            ic_n = sum(t["particle_type"] == "internal_conversion" for t in intervening)
            pair = {
                "E_previous_MeV": left["energy"],
                "E_next_MeV": right["energy"],
                "transition_gap": gap,
                "intervening_gamma": gamma_n,
                "intervening_internal_conversion": ic_n,
            }
            adjacent.append(pair)
            by_gap[str(gap)].append(pair)
    result = {
        "fragment_count": len(fragments),
        "transition_counts": dict(counts),
        "adjacent_neutron_pairs": len(adjacent),
        "adjacent_energy_pearson": pearson(
            [p["E_previous_MeV"] for p in adjacent],
            [p["E_next_MeV"] for p in adjacent],
        ),
        "by_transition_gap": {},
        "interpretation_limit": (
            "emission_index gives order, not elapsed physical time; "
            "this is a descriptive within-fragment sequence statistic"
        ),
    }
    for gap, pairs in sorted(by_gap.items(), key=lambda item: int(item[0])):
        result["by_transition_gap"][gap] = {
            "pairs": len(pairs),
            "pearson": pearson(
                [p["E_previous_MeV"] for p in pairs],
                [p["E_next_MeV"] for p in pairs],
            ),
            "mean_previous_MeV": sum(p["E_previous_MeV"] for p in pairs)/len(pairs),
            "mean_next_MeV": sum(p["E_next_MeV"] for p in pairs)/len(pairs),
        }
    return result


def bin_value(value, width):
    return math.floor(value / width)


def cross_fragment(events, a_width, ex_width, permutations, seed):
    rows = []
    for event_id, sides in sorted(events.items()):
        if "LF" not in sides or "HF" not in sides:
            continue
        lf, hf = sides["LF"], sides["HF"]
        if not lf["neutrons"] or not hf["neutrons"]:
            continue
        # Event-level summaries retain each side's whole history. No neutron-level
        # shuffling or synthetic cross-pair construction is performed.
        x = sum(n["energy"] for n in lf["neutrons"]) / len(lf["neutrons"])
        y = sum(n["energy"] for n in hf["neutrons"]) / len(hf["neutrons"])
        stratum = (
            lf["A"], lf["Z"], hf["A"], hf["Z"],
            bin_value(lf["excitation"], ex_width),
            bin_value(hf["excitation"], ex_width),
        )
        rows.append({"event_id": event_id, "x": x, "y": y, "stratum": stratum,
                     "n_lf": len(lf["neutrons"]), "n_hf": len(hf["neutrons"])})
    groups = defaultdict(list)
    for row in rows:
        groups[row["stratum"]].append(row)
    eligible = {k: v for k, v in groups.items() if len(v) >= 2}
    matched = [r for group in eligible.values() for r in group]
    if not matched:
        return {
            "events_with_both_sides_emitting": len(rows),
            "eligible_events_in_strata_size_ge_2": 0,
            "eligible_strata": 0,
            "observed_within_stratum_residual_correlation": None,
            "permutation_p_two_sided": None,
            "permutations": permutations,
            "warning": "no exchangeable stratum has at least two events; conditional cross-side dependence is not estimable",
        }

    def statistic(permuted_y=None):
        xs, ys = [], []
        offset = 0
        for _, group in sorted(eligible.items(), key=lambda item: repr(item[0])):
            gx = [r["x"] for r in group]
            gy = [r["y"] for r in group] if permuted_y is None else permuted_y[offset:offset+len(group)]
            offset += len(group)
            mx, my = sum(gx)/len(gx), sum(gy)/len(gy)
            xs.extend(x-mx for x in gx)
            ys.extend(y-my for y in gy)
        return pearson(xs, ys)

    observed = statistic()
    rng = random.Random(seed)
    extreme = 0
    valid = 0
    for _ in range(permutations):
        shuffled = []
        for _, group in sorted(eligible.items(), key=lambda item: repr(item[0])):
            values = [r["y"] for r in group]
            rng.shuffle(values)
            shuffled.extend(values)
        value = statistic(shuffled)
        if value is not None and observed is not None:
            valid += 1
            if abs(value) >= abs(observed):
                extreme += 1
    return {
        "events_with_both_sides_emitting": len(rows),
        "eligible_events_in_strata_size_ge_2": len(matched),
        "eligible_strata": len(eligible),
        "excluded_singleton_strata": sum(len(v) == 1 for v in groups.values()),
        "observed_within_stratum_residual_correlation": observed,
        "permutation_p_two_sided": (1 + extreme)/(1 + valid) if valid else None,
        "valid_permutations": valid,
        "permutations_requested": permutations,
        "seed": seed,
        "conditioning": {
            "exact": ["A_L", "Z_L", "A_H", "Z_H"],
            "binned": {"excitation_L_MeV": ex_width, "excitation_H_MeV": ex_width},
            "warning": "not conditioned on unrecorded shared scission variables, TKE/TXE, angular momentum or detector selection",
        },
        "statistic": "Pearson correlation of within-stratum centered LF/HF event mean neutron Lab energies",
        "permutation_unit": "whole HF event history summary within matched initial-state stratum",
        "interpretation_limit": "residual dependence is not proof of direct cross-fragment interaction; omitted common causes remain possible",
    }


def efficiency_at(energy, curve):
    if not curve:
        return 1.0
    points = sorted((float(p[0]), float(p[1])) for p in curve)
    if any(not 0.0 <= eff <= 1.0 for _, eff in points):
        raise ValueError("detector efficiencies must lie in [0,1]")
    if energy <= points[0][0]:
        return points[0][1]
    if energy >= points[-1][0]:
        return points[-1][1]
    for (e0, p0), (e1, p1) in zip(points, points[1:]):
        if e0 <= energy <= e1:
            f = (energy-e0)/(e1-e0)
            return p0 + f*(p1-p0)
    return 0.0


def detector_projection(events, config, seed):
    threshold = float(config.get("threshold_MeV", 0.0))
    curve = config.get("efficiency_curve", [])
    detectors = config.get("detectors", [])
    if not detectors:
        raise ValueError("detector config requires a nonempty detectors array")
    parsed = []
    for det in detectors:
        direction = vec3(det.get("direction"), "detector direction")
        norm = math.sqrt(sum(x*x for x in direction))
        if norm == 0:
            raise ValueError("detector direction cannot be zero")
        direction = tuple(x/norm for x in direction)
        half_angle = float(det["half_angle_deg"])
        if not 0 < half_angle <= 180:
            raise ValueError("half_angle_deg must be in (0,180]")
        parsed.append((str(det["id"]), direction, math.cos(math.radians(half_angle))))
    rng = random.Random(seed)
    detections = []
    for event_id, sides in sorted(events.items()):
        for side, frag in sides.items():
            for neutron in frag["neutrons"]:
                energy = neutron["energy"]
                if energy < threshold:
                    continue
                direction = neutron["direction"]
                for det_id, axis, cos_min in parsed:
                    cosine = sum(a*b for a, b in zip(direction, axis))
                    if cosine < cos_min:
                        continue
                    if rng.random() <= efficiency_at(energy, curve):
                        detections.append({
                            "event_id": event_id, "fragment_side": side,
                            "neutron_index": neutron["transition"].get("neutron_index"),
                            "detector_id": det_id, "energy_lab_MeV": energy,
                            "direction_lab": list(direction),
                        })
    return {
        "detected_neutron_hits": len(detections),
        "detector_ids": [d[0] for d in parsed],
        "threshold_MeV": threshold,
        "efficiency_curve": curve,
        "seed": seed,
        "hits": detections,
        "model_scope": "idealized independent single-neutron thinning and cone acceptance only",
        "not_included": ["energy/time resolution", "TOF cuts", "dead time", "pile-up",
                         "trigger/logic", "correlated multi-hit efficiency", "gamma tagging",
                         "backgrounds", "detector cross-talk"],
        "warning": "not an experimental Bai/Schuster response model; configure and validate against each apparatus before comparison",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mixed_jsonl", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--excitation-bin-MeV", type=float, required=True)
    parser.add_argument("--permutations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--detector-config", type=Path)
    if parser.parse_args is None:
        raise RuntimeError("argparse unavailable")
    args = parser.parse_args()
    if args.excitation_bin_MeV <= 0 or args.permutations < 1:
        raise ValueError("excitation bin width and permutation count must be positive")

    records = read_records(args.mixed_jsonl)
    fragments = [validate_fragment(row) for row in records.values()]
    events = defaultdict(dict)
    for frag in fragments:
        events[frag["event_id"]][frag["side"]] = frag

    # Report incomplete LF/HF coverage rather than silently dropping it.
    event_ids = sorted({event_id for event_id, _ in records})
    incomplete = [event_id for event_id in event_ids
                  if set(events[event_id]) != {"LF", "HF"}]
    result = {
        "schema": "cgmf.g2.three-layer-analysis.v1",
        "input_records": len(records),
        "events_seen": len(event_ids),
        "events_missing_one_fragment_record": len(incomplete),
        "incomplete_event_ids": incomplete,
        "layer_1_intra_fragment": {
            "LF": intra_fragment([f for f in fragments if f["side"] == "LF"]),
            "HF": intra_fragment([f for f in fragments if f["side"] == "HF"]),
        },
        "layer_2_cross_fragment": cross_fragment(
            events, 1.0, args.excitation_bin_MeV, args.permutations, args.seed
        ),
        "layer_3_detector_projection": None,
        "input_contract": {
            "schema": SCHEMA,
            "required_event_identity": ["event_id", "fragment_side"],
            "required_initial_state": ["A", "Z", "excitation_MeV"],
            "required_neutron_fields": ["energy_lab_MeV", "direction_lab"],
        },
        "global_limitations": [
            "A/Z and excitation are only partial shared-state controls; no TKE/TXE or scission-state conditioning unless added to the sidecar schema.",
            "No event-level causal interpretation follows from observational simulation histories.",
            "Emission index is sequence order, not a physical elapsed-time measurement.",
            "Detector layer is omitted unless an explicit idealized response config is supplied.",
        ],
    }
    if args.detector_config:
        config = json.loads(args.detector_config.read_text(encoding="utf-8"))
        result["layer_3_detector_projection"] = detector_projection(events, config, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output}; events={len(event_ids)}, incomplete={len(incomplete)}")


if __name__ == "__main__":
    main()

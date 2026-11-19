#!/usr/bin/env python3
"""Validate complete ordered CGMF G2 mixed transition history JSONL."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

MIXED_SCHEMA = "cgmf.g2.mixed-history.v1"
NEUTRON_SCHEMA = "cgmf.g2.neutron-transition.v1"


def finite(value, label, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if nonnegative and value < 0:
        raise ValueError(f"{label} must be nonnegative")


def vector(value, label, unit=False):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must be a 3-vector")
    for i, component in enumerate(value):
        finite(component, f"{label}[{i}]")
    if unit:
        norm = math.sqrt(sum(component * component for component in value))
        if not math.isclose(norm, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise ValueError(f"{label} is not a unit vector (norm={norm})")


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"{path}: blank line {line_no}")
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: invalid JSON at line {line_no}: {exc}") from exc
    return rows


def compare_number(a, b, label, tolerance=1e-12):
    finite(a, label)
    finite(b, label)
    if not math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance):
        raise ValueError(f"{label} mismatch: mixed={a}, legacy={b}")


def compare_vector(a, b, label):
    vector(a, label)
    vector(b, label)
    for axis, (x, y) in enumerate(zip(a, b)):
        compare_number(x, y, f"{label}[{axis}]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mixed_jsonl", type=Path)
    parser.add_argument("--neutron-jsonl", type=Path, required=True)
    parser.add_argument("--expected-events", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if args.expected_events < 1:
        raise ValueError("expected-events must be positive")

    mixed_rows = read_jsonl(args.mixed_jsonl)
    neutron_rows = read_jsonl(args.neutron_jsonl)
    expected_groups = {
        (event_id, side)
        for event_id in range(1, args.expected_events + 1)
        for side in ("LF", "HF")
    }
    mixed_groups = {}
    neutron_from_mixed = {}
    type_counts = defaultdict(int)

    for row_no, row in enumerate(mixed_rows, 1):
        if not isinstance(row, dict) or row.get("schema") != MIXED_SCHEMA:
            raise ValueError(f"mixed record {row_no}: schema mismatch")
        if row.get("run_id") != args.run_id:
            raise ValueError(f"mixed record {row_no}: run_id mismatch")
        event_id, side = row.get("event_id"), row.get("fragment_side")
        if isinstance(event_id, bool) or not isinstance(event_id, int) or not 1 <= event_id <= args.expected_events:
            raise ValueError(f"mixed record {row_no}: invalid event_id")
        if side not in ("LF", "HF"):
            raise ValueError(f"mixed record {row_no}: invalid fragment_side")
        group = (event_id, side)
        if group in mixed_groups:
            raise ValueError(f"duplicate event-fragment summary {group}")
        mixed_groups[group] = row

        initial = row.get("initial_fragment")
        if not isinstance(initial, dict):
            raise ValueError(f"{group}: missing initial_fragment")
        for field in ("Z", "A", "parity_index"):
            if isinstance(initial.get(field), bool) or not isinstance(initial.get(field), int):
                raise ValueError(f"{group}: initial_fragment.{field} must be integer")
        finite(initial.get("excitation_MeV"), f"{group} initial excitation", True)
        vector(initial.get("pre_fragment_momentum_MeV_c"), f"{group} initial momentum")

        transitions = row.get("transitions")
        if not isinstance(transitions, list) or row.get("transition_count") != len(transitions):
            raise ValueError(f"{group}: transition_count/list mismatch")
        n_index = 0
        g_index = 0
        for expected_index, tr in enumerate(transitions):
            if not isinstance(tr, dict) or tr.get("emission_index") != expected_index:
                raise ValueError(f"{group}: transition order/index is invalid")
            kind = tr.get("particle_type")
            if kind not in ("neutron", "gamma", "internal_conversion"):
                raise ValueError(f"{group}: unsupported particle_type {kind!r}")
            type_counts[kind] += 1
            finite(tr.get("energy_cm_MeV"), f"{group} transition {expected_index} CM energy", True)

            for state_name in ("parent_state", "daughter_state"):
                state = tr.get(state_name)
                if not isinstance(state, dict):
                    raise ValueError(f"{group}: missing {state_name}")
                for field in ("Z", "A", "spin_index", "parity"):
                    if isinstance(state.get(field), bool) or not isinstance(state.get(field), int):
                        raise ValueError(f"{group}: {state_name}.{field} must be integer")
                finite(state.get("excitation_MeV"), f"{group} {state_name} excitation", True)
                if not isinstance(state.get("discrete"), bool):
                    raise ValueError(f"{group}: {state_name}.discrete must be boolean")

            parent, daughter = tr["parent_state"], tr["daughter_state"]
            if kind == "neutron":
                if parent["Z"] != daughter["Z"] or parent["A"] != daughter["A"] + 1:
                    raise ValueError(f"{group}: neutron transition has invalid nuclide change")
            elif parent["Z"] != daughter["Z"] or parent["A"] != daughter["A"]:
                raise ValueError(f"{group}: gamma/IC transition changes nuclide")

            valid = tr.get("timestamp_valid")
            if not isinstance(valid, bool):
                raise ValueError(f"{group}: timestamp_valid must be boolean")
            if valid:
                if kind == "neutron":
                    raise ValueError(f"{group}: neutron transition has a gamma timestamp")
                finite(tr.get("timestamp_s"), f"{group} timestamp", True)
            elif "timestamp_s" in tr:
                raise ValueError(f"{group}: invalid timestamp must not carry timestamp_s")

            if kind == "neutron":
                kin = tr.get("neutron_kinematics")
                if tr.get("neutron_index") != n_index or not isinstance(kin, dict):
                    raise ValueError(f"{group}: neutron index/kinematics mismatch")
                finite(kin.get("energy_cm_MeV"), f"{group} neutron CM energy", True)
                finite(kin.get("energy_lab_MeV"), f"{group} neutron Lab energy", True)
                for field in ("direction_cm", "direction_lab"):
                    vector(kin.get(field), f"{group} neutron {field}", unit=True)
                for field in ("recoil_before_MeV_c", "recoil_after_MeV_c"):
                    vector(kin.get(field), f"{group} neutron {field}")
                neutron_from_mixed[(event_id, side, n_index)] = tr
                n_index += 1
            elif kind == "gamma":
                kin = tr.get("gamma_kinematics")
                if tr.get("gamma_index") != g_index or not isinstance(kin, dict):
                    raise ValueError(f"{group}: gamma index/kinematics mismatch")
                finite(kin.get("energy_cm_MeV"), f"{group} gamma CM energy", True)
                finite(kin.get("energy_lab_MeV"), f"{group} gamma Lab energy", True)
                for field in ("direction_cm", "direction_lab"):
                    vector(kin.get(field), f"{group} gamma {field}", unit=True)
                compare_number(tr["energy_cm_MeV"], kin["energy_cm_MeV"], f"{group} gamma CM energy")
                g_index += 1
            elif tr.get("internal_conversion") is not True:
                raise ValueError(f"{group}: internal-conversion marker missing")

    if set(mixed_groups) != expected_groups:
        missing = sorted(expected_groups - set(mixed_groups))
        extra = sorted(set(mixed_groups) - expected_groups)
        raise ValueError(f"event-fragment coverage mismatch; missing={missing[:5]}, extra={extra[:5]}")

    neutron_from_legacy = {}
    for row_no, row in enumerate(neutron_rows, 1):
        if row.get("schema") != NEUTRON_SCHEMA or row.get("run_id") != args.run_id:
            raise ValueError(f"legacy neutron record {row_no}: schema/run_id mismatch")
        key = (row.get("event_id"), row.get("fragment_side"), row.get("neutron_index"))
        if key in neutron_from_legacy:
            raise ValueError(f"duplicate legacy neutron key {key}")
        neutron_from_legacy[key] = row
    if set(neutron_from_mixed) != set(neutron_from_legacy):
        raise ValueError("mixed-history neutron keys differ from legacy sidecar keys")

    for key, tr in neutron_from_mixed.items():
        old = neutron_from_legacy[key]
        for new_name, old_name in (("parent_state", "parent"), ("daughter_state", "daughter")):
            new_state, old_state = tr[new_name], old[old_name]
            for field in ("Z", "A", "spin_index", "parity"):
                if new_state[field] != old_state[field]:
                    raise ValueError(f"{key}: {new_name}.{field} differs from legacy sidecar")
            compare_number(new_state["excitation_MeV"], old_state["excitation_MeV"], f"{key} {new_name} excitation")
            if new_state["discrete"] != old_state["discrete"]:
                raise ValueError(f"{key}: {new_name}.discrete differs from legacy sidecar")
        kin, old_n, old_r = tr["neutron_kinematics"], old["neutron"], old["fragment_recoil"]
        compare_number(tr["energy_cm_MeV"], old_n["energy_cm_MeV"], f"{key} CM energy")
        compare_number(kin["energy_lab_MeV"], old_n["energy_lab_MeV"], f"{key} Lab energy")
        compare_vector(kin["direction_cm"], old_n["direction_cm"], f"{key} CM direction")
        compare_vector(kin["direction_lab"], old_n["direction_lab"], f"{key} Lab direction")
        compare_vector(kin["recoil_before_MeV_c"], old_r["momentum_before_MeV_c"], f"{key} recoil before")
        compare_vector(kin["recoil_after_MeV_c"], old_r["momentum_after_MeV_c"], f"{key} recoil after")

    print(f"Mixed-history validation passed: {len(mixed_rows)} fragment summaries, "
          f"{len(neutron_from_mixed)} neutron transitions, particle_counts={dict(type_counts)}")


if __name__ == "__main__":
    main()

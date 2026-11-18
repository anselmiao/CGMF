#!/usr/bin/env python3
"""Validate the CGMF G2 neutron-transition JSONL smoke-test output."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

SCHEMA = "cgmf.g2.neutron-transition.v1"


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")


def vector(value, label, unit=False):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must be a 3-vector")
    for i, component in enumerate(value):
        finite_number(component, f"{label}[{i}]")
    if unit:
        norm = math.sqrt(sum(component * component for component in value))
        if not math.isclose(norm, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise ValueError(f"{label} is not a unit direction vector (norm={norm})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--expected-events", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    records = []
    with args.jsonl.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"blank JSONL line at {line_number}")
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc

    if not records:
        raise ValueError("sidecar produced no neutron records")

    groups = defaultdict(list)
    seen = set()
    for row_number, row in enumerate(records, 1):
        if not isinstance(row, dict):
            raise ValueError(f"record {row_number} is not a JSON object")
        if row.get("schema") != SCHEMA:
            raise ValueError(f"record {row_number}: unexpected schema")
        if row.get("run_id") != args.run_id:
            raise ValueError(f"record {row_number}: run_id mismatch")

        event_id = row.get("event_id")
        if isinstance(event_id, bool) or not isinstance(event_id, int) or not 1 <= event_id <= args.expected_events:
            raise ValueError(f"record {row_number}: event_id out of expected range")
        side = row.get("fragment_side")
        if side not in ("LF", "HF"):
            raise ValueError(f"record {row_number}: invalid fragment_side")
        index = row.get("neutron_index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ValueError(f"record {row_number}: invalid neutron_index")

        key = (event_id, side, index)
        if key in seen:
            raise ValueError(f"duplicate neutron record key: {key}")
        seen.add(key)
        groups[(event_id, side)].append(index)

        parent, daughter = row.get("parent"), row.get("daughter")
        if not isinstance(parent, dict) or not isinstance(daughter, dict):
            raise ValueError(f"record {row_number}: missing parent/daughter objects")
        for nucleus_name, nucleus in (("parent", parent), ("daughter", daughter)):
            for field in ("Z", "A", "spin_index", "parity"):
                value = nucleus.get(field)
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError(f"record {row_number}: {nucleus_name}.{field} must be integer")
            finite_number(nucleus.get("excitation_MeV"), f"{nucleus_name}.excitation_MeV")
            if nucleus["A"] <= 0 or nucleus["Z"] < 0 or nucleus["Z"] > nucleus["A"]:
                raise ValueError(f"record {row_number}: invalid {nucleus_name} nuclide")
            if not isinstance(nucleus.get("discrete"), bool):
                raise ValueError(f"record {row_number}: {nucleus_name}.discrete must be boolean")
        if parent["Z"] != daughter["Z"] or parent["A"] != daughter["A"] + 1:
            raise ValueError(f"record {row_number}: parent/daughter do not represent neutron emission")

        neutron = row.get("neutron")
        recoil = row.get("fragment_recoil")
        if not isinstance(neutron, dict) or not isinstance(recoil, dict):
            raise ValueError(f"record {row_number}: missing neutron/recoil objects")
        for field in ("energy_cm_MeV", "energy_lab_MeV"):
            finite_number(neutron.get(field), f"neutron.{field}")
            if neutron[field] < 0:
                raise ValueError(f"record {row_number}: negative neutron energy")
        for field in ("direction_cm", "direction_lab"):
            vector(neutron.get(field), f"neutron.{field}", unit=True)
        for field in ("momentum_before_MeV_c", "momentum_after_MeV_c"):
            vector(recoil.get(field), f"fragment_recoil.{field}")

    for group, indices in groups.items():
        ordered = sorted(indices)
        if ordered != list(range(len(ordered))):
            raise ValueError(f"non-contiguous neutron indices for {group}: {ordered}")

    event_ids = sorted({event_id for event_id, _ in groups})
    sides = sorted({side for _, side in groups})
    print(
        f"G2 sidecar smoke test passed: {len(records)} neutron records, "
        f"{len(event_ids)} emitting events, fragment sides={','.join(sides)}, "
        f"{len(groups)} event/fragment groups"
    )


if __name__ == "__main__":
    main()

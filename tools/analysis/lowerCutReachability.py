#!/usr/bin/env python3
"""Audit discrete-state reachability for continuum-to-discrete gamma bridges.

This is an independent analysis utility. It does not modify CGMF physics,
sampling, level data, or bridge selection. Input is an explicit JSON snapshot
of discrete levels and continuum-bin samples.
"""
from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
from pathlib import Path

MULTIPOLARITIES = {"E1": ("E", 1), "M1": ("M", 1), "E2": ("E", 2)}
BRIDGE_SCHEMES = {
    "current_E1_only": ["E1"],
    "comparison_E1_M1_E2": ["E1", "M1", "E2"],
}


def _spin(value, field):
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{field}: invalid spin {value!r}") from exc
    if result < 0 or (2 * result).denominator != 1:
        raise ValueError(f"{field}: spin must be a nonnegative integer or half-integer")
    return result


def transition_allowed(initial, final, multipolarity):
    """Return the gamma selection-rule result for a pure E/M multipole."""
    if multipolarity not in MULTIPOLARITIES:
        raise ValueError(f"unsupported multipolarity: {multipolarity}")
    kind, rank = MULTIPOLARITIES[multipolarity]
    ji = _spin(initial["spin"], "initial.spin")
    jf = _spin(final["spin"], "final.spin")
    pi, pf = initial["parity"], final["parity"]
    if pi not in (-1, 1) or pf not in (-1, 1):
        raise ValueError("parity must be +1 or -1")
    if abs(ji - jf) > rank or rank > ji + jf:
        return False
    if ji == 0 and jf == 0:
        return False
    parity_factor = (-1) ** rank if kind == "E" else (-1) ** (rank + 1)
    return pi * pf == parity_factor


def analyze_sample(sample, levels):
    energy = float(sample["energy_MeV"])
    low = float(sample["bin_min_MeV"])
    high = float(sample["bin_max_MeV"])
    if not all(math.isfinite(x) for x in (energy, low, high)):
        raise ValueError("sample energies must be finite")
    if low < 0 or high <= low or energy < low or energy > high:
        raise ValueError("sample energy must lie inside a positive-width nonnegative bin")
    initial = {
        "spin": sample["spin"],
        "parity": sample["parity"],
    }
    candidate_rows = []
    for level in levels:
        level_energy = float(level["energy_MeV"])
        if not math.isfinite(level_energy) or level_energy < 0:
            raise ValueError(f"invalid level energy for {level.get('level_id')}")
        if level_energy >= energy:
            energy_accessible = False
        else:
            energy_accessible = True
        allowed = [
            multipole for multipole in MULTIPOLARITIES
            if transition_allowed(initial, level, multipole)
        ]
        candidate_rows.append({
            "level_id": level["level_id"],
            "energy_MeV": level_energy,
            "energy_accessible_at_sample": energy_accessible,
            "allowed_multipolarities": allowed,
        })

    schemes = {}
    for scheme_name, multipoles in BRIDGE_SCHEMES.items():
        eligible = [
            row for row in candidate_rows
            if row["energy_accessible_at_sample"]
            and any(m in row["allowed_multipolarities"] for m in multipoles)
        ]
        # For a fixed Jpi and a fixed set of multipoles, a level is reachable
        # whenever E_gamma > 0. The union over levels is E > min(E_level).
        eligible_energies = [
            row["energy_MeV"] for row in candidate_rows
            if any(m in row["allowed_multipolarities"] for m in multipoles)
        ]
        threshold = min(eligible_energies) if eligible_energies else None
        if threshold is None:
            fraction = 0.0
        else:
            fraction = max(0.0, high - max(low, threshold)) / (high - low)
        schemes[scheme_name] = {
            "multipolarities": multipoles,
            "reachable_at_sample": bool(eligible),
            "eligible_level_ids_at_sample": [row["level_id"] for row in eligible],
            "lowest_selection_allowed_level_MeV": threshold,
            "reachable_bin_fraction": fraction,
            "unreachable_bin_fraction": 1.0 - fraction,
        }

    return {
        "sample_id": sample.get("sample_id"),
        "nuclide": sample.get("nuclide"),
        "initial_state": {
            "energy_MeV": energy,
            "spin": str(_spin(initial["spin"], "initial.spin")),
            "parity": initial["parity"],
        },
        "bin": {"min_MeV": low, "max_MeV": high},
        "candidate_levels": candidate_rows,
        "schemes": schemes,
    }


def analyze_document(document):
    if document.get("schema_version") != "cgmf-lower-cut-reachability-v1":
        raise ValueError("unsupported or missing schema_version")
    levels = document.get("discrete_levels")
    samples = document.get("continuum_samples")
    if not isinstance(levels, list) or not isinstance(samples, list) or not samples:
        raise ValueError("discrete_levels must be a list and continuum_samples must be nonempty")
    ids = [level.get("level_id") for level in levels]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("discrete level IDs must be nonempty and unique")
    for level in levels:
        _spin(level.get("spin"), f'{level.get("level_id")}.spin')
        if level.get("parity") not in (-1, 1):
            raise ValueError(f'{level.get("level_id")}: parity must be +1 or -1')
    return {
        "schema_version": "cgmf-lower-cut-reachability-report-v1",
        "analysis_scope": "selection-rule and energy-interval reachability only; not a CGMF runtime reproduction",
        "source_metadata": document.get("source_metadata", {}),
        "results": [analyze_sample(sample, levels) for sample in samples],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding="utf-8"))
    report = analyze_document(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote reachability report: {args.output}")


if __name__ == "__main__":
    main()

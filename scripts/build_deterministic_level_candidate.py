#!/usr/bin/env python3
"""Build a deterministic, fail-closed candidate catalog for CGMF discrete levels.

This tool does NOT rewrite data/discreteLevels.dat. It validates a reviewed JSON
manifest and emits a separate candidate JSON plus a decision report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

SCHEMA_VERSION = "cgmf-targeted-level-candidate-v0.1"
VALID_JPI = {"ADOPTED_UNIQUE", "TENTATIVE", "AMBIGUOUS", "UNKNOWN"}
VALID_DECISIONS = {"PROMPT_INCLUDE", "CATALOG_ONLY", "REJECT", "BLOCKED"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _finite_nonnegative(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be numeric")
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field} must be finite and nonnegative")
    return number


def _spin(value) -> Fraction:
    if value is None or value == "":
        raise ValueError("spin is unknown")
    spin = Fraction(str(value))
    if spin < 0 or (2 * spin).denominator != 1:
        raise ValueError("spin must be a nonnegative integer or half-integer")
    return spin


def _transition_allowed(ji: Fraction, jf: Fraction, pi: int, pf: int, multipole: str) -> bool:
    # E1, M1, E2, ... ; rank L must obey |Ji-Jf| <= L <= Ji+Jf.
    if len(multipole) < 2 or multipole[0] not in "EM" or not multipole[1:].isdigit():
        raise ValueError(f"invalid multipolarity: {multipole}")
    kind, rank = multipole[0], int(multipole[1:])
    if rank < 1 or abs(ji - jf) > rank or rank > ji + jf:
        return False
    if ji == 0 and jf == 0:
        return False
    parity_factor = (-1) ** rank if kind == "E" else (-1) ** (rank + 1)
    return pi * pf == parity_factor


def validate_manifest(doc: dict) -> dict:
    if doc.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    sources = doc.get("sources")
    levels = doc.get("levels")
    if not isinstance(sources, list) or not isinstance(levels, list):
        raise ValueError("sources and levels must be arrays")

    source_ids = set()
    for src in sources:
        sid = src.get("source_id")
        if not sid or sid in source_ids or not src.get("reference") or not src.get("version"):
            raise ValueError("each source needs unique source_id, reference, and version")
        source_ids.add(sid)

    ids = set()
    by_nuclide = {}
    decisions = []
    accepted = []
    for item in levels:
        lid = item.get("level_id")
        if not lid or lid in ids:
            raise ValueError(f"missing or duplicate level_id: {lid}")
        ids.add(lid)
        zaid = int(item["zaid"])
        a = int(item["A"])
        z = int(item["Z"])
        if zaid != 1000 * z + a or a <= 0 or z <= 0 or z > a:
            raise ValueError(f"{lid}: inconsistent ZAID/Z/A")
        energy = _finite_nonnegative(item.get("energy_MeV"), f"{lid}.energy_MeV")
        uncertainty = _finite_nonnegative(item.get("energy_uncertainty_MeV", 0), f"{lid}.energy_uncertainty_MeV")
        jpi_status = item.get("jpi_status")
        if jpi_status not in VALID_JPI:
            raise ValueError(f"{lid}: invalid jpi_status")
        source_id = item.get("source_id")
        if source_id not in source_ids:
            raise ValueError(f"{lid}: unknown source_id")
        decision = item.get("decision")
        if decision not in VALID_DECISIONS:
            raise ValueError(f"{lid}: invalid decision")
        parity = item.get("parity")
        spin_value = item.get("spin")
        spin = None
        if jpi_status == "ADOPTED_UNIQUE":
            spin = _spin(spin_value)
            if parity not in (-1, 1):
                raise ValueError(f"{lid}: adopted Jpi requires parity +/-1")
            if (2 * spin).denominator != 1 or int(2 * spin) % 2 != a % 2:
                raise ValueError(f"{lid}: J/A integer-half-integer lattice mismatch")
        elif decision == "PROMPT_INCLUDE":
            raise ValueError(f"{lid}: tentative/ambiguous/unknown Jpi cannot enter prompt scheme")

        record = dict(item)
        record["energy_MeV"] = energy
        record["energy_uncertainty_MeV"] = uncertainty
        record["spin_exact"] = str(spin) if spin is not None else None
        by_nuclide.setdefault(zaid, []).append(record)

    for zaid, records in by_nuclide.items():
        records.sort(key=lambda x: (x["energy_MeV"], x["level_id"]))
        energy_by_id = {x["level_id"]: x["energy_MeV"] for x in records}
        for rec in records:
            branches = rec.get("gamma_branches", [])
            if not isinstance(branches, list):
                raise ValueError(f'{rec["level_id"]}: gamma_branches must be an array')
            if rec["decision"] == "PROMPT_INCLUDE":
                if rec["jpi_status"] != "ADOPTED_UNIQUE" or not branches:
                    raise ValueError(f'{rec["level_id"]}: prompt inclusion requires adopted Jpi and gamma branches')
                if rec.get("competing_decay", "NONE") != "NONE":
                    raise ValueError(f'{rec["level_id"]}: competing beta/IT decay is not represented by legacy gamma scheme')
            total = 0.0
            for branch in branches:
                target = branch.get("to_level_id")
                if target not in energy_by_id or energy_by_id[target] >= rec["energy_MeV"]:
                    raise ValueError(f'{rec["level_id"]}: gamma destination must be a lower level in same nuclide')
                probability = _finite_nonnegative(branch.get("probability"), f'{rec["level_id"]}.branch.probability')
                alpha = _finite_nonnegative(branch.get("internal_conversion_coefficient", 0), f'{rec["level_id"]}.branch.alpha')
                components = branch.get("multipolarities", [])
                if not components:
                    raise ValueError(f'{rec["level_id"]}: branch multipolarities must be explicit')
                if rec["jpi_status"] == "ADOPTED_UNIQUE" and by_nuclide[zaid]:
                    target_rec = next(x for x in records if x["level_id"] == target)
                    if target_rec["jpi_status"] != "ADOPTED_UNIQUE":
                        raise ValueError(f'{rec["level_id"]}: transition target Jpi is not uniquely adopted')
                    ji, jf = _spin(rec["spin"]), _spin(target_rec["spin"])
                    allowed = False
                    for multipole in components:
                        allowed = _transition_allowed(ji, jf, rec["parity"], target_rec["parity"], multipole) or allowed
                    if not allowed:
                        raise ValueError(f'{rec["level_id"]}: no declared multipole satisfies Jpi selection rules')
                total += probability
            if branches and not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-8):
                raise ValueError(f'{rec["level_id"]}: gamma branch probabilities sum to {total}, not 1')
            status = rec["decision"]
            if status == "PROMPT_INCLUDE":
                accepted.append(rec["level_id"])
            decisions.append({
                "level_id": rec["level_id"], "zaid": zaid,
                "decision": status,
                "reason": rec.get("decision_reason", ""),
                "gamma_branch_count": len(branches),
            })

    return {
        "schema_version": SCHEMA_VERSION,
        "generator": "build_deterministic_level_candidate.py",
        "source_manifest_sha256": None,
        "levels": sorted(
            [r for group in by_nuclide.values() for r in group],
            key=lambda x: (x["zaid"], x["energy_MeV"], x["level_id"]),
        ),
        "decision_report": {
            "counts": {key: sum(d["decision"] == key for d in decisions) for key in sorted(VALID_DECISIONS)},
            "accepted_prompt_level_ids": sorted(accepted),
            "decisions": sorted(decisions, key=lambda x: (x["zaid"], x["level_id"])),
            "production_data_modified": False,
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.manifest.read_bytes()
        doc = json.loads(raw.decode("utf-8"))
        result = validate_manifest(doc)
        result["source_manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        candidate = {k: v for k, v in result.items() if k != "decision_report"}
        report = result["decision_report"]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"candidate={args.output} report={args.report} prompt_levels={len(report['accepted_prompt_level_ids'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

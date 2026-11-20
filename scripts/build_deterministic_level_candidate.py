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

SCHEMA_VERSION = "cgmf-targeted-level-candidate-v0.2"
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



def derive_mode_conditional_branches(level: dict, mode: str) -> dict:
    """Derive conditional transition and photon/conversion probabilities.

    ENSDF relative photon intensities I_gamma are converted to total transition
    weights I_gamma * (1 + alpha). The result is BLOCKED unless the evaluated
    transition inventory for this decay mode is explicitly complete.
    """
    channels = {c.get("mode"): c for c in level.get("decay_channels", [])}
    if mode not in channels:
        return {"status": "BLOCKED", "reason": "decay mode fraction is absent"}
    channel = channels[mode]
    sets = {x.get("mode"): x for x in level.get("transition_sets", [])}
    transition_set = sets.get(mode)
    if not transition_set or transition_set.get("complete") is not True:
        return {"status": "BLOCKED", "reason": "transition inventory for decay mode is not certified complete"}
    if transition_set.get("intensity_basis") != "relative_photon_intensity_within_decay_mode":
        return {"status": "BLOCKED", "reason": "transition intensity basis is not explicit"}
    transitions = [x for x in level.get("observed_transitions", []) if x.get("decay_mode_id") == mode]
    dataset_source = transition_set.get("source_id")
    if not dataset_source or any(x.get("source_id") != dataset_source for x in transitions):
        return {"status": "BLOCKED", "reason": "transition records do not share the declared source dataset"}
    if not transitions:
        return {"status": "BLOCKED", "reason": "no observed transitions for decay mode"}
    weights = []
    for tr in transitions:
        intensity = tr.get("relative_photon_intensity")
        alpha = tr.get("total_internal_conversion_coefficient")
        if intensity is None or alpha is None:
            return {"status": "BLOCKED", "reason": "each transition requires photon intensity and total ICC"}
        intensity = _finite_nonnegative(intensity, "relative_photon_intensity")
        alpha = _finite_nonnegative(alpha, "total_internal_conversion_coefficient")
        if intensity <= 0:
            return {"status": "BLOCKED", "reason": "relative photon intensity must be positive"}
        weights.append(intensity * (1.0 + alpha))
    denominator = math.fsum(weights)
    if not math.isfinite(denominator) or denominator <= 0:
        return {"status": "BLOCKED", "reason": "total transition weight is not positive and finite"}
    mode_fraction = _finite_nonnegative(channel.get("fraction"), "decay mode fraction")
    results = []
    for tr, weight in zip(transitions, weights):
        alpha = float(tr["total_internal_conversion_coefficient"])
        transition_probability = weight / denominator
        gamma_conditional = 1.0 / (1.0 + alpha)
        conversion_conditional = alpha / (1.0 + alpha)
        results.append({
            "transition_id": tr["transition_id"],
            "transition_probability_given_mode": transition_probability,
            "gamma_probability_given_transition": gamma_conditional,
            "conversion_probability_given_transition": conversion_conditional,
            "total_isomer_decay_gamma_probability": mode_fraction * transition_probability * gamma_conditional,
            "total_isomer_decay_conversion_probability": mode_fraction * transition_probability * conversion_conditional,
        })
    return {
        "status": "DERIVED_CONDITIONAL",
        "mode": mode,
        "mode_fraction": mode_fraction,
        "transition_weight_basis": "relative_photon_intensity_times_one_plus_total_ICC",
        "uncertainty_propagated": False,
        "transitions": results,
    }


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
            channels = rec.get("decay_channels", [])
            if not isinstance(channels, list):
                raise ValueError(f'{rec["level_id"]}: decay_channels must be an array')
            channel_ids = set()
            channel_total = 0.0
            for channel in channels:
                mode = channel.get("mode")
                if not mode or mode in channel_ids:
                    raise ValueError(f'{rec["level_id"]}: decay channel modes must be unique')
                channel_ids.add(mode)
                if channel.get("fraction_basis") != "total_isomer_decay":
                    raise ValueError(f'{rec["level_id"]}: fraction_basis must be total_isomer_decay')
                channel_total += _finite_nonnegative(channel.get("fraction"), f'{rec["level_id"]}.{mode}.fraction')
                if channel.get("source_id") not in source_ids:
                    raise ValueError(f'{rec["level_id"]}: decay channel has unknown source_id')
            if rec.get("decay_channels_complete", False):
                if not channels or not math.isclose(channel_total, 1.0, rel_tol=0.0, abs_tol=1e-6):
                    raise ValueError(f'{rec["level_id"]}: complete decay-channel fractions must sum to 1')
            elif channels and channel_total > 1.0 + 1e-6:
                raise ValueError(f'{rec["level_id"]}: partial decay-channel fractions exceed 1')

            transition_sets = rec.get("transition_sets", [])
            if not isinstance(transition_sets, list):
                raise ValueError(f'{rec["level_id"]}: transition_sets must be an array')
            transition_set_modes = [x.get("mode") for x in transition_sets]
            if len(transition_set_modes) != len(set(transition_set_modes)):
                raise ValueError(f'{rec["level_id"]}: duplicate transition-set mode')
            for transition_set in transition_sets:
                if transition_set.get("mode") not in channel_ids:
                    raise ValueError(f'{rec["level_id"]}: transition set has no matching decay channel')
                if not isinstance(transition_set.get("complete"), bool):
                    raise ValueError(f'{rec["level_id"]}: transition-set completeness must be explicit')
            transitions = rec.get("observed_transitions", [])
            if not isinstance(transitions, list):
                raise ValueError(f'{rec["level_id"]}: observed_transitions must be an array')
            transition_ids = set()
            for tr in transitions:
                transition_id = tr.get("transition_id")
                if not transition_id or transition_id in transition_ids:
                    raise ValueError(f'{rec["level_id"]}: transition IDs must be present and unique')
                transition_ids.add(transition_id)
                mode_id = tr.get("decay_mode_id")
                if mode_id is not None and mode_id not in channel_ids:
                    raise ValueError(f'{rec["level_id"]}: observed transition has unknown decay_mode_id')
                if tr.get("source_id") not in source_ids:
                    raise ValueError(f'{rec["level_id"]}: observed transition has unknown source_id')
                if tr.get("initial_level_id") != rec["level_id"]:
                    raise ValueError(f'{rec["level_id"]}: transition initial_level_id mismatch')
                target_id = tr.get("final_level_id")
                target_rec = next((x for x in records if x["level_id"] == target_id), None)
                if target_rec is None or target_rec["energy_MeV"] >= rec["energy_MeV"]:
                    raise ValueError(f'{rec["level_id"]}: observed transition destination must be a lower catalogued level')
                gamma_keV = _finite_nonnegative(tr.get("gamma_energy_keV"), f'{rec["level_id"]}.gamma_energy_keV')
                alpha_value = tr.get("total_internal_conversion_coefficient")
                if alpha_value is not None:
                    _finite_nonnegative(alpha_value, f'{rec["level_id"]}.total_internal_conversion_coefficient')
                elif tr.get("conversion_coefficient_required", False):
                    raise ValueError(f'{rec["level_id"]}: required internal-conversion coefficient is missing')
                if tr.get("relative_photon_intensity") is not None:
                    _finite_nonnegative(tr["relative_photon_intensity"], f'{rec["level_id"]}.relative_photon_intensity')
                if tr.get("prompt_status") == "PROMPT":
                    if rec.get("half_life_s") is None or rec["half_life_s"] > 1e-6:
                        raise ValueError(f'{rec["level_id"]}: long-lived or unspecified level cannot be marked prompt')
                    if any(c["mode"] in {"BETA_MINUS", "ISOMERIC_TRANSITION"} for c in channels):
                        raise ValueError(f'{rec["level_id"]}: beta/IT competition cannot be promoted as prompt')
                initial_u = rec.get("energy_uncertainty_MeV")
                final_u = target_rec.get("energy_uncertainty_MeV")
                gamma_u = tr.get("gamma_energy_uncertainty_keV")
                if initial_u is not None and final_u is not None and gamma_u is not None:
                    delta_keV = (rec["energy_MeV"] - target_rec["energy_MeV"]) * 1000.0
                    sigma_keV = math.sqrt((initial_u * 1000.0) ** 2 + (final_u * 1000.0) ** 2 + float(gamma_u) ** 2)
                    residual = abs(delta_keV - gamma_keV)
                    if residual > max(1e-6, 3.0 * sigma_keV):
                        raise ValueError(f'{rec["level_id"]}: transition energy closure failed ({residual:.6g} keV > 3 sigma)')
            derived_modes = {}
            for mode in channel_ids:
                derived_modes[mode] = derive_mode_conditional_branches(rec, mode)
            status = rec["decision"]
            if status == "PROMPT_INCLUDE":
                accepted.append(rec["level_id"])
            decisions.append({
                "level_id": rec["level_id"], "zaid": zaid,
                "decision": status,
                "reason": rec.get("decision_reason", ""),
                "gamma_branch_count": len(branches),
                "derived_decay_modes": derived_modes,
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

#!/usr/bin/env python3
"""Audit physical J/parity fields in CGMF's fixed-width discreteLevels.dat.

The parser mirrors the field slices used by libcgmf/src/ripl2levels.cpp:
  header: ZAID [6:12], number of levels [12:17]
  level:  energy [0:10], J [10:15], parity [15:18], gamma count [31:34]

This is an audit only. It never changes the input data or assigns missing J/pi.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMA_VERSION = "cgmf-discrete-level-quantum-number-audit-v1"


def _int_field(text: str, field: str, line_number: int) -> int:
    try:
        return int(text.strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line {line_number}: invalid {field}: {text!r}") from exc


def _decimal_field(text: str, field: str, line_number: int) -> Decimal:
    try:
        value = Decimal(text.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"line {line_number}: invalid {field}: {text!r}") from exc
    if not value.is_finite():
        raise ValueError(f"line {line_number}: non-finite {field}: {text!r}")
    return value


def audit_discrete_levels(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: data file is not UTF-8") from exc

    nuclei_count = 0
    level_count = 0
    missing_spin_count = 0
    spin_lattice_violations: list[dict] = []
    invalid_parity_records: list[dict] = []
    i = 0

    while i < len(lines):
        header = lines[i]
        if not header or header.startswith("#"):
            i += 1
            continue
        if len(header) < 17:
            raise ValueError(f"line {i + 1}: truncated isotope header")

        zaid = _int_field(header[6:12], "ZAID", i + 1)
        nlevels = _int_field(header[12:17], "number of levels", i + 1)
        if zaid < 0 or nlevels < 0:
            raise ValueError(f"line {i + 1}: negative ZAID or level count")

        z, mass_number = divmod(zaid, 1000)
        nuclei_count += 1

        for level_index in range(nlevels):
            i += 1
            if i >= len(lines):
                raise ValueError(
                    f"line {i + 1}: truncated level list for ZAID {zaid}"
                )
            row = lines[i]
            if len(row) < 34:
                raise ValueError(f"line {i + 1}: truncated level row for ZAID {zaid}")

            energy = _decimal_field(row[0:10], "energy", i + 1)
            spin = _decimal_field(row[10:15], "spin", i + 1)
            parity = _int_field(row[15:18], "parity", i + 1)
            ngamma = _int_field(row[31:34], "gamma count", i + 1)
            if ngamma < 0:
                raise ValueError(f"line {i + 1}: negative gamma count")

            level_count += 1
            common = {
                "zaid": zaid,
                "Z": z,
                "A": mass_number,
                "level_index": level_index,
                "line": i + 1,
                "energy_MeV": str(energy),
                "spin_J": str(spin),
                "parity": parity,
                "is_ground_state": level_index == 0,
            }

            if parity not in (-1, 1):
                invalid_parity_records.append({**common, "reason": "PARITY_NOT_PLUS_OR_MINUS_ONE"})

            if spin < 0:
                missing_spin_count += 1
            else:
                two_j = spin * 2
                if two_j != two_j.to_integral_value():
                    spin_lattice_violations.append(
                        {**common, "reason": "J_NOT_INTEGER_OR_HALF_INTEGER"}
                    )
                elif int(two_j) % 2 != mass_number % 2:
                    reason = (
                        "ODD_A_INTEGER_J"
                        if mass_number % 2
                        else "EVEN_A_HALF_INTEGER_J"
                    )
                    spin_lattice_violations.append({**common, "reason": reason})

            # Each level's gamma-branch records immediately follow the level row.
            i += ngamma
            if i >= len(lines) and (level_index != nlevels - 1):
                raise ValueError(f"ZAID {zaid}: gamma records run past end of file")

        i += 1

    by_nuclide: dict[int, int] = {}
    for item in spin_lattice_violations:
        key = item["zaid"]
        by_nuclide[key] = by_nuclide.get(key, 0) + 1

    ground_state_violations = [
        item for item in spin_lattice_violations if item["is_ground_state"]
    ]
    excited_state_violations = [
        item for item in spin_lattice_violations if not item["is_ground_state"]
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_file": path.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "parser_contract": {
            "header_zaid_slice": "[6:12]",
            "header_level_count_slice": "[12:17]",
            "level_energy_slice": "[0:10]",
            "level_spin_slice": "[10:15]",
            "level_parity_slice": "[15:18]",
            "level_gamma_count_slice": "[31:34]",
            "spin_interpretation": "J in units of hbar, not 2J",
            "mass_spin_lattice": "2J mod 2 equals A mod 2",
        },
        "counts": {
            "nuclei": nuclei_count,
            "levels": level_count,
            "missing_or_negative_spin": missing_spin_count,
            "spin_lattice_violations": len(spin_lattice_violations),
            "spin_lattice_violating_nuclides": len(by_nuclide),
            "ground_state_spin_lattice_violations": len(ground_state_violations),
            "excited_state_spin_lattice_violations": len(excited_state_violations),
            "invalid_parity_records": len(invalid_parity_records),
        },
        "spin_lattice_violations": spin_lattice_violations,
        "invalid_parity_records": invalid_parity_records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--fail-on-violations",
        action="store_true",
        help="return status 1 when any spin-lattice or parity issue is found",
    )
    args = parser.parse_args(argv)

    try:
        report = audit_discrete_levels(args.data_file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")

    counts = report["counts"]
    print(
        "AUDIT SUMMARY: "
        f"nuclei={counts['nuclei']} levels={counts['levels']} "
        f"spin_lattice_violations={counts['spin_lattice_violations']} "
        f"invalid_parity={counts['invalid_parity_records']}"
    )
    if args.fail_on_violations and (
        counts["spin_lattice_violations"] or counts["invalid_parity_records"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

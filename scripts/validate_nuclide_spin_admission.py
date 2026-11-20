#!/usr/bin/env python3
"""Fail-closed N1 admission for nuclear ground-state spin/parity records.

Input CSV columns:
  nuclide,A,J,parity,source_status,source_ref,source_version

J accepts exact integers, decimals, and fractions such as 3/2. parity is
+1/-1 (also accepts + / -). Only ADOPTED_UNIQUE with a non-empty source
reference and version can be ADMITTED. This validates the spin lattice; it
does not establish that a source's nuclear assignment is experimentally proven.
"""
from __future__ import annotations

import argparse
import csv
import sys
from fractions import Fraction
from pathlib import Path

ALLOWED_SOURCE_STATUS = {
    "ADOPTED_UNIQUE", "PROVISIONAL", "NONEXPERIMENTAL", "AMBIGUOUS", "UNKNOWN"
}
REQUIRED_COLUMNS = {
    "nuclide", "A", "J", "parity", "source_status", "source_ref", "source_version"
}


def parse_parity(value: str) -> int | None:
    value = value.strip()
    if value in ("+", "+1", "1"):
        return 1
    if value in ("-", "-1"):
        return -1
    return None


def parse_spin(value: str | int | float | Fraction) -> Fraction:
    """Parse nuclear J exactly; accepts e.g. '3/2', '1.5', and 1.5."""
    return value if isinstance(value, Fraction) else Fraction(str(value).strip())


def spin_lattice_status(a: int, j: str | int | float | Fraction) -> str:
    """Check exact 2J integrality and A/J parity compatibility."""
    try:
        spin = parse_spin(j)
    except (ValueError, ZeroDivisionError):
        return "INVALID_NOT_INTEGER_OR_HALF_INTEGER"
    if a <= 0 or spin < 0:
        return "INVALID_DOMAIN"
    twice_j = 2 * spin
    if twice_j.denominator != 1:
        return "INVALID_NOT_INTEGER_OR_HALF_INTEGER"
    if twice_j.numerator % 2 != a % 2:
        return "INVALID_A_J_PARITY_MISMATCH"
    return "VALID"


def classify_record(row: dict[str, str]) -> dict[str, str]:
    result = {
        "nuclide": row.get("nuclide", "").strip(),
        "A": row.get("A", "").strip(),
        "J": row.get("J", "").strip(),
        "parity": row.get("parity", "").strip(),
        "source_status": row.get("source_status", "").strip().upper(),
        "source_ref": row.get("source_ref", "").strip(),
        "source_version": row.get("source_version", "").strip(),
    }

    try:
        a = int(result["A"])
        spin = parse_spin(result["J"])
    except (TypeError, ValueError, ZeroDivisionError):
        result.update(admission="CONDITIONAL", reason="MISSING_OR_NONNUMERIC_A_OR_J",
                      spin_lattice="NOT_EVALUATED")
        return result

    lattice = spin_lattice_status(a, spin)
    result["spin_lattice"] = lattice
    parity = parse_parity(result["parity"])
    source_status = result["source_status"]

    if lattice.startswith("INVALID"):
        admission, reason = "REJECTED", lattice
    elif parity is None:
        admission, reason = "CONDITIONAL", "UNKNOWN_OR_INVALID_PARITY"
    elif source_status not in ALLOWED_SOURCE_STATUS:
        admission, reason = "CONDITIONAL", "UNRECOGNIZED_SOURCE_STATUS"
    elif source_status == "ADOPTED_UNIQUE" and result["source_ref"] and result["source_version"]:
        admission, reason = "ADMITTED", "VALID_LATTICE_UNIQUE_ADOPTED_SOURCE"
    elif source_status == "AMBIGUOUS":
        admission, reason = "CONDITIONAL", "AMBIGUOUS_JPI_ASSIGNMENT"
    elif source_status in ("PROVISIONAL", "NONEXPERIMENTAL"):
        admission, reason = "CONDITIONAL", "NONFINAL_OR_NONEXPERIMENTAL_ASSIGNMENT"
    else:
        admission, reason = "CONDITIONAL", "SOURCE_NOT_VERIFIED_AS_UNIQUE_ADOPTED"
    result.update(admission=admission, reason=reason)
    return result


def read_records(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError("missing required CSV columns: " + ", ".join(missing))
        return [classify_record(row) for row in reader]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="ground-state Jπ CSV")
    parser.add_argument("--output", required=True, type=Path, help="classified CSV output")
    parser.add_argument("--strict-exit", action="store_true",
                        help="return exit code 2 unless every row is ADMITTED")
    args = parser.parse_args(argv)
    try:
        rows = read_records(args.input)
        fields = ["nuclide", "A", "J", "parity", "source_status", "source_ref",
                  "source_version", "spin_lattice", "admission", "reason"]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    except (OSError, ValueError) as exc:
        print(f"N1 admission error: {exc}", file=sys.stderr)
        return 1
    counts = {key: sum(row["admission"] == key for row in rows)
              for key in ("ADMITTED", "CONDITIONAL", "REJECTED")}
    print("N1 admission counts: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    if args.strict_exit and counts["CONDITIONAL"] + counts["REJECTED"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

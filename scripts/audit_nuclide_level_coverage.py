#!/usr/bin/env python3
"""Audit RIPL-3 level-scheme metadata against CGMF discreteLevels.dat.

This is a data-lineage diagnostic, not a physics validator. It deliberately
keeps Nol, Nog, Nmax and Nc separate and never treats Nc as a level-count cap.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ISOTOPE = re.compile(r"^\s*(\d{1,3}[A-Za-z]{1,2})\s+")


@dataclass
class RiplRecord:
    symbol: str
    a: int
    z: int
    nol: int
    nog: int
    nmax: int
    nc: int
    levels: list[tuple[int, float, float, int]]


@dataclass
class CgmfRecord:
    symbol: str
    zaid: int
    ndisc: int
    levels: list[tuple[float, float, int]]


def _is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def parse_ripl(path: Path) -> dict[str, RiplRecord]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    records: dict[str, RiplRecord] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        match = ISOTOPE.match(line)
        fields = line.split()
        if not match or len(fields) < 9 or not all(_is_int(x) for x in fields[1:7]):
            i += 1
            continue
        symbol = match.group(1)
        a, z, nol, nog, nmax, nc = map(int, fields[1:7])
        # Avoid interpreting level records or continuation records as headers.
        if a <= 0 or z < 0 or nol < 0 or nog < 0 or nmax < 0 or nc < 0:
            i += 1
            continue
        levels: list[tuple[int, float, float, int]] = []
        j = i + 1
        while j < len(lines) and len(levels) < nol:
            row = lines[j]
            try:
                level_no = int(row[0:3])
                energy = float(row[4:14])
                spin = float(row[15:20])
                parity = int(row[20:23])
            except (ValueError, IndexError):
                j += 1
                continue
            # RIPL level records are numbered sequentially. Gamma continuation
            # rows do not occupy the first three fixed-width columns.
            if level_no != len(levels) + 1:
                j += 1
                continue
            levels.append((level_no, energy, spin, parity))
            j += 1
        records[symbol] = RiplRecord(symbol, a, z, nol, nog, nmax, nc, levels)
        i = max(j, i + 1)
    return records


def parse_cgmf(path: Path) -> dict[str, CgmfRecord]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    records: dict[str, CgmfRecord] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        match = ISOTOPE.match(line)
        fields = line.split()
        if not match or len(fields) < 3 or not _is_int(fields[1]) or not _is_int(fields[2]):
            i += 1
            continue
        symbol, zaid, ndisc = match.group(1), int(fields[1]), int(fields[2])
        if zaid <= 0 or ndisc < 0:
            i += 1
            continue
        levels: list[tuple[float, float, int]] = []
        j = i + 1
        while j < len(lines) and len(levels) < ndisc:
            row = lines[j].split()
            if len(row) >= 4:
                try:
                    energy, spin, parity = float(row[0]), float(row[1]), int(row[2])
                    levels.append((energy, spin, parity))
                except ValueError:
                    pass
            j += 1
        records[symbol] = CgmfRecord(symbol, zaid, ndisc, levels)
        i = max(j, i + 1)
    return records


def audit(ripl: dict[str, RiplRecord], cgmf: dict[str, CgmfRecord], selected: set[str] | None = None) -> list[dict[str, object]]:
    names = sorted(selected if selected is not None else (ripl.keys() | cgmf.keys()))
    rows = []
    for name in names:
        rr, cc = ripl.get(name), cgmf.get(name)
        if rr is None or cc is None:
            rows.append({"nuclide": name, "status": "MISSING_RIPL" if rr is None else "MISSING_CGMF"})
            continue
        unknown_jpi = sum(1 for _, _, spin, parity in rr.levels if spin < 0 or parity not in (-1, 1))
        if len(rr.levels) != rr.nol:
            status = "RIPL_PARSE_INCOMPLETE"
        elif cc.ndisc == rr.nmax and rr.nmax <= rr.nol:
            status = "MATCHES_RIPL_NMAX_CUTOFF"
        elif cc.ndisc < rr.nol:
            status = "CGMF_FEWER_THAN_RIPL_NOL_REVIEW"
        elif cc.ndisc > rr.nol:
            status = "CGMF_MORE_THAN_RIPL_NOL_REVIEW"
        else:
            status = "COUNT_MATCH"
        rows.append({
            "nuclide": name, "Z": rr.z, "A": rr.a, "ZAID": cc.zaid,
            "RIPL_Nol": rr.nol, "RIPL_Nog": rr.nog, "RIPL_Nmax": rr.nmax,
            "RIPL_Nc": rr.nc, "RIPL_level_records_parsed": len(rr.levels),
            "RIPL_unknown_J_or_parity_records": unknown_jpi,
            "CGMF_ndisc": cc.ndisc, "CGMF_level_records_parsed": len(cc.levels),
            "status": status,
            "RIPL_ground_J": rr.levels[0][2] if rr.levels else "",
            "RIPL_ground_parity": rr.levels[0][3] if rr.levels else "",
            "CGMF_ground_J": cc.levels[0][1] if cc.levels else "",
            "CGMF_ground_parity": cc.levels[0][2] if cc.levels else "",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ripl", required=True, type=Path, help="RIPL-3 levels.dat")
    parser.add_argument("--cgmf", required=True, type=Path, help="CGMF discreteLevels.dat")
    parser.add_argument("--nuclides", nargs="*", help="Optional isotope symbols, e.g. 136I 105Zr")
    parser.add_argument("--output", type=Path, help="CSV output (stdout if omitted)")
    args = parser.parse_args()
    rows = audit(parse_ripl(args.ripl), parse_cgmf(args.cgmf), set(args.nuclides) if args.nuclides else None)
    if not rows:
        print("No records selected.", file=sys.stderr)
        return 2
    stream = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.output:
            stream.close()
    if any(str(row.get("status", "")).startswith("MISSING") or row.get("status") == "RIPL_PARSE_INCOMPLETE" for row in rows):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

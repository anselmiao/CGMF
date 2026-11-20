#!/usr/bin/env python3
"""Reproducibly audit the checked-in I-136 RIPL-to-CGMF discrete-level baseline.

This is a provenance/data-integrity audit only. It does not change CGMF data,
assign nuclear levels, or claim that the RIPL level list is experimentally
complete. Hashes are calculated from raw file bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_DISCRETE_SHA256 = "c79679e4247ddf69e3766ccce0b3177fcb7b253e26fd50ff621d2721d023c80e"
EXPECTED_RIPL_SHA256 = "32088e482125829d4b6059a93c061a77713e17bad89ad21f773aebc6a5bc9547"
RIPL_LEVEL_ROW = re.compile(r"^ {0,2}\d{1,2}\s{2,}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def find_cgmf_i136(lines: list[str]) -> tuple[int, int, list[dict[str, object]]]:
    for index, line in enumerate(lines):
        fields = line.split()
        if len(fields) >= 3 and fields[0] == "136I" and fields[1] == "53136":
            ndisc = int(fields[2])
            records = []
            for offset in range(ndisc):
                row = lines[index + 1 + offset].split()
                if len(row) < 4:
                    raise ValueError("Malformed I-136 CGMF level row")
                records.append({
                    "energy_MeV": float(row[0]),
                    "spin": float(row[1]),
                    "parity": int(row[2]),
                    "half_life_s": float(row[3]),
                })
            return index + 1, ndisc, records
    raise ValueError("ZAID 53136 (136I) not found in CGMF discrete-level file")


def find_ripl_i136(lines: list[str]) -> tuple[int, dict[str, int], list[dict[str, object]]]:
    for index, line in enumerate(lines):
        if not line.startswith("136I"):
            continue
        # Match the exact fixed-width fields consumed by ripl2levels.cpp:
        # substr(15,5)=Nol, substr(20,5)=Nog, substr(25,5)=Nmax,
        # substr(30,5)=Nc.
        if len(line) < 35:
            raise ValueError("Malformed fixed-width RIPL I-136 header")
        counts = {
            "Nol": int(line[15:20]),
            "Nog": int(line[20:25]),
            "Nmax": int(line[25:30]),
            "Nc": int(line[30:35]),
        }
        levels = []
        for row in lines[index + 1:]:
            if len(levels) >= counts["Nol"]:
                break
            if not RIPL_LEVEL_ROW.match(row):
                continue
            try:
                level_no = int(row[0:3])
                energy = float(row[4:14])
                spin = float(row[15:20])
                parity = int(row[20:23])
            except (ValueError, IndexError):
                continue
            if level_no != len(levels) + 1:
                continue
            levels.append({
                "level": level_no,
                "energy_MeV": energy,
                "spin_field": spin,
                "parity_field": parity,
                "evaluated_Jpi_text": row[46:64].strip(),
            })
        if len(levels) != counts["Nol"]:
            raise ValueError(
                f"RIPL I-136 level parse incomplete: {len(levels)}/{counts['Nol']}"
            )
        return index + 1, counts, levels
    raise ValueError("I-136 not found in RIPL-3 file")


def build_report(discrete_path: Path, ripl_path: Path) -> dict[str, object]:
    discrete_hash = sha256(discrete_path)
    ripl_hash = sha256(ripl_path)
    discrete_lines = read_text(discrete_path)
    ripl_lines = read_text(ripl_path)
    cgmf_line, ndisc, cgmf_levels = find_cgmf_i136(discrete_lines)
    ripl_line, ripl_counts, ripl_levels = find_ripl_i136(ripl_lines)

    first_ripl = ripl_levels[0]
    first_cgmf = cgmf_levels[0] if cgmf_levels else None
    ground_state_match = bool(
        first_cgmf
        and abs(float(first_ripl["energy_MeV"]) - float(first_cgmf["energy_MeV"])) < 1e-9
        and abs(float(first_ripl["spin_field"]) - float(first_cgmf["spin"])) < 1e-9
        and int(first_ripl["parity_field"]) == int(first_cgmf["parity"])
    )
    return {
        "scope": "I-136 / ZAID 53136",
        "classification": "data provenance and integrity audit; not a physics validation",
        "files": {
            str(discrete_path): {
                "bytes": discrete_path.stat().st_size,
                "sha256": discrete_hash,
                "expected_sha256": EXPECTED_DISCRETE_SHA256,
                "matches_frozen_baseline": discrete_hash == EXPECTED_DISCRETE_SHA256,
            },
            str(ripl_path): {
                "bytes": ripl_path.stat().st_size,
                "sha256": ripl_hash,
                "expected_sha256": EXPECTED_RIPL_SHA256,
                "matches_frozen_baseline": ripl_hash == EXPECTED_RIPL_SHA256,
            },
        },
        "records": {
            "CGMF": {
                "line_1based": cgmf_line,
                "ndisc": ndisc,
                "levels": cgmf_levels,
            },
            "RIPL3": {
                "line_1based": ripl_line,
                "counts": ripl_counts,
                "parsed_level_count": len(ripl_levels),
                "levels": ripl_levels,
            },
        },
        "checks": {
            "RIPL_Nol_equals_parsed_level_count": ripl_counts["Nol"] == len(ripl_levels),
            "CGMF_ndisc_equals_RIPL_Nmax": ndisc == ripl_counts["Nmax"],
            "CGMF_ndisc_equals_RIPL_Nc": ndisc == ripl_counts["Nc"],
            "CGMF_ground_state_matches_RIPL_first_level": ground_state_match,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ripl", type=Path, default=Path("data/ripl3-levels.dat"))
    parser.add_argument("--cgmf", type=Path, default=Path("data/discreteLevels.dat"))
    parser.add_argument("--allow-hash-change", action="store_true",
                        help="Report changed hashes without failing the frozen-baseline check")
    args = parser.parse_args()
    report = build_report(args.cgmf, args.ripl)
    print(json.dumps(report, indent=2, sort_keys=True))
    hashes_ok = all(item["matches_frozen_baseline"] for item in report["files"].values())
    checks_ok = all(report["checks"].values())
    return 0 if checks_ok and (hashes_ok or args.allow_hash_change) else 1


if __name__ == "__main__":
    raise SystemExit(main())

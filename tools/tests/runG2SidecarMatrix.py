#!/usr/bin/env python3
"""Run the complete G2 sidecar configuration matrix against native CGMF cases."""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd, env, log_path, log_prefix=b""):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("wb") as log:
        if log_prefix:
            log.write(log_prefix)
        subprocess.run(
            command, cwd=cwd, env=env, stdout=log,
            stderr=subprocess.STDOUT, check=True
        )


def resolve_discrete_level_file(cwd, env, binary):
    """Mirror CGMF's current-directory-first data-file lookup for audit metadata."""
    filename = "discreteLevels.dat"
    local_file = cwd / filename
    if local_file.is_file():
        return local_file.resolve(), "current-directory"

    configured_dir = env.get("CGMFDATA", "")
    if configured_dir:
        data_dir = Path(configured_dir)
        if not data_dir.is_absolute():
            data_dir = cwd / data_dir
        candidate = data_dir / filename
        return (candidate.resolve(), "CGMFDATA") if candidate.is_file() else (None, "CGMFDATA-missing")

    config_header = binary.resolve().parents[2] / "libcgmf" / "cgmf_config.h"
    macros = {}
    if config_header.is_file():
        for line in config_header.read_text(encoding="utf-8").splitlines():
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0] == "#define" and parts[1] in {"INSTALL_DATADIR", "BUILD_DATADIR"}:
                macros[parts[1]] = parts[2].strip().strip('"')
    for macro in ("INSTALL_DATADIR", "BUILD_DATADIR"):
        directory = macros.get(macro)
        if directory and Path(directory).is_dir():
            candidate = Path(directory) / filename
            if candidate.is_file():
                return candidate.resolve(), macro
            return None, f"{macro}-directory-without-file"
    return None, "no-readable-candidate"


def discrete_level_audit_prefix(cwd, env, binary):
    path, source = resolve_discrete_level_file(cwd, env, binary)
    lines = [
        "[CGMF DATA AUDIT PYTHON] CGMFDATA="
        + (env.get("CGMFDATA") if env.get("CGMFDATA") is not None else "<unset>"),
        f"[CGMF DATA AUDIT PYTHON] selected_by={source}",
    ]
    if path is None:
        lines.append("[CGMF DATA AUDIT PYTHON] selected_file=<unresolved>")
    else:
        lines.append(f"[CGMF DATA AUDIT PYTHON] selected_file={path}")
        lines.append(f"[CGMF DATA AUDIT PYTHON] sha256={sha256(path)}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def read_audit(path, seed_start, event_count):
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"event", "seed", "calls", "fnv1a64"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: RNG audit header missing required columns")
        rows = list(reader)
    expected_events = list(range(1, event_count + 1))
    expected_seeds = list(range(seed_start, seed_start + event_count))
    try:
        events = [int(row["event"]) for row in rows]
        seeds = [int(row["seed"]) for row in rows]
        calls = [int(row["calls"]) for row in rows]
        digests = [int(row["fnv1a64"]) for row in rows]
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError(f"{path}: malformed RNG audit row: {exc}") from exc
    if events != expected_events:
        raise ValueError(
            f"{path}: event audit coverage mismatch; expected 1..{event_count}, "
            f"got {len(events)} rows and event IDs {events[:3]}..{events[-3:]}"
        )
    if seeds != expected_seeds:
        raise ValueError(
            f"{path}: RNG seed coverage mismatch; expected {seed_start}..{seed_start + event_count - 1}, "
            f"got {len(seeds)} rows and seeds {seeds[:3]}..{seeds[-3:]}"
        )
    if any(seed < 0 for seed in seeds):
        raise ValueError(f"{path}: negative RNG seed")
    if any(call_count <= 0 for call_count in calls):
        raise ValueError(f"{path}: event with no RNG calls")
    if any(digest < 0 or digest >= 2**64 for digest in digests):
        raise ValueError(f"{path}: FNV-1a digest outside uint64 range")
    return {"rows": len(rows), "event_start": events[0], "event_end": events[-1],
            "seed_start": seeds[0], "seed_end": seeds[-1],
            "min_calls": min(calls), "max_calls": max(calls)}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stdout_without_data_audit(path):
    """Remove opt-in provenance lines before the simulation stdout comparison."""
    return b"".join(
        line for line in path.read_bytes().splitlines(keepends=True)
        if not line.startswith(b"[CGMF DATA AUDIT")
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--mixed-validator", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    binary = args.binary.resolve()
    validator = args.validator.resolve()
    mixed_validator = args.mixed_validator.resolve()
    matrix_path = args.matrix.resolve()
    output_root = args.output_dir.resolve()
    for required_path in (binary, validator, mixed_validator, matrix_path):
        if not required_path.is_file():
            raise FileNotFoundError(required_path)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    cases = matrix["cases"]
    names = [case["name"] for case in cases]
    if len(names) != len(set(names)):
        raise ValueError("matrix case names must be unique")

    output_root.mkdir(parents=True, exist_ok=True)
    results = []
    for number, case in enumerate(cases, 1):
        name = case["name"]
        energy = str(case["energy_MeV"])
        isotope = int(case["ZAID"])
        seed_start = int(case.get("seed_start", 1))
        event_count = int(case.get("events", matrix.get("default_events", 40)))
        if seed_start < 1 or event_count < 1:
            raise ValueError(f"{name}: seed_start and events must be positive")
        case_root = output_root / name
        on_dir, off_dir, baseline_dir = (
            case_root / "on", case_root / "off", case_root / "baseline"
        )
        for directory in (on_dir, off_dir, baseline_dir):
            directory.mkdir(parents=True, exist_ok=True)

        common = [str(binary), "-n", str(event_count), "-e", energy,
                  "-i", str(isotope)]
        if seed_start != 1:
            common += ["-s", str(seed_start)]
        common += ["-f", "histories.cgmf"]
        run_id = "ci-g2-" + name

        on_env = os.environ.copy()
        on_env["CGMF_G2_SIDECAR"] = str((on_dir / "neutron-transition.jsonl").resolve())
        on_env["CGMF_G2_MIXED_HISTORY_SIDECAR"] = str((on_dir / "mixed-history.jsonl").resolve())
        on_env["CGMF_G2_RUN_ID"] = run_id
        on_env["CGMF_RNG_AUDIT"] = "1"
        on_env["CGMF_RNG_AUDIT_FILE"] = str((on_dir / "rng-audit.tsv").resolve())
        on_env["CGMF_DATA_AUDIT"] = "1"

        off_env = os.environ.copy()
        off_env.pop("CGMF_G2_SIDECAR", None)
        off_env.pop("CGMF_G2_MIXED_HISTORY_SIDECAR", None)
        off_env.pop("CGMF_G2_RUN_ID", None)
        off_env["CGMF_RNG_AUDIT"] = "1"
        off_env["CGMF_RNG_AUDIT_FILE"] = str((off_dir / "rng-audit.tsv").resolve())

        baseline_env = os.environ.copy()
        baseline_env.pop("CGMF_G2_SIDECAR", None)
        baseline_env.pop("CGMF_G2_MIXED_HISTORY_SIDECAR", None)
        baseline_env.pop("CGMF_G2_RUN_ID", None)
        baseline_env.pop("CGMF_RNG_AUDIT", None)
        baseline_env.pop("CGMF_RNG_AUDIT_FILE", None)

        print(f"[{number}/{len(cases)}] {name}: ZAID={isotope}, En={energy} MeV, "
              f"event_ids=1..{event_count}, seeds={seed_start}..{seed_start + event_count - 1}", flush=True)
        data_audit_prefix = discrete_level_audit_prefix(on_dir, on_env, binary)
        run_command(common, on_dir, on_env, on_dir / "sidecar-on.stdout", data_audit_prefix)
        run_command(common, off_dir, off_env, off_dir / "sidecar-off.stdout")
        run_command(common, baseline_dir, baseline_env, baseline_dir / "baseline.stdout")

        jsonl = on_dir / "neutron-transition.jsonl"
        mixed_jsonl = on_dir / "mixed-history.jsonl"
        history_on = on_dir / "histories.cgmf.0"
        history_off = off_dir / "histories.cgmf.0"
        history_baseline = baseline_dir / "histories.cgmf.0"
        stdout_on = on_dir / "sidecar-on.stdout"
        stdout_off = off_dir / "sidecar-off.stdout"
        stdout_baseline = baseline_dir / "baseline.stdout"
        audit_on = on_dir / "rng-audit.tsv"
        audit_off = off_dir / "rng-audit.tsv"
        for path in (jsonl, mixed_jsonl, history_on, history_off, history_baseline,
                     stdout_on, stdout_off, stdout_baseline, audit_on, audit_off):
            if not path.is_file():
                raise FileNotFoundError(f"{name}: expected output missing: {path}")

        subprocess.run(
            [sys.executable, str(validator), str(jsonl),
             "--expected-events", str(event_count),
             "--run-id", run_id],
            cwd=case_root, check=True
        )
        subprocess.run(
            [sys.executable, str(mixed_validator), str(mixed_jsonl),
             "--neutron-jsonl", str(jsonl),
             "--expected-events", str(event_count),
             "--run-id", run_id],
            cwd=case_root, check=True
        )
        audit_summary = read_audit(audit_on, seed_start, event_count)
        read_audit(audit_off, seed_start, event_count)

        comparisons = {
            "histories_on_off": history_on.read_bytes() == history_off.read_bytes(),
            "histories_on_baseline": history_on.read_bytes() == history_baseline.read_bytes(),
            "stdout_on_off": stdout_without_data_audit(stdout_on) == stdout_without_data_audit(stdout_off),
            "stdout_on_baseline": stdout_without_data_audit(stdout_on) == stdout_without_data_audit(stdout_baseline),
            "rng_audit_on_off": audit_on.read_bytes() == audit_off.read_bytes(),
        }
        failed = [key for key, passed in comparisons.items() if not passed]
        if failed:
            raise RuntimeError(f"{name}: sidecar non-interference comparison failed: {failed}")

        records = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
        sides = {}
        for side in ("LF", "HF"):
            sides[side] = sum(row["fragment_side"] == side for row in records)
        result = {
            "name": name, "ZAID": isotope, "energy_MeV": energy,
            "seed_start": seed_start, "seed_end": seed_start + event_count - 1,
            "event_id_start": 1, "event_id_end": event_count, "events_run": event_count,
            "neutron_records": len(records),
            "mixed_fragment_summaries": len(mixed_jsonl.read_text(encoding="utf-8").splitlines()),
            "emitting_events": len({row["event_id"] for row in records}),
            "LF_records": sides["LF"], "HF_records": sides["HF"],
            "event_fragment_groups": len({(row["event_id"], row["fragment_side"]) for row in records}),
            "rng_audit": audit_summary, "comparisons": comparisons,
            "histories_sha256": sha256(history_on),
            "stdout_sha256": sha256(stdout_on),
            "rng_audit_sha256": sha256(audit_on),
        }
        results.append(result)
        (case_root / "result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )

    summary = {
        "schema": "cgmf.g2.sidecar-matrix.v1",
        "case_count": len(results),
        "total_events_per_mode": sum(item["events_run"] for item in results),
        "all_passed": True,
        "cases": results,
    }
    (output_root / "matrix-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# CGMF G2 neutron sidecar matrix",
        "",
        f"- Cases passed: {len(results)}",
        f"- Events per execution mode: {summary['total_events_per_mode']}",
        "- For every case: legacy and mixed-history JSONL validation, RNG audit coverage, histories/stdout bytewise "
        "comparison (on/off/baseline), and RNG audit bytewise comparison (on/off).",
        "",
        "| Case | ZAID | En (MeV) | Event IDs | RNG seeds | Neutron records | LF | HF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| {item['name']} | {item['ZAID']} | {item['energy_MeV']} | "
            f"1–{item['events_run']} | {item['seed_start']}–{item['seed_end']} | "
            f"{item['neutron_records']} | {item['LF_records']} | {item['HF_records']} |"
        )
    (output_root / "matrix-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"G2 matrix passed: {len(results)} cases; "
          f"{summary['total_events_per_mode']} events per execution mode.", flush=True)


if __name__ == "__main__":
    main()

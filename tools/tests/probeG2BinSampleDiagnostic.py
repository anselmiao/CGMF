#!/usr/bin/env python3
"""Same-seed A/B probe: bin-sample diagnostics off vs on, including expected failure."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

from runG2SidecarMatrix import discrete_level_audit_prefix, stdout_without_diagnostics


def run_probe(binary, output_root, events):
    output_root.mkdir(parents=True, exist_ok=True)
    variants = {}
    for label, diagnostic in (("off", False), ("on", True)):
        work = output_root / label
        work.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["CGMF_G2_SIDECAR"] = str((work / "neutron-transition.jsonl").resolve())
        env["CGMF_G2_MIXED_HISTORY_SIDECAR"] = str((work / "mixed-history.jsonl").resolve())
        env["CGMF_G2_RUN_ID"] = "ci-g2-cf252-sf-diagnostic-ab"
        env["CGMF_G2_POPULATION_DIAGNOSTIC"] = "1"
        env["CGMF_RNG_AUDIT"] = "1"
        env["CGMF_RNG_AUDIT_FILE"] = str((work / "rng-audit.tsv").resolve())
        env["CGMF_DATA_AUDIT"] = "1"
        if diagnostic:
            env["CGMF_G2_BIN_SAMPLE_DIAGNOSTIC"] = "1"
        else:
            env.pop("CGMF_G2_BIN_SAMPLE_DIAGNOSTIC", None)

        command = [str(binary), "-n", str(events), "-e", "0.0", "-i", "98252",
                   "-f", "histories.cgmf"]
        log = work / "run.stdout"
        prefix = discrete_level_audit_prefix(work, env, binary)
        with log.open("wb") as stream:
            stream.write(prefix)
            completed = subprocess.run(
                command, cwd=work, env=env, stdout=stream,
                stderr=subprocess.STDOUT, check=False
            )
        variants[label] = {"work": work, "returncode": completed.returncode}
        print(f"{label}: exit={completed.returncode}", flush=True)

    off = variants["off"]
    on = variants["on"]
    if off["returncode"] != on["returncode"]:
        raise RuntimeError(
            "diagnostic toggle changed process exit status: "
            f"off={off['returncode']} on={on['returncode']}"
        )

    names = ("histories.cgmf.0", "rng-audit.tsv",
             "neutron-transition.jsonl", "mixed-history.jsonl")
    comparisons = {}
    for name in names:
        left = off["work"] / name
        right = on["work"] / name
        if not left.is_file() or not right.is_file():
            raise FileNotFoundError(f"probe output missing: {left if not left.is_file() else right}")
        comparisons[name] = left.read_bytes() == right.read_bytes()
        if not comparisons[name]:
            raise RuntimeError(f"diagnostic toggle changed {name}")

    stdout_equal = stdout_without_diagnostics(off["work"] / "run.stdout") == stdout_without_diagnostics(on["work"] / "run.stdout")
    comparisons["stdout_without_diagnostics"] = stdout_equal
    if not stdout_equal:
        raise RuntimeError("diagnostic toggle changed normalized stdout")

    report = output_root / "diagnostic-ab-report.txt"
    report.write_text(
        "CGMF_G2_BIN_SAMPLE_DIAGNOSTIC same-seed A/B probe\\n"
        f"events={events}; ZAID=98252; energy_MeV=0.0; seeds=1..{events}\\n"
        f"exit_off={off['returncode']}; exit_on={on['returncode']}\\n"
        + "\\n".join(f"{key}={value}" for key, value in comparisons.items())
        + "\\n",
        encoding="utf-8"
    )
    print(f"Diagnostic A/B non-interference verified: {len(comparisons)} comparisons", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--events", type=int, default=200)
    args = parser.parse_args()
    binary = args.binary.resolve()
    if not binary.is_file():
        raise FileNotFoundError(binary)
    if args.events < 1:
        raise ValueError("--events must be positive")
    run_probe(binary, args.output_dir.resolve(), args.events)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Post-hoc decomposition of pair-shared TXE from LF-local spin/parity.

This diagnostic follows the completed, predeclared v2 fragment-state ablation.
It asks whether LF spin/parity add predictive information after conditioning
on the event-level sum of the two initial fragment excitation energies.
It does not change or replace the v2 primary decision rule.
"""
import argparse
import json
from pathlib import Path

import g2FragmentStateAblation as base

SCHEMA = "cgmf.g2.shared-energy-decomposition.v1"
RIDGE = 1.0
BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20261119


def add_pair_txe(records):
    for row in records:
        row["TXE_pair_sum"] = [
            float(row["diagnostics"]["TXE_sum_initial_fragment_excitation_MeV"])
        ]
    return records


def feature_builders(row):
    return {
        "H_local": row["H_local"],
        "H+TXE_pair_sum": row["H_local"] + row["TXE_pair_sum"],
        "H+TXE+L_spin_parity": row["H_local"] + row["TXE_pair_sum"] + row["L_spin"] + row["L_parity"],
        "H+TXE+L_parity": row["H_local"] + row["TXE_pair_sum"] + row["L_parity"],
        "H+TXE+L_spin": row["H_local"] + row["TXE_pair_sum"] + row["L_spin"],
        "H_local+K": row["H_local"] + row["shared_kinematics"],
        "H+TXE+K": row["H_local"] + row["TXE_pair_sum"] + row["shared_kinematics"],
        "H+TXE+L_spin_parity+K": row["H_local"] + row["TXE_pair_sum"] + row["L_spin"] + row["L_parity"] + row["shared_kinematics"],
        "H+L_excitation_reference": row["H_local"] + row["L_excitation"],
        "H+L_intrinsic_reference": row["H_local"] + row["L_intrinsic"],
    }


def run(train_paths, test_paths, output, ridge=RIDGE,
        n_boot=BOOTSTRAP, bootstrap_seed=BOOTSTRAP_SEED):
    train, train_runs, train_seeds, _ = base.read_split(train_paths)
    test, test_runs, test_seeds, diagnostics = base.read_split(test_paths)
    base.validate_disjoint_runs(train_runs, test_runs)
    base.validate_disjoint_seed_sets(train_seeds, test_seeds)
    if len(train) < 20 or len(test) < 20:
        raise ValueError("need at least 20 complete LF/HF event pairs in train and test")
    add_pair_txe(train)
    add_pair_txe(test)

    names = list(feature_builders(train[0]))
    for row in train + test:
        for name, values in feature_builders(row).items():
            row[name] = values

    fits, models = {}, {}
    for name in names:
        fits[name] = base.fit_predict(train, test, name, ridge)
        models[name] = {
            "feature_count": len(train[0][name]),
            "mean_train_SD_normalized_RMSE": fits[name]["mean_train_SD_normalized_RMSE"],
            "targets": fits[name]["targets"],
        }

    comparisons = {
        "H+TXE_vs_H": base.paired_bootstrap_delta(
            fits["H+TXE_pair_sum"], fits["H_local"], n_boot, bootstrap_seed),
        "H+TXE+L_spin_parity_vs_H+TXE": base.paired_bootstrap_delta(
            fits["H+TXE+L_spin_parity"], fits["H+TXE_pair_sum"], n_boot, bootstrap_seed),
        "H+TXE+K_vs_H+K": base.paired_bootstrap_delta(
            fits["H+TXE+K"], fits["H_local+K"], n_boot, bootstrap_seed),
        "H+TXE+L_spin_parity+K_vs_H+TXE+K": base.paired_bootstrap_delta(
            fits["H+TXE+L_spin_parity+K"], fits["H+TXE+K"], n_boot, bootstrap_seed),
        "H+L_excitation_reference_vs_H": base.paired_bootstrap_delta(
            fits["H+L_excitation_reference"], fits["H_local"], n_boot, bootstrap_seed),
        "H+L_intrinsic_reference_vs_H": base.paired_bootstrap_delta(
            fits["H+L_intrinsic_reference"], fits["H_local"], n_boot, bootstrap_seed),
        "H+TXE+L_parity_vs_H+TXE": base.paired_bootstrap_delta(
            fits["H+TXE+L_parity"], fits["H+TXE_pair_sum"], n_boot, bootstrap_seed),
        "H+TXE+L_spin_vs_H+TXE": base.paired_bootstrap_delta(
            fits["H+TXE+L_spin"], fits["H+TXE_pair_sum"], n_boot, bootstrap_seed),
    }

    mean_txe = sum(d["TXE_sum_initial_fragment_excitation_MeV"] for d in diagnostics) / len(diagnostics)
    sd_txe = (sum((d["TXE_sum_initial_fragment_excitation_MeV"] - mean_txe) ** 2
                  for d in diagnostics) / len(diagnostics)) ** 0.5
    result = {
        "schema": SCHEMA,
        "analysis_status": "POSTHOC_DIAGNOSTIC_NOT_A_REPLACEMENT_FOR_V2_PRIMARY_TEST",
        "train_files": [str(x) for x in train_paths],
        "test_files": [str(x) for x in test_paths],
        "n_train_events": len(train),
        "n_test_events": len(test),
        "train_run_ids": sorted(train_runs),
        "test_run_ids": sorted(test_runs),
        "train_rng_seed_ranges": base.contiguous_ranges(train_seeds),
        "test_rng_seed_ranges": base.contiguous_ranges(test_seeds),
        "ridge_lambda": ridge,
        "bootstrap_replicates": n_boot,
        "bootstrap_seed": bootstrap_seed,
        "targets": base.TARGETS,
        "feature_groups": {
            "H_local": ["HF A", "HF Z", "HF parity_index", "HF excitation_MeV", "HF spin_stored"],
            "TXE_pair_sum": ["LF initial excitation_MeV + HF initial excitation_MeV"],
            "L_nonenergy_local": ["LF parity_index", "LF spin_stored"],
            "K": ["LF pre-fragment momentum vector (3 components)", "HF pre-fragment momentum vector (3 components)"],
        },
        "models": models,
        "paired_bootstrap_comparisons": comparisons,
        "heldout_event_state_diagnostics": {
            "TXE_sum_initial_fragment_excitation_MeV": {"mean": mean_txe, "sd": sd_txe}
        },
        "interpretation_limits": [
            "This is a post-hoc decomposition of the completed v2 analysis; it does not replace or modify the v2 primary decision rule.",
            "TXE_pair_sum is the conventional derived sum of the two recorded initial fragment excitation energies, not an independent primitive observation or a 气论 Q variable.",
            "Given HF excitation in H_local, adding LF excitation also supplies information about the pair-shared total excitation budget; this diagnostic separates that pair-level coordinate from LF spin/parity.",
            "A stable predictive increment would still be conditional association, not direct LF-to-HF causation.",
            "The K block remains a shared/constraint-related kinematic control, not an independent cross-fragment mechanism.",
            "All fits use training-only standardization, fixed ridge lambda, and complete held-out LF/HF event-pair bootstrap units.",
        ],
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for fit_result in fits.values():
        fit_result.pop("_event_error2", None)
    print(f"wrote {output}; train={len(train)} test={len(test)}; ridge={ridge}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", nargs="+", required=True)
    parser.add_argument("--test", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ridge", type=float, default=RIDGE)
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP)
    parser.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED)
    args = parser.parse_args()
    if args.ridge <= 0 or args.bootstrap < 100:
        raise ValueError("ridge must be positive and bootstrap count must be >=100")
    run(args.train, args.test, args.output, args.ridge, args.bootstrap, args.bootstrap_seed)


if __name__ == "__main__":
    main()

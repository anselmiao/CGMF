# G2 event-state diagnostics and held-out-run model competition v1

## Purpose

This analysis moves beyond within-sample cross-fragment correlations. It asks whether LF history summaries improve prediction of HF history summaries on a **different random-seed run**, after controlling for the recorded initial event/fragment state.

## Event-level state diagnostics

The mixed-history sidecar supplies these raw simulation fields: fragment A/Z, initial excitation, stored spin, parity index, and pre-fragment momentum vector. The analysis derives:

- `TXE_sum_initial_fragment_excitation_MeV = E*_L + E*_H`;
- `momentum_closure_MeV_c = |p_L + p_H|`;
- `TKE_nonrel_proxy_MeV = |p_L|^2/(2 A_L u) + |p_H|^2/(2 A_H u)`, with `u = 931.49410242 MeV/c^2`.

TXE is a sum of the two recorded initial fragment excitation fields. The TKE quantity is only a nonrelativistic proxy using mass number times the atomic mass unit; it is **not** a separately recorded or independently validated CGMF TKE observable. These are conventional derived diagnostics, not primitive 气论 state variables. The momentum-closure norm is a diagnostic of the stored pre-fragment vectors, not a complete conservation audit of all emitted particles.

## Predictive models

All models predict four HF history outcomes: neutron multiplicity, total neutron Lab energy, gamma multiplicity, and total gamma CM energy. They use the same training events and fixed ridge regression (`lambda=1` by default).

- **M1 — recorded initial state:** both fragments' A/Z, excitation, stored spin/parity and pre-fragment momentum vectors. No LF transition-history summaries.
- **M2 — shared-budget feature expansion:** M1 plus derived TXE, the TKE proxy, excitation asymmetry and TXE×TKE-proxy interaction. These are deterministic transformations of M1 fields, so M2 tests a nonlinear feature expansion; it does not add independent measured information or establish an energy-budget mechanism.
- **M3 — incremental LF history:** M2 plus LF neutron/gamma/internal-conversion history summaries. Its held-out improvement is the relevant test of whether opposite-fragment history contributes predictive information beyond the recorded initial state and the chosen budget feature expansion.

Inputs are explicitly separated into `--train` and `--test` files. The script rejects overlapping `run_id`s, so event-level random splitting within one simulation run cannot masquerade as independent-seed validation. Event IDs are local to each file.

## Interpretation

Compare held-out normalized RMSE across models, targets, and both train/test directions. Paired bootstrap intervals resample complete held-out LF/HF event pairs (not individual particles) and report the change in mean train-SD-normalized RMSE versus M1. M2 improvement is evidence only for the chosen feature expansion. M3 improvement would show incremental prediction from LF history under this model and split, not direct LF→HF causation: omitted common causes (including unrecorded scission configuration and full angular-momentum coupling) remain possible. No detector response is applied.

A single pair of 200-event CI seeds is a software/analysis smoke test, not a stable scientific estimate. The next data-quality gate is more independent Pu-239 thermal seeds and larger event counts, followed by Cf-252, U-235 and incident-energy comparisons. Do not pool different fission systems or incident energies as interchangeable seed replicates.

## Example

```bash
python3 tools/analysis/g2EventStateModelCompetition.py \
  --train run-seed-1/mixed-history.jsonl \
  --test run-seed-201/mixed-history.jsonl \
  --output results/seed1-to-seed201.json
```

Run the reverse direction as a separate fold. Report the seed/run IDs, event counts, fixed ridge value, per-target RMSE, paired event-bootstrap intervals and all three models; do not select a model based on the best direction alone.

# G2 LF/HF fragment-state ablation v2

## Question

Run #74 showed that the earlier LF block did not add a stable increment beyond HF state. That LF block included A/Z, however, which are conserved complements in a fixed-parent fission event and therefore should not be treated as independent LF-local information.

This revision separates LF conserved-complement fields from LF intrinsic fields and tests whether LF parity, excitation, or stored spin add predictive information beyond HF's own state.

## Feature blocks

- HF conditioning state: HF A, Z, parity index, initial excitation, stored spin.
- LF conserved-complement block: LF A and Z, reported separately and excluded from the primary intrinsic-information test.
- LF intrinsic block: LF parity index, initial excitation, and stored spin.
- Kinematic block K: both recorded pre-fragment momentum vectors, kept separate because they are linked by event-level momentum constraints.

TXE and the TKE proxy remain excluded as separate columns because they are deterministic transforms of recorded fields. No LF transition-history features enter this analysis.

## Models and comparisons

Primary:
1. H-local
2. H-local + LF intrinsic (parity, excitation, stored spin)
3. H-local + K
4. H-local + LF intrinsic + K

Decomposition/diagnostics:
- H-local + LF parity only
- H-local + LF excitation only
- H-local + LF stored spin only
- H-local + LF A/Z (conserved-complement diagnostic only)
- LF intrinsic only versus H-local

Single-field comparisons are exploratory decompositions, not independent confirmatory tests. The A/Z diagnostic must not be interpreted as independent cross-fragment information.

## Fixed protocol

- Same three independent seed folds: train 1–400/test 401–600; train 1–200 plus 401–600/test 201–400; train 201–600/test 1–200.
- Each fold: 400 training and 200 held-out complete LF/HF event pairs.
- RNG audit files exactly cover sidecar event IDs; seeds unique within runs and disjoint across train/test.
- Four unchanged HF targets: neutron count, total neutron Lab energy, gamma count, total gamma CM energy.
- Ridge lambda = 1.0; training-only standardization; 2,000 paired-event bootstrap replicates; seed 20261119.
- No test-driven feature or hyperparameter selection.

## Decision rule

For the primary comparison, report candidate-minus-reference mean train-SD-normalized RMSE and paired 95% bootstrap intervals. A reproducible LF intrinsic predictive increment requires the interval to lie below zero in all three folds, both without K and with K controlled. Intervals crossing zero mean the increment is not identified under this sample size and model.

Even a stable gain establishes conditional predictive information only. Omitted common causes, including scission configuration and complete angular-momentum coupling, remain possible; this is not a causal identification design.

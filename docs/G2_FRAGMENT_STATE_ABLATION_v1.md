# G2 LF/HF fragment-state ablation v1

## Question

The earlier M1 model included both LF and HF initial-state fields. Its held-out advantage over an intercept-only model did not identify whether the predictive information came from the HF fragment's own initial state or from LF state available beyond the HF state.

This analysis isolates that distinction using the existing three independent Pu-239 thermal seed ranges from Run #73. It does not rerun CGMF or alter the seed matrix.

## Feature blocks

- HF-local intrinsic state: HF A, Z, parity index, initial excitation, and stored spin.
- LF-local intrinsic state: the corresponding five LF fields.
- Kinematic block K: both recorded pre-fragment momentum vectors (six components). K is kept separate because the vectors are linked by event-level momentum constraints; it must not be described as a direct LF-to-HF mechanism.

TXE and the TKE proxy are excluded as separate columns because they are deterministic transforms of the state fields. No LF transition-history features enter this ablation.

## Models

1. H-local
2. L-local
3. L+H-local
4. H-local+K
5. L+H-local+K

The primary comparisons are L+H-local versus H-local, and L+H-local+K versus H-local+K. The second comparison controls for the same recorded momentum block on both sides. L-local versus H-local is descriptive only.

## Fixed protocol

- Three existing folds: train 1–400/test 401–600; train 1–200 plus 401–600/test 201–400; train 201–600/test 1–200.
- Each fold has 400 training and 200 held-out complete LF/HF event pairs.
- RNG audit files must exactly cover sidecar event IDs, contain unique seeds, and be disjoint between train and test.
- Four unchanged HF targets: neutron count, total neutron Lab energy, gamma count, total gamma CM energy.
- Ridge lambda = 1.0, training-only feature standardization, 2,000 paired-event bootstrap replicates, seed 20261119.
- No test-driven feature or hyperparameter selection.

## Decision rule and interpretation

For each primary comparison, report candidate-minus-reference mean training-SD-normalized RMSE and the paired 95% bootstrap interval. A reproducible incremental predictive signal requires the interval to lie below zero in all three folds. Intervals crossing zero mean the extra LF-local predictive contribution is not identified at this sample size and under this model.

Even a stable gain would establish conditional predictive information only. Omitted common causes, including scission configuration and complete angular-momentum coupling, remain possible; this protocol is not a causal identification design.

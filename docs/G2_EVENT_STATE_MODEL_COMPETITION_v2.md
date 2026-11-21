# G2 event-state model competition v2

## Purpose

This stage asks whether recorded shared initial state predicts the opposite fragment's de-excitation history, whether one predeclared nonlinear energy-coordinate interaction adds out-of-seed predictive value, and whether LF history summaries add anything beyond that.

## Models

- M0: intercept-only training-mean baseline.
- M1: recorded initial LF/HF state (A/Z, excitation, stored spin, parity index and raw momentum vectors).
- M2: M1 plus one nonlinear `TXE × TKE_proxy` term. TXE and TKE proxy are deterministic transformations of M1 inputs, so their linear forms are not added as duplicate columns. The interaction is residualized against M1 using training data only; this tests only its nonlinear component not linearly predictable from M1.
- M3: M2 plus LF neutron/gamma/internal-conversion history summaries.

All models predict four HF targets: neutron count, neutron total Lab energy, gamma count, and gamma total CM energy. This is a predictive comparison, not a causal test.

## Event-state diagnostics

- TXE = stored initial LF excitation + stored initial HF excitation.
- TKE proxy = `|p_L|²/(2 A_L u) + |p_H|²/(2 A_H u)`, with `u=931.49410242 MeV/c²`. This is a nonrelativistic A*u proxy, not a validated CGMF TKE observable.
- Momentum closure = `|p_L+p_H|` from the stored pre-fragment momentum vectors.

Raw simulation fields and derived conventional quantities remain separately labelled. None is asserted to be a primitive 气论 state variable.

## Independence gate

Distinct `run_id` values are insufficient to establish independent random-seed replication. Each input JSONL must have a sibling `rng-audit.tsv`; the analysis verifies exact event coverage, unique seeds within each run, no overlap among training runs, and no overlap between training and held-out seeds. The CI matrix validator also rejects overlapping seed ranges for the same ZAID and incident energy before simulation.

The Pu-239 thermal CI design uses three disjoint ranges:

- training range A: seeds 1–200;
- held-out range B: seeds 201–400;
- training range C: seeds 401–600.

The two directions are evaluated: A+C train / B test, then B train / A+C test. Event bootstrap resamples complete held-out LF/HF event pairs. Seed ranges, rather than run labels, establish the split.

## Interpretation limits

- M1 performance over M0 shows predictive information in the recorded initial state, not a cross-fragment force.
- M2 tests one specified nonlinear coordinate interaction, not an independently observed energy-budget variable or proof of an energy-budget mechanism.
- M3 predictive improvement would still not prove direct LF→HF causation; omitted common state may remain.
- Current sidecar lacks explicit scission geometry and complete angular-momentum coupling.
- Linear ridge is a baseline model family; nonlinear model families require separate preregistration.
- TKE proxy and TXE remain derived conventional diagnostics.


## Run #43 retrospective (existing CI artifacts only)

The original `pu239-thermal-seed10` case actually used seeds 10–49 and therefore overlapped the default run's 1–200 range. It is not an independent replicate and is excluded from independent-seed conclusions. The corrected comparison uses only the verified disjoint ranges 1–200 and 201–400, 200 events in each direction.

With the refined feature definitions and 2,000 complete-event-pair bootstrap replicates:

| Train → test | M0 | M1 | M2 | M3 |
|---|---:|---:|---:|---:|
| 1–200 → 201–400 | 0.9985 | 0.7730 | 0.7819 | 0.8103 |
| 201–400 → 1–200 | 1.0207 | 0.7762 | 0.7786 | 0.7885 |

Metric: mean training-SD-normalized RMSE across four HF history targets; lower is better. M1 improves substantially over the intercept-only M0 baseline in both directions. M2 does not improve on M1 in either direction; the paired bootstrap CI for M2−M1 is `[0.00133, 0.01651]` in the first direction and `[-0.00349, 0.00789]` in the reverse direction. M3 worsens relative to M2 in both directions; corresponding CIs are `[0.00942, 0.04732]` and `[0.00179, 0.01792]`.

These are `COMPUTATION_VERIFIED` on the two Run #43 CI artifacts. They show predictive information in recorded initial state, but no held-out predictive gain from the tested nonlinear TXE×TKE proxy interaction or LF history summaries. Two seed ranges are still insufficient to estimate seed-to-seed variability. The corrected third range 401–600 has not yet been simulated in GitHub Actions.

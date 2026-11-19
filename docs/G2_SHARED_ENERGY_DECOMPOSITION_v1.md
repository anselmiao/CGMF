# G2 shared-energy versus LF spin/parity decomposition

## Status and purpose

This is a **post-hoc diagnostic** following the completed v2 fragment-state ablation. It does not replace, weaken, or rewrite the v2 primary decision rule.

The v2 LF intrinsic block contained LF parity, LF initial excitation, and LF stored spin. However, HF conditioning already includes HF initial excitation. Adding LF excitation therefore also supplies information about the pair-level total excitation budget:

\[
TXE_{pair}=U_{LF}+U_{HF}.
\]

This diagnostic separates that shared event-level coordinate from the LF non-energy fields.

## Models

- H_local: HF A/Z, parity, initial excitation, stored spin.
- H+TXE_pair_sum: the same HF block plus the derived sum of LF and HF initial excitation.
- H+TXE+L_spin_parity: pair total excitation plus LF stored spin and parity.
- H+TXE+K: pair total excitation with the existing shared/constraint-related momentum block.
- H+TXE+L_spin_parity+K: LF spin/parity increment with K controlled.

Single-field LF spin and parity models and the original v2 LF-excitation/intrinsic models are retained as diagnostics.

## Fixed computation

The same three independent Pu-239 thermal seed folds are used: train 1–400/test 401–600; train 1–200 plus 401–600/test 201–400; train 201–400 plus 401–600/test 1–200. Each fold has 400 training and 200 held-out complete event pairs. The analysis reuses the v2 reader, exact RNG-audit validation, target definitions, training-only standardization, Ridge lambda 1.0, and 2,000 paired-event bootstrap replicates with seed 20261119.

## Interpretation

- TXE_pair_sum is a derived conventional nuclear diagnostic, not an independent primitive observation and not a 气论 Q variable.
- Improvement from H to H+TXE_pair_sum would indicate predictive value in the pair-level energy budget, not a direct LF-to-HF effect.
- The critical local-field comparison is H+TXE+L_spin_parity versus H+TXE, with and without K.
- Even a stable predictive increment would be conditional association, not direct cross-fragment causation.
- This is post-hoc explanatory decomposition; conclusions must be labelled exploratory and kept separate from the v2 predeclared primary test.

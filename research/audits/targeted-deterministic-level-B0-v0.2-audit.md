# Targeted discrete-level candidate validator v0.2

**Date:** 2026-11-21  
**Branch:** `qi/fix-discrete-start-index`  
**Implementation commit:** `5426a1a043b1763172fbcaf6d35574845d04d677` (validator), `6c0dbd11f6b05bba5b500c8f9afdd8cbd27fe290` (manifest), `0fdfa90e53f8b2c0630080db4d831003e2b7ed2c` (tests)

## Purpose

The v0.1 candidate model used a single `gamma_branches[].probability` field. That representation is inadequate for evaluated nuclear decay data because it can conflate unconditional decay-mode fractions, photon intensities conditional on a transition dataset, and internal conversion. Version 0.2 keeps evaluated observations separate from executable prompt-cascade branches.

## v0.2 semantics

- `decay_channels[].fraction`: unconditional fraction of all decays from the level; `fraction_basis` must be `total_isomer_decay`. If `decay_channels_complete=true`, all listed fractions must sum to 1 within 1e-6. Incomplete channel lists may not exceed 1.
- `observed_transitions[].relative_photon_intensity`: nonnegative relative photon intensity only. It is not summed with decay-mode fractions and is not treated as an unconditional probability.
- `total_internal_conversion_coefficient`: nonnegative total ICC. If `conversion_coefficient_required=true`, absence is a hard validation error.
- `observed_transitions[].prompt_status`: source/evidence classification; it does not itself create a CGMF gamma branch.
- Transition energy closure is checked when initial and final level-energy uncertainties and gamma-energy uncertainty are all supplied. The check uses independent quadrature and a 3-sigma acceptance interval. If any uncertainty is absent, closure is not asserted.
- Observed transition destinations must exist in the same nuclide catalog and be lower in energy.
- A long-lived or unspecified level cannot label an observed transition `PROMPT`; beta/IT competition blocks that promotion.

## ¹³²I application

The manifest now includes the explicit ¹³²I 4+ ground-state endpoint. The 120(20)-keV (8−) isomer has total decay fractions β− = 0.14(2) and IT = 0.86(2), marked complete. Its 98.0(10)-keV E3 observed transition to the tentative 22(11)-keV level carries relative photon intensity 100 and total ICC 21.6; it is explicitly classified as delayed isomeric decay, not prompt fission gamma emission.

The 22(11)-keV level's adopted-table 29.11-keV entry remains an uncertain, unassigned-multipolarity observation. Its gamma-energy uncertainty is absent, so the validator correctly does not claim a numerical energy-closure pass for that entry.

All five manifest levels remain `CATALOG_ONLY`. No production `data/discreteLevels.dat` file was changed, and no new prompt branch is authorized.

## Verification

GitHub Actions `Nuclide data audit tests` run [#44803454126](https://github.com/anselmiao/CGMF/actions/runs/44803454126) on commit `0fdfa90e53f8b2c0630080db4d831003e2b7ed2c` completed successfully. The run executed 33 unit tests; all passed, followed by the eight-nuclide audit and frozen I-136 baseline verification.

A separate `CGMF G2 Build` run for the same commit was pending at the time this note was written. It is not represented as passed here. Earlier PR-triggered G2 runs were cancelled or had steps skipped, so they do not establish a successful full G2 matrix.

## Status ledger

| Item | Status | Basis |
|---|---|---|
| v0.2 decay-channel validation | `COMPUTATION_VERIFIED` | CI unit test and malformed-sum negative test |
| observed transition destination checks | `COMPUTATION_VERIFIED` | CI unit tests |
| energy closure with explicit uncertainties | `COMPUTATION_VERIFIED` | ¹³²I transition closure plus deliberately failing mismatch test |
| ICC required-field gate | `COMPUTATION_VERIFIED` | CI missing-ICC negative test |
| separation of photon intensity from total decay fraction | `COMPUTATION_VERIFIED` | CI semantic regression test |
| ENSDF ¹³²I source interpretation | `SOURCE_VERIFIED` | Separate ENSDF audit; evaluated assignment uncertainties remain explicit |
| production CGMF discrete-data integration | `BLOCKED` | No legacy fixed-width adapter; production data intentionally untouched |
| full G2 build/matrix on this head | `PENDING` | PR workflow run not yet completed |

## Next gate

Before any production adapter is considered, add a schema-level representation of conditional photon branching within a named decay mode and define how ICC converts photon intensity into total transition intensity. Then validate against at least one evaluated level scheme with a complete transition set. Do not infer missing branches or assign prompt status from a long-lived isomer's delayed decay data.

# ¹³²I ICC cross-check and G2 workflow status

**Date:** 2026-11-21  
**Branch:** `qi/fix-discrete-start-index`  
**Scope:** External cross-check of the 98-keV ¹³²I isomeric-transition ICC and status audit of the latest full G2 Actions run. No production data or executable code is changed by this note.

## 1. Independent ICC cross-check

The ¹³²I 120-keV isomeric transition is listed in the ENSDF adopted record as a 98.0(10)-keV E3 transition from the tentative (8−) isomer to the tentative 22(11)-keV (5+) level. ENSDF gives total theoretical ICC α=21.6.

Gerl et al., *Internal conversion coefficients of high multipole transitions: Experiment and theories*, Atomic Data and Nuclear Data Tables 94 (2008) 701–738, Table 1, independently lists the ¹³²I 98.0(10)-keV transition:
- experimental total ICC: 21.8(14);
- experimental method: coincidence technique (CT);
- experimental reference: 1974Di03;
- BRICC theoretical value: 21.9.

This is a useful independent cross-check: the ENSDF value 21.6 is consistent with the 2008 compilation's experimental 21.8(14) and BRICC 21.9. Preserve the three provenance-bearing values separately; do not overwrite ENSDF's adopted value with the experimental central value.

The APS abstract for 1974Di03 independently confirms the 83.6-minute ¹³²mI isomer, the 98-keV isomeric-transition gamma line, and an 86% IT branch, with the remainder beta-minus decay. NNDC ENSDF references identify 1974Di03 as measuring Eγ, Iγ, γγ/βγ coincidences, conversion-electron intensity I(ce), beta spectrum, and half-life.

## 2. Updated conditional arithmetic (reference only)

Using the experimental central value α=21.8:

- photon fraction conditional on this transition: 1/(1+21.8) = 1/22.8 ≈ 0.0438596;
- conversion-electron fraction conditional on this transition: 21.8/22.8 ≈ 0.9561404.

Using the adopted total IT fraction 0.86, and assuming solely for this arithmetic that the single listed transition exhausts the IT mode:

- parent-level gamma outcome: 0.86/22.8 ≈ 0.0377193 (3.772%);
- parent-level conversion-electron outcome: 0.86×21.8/22.8 ≈ 0.8222807 (82.228%).

The experimental ICC uncertainty ±1.4 gives an alpha-only first-order uncertainty on the conditional photon fraction of approximately 0.002695 (0.270 percentage points), using |dpγ/dα|σ_α = σ_α/(1+α)^2. This does not include uncertainty in the IT fraction, covariance, transition-intensity uncertainty, or missing branches. Do not present the parent-level percentages as fully uncertainty-qualified results.

For comparison, the ENSDF adopted α=21.6 gives pγ=1/22.6≈4.425% and pIC≈95.575%. The small difference is within the scale indicated by the experimental uncertainty.

## 3. What this cross-check does and does not establish

Established by the inspected sources:
- 98.0(10)-keV transition and E3 assignment in the adopted record;
- total ICC α=21.6 in ENSDF;
- independent experimental total ICC 21.8(14), attributed to 1974Di03, in the 2008 compilation;
- BRICC value 21.9 in that compilation;
- 86(2)% total IT branch and 14(2)% beta-minus branch in the adopted decay evaluation.

Still blocked:
- complete inventory of all IT de-excitation transitions, including weak branches and upper limits;
- uncertainty/covariance model for all transition intensities and ICCs;
- unique, firm Jπ assignments for the parent and 22-keV daughter;
- prompt ²⁵²Cf fission-fragment population evidence for this long-lived isomer.

Therefore the manifest's IT transition set must remain `complete: false`, and `derive_mode_conditional_branches` must continue to return `BLOCKED` for the ¹³²I isomer. The isomer remains `CATALOG_ONLY` for prompt CGMF use. No production `data/discreteLevels.dat` update is authorized.

## 4. Latest full G2 workflow: run #44804783105

GitHub Actions run #44804783105, job `build-and-g2-matrix` (job ID 136525875303), concluded `cancelled`.

Observed step outcomes:
- Set up job: success;
- Checkout source: success;
- Install build tools: cancelled;
- Configure, Build, native test suite, all G2 synthetic tests, targeted discrete-level tests, RNG matrix validation, full G2 sidecar matrix and representative simulation analyses: skipped.

The final step `Enforce native regression baseline after G2 diagnostics` exited 1 because its input test step had conclusion `skipped`. The log explicitly says the native regression comparison failed because the comparison result was not success; no native regression comparison actually ran. Thus this run is classified as `CANCELLED_BEFORE_BUILD`, not as a numerical/native regression failure and not as a passing G2 run.

The run's artifacts were absent because the build/test directories were never produced. No inference about the underlying native baseline can be made from this cancelled run.

## 5. Status ledger

| Item | Status |
|---|---|
| ENSDF total ICC transcription (21.6) | `SOURCE_VERIFIED` |
| Experimental ICC cross-check (21.8(14), CT, 1974Di03) | `SOURCE_VERIFIED` from 2008 compilation |
| BRICC comparison (21.9) | `SOURCE_VERIFIED` from 2008 compilation |
| ¹³²I conditional branch inventory completeness | `BLOCKED` |
| Prompt CGMF admission of ¹³²I isomer | `REJECTED_FOR_PROMPT_SCOPE` |
| Full G2 run #44804783105 | `CANCELLED_BEFORE_BUILD` |
| Full G2 build/matrix verification | `NOT_VERIFIED` |

## References

- Gerl et al. (2008), *Internal conversion coefficients of high multipole transitions: Experiment and theories*, Atomic Data and Nuclear Data Tables 94, 701–738: https://doi.org/10.1016/j.adt.2008.04.001
- 1974Di03, *Identification and Decay Characteristics of ¹³²mI*, Phys. Rev. C 10, 1172 (1974): https://doi.org/10.1103/PhysRevC.10.1172
- NNDC ENSDF ¹³²I adopted levels and gammas: https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=132I
- NNDC references for 1974Di03: https://www.nndc.bnl.gov/ensdf/getrefs.jsp?dsid=ADOPTED+LEVELS%2C+GAMMAS&recid=132053001
- GitHub Actions run #44804783105: https://github.com/anselmiao/CGMF/actions/runs/44804783105

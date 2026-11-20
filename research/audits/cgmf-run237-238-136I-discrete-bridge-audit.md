# Run 237/238: 136I discrete-bridge failure audit

**Date:** 2026-11-20  
**Branch:** `qi/fix-discrete-start-index`  
**Code under test:** `d499e21370bbec8b11898141e66665899ba3caee`  
**Report-only baseline at start:** `ffb65fd1737d46fd8164721168825acbdcf38a61`

## Executive result

Runs #237 (push, `44685572509`) and #238 (pull request, `44685578387`) both completed with failure. Configure, build, native test setup, all synthetic G2 analysis tests, RNG seed validation, and seed-range validation passed. The real G2 neutron/mixed-history sidecar matrix failed in its first Cf-252 spontaneous-fission case. The subsequent full-history/model-competition analyses were skipped. The native-regression-baseline enforcement step also failed.

The sidecar artifact from both runs independently reports:

```text
[CGMF DATA AUDIT] ZAID=53136 ndisc=1
[CGMF DATA AUDIT] ZAID=53136 level_index=0 energy_MeV=0 spin=1 parity=-1
[MC bridge diagnostic] site=lower_cut event_id=6 fragment_side=HF
  Z=53 A=136 initial_energy_MeV=0.079303252558488524
  spin_index=7 initial_spin=7 initial_parity=1 ndisc=1
  rejected_invalid=0 rejected_energy=0 rejected_angular_momentum=1
  rejected_parity=0 accepted=0
ERROR: [MC history] lower-cut transition has no mappable discrete state
```

The loaded file was the build-tree `data/discreteLevels.dat`; `CGMFDATA` was unset. Both run artifacts contain only the first Cf-252 sidecar case, with empty RNG audit output. This is not a complete event sample and must not be used for statistical model comparison.

## Key finding: the 136I ground-state record is consistent with ENSDF

The run-time database entry is the 136I ground state at 0 MeV with (J^\pi=1^-). The NNDC ENSDF adopted-level evaluation (evaluated April 2018) independently lists:

- 0 keV: ((1^-));
- 86.73 keV: ((2^-,1^-,0^-));
- 201 keV: ((6^-)), the 46.6 s isomer;
- 243.6 keV: ((7^-)).

The event's initial excitation is about 79.30 keV, below the first listed excited level at 86.73 keV. Therefore, among the adopted levels listed by ENSDF, only the ground state is energetically accessible at this event energy. The observed `ndisc=1` is not by itself evidence that the data file omitted an energetically accessible low-lying level.

ENSDF source: https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=136I (Adopted Levels, Gammas; evaluated April 2018, A=136 evaluation).

## Code-path finding

The branch's `libcgmf/src/specmc.cpp::mcSelectE1DiscreteBridge` computes the continuum spin as `spinIndex + halfint(target.lev[0].spin)` and accepts a candidate only if:

1. candidate energy is strictly below initial energy;
2. `|Ji-Jf| <= 1` and `1 <= Ji+Jf`;
3. initial and final parities are opposite.

This is an E1-only bridge predicate. For the event above, the only energy-accessible candidate is the 136I ground state (1^-), while the continuum state is (7^+). The spin difference is 6, so the candidate fails the E1 angular-momentum condition. The diagnostic confirms exactly one angular-momentum rejection and no energy or parity rejection.

The helper `libcgmf/include/gamma_transition_selection.h` already contains a pure selection-rule predicate for E1, M1, and E2, but the bridge currently hardcodes the E1 conditions rather than evaluating the allowed multipolarities relevant to the model.

This establishes the immediate software cause of this failure: **an E1-only continuum-to-discrete bridge cannot map this particular continuum state to the only energetically accessible discrete state**. It does not establish that E1 is the only physically admissible electromagnetic multipolarity, nor that an E2/M6 or other transition should be inserted without a transition-strength/probability model.

## Additional native-regression evidence

The Run #238 native test log shows the same class of no-mappable-state failures outside the first G2 case, including:

- Cf-252 SF: 136I states at 79.30 keV and 20.54 keV;
- Pu-244 SF: 105Nb, 96Y, 137I, 105Zr, 138Te, and 136I states;
- further failures in several neutron-induced and yield tests.

The diagnostic counts are frequently `ndisc=1`, but the failures are not all the same nucleus or parity configuration. The native regression baseline therefore remains broken beyond the single 136I sidecar event. Do not characterize the result as a 136I-only database issue.

## What is established, and what is not

| Item | Status | Basis |
|---|---|---|
| Runs #237/#238 compile successfully | COMPUTATION_VERIFIED | Actions job steps |
| Synthetic G2 analysis and RNG validator tests pass | COMPUTATION_VERIFIED | Actions job steps |
| Real sidecar matrix is incomplete and fails at first Cf-252 case | COMPUTATION_VERIFIED | Run artifacts |
| Runtime 136I database entry is 0 MeV, (1^-), with one accessible stored level | COMPUTATION_VERIFIED | Runtime audit output |
| ENSDF lists first excited 136I level at 86.73 keV | SOURCE_VERIFIED | NNDC ENSDF adopted levels |
| The immediate rejection is the hardcoded E1 angular-momentum rule | COMPUTATION_VERIFIED | Source inspection + diagnostic counters |
| A broader E1/M1/E2 bridge will resolve all cases | BLOCKED | Must inspect physical gamma-strength sampling and state-population support |
| The failed native regressions are explained solely by missing database levels | NOT ESTABLISHED | Multiple nuclei/configurations and selection-rule failures |

## Next work — no physics-rule change yet

1. Inspect how continuum gamma multipolarity and strength are sampled in the production cascade. Determine whether the bridge is required to honor E1 only, or whether E1/M1/E2 transitions are already part of the sampled process.
2. Trace the continuum spin/parity population at low excitation for the failing nuclei. In particular, test whether states such as (J=7^+) at 79 keV in 136I are supported by the model's level-density prescription.
3. Build a per-failure table with nucleus, excitation, (J^\pi), accessible discrete candidates, and E1/M1/E2 selection-rule outcomes. Do not change candidate acceptance or gamma strengths during this diagnostic.
4. Only after the model's transition process is specified, implement a bridge consistent with that process and add unit tests for E1/M1/E2 plus physically blocked cases.
5. Rerun native regressions and the complete sidecar matrix. Do not weaken the angular-momentum/parity rules, skip events, modify golden files, or use the partial histories for P/H/O inference.


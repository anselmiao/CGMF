# Conditional decay-mode transition probability model

**Date:** 2026-11-21  
**Branch:** `qi/fix-discrete-start-index`  
**Scope:** Deterministic derivation of transition probabilities conditional on a named decay mode. This does not alter CGMF production data.

## 1. Why a separate derivation layer is required

A total decay-mode fraction, a relative photon intensity, and an internal-conversion coefficient are not interchangeable probabilities. In particular, a relative photon intensity of 100 does not mean that 100% of all parent-level decays emit that photon.

For a transition (i) with relative photon intensity (I_{gamma,i}) and total internal-conversion coefficient (alpha_i), the total transition intensity is proportional to:

[
w_i=I_{gamma,i}(1+alpha_i).
]

Only when the transition inventory for the same decay mode is explicitly complete, the intensities share a declared normalization basis/source dataset, and every transition has a finite nonnegative total ICC, may the conditional transition probability be derived:

[
P(imid m)=rac{w_i}{sum_j w_j}.
]

The photon and conversion-electron fractions conditional on that transition are:

[
P(gammamid i)=rac{1}{1+alpha_i},qquad
P(e_{m IC}mid i)=rac{alpha_i}{1+alpha_i}.
]

Given a total parent-level decay-mode fraction (P(m)), the corresponding unconditional outcome fractions are:

[
P(m,i,gamma)=P(m)P(imid m)P(gammamid i),
]
[
P(m,i,e_{m IC})=P(m)P(imid m)P(e_{m IC}mid i).
]

These equations assume the evaluated (I_gamma) values are comparable within one decay-mode dataset and that the listed set includes all transitions needed for that mode. They do not repair missing weak branches or mixed normalization conventions.

## 2. Fail-closed conditions

The helper `derive_mode_conditional_branches` returns `BLOCKED` unless:
- the named decay mode exists with an explicit total-decay fraction;
- a transition-set record exists and explicitly declares `complete: true`;
- the intensity basis is `relative_photon_intensity_within_decay_mode`;
- all transitions in that set share the declared source dataset;
- at least one transition is present;
- every transition has a positive relative photon intensity and a finite, nonnegative total ICC.

When derivation is allowed, the report preserves separate fields for transition probability, conditional photon fraction, conditional conversion fraction, and parent-level total outcome fractions. Uncertainty propagation is not implemented and is explicitly marked false.

## 3. ¹³²I application

The 120(20)-keV ¹³²I isomer retains:
- beta-minus total decay fraction 0.14(2);
- IT total decay fraction 0.86(2);
- the observed 98.0(10)-keV E3 transition with relative photon intensity 100 and total ICC 21.6.

However, the current evidence package has not established that the listed observed-transition inventory is exhaustive for the IT mode. The manifest therefore declares the IT transition set `complete: false`. The model returns `BLOCKED` for conditional IT transition probabilities rather than treating the one visible line as the complete set.

For reference only, if independent source evidence later establishes that this is the complete IT transition inventory, the single-line conditional arithmetic would give:
- (P(gammamid i)=1/22.6approx0.04425);
- (P(e_{IC}mid i)=21.6/22.6approx0.95575);
- after multiplying by the 0.86 IT mode fraction, approximately 0.03805 parent-level gamma outcomes and 0.82195 conversion-electron outcomes.

Those last parent-level values remain conditional calculations, not an admitted CGMF prompt yield. The 1.387-hour isomer remains `CATALOG_ONLY`; no prompt gamma branch is generated.

## 4. Primary-source check and interpretation\n\nThe 1974Di03 abstract says the isomeric transition is via the 98-keV gamma line with an 86% branch and the remainder via beta-minus decay. The ENSDF adopted record separately gives IT=86(2)% and beta=14(2)%. This 86% is therefore used as the total IT decay-mode fraction, not as (P_\gamma). The 98-keV transition's photon/conversion partition is governed separately by its ICC. The paper's abstract is directly available, but its full measurement tables were not retrievable here; this is why the inventory-completeness gate remains closed.\n\nNNDC NuDat's gamma-emission guide states (α=P_{IC}/P_\gamma) and defines (I_\gamma) normalization within transitions de-exciting the same level. It gives the partial-transition half-life relation (T_\gamma=T_{1/2}/[I_\gamma(1+α)]), independently supporting the total-transition weight factor (I_\gamma(1+α)).\n\nSources: [1974Di03 APS abstract](https://journals.aps.org/prc/abstract/10.1103/PhysRevC.10.1172); [ENSDF references for 1974Di03](https://www.nndc.bnl.gov/ensdf/getrefs.jsp?dsid=ADOPTED+LEVELS%2C+GAMMAS&recid=132053001); [NNDC NuDat gamma emission and internal conversion](https://www.nndc.bnl.gov/nudat3/guide/gammaemission.html).\n\n## 5. Tests

Added regression coverage for:
- incomplete ¹³²I transition inventory producing `BLOCKED`;
- synthetic complete two-transition data deriving distinct conditional transition, photon, and conversion probabilities;
- conservation of the declared IT mode fraction across gamma and conversion outcomes.

The synthetic fixture is a mathematical/algorithmic test, not a nuclear-data claim.

## 6. CI verification\n\nGitHub Actions [Nuclide data audit tests run #44804510270](https://github.com/anselmiao/CGMF/actions/runs/44804510270), on code/test commit `072945d92c040b87cf3643385947b637bb88ab9c`, completed successfully: 35 unit tests passed, including the synthetic two-transition probability-conservation test and the ¹³²I incomplete-inventory blocking test. The eight-nuclide audit and frozen I-136 baseline verification also passed. The subsequent audit-document commit does not change executable code.\n\nThe full `CGMF G2 Build` run [#44804581048](https://github.com/anselmiao/CGMF/actions/runs/44804581048) was still in progress when checked; its build and G2 matrix are not yet verified.\n\n## 7. Status ledger

| Item | Status |
|---|---|
| Conditional branch formula implementation | `IMPLEMENTED` |
| Fail-closed completeness/source-basis gates | `IMPLEMENTED` |
| ¹³²I conditional IT probability | `BLOCKED` pending completeness evidence |
| Synthetic probability normalization | `COMPUTATION_VERIFIED` |
| Uncertainty propagation | `NOT_IMPLEMENTED` |
| Prompt CGMF integration | `BLOCKED` |
| Production `data/discreteLevels.dat` modification | `NO` |

## 8. Next gate

Find and inspect the underlying 1974Di03 IT-decay dataset and its complete transition/intensity table, including any unobserved or upper-limit branches and the normalization convention. Only then may the ¹³²I IT transition inventory be marked complete. In parallel, implement uncertainty propagation for (I_gamma) and (alpha) before using derived probabilities in quantitative A/B comparisons.

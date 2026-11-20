# Run #317 I-136 low-energy continuum-tail audit

**Branch:** `qi/fix-discrete-start-index`  
**Scope:** source/data audit only; no production-code or physics-parameter change  
**Related run:** [GitHub Actions #317](https://github.com/anselmiao/CGMF/actions/runs/44783179575)

## Executive finding

Run #317 event 6 reaches an I-136 continuum daughter at approximately 19.0635 keV with (J^\pi=6^-). The checked-in/runtime level table reported by the run has `ndisc=1`, i.e. only the ground state (0\,\mathrm{keV},1^-). The E1 bridge therefore has no allowed terminal state.

The independent ENSDF adopted evaluation for I-136 (full evaluation cutoff 2018-04-01) lists, in addition to the ground state:

- 86.73(7) keV, (J^\pi=(2^-,1^-,0^-)), with an 87.3-keV M1(+E2) transition to the ground state;
- 201(26) keV, (J^\pi=(6^-)), a 46.6-s isomer;
- 243.6 keV, (J^\pi=(7^-)), with a 42.6-keV M1+E2 transition to the 201-keV (6^-) level.

The 201-keV (6^-) level is real evaluated nuclear-structure evidence, but it is **not energetically reachable** from a 19.06-keV state. The 86.73-keV level is likewise above the event energy. Thus this finding does not create an allowed discrete endpoint for event 6.

## Source-chain observations

### 1. Discrete-level maximum controls the continuum boundary

In `libcgmf/src/setup.cpp`, `statSetupEnergyBin()` sets:

```cpp
int num_levels = (n->ndisc == 0) ? 0 : n->ndisc - 1;
double elmax = n->lev[num_levels].energy;
...
if (elmax == 0.0) n->ncont = n->ntotal-1;
else if (elmax < n->max_energy) {
  for (int k=1; k<n->ntotal; k++) {
    if (n->excitation[k] < elmax) {
      n->ncont = k-1;
      break;
    }
  }
}
```

The continuum mesh descends from the maximum excitation. If the only discrete level is the 0-keV ground state, `elmax==0` and the continuum extends down to zero excitation. Consequently, low-energy bins such as the event-6 19-keV bin remain eligible for continuum population.

If evaluated discrete levels above zero are included, `elmax` moves above zero and the mesh's continuum region is cut off below the highest included discrete level. The 19-keV continuum bin would then no longer be sampled as a continuum bin. This is a structural consequence of the code, not a claim that the 201-keV state can be reached from 19 keV.

### 2. Continuum spin density is statistical, not a catalogue of observed levels

In `libcgmf/src/levden.cpp`, `ldSpinDistribution()` assigns spin weights using a Gaussian spin distribution:

```cpp
double s = max(sc,sc0);
double r = (j+0.5)*exp(-(j+0.5)*(j+0.5)/(2.0*s*s))/(s*s);
```

In `libcgmf/src/setup.cpp`, `statSetupLevelDensity()` applies this spin distribution to every continuum energy bin and assigns parity through `ldParityDistribution()`. Thus the model can assign nonzero statistical density to high-spin continuum bins even where the adopted discrete-level scheme contains no corresponding low-energy observed state.

This is not, by itself, proof that a particular continuum state is impossible. It does show that the 19-keV (6^-) state is generated under a statistical continuum approximation and must not be relabelled as an experimentally established I-136 level.

### 3. Gamma population path

In `libcgmf/src/gampop.cpp`, `specTransitionGamma()` sums E1, M1 and E2 continuum-to-continuum transitions, and separately computes E1/M1/E2 continuum-to-discrete population. The continuum-to-continuum routine multiplies transmission by the spin/parity-resolved level density. This is the route by which a low-energy continuum population can retain a high-spin component.

The later Monte Carlo handoff in `libcgmf/src/specmc.cpp` uses a separate E1-only discrete bridge. The bridge does not consume the E1/M1/E2 transition strengths already used in the statistical population calculation.

### 4. Level-data selection/provenance remains unresolved

The RIPL reader has `riplSetNmax()` modes: `normal` uses `Nc`, `extended/reassign` use `Nmax`, and `all` uses `Nol`. This establishes that the source has multiple discrete-level selection modes. It does **not** establish which mode or exact generator command produced the checked-in `data/discreteLevels.dat` used by Run #317.

Prior RIPL comparison found I-136 has more than one level in the source listing, while the runtime table had `ndisc=1`. Exact generation lineage remains **BLOCKED** until the historical input, command, version and output are recovered or the file is regenerated under a declared mode.

## Evidence/status ledger

| Claim | Status | Basis |
|---|---|---|
| Run #317 event 6 entered I-136 at 19.0635 keV, (6^-), with `ndisc=1` | `COMPUTATION_VERIFIED` | Archived Run #317 diagnostic |
| I-136 has evaluated 86.73-keV and 201-keV levels | `SOURCE_VERIFIED` | NNDC ENSDF Adopted Levels, 2018 evaluation |
| The 86.73- and 201-keV levels are above event-6 energy | `COMPUTATION_VERIFIED` | Direct energy comparison |
| A one-level 0-keV discrete scheme leaves positive-energy bins in continuum | `SOURCE_VERIFIED` | `statSetupEnergyBin()` |
| Statistical continuum density can populate spin/parity bins not represented by observed discrete levels | `SOURCE_VERIFIED` | `ldSpinDistribution()`, `statSetupLevelDensity()`, `specTransitionGamma()` |
| The event-6 high-spin tail is caused by the missing-level cutoff | `CANDIDATE` | Strong source-chain explanation; no controlled run comparison yet |
| Historical generator mode/command for checked-in discrete-level file | `BLOCKED` | Provenance not recovered |
| A new bridge multipolarity fixes event 6 | `REJECTED` for E1/M1/E2 | All three have excessive spin change to the only energetically accessible (1^-) ground state |

## Recommended next action

Do **not** add M1/E2 or higher multipoles to the event-6 bridge, and do not suppress the event. First recover or regenerate the I-136 discrete-level input with explicit provenance and a declared RIPL selection policy. Then run a controlled A/B diagnostic:

1. baseline: current one-level runtime table;
2. data-completeness case: include only evaluated, spin/parity-assigned discrete levels under an explicitly declared policy;
3. compare the low-energy continuum mesh boundary, population by ((E,J,\pi)), event-level unmappable rate, RNG consumption, and seed/event identity.

The comparison must preserve the same seed range and report any change in state space. It is a data/model-sensitivity audit, not a physics confirmation. If a complete discrete scheme removes the 19-keV continuum tail, that supports the missing-level-cutoff explanation. If it does not, inspect the population and bin-index path further.

## External nuclear-data source

NNDC ENSDF, I-136 Adopted Levels, Gammas, evaluation cutoff 2018-04-01:  
https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=136I

The 201-keV (6^-) state is listed with XREF D (248Cm SF), not XREF C (252Cf SF). This matters for claims about direct observation/population in the specific Cf-252 dataset: the adopted existence of the level is not evidence that the particular Run #317 Cf-252 event populated it.


## 5. Archived CI event-6 population trace (Run #44808780129)

The opt-in diagnostic CGMF_G2_POPULATION_DIAGNOSTIC=1 was already enabled by tools/tests/runG2SidecarMatrix.py for the sidecar-on execution. The diagnostic was present in the uploaded artifact; it had not been inspected in the earlier review. The archived cf252-sf/on/sidecar-on.stdout now provides a direct trace for event 6.

### Exact HF trace

| Stage | Energy (MeV) | Jπ | Runtime state |
|---|---:|---:|---|
| I-137 parent | 8.52815597778 | 11.5− | continuum |
| First I-136 daughter | 2.521994448 | 9− | continuum, daughter index 20 |
| I-136 next daughter | 0.875232221939 | 8+ | continuum, daughter index 33 |
| I-136 next daughter | 0.205738886944 | 7− | continuum, daughter index 13 |
| I-136 next daughter | 0.0584223516066 | 7+ | continuum, daughter index 3 |
| I-136 selected daughter before within-bin perturbation | 0.0293032525585 | 6− | continuum, daughter index 1 |
| I-136 bridge input after within-bin perturbation | 0.019063529367160315 | 6− | bridge rejects; ndisc=1 |

The last continuum-bin population (k=1, energy 0.0293032525585 MeV) is normalized to 1 (within printed precision). Its spin/parity decomposition is:

| Jπ | Population |
|---|---:|
| 5+ | 0.00312825546833 |
| 6+ | 0.0031671744242 |
| **6−** | **0.719998224252** |
| 7+ | 0.000961649692116 |
| **7−** | **0.218613179428** |
| 8+ | 0.000236996847355 |
| **8−** | **0.0538768272265** |
| 9+ | 0.0000176926628 |

The selected 6− daughter is therefore not an unexplained isolated state: it is sampled from the dominant 6− component of the final I-136 continuum bin. Its preceding transition from 7+ to 6− satisfies the E1 selection rules (ΔJ=1, parity changes). The selected bin energy is then perturbed downward by approximately 0.0102397231913 MeV, to 0.0190635293672 MeV, crossing below the 0.020-MeV lower-cut threshold while preserving Jπ.

At the bridge, the only runtime discrete state is the 0-keV 1− ground state. The bridge rejects it solely on angular momentum: rejected_angular_momentum=1; energy and parity are not the rejection causes. The 6− to 1− spin difference is 5, outside the E1 bridge's allowed |ΔJ|≤1 range (with the usual triangle condition).

### Updated interpretation

This run establishes the immediate event-level mechanism:

1. the low-energy continuum bin contains a dominant 6− statistical population;
2. Monte Carlo selects that 6− continuum state through an E1-allowed 7+ → 6− step;
3. within-bin energy perturbation moves the selected state below the lower cut;
4. the E1-only continuum-to-discrete bridge cannot connect 6− to the sole 1− ground state.

This upgrades the existence and identity of the event-6 continuum population from a source-chain hypothesis to **COMPUTATION_VERIFIED for this archived CI run**. It does not establish why the current data policy leaves only one discrete level, nor does it prove that adding a particular evaluated level is the correct remedy. The historical level-file generation lineage remains **BLOCKED**. The event-level chain also does not justify adding an M5 bridge or changing the physical transition model: such a change would be a separate physics-model proposal requiring independent evidence and validation.

**Reproducibility scope:** this trace is from the archived CI artifact for run #44808780129, the 200-event Cf-252 SF sidecar-on case with the existing configured seed range. It is not a newly rerun experiment.


## 6. Event-6 within-bin perturbation interval reconstruction

The archived log records, for the final I-136 continuum step:

- selected bin index: k=1;
- bin-centre energy: 0.0293032525585 MeV;
- previous-bin centre: 0.0793032525585 MeV (the parent energy printed at the next population call);
- final mesh entry: 0 MeV;
- sampled energy after perturbation: 0.019063529367160315 MeV;
- lower-cut threshold: 0.020 MeV.

The source in specmc.cpp constructs the perturbation interval as:

```cpp
emax = (excitation[k-1] + excitation[k]) * 0.5;
emin = (excitation[k+1] + excitation[k]) * 0.5;
if (emin < highest_discrete_level_energy)
    emin = highest_discrete_level_energy;
ex = emin + (emax-emin)*rng_cgm();
```

For this event, ndisc=1 and the highest discrete level is the 0-MeV ground state. With k=1 and the final mesh entry at zero, the reconstructed interval is:

- emax = (0.0793032525585 + 0.0293032525585)/2 = 0.0543032525585 MeV;
- emin = (0 + 0.0293032525585)/2 = 0.01465162627925 MeV.

The observed sample therefore corresponds to the normalized within-bin coordinate:

```
u = (0.019063529367160315 - 0.01465162627925)
    / (0.0543032525585 - 0.01465162627925)
  = 0.1112666365
```

The lower-cut threshold 0.020 MeV lies inside this interval. Its normalized position is:

```
u_cut = (0.020 - 0.01465162627925)
        / (0.0543032525585 - 0.01465162627925)
      = 0.1348840949
```

Thus the sampled coordinate is below the threshold coordinate, so this draw enters the lower-cut bridge. The interval itself extends about 5.35 keV below the threshold. This is not a fixed 10.24-keV perturbation: 10.24 keV is only the observed difference between the selected bin centre and this particular sampled energy.

If rng_cgm() is uniform on [0,1), the conditional fraction of this interval below the lower cut is approximately 13.49%. This is a conditional geometric fraction for this one bin, not an empirical failure probability across events; the RNG distribution implementation and population of comparable bins must be checked before using it as a statistical rate.

### Consequence

The immediate trigger is now localized more precisely: the within-bin perturbation interval straddles the lower-cut threshold, and the archived draw lands below it. The lower-cut bridge is therefore invoked on a statistical 6− state. The bridge rejection remains a separate, deterministic selection-rule consequence given the one-level runtime scheme.

This does **not** establish that the perturbation algorithm is itself erroneous. It may be an intentional bin-sampling plus lower-cut handoff design. The unresolved design question is whether the lower-cut handoff is required to map every below-cut sample to an allowed discrete state, and what the specified behavior should be when no such state exists. Do not clamp the sampled energy to 20 keV or alter the perturbation interval without a model-level decision and controlled validation.

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

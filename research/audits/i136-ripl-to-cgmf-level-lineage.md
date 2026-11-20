# I-136 RIPL-to-CGMF discrete-level lineage audit

- Branch: `qi/fix-discrete-start-index`
- Audited data files: `data/ripl3-levels.dat`, `data/discreteLevels.dat`
- Purpose: explain why the Run #309 runtime table reported one discrete state for I-136.
- Scope: static source-file comparison only; no production data or cascade algorithm changed.

## 1. Directly observed source records

The repository's `data/ripl3-levels.dat` contains this I-136 header:

```text
136I   136   53   11   19    1    1    3.780000    8.960000
```

The first 11 listed level records include:
- level 1: 0.000000 MeV, J=1, parity=-1, with adopted notation `(1-)`;
- levels 2-6: energies 0.086730, 0.222100, 0.333970, 0.578770, 0.630530 MeV, with unknown spin/parity encoded as J=-1 and parity=0;
- level 7: 0.640000 MeV, J=6, parity=-1, with adopted notation `(6-)`;
- levels 8-11: higher levels, mostly unknown spin/parity in the numeric fields.

The repository's `data/discreteLevels.dat` contains:

```text
136I  53136   1
 0.000000   1.0 -1  8.34000e+01  0
```

Thus the checked-in RIPL source record contains 11 listed levels, while the checked-in CGMF discrete-level table contains only the ground state for I-136.

## 2. What this establishes

- The `ndisc=1` seen by Run #309 is not a runtime parser accidentally overlooking additional I-136 rows in `discreteLevels.dat`: the checked-in file itself declares exactly one level.
- The RIPL record does list additional levels, including a level at 0.640 MeV with Jπ=6-.
- Most intervening RIPL levels have unknown Jπ in the numeric columns; they cannot be admitted as definite discrete bridge states merely because they have energies.
- The RIPL and CGMF files are not equivalent level schemes for I-136.

## 3. What remains unresolved

The header fields are `Nol=11`, `Nog=19`, `Nmax=1`, `Nc=1`. The repository audit currently reports that CGMF's one level matches `min(Nmax,Nc)`, but this numerical match alone does **not** prove which generation rule selected the level or whether it is the intended CGMF truncation policy.

This static comparison does not establish:
- whether the RIPL-3 entry is the authoritative evaluated level scheme for the exact data release used by CGMF;
- whether the excited 6- level is experimentally adopted, sufficiently certain, and within the model's intended discrete-level cutoff;
- why the CGMF data-generation process retained only the ground state;
- whether adding that level would provide an allowed and energy-consistent bridge for the actual Run #309 parent state.

In particular, the Run #309 parent was Jπ=7+ at 0.079303 MeV, below the RIPL-listed 6- level at 0.640 MeV. The 6- state is therefore not energetically reachable as a downward transition from that parent. Adding it alone cannot repair this event.

## 4. Required next work

1. Locate and document the original CGMF/RIPL conversion procedure and the precise meanings of `Nol`, `Nog`, `Nmax`, and `Nc` for this file format.
2. Identify the evaluated-data version and level-assignment confidence for I-136, especially the ground state and 0.640-MeV 6- level.
3. Trace the continuum-to-discrete cutoff rule and determine whether the low-energy parent at 0.079303 MeV should have a physically justified terminal treatment when no discrete state is reachable under the implemented E1 bridge.
4. Do not add the 0.640-MeV state as a purported fix for event 6: it lies above the parent energy. Do not invent intermediate levels, remap to nearest J, or skip the event.
5. Any proposed production-data change must preserve source/version/provenance and be tested with fixed seeds against event completion, conservation, and observables.

## 5. Status

`SOURCE_FILE_COMPARISON=COMPUTATION_VERIFIED`

`RIPL_TO_CGMF_SELECTION_MECHANISM=BLOCKED`

`RUN309_EVENT6_BRIDGE_REPAIR=BLOCKED`

No production input or physical selection rule was changed by this audit.

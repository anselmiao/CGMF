# Run 277/312: RIPL completeness bound versus CGMF discrete-level count

- Date: 2026-11-20
- Branch: `qi/fix-discrete-start-index`
- Data inputs: `data/ripl3-levels.dat`, `data/discreteLevels.dat`
- Relevant failed run: CGMF G2 Build #312, run ID `44776974041`, commit `3de7c9ab3d0e1be739ab92748d7843e0acece313`
- Status: source/data comparison performed; physics bridge remains unresolved.

## 1. Main finding

The eight Run 277 failure nuclides all have `RIPL_Nmax=1` and `CGMF_ndisc=1`. The CGMF runtime count is therefore consistent with a conservative one-level completeness cutoff already present in the RIPL metadata; it is not evidence that the runtime reader silently truncated an 11- or 15-level record.

The strongest discriminating case is `96Y`:

- RIPL: `Nol=7`, `Nmax=1`, `Nc=3`
- CGMF: `ndisc=1`

The runtime count matches `Nmax`, not `Nc`. The other seven cases also have `Nmax=1`, and their `ndisc=1`.

The machine-readable comparison is in `research/audits/run277-ripl-nmax-vs-cgmf-ndisc.csv`.

## 2. What the source code says

In `libcgmf/src/ripl2levels.cpp`:

- `riplSetNmax()` documents `normal` mode as using `Nc` (highest level with unique spin/parity).
- `extended` and `reassign` modes use `Nmax` (highest level through which the level scheme is considered complete).
- The DEVUTIL RIPL conversion path sets `ml=reassign`, which selects `Nmax`.
- The production `readDiscreteLevelData()` path reads the already-prepared `DISCRETEDATA` file and stores its header count in `numberLevels[c]`; `getDiscreteLevels()` copies that count into `ncl[k].ndisc`. It does not subsequently reduce the count based on `Nol`.

This is consistent with the observed `discreteLevels.dat` counts. The exact historical provenance/build command that produced the committed data file is not recorded here, so the precise export invocation remains a provenance gap. But the evidence does not support calling this a runtime parser truncation.

## 3. Eight-nuclide comparison

| Nuclide | RIPL Nol | RIPL Nmax | RIPL Nc | CGMF ndisc |
|---|---:|---:|---:|---:|
| 89Br | 1 | 1 | 1 | 1 |
| 96Y | 7 | 1 | 3 | 1 |
| 105Zr | 1 | 1 | 1 | 1 |
| 105Nb | 6 | 1 | 1 | 1 |
| 138Te | 7 | 1 | 1 | 1 |
| 132I | 6 | 1 | 1 | 1 |
| 136I | 11 | 1 | 1 | 1 |
| 137I | 15 | 1 | 1 | 1 |

Important distinction: `Nol` is the number of levels listed; it is not the same as the level-scheme completeness bound. A listed excited level must not automatically be promoted into a complete, usable CGMF discrete scheme merely because an individual row contains a tentative or assigned Jπ.

## 4. I-136 event 6: energy and spin-parity check

RIPL-3 header at line 157530:

```text
136I  136  53  11  19  1  1  ...
```

Thus `Nol=11`, `Nog=19`, `Nmax=1`, `Nc=1`.

The first two listed levels are:

| Level | Energy (MeV) | RIPL Jπ fields | Interpretation |
|---|---:|---|---|
| 1 | 0.000000 | `(1-)` | ground state, J=1, negative parity |
| 2 | 0.086730 | `(0-,1-,2-)` | ambiguous Jπ; tabulated numeric spin/parity are unknown |
| 3 | 0.222100 | `(0-,1,2-)` | ambiguous Jπ |
| 7 | 0.640000 | `(6-)` | a listed higher state, beyond Nmax completeness bound |

The failed event 6 parent state was:

- excitation energy: `0.079303252558488524 MeV`
- spin/parity: `7+`

The first listed excited level is at `0.086730 MeV`, which is above the event's parent excitation energy. Therefore, among the tabulated levels, only the ground state is energetically accessible for this event. The ground-state transition would have `ΔJ=6` and a parity change.

The production bridge is E1-only. E1 cannot satisfy `ΔJ=6`. M1 or E2 would not solve a six-unit angular-momentum gap either. A high-multipole transition such as M6 is angular-momentum/parity allowed in principle for `7+ → 1-`, but its transition strength is not supplied by this evidence and must not be invented or assumed. The event does not establish that a physically valid transition is impossible; it establishes that the current E1-only bridge has no supported accessible state/branch for this event.

## 5. Interpretation and limits

Established:
- The RIPL header itself marks all eight records with `Nmax=1`.
- The committed CGMF table contains one discrete state for each of the eight.
- The runtime reader preserves the table's declared count.
- For I-136 event 6, the first listed excited level lies above the parent energy, and its Jπ is ambiguous.

Not established:
- That all listed RIPL levels beyond `Nmax` are physically wrong; only that the record's completeness metadata does not certify the scheme through those levels.
- That a high-multipole bridge has a non-negligible transition probability.
- That adding levels, using a different completeness policy, or enabling higher multipoles improves agreement with independent data.
- That this resolves the other native failures or permits the G2 matrix to complete.

## 6. Next controlled work

1. Record the provenance of the committed `discreteLevels.dat` export: exact RIPL snapshot, conversion mode, cutoff policy, and any manual corrections.
2. For each failed event, join its parent `(E,J,π)` to the RIPL level list and mark every candidate as: energetically accessible, Jπ known/ambiguous, within/outside Nmax, and transition multipolarities allowed.
3. Keep the current E1-only production path unchanged while building this diagnostic.
4. If a candidate extension is justified, specify its multipole strength/branching model and uncertainty before code changes; run a fixed-seed contrast and compare cascade completion, gamma/neutron observables, TKE/TXE, and conservation.
5. Do not restore nearest-J fallback, silently skip events, or replace regression goldens to obtain a green workflow.

## 7. CI status

Run #312 failed. Its log again contains multiple bridge failures with `ndisc=1`, including I-136 and other fission-fragment nuclides. This is consistent with the structural limitation above; it does not prove every event shares the I-136 event-6 cause. The N1 audit workflow passed independently in run #12 and is not a G2 physics validation.

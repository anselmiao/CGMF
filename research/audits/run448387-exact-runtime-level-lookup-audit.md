# Run #448387: exact runtime discrete-level lookup audit

- Branch at execution: `qi/diagnose-lpop-nan`
- Tested commit: `f35ee5e238ded0cee033da6ebf1231e66da701f3`
- Workflow run: [44838774835](https://github.com/anselmiao/CGMF/actions/runs/44838774835)
- Scope: read-only interpretation of the exact-lookup and lower-cut diagnostics emitted by the tested build.
- No nuclear data, transition rule, RNG behavior, or production simulation behavior was changed in this audit.

## 1. Runtime lookup result

The run emitted 315 `[CGMF G2 EXACT LEVEL LOOKUP BEGIN]` records, 228 `[CGMF G2 EXACT LEVEL LOOKUP RESULT]` records, and 11 `[CGMF G2 LOWER-CUT UNMAPPABLE]` records across the native event tests and first G2 matrix case.

For all eight recurrently audited problem nuclides, the exact ZAID lookup succeeded. The result was `database_ndisc=1` and `resulting_ndisc=1`:

| Nuclide | ZAID | exact_found | database_ndisc | resulting_ndisc | Runtime ground state |
|---|---:|---:|---:|---:|---|
| Br-89 | 35089 | 1 | 1 | 1 | 0 MeV, J=2, positive parity |
| Y-96 | 39096 | 1 | 1 | 1 | 0 MeV, J=0, negative parity |
| Zr-105 | 40105 | 1 | 1 | 1 | 0 MeV, J=4, positive parity |
| Nb-105 | 41105 | 1 | 1 | 1 | 0 MeV, J=5/2, positive parity |
| Te-138 | 52138 | 1 | 1 | 1 | 0 MeV, J=0, positive parity |
| I-132 | 53132 | 1 | 1 | 1 | 0 MeV, J=4, positive parity |
| I-136 | 53136 | 1 | 1 | 1 | 0 MeV, J=1, negative parity |
| I-137 | 53137 | 1 | 1 | 1 | 0 MeV, J=7/2, positive parity |

This directly rules out a missing-exact-ZAID lookup and the `riplGSonly()` fallback as the explanation for these eight observed one-level cases in this run. The runtime copied a one-level record from the loaded CGMF discrete-level database.

It does **not** establish why the prepared data file contains one level. That is an upstream data-preparation/provenance question, not a runtime lookup failure.

## 2. Relationship to the checked-in data

The earlier source/data audits already established that the checked-in runtime file `data/discreteLevels.dat` declares one level for these eight nuclides, and that their RIPL headers have `Nmax=1`. For I-136 specifically, the RIPL source lists 11 rows, but `Nmax=1); the CGMF runtime file contains one ground-state row. The RIPL-listed 0.640-MeV (6-) level is above the event-6 continuum state at 0.019063529367 MeV and is not an energetically available endpoint for that event.

The current run is consistent with those earlier file-level audits. It does not independently reproduce the historical converter invocation or prove the exact generator/version that produced the prepared file. Keep the converter lineage status BLOCKED until that source is recovered or independently reconstructed with provenance.

## 3. Lower-cut failures

The run emitted 11 lower-cut unmappable events. In every emitted failure record, the runtime candidate list contained only one discrete state (the ground state). The candidate diagnostics rejected that state through angular-momentum and/or parity selection. This is a state-space/bridge reachability failure, not a failed ZAID lookup.

For I-136 event 6 (HF), the runtime selected state was:
- continuum state: E=0.019063529367160315 MeV, J=6, negative parity;
- sole discrete candidate: E=0 MeV, J=1, negative parity;
- energy condition: allowed;
- angular-momentum condition: rejected;
- parity condition: rejected.

No additional M1/E2 bridge rule or nearest-J fallback is justified by this diagnostic. The candidate remains physically unmappable under the current E1-only bridge contract.

## 4. The MAX_NUCLEI loop-bound issue is separate

The production `getDiscreteLevels()` currently searches with:

```cpp
id = -1;
while (!found && id < MAX_NUCLEI) {
    id++;
    if (zaidIndex[id] == zaid) found = true;
}
```

The arrays are allocated with exactly `MAX_NUCLEI` elements, valid indices `0..MAX_NUCLEI-1`. If a ZAID is absent, the loop can increment `id` to `MAX_NUCLEI` and read one element past the allocation. The loaded-entry count `NUM_NUCLEI` is set after parsing and is the appropriate search bound.

This is a genuine defensive bounds defect in the missing-ZAID path, but it did **not** cause the eight audited failures in this run: all eight exact lookups succeeded. It should be fixed and regression-tested as a separate runtime safety correction, not presented as the cause of the lower-cut failures.

A further parser-capacity check is also absent before writing `zaidIndex[c]`, `numberLevels[c]`, and `allLevels[c]`; the data loader should guard `c < MAX_NUCLEI` before storing a new nuclide. This is a separate input-capacity hardening item; this run does not show that the current data exceeds the allocation.

## 5. CI outcome

- Build: passed.
- Targeted deterministic candidate/reachability tests and synthetic G2 analysis tests: passed.
- Native CTest: 78/100 passed; 11 execution tests failed and their 11 dependent diff tests were not run. The native-test step itself is marked success by workflow continuation behavior, but final enforcement failed.
- Complete G2 sidecar matrix: failed in its first Cf-252 SF case (200 events, seed 98252) because the CGMF executable returned exit code 255 after a lower-cut unmappable transition.
- Downstream full-history/model-competition steps: skipped.
- PR #5 remains Draft/Open; this run does not qualify the branch for merge.

## 6. Evidence ledger and next work

| Claim | Status | Basis |
|---|---|---|
| The eight target ZAIDs are found by the production exact lookup in Run #448387 | COMPUTATION_VERIFIED | CI runtime diagnostics |
| Each of those eight loaded records has exactly one discrete level | COMPUTATION_VERIFIED | `database_ndisc=1` and `resulting_ndisc=1` in CI |
| The observed lower-cut failures arise from the sole candidate failing current bridge selection conditions | COMPUTATION_VERIFIED | 11 candidate/failure diagnostic pairs |
| Missing ZAID fallback caused the eight audited failures | REJECTED for this run | All eight exact lookups succeeded |
| The one-level prepared data was generated by a specific historical converter invocation | BLOCKED | Generator/version/invocation provenance remains unavailable |
| The `getDiscreteLevels()` missing-ZAID search can read past its array bound | SOURCE_AUDITED | Loop bound vs allocation size |
| The bounds defect caused the current eight lower-cut failures | REJECTED for this run | All eight ZAIDs found |
| Complete G2 histories and P/H/O competition are validated | BLOCKED | Matrix failed before completion |

Recommended order:
1. Fix and test the missing-ZAID lookup bound using `NUM_NUCLEI`, and guard database insertion capacity before writing arrays.
2. Keep this correction separate from the physical lower-cut problem; prove missing-ZAID behavior with a deterministic test that does not depend on stochastic fission events.
3. Continue the source/provenance audit of the prepared level file and its RIPL-to-CGMF conversion.
4. Only then evaluate a policy-explicit alternative level scheme and the terminal treatment of continuum states for which no physically allowed discrete endpoint exists.
5. Do not resume P/H/O analysis until the complete G2 sidecar matrix and native regression baseline pass.

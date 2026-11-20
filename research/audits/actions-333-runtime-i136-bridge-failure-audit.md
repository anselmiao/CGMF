# Actions #333: Run-time discrete-level provenance and I-136 bridge failure audit

- **Workflow:** [CGMF G2 Build, run #333](https://github.com/anselmiao/CGMF/actions/runs/44792258863)
- **Run ID:** `44792258863`
- **Commit:** `cb27ad1baad4198f65da027032e30b0ab079bda4`
- **Branch:** `qi/fix-discrete-start-index`
- **Date:** 2026-11-20 UTC
- **Scope:** Runtime data-file identity and the first failing Cf-252 spontaneous-fission matrix case. This is an audit, not a physics-data change.

## 1. CI outcome

The job built successfully. The native CGMF test suite, G2 synthetic-fixture unit tests, seed-matrix unit tests, and 31-case seed-range validator all passed.

The first production simulation in the matrix failed:
- Case: `cf252-sf`
- ZAID: `98252`
- Incident energy: `0.0 MeV`
- Requested events: `200`
- Default seed range: `1..200`
- Executable: `build/utils/cgmf/cgmf.x`
- Exit status: `255`
- Failure point: event 6, HF, lower-cut MC bridge.

The later conditional-history, model-competition, ablation, and shared-energy analyses were skipped. Therefore this run is **not** a successful G2 matrix validation.

## 2. Runtime discrete-level file: path confirmed

The C++ runtime diagnostic in `cf252-sf/on/sidecar-on.stdout` reports:

```text
[CGMF DATA AUDIT] opened_file=/home/runner/work/CGMF/CGMF/libcgmf/../data/discreteLevels.dat
[CGMF DATA AUDIT] datadir=/home/runner/work/CGMF/CGMF/libcgmf/../data/
[CGMF DATA AUDIT] CGMFDATA=<unset>
```

The matrix runner's independent pre-launch path-resolution audit reports:

```text
[CGMF DATA AUDIT PYTHON] selected_by=BUILD_DATADIR
[CGMF DATA AUDIT PYTHON] selected_file=/home/runner/work/CGMF/CGMF/data/discreteLevels.dat
[CGMF DATA AUDIT PYTHON] sha256=c79679e4247ddf69e3766ccce0b3177fcb7b253e26fd50ff621d2721d023c80e
```

The two paths resolve to the same file. Thus, for this run, the actual C++ opened path is confirmed and the corresponding file's SHA-256 was captured independently before the simulation. `CGMFDATA` was unset; no current-working-directory shadow file was selected.

Important distinction: this SHA-256 is a byte-level file digest. It is not the Git blob SHA. The previously frozen repository artifact identity for `data/discreteLevels.dat` is a Git blob SHA and must remain labeled as such.

## 3. I-136 runtime level list

The C++ runtime audit reports the complete loaded list for ZAID 53136:

```text
[CGMF DATA AUDIT] ZAID=53136 ndisc=1
[CGMF DATA AUDIT] ZAID=53136 level_index=0 energy_MeV=0 spin=1 parity=-1
```

So the run loaded exactly one discrete level for I-136:
- index 0
- energy 0 MeV
- spin 1 (i.e. J=1 in the code's representation)
- parity -1

No additional I-136 discrete level was loaded in this run. This confirms the runtime input state; it does not establish why the prepared data file has this selection or whether another level-selection policy would be physically justified.

## 4. Event-6 failure is reproduced with bridge diagnostics

The captured event-6 log gives:

```text
[MC bridge diagnostic] site=lower_cut event_id=6 fragment_side=HF nucleus_index=1 Z=53 A=136 initial_energy_MeV=0.019063529367160315 spin_index=6 initial_spin=6 initial_parity=-1 ndisc=1 rejected_invalid=0 rejected_energy=0 rejected_angular_momentum=1 rejected_parity=0 accepted=0
ERROR     :[MC history] lower-cut transition has no mappable discrete state
```

Observed facts:
- The failing nucleus is I-136 (Z=53, A=136).
- The bridge initial state is approximately 19.0635 keV, J=6, negative parity.
- The runtime discrete scheme has only the 0-keV J=1 negative-parity state.
- Exactly one candidate was rejected for angular-momentum reasons; none were rejected for invalid state, energy, or parity.
- No candidate was accepted, so the lower-cut transition could not be mapped.

This is consistent with the previously identified angular-momentum mismatch for a direct 6-to-1 transition under the bridge's implemented transition rules. It does **not** justify adding an arbitrary high-multipole transition, nor does it justify inserting an unverified discrete level.

## 5. Partial artifacts and event-integrity limits

The matrix artifact contains only the first case's sidecar-on outputs because the process stopped during event 6.

Independent inspection of the artifact found:
- `neutron-transition.jsonl`: 21 records, covering event IDs 1–5 only; each of these five events contains both LF and HF records.
- `mixed-history.jsonl`: 10 records, covering event IDs 1–5 only; each of these five events contains one LF and one HF record.
- `rng-audit.tsv`: zero bytes. A complete RNG audit was not produced before the abrupt simulation exit.

No event-6 LF/HF pair is present in these JSONL artifacts. These partial files must not be treated as a complete 200-event sample or used for inferential analysis.

Artifact:
- [G2 matrix artifact for run #333](https://github.com/anselmiao/CGMF/actions/runs/44792258863/artifacts/14657976232)
- Artifact ZIP SHA-256: `8d004a13e0db62c1271159641769241fba9bfe1e4246c688be7b4a2cefae7afd`

## 6. Status ledger

| Claim | Status | Basis / remaining work |
|---|---|---|
| Build and native CGMF tests pass at this commit | `COMPUTATION_VERIFIED` | Actions #333 job steps |
| G2 synthetic unit tests and seed-range validator pass | `COMPUTATION_VERIFIED` | Actions #333 job steps |
| C++ opened the repository build data path shown above | `COMPUTATION_VERIFIED` | Runtime `opened_file` diagnostic |
| I-136 runtime discrete list contains only the 0-keV J=1− state | `COMPUTATION_VERIFIED` | Runtime `ndisc=1` and level-index diagnostic |
| SHA-256 of the opened data file | `COMPUTATION_VERIFIED` | Python pre-launch digest for the same resolved path |
| Event-6 bridge failure mechanism: no angular-momentum-allowed candidate among loaded discrete levels | `COMPUTATION_VERIFIED` | Bridge diagnostic counters |
| Why the prepared I-136 data file contains only one discrete level | `BLOCKED` | Provenance/generation policy still not established |
| A defensible alternative I-136 discrete-level policy | `BLOCKED` | Requires explicit source-backed inclusion criteria |
| Complete 200-event Cf-252 sample and RNG audit | `BLOCKED` | Run terminates at event 6; RNG audit file is empty |
| Full 31-case G2 sidecar matrix | `BLOCKED` | First case fails; remaining cases not run |

## 7. Next controlled work

1. Preserve the current failure as a regression signal; do not suppress it or relabel the run as passed.
2. Use the confirmed runtime path and digest as the frozen baseline-A runtime record.
3. Keep baseline B unbuilt until a source-backed adopted-level inclusion policy is specified. Unknown or ambiguous spin/parity assignments must remain explicitly unknown; do not blindly copy every RIPL row.
4. Add a diagnostic mode to the matrix runner that records a case-level failure and continues to later cases, while retaining a nonzero final exit if any case is incomplete or fails. It must preserve partial logs and must never count partial events as valid complete events.
5. Run a narrowly scoped A/B comparison only after B's construction policy is frozen, with identical executable, inputs, event count, and seed range. Compare complete event pairs and exact RNG audits; do not mix the A and B samples.

No production nuclear data or physics behavior was modified by this audit.

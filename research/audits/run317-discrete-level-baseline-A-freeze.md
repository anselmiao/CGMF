# Run #317 follow-up: discrete-level baseline A freeze specification

**Branch:** `qi/fix-discrete-start-index`  
**Scope:** Freeze and identify the exact runtime discrete-level input before constructing any alternative B dataset.  
**Production changes:** none in this audit.

## 1. Immutable repository identity for baseline A

The current branch's prepared data artifacts have the following Git blob identities:

| Artifact | Repository path | Git blob SHA | Identity comparison |
|---|---|---|---|
| Prepared CGMF levels (A candidate) | `data/discreteLevels.dat` | `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c` | identical to CGMF 1.1.0 release commit `e333c9ca3bd869032a170393a50942b31d992aeb` |
| RIPL source | `data/ripl3-levels.dat` | `c3c3a816730deef172ccbd11b0dfd58b6d197d90` | identical to CGMF 1.1.0 release |
| RIPL 2015 source | `data/ripl3-levels-2015.dat` | `3be0a27558c793837f6c3cc5deb45ea1deee7259` | identical to CGMF 1.1.0 release |

These are Git blob SHAs, **not** SHA-256 file digests. They identify repository objects exactly and must not be mislabeled as SHA-256.

The current branch inherits the prepared file from the 2021 CGMF 1.1.0 data revision. This is a reproducible repository identity for A, but not proof of the historical generator command.

## 2. Runtime file resolution must be recorded

In `readDiscreteLevelData()`, CGMF tries the process current working directory first:

1. `DISCRETEDATA` (normally `discreteLevels.dat`) relative to the current working directory;
2. if that open fails, `datadir + DISCRETEDATA`.

Therefore the repository's `data/discreteLevels.dat` blob alone does not prove which physical file a particular Actions job opened. A run can shadow the packaged file with a same-named working-directory file.

The source now supports the opt-in `CGMF_DATA_AUDIT` diagnostic, which reports:
- `opened_file`
- `datadir`
- `CGMFDATA`
- selected audit ZAIDs and their runtime `ndisc` and level tuples ((E,J,\pi)).

Run #317's archived diagnostic reported I-136 (ZAID 53136) `ndisc=1`; it did not, by that single value alone, establish the physical path or full table contents. The A baseline is therefore **repository-identity frozen, runtime-path confirmation pending**.

## 3. Required baseline-A capture

Run one diagnostic-only invocation with `CGMF_DATA_AUDIT=1`, using the exact same binary, input deck, working directory, `CGMFDATA`, seed and event range as the baseline case. Preserve the full stdout/stderr and record:

- resolved `opened_file` (canonical absolute path);
- file byte size and SHA-256 of the opened file;
- Git blob SHA if it is the repository artifact;
- ZAID 53136 full runtime level list: level index, energy, spin, parity;
- `ndisc`, maximum loaded discrete energy, and `ncont` / continuum boundary;
- executable commit, compiler/build configuration, input-deck hash, seed and event count.

Do not infer the SHA-256 from the Git blob SHA. Compute it over the exact opened bytes in the runner and archive it beside the log.

## 4. B dataset is not authorized yet

Do not construct B by blindly selecting RIPL `Nol`, and do not overwrite A. The 201-keV evaluated I-136 (6^-) state is above the event-6 energy of about 19.06 keV and cannot be a terminal state for that event.

After A is fully captured, a separate B candidate may be generated only with:
- a pinned RIPL/ENSDF input revision and checksums;
- explicit adopted-level inclusion criteria;
- uncertainty and unknown-(J^\pi) handling kept separate;
- transition data/provenance preserved rather than inferred from level existence;
- a deterministic generator command, script revision and output hash.

The first B comparison is a sensitivity diagnostic. It is not a replacement for A and does not establish a physical correction merely because the event no longer fails.

## 5. Decision gates

| Gate | Required evidence | Status |
|---|---|---|
| A repository artifact identity | Git blob SHA pinned to 1.1.0 | **COMPUTATION_VERIFIED** |
| A runtime path identity | `CGMF_DATA_AUDIT` canonical path in exact run | **BLOCKED** |
| A byte-level SHA-256 | SHA-256 of the exact opened file | **BLOCKED** |
| A full I-136 runtime level list | audit output for all levels | **BLOCKED** |
| A generation lineage | exact generator/version/command | **BLOCKED** |
| B scientifically declared level policy | explicit evaluated-data criteria | **NOT STARTED** |
| A/B same-seed comparison | only after A and B are independently frozen | **NOT STARTED** |

## 6. Current interpretation

The one-level I-136 runtime scheme is consistent with the observed Run #317 `ndisc=1` and the old prepared-data artifact. The source code's continuum mesh can extend to zero excitation when the highest loaded discrete level is the 0-keV ground state. This remains a plausible explanation for why a 19-keV high-spin statistical continuum state is generated.

It is **not yet a demonstrated root cause**. First prove which exact file the failing job opened and capture the full runtime table. Only then proceed to a separate data-policy sensitivity experiment.

No production physics, bridge selection rule, level table, RNG sequence, seed range, or golden result is changed by this audit.

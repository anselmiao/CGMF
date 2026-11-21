# G2 Engineering Contract Amendment — 2026-11-19

Status: USER-AUTHORIZED ENGINEERING AMENDMENT
Applies to: `anselmiao/CGMF`, G2 neutron-transition-history work
Base: historical engineering baseline `0118b54c4848a8754f94a1a9666ea66335832651`

## 1. Authorization

The user explicitly authorized revision of the former G2 engineering freeze to permit:
- CGMF source-code changes required to improve G2 event/transition observability;
- regression tests and validators for the new output;
- CI workflow changes needed to build and validate those changes;
- a dedicated development branch and reviewable pull request.

This amendment supersedes only the blanket prohibition on source, test, and CI modifications for the scoped engineering work below. It does not retroactively authorize changes to historical results.

## 2. Immutable historical evidence

The following remain immutable reference records:
- Run #29: workflow run `44237543747`, source commit `41448e9645226983700c9dcb661f2fe012adcdbe`, artifact `14397847806`;
- Run #30: workflow run `44238818958`, source commit `0118b54c4848a8754f94a1a9666ea66335832651`, artifact `14399181633`.

Do not overwrite, delete, relabel, or silently regenerate these runs or artifacts. Their byte-identical outputs are deterministic reproduction, not independent stochastic replication.

## 3. Permitted engineering scope

Permitted on a non-default development branch:
1. Correct mixed-history indexing and timestamp validity bookkeeping.
2. Add an opt-in JSONL sidecar that records the ordered neutron, gamma, and internal-conversion transitions for each fission fragment, including fragments with zero neutron emissions.
3. Preserve the existing neutron sidecar schema and default-off behavior.
4. Add schema validation and cross-checks against the existing neutron sidecar.
5. Extend the CI regression matrix to test sidecar-on/off non-interference, RNG audit equality, output coverage, and consistency between the mixed and legacy neutron sidecars.
6. Add documentation describing schema fields, units, timestamp semantics, and limitations.

## 4. Not authorized by this amendment

This amendment does not authorize:
- modification or replacement of Run #29/#30 or their artifacts;
- changing the historical 6,865-record / 2,151-event / 31-scenario / 2,857-transition baseline;
- production-scale scientific parameter sweeps or new scientific claims;
- creating TASK-08 or a new high-order physical model;
- treating simulated histories as measured experimental data;
- direct identification of CGMF transitions with 气论 entities or mechanisms;
- adding tunable physical parameters to the theory.

CI may run only bounded, deterministic regression cases necessary to validate the engineering changes. Any larger scientific simulation campaign requires a separate explicit plan and authorization.

## 5. Required acceptance criteria

- Existing neutron sidecar schema and validator remain backward compatible.
- Mixed sidecar is opt-in and emits one fragment summary per LF/HF fragment, including zero-neutron fragments.
- Transition order is the original mixed history order, not a reconstructed ordering from grouped particle arrays.
- Neutron kinematics and recoil values agree with the legacy sidecar within exact serialized precision/tolerance specified by the validator.
- Timestamp is marked valid only when the source code actually sampled/assigned it; invalid timestamps are not represented as numeric zero measurements.
- Enabling either sidecar does not change RNG call count/digest, legacy histories, or ordinary stdout.
- CI tests include zero-neutron, neutron-only, gamma-containing, and mixed-particle event coverage where supported by the bounded test matrix.
- Run #29/#30 artifacts remain untouched.

## 6. Evidence and reporting discipline

Report separately:
- source-level findings;
- compile/test/CI results actually observed;
- simulated outputs from newly authorized bounded regression cases;
- historical Run #29/#30 results;
- external experimental measurements.

A passing CI matrix establishes software behavior for its tested cases only. It does not establish a physical mechanism or independent experimental validation.

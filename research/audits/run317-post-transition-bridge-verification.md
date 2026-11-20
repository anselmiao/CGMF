# Run 317: post-transition lower-cut state verification

- Branch: `qi/fix-discrete-start-index`
- Workflow run: CGMF G2 Build #317
- Run ID: `44783179575`
- Workflow head: `682c9ff4b94385f635dd41664d65ceda2ccb9aa0`
- Code correction under test: `4265ed5094270fceb522b1b0a2f8dc4ffb010619`
- Result: **FAILURE**
- Matrix artifact ID: `14653370742`
- Matrix artifact SHA-256: `03433a32487adaabd6b02fd95f87f7a22fd81515b4229efa59bf77aacaf760eb`

## 1. Run result

Configure, Build, native CGMF tests, synthetic G2/conditional-history/competition/ablation tests, RNG matrix tests, and the 31-case non-overlapping seed-range validator all passed.

The real G2 sidecar matrix failed in its first case:
- case: `cf252-sf`
- incident energy: 0.0 MeV
- requested events: 200
- seed range: 1..200
- failure: event 6, HF I-136
- sidecar output stopped at the bridge failure; only partial event records were written.
- `rng-audit.tsv` is empty.
- Conditional-history and model-competition stages were skipped.

The run therefore does not yield a valid complete sample for P/H/O competition.

## 2. The state-reference correction is confirmed by the new diagnostic

The archived `sidecar-on.stdout` now reports:

```
[MC bridge diagnostic] site=lower_cut event_id=6 fragment_side=HF
nucleus_index=1 Z=53 A=136
initial_energy_MeV=0.019063529367160315
spin_index=6 initial_spin=6 initial_parity=-1
ndisc=1 rejected_invalid=0 rejected_energy=0
rejected_angular_momentum=1 rejected_parity=0 accepted=0
```

This is the decisive confirmation that the lower-cut selector is now evaluating the selected, post-perturbation continuum daughter state, rather than the prior (7^+) parent state at 0.0793032525585 MeV.

The population-selection trace before the energy perturbation reports the daughter as:
- energy: 0.0293032525585 MeV
- (J^π=6^-)
- continuum state (`daughter_discrete=0`)

The bridge diagnostic records the energy after the within-bin perturbation:
- (E=0.019063529367160315) MeV
- (J^π=6^-)

Thus the previously identified `mcurr` versus `mnext` state-reference mismatch is corrected in the executed run.

## 3. Why the event still fails

The checked-in I-136 discrete-level scheme has `ndisc=1`, with only the (1^-) ground state available.

For the actual post-perturbation state (6^-ightarrow1^-):
- energy reachability is not the rejection: `rejected_energy=0`;
- angular-momentum selection is the rejection: `rejected_angular_momentum=1`;
- parity is not separately counted as a rejection: `rejected_parity=0`;
- no candidate is accepted.

E1 requires (|J_i-J_f|leq1) (excluding (0	o0)) and parity change. Here (|6-1|=5), so E1 is forbidden. The unchanged negative parity is also not an E1 transition. The observed failure is therefore not explained away by the old-state call-site bug: after correcting that bug, the actual daughter state still has no E1-allowed bridge to the only checked-in discrete state.

No evidence in this run supports adding an M6 transition strength, changing the selection rules, substituting a nearest-J state, or skipping the event.

## 4. Evidence status

| Claim | Status |
|---|---|
| Build and native test stages passed | COMPUTATION_VERIFIED |
| Synthetic analysis and RNG validation passed | COMPUTATION_VERIFIED |
| Real sidecar matrix failed at first case/event 6 | COMPUTATION_VERIFIED |
| Lower-cut diagnostic uses post-perturbation (mnext) state | COMPUTATION_VERIFIED |
| Actual post-perturbation I-136 state is (0.019063529367160315) MeV, (6^-) | COMPUTATION_VERIFIED |
| Only one I-136 discrete state is available in this run | COMPUTATION_VERIFIED |
| No E1 candidate is available from (6^-) to (1^-) | COMPUTATION_VERIFIED under current level scheme and selector |
| A physically supported alternative bridge exists | BLOCKED |
| Complete 200-event case / 31-case matrix | NOT COMPLETED |
| P/H/O competition analysis | NOT RUN |

## 5. Next controlled investigation

The next task is no longer to revisit the old-state reference. That correction is verified.

Instead:
1. Trace how the I-136 low-energy continuum population is constructed and why the selected (6^-) state occurs at 19.06 keV after perturbation.
2. Verify whether the continuum-to-discrete handoff is intended to be E1-only in the model's physics specification, or whether the production code is omitting documented transition channels/strengths.
3. Obtain evaluated I-136 level and transition data with uncertainties/assignments. A level's existence alone is insufficient: a bridge requires energy ordering, (J^π), multipolarity, and strength/branching evidence.
4. If the model has no physically specified transition path, record this as a model-domain limitation rather than inventing a path.
5. Keep the current seed matrix and golden files unchanged. Any alternative must be a separately named, opt-in contrast with fixed-seed provenance and full observable/energy/angular-momentum audits.

No gas-theory mechanism or empirical G2 claim is upgraded by this run.

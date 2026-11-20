# Run 309 G2 sidecar lower-cut bridge failure audit

- Date: 2026-11-20
- Branch: `qi/fix-discrete-start-index`
- Commit tested: `c04b10b37d574e98b2100971ee2b4f8712998078`
- Workflow: CGMF G2 Build #309
- Run ID: `44772225632`
- Result: `failure`
- Artifact: `cgmf-g2-mixed-history-matrix` (artifact ID `14647258465`)
- Artifact SHA-256: `0cc81d970e44f74834f850585adc7d21307ae5d608bccc830e96e2fa726d0de8`

## 1. Execution boundary

Configure and Build succeeded. The native CGMF test step succeeded. The synthetic G2 three-layer, conditional-history, matched-history, event-state competition, fragment-state ablation, RNG seed matrix tests, and 31-case non-overlap seed validator all succeeded.

The first real sidecar matrix case, `cf252-sf/on` (200 events, seeds 1..200), stopped at event 6. The later representative conditional-history and competition analyses were skipped because the sidecar matrix failed. This run therefore supplies no complete event sample for P/H/O competition.

## 2. Direct failure evidence

The runtime data audit printed:

- `ZAID=53136 ndisc=1`
- level index 0: energy 0 MeV, spin `J=1`, parity `-1`
- selected data file: `data/discreteLevels.dat`
- SHA-256: `c79679e4247ddf69e3766ccce0b3177fcb7b253e26fd50ff621d2721d023c80e`

For HF event 6, the low-energy cascade reached:

- nucleus: `Z=53, A=136` (iodine-136)
- lower-cut parent state: `E=0.079303252558488524 MeV`
- `J=7`, parity `+1`
- available discrete states: `ndisc=1` (only the recorded ground state `J=1^-`)

The bridge diagnostic was:

```text
site=lower_cut event_id=6 fragment_side=HF nucleus_index=1
Z=53 A=136 initial_energy_MeV=0.079303252558488524
initial_spin=7 initial_parity=1 ndisc=1
rejected_invalid=0 rejected_energy=0
rejected_angular_momentum=1 rejected_parity=0 accepted=0
```

The run then reported:

```text
ERROR :[MC history] lower-cut transition has no mappable discrete state
```

## 3. Root-cause classification

This is a real bridge-reachability failure, not a compile failure, synthetic-analysis test failure, or RNG seed-overlap failure.

Given the only available discrete state `J=1^-` and the lower-cut parent `J=7^+`, the spin difference is 6. The current E1 bridge rejects it on angular-momentum selection. The diagnostic reports exactly one angular-momentum rejection and no parity rejection. Since the data table has only one discrete level for this nuclide, there is no alternative recorded level to bridge to.

This observation does **not** establish that the evaluated nuclear ground-state assignment is wrong, that adding a level is justified, or that M1/E2 selection would solve this particular transition. A multipole extension cannot bridge a `Delta J=6` gap under E1/M1/E2 rules. Nearest-J fallback, arbitrary state remapping, or silent event skipping would conceal rather than solve the physical/data-model mismatch.

## 4. What this run does and does not establish

Established for this run:
- Build and native unit/regression step completed successfully.
- The G2 matrix stopped at its first case, event 6.
- The failure is at the lower-cut discrete bridge for iodine-136 with `ndisc=1`.
- The sidecar artifact contains only partial event records through the failed event; `rng-audit.tsv` is empty.

Not established:
- Full 200-event completion or the remaining 30 matrix cases.
- Any P/H/O model comparison or independent evidence for cross-fragment history dependence.
- Whether a more complete, provenance-qualified discrete-level source would provide a physically valid cascade path.
- Whether the same failure is resolved by any proposed continuum-floor or ground-state override.

## 5. Required next diagnostic

Before changing production selection rules or nuclear data:
1. Trace the provenance and preprocessing of the iodine-136 discrete-level record, including the source level count and why the runtime table has `ndisc=1`.
2. Compare the full evaluated level scheme and transition information with the actual CGMF discrete-level representation; preserve source/version and uncertainty flags.
3. Determine whether the continuum-to-discrete handoff model has a physically justified treatment for a high-spin parent when the available discrete scheme has no allowed bridge.
4. Only after a documented candidate is defined, run a fixed-seed before/after contrast and compare event admission, cascade completion, gamma/neutron observables, TKE/TXE, and conservation. Do not replace golden outputs or loosen the selector to make CI green.

## 6. Separate N1 validator maintenance

After Run #309, the N1 spin-admission parser was updated to parse exact rational values such as `1/2` and `3/2` using `fractions.Fraction`, avoiding floating-point approximation and accepting common nuclear-data notation. The update and tests were committed as:
- parser: `e49fc2fe6edf4b1e249830cb5cb39b1af13cc9d5`
- tests: `8528e3bb819aa86771dc1178fea5d90df16488e2`

The Nuclide data audit workflow for the latter commit completed successfully (run `44776743056`), including compile, unit tests, and the eight-nuclide coverage audit. This is N1 tooling verification only; it does not resolve the G2 bridge failure.

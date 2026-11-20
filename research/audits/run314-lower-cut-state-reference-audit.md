# Run 314: lower-cut bridge state mismatch and I-136 event trace

- Branch: `qi/fix-discrete-start-index`
- Source revision analyzed: `36101089dc48d8bd7346fb7ad7d24d657cc1e495`
- Workflow: CGMF G2 Build #314
- Run ID: `44781809313`
- Result: `failure`
- Matrix artifact: `cgmf-g2-mixed-history-matrix`, artifact ID `14652198165`
- Artifact SHA-256: `c4e3f626412253a5f60a8a85a6eb90479f913c4528ad2dec65197c8467465b77`
- Scope: source/log audit only; no production selector, nuclear data, continuum model, RNG, or golden output changed.

## 1. Run boundary

Configure and Build succeeded. The native CGMF test step and all synthetic G2/competition/ablation/RNG validation steps succeeded. The first real sidecar case, `cf252-sf` (200 events), failed in event 6. The conditional-history and model-competition stages were skipped. The run does not provide a complete event sample for P/H/O analysis.

## 2. Event 6 state trace

The archived `sidecar-on.stdout` contains the following final sequence for HF iodine-136 (Z=53, A=136):

1. Before the final low-energy handoff, the cascade's current state was reported as:
   - (E_{curr}=0.0793032525585) MeV
   - (J_{curr}=7)
   - parity (+)

2. `mcFindNext()` selected a continuum daughter state:
   - (E_{next}=0.0293032525585) MeV before the subsequent within-bin energy perturbation
   - (J_{next}=6)
   - parity (-)
   - `daughter_discrete=0`

3. The code then perturbs the continuum daughter energy when `PERTURB_EXCITATON_ENERGY` is enabled. The lower-cut test is evaluated after this perturbation. The logged 0.029303 MeV is therefore the selected bin energy before perturbation, not necessarily the energy used by the lower-cut condition.

4. The bridge diagnostic nevertheless reports:
   - `initial_energy_MeV=0.079303252558488524`
   - `initial_spin=7`
   - `initial_parity=1`
   - `ndisc=1`
   - `rejected_angular_momentum=1`
   - `accepted=0`

The diagnostic corresponds to the pre-transition `mcurr`, not the newly selected continuum daughter `mnext`.

## 3. Source-level mismatch

In `libcgmf/src/specmc.cpp`, the relevant order is:

- `mcFindNext(...)` creates `mnext` from the next continuum/discrete population.
- If the next state is continuum, `PERTURB_EXCITATON_ENERGY` may update `mnext`'s energy.
- The lower-cut condition is then evaluated using `mnext.getE()`.
- But the bridge selector is called with the previous state:

```cpp
const int index0 = mcSelectE1DiscreteBridge(
    c0, mcurr.getE(), mcurr.getJ(), mcurr.getP(), "lower_cut");
```

This is an internal state-reference inconsistency: the handoff trigger is based on the post-transition `mnext`, while the discrete candidate's energy, spin, and parity admissibility are evaluated against the pre-transition `mcurr`.

For this branch, the bridge selector uses its energy argument for the strict candidate test `candidate.energy < initialEnergy`, and its spin/parity arguments for the E1 selection rules. Therefore the mismatch can:
- report the wrong parent state in diagnostics;
- test angular-momentum and parity rules against the wrong continuum state;
- admit a discrete candidate whose energy is below `mcurr` but not below the actual post-perturbation `mnext` energy.

The call site is guarded by `c0 == mnext.getN()`, so the relevant candidate state is the same nucleus. The state to test at this point is the current `mnext` after its energy perturbation.

## 4. Does correcting the state reference solve I-136 event 6?

No. It corrects which state is tested; it does not establish an allowed bridge.

The only checked-in CGMF discrete I-136 state is the ground state (J^\pi=1^-). The post-transition continuum daughter reported by the population selector is (J^\pi=6^-). From that state to (1^-):
- (|\Delta J|=5), so E1 is forbidden;
- parity is unchanged, also inconsistent with E1;
- M1 and E2 cannot bridge a five-unit spin difference either.

The exact post-perturbation daughter energy was not emitted by the current diagnostic, so it must be logged in a follow-up instrumented run before making any energy-reachability claim. The existing event remains unmappable under the current E1-only bridge even if the selector is evaluated against the logged (J=6^-) daughter.

Thus two findings must remain separate:
- **Source defect candidate:** lower-cut selector is passed `mcurr` instead of the post-transition `mnext`.
- **Remaining physical/data-model blockage:** with only the (1^-) ground state available, the logged (6^-) daughter has no E1 bridge.

## 5. Corrected interpretation of the Nmax evidence

The RIPL/CGMF count comparison remains an observed file-level fact, but the causal lineage must not be overstated.

In `ripl2levels.cpp`:
- `readDiscreteLevelData()` reads the already-prepared `discreteLevels.dat` and sets `ndisc` from the file header. It does not apply `Nmax` during that runtime read.
- `riplReadDiscreteLevelData()` reads `RIPLDATA`, sets `MaxLevelCtl` to `reassign`, and calls `riplSetNmax()`.
- `getRiplDiscreteLevels()` also uses `reassign` when importing RIPL records.
- `riplSetNmax()` maps `reassign` and `extended` to `Nmax`, `normal` to `Nc`, and `all` to `Nol`.

This proves that the codebase contains an RIPL import path that applies `Nmax`; it does not, by itself, prove that this historical path generated the checked-in `data/discreteLevels.dat`. The conversion writer/tool invocation and exact data-generation provenance remain to be recovered. The existing I-136 lineage report correctly leaves that link unresolved.

## 6. Next controlled action

Do not immediately merge a production behavior change. First prepare a minimal diagnostic/test patch:

1. Log `mcurr` and `mnext` (nucleus, energy before/after perturbation, spin, parity, discrete flag) at the lower-cut site.
2. Add a deterministic unit-level regression where the pre-transition and post-transition states differ and a candidate level lies between their energies. Assert that the post-transition energy controls candidate reachability.
3. In an isolated fixed-seed contrast, compare the current call with a candidate call using `mnext.getE(), mnext.getJ(), mnext.getP()`. Keep the production default and golden outputs unchanged until the contrast is reviewed.
4. Re-run the complete native suite and G2 matrix. If I-136 remains unmappable, retain that failure as a distinct unresolved physics/data-model issue; do not add unsupported high-multipole strengths or skip the event.
5. Separately recover the historical generator for `data/discreteLevels.dat`, including source revision, command, mode, and input hashes.

## 7. Evidence status

- Run #314 workflow failure and job-step outcomes: **COMPUTATION_VERIFIED**.
- Event 6 pre-perturbation continuum daughter and selector diagnostic: **COMPUTATION_VERIFIED** from archived artifact.
- Lower-cut call-site state mismatch (`mcurr` versus `mnext`): **SOURCE_VERIFIED**.
- Exact post-perturbation daughter energy: **NOT LOGGED / BLOCKED**.
- Whether a `mnext`-based call alone resolves event 6: **NO**; current checked-in level scheme still has no E1-allowed path from the logged (6^-) daughter to the (1^-) ground state.
- Historical generation provenance of `discreteLevels.dat`: **BLOCKED**.
- Complete G2 matrix and P/H/O competition: **NOT COMPLETED**.

No gas-theory mechanism or empirical G2 claim is upgraded by this audit.


## 8. Follow-up candidate correction

After this audit, the lower-cut selector call was changed in commit
`4265ed5094270fceb522b1b0a2f8dc4ffb010619` to pass the selected
post-transition state (`mnext.getE(), mnext.getJ(), mnext.getP()`) rather
than the pre-transition state (`mcurr`). This is a narrow call-site
correction; it does not add multipoles, alter the discrete-level data, or
change the selector's E1 rules.

At the time this addendum was written, the new commit's CI result had not yet
been established. The correction is therefore **CANDIDATE / NOT YET
COMPUTATION_VERIFIED**. The expected I-136 result remains an unmappable
bridge under the current one-level scheme; the next run must confirm that
the diagnostic now reports the post-perturbation daughter state and must
record the exact post-perturbation energy.

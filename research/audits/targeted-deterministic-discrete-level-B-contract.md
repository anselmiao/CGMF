# Targeted deterministic discrete-level B: evidence audit and construction contract

**Branch:** `qi/fix-discrete-start-index`  
**Purpose:** replace byte-for-byte reconstruction of the historical randomized prepared file with a separately versioned, deterministic, source-audited candidate B.  
**Production data:** unchanged.  
**Evidence date:** 2026-11-21.

## 1. Decision

The historical baseline A remains frozen by repository blob identity and by the run-time path/digest recorded in the Actions #333 audit. Reconstructing its exact bytes is not a prerequisite for B: the CGMF 1.1.0 manual explicitly says missing parities are chosen randomly under an equal-parity assumption, and a later CGMF/BeoH report describes random sampling of missing spins/parities and additional levels. The original preparation notebook / random seed are not present in the inspected repository trees. Thus there is no uniquely defined historical output to reproduce from the surviving inputs alone.

B is a distinct, reproducible dataset candidate. It must never overwrite A, and its generator must not infer missing (J^\pi), gamma branches, multipolarities, or conversion coefficients.

**Important CI qualification:** Actions #333 did not pass the full G2 matrix. Build and several unit/seed checks passed, but the first Cf-252 production case failed at event 6. The run-time data audit succeeded; the matrix result remains failed/incomplete.

## 2. Source-backed facts checked in this pass

### 2.1 I-132

The ENSDF adopted-level evaluation (February 2005; NDS 104, 497 (2005)) lists:
- ground state: (0.0), (4^+), half-life 2.295 h;
- a tentative (22?\,(11)) keV ((5^+)) level;
- (120\,(20)) keV ((8^-)), half-life 1.387 h, XREF B (132I isomeric-transition decay);
- the 120-keV isomer has 14(2)% beta decay and 86(2)% IT;
- an approximately 98-keV E3 transition connects the (8^-) isomer to the tentative (22?)-keV ((5^+)) level.

The RIPL-3 record in the repository contains the corresponding 120-keV, (8^-), approximately 4.99e3-s isomer and an IT branch to the lower (22)-keV level. The current prepared CGMF `discreteLevels.dat` contains only the I-132 ground state (ndisc=1), consistent with the RIPL header fields (Nol=6, Nog=6, Nmax=1, Nc=1). Under the CGMF DEVUTIL reader's `reassign` mode, Nmax is the selected count; this matches the one-level prepared/runtime scheme and the same Nmax truncation mechanism as I-136.

**Implication:** I-132 is a plausible targeted B inclusion candidate, but the (22?\)-keV intermediate has uncertain energy and tentative (J^\pi). The generator must retain those uncertainties in a provenance manifest and must not silently present the central value as exact. It must also preserve the IT/beta competition and the observed gamma/ICC branch information; adding only a 120-keV level connected arbitrarily to the ground state is forbidden.

### 2.2 I-136

The ENSDF adopted-level evaluation (April 2018; NDS 152, 331 (2018)) lists:
- ground state: (0), ((1^-)), 83.4 s;
- 86.73(7) keV, ((2^-,1^-,0^-)), 0.4 ns;
- 201(26) keV, ((6^-)), 46.6(11) s, XREF D only (248Cm SF), not XREF C (252Cf SF).

The RIPL-3 file in this repository lists a 6− level at 640 keV with half-life 46.9 s and 100% beta decay. Its matching spin and near-identical half-life make it a strong candidate for the same long-lived isomer, but identity should be recorded as a source reconciliation, not assumed from those two fields alone. The energy is in serious conflict with ENSDF's 201(26) keV. Preserve both source values and the ENSDF uncertainty; do not overwrite the RIPL value silently.

The current prepared CGMF file contains only the 0-keV (1^-) I-136 state. Actions #333 confirmed that this was the file actually opened and captured its SHA-256.

**Critical limitation:** the ENSDF 201-keV state is above the event-6 initial excitation (about 19.0635 keV), so it cannot resolve event 6 by direct population or decay from that event state. Further, the evaluated 201-keV isomer is reported as beta-decaying, and its ENSDF cross-reference is to 248Cm SF rather than 252Cf SF. It must not be inserted as a prompt gamma bridge state merely to make the simulation continue. It may be recorded in the nuclear-level provenance catalog, but prompt-scheme inclusion is blocked until a physically justified gamma de-excitation scheme and production-relevance argument are established.

### 2.3 Existing prepared file and RIPL source

The current repository objects are unchanged from the pinned CGMF 1.1.0 data objects:
- `data/discreteLevels.dat`: Git blob `dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c`
- `data/ripl3-levels.dat`: Git blob `c3c3a816730deef172ccbd11b0dfd58b6d197d90`

These are Git blob identities, not SHA-256 file digests. The actual Actions #333 opened file SHA-256 is recorded separately in `actions-333-runtime-i136-bridge-failure-audit.md`.

The CGMF prepared file itself states that it was generated from evaluated RIPL-3 discrete levels and that missing spin/parity assignments were filled according to the CGMF manual's systematics rules. The inspected `ripl2levels.cpp` confirms that the `DEVUTIL` RIPL reader selects `Nmax` under `reassign`, and that its fallback can assign missing spin/parity using simple systematics. This source routine is not evidence that the missing historical notebook or exact random seed has been recovered.

## 3. Why byte reproduction of A is not a B gate

A is retained as a historical artifact with exact repository and run-time identities. If its preparation procedure used stochastic choices for missing quantum numbers and the original random state is unavailable, there is no unique basis for demanding one reconstructed byte sequence.

The correct separation is:
- A: frozen historical artifact, exact identity preserved;
- B: new deterministic, explicitly curated candidate;
- A/B: compare physical observables and event-level completeness under controlled conditions, not raw file bytes.

Byte comparisons remain useful for proving a particular artifact was not changed; they are not the scientific acceptance criterion for B.

## 4. Deterministic B manifest contract

The builder must consume a hand-reviewed manifest, not scrape and auto-accept all RIPL rows. Each nuclide entry must contain:
- ZAID and nuclide label;
- exact source URLs, evaluation date, bibliographic citation, source-file revision and SHA-256;
- per-level central energy, energy uncertainty, spin, parity, assignment quality (e.g. firm/tentative/ambiguous), half-life and half-life uncertainty;
- source-specific identifiers and cross-reference flags;
- explicit inclusion decision and rationale;
- each gamma branch's destination level, measured/evaluated photon branch, internal-conversion coefficient, multipolarity/mixing information and provenance;
- beta / IT / other competing decay fractions kept separate from gamma branches;
- a decision on whether the level belongs in the CGMF prompt discrete gamma scheme. A level may be catalogued but excluded from the prompt scheme.

### Hard validation gates

1. No unknown or ambiguous (J^\pi) may be silently converted to a fixed value.
2. No level is included in the prompt scheme without a defensible decay path and source-backed branch information.
3. Every gamma destination must be a lower-energy level present in the same nuclide scheme.
4. Gamma branch probabilities and conversion coefficients must be finite and nonnegative; normalization must be explicit and logged.
5. Multipolarity must be compatible with (Delta J) and parity. A mixed transition is accepted only if at least one declared component is allowed.
6. Beta and IT fractions must not be normalized as if they were gamma branches.
7. Uncertainties and tentative assignments remain in a sidecar provenance manifest even if CGMF's legacy fixed-width file cannot represent them.
8. B output is a separate artifact. The builder must not edit `data/discreteLevels.dat` in place.
9. The builder must emit a machine-readable decision report listing included, catalog-only, rejected, and blocked levels with reasons.
10. The generator must be deterministic: identical manifest + base file + script version => identical output bytes.

## 5. Proposed implementation sequence

**B0 — schema and validator (next):** implement a deterministic overlay builder that reads the frozen A file, applies only explicit manifest entries, validates level order, quantum numbers, branches and transition selection rules, and emits a separate candidate file plus provenance JSON. Add synthetic unit tests for valid branches, unknown (J^\pi), forbidden transitions, missing destinations, duplicate levels, and non-normalized branches.

**B1 — I-132 candidate:** construct a reviewed manifest for the 0-keV ground state, tentative 22-keV intermediate, and 120-keV (8^-) isomer. Preserve the tentative status and energy uncertainty; confirm gamma branch and conversion details against ENSDF before enabling it in the generated candidate. Compare the B scheme with A under the same executable, input deck and seed range.

**B2 — I-136 catalog-only record:** record the ENSDF 201(26)-keV (6^-) isomer and RIPL 640-keV conflict in the provenance catalog. Do not include it in the prompt gamma scheme yet. Separately investigate the event-6 19-keV continuum-state origin; the 201-keV state cannot explain it.

**B3 — controlled physics comparison:** compare complete event-paired outputs and distributions of prompt gamma multiplicity/energy, neutron multiplicity/energy, and TKE where those observables are actually emitted and recorded by the chosen CGMF configuration. Include uncertainties and per-seed reproducibility. Do not interpret differences as nuclear-physics effects until input differences are isolated.

## 6. Source links

- ENSDF I-136 Adopted Levels, Gammas (NDS 152, 331 (2018)): https://www.nndc.bnl.gov/ensdf/getadopted.jsp?nuc=136I
- ENSDF I-132 Adopted Levels, Gammas (NDS 104, 497 (2005), PDF): https://www.nndc.bnl.gov/ensnds/132/I/adopted.pdf
- ENSDF I-136 46.6-s isomer decay dataset: https://www.nndc.bnl.gov/nudat3/getdecaydataset.jsp?dsid=136i+bM+decay+%2846.6+s%29&nucleus=136XE
- IAEA RIPL-3 resource description: https://nucleus.iaea.org/Pages/ripl-3.aspx
- CGMF 1.1.0 User Manual, §1.3.7 "Fixing the level scheme" and §1.3.8 "Isomeric States": https://cgmf.readthedocs.io/_/downloads/en/latest/pdf/
- CGMF/BeoH report discussing stochastic missing-level and spin/parity sampling: https://www.osti.gov/servlets/purl/1878094

## 7. Status ledger

| Item | Status | Reason |
|---|---|---|
| Historical A repository blob identities | `COMPUTATION_VERIFIED` | Git objects pinned |
| A run-time opened path and byte SHA-256 | `COMPUTATION_VERIFIED` | Actions #333 audit |
| I-132 120-keV (8^-) isomer and IT fraction | `SOURCE_VERIFIED` | ENSDF adopted evaluation |
| I-132 22-keV intermediate exact energy/Jπ | `SOURCE_VERIFIED` with tentative assignment | ENSDF marks it 22?(11), (5+) |
| I-132 isomer's beta/IT competition in legacy CGMF prompt scheme | `BLOCKED` | Legacy level format has no explicit beta-branch field; modeling semantics need resolution |
| I-136 201(26)-keV (6^-) isomer | `SOURCE_VERIFIED` | ENSDF adopted evaluation |
| RIPL I-136 640-keV (6^-) entry | `SOURCE_VERIFIED` | Repository RIPL-3 record |
| RIPL I-136 energy is inconsistent with ENSDF | `SOURCE_VERIFIED` | 640 keV vs 201(26) keV, similar half-life |
| I-136 201-keV state resolves event 6 | `REJECTED` | Above 19-keV event energy; wrong production cross-reference |
| I-136 state belongs in prompt gamma scheme | `BLOCKED` | Evaluated record does not establish a prompt gamma cascade |
| Deterministic B generator | `NOT STARTED` | Contract defined; implementation and tests remain |
| A/B physical comparison | `NOT STARTED` | Requires validated B and complete event samples |


# Full-table quantum-number integrity audit

**Audit date:** 2026-11-21  
**Branch snapshot:** qi/diagnose-lpop-nan at parent commit 1c755240b49dce0e3ba46cbdd1684cbe6ea85b6b  
**Scope:** frozen runtime input data/discreteLevels.dat; no production data or physics rules modified.

## Result

The checked-in runtime table contains 3,351 nuclide records and 45,697 discrete-level records. A fixed-width scan found:

| Check | Count |
|---|---:|
| Spin-lattice violations | 114 |
| Distinct nuclides affected | 54 |
| Ground-state spin-lattice violations | 15 |
| Excited-state spin-lattice violations | 99 |
| Invalid parity fields (not +1 or -1) | 3 |
| Missing/negative spin fields | 0 |

All 114 spin-lattice violations occur for odd mass number A with integer J. No even-A half-integer violations were found. For a nucleus with A nucleons, the expected angular-momentum lattice is:

- even A: integer J;
- odd A: half-integer J.

Equivalently, 2J must be an integer and its parity must match A modulo 2. The file stores J itself in units of hbar, not 2J. The runtime code uses this spin value directly in angular-momentum differences.

## Method and reproducibility

The scan used the same fixed-width field boundaries read by libcgmf/src/ripl2levels.cpp:

| Field | Slice |
|---|---|
| Isotope ZAID | header [6:12] |
| Number of levels | header [12:17] |
| Excitation energy | level [0:10] |
| Spin J | level [10:15] |
| Parity | level [15:18] |
| Gamma-branch count | level [31:34] |

For every level, the scanner skips exactly the number of following gamma-branch rows before reading the next level or isotope. The source artifact is identified by:

- Git blob SHA-1: dfd64cd3d7d890fec4b74e4bb82575ce0cc82e7c
- Raw-file SHA-256: c79679e4247ddf69e3766ccce0b3177fcb7b253e26fd50ff621d2721d023c80e

The complete-file counts above were obtained by parsing the complete GitHub API file body with these fixed-width fields. The added Python audit utility reproduces the same contract; its seven synthetic parser tests passed locally. CI run 44843184310 independently ran the Python utility against the complete repository file and verified the frozen hash and all counts. All 42 Python audit tests passed in that run (including the seven new parser tests); the complete-table audit step passed. The generated JSON now uploads as a workflow artifact so the row-level findings remain inspectable.

## Ground-state anomalies

The 15 ground-state spin-lattice findings are:

| Nuclide | ZAID | Runtime Jπ |
|---|---:|---|
| Br-89 | 35089 | 2+ |
| Kr-101 | 36101 | 2− |
| Sr-105 | 38105 | 5+ |
| Sr-107 | 38107 | 1+ |
| Zr-105 | 40105 | 4+ |
| Zr-107 | 40107 | 3+ |
| Zr-109 | 40109 | 7+ |
| Zr-111 | 40111 | 7+ |
| Mo-115 | 42115 | 3+ |
| Mo-117 | 42117 | 6− |
| Ru-119 | 44119 | 5+ |
| Ru-121 | 44121 | 5− |
| Ru-123 | 44123 | 3− |
| Sm-129 | 62129 | 3− |
| Lu-157 | 71157 | 4+ |

The three parity values outside {-1,+1} are ground-state records:

| Nuclide | ZAID | Runtime J | Stored parity |
|---|---:|---:|---:|
| Sn-118 | 55118 | 2 | 0 |
| Pr-121 | 59121 | 3/2 | 0 |
| Re-172 | 75172 | 5 | 0 |

The 114 spin violations include 99 excited-state rows. They should be retained individually in the generated JSON audit output rather than collapsed to only a per-nuclide status.

## Two checked source comparisons

### Br-89

The runtime table record is 89Br / ZAID 35089, with one level at zero energy and Jπ=2+. Because A=89 is odd, integer J is inconsistent with the nuclear spin lattice.

The paired RIPL-3 record has its ground-state spin/parity fields unassigned (-1, 0), while its textual Jπ candidate field reads (3/2−, 5/2−). Neither candidate is 2+. This is a source-to-prepared-file discrepancy; it is not proof of which historical conversion rule or file revision caused it.

### Zr-105

The runtime record is 105Zr / ZAID 40105, with one zero-energy level and Jπ=4+. Since A=105 is odd, integer J is inconsistent with the spin lattice.

The paired RIPL-3 row has unassigned Jπ fields (-1, 0) and no textual adopted candidate in that row. It therefore does not provide evidence for the runtime 4+ assignment.

These examples are independently confirmed from the exact rows in data/discreteLevels.dat and data/ripl3-levels.dat. They do not authorize replacing either assignment with a guessed value.

The CGMF User Manual states that uncertain RIPL Jπ candidate lists are resolved by selecting the first option, and that a completely unknown ground state defaults to 0+ for even-even, 1+ for odd-odd, and 1/2+ for even-odd nuclei. Under those documented rules, the Br-89 prepared 2+ assignment is inconsistent with the RIPL candidate text (3/2−, 5/2−), and the Zr-105 prepared 4+ assignment is inconsistent with the odd-A unknown-ground-state default 1/2+. The official preparation method is documented at https://cgmf.readthedocs.io/en/latest/discreteLevels.html. This sharpens the source-to-prepared-file discrepancy, but the exact historical notebook, class version, inputs, and random seed are still unavailable; it does not identify the causal software defect.

## Interpretation and limits

The audit establishes internal consistency defects in the prepared runtime table under the physical interpretation of its spin field as J. It does not establish that every flagged row came from one faulty converter operation, nor does it identify the exact historical generation script/version.

CGMF's preparation documentation describes transformLevelDataFile.ipynb and Nucleus.py as the process for generating the CGMF-ready table from RIPL-3, including repairs to missing/uncertain spin, parity, and gamma transitions. The referenced converter source was not found in the inspected repository trees. The 2021 CGMF 1.1.0 release note says the prepared table was expanded to include all isotopes, but it does not record a reproducible generation command or converter revision.

Therefore:
- The original prepared table remains frozen as baseline A.
- Do not rewrite data/discreteLevels.dat from these counts alone.
- Do not infer Jπ from mass parity alone; use evaluator-grounded assignments and retain ambiguity.
- Keep tentative or ambiguous levels in a separate catalogue; only promote levels with explicit, adopted, unique Jπ and a separately justified decay scheme.
- Do not treat RIPL Nol as a complete prompt-discrete level scheme.
- Do not restore nearest-J fallback or broaden multipolarities to hide lower-cut failures.

## Evidence ledger

| Claim | Status | Basis |
|---|---|---|
| Runtime reads these fixed-width J, parity, and gamma-count fields | SOURCE_VERIFIED | libcgmf/src/ripl2levels.cpp |
| Runtime table has 3,351 nuclei and 45,697 level rows | COMPUTATION_VERIFIED | Full GitHub API file scan |
| 114 J/A lattice violations across 54 nuclides | COMPUTATION_VERIFIED | Full GitHub API file scan |
| 15 ground-state violations and 3 non-±1 parity fields | COMPUTATION_VERIFIED | Full GitHub API file scan |
| Br-89 and Zr-105 prepared values disagree with their RIPL-3 rows | SOURCE_VERIFIED | Exact fixed-width records from both files |
| Exact historical converter invocation produced these assignments | BLOCKED | Converter source/version/invocation not recovered |
| All 114 findings share one conversion bug | NOT ESTABLISHED | Needs source-lineage and evaluator-by-evaluator reconciliation |
| This audit resolves the 11 lower-cut event failures | NOT ESTABLISHED | Quantum-number defects are relevant, but event-level causal mapping remains to be tested |

## Files added

- scripts/audit_discrete_level_quantum_numbers.py — read-only full-table auditor, optional fail-on-violations flag.
- tests/test_audit_discrete_level_quantum_numbers.py — parser contract tests.
- .github/workflows/nuclide-audit.yml — executes the parser against the complete frozen runtime file and checks its digest/count baseline.

The workflow intentionally records known anomalies without changing the production input or failing only because these baseline anomalies exist. If the data file changes, the expected digest/counts must be explicitly reviewed and updated.

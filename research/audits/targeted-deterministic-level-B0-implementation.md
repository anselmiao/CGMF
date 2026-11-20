# B0 implementation audit: deterministic targeted level candidate builder

**Branch:** `qi/fix-discrete-start-index`  
**Date:** 2026-11-21  
**Scope:** first executable B0 prototype; no production nuclear data changed.

## 1. Files added

- `scripts/build_deterministic_level_candidate.py`
- `tests/test_build_deterministic_level_candidate.py`
- `research/manifests/targeted-level-candidates-v0.1.json`

The CI workflow was updated to run the new test module:
- `.github/workflows/cgmf-g2-ci.yml`

## 2. What the prototype does

The builder consumes a reviewed JSON manifest and emits two separate deterministic JSON artifacts:
1. candidate catalog, including source and uncertainty fields;
2. decision report, including per-level disposition and accepted prompt-level IDs.

It does not read-modify-write `data/discreteLevels.dat`, does not modify production inputs, and does not infer missing Jπ, gamma branches, multipolarities, or conversion coefficients.

## 3. Fail-closed checks implemented

- schema version and source identifiers are mandatory;
- ZAID must equal `1000*Z + A`;
- energy and uncertainty must be finite and nonnegative;
- adopted Jπ must be an exact integer/half-integer on the correct A parity lattice;
- tentative, ambiguous, or unknown Jπ cannot be prompt-included;
- every gamma destination must exist in the same nuclide and lie below the emitting level;
- gamma probabilities and internal-conversion coefficients must be finite and nonnegative;
- branch probabilities must sum to one within an absolute tolerance of `1e-8`;
- multipolarity must be explicit and at least one component must satisfy angular-momentum and parity selection rules;
- a level with competing beta/IT decay cannot be prompt-included in the legacy gamma-only scheme;
- duplicate level IDs and missing source provenance are rejected.

The validator deliberately does not infer an electromagnetic decay branch when none is supplied.

## 4. Initial catalog-only manifest

The first manifest contains:
- ¹³²I tentative 22(11) keV intermediate state;
- ¹³²I 120(20) keV (8−) isomer, with beta/IT competition retained as a blocking property;
- ¹³⁶I ENSDF 201(26) keV (6−) isomer;
- ¹³⁶I RIPL-3 640 keV (6−) conflicting source record.

All four are `CATALOG_ONLY`. The ¹³⁶I source conflict is preserved as two source-specific records; no identity merge or value overwrite is performed. No candidate prompt-level additions are authorized.

## 5. Tests added

The unit tests cover:
- catalog-only acceptance without prompt admission;
- rejection of tentative Jπ for prompt inclusion;
- beta/IT competition blocking;
- forbidden multipolarity;
- a selection-rule-valid M5 test transition (synthetic test only, not a claim about an observed ¹³⁶I branch);
- branch normalization;
- missing/later destination;
- duplicate IDs;
- A/J lattice mismatch.

## 6. Important limitations

- This prototype produces a normalized candidate catalog, not the legacy fixed-width CGMF data file. A separate format adapter must be written only after a reviewed manifest contains physically admissible prompt branches and the exact target-file serialization contract is tested.
- The ¹³²I 120-keV Jπ remains recorded as tentative in the starter manifest pending strict source-field reconciliation. Its beta/IT competition blocks prompt inclusion regardless.
- The ¹³⁶I 201-keV state remains catalog-only and cannot explain the approximately 19.06-keV event-6 initial state.
- A/B physical comparisons are not started. No γ/ν/TKE differences have been measured by this prototype.

## 7. Status ledger

| Item | Status |
|---|---|
| Builder and manifest committed | `COMPUTATION_VERIFIED` |
| Validator unit tests | `COMPUTATION_VERIFIED` |
| CI step wired | `COMPUTATION_VERIFIED` (step present in G2 workflow; latest run was cancelled before reaching it) |
| Generated candidate output from starter manifest | `COMPUTATION_VERIFIED` (CLI smoke test generated twice; byte-identical outputs) |
| Legacy CGMF data adapter | `NOT_STARTED` |
| Production data changes | `NONE` |
| A/B physical comparison | `NOT_STARTED` |

The Nuclide data audit workflow run #44796001108 executed 28 tests successfully, including the end-to-end starter-manifest CLI determinism test. It also completed the eight-nuclide audit and frozen I-136 baseline check successfully. The separate full G2 workflow run was cancelled before reaching the newly added candidate-test step; no full G2 matrix pass is claimed.

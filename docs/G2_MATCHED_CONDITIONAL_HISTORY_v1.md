# Matched-pair conditional G2 history permutation

The script `tools/analysis/g2MatchedHistoryPermutation.py` is a complementary sensitivity analysis to the coarsened-strata multivariate test.

## Matching

It builds one record per complete LF/HF event pair. Matching is exact on:
- LF and HF fragment A and Z;
- LF and HF stored parity indices.

It matches approximately on:
- LF and HF initial excitation;
- LF and HF stored spin;
- mean LF/HF pre-fragment momentum magnitude and the vector momentum-closure residual.

Continuous covariates are standardized across complete events. Within each exact group, all pairwise distances are computed and a deterministic greedy disjoint matching selects the shortest pairs first. The caliper is the standardized RMS distance across the six continuous covariates.

## Outcome/history features

Each fragment contributes the same 14-coordinate summary used by the multivariate conditional analysis: neutron multiplicity and energy summaries, neutron direction moments relative to fragment motion, gamma multiplicity/energy, internal-conversion count, and valid timestamp count. Zero-neutron fragments remain in the analysis.

For each matched pair, form LF and HF feature-difference vectors. The omnibus statistic is the squared Frobenius norm of their cross-covariance matrix after coordinate-wise scaling. The randomization null flips the sign of the entire HF difference vector independently for each matched pair. The full vector is the permutation unit; individual feature coordinates are never flipped independently.

## Example

```bash
python3 tools/analysis/g2MatchedHistoryPermutation.py \
  path/to/mixed-history.jsonl \
  --output results/matched-history.json \
  --calipers 1.5,2.5 \
  --permutations 5000 \
  --seed 20261119
```

## Interpretation boundary

This is an exploratory matched conditional-association test, not a causal test. The matching is approximate, greedy rather than globally optimal, and may leave residual confounding. Explicit scission configuration, event TKE/TXE, and complete angular-momentum coupling are not represented in the current sidecar. A small p-value means that matched histories retain association under the chosen matching specification; it does not establish direct cross-fragment interaction or a 气论 mechanism.

Always report matched-pair counts, unmatched events, match-distance diagnostics, caliper sensitivity, and the top feature-level associations. Do not select a caliper after seeing which one produces the smallest p-value.

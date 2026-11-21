# G2 next development batch v2 (uncommitted)

This batch corrects a seed-independence flaw found in the previous proposal and refines model nesting.

- `tools/analysis/g2EventStateModelCompetition.py`: requires sibling `rng-audit.tsv`, checks actual train/test seed disjointness, includes M0-M3, and tests a training-residualized nonlinear TXE×TKE proxy interaction.
- `tools/tests/testG2EventStateModelCompetition.py`: unit tests including seed audit and overlap gates.
- `tools/tests/validateG2SeedMatrix.py` + `testG2SeedMatrix.py`: fail-fast same-condition seed-range overlap validation.
- `tools/tests/g2SidecarMatrix.json`: replaces the overlapping 10–49 case with a 200-event 401–600 case.
- `.github/workflows/cgmf-g2-ci.yml`: validates matrix seed ranges and runs bidirectional held-out-seed model comparisons.
- `docs/G2_EVENT_STATE_MODEL_COMPETITION_v2.md`: method and interpretation boundaries.

No commit or push has been made. The new code is locally tested on Run #43 artifacts; future three-range CI results are pending.

See `G2_ROUND_REPORT.md` for the Run #43 correction and current evidence status.

The `results/` directory contains the two bidirectional Run #43 JSON outputs used in the report. They are retrospective computations on the already available two disjoint seed ranges, not results from the proposed third 401–600 CI run.

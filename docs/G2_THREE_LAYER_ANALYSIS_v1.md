# G2 three-layer analysis prototype

## Purpose

```text
CGMF mixed-history JSONL
  -> within-fragment ordered cascade summaries
  -> LF/HF event-level conditional permutation
  -> optional idealized detector projection
```

Run:

```bash
python3 tools/analysis/g2ThreeLayerAnalysis.py \
  path/to/mixed-history.jsonl \
  --output results/three-layer.json \
  --excitation-bin-MeV 1.0 \
  --permutations 5000 \
  --seed 20261119
```

Optional idealized detector configuration:

```json
{
  "threshold_MeV": 0.5,
  "efficiency_curve": [[0.5, 0.25], [1.0, 0.45], [3.0, 0.6], [6.0, 0.5]],
  "detectors": [
    {"id": "D0", "direction": [1, 0, 0], "half_angle_deg": 12},
    {"id": "D1", "direction": [-1, 0, 0], "half_angle_deg": 12}
  ]
}
```

Pass it with `--detector-config detector.json`.

## Statistical definitions

### Layer 1: within-fragment sequence

For consecutive neutron emissions in the original mixed transition order, the script reports the adjacent Lab-energy correlation and stratifies pairs by the number of intervening transitions. It separately counts intervening gamma and internal-conversion transitions.

The transition index is an ordering variable, not elapsed physical time. No neutron emission time is inferred.

### Layer 2: cross-fragment conditional permutation

Each event contributes at most one LF and one HF summary: the mean Lab energy of all neutrons emitted by that fragment in that event. Events are stratified by exact (A_L, Z_L, A_H, Z_H) and binned initial fragment excitation energies. The HF event summary is permuted among events within each stratum; the complete event summary is the permutation unit.

The statistic is the Pearson correlation between within-stratum centered LF and HF mean energies. A two-sided Monte Carlo permutation p-value is reported with the plus-one correction.

This is an initial, deliberately conservative test, not a complete conditional-independence test:
- no conditioning on TKE/TXE, scission configuration, total angular momentum, or other shared variables absent from the current sidecar;
- singleton strata are excluded and counted;
- the analysis is restricted to events with at least one neutron from each fragment;
- event-mean energies do not retain all features of the full histories;
- a residual association is not proof of direct cross-fragment interaction.

### Layer 3: detector projection

The optional projection applies a Lab-energy threshold, piecewise-linear energy-dependent single-neutron efficiency, and conical angular acceptance for each idealized detector. Detection draws are reproducible for a fixed seed.

It deliberately does not model energy/time resolution, TOF windows, dead time, pile-up, trigger logic, gamma tagging, correlated multi-hit efficiency, backgrounds, or cross-talk. It must not be described as a Bai or Schuster response model until those apparatus-specific effects and geometries are implemented and validated.

## Tests

Run synthetic-fixture tests:

```bash
python3 -m unittest discover -s tools/tests -p 'testG2ThreeLayerAnalysis.py' -v
```

These tests verify code behavior only. They are not CGMF simulations and do not use or reproduce any user-local event data.

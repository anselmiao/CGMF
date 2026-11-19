#!/usr/bin/env python3
"""Unit tests for g2ThreeLayerAnalysis.py using synthetic fixtures only."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("..") / "analysis" / "g2ThreeLayerAnalysis.py"
SPEC = importlib.util.spec_from_file_location("g2_three_layer", MODULE_PATH.resolve())
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)


def neutron(index, energy, direction=(1.0, 0.0, 0.0)):
    return {
        "emission_index": index,
        "particle_type": "neutron",
        "energy_cm_MeV": energy,
        "neutron_index": 0,
        "neutron_kinematics": {
            "energy_lab_MeV": energy,
            "direction_lab": list(direction),
        },
    }


def fragment(event_id, side, a, excitation, transitions):
    return {
        "schema": ANALYSIS.SCHEMA,
        "run_id": "synthetic",
        "event_id": event_id,
        "fragment_side": side,
        "initial_fragment": {
            "A": a, "Z": 40 if side == "LF" else 52,
            "excitation_MeV": excitation,
        },
        "transitions": transitions,
    }


class ThreeLayerAnalysisTests(unittest.TestCase):
    def test_mixed_history_order_and_intervening_gamma(self):
        row = fragment(1, "LF", 100, 8.0, [
            neutron(0, 1.0),
            {"emission_index": 1, "particle_type": "gamma", "energy_cm_MeV": 0.2},
            neutron(2, 2.0),
        ])
        parsed = ANALYSIS.validate_fragment(row)
        result = ANALYSIS.intra_fragment([parsed])
        self.assertEqual(result["adjacent_neutron_pairs"], 1)
        self.assertEqual(result["by_transition_gap"]["1"]["pairs"], 1)
        self.assertEqual(result["by_transition_gap"]["1"]["mean_next_MeV"], 2.0)

    def test_zero_neutron_fragment_is_valid_and_counted(self):
        row = fragment(1, "HF", 140, 7.0, [])
        parsed = ANALYSIS.validate_fragment(row)
        result = ANALYSIS.intra_fragment([parsed])
        self.assertEqual(result["fragment_count"], 1)
        self.assertEqual(result["transition_counts"]["neutron"], 0)

    def test_cross_fragment_permutation_uses_whole_event_summaries(self):
        events = {}
        for event_id, energy in enumerate((1.0, 2.0, 3.0, 4.0), 1):
            events[event_id] = {
                "LF": {"A": 100, "Z": 40, "excitation": 8.0,
                       "neutrons": [{"energy": energy}]},
                "HF": {"A": 140, "Z": 52, "excitation": 9.0,
                       "neutrons": [{"energy": energy * 2.0}]},
            }
        result = ANALYSIS.cross_fragment(events, 1.0, 199, 17)
        self.assertEqual(result["events_with_both_sides_emitting"], 4)
        self.assertEqual(result["eligible_events_in_strata_size_ge_2"], 4)
        self.assertAlmostEqual(result["observed_within_stratum_residual_correlation"], 1.0)
        self.assertEqual(result["permutations_requested"], 199)

    def test_detector_projection_is_seed_reproducible(self):
        events = {1: {"LF": {"neutrons": [{
            "energy": 2.0, "direction": (1.0, 0.0, 0.0),
            "transition": {"neutron_index": 0},
        }]}}}
        config = {
            "threshold_MeV": 0.5,
            "efficiency_curve": [[0.0, 1.0], [3.0, 1.0]],
            "detectors": [{"id": "D0", "direction": [1, 0, 0], "half_angle_deg": 10}],
        }
        a = ANALYSIS.detector_projection(events, config, 123)
        b = ANALYSIS.detector_projection(events, config, 123)
        self.assertEqual(a["hits"], b["hits"])
        self.assertEqual(a["detected_neutron_hits"], 1)

    def test_duplicate_fragment_key_rejected(self):
        row = fragment(1, "LF", 100, 8.0, [])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.jsonl"
            path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate fragment"):
                ANALYSIS.read_records(path)


if __name__ == "__main__":
    unittest.main()

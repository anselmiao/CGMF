#!/usr/bin/env python3
"""Synthetic tests for conditional multivariate G2 history analysis."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent / "analysis" / "g2ConditionalHistoryAnalysis.py"
SPEC = importlib.util.spec_from_file_location("g2_conditional_history", MODULE)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def record(event, side, a, z, excitation, energy):
    transitions = []
    if energy is not None:
        transitions = [{
            "emission_index": 0, "particle_type": "neutron",
            "energy_cm_MeV": energy * 0.7,
            "timestamp_valid": False,
            "neutron_kinematics": {
                "energy_cm_MeV": energy * 0.7,
                "energy_lab_MeV": energy,
                "direction_lab": [1.0, 0.0, 0.0],
            },
        }]
    return {
        "schema": A.SCHEMA, "run_id": "test", "event_id": event,
        "fragment_side": side,
        "initial_fragment": {
            "A": a, "Z": z, "excitation_MeV": excitation,
            "pre_fragment_momentum_MeV_c": [1000.0, 0.0, 0.0],
        },
        "transition_count": len(transitions), "transitions": transitions,
    }


class ConditionalHistoryTests(unittest.TestCase):
    def test_zero_neutron_side_is_retained(self):
        events = {
            1: {
                "LF": record(1, "LF", 100, 40, 8.0, None),
                "HF": record(1, "HF", 140, 54, 9.0, 1.0),
            }
        }
        lf = A.fragment_features(events[1]["LF"])
        hf = A.fragment_features(events[1]["HF"])
        self.assertEqual(lf[0], 0.0)
        self.assertEqual(hf[0], 1.0)

    def test_complete_event_pair_and_strata(self):
        events = {}
        for i in range(1, 9):
            events[i] = {
                "LF": record(i, "LF", 100, 40, 8.1 + (i % 2)*0.1, float(i)),
                "HF": record(i, "HF", 140, 54, 9.1 + (i % 2)*0.1, float(2*i)),
            }
        rows, incomplete = A.make_rows(events, 2.0)
        self.assertEqual(len(rows), 8)
        self.assertEqual(incomplete, 0)
        result = A.run_width(rows, 2.0, 99, 7)
        self.assertEqual(result["eligible_events"], 8)
        self.assertGreaterEqual(result["permutation_p_one_sided_upper_tail"], 0.01)

    def test_incomplete_event_is_reported(self):
        events = {1: {"LF": record(1, "LF", 100, 40, 8.0, 1.0)}}
        rows, incomplete = A.make_rows(events, 1.0)
        self.assertEqual(rows, [])
        self.assertEqual(incomplete, 1)

    def test_duplicate_fragment_rejected(self):
        row = record(1, "LF", 100, 40, 8.0, 1.0)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.jsonl"
            p.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                A.load_events(p)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Synthetic tests for matched-pair conditional G2 history permutation."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent / "analysis" / "g2MatchedHistoryPermutation.py"
SPEC = importlib.util.spec_from_file_location("g2_matched_history", MODULE)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def row(eid, side, a, z, parity, ex, spin, energy):
    transitions = []
    if energy is not None:
        transitions = [{
            "emission_index": 0, "particle_type": "neutron",
            "energy_cm_MeV": energy*0.7, "timestamp_valid": False,
            "neutron_kinematics": {
                "energy_cm_MeV": energy*0.7, "energy_lab_MeV": energy,
                "direction_lab": [1.0, 0.0, 0.0],
            },
        }]
    return {
        "schema": A.SCHEMA, "run_id": "synthetic", "event_id": eid,
        "fragment_side": side,
        "initial_fragment": {
            "A": a, "Z": z, "parity_index": parity,
            "excitation_MeV": ex, "spin_stored": spin,
            "pre_fragment_momentum_MeV_c": [1000.0, 0.0, 0.0],
        },
        "transitions": transitions,
    }


class MatchedHistoryTests(unittest.TestCase):
    def test_zero_neutron_history_retained(self):
        r = row(1, "LF", 100, 40, 1, 8.0, 4, None)
        self.assertEqual(A.features(r)[0], 0.0)

    def test_matching_is_disjoint_and_exact_on_group(self):
        records = []
        for i in range(1, 7):
            L = row(i, "LF", 100, 40, 1, 8.0+i*0.1, 4+i*0.1, float(i))
            H = row(i, "HF", 140, 54, -1, 9.0+i*0.1, 6+i*0.1, float(2*i))
            records.append({
                "event_id": i, "group": (100,40,140,54,1,-1),
                "cov": [L["initial_fragment"]["excitation_MeV"],
                        H["initial_fragment"]["excitation_MeV"],
                        L["initial_fragment"]["spin_stored"],
                        H["initial_fragment"]["spin_stored"],1000.0,1000.0],
                "x": A.features(L), "y": A.features(H),
            })
        pairs = A.greedy_pairs(records)
        self.assertEqual(len(pairs), 3)
        ids = [r["event_id"] for _,a,b in pairs for r in (a,b)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_sign_flip_permutation_reproducible(self):
        records = []
        for i in range(1, 9):
            L = row(i, "LF", 100, 40, 1, 8.0+i*0.01, 4, float(i))
            H = row(i, "HF", 140, 54, -1, 9.0+i*0.01, 6, float(2*i))
            records.append({
                "event_id": i, "group": (100,40,140,54,1,-1),
                "cov": [8.0+i*0.01,9.0+i*0.01,4,6,1000,1000],
                "x": A.features(L), "y": A.features(H),
            })
        pairs = A.greedy_pairs(records)
        x = A.test_pairs(pairs, 3.0, 99, 123)
        y = A.test_pairs(pairs, 3.0, 99, 123)
        self.assertEqual(x, y)
        self.assertEqual(x["matched_pairs"], 4)
        self.assertIn("top_absolute_feature_correlations", x)

    def test_duplicate_side_rejected(self):
        r = row(1, "LF", 100, 40, 1, 8.0, 4, 1.0)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.jsonl"
            p.write_text(json.dumps(r)+"\n"+json.dumps(r)+"\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                A.load_events(p)


if __name__ == "__main__":
    unittest.main()

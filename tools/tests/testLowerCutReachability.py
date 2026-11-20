import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from lowerCutReachability import analyze_document, transition_allowed


class LowerCutReachabilityTests(unittest.TestCase):
    def test_i136_event6_unreachable_even_with_e1_m1_e2(self):
        doc = {
            "schema_version": "cgmf-lower-cut-reachability-v1",
            "discrete_levels": [
                {"level_id": "I136-gs", "energy_MeV": 0.0, "spin": "1", "parity": -1}
            ],
            "continuum_samples": [{
                "sample_id": "I136-event6",
                "nuclide": "I-136",
                "energy_MeV": 0.019063529367160315,
                "bin_min_MeV": 0.014651626279244257,
                "bin_max_MeV": 0.054303252558488516,
                "spin": "6",
                "parity": -1,
            }],
        }
        result = analyze_document(doc)["results"][0]
        self.assertEqual(result["candidate_levels"][0]["allowed_multipolarities"], [])
        self.assertFalse(result["schemes"]["current_E1_only"]["reachable_at_sample"])
        self.assertFalse(result["schemes"]["comparison_E1_M1_E2"]["reachable_at_sample"])
        self.assertEqual(result["schemes"]["comparison_E1_M1_E2"]["reachable_bin_fraction"], 0.0)

    def test_e1_parity_and_delta_j(self):
        initial = {"spin": "2", "parity": -1}
        final = {"spin": "1", "parity": 1}
        self.assertTrue(transition_allowed(initial, final, "E1"))
        self.assertFalse(transition_allowed(initial, final, "M1"))
        self.assertFalse(transition_allowed(initial, final, "E2"))

    def test_m1_same_parity(self):
        self.assertTrue(transition_allowed(
            {"spin": "2", "parity": 1}, {"spin": "1", "parity": 1}, "M1"
        ))

    def test_e2_delta_j_two_same_parity(self):
        self.assertTrue(transition_allowed(
            {"spin": "3", "parity": -1}, {"spin": "1", "parity": -1}, "E2"
        ))

    def test_interval_fraction_from_accessible_level_threshold(self):
        doc = {
            "schema_version": "cgmf-lower-cut-reachability-v1",
            "discrete_levels": [
                {"level_id": "level-1", "energy_MeV": 0.02, "spin": "2", "parity": 1}
            ],
            "continuum_samples": [{
                "sample_id": "fraction",
                "energy_MeV": 0.03,
                "bin_min_MeV": 0.01,
                "bin_max_MeV": 0.05,
                "spin": "4",
                "parity": 1,
            }],
        }
        result = analyze_document(doc)["results"][0]
        # Only E2 is allowed for 4+ -> 2+ among the tested multipoles.
        self.assertEqual(result["schemes"]["current_E1_only"]["reachable_bin_fraction"], 0.0)
        self.assertAlmostEqual(
            result["schemes"]["comparison_E1_M1_E2"]["reachable_bin_fraction"], 0.75
        )

    def test_rejects_invalid_bin(self):
        doc = {
            "schema_version": "cgmf-lower-cut-reachability-v1",
            "discrete_levels": [],
            "continuum_samples": [{
                "energy_MeV": 0.1, "bin_min_MeV": 0.2, "bin_max_MeV": 0.1,
                "spin": "1", "parity": 1,
            }],
        }
        with self.assertRaises(ValueError):
            analyze_document(doc)


if __name__ == "__main__":
    unittest.main()

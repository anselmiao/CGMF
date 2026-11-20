import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_deterministic_level_candidate import SCHEMA_VERSION, validate_manifest


def base_doc():
    return {
        "schema_version": SCHEMA_VERSION,
        "sources": [{"source_id": "ensdf", "reference": "https://example.org/ensdf", "version": "evaluation-1"}],
        "levels": [
            {"level_id": "136I-gs", "zaid": 53136, "Z": 53, "A": 136,
             "energy_MeV": 0.0, "energy_uncertainty_MeV": 0.0,
             "spin": "1", "parity": -1, "jpi_status": "ADOPTED_UNIQUE",
             "source_id": "ensdf", "decision": "CATALOG_ONLY", "decision_reason": "reference state"},
            {"level_id": "136I-m1", "zaid": 53136, "Z": 53, "A": 136,
             "energy_MeV": 0.201, "energy_uncertainty_MeV": 0.026,
             "spin": "6", "parity": -1, "jpi_status": "ADOPTED_UNIQUE",
             "source_id": "ensdf", "decision": "CATALOG_ONLY",
             "decision_reason": "isomer; above event-6 excitation; not a prompt bridge",
             "competing_decay": "BETA"}
        ]
    }


class DeterministicCandidateTests(unittest.TestCase):
    def test_catalog_only_i136_is_accepted_as_catalog_not_prompt(self):
        result = validate_manifest(base_doc())
        self.assertEqual(result["decision_report"]["accepted_prompt_level_ids"], [])
        self.assertEqual(result["decision_report"]["counts"]["CATALOG_ONLY"], 2)

    def test_unknown_jpi_cannot_be_prompt_included(self):
        doc = base_doc()
        doc["levels"][1].update(jpi_status="TENTATIVE", spin=None, parity=None, decision="PROMPT_INCLUDE")
        with self.assertRaisesRegex(ValueError, "cannot enter prompt scheme"):
            validate_manifest(doc)

    def test_beta_competing_level_cannot_enter_legacy_prompt_scheme(self):
        doc = base_doc()
        doc["levels"][1].update(decision="PROMPT_INCLUDE", competing_decay="BETA",
                                gamma_branches=[{"to_level_id": "136I-gs", "probability": 1.0,
                                                 "multipolarities": ["M5"]}])
        with self.assertRaisesRegex(ValueError, "competing beta/IT"):
            validate_manifest(doc)

    def test_forbidden_transition_is_rejected(self):
        doc = base_doc()
        doc["levels"][1].update(decision="PROMPT_INCLUDE", competing_decay="NONE",
                                gamma_branches=[{"to_level_id": "136I-gs", "probability": 1.0,
                                                 "multipolarities": ["E1"]}])
        with self.assertRaisesRegex(ValueError, "selection rules"):
            validate_manifest(doc)

    def test_valid_transition_passes_selection_rules(self):
        doc = base_doc()
        # 6- -> 1- permits M5 (same parity, |Delta J|=5).
        doc["levels"][1].update(decision="PROMPT_INCLUDE", competing_decay="NONE",
                                gamma_branches=[{"to_level_id": "136I-gs", "probability": 1.0,
                                                 "multipolarities": ["M5"]}])
        result = validate_manifest(doc)
        self.assertEqual(result["decision_report"]["accepted_prompt_level_ids"], ["136I-m1"])

    def test_branch_probabilities_must_sum_to_one(self):
        doc = base_doc()
        doc["levels"][1].update(gamma_branches=[{"to_level_id": "136I-gs", "probability": 0.8,
                                                 "multipolarities": ["M5"]}])
        with self.assertRaisesRegex(ValueError, "not 1"):
            validate_manifest(doc)

    def test_missing_destination_rejected(self):
        doc = base_doc()
        doc["levels"][1].update(gamma_branches=[{"to_level_id": "missing", "probability": 1.0,
                                                 "multipolarities": ["M5"]}])
        with self.assertRaisesRegex(ValueError, "lower level"):
            validate_manifest(doc)

    def test_duplicate_level_ids_rejected(self):
        doc = base_doc()
        doc["levels"][1]["level_id"] = doc["levels"][0]["level_id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_manifest(doc)

    def test_even_a_requires_integer_spin(self):
        doc = base_doc()
        doc["levels"][1]["spin"] = "11/2"
        with self.assertRaisesRegex(ValueError, "lattice mismatch"):
            validate_manifest(doc)

    def test_i132_ensdf_delayed_it_and_uncertain_29kev_line_are_not_prompt_branches(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "research/manifests/targeted-level-candidates-v0.1.json").read_text(encoding="utf-8"))
        isomer = next(x for x in manifest["levels"] if x["level_id"] == "132I-120keV-isomer")
        intermediate = next(x for x in manifest["levels"] if x["level_id"] == "132I-22keV-tentative")
        self.assertEqual(isomer["decision"], "CATALOG_ONLY")
        self.assertEqual(isomer["decay_channels"][0]["fraction"], 0.14)
        self.assertEqual(isomer["decay_channels"][1]["fraction"], 0.86)
        transition = isomer["observed_transitions"][0]
        self.assertEqual(transition["gamma_energy_keV"], 98.0)
        self.assertEqual(transition["multipolarity"], "E3")
        self.assertEqual(transition["total_internal_conversion_coefficient"], 21.6)
        uncertain = intermediate["observed_transitions"][0]
        self.assertEqual(uncertain["gamma_energy_keV"], 29.11)
        self.assertIsNone(uncertain["multipolarity"])
        self.assertIn("UNCERTAIN", uncertain["evidence_status"])
        result = validate_manifest(manifest)
        self.assertEqual(result["decision_report"]["accepted_prompt_level_ids"], [])

    def test_starter_manifest_cli_is_deterministic_and_catalog_only(self):
        root = Path(__file__).resolve().parents[1]
        manifest = root / "research/manifests/targeted-level-candidates-v0.1.json"
        script = root / "scripts/build_deterministic_level_candidate.py"
        with tempfile.TemporaryDirectory() as tmp:
            out1, report1 = Path(tmp) / "candidate1.json", Path(tmp) / "report1.json"
            out2, report2 = Path(tmp) / "candidate2.json", Path(tmp) / "report2.json"
            for output, report in ((out1, report1), (out2, report2)):
                import subprocess
                subprocess.run(
                    [sys.executable, str(script), "--manifest", str(manifest),
                     "--output", str(output), "--report", str(report)],
                    check=True, capture_output=True, text=True,
                )
            self.assertEqual(out1.read_bytes(), out2.read_bytes())
            self.assertEqual(report1.read_bytes(), report2.read_bytes())
            candidate = json.loads(out1.read_text(encoding="utf-8"))
            report = json.loads(report1.read_text(encoding="utf-8"))
            self.assertEqual(len(candidate["levels"]), 5)
            self.assertEqual(report["counts"]["CATALOG_ONLY"], 5)
            self.assertEqual(report["accepted_prompt_level_ids"], [])
            self.assertFalse(report["production_data_modified"])

    def test_complete_decay_channels_must_sum_to_one(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "research/manifests/targeted-level-candidates-v0.1.json").read_text(encoding="utf-8"))
        isomer = next(x for x in manifest["levels"] if x["level_id"] == "132I-120keV-isomer")
        isomer["decay_channels"][1]["fraction"] = 0.80
        with self.assertRaisesRegex(ValueError, "fractions must sum to 1"):
            validate_manifest(manifest)

    def test_observed_transition_energy_closure_is_checked_when_uncertainties_exist(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "research/manifests/targeted-level-candidates-v0.1.json").read_text(encoding="utf-8"))
        isomer = next(x for x in manifest["levels"] if x["level_id"] == "132I-120keV-isomer")
        isomer["observed_transitions"][0]["gamma_energy_keV"] = 300.0
        with self.assertRaisesRegex(ValueError, "energy closure failed"):
            validate_manifest(manifest)

    def test_required_internal_conversion_coefficient_cannot_be_missing(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "research/manifests/targeted-level-candidates-v0.1.json").read_text(encoding="utf-8"))
        isomer = next(x for x in manifest["levels"] if x["level_id"] == "132I-120keV-isomer")
        isomer["observed_transitions"][0]["total_internal_conversion_coefficient"] = None
        with self.assertRaisesRegex(ValueError, "coefficient is missing"):
            validate_manifest(manifest)

    def test_relative_photon_intensity_is_not_treated_as_total_decay_probability(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "research/manifests/targeted-level-candidates-v0.1.json").read_text(encoding="utf-8"))
        isomer = next(x for x in manifest["levels"] if x["level_id"] == "132I-120keV-isomer")
        self.assertEqual(isomer["observed_transitions"][0]["relative_photon_intensity"], 100)
        result = validate_manifest(manifest)
        self.assertEqual(result["decision_report"]["accepted_prompt_level_ids"], [])

    def test_i132_conditional_it_branch_is_blocked_without_complete_inventory(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "research/manifests/targeted-level-candidates-v0.1.json").read_text(encoding="utf-8"))
        result = validate_manifest(manifest)
        row = next(x for x in result["decision_report"]["decisions"] if x["level_id"] == "132I-120keV-isomer")
        derived = row["derived_decay_modes"]["ISOMERIC_TRANSITION"]
        self.assertEqual(derived["status"], "BLOCKED")
        self.assertIn("not certified complete", derived["reason"])

    def test_conditional_transition_and_icc_probabilities_are_derived_separately(self):
        doc = base_doc()
        doc["levels"].append({
            "level_id": "136I-exc", "zaid": 53136, "Z": 53, "A": 136,
            "energy_MeV": 0.05, "energy_uncertainty_MeV": 0.0,
            "spin": "2", "parity": -1, "jpi_status": "ADOPTED_UNIQUE",
            "source_id": "ensdf", "decision": "CATALOG_ONLY"
        })
        isomer = doc["levels"][1]
        isomer["decay_channels"] = [{
            "mode": "IT", "fraction": 0.86,
            "fraction_basis": "total_isomer_decay", "source_id": "ensdf"
        }]
        isomer["transition_sets"] = [{"mode": "IT", "complete": True,
                                      "intensity_basis": "relative_photon_intensity_within_decay_mode",
                                      "source_id": "ensdf"}]
        isomer["observed_transitions"] = [
            {"transition_id": "t1", "decay_mode_id": "IT", "initial_level_id": "136I-m1",
             "final_level_id": "136I-exc", "gamma_energy_keV": 151.0,
             "relative_photon_intensity": 100, "total_internal_conversion_coefficient": 1.0,
             "source_id": "ensdf"},
            {"transition_id": "t2", "decay_mode_id": "IT", "initial_level_id": "136I-m1",
             "final_level_id": "136I-gs", "gamma_energy_keV": 201.0,
             "relative_photon_intensity": 50, "total_internal_conversion_coefficient": 0.0,
             "source_id": "ensdf"}
        ]
        result = validate_manifest(doc)
        row = next(x for x in result["decision_report"]["decisions"] if x["level_id"] == "136I-m1")
        derived = row["derived_decay_modes"]["IT"]
        self.assertEqual(derived["status"], "DERIVED_CONDITIONAL")
        first, second = derived["transitions"]
        self.assertAlmostEqual(first["transition_probability_given_mode"], 0.8)
        self.assertAlmostEqual(first["gamma_probability_given_transition"], 0.5)
        self.assertAlmostEqual(first["conversion_probability_given_transition"], 0.5)
        self.assertAlmostEqual(first["total_isomer_decay_gamma_probability"], 0.86 * 0.8 * 0.5)
        self.assertAlmostEqual(first["total_isomer_decay_conversion_probability"], 0.86 * 0.8 * 0.5)
        self.assertAlmostEqual(second["transition_probability_given_mode"], 0.2)
        self.assertAlmostEqual(second["total_isomer_decay_gamma_probability"], 0.86 * 0.2)
        self.assertAlmostEqual(
            sum(x["total_isomer_decay_gamma_probability"] + x["total_isomer_decay_conversion_probability"] for x in derived["transitions"]),
            0.86
        )


if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_nuclide_spin_admission import classify_record, spin_lattice_status, read_records


def record(**overrides):
    row = {
        "nuclide": "105Zr", "A": "105", "J": "0.5", "parity": "+",
        "source_status": "NONEXPERIMENTAL",
        "source_ref": "RIPL-4:levels/z040.dat", "source_version": "RIPL-4-2026-05",
    }
    row.update(overrides)
    return row


class SpinLatticeTests(unittest.TestCase):
    def test_odd_a_requires_half_integer_spin(self):
        self.assertEqual(spin_lattice_status(105, 4.0), "INVALID_A_J_PARITY_MISMATCH")
        self.assertEqual(spin_lattice_status(105, 0.5), "VALID")

    def test_even_a_requires_integer_spin(self):
        self.assertEqual(spin_lattice_status(136, 0.5), "INVALID_A_J_PARITY_MISMATCH")
        self.assertEqual(spin_lattice_status(136, 1.0), "VALID")

    def test_non_quantized_spin_rejected(self):
        self.assertEqual(spin_lattice_status(105, 0.25),
                         "INVALID_NOT_INTEGER_OR_HALF_INTEGER")

    def test_105zr_nonexperimental_candidate_is_conditional(self):
        result = classify_record(record())
        self.assertEqual(result["spin_lattice"], "VALID")
        self.assertEqual(result["admission"], "CONDITIONAL")
        self.assertEqual(result["reason"], "NONFINAL_OR_NONEXPERIMENTAL_ASSIGNMENT")

    def test_89br_ambiguous_assignment_is_conditional(self):
        result = classify_record(record(
            nuclide="89Br", A="89", J="1.5", parity="-",
            source_status="AMBIGUOUS", source_ref="RIPL-4:levels/z035.dat"))
        self.assertEqual(result["admission"], "CONDITIONAL")
        self.assertEqual(result["reason"], "AMBIGUOUS_JPI_ASSIGNMENT")

    def test_wrong_legacy_ground_spin_is_rejected_even_if_source_claims_adopted(self):
        result = classify_record(record(J="4.0", source_status="ADOPTED_UNIQUE"))
        self.assertEqual(result["admission"], "REJECTED")

    def test_adopted_unique_requires_source_ref_and_version(self):
        result = classify_record(record(
            nuclide="136I", A="136", J="1", parity="+",
            source_status="ADOPTED_UNIQUE", source_ref="", source_version=""))
        self.assertEqual(result["admission"], "CONDITIONAL")

    def test_missing_j_is_not_silently_imputed(self):
        result = classify_record(record(J="", source_status="AMBIGUOUS"))
        self.assertEqual(result["admission"], "CONDITIONAL")
        self.assertEqual(result["spin_lattice"], "NOT_EVALUATED")

    def test_csv_schema_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("nuclide,A,J\n105Zr,105,0.5\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_records(path)


if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_discrete_level_quantum_numbers import audit_discrete_levels


def header(name, zaid, nlevels):
    return f"{name:<6}{zaid:6d}{nlevels:5d}"


def level(energy, spin, parity, ngamma=0):
    return f"{energy:10.6f}{spin:5.1f}{parity:3d}{0.0:13.5e}{ngamma:3d}"


class DiscreteLevelQuantumNumberAuditTests(unittest.TestCase):
    def run_audit(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "discreteLevels.dat"
            path.write_text(content, encoding="utf-8")
            return audit_discrete_levels(path)

    def test_even_mass_integer_spin_and_odd_mass_half_integer_spin_are_valid(self):
        content = "\n".join([
            header("10Be", 4010, 1), level(0.0, 0.0, 1),
            header("11B", 5011, 1), level(0.0, 1.5, -1),
            "",
        ])
        report = self.run_audit(content)
        self.assertEqual(report["counts"]["nuclei"], 2)
        self.assertEqual(report["counts"]["levels"], 2)
        self.assertEqual(report["counts"]["spin_lattice_violations"], 0)

    def test_odd_mass_integer_spin_is_reported(self):
        content = "\n".join([
            header("89Br", 35089, 1), level(0.0, 2.0, 1), "",
        ])
        report = self.run_audit(content)
        self.assertEqual(report["counts"]["spin_lattice_violations"], 1)
        item = report["spin_lattice_violations"][0]
        self.assertEqual(item["reason"], "ODD_A_INTEGER_J")
        self.assertTrue(item["is_ground_state"])

    def test_even_mass_half_integer_spin_is_reported(self):
        content = "\n".join([
            header("12C", 6012, 1), level(0.0, 0.5, 1), "",
        ])
        report = self.run_audit(content)
        self.assertEqual(report["spin_lattice_violations"][0]["reason"], "EVEN_A_HALF_INTEGER_J")

    def test_non_half_integral_spin_and_invalid_parity_are_separate_findings(self):
        content = "\n".join([
            header("89Br", 35089, 1), level(0.0, 0.25, 0), "",
        ])
        report = self.run_audit(content)
        self.assertEqual(report["counts"]["spin_lattice_violations"], 1)
        self.assertEqual(report["spin_lattice_violations"][0]["reason"], "J_NOT_INTEGER_OR_HALF_INTEGER")
        self.assertEqual(report["counts"]["invalid_parity_records"], 1)

    def test_gamma_branch_lines_are_skipped_using_fixed_width_gamma_count(self):
        branch = f"{0:3d}{1.0:9.3f}{0.0:10.3f}"
        content = "\n".join([
            header("10Be", 4010, 2),
            level(0.0, 0.0, 1),
            level(1.0, 2.0, 1, ngamma=1),
            branch,
            header("11B", 5011, 1), level(0.0, 1.5, -1), "",
        ])
        report = self.run_audit(content)
        self.assertEqual(report["counts"]["nuclei"], 2)
        self.assertEqual(report["counts"]["levels"], 3)
        self.assertEqual(report["counts"]["spin_lattice_violations"], 0)

    def test_negative_spin_is_counted_as_unassigned_not_as_lattice_failure(self):
        content = "\n".join([
            header("89Br", 35089, 1), level(0.0, -1.0, 0), "",
        ])
        report = self.run_audit(content)
        self.assertEqual(report["counts"]["missing_or_negative_spin"], 1)
        self.assertEqual(report["counts"]["spin_lattice_violations"], 0)


if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_i136_discrete_baseline import (
    EXPECTED_DISCRETE_SHA256,
    build_report,
    find_cgmf_i136,
    find_ripl_i136,
    sha256,
)


class I136BaselineAuditTests(unittest.TestCase):
    def test_ripl_fixed_width_fields_are_separated(self):
        header = "136I   136   53   11   19    1    1    3.780000    8.960000"
        levels_input = [f"{i:3d}   {0.1 * (i - 1):0.6f}   1.0 -1   8.34E+01  0" for i in range(1, 12)]
        levels_input[0] = levels_input[0].ljust(46) + "(1-)"
        line, counts, levels = find_ripl_i136([header] + levels_input)
        self.assertEqual(line, 1)
        self.assertEqual(counts, {"Nol": 11, "Nog": 19, "Nmax": 1, "Nc": 1})
        self.assertEqual(len(levels), 11)
        self.assertEqual(levels[0]["evaluated_Jpi_text"], "(1-)")

    def test_cgmf_i136_level_count_and_fields(self):
        line, ndisc, levels = find_cgmf_i136([
            "136I  53136   1",
            " 0.000000   1.0 -1  8.34000e+01  0",
        ])
        self.assertEqual((line, ndisc), (1, 1))
        self.assertEqual(levels[0]["spin"], 1.0)
        self.assertEqual(levels[0]["parity"], -1)

    def test_sha256_is_raw_byte_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_bytes(b"abc")
            self.assertEqual(
                sha256(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )

    def test_report_compares_the_frozen_i136_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cgmf = root / "discreteLevels.dat"
            ripl = root / "ripl3-levels.dat"
            cgmf.write_text(
                "136I  53136   1\n 0.000000   1.0 -1  8.34000e+01  0\n",
                encoding="utf-8",
            )
            ripl_levels = [f"{i:3d}   {0.1 * (i - 1):0.6f}   1.0 -1   8.34E+01  0" for i in range(1, 12)]
            ripl_levels[0] = ripl_levels[0].ljust(46) + "(1-)"
            ripl.write_text(
                "136I   136   53   11   19    1    1    3.780000    8.960000\\n"
                + "\\n".join(ripl_levels) + "\\n",
                encoding="utf-8",
            )            report = build_report(cgmf, ripl)
        self.assertEqual(report["records"]["CGMF"]["ndisc"], 1)
        self.assertEqual(report["records"]["RIPL3"]["counts"]["Nmax"], 1)
        self.assertTrue(report["checks"]["CGMF_ground_state_matches_RIPL_first_level"])
        self.assertFalse(report["files"][str(cgmf)]["matches_frozen_baseline"])


if __name__ == "__main__":
    unittest.main()

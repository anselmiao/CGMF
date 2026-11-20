import tempfile
import unittest
from pathlib import Path

from audit_nuclide_level_coverage import audit, parse_cgmf, parse_ripl


class ParserTests(unittest.TestCase):
    def test_ripl_header_fields_are_not_conflated(self):
        header = "136I   136   53   11   19    1    1    3.780000    8.960000"
        levels = [
            "  1   0.000000   1.0 -1   8.34E+01  0",
            "  2   0.086730  -1.0  0   4.00E-10  1",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ripl.dat"
            p.write_text("\n".join([header] + levels), encoding="utf-8")
            r = parse_ripl(p)["136I"]
        self.assertEqual((r.nol, r.nog, r.nmax, r.nc), (11, 19, 1, 1))
        self.assertEqual(len(r.levels), 2)

    def test_cgmf_record_and_nmax_classification(self):
        ripl_text = "\n".join([
            "105Zr  105   40    1    0    1    1    4.090000   14.740001",
            "  1   0.000000  -1.0  0   6.00E-01  0",
        ])
        cgmf_text = "\n".join([
            "105Zr  40105   1",
            " 0.000000   4.0  1  6.70000e-01  0",
        ])
        with tempfile.TemporaryDirectory() as tmp:
            rp, cp = Path(tmp)/"ripl.dat", Path(tmp)/"cgmf.dat"
            rp.write_text(ripl_text, encoding="utf-8")
            cp.write_text(cgmf_text, encoding="utf-8")
            rows = audit(parse_ripl(rp), parse_cgmf(cp), {"105Zr"})
        self.assertEqual(rows[0]["status"], "MATCHES_RIPL_NMAX_CUTOFF")
        self.assertEqual(rows[0]["RIPL_ground_J"], -1.0)
        self.assertEqual(rows[0]["CGMF_ground_J"], 4.0)


if __name__ == "__main__":
    unittest.main()

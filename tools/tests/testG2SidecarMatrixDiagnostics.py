#!/usr/bin/env python3
"""Regression tests for diagnostic-only log filtering in the G2 matrix harness."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runG2SidecarMatrix import stdout_without_diagnostics


class SidecarMatrixDiagnosticFilterTests(unittest.TestCase):
    def test_removes_only_known_diagnostic_records(self):
        raw = (
            b"ordinary simulation output\n"
            b"[CGMF DATA AUDIT PYTHON] sha256=abc\n"
            b"[G2 BIN SAMPLE] event_id=6 u=0.11\n"
            b"[MC bridge diagnostic] event_id=6 accepted=0\n"
            b"physical warning that must remain\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.stdout"
            path.write_bytes(raw)
            self.assertEqual(
                stdout_without_diagnostics(path),
                b"ordinary simulation output\nphysical warning that must remain\n",
            )
            self.assertEqual(path.read_bytes(), raw)

    def test_near_match_is_not_silently_removed(self):
        raw = b"[G2 BIN SAMPLE EXTRA] this is not a registered prefix\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.stdout"
            path.write_bytes(raw)
            self.assertEqual(stdout_without_diagnostics(path), raw)

    def test_empty_log(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.stdout"
            path.write_bytes(b"")
            self.assertEqual(stdout_without_diagnostics(path), b"")


if __name__ == "__main__":
    unittest.main()

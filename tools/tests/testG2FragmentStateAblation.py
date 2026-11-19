import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "analysis" / "g2FragmentStateAblation.py"
SPEC = importlib.util.spec_from_file_location("g2_fragment_state_ablation", MODULE)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def fragment(side, A_value, Z_value, momentum):
    return {
        "schema": A.SCHEMA, "run_id": "fixture-run", "event_id": 1, "fragment_side": side,
        "initial_fragment": {
            "A": A_value, "Z": Z_value, "parity_index": 1,
            "excitation_MeV": 5.0, "spin_stored": 3.0,
            "pre_fragment_momentum_MeV_c": momentum,
        },
        "transitions": [],
    }


class FragmentStateAblationTests(unittest.TestCase):
    def test_local_state_uses_only_intrinsic_fields(self):
        f = fragment("HF", 140, 54, [1.0, 2.0, 3.0])["initial_fragment"]
        self.assertEqual(A.local_state(f), [140.0, 54.0, 1.0, 5.0, 3.0])

    def test_read_split_requires_exact_rng_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lf = fragment("LF", 100, 40, [10.0, 0.0, 0.0])
            hf = fragment("HF", 140, 54, [-10.0, 0.0, 0.0])
            (root / "mixed-history.jsonl").write_text(
                json.dumps(lf) + "\n" + json.dumps(hf) + "\n", encoding="utf-8")
            (root / "rng-audit.tsv").write_text("event\tseed\n1\t701\n", encoding="utf-8")
            records, runs, seeds, _ = A.read_split([root / "mixed-history.jsonl"])
            self.assertEqual(len(records), 1)
            self.assertEqual(runs, {"fixture-run"})
            self.assertEqual(seeds, {701})
            self.assertEqual(len(records[0]["shared_kinematics"]), 6)
            (root / "rng-audit.tsv").write_text("event\tseed\n2\t701\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly match"):
                A.read_split([root / "mixed-history.jsonl"])

    def test_paired_bootstrap_is_reproducible_and_favors_lower_error(self):
        reference = {"_event_error2": [[float(i + k + 1) for k in range(4)] for i in range(30)]}
        candidate = {"_event_error2": [[v * 0.5 for v in row] for row in reference["_event_error2"]]}
        a = A.paired_bootstrap_delta(candidate, reference, n_boot=200, seed=17)
        b = A.paired_bootstrap_delta(candidate, reference, n_boot=200, seed=17)
        self.assertEqual(a, b)
        self.assertLess(a["delta_candidate_minus_reference"], 0)
        self.assertEqual(a["bootstrap_unit"], "held-out complete LF/HF event pair")

    def test_fit_predict_reports_all_four_hf_targets(self):
        train, test = [], []
        for i in range(40):
            train.append({"H_local": [float(i), 1.0, 1.0, float(i) / 4, 2.0],
                          "target": [float(i % 4), float(i) / 2, float(i % 3), float(i) / 3]})
        for i in range(20):
            test.append({"H_local": [float(i + 40), 1.0, 1.0, float(i + 40) / 4, 2.0],
                         "target": [float(i % 4), float(i + 40) / 2, float(i % 3), float(i + 40) / 3]})
        result = A.fit_predict(train, test, "H_local", ridge=1.0)
        self.assertEqual(set(result["targets"]), set(A.TARGETS))
        self.assertEqual(len(result["_event_error2"]), 20)


if __name__ == "__main__":
    unittest.main()

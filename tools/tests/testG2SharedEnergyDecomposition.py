import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "analysis" / "g2SharedEnergyDecomposition.py"
SPEC = importlib.util.spec_from_file_location("g2_shared_energy_decomposition", MODULE)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


class SharedEnergyDecompositionTests(unittest.TestCase):
    def test_pair_txe_and_local_nonenergy_features_are_separate(self):
        row = {
            "diagnostics": {"TXE_sum_initial_fragment_excitation_MeV": 17.5},
            "H_local": [140.0, 54.0, 1.0, 10.0, 4.0],
            "L_spin": [3.0], "L_parity": [-1.0],
            "L_excitation": [7.5], "L_intrinsic": [-1.0, 7.5, 3.0],
            "shared_kinematics": [1.0] * 6,
        }
        A.add_pair_txe([row])
        features = A.feature_builders(row)
        self.assertEqual(row["TXE_pair_sum"], [17.5])
        self.assertEqual(features["H+TXE+L_spin_parity"],
                         features["H+TXE_pair_sum"] + [3.0, -1.0])
        self.assertEqual(features["H+L_excitation_reference"],
                         row["H_local"] + [7.5])

    def test_schema_and_protocol_defaults(self):
        self.assertEqual(A.SCHEMA, "cgmf.g2.shared-energy-decomposition.v1")
        self.assertEqual(A.RIDGE, 1.0)
        self.assertEqual(A.BOOTSTRAP, 2000)
        self.assertEqual(A.BOOTSTRAP_SEED, 20261119)


if __name__ == "__main__":
    unittest.main()

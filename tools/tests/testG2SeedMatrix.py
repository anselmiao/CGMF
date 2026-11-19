#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path
P=Path(__file__).with_name("validateG2SeedMatrix.py")
S=importlib.util.spec_from_file_location("seed_matrix",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class SeedMatrixTests(unittest.TestCase):
 def test_rejects_overlap_for_same_condition(self):
  c=[{"name":"a","ZAID":94239,"energy_MeV":"2.53e-8","events":200},
     {"name":"b","ZAID":94239,"energy_MeV":"2.53e-8","seed_start":10,"events":40}]
  with self.assertRaisesRegex(ValueError,"overlaps"): M.validate_seed_ranges(c)
 def test_accepts_adjacent_nonoverlapping_ranges(self):
  c=[{"name":"a","ZAID":94239,"energy_MeV":"2.53e-8","events":200},
     {"name":"b","ZAID":94239,"energy_MeV":"2.53e-8","seed_start":201,"events":200},
     {"name":"c","ZAID":94239,"energy_MeV":"2.53e-8","seed_start":401,"events":200}]
  self.assertEqual(len(M.validate_seed_ranges(c)["94239@0.0000000253"]),3)
 def test_same_seed_different_energy_is_separate_condition(self):
  c=[{"name":"a","ZAID":94239,"energy_MeV":"2.53e-8","events":200},
     {"name":"b","ZAID":94239,"energy_MeV":"10.0","events":200}]
  self.assertEqual(len(M.validate_seed_ranges(c)),2)
 def test_energy_numeric_format_is_canonicalized(self):
  c=[{"name":"a","ZAID":94239,"energy_MeV":"2.53e-8","events":200},
     {"name":"b","ZAID":94239,"energy_MeV":"0.0000000253","seed_start":10,"events":40}]
  with self.assertRaisesRegex(ValueError,"overlaps"): M.validate_seed_ranges(c)
if __name__=="__main__": unittest.main()

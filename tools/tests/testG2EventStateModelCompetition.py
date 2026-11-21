#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE=Path(__file__).parents[1]/'analysis'/'g2EventStateModelCompetition.py'
SPEC=importlib.util.spec_from_file_location('g2_event_state',MODULE)
A=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(A)

def frag(eid,side,Aa,ex,p):
    return {'schema':A.SCHEMA,'run_id':'seed-x','event_id':eid,'fragment_side':side,
      'initial_fragment':{'A':Aa,'Z':40 if side=='LF' else 54,'parity_index':1 if side=='LF' else -1,
       'excitation_MeV':ex,'spin_stored':4.0,'pre_fragment_momentum_MeV_c':p},
      'transitions':[{'particle_type':'neutron','neutron_kinematics':{'energy_lab_MeV':1.5}},
                     {'particle_type':'gamma','energy_cm_MeV':0.5}]}

class EventStateTests(unittest.TestCase):
    def test_tx_e_tke_and_closure_are_derived(self):
        sides={'LF':frag(1,'LF',100,8.0,[3000,0,0]),'HF':frag(1,'HF',140,9.0,[-3000,0,0])}
        r=A.make_record(1,sides,'fixture','seed-x')
        self.assertAlmostEqual(r['diagnostics']['TXE_sum_initial_fragment_excitation_MeV'],17.0)
        self.assertAlmostEqual(r['diagnostics']['momentum_closure_MeV_c'],0.0)
        self.assertGreater(r['diagnostics']['TKE_nonrel_proxy_MeV'],0)
        self.assertEqual(r['target'],[1.0,1.5,1.0,0.5])

    def test_history_features_are_added_only_in_m3(self):
        sides={'LF':frag(1,'LF',100,8.0,[3000,0,0]),'HF':frag(1,'HF',140,9.0,[-3000,0,0])}
        r=A.make_record(1,sides,'fixture','seed-x')
        self.assertEqual(len(r['m2']),len(r['m1'])+1)
        self.assertEqual(len(r['m2']+r['lf_history']),len(r['m2'])+5)

    def test_paired_bootstrap_is_reproducible_and_event_based(self):
        a=[[float(i),float(i+1),float(i+2),float(i+3)] for i in range(30)]
        b=[[v*0.8 for v in row] for row in a]
        results={"M0":{"_event_normalized_squared_error_by_target":a},
                 "M1":{"_event_normalized_squared_error_by_target":a},
                 "M2":{"_event_normalized_squared_error_by_target":b},
                 "M3":{"_event_normalized_squared_error_by_target":a}}
        x=A.paired_bootstrap_deltas(results,[("M1","M0"),("M2","M1"),("M3","M2")],n_boot=100,seed=11)
        y=A.paired_bootstrap_deltas(results,[("M1","M0"),("M2","M1"),("M3","M2")],n_boot=100,seed=11)
        self.assertEqual(x,y)
        self.assertEqual(x["M2_vs_M1"]["bootstrap_unit"],"held-out complete LF/HF event pair")
        self.assertLess(x["M2_vs_M1"]["delta_mean_train_SD_normalized_RMSE"],0)

    def test_train_test_run_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError,'run_id overlap'):
            A.validate_disjoint_runs({'seed-x'},{'seed-x'})
        A.validate_disjoint_runs({'seed-a'},{'seed-b'})

    def test_rng_seed_overlap_rejected_even_with_different_run_ids(self):
        with self.assertRaisesRegex(ValueError,'RNG seed overlap'):
            A.validate_disjoint_seed_sets({1,2,3},{3,4})
        A.validate_disjoint_seed_sets({1,2},{3,4})


    def test_seed_audit_required_and_exact(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td); f=d/'mixed-history.jsonl'; f.write_text('{}\n')
            with self.assertRaisesRegex(ValueError,'missing sibling rng-audit'):
                A.read_seed_audit(f,{1})
            (d/'rng-audit.tsv').write_text('event\tseed\tfoo\n1\t401\tx\n')
            self.assertEqual(A.read_seed_audit(f,{1}),{401})
            with self.assertRaisesRegex(ValueError,'exactly match'):
                A.read_seed_audit(f,{1,2})

    def test_seed_ranges_are_compressed(self):
        self.assertEqual(A.contiguous_ranges({1,2,3,8,10,11}),[[1,3],[8,8],[10,11]])

if __name__=='__main__': unittest.main()

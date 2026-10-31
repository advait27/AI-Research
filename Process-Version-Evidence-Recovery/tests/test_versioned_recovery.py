import sys
import unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from versioned_recovery import (Claim,Evidence,State,World,Environment,endorsement_allowed,
    posterior,available,transition,run)


class VersionedRecoveryChecks(unittest.TestCase):
    def evidence(self):
        return Evidence(Claim('A',1),1,0,120,50,800,.04,True,True)

    def test_good_outcome_does_not_authorize_another_process_version(self):
        e=self.evidence()
        self.assertTrue(endorsement_allowed(Claim('A',1),e,1,0))
        self.assertFalse(endorsement_allowed(Claim('A',0),e,1,0))
        self.assertTrue(endorsement_allowed(Claim('A',0),e,1,0,version_guard=False))

    def test_all_target_fields_are_checked(self):
        e=self.evidence()
        for claim in [replace(e.claim,line='B'),replace(e.claim,comparator_version=1),
                      replace(e.claim,outcome='different_defect'),replace(e.claim,population='later_period'),
                      replace(e.claim,minimum=.02)]:
            self.assertFalse(endorsement_allowed(claim,e,1,0))

    def test_stale_observation_versions_are_rejected(self):
        e=self.evidence()
        self.assertFalse(endorsement_allowed(e.claim,e,2,0))
        self.assertFalse(endorsement_allowed(e.claim,e,1,1))

    def test_repair_cannot_certify_its_own_success(self):
        s=State(.8,.1,True,True,0,40)
        after=transition(s,2)
        self.assertFalse(after.gs)
        self.assertTrue(after.gl)
        self.assertNotIn(5,list(available(after)))
        self.assertIn(4,list(available(after)))
        self.assertAlmostEqual(after.ps,.12)

    def test_noisy_negative_screen_does_not_mean_zero_fault_probability(self):
        self.assertAlmostEqual(posterior(.5,True,.8,.9),2/11)
        self.assertGreater(posterior(.5,True,.8,.9),0)

    def test_calibration_changes_target_but_label_repair_does_not(self):
        env=Environment(World(31,True,True,True,.04),40)
        s=env.start();c=env.claim()
        s=env.act(s,'repair_labels')
        self.assertEqual(c,env.claim())
        s=env.act(s,'calibrate_sensor')
        self.assertNotEqual(c,env.claim())
        self.assertTrue(env.independent_line_b)

    def test_guard_ablation_has_identical_actions_and_pilot_data(self):
        w=World(20271031,True,True,False,.04)
        aware,a=run(w,40,'decision_loss')
        blind,b=run(w,40,'decision_loss_no_version')
        self.assertEqual(a[:-1],b[:-1])
        self.assertEqual(aware['cost'],blind['cost'])
        self.assertEqual(aware['n'],blind['n'])
        self.assertEqual(aware['accepted'],blind['accepted'])
        self.assertEqual(aware['wrong_version'],0)

    def test_every_policy_respects_tight_budget(self):
        for policy in ['stop','screen_targeted','full_revalidation','cheapest','information_gain','decision_loss']:
            r,_=run(World(42,True,True,False,.04),16,policy)
            self.assertLessEqual(r['cost'],16)
            self.assertEqual(r['line_b_preserved'],1)


if __name__=='__main__':unittest.main()

class AdditionalAuditChecks(unittest.TestCase):
    def test_independent_claim_survives_local_invalidation(self):
        env=Environment(World(40,True,False,False,.04),40)
        env.claim_validity['A']=True
        env.invalidate_claim('A')
        self.assertFalse(env.claim_validity['A'])
        self.assertTrue(env.claim_validity['B'])

    def test_reference_auditor_detects_wrong_version(self):
        from audit_versioned import audit
        w=World(20271031,True,True,False,.04)
        for policy in ['full_revalidation','full_revalidation_no_version','decision_loss']:
            row,trace=run(w,40,policy)
            result=audit(w,trace)
            for k,v in result.items():self.assertEqual(row[k],v)

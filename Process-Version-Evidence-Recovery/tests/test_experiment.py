import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from experiment import Environment, Ledger, World, run_policy, effect_bounds


class ExperimentChecks(unittest.TestCase):
    def test_invalidation_preserves_independent_branch(self):
        ledger = Ledger()
        affected = ledger.invalidate("measurement")
        self.assertIn("control_plan", affected)
        self.assertTrue(ledger.valid["labels"])
        with self.assertRaises(ValueError):
            ledger.restore("improvement_claim")
        ledger.restore("measurement")
        self.assertFalse(ledger.valid["control_plan"])

    def test_targeted_and_full_have_identical_repaired_trial_outcomes(self):
        for flags in [(False, False, False), (True, False, False), (False, True, False), (True, True, True)]:
            w = World(42, *flags, 0.04)
            full = run_policy(Environment(w), "full_revalidation")
            targeted = run_policy(Environment(w), "targeted_recovery")
            self.assertEqual(full["lower_bound"], targeted["lower_bound"])
            self.assertEqual(full["claimed"], targeted["claimed"])
            self.assertLessEqual(targeted["cost"], full["cost"])

    def test_insufficient_budget_never_partially_deploys(self):
        env = Environment(World(42, True, True, True, 0.04))
        result = run_policy(env, "targeted_recovery", budget=10)
        self.assertEqual(result["reason"], "budget_exhausted")
        self.assertEqual(result["claimed"], 0)
        self.assertFalse(env.sensor_fixed)
        self.assertFalse(env.labels_fixed)

    def test_confounding_cannot_change_randomized_evidence(self):
        clean = run_policy(Environment(World(4, False, False, False, 0)), "targeted_recovery")
        confounded = run_policy(Environment(World(4, False, False, True, 0)), "targeted_recovery")
        self.assertEqual(clean["lower_bound"], confounded["lower_bound"])

    def test_equal_arms_do_not_support_positive_effect(self):
        lo, hi = effect_bounds(80, 80, 800)
        self.assertLess(lo, 0)
        self.assertGreater(hi, 0)

    def test_later_drift_revokes_accepted_claim(self):
        env = Environment(World(42, False, False, False, 0.09))
        result = run_policy(env, "targeted_recovery")
        self.assertEqual(result["claimed"], 1)
        self.assertTrue(env.ledger.valid["improvement_claim"])
        env.ledger.invalidate("measurement")
        self.assertFalse(env.ledger.valid["improvement_claim"])
        self.assertFalse(env.ledger.valid["control_plan"])


if __name__ == "__main__":
    unittest.main()

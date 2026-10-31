"""A transparent, standard-library-only pilot benchmark; no LLM or plant data."""
import argparse
import csv
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class World:
    seed: int
    sensor_drift: bool
    label_error: bool
    confounding: bool
    benefit: float  # Hidden simulator parameter; never passed to a policy.
    baseline: float = 0.12


PARENTS = {
    "measurement": [],
    "labels": [],
    "cause": ["measurement", "labels"],
    "effect": ["cause"],
    "improvement_claim": ["effect"],
    "control_plan": ["improvement_claim"],
}


class Ledger:
    def __init__(self):
        self.valid = {name: True for name in PARENTS}

    def invalidate(self, source):
        """Revoke a claim and every descendant, retaining independent evidence."""
        affected = {source}
        changed = True
        while changed:
            changed = False
            for node, parents in PARENTS.items():
                if node not in affected and any(p in affected for p in parents):
                    affected.add(node)
                    changed = True
        for node in affected:
            self.valid[node] = False
        return sorted(affected)

    def restore(self, node):
        if not all(self.valid[p] for p in PARENTS[node]):
            raise ValueError("Cannot restore a claim with invalid prerequisites")
        self.valid[node] = True


def rng_for(seed, channel):
    digest = hashlib.sha256((str(seed) + ":" + channel).encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def count_defects(seed, channel, probability, n):
    rng = rng_for(seed, channel)
    probability = min(0.99, max(0.001, probability))
    return sum(rng.random() < probability for _ in range(n))


def wilson(k, n, z=1.959963984540054):
    """Wilson interval; finite-sample coverage is approximate, not guaranteed."""
    p = k / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return center - margin, center + margin


def effect_bounds(control, treatment, n):
    # Subtract separate arm bounds: deliberately conservative, fixed sample only.
    clo, chi = wilson(control, n)
    tlo, thi = wilson(treatment, n)
    return clo - thi, chi - tlo


class Environment:
    """Only this class can see hidden truth. Policy sees diagnostics and trials."""
    def __init__(self, world):
        self._world = world
        self.sensor_fixed = False
        self.labels_fixed = False
        self.cost = 0.0
        self.trace = []
        self.ledger = Ledger()

    def diagnostics(self):
        # V0 intentionally supplies perfect fault flags; noisy checks are future work.
        w = self._world
        observed = {
            "measurement_valid": not w.sensor_drift,
            "labels_valid": not w.label_error,
            "historical_comparison_valid": not w.confounding,
        }
        self.cost += 1.0
        # Every evaluation must earn a fresh improvement claim.
        self.ledger.invalidate("improvement_claim")
        for flag, node in [("measurement_valid", "measurement"),
                           ("labels_valid", "labels"),
                           ("historical_comparison_valid", "cause")]:
            if not observed[flag]:
                affected = self.ledger.invalidate(node)
                self.trace.append({"event": "invalidate", "source": node, "affected": affected})
        return observed

    def repair(self, action):
        if action == "calibrate_sensor":
            self.sensor_fixed = True
            self.cost += 4.0
            self.ledger.restore("measurement")
        elif action == "audit_labels":
            self.labels_fixed = True
            self.cost += 6.0
            self.ledger.restore("labels")
        else:
            raise ValueError(action)
        self.trace.append({"event": action})

    def historical(self, n):
        w = self._world
        control = count_defects(w.seed, "historical_control", w.baseline, n)
        apparent_benefit = w.benefit - (0.06 if w.sensor_drift else 0)
        apparent_benefit += 0.07 if w.confounding else 0
        apparent_benefit += 0.05 if w.label_error else 0
        treatment = count_defects(w.seed, "historical_treatment", w.baseline - apparent_benefit, n)
        # Historical records are already available; no new sampling cost.
        return control, treatment

    def randomized_pilot(self, n):
        w = self._world
        physical_benefit = w.benefit - (0.06 if w.sensor_drift and not self.sensor_fixed else 0)
        measured_benefit = physical_benefit + (0.05 if w.label_error and not self.labels_fixed else 0)
        control = count_defects(w.seed, "pilot_control", w.baseline, n)
        treatment = count_defects(w.seed, "pilot_treatment", w.baseline - measured_benefit, n)
        self.cost += 0.01 * (2 * n)
        # A randomized, correctly measured pilot supplies a new causal contrast.
        self.ledger.restore("cause")
        self.ledger.restore("effect")
        self.trace.append({"event": "randomized_pilot", "n_per_arm": n,
                           "control_defects": control, "treatment_defects": treatment})
        return control, treatment

    def score(self, claimed, minimum):
        # Ground truth is used only AFTER the policy has made its decision.
        w = self._world
        deployed_benefit = w.benefit - (0.06 if w.sensor_drift and not self.sensor_fixed else 0)
        return {
            "false_claim": int(claimed and deployed_benefit <= minimum),
            "true_claim": int(claimed and deployed_benefit > minimum),
            "missed_opportunity": int(w.benefit > minimum and not (claimed and deployed_benefit > minimum)),
            "deployed_risk_reduction": deployed_benefit if claimed else 0.0,
        }


def run_policy(env, policy, n=800, minimum=0.01, budget=30.0):
    """Policies receive an observation/action interface, never a World object."""
    diagnostics = env.diagnostics()
    reason = "insufficient_evidence"
    claimed = False
    lower = upper = None
    if policy == "historical":
        control, treatment = env.historical(n)
        lower, upper = effect_bounds(control, treatment, n)
        claimed = lower > minimum
        reason = "historical_comparison"
    elif policy == "stop" and not all(diagnostics.values()):
        reason = "failed_prerequisite"
    else:
        if policy == "full_revalidation":
            actions = ["calibrate_sensor", "audit_labels"]
        elif policy == "targeted_recovery":
            # Cheapest applicable repair first. This is a rule, not learned planning.
            actions = []
            if not diagnostics["measurement_valid"]:
                actions.append("calibrate_sensor")
            if not diagnostics["labels_valid"]:
                actions.append("audit_labels")
        elif policy == "stop":
            actions = []
        else:
            raise ValueError(policy)
        prices = {"calibrate_sensor": 4.0, "audit_labels": 6.0}
        total_cost = env.cost + sum(prices[a] for a in actions) + 0.02 * n
        if total_cost > budget:
            reason = "budget_exhausted"
        else:
            for action in actions:
                env.repair(action)
            control, treatment = env.randomized_pilot(n)
            lower, upper = effect_bounds(control, treatment, n)
            claimed = lower > minimum
            if claimed:
                env.ledger.restore("improvement_claim")
                env.ledger.restore("control_plan")
            reason = "randomized_confirmation"
    return {"policy": policy, "claimed": int(claimed), "cost": env.cost,
            "lower_bound": lower, "upper_bound": upper, "reason": reason,
            **env.score(claimed, minimum)}


FAULTS = {
    "clean": (False, False, False),
    "sensor_drift": (True, False, False),
    "label_error": (False, True, False),
    "confounding": (False, False, True),
    "combined": (True, True, True),
}
POLICIES = ["historical", "stop", "full_revalidation", "targeted_recovery"]


def summarize(rows):
    result = []
    for policy in POLICIES:
        selected = [r for r in rows if r["policy"] == policy]
        claims = sum(r["claimed"] for r in selected)
        result.append({
            "policy": policy, "cases": len(selected), "claims": claims,
            "false_claims": sum(r["false_claim"] for r in selected),
            "false_claim_fraction_of_claims": sum(r["false_claim"] for r in selected) / claims if claims else None,
            "true_claims": sum(r["true_claim"] for r in selected),
            "missed_opportunities": sum(r["missed_opportunity"] for r in selected),
            "mean_cost": sum(r["cost"] for r in selected) / len(selected),
            "mean_deployed_risk_reduction": sum(r["deployed_risk_reduction"] for r in selected) / len(selected),
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261027)
    parser.add_argument("--n", type=int, default=800)
    parser.add_argument("--budget", type=float, default=30.0)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    args = parser.parse_args()
    if args.repetitions < 1 or args.n < 1:
        parser.error("repetitions and n must be positive")
    args.out.mkdir(parents=True, exist_ok=True)
    rows, example = [], None
    for fault_name, flags in FAULTS.items():
        for effect_id, benefit in enumerate([0.04, 0.0, -0.02]):
            for rep in range(args.repetitions):
                # Same worlds and random streams across policies; no policy seed advantage.
                seed = args.seed + effect_id * args.repetitions + rep
                world = World(seed, *flags, benefit)
                for policy in POLICIES:
                    env = Environment(world)
                    row = run_policy(env, policy, n=args.n, budget=args.budget)
                    rows.append({"fault": fault_name, "true_benefit_after_repair": benefit,
                                 "seed": seed, **row})
                    if fault_name == "combined" and benefit == 0.04 and rep == 0 and policy == "targeted_recovery":
                        example = {"result": rows[-1], "trace": env.trace, "ledger": env.ledger.valid}
    summary = summarize(rows)
    with (args.out / "trials.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    payload = {"configuration": {**vars(args), "out": str(args.out), "minimum_benefit": 0.01},
               "summary": summary, "by_fault": {name: summarize([r for r in rows if r["fault"] == name]) for name in FAULTS}}
    (args.out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    (args.out / "example_trace.json").write_text(json.dumps(example, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

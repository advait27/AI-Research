# Research protocol v0.1

Date: 27 October 2026. This protocol was written during the first pilot campaign, after its initial results were visible. It is not a preregistration. Freeze the next protocol and held-out seeds before running the next evaluation.

## Question and candidate contribution

When manufacturing evidence becomes unreliable, can a DMAIC assistant select an affordable recovery experiment, update dependent conclusions, and regain valid decisions with less cost than full revalidation?

The candidate contribution is **budgeted recovery experiment selection under uncertain evidence validity**. Neither applying AI to DMAIC nor invalidating stale evidence is claimed as new. Universal novelty is unverified.

## Closest verified sources

| Work | Established overlap | Implication for this project |
|---|---|---|
| [DMAIC-IAD, arXiv:2606.04599v1](https://arxiv.org/html/2606.04599v1) | DMAIC-organized agents, standardized procedures, strategy generation, and an execution-free judge. Its limitations describe a static framework without continuous self-evolution. | A new DMAIC agent architecture alone is insufficient. Test recovery after evidence changes. |
| [DMAIC-Bench, arXiv:2610.32305](https://arxiv.org/html/2610.32305) | Evidence-dependent routing, prerequisite guards, paired go/no-go tasks, and evaluation of stopping behavior. | Stopping when evidence fails already has direct prior work. Add active recovery choices and resource tradeoffs. |
| [Hinov, Evidence-Grounded Runtime Assurance, 2026](https://www.mdpi.com/2673-4117/7/10/495) | Constraint-local evidence requirements, stale-evidence invalidation, structured revision, and replacement records in power-electronics design. | A dependency ledger and evidence replacement are infrastructure, not the novelty claim. The paper distinguishes checked replacement fixtures from optimizer-selected remedies and physical repairs. |

These sources were read for methodological overlap. This is a targeted novelty map, not a systematic review. Before a publication claim, expand to active experimental design, Bayesian decision theory, value-of-information planning, truth-maintenance systems, measurement-system analysis, sequential testing, and process control.

## DMAIC mapping

- **Define:** defect risk, process setting, required minimum improvement, permitted action budget.
- **Measure:** sensor calibration and inspection-label validity.
- **Analyze:** identify invalid evidence and the claims depending on it.
- **Improve:** repair measurement or labels, then conduct a randomized confirmation trial.
- **Control:** preserve a traceable claim and revoke it if a prerequisite changes. V0 tests revocation as a software behavior only; it does not simulate long-term operating trajectories.

## V0 environment

Baseline defect probability is 0.12. Fully repaired treatment effects are absolute risk reductions of 0.04, 0.00, or -0.02. A positive effect is beneficial. Defects are independent Bernoulli draws within each arm.

Five settings are equally represented: clean, sensor drift, label error, confounding, and all three together. Sensor drift reduces actual treatment benefit by 0.06 until calibration. Biased inspection creates an apparent benefit of 0.05 until audit; historical confounding creates an apparent benefit of 0.07 that disappears under randomization. Probabilities are clipped to [0.001, 0.99]. These mechanisms are deliberately simplified, not calibrated to a real factory.

Diagnostics expose fault status exactly. The policy receives diagnostic flags and trial results, not the latent benefit or simulated outcome score. The environment scores the policy only after its decision. The Python interface is a logical separation, not a security sandbox.

Available actions: diagnostics cost 1; calibration costs 4; label audit costs 6; sampling costs 0.01 per observation. The default randomized trial has 800 observations per arm and costs 16. The total budget is 30. Repairs are perfect, immediate, and persistent in v0.

The evidence graph contains measurement and labels → cause → effect → improvement claim → control plan. Descendants are invalidated when a prerequisite fails. Repairing a prerequisite does not automatically restore downstream conclusions. Fresh randomized evidence is required to restore the effect chain.

## Comparison policies

1. **Historical:** receives the same diagnostic information but ignores failures and evaluates existing before/after records. This deliberately weak baseline illustrates the failure mode, not current best practice.
2. **Stop:** stops if any prerequisite fails; otherwise conducts randomized confirmation.
3. **Full revalidation:** recalibrates, audits labels, and conducts randomized confirmation for every case.
4. **Targeted recovery:** repairs only failed measurement and label prerequisites, then conducts randomized confirmation. Confounding is resolved by randomization.

Targeted recovery currently sorts predetermined repairs by cost. There are no competing remedies for a given fault. Matching full revalidation's decisions at lower cost is therefore largely built into v0 and is not evidence of an intelligent planner.

## Decision rule and endpoints

Accept improvement only if the lower bound on absolute defect-risk reduction exceeds 0.01. Compute each arm's Wilson interval with z = 1.959963984540054 and subtract the treatment upper bound from the control lower bound. This is a conservative approximate bound, not an exact finite-sample or anytime-valid guarantee. Each policy has one fixed-sample decision per case; do not repeatedly inspect these bounds to decide when to stop sampling.

Primary v0 endpoints:

- False improvement claims: accepted interventions whose true deployed risk reduction is at most 0.01.
- False-claim fraction: false claims divided by accepted claims, with null if no claims.
- Valid positive claims and missed recoverable opportunities.
- Mean action cost, including diagnostics and sampling.
- Mean actual risk reduction across all scenarios, assigning zero when an intervention is not accepted.

The last endpoint is computed from known simulator probabilities, not an independently observed follow-up cohort. Recovery latency, actual downtime, and long-term control stability are not measured in v0.

## Experimental design and interpretation

Each policy runs on identical worlds. Seeds are reused across fault settings to reduce comparison noise. There are 1,500 scenario instances but only 300 base seed/effect pairs, and observations across policies/settings are paired. Do not treat all rows as independent replications or use unpaired significance tests. No confirmatory significance claim is made from this exploratory pilot.

Equal scenario weights and large injected artifacts favor exposing unreliable historical claims. Report per-fault outcomes, not just pooled rates. A zero observed false-claim count is not a guarantee of safety or a Six Sigma defect-rate demonstration.

## Next milestone: make recovery a real decision problem

Implement noisy tests and multiple alternative actions: a cheap calibration check, a full gauge repeatability/reproducibility study, a blinded label audit of selectable size, and randomized pilots of selectable size. Include cases where the cheap test is misleading, where different fault combinations explain the same data, and where full revalidation is rational.

Represent a belief over fault states. For action a, estimate expected downstream decision loss plus action cost, updating that belief from new observations. Compare a greedy expected-information-gain rule, a cost-sensitive decision-loss rule, a random feasible action policy, and full revalidation. An oracle with simulator truth may be used only as a separately labeled upper bound.

Test the hypothesis: **under a matched resource budget, a recovery planner yields more defensible beneficial deployments than stop-only behavior, with lower cost than full revalidation at comparable false-claim risk.** Treat this as an untested hypothesis.

Freeze held-out seeds and fault severities before the next campaign. Sweep noise, effect size, fault prevalence, repair failure probability, costs, and budgets. Use paired uncertainty estimates clustered by base scenario seed. Keep model development and held-out evaluation separate.

Then add an LLM policy that sees only the same observation/action interface. Require structured action choices and machine-checked evidence prerequisites. Compare against the rule-based and cost-sensitive planners using the same trials, budget accounting, and model-call costs. Record model/version, prompts, raw responses, failures, and all action traces.

After that, introduce recurring sensor drift, delayed defect labels, and post-deployment control-chart events. Real manufacturing data and expert review are required before making practical industrial claims.

## Deliverable acceptance for the next milestone

- The planner faces at least two plausible recovery actions for the same observed failure.
- Diagnostics and repairs can fail; hidden truth remains unavailable to policies.
- A blocked recovery respects its budget and cannot reuse invalidated claims.
- Claims have timestamped supporting observations and explicit validity prerequisites.
- Evaluation reports false claims alongside power, cost, and actual process outcomes.
- Performance advantage is tested rather than structurally guaranteed by action definitions.

# Initial experiment: what works and what remains untested

Run date: 27 October 2026. These are exploratory simulator results, not evidence of industrial effectiveness or established novelty.

## Main run

The experiment used 1,500 scenario instances and evaluated four policies on each, for 6,000 policy evaluations. Each randomized pilot used 800 observations per arm. There were 500 scenarios in which a beneficial intervention was recoverable. Cost is measured in arbitrary simulation units.

| Policy | Accepted improvement claims | False claims | Valid positive claims | Missed recoverable improvements | Mean cost |
|---|---:|---:|---:|---:|---:|
| Historical comparison, ignoring failed diagnostics | 639 | 419 | 220 | 280 | 1.0 |
| Stop when a prerequisite fails | 25 | 0 | 25 | 475 | 4.2 |
| Full revalidation | 125 | 0 | 125 | 375 | 27.0 |
| Targeted recovery | 125 | 0 | 125 | 375 | 21.0 |

Targeted recovery and full revalidation produced identical confirmation bounds and acceptance decisions. Targeted recovery used 22.2% less mean cost: (27 − 21) / 27. They both confirmed only 25% of the 500 recoverable improvements. Zero observed false claims does not establish zero risk.

The poor historical baseline shows how injected confounding and inspection bias can produce unsupported improvement claims. It is deliberately weak; the 65.6% false-claim fraction among its accepted claims is not an estimate of any real organization's error rate.

## Sample-size sensitivity

Because the main run recovered few beneficial interventions, two additional runs varied trial size. Both use a budget of 60 to avoid conflating larger samples with budget refusal. The main run's budget of 30 was also nonbinding at its sample size. All scenarios and seed assignments otherwise match.

| Observations per arm | Targeted recovery: valid positive claims / 500 | Full revalidation: valid positive claims / 500 | Targeted mean cost | Full mean cost |
|---|---:|---:|---:|---:|
| 400 | 40 / 500 (8%) | 40 / 500 (8%) | 13 | 19 |
| 800 | 125 / 500 (25%) | 125 / 500 (25%) | 21 | 27 |
| 1,600 | 260 / 500 (52%) | 260 / 500 (52%) | 37 | 43 |

No false claims occurred for either recovery policy in these runs. The conservative evidence rule has low power at the smaller sample sizes. Increasing samples improves recovery but raises cost. This motivates making sample size a recovery decision rather than fixing it in advance. These results do not validate sequential stopping; the current intervals support one fixed-sample decision only.

## Meaning and limitations

The baseline software behaves as intended: it revokes dependent claims, respects budgets, repairs failed prerequisites, and preserves independent evidence. Six behavioral checks pass, including a post-acceptance invalidation test and a comparison showing that historical confounding does not change randomized evidence.

The apparent cost advantage is largely structural. Diagnostics are perfect, each failure has a known perfect repair, and full revalidation deliberately repeats unnecessary checks. No learned decision-making is involved. We have demonstrated a reproducible test harness and baseline, not the proposed intelligent recovery planner.

Fault mechanisms are stylized probability shifts. Costs, effect sizes, and fault frequencies are hand chosen. Seeds are shared across policies and fault settings; rows are not independent observations. No confidence interval for the policy comparison, independent validation dataset, plant experiment, or LLM evaluation has been produced. The process-outcome metric comes from simulator probabilities, not an observed follow-up cohort. Continuous drift and delayed defects remain future extensions.

## Next research test

Introduce noisy diagnostics and competing repair/experiment options. Freeze held-out seeds before evaluation. Then test whether a planner that chooses actions by expected downstream decision loss and cost outperforms the present rules at matched budgets, without increasing false improvement claims.

## Reproducibility files

- Main run: [configuration and summary](../results/summary.json), [individual results](../results/trials.csv), [recovery trace](../results/example_trace.json).
- Smaller pilot: [summary](../results/sensitivity_n400/summary.json).
- Larger pilot: [summary](../results/sensitivity_n1600/summary.json).
- [Source](../src/experiment.py), [tests](../tests/test_experiment.py), and [research protocol](PROTOCOL.md).

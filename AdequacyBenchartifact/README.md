# AdequacyBench

Reference implementation and benchmark for the paper
"What Agent Traces Cannot Tell You: Evidentiary Adequacy of Runtime Records
for Agentic AI Oversight" (HICSS-61 submission).

## What this measures

Whether an agent runtime record can answer a legally operative determination.
A record answers only if it carries both a typing that maps events to the
legally operative category and the relation the determination depends on.
Coverage is whether the record can answer; soundness is whether the answer is
right. The two come apart, which is the point of the paper.

## Reproduce

    python3 -m adqbench.run          # writes results/results.json
    python3 figure.py                # writes fig1.png
    node paper.js                    # writes the manuscript

Requires Python 3 with scipy and matplotlib, and Node with the docx package.
Runtime is about 30 seconds.

Everything except the record-construction timing is deterministic under the
fixed seed (20260820) and reproduces byte for byte. Timing varies by a few
percent between runs, which is why it is reported in prose as a range rather
than tabulated.

## Layout

    adqbench/model.py      labelled values, capabilities, events, trajectories
    adqbench/generate.py   six determination families with adversarial decoys
    adqbench/emit.py       four record conditions: BARE, OTEL, GUARD, TYPED
    adqbench/resolve.py    conservative and heuristic resolvers
    adqbench/run.py        experiment driver, statistics, oracle control
    results/results.json   every number reported in the paper
    figure.py              Figure 1
    paper.js               manuscript generator

## Design invariants worth preserving if you extend this

1. Resolvability is decided from the record alone. A resolver must never read
   ground truth to decide whether it can answer. Violating this makes coverage
   meaningless.
2. Each emitter writes only what that class of instrumentation can honestly
   know. The baselines are modelled from published descriptions, deliberately
   generously where there was doubt.
3. Ground truth is known by construction, never adjudicated after the fact.
   This is the reason the corpus is generated rather than collected.
4. The heuristic resolver is a stipulated model of practitioner inference, not
   measured human behaviour. Any claim about what auditors actually conclude
   needs the expert panel, which has not been run.

## Determination families

    D1  Did protected data cross an external boundary?
    D2  Could a human have intervened before the effecting action?
    D3  Did the information barrier hold?
    D4  Was delegated authority valid at the moment of use?
    D5  Was a denied action later achieved by another path?
    D6  Which principal authorised the effecting call?

## Headline result

Coverage of resolvable determinations, pooled over 1,200 trajectories:
BARE 0.1633, OTEL 0.1633, GUARD 0.2875, TYPED 1.0000.
OTEL and BARE are identical on every trajectory.

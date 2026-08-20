# AI Research

> Open research on **Forward Deployed Engineering**, **AI Engineering**, **Enterprise AI**, and **Production AI Systems**.

This repository is the public research archive for my work on the engineering principles, methodologies, architectures and evaluation methods required to build, deploy and operate AI systems in real enterprise environments.

The work sits under a single umbrella theme, **Production AI Systems Engineering (PAISE)**: treating the deployment and operation of AI systems as an engineering discipline in its own right, with its own lifecycle, failure modes, measurements and standards, rather than as an afterthought to model development.

The goal is rigorous, reproducible and open research that closes the gap between academic AI research and production AI engineering. Where a paper makes an empirical claim, the code and data behind it are published alongside it.

---

## Research Areas

- Forward Deployed Engineering (FDE)
- AI Engineering
- Production AI Systems
- Enterprise AI Architecture
- Agentic AI
- Multi-Agent Systems
- Context Engineering
- LLM Systems
- AI Observability
- AI Evaluation
- AI Reliability
- AI Governance and Auditability
- Human-AI Collaboration
- Enterprise AI Deployment

---

## Publications

### 1. Forward Deployed Engineering: A Systems Engineering Perspective

**Status:** Preprint
**Type:** Conceptual, multivocal literature review

**Abstract**

Forward Deployed Engineering (FDE) has rapidly emerged as a critical practice for deploying AI systems within enterprise environments, yet it has received little formal academic attention. This paper examines FDE from a systems engineering perspective, presents a structured multivocal literature review, analyzes the practice through ISO/IEC/IEEE 15288 system lifecycle processes, and proposes a cross-organizational deployment lifecycle together with a research agenda for future work.

**Paper:** [`Forward_Deployed_Engineering_A_Systems_Engineering_Perspective.pdf`](Forward_Deployed_Engineering_A_Systems_Engineering_Perspective.pdf)

---

### 2. What Agent Traces Cannot Tell You: Evidentiary Adequacy of Runtime Records for Agentic AI Oversight

**Status:** Preprint
**Type:** Empirical, benchmark and reference implementation

**Abstract**

Governance platforms for agentic artificial intelligence now compile runtime telemetry into regulator-facing compliance evidence. Whether the resulting records can actually support the findings of fact that oversight requires has not been measured. We operationalise a published evidentiary-adequacy criterion, under which a runtime record answers a determination only if it carries both a typing that maps events to the legally operative category and the relation on which the determination depends, and we build the first benchmark that tests it. We generate 1,200 enterprise agent trajectories spanning 36,296 steps across six determination families, with ground truth known by construction, and instrument each trajectory under four record conditions: an application action log, OpenTelemetry GenAI spans, a governance layer carrying policy verdicts and article mappings, and a substrate that propagates information-flow labels and capability state into spans.

**Headline results**

| Record condition | Determinations both answered and answered correctly |
|---|---|
| Application action log | 16.33% |
| OpenTelemetry GenAI spans | 16.33% |
| Governance layer (policy verdicts, article mappings, hash chain) | 28.75% |
| Label-propagating substrate | 100.00% |

Three findings are worth stating plainly.

1. **OpenTelemetry GenAI spans are indistinguishable from an unstructured action log** for these six oversight questions. The two conditions produce identical outcomes on all 1,200 trajectories, with McNemar discordant counts of zero in both directions. The conventions add control-flow structure, and none of the six determinations depends on control flow.
2. **Weak records fail silently rather than visibly.** On the human-intervention determination the action log answers 52% of cases and is wrong in 27% of those, because with no reviewer-identity field the analysis quietly substitutes elapsed time for the missing typing. The governance layer answers exactly the same 52% and is wrong in none. Coverage statistics alone would rank the two as equal.
3. **The relation binds, not the typing.** An oracle control given perfect knowledge of every document's true classification, but no derivation relation, still errs at 47.0%, all of it false positives. Sweeping the classification proxy across almost its entire achievable range moves baseline error by under four percentage points. Better content classification cannot repair instrumentation that does not record derivation.

The substrate costs 4.8% more serialised bytes than the governance layer it extends, and 8.4% more after compression.

**Paper:** [`What_Agent_Traces_Cannot_Tell_You_Evidentiary_Adequacy_of_Runtime_Records_for_Agentic_AI_Oversight.pdf`](What_Agent_Traces_Cannot_Tell_You_Evidentiary_Adequacy_of_Runtime_Records_for_Agentic_AI_Oversight.pdf)
**Code and data:** [`adequacy-bench/`](adequacy-bench/)

---

## AdequacyBench

The benchmark, four record emitters, resolvers, experiment driver and full result set behind Paper 2 live in [`adequacy-bench/`](adequacy-bench/).

```
adequacy-bench/
  adqbench/model.py      labelled values, capabilities, events, trajectories
  adqbench/generate.py   six determination families with adversarial decoys
  adqbench/emit.py       four record conditions
  adqbench/resolve.py    conservative and heuristic resolvers
  adqbench/run.py        experiment driver, statistics, oracle control
  results/results.json   every number reported in the paper
  figure.py              Figure 1
```

Reproduce with:

```bash
python3 -m adqbench.run     # writes results/results.json
python3 figure.py           # writes fig1.png
```

Requires Python 3 with scipy and matplotlib. Runtime is roughly 30 seconds. Everything except record-construction timing is deterministic under the fixed seed (20260820) and reproduces exactly, which is why timing is reported in the paper as a range in prose rather than tabulated.

**The six determinations**

| ID | Question |
|---|---|
| D1 | Did protected data cross an external boundary? |
| D2 | Could a human have intervened before the effecting action? |
| D3 | Did the information barrier hold? |
| D4 | Was delegated authority valid at the moment of use? |
| D5 | Was a denied action later achieved by another path? |
| D6 | Which principal authorised the effecting call? |

**Design invariants worth preserving if you extend this**

1. Resolvability is decided from the record alone. A resolver must never read ground truth to decide whether it can answer. Violating this makes coverage meaningless.
2. Each emitter writes only what that class of instrumentation can honestly know. The baselines are modelled from published descriptions, deliberately generously where there was doubt.
3. Ground truth is known by construction, never adjudicated after the fact. This is the reason the corpus is generated rather than collected: obtaining ground-truth determinations from production data would require legal adjudication of every case.
4. The heuristic resolver is a stipulated model of practitioner inference, not measured human behaviour. Any claim about what auditors actually conclude requires an expert panel, which has not yet been run.

---

## Research Vision

Modern AI systems are no longer isolated machine learning models.

They are complex socio-technical systems involving:

- Large Language Models
- Enterprise Knowledge
- Human Decision Making
- Organizational Processes
- Software Systems
- Infrastructure
- Governance
- Continuous Learning

This repository explores the engineering principles required to design, deploy, evaluate and operate these systems reliably at enterprise scale.

---

## Long-Term Research Roadmap

Planned and in-progress research topics:

- Forward Deployed Engineering
- AI Engineering Lifecycle
- Context Engineering
- Enterprise Agent Architecture
- AI Observability and Auditability
- Agent Reliability
- Enterprise RAG Systems
- AI Evaluation Frameworks
- AI Governance
- AI Technical Debt
- Multi-Agent Coordination
- Re-qualification of deployed systems under model version churn
- Multi-tenant isolation for agent platforms
- The grounding cost curve: accuracy against curation effort
- Production AI Systems Engineering

---

## Citation

```bibtex
@misc{dharmadhikari2026fde,
  author       = {Dharmadhikari, Advait},
  title        = {Forward Deployed Engineering: A Systems Engineering Perspective},
  year         = {2026},
  note         = {Preprint},
  howpublished = {\url{https://github.com/advait27/AI-Research}}
}

@misc{dharmadhikari2026adequacy,
  author       = {Dharmadhikari, Advait},
  title        = {What Agent Traces Cannot Tell You: Evidentiary Adequacy of
                  Runtime Records for Agentic AI Oversight},
  year         = {2026},
  note         = {Preprint. Benchmark and reference implementation released as AdequacyBench},
  howpublished = {\url{https://github.com/advait27/AI-Research}}
}
```

BibTeX entries will be updated with DOIs and venue details as papers are formally published.

---

## Contact

**Advait Dharmadhikari**

- LinkedIn: https://linkedin.com/in/advaitdharmadhikari
- GitHub: https://github.com/advait27

---

## License

Unless otherwise specified, all papers remain the intellectual property of their respective authors. Please cite appropriately when referencing this work.

Code in `adequacy-bench/` is released to support replication and independent verification of the results reported in Paper 2.

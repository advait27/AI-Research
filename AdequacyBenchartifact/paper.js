const d = require('docx');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
        ShadingType, AlignmentType, BorderStyle, SectionType, LevelFormat, ImageRun } = d;
const fs = require('fs');

const NAMED = process.argv.includes('--named');
const OUTNAME = NAMED ? 'HICSS61-evidentiary-adequacy-NAMED.docx' : 'HICSS61-evidentiary-adequacy.docx';
const COLW = 4480;                 // usable width inside one of two columns (DXA)
const F = 'Times New Roman';

function P(t, o = {}) {
  return new Paragraph({
    children: [new TextRun({ text: t, font: F, size: o.size || 20, bold: o.bold, italics: o.italics })],
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { after: o.after === undefined ? 100 : o.after, before: o.before || 0, line: o.line || 230 },
    indent: o.indent
  });
}
function RUNS(rs, o = {}) {
  return new Paragraph({
    children: rs.map(r => new TextRun({ text: r.t, font: F, size: o.size || 20, bold: r.b, italics: r.i })),
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { after: o.after === undefined ? 100 : o.after, line: 230 },
    indent: o.indent
  });
}
function H(t, o = {}) {
  return new Paragraph({
    children: [new TextRun({ text: t, font: F, size: o.size || 22, bold: true })],
    spacing: { before: o.before || 200, after: 80 }, alignment: AlignmentType.LEFT
  });
}
function BUL(t) {
  return new Paragraph({
    children: [new TextRun({ text: t, font: F, size: 20 })],
    numbering: { reference: 'b', level: 0 }, spacing: { after: 60, line: 230 },
    alignment: AlignmentType.JUSTIFIED
  });
}
function REF(t) {
  return new Paragraph({
    children: [new TextRun({ text: t, font: F, size: 18 })],
    spacing: { after: 60, line: 215 }, indent: { left: 260, hanging: 260 },
    alignment: AlignmentType.LEFT
  });
}
function cell(t, w, o = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: o.shade ? { type: ShadingType.CLEAR, fill: o.shade, color: 'auto' } : undefined,
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({
      children: [new TextRun({ text: t, font: F, size: o.size || 16, bold: o.bold })],
      alignment: o.align || AlignmentType.LEFT, spacing: { after: 0, line: 205 },
      keepNext: true, keepLines: true
    })]
  });
}
function TBL(headers, rows, widths, opts = {}) {
  const hr = new TableRow({ tableHeader: true, cantSplit: true,
    children: headers.map((h, i) => cell(h, widths[i], { bold: true, shade: 'EEEEEE', size: opts.size || 16, align: i ? AlignmentType.CENTER : AlignmentType.LEFT })) });
  const br = rows.map(r => new TableRow({ cantSplit: true,
    children: r.map((c, i) => cell(c, widths[i], { size: opts.size || 16, align: i ? AlignmentType.CENTER : AlignmentType.LEFT })) }));
  return new Table({ columnWidths: widths, width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, rows: [hr, ...br] });
}
const CAP = t => new Paragraph({ children: [new TextRun({ text: t, font: F, size: 16, bold: true })],
  spacing: { before: 60, after: 140 }, alignment: AlignmentType.LEFT });
const GAP = () => new Paragraph({ text: '', spacing: { after: 80 } });

// ============================== FRONT MATTER (single column) =================
const front = [
  new Paragraph({ children: [new TextRun({ text: 'What Agent Traces Cannot Tell You: Evidentiary Adequacy of Runtime Records for Agentic AI Oversight', font: F, size: 32, bold: true })],
    alignment: AlignmentType.CENTER, spacing: { after: 180, line: 300 } }),
  ...(NAMED ? [
    new Paragraph({ children: [new TextRun({ text: 'Advait Dharmadhikari', font: F, size: 22 })],
      alignment: AlignmentType.CENTER, spacing: { after: 40 } }),
    new Paragraph({ children: [new TextRun({ text: 'Frensei Innovation Labs', font: F, size: 20, italics: true })],
      alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  ] : [
    new Paragraph({ children: [new TextRun({ text: 'Anonymous Submission', font: F, size: 22 })],
      alignment: AlignmentType.CENTER, spacing: { after: 40 } }),
    new Paragraph({ children: [new TextRun({ text: 'Author and affiliation details withheld for double-blind review', font: F, size: 20, italics: true })],
      alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  ]),
];

// ============================== BODY (two columns) ===========================
const K = [];
const A = (...x) => x.forEach(i => K.push(i));

A(H('Abstract', { size: 22, before: 0 }));
A(P('Governance platforms for agentic artificial intelligence now compile runtime telemetry into regulator-facing compliance evidence. Whether the resulting records can actually support the findings of fact that oversight requires has not been measured. We operationalise a published evidentiary-adequacy criterion, under which a runtime record answers a determination only if it carries both a typing that maps events to the legally operative category and the relation on which the determination depends, and we build the first benchmark that tests it. We generate 1,200 enterprise agent trajectories spanning 36,296 steps across six determination families, with ground truth known by construction, and instrument each trajectory under four record conditions: an application action log, OpenTelemetry GenAI spans, a governance layer carrying policy verdicts and article mappings, and a substrate that propagates information-flow labels and capability state into spans. Coverage of resolvable determinations is 16.3 percent for the action log, 16.3 percent for OpenTelemetry spans, 28.75 percent for the governance layer and 100 percent for the labelled substrate. Two findings are unexpected. First, weaker records fail silently rather than visibly: on the human-intervention determination the action log resolves 52 percent of cases but is wrong in 27 percent of those, because it substitutes elapsed time for the missing typing. Second, an oracle control shows that perfect classification knowledge without a derivation relation still yields a 47 percent error rate, all of it false positives. The labelled substrate costs 4.8 percent more serialised bytes than the governance layer it extends. We argue that agent telemetry standards should carry authorisation and information-flow semantics as first-class attributes, and we release the benchmark and reference implementation.',
  { size: 19 }));

A(H('1. Introduction'));
A(P('Regulatory regimes for artificial intelligence increasingly assume that the operator of a deployed system can reconstruct what it did. The European Union Artificial Intelligence Act requires record-keeping, human oversight, post-market monitoring and serious-incident reporting, each of which presupposes that the operator can establish facts about specific past events. A recent legal analysis of agentic systems under Union law concludes that high-risk agentic systems whose behaviour cannot be traced cannot currently satisfy those essential requirements (Nannini et al., 2026).'));
A(P('Industry has responded with instrumentation. Observability vendors and open standards emit structured traces of agent execution, and governance platforms compile those traces into evidence packages mapped to named articles, with tamper-resistant hashing and human review queues (Naik et al., 2026). The implicit claim is that a sufficiently rich, sufficiently tamper-evident record discharges the obligation.'));
A(P('That claim has not been tested. Janssen (2026) argues on analytic grounds that it is false as stated: the existence and integrity of a record do not establish that a legally operative finding can be recovered from it. A record answers a determination only if it carries both a typing that maps recorded events to the legally operative category and the relation, such as provenance, authority, derivation or temporal validity, on which the truth of the determination depends. The claim is one of necessity, not sufficiency, and it is made by construction rather than by measurement. No system has been built that satisfies it, and no benchmark exists against which any record format can be scored.'));
A(P('This paper supplies the measurement. Our contributions are as follows.'));
A(BUL('An operationalisation of the evidentiary-adequacy criterion as a decidable procedure over machine-readable records, separating coverage (can the record answer) from soundness (is the answer right).'));
A(BUL('A benchmark of 1,200 generated enterprise agent trajectories across six determination families, with ground truth known by construction and adversarial decoys that defeat surface heuristics.'));
A(BUL('A four-condition comparison covering the instrumentation that is actually deployed, and a reference substrate that propagates information-flow labels and capability state into spans.'));
A(BUL('Two results that were not anticipated by the analytic argument: silent unsoundness in weaker records, and the demonstration by oracle control that the relation, not the typing, is the binding constraint.'));

A(H('2. Background and related work'));
A(H('2.1. Evidence generation from agent telemetry', { size: 20 }));
A(P('Traccia builds a governance stack on OpenTelemetry that carries guardrail attributes, policy verdicts of log-only, warn and block, denied tool calls, human approvals through a reviewer queue, a hash-chained ledger, and an explicit article-mapping attribute, and compiles compliance evidence packages from them (Naik et al., 2026). Cilla Ugarte et al. (2026) address the complementary format problem, adapting a compliance-as-code assessment schema so that evidence is machine-readable across the Act, ISO/IEC 42001 and the NIST risk framework. Kahani et al. (2026) build a runtime monitor that enforces data-protection principles over agent event traces and emits per-event verdicts. AgentTrace proposes structured logging across operational, cognitive and contextual dimensions (AlSayyad et al., 2026), and Policy Cards proposes machine-readable runtime constraints (Mavracic, 2025).'));
A(P('None of this work evaluates whether the emitted record can answer an oversight question. Traccia reports the platform, not an evaluation of the evidence it produces. The gap is not incidental: there is no benchmark of agent traces annotated with compliance-relevant ground truth against which such an evaluation could be run.'));

A(H('2.2. What auditability requires', { size: 20 }));
A(P('Chan et al. (2024) set out visibility measures for deployed agents, including agent identifiers and activity logging. Nian et al. (2026) decompose auditability into action recoverability, lifecycle coverage, policy checkability, responsibility attribution and evidence integrity, and argue that no single temporal vantage point satisfies all five. Wang et al. (2026) survey evidence tracing and execution provenance, defining provenance as a typed graph over agent execution. Mumtaz and Mumtaz (2026) find, across 480 catalogued incidents, that the overwhelming majority show no evidence of post-market monitoring, and that internally detected incidents are dramatically more likely to be compliant than externally detected ones. Staufer et al. (2026) document that developers of deployed agents disclose very little about safety and evaluation.'));
A(P('This literature establishes that something is missing. It does not measure what.'));

A(H('2.3. Security substrates and conventions', { size: 20 }));
A(P('The architectural line on agent security supplies the primitives our substrate reuses. Information-flow control for agents attaches confidentiality and integrity labels to planner data (Costa et al., 2025); capability-based designs separate control flow from data flow and restrict what a tool call may do (Debenedetti et al., 2025); privilege control expresses tool-call policy symbolically (Shi et al., 2025); and the pattern catalogue codifies the design space (Beurer-Kellner et al., 2025). These lineages descend from the lattice model of secure information flow (Denning, 1976), the decentralized label model (Myers and Liskov, 2000), and capability semantics (Dennis and Van Horn, 1966). Provenance has a mature standard in the PROV data model (Moreau and Missier, 2013).'));
A(P('Critically, these systems are built to prevent violations, not to evidence them. Their labels and grants live in memory and are discarded. The OpenTelemetry GenAI semantic conventions, which are the emerging carrier for agent telemetry, define agent spans and Model Context Protocol conventions but no attribute for a policy verdict, a denied call, an approval, a capability grant or an information-flow label; at the time of writing every relevant document in that repository is marked as in development rather than stable (OpenTelemetry Authors, 2026). An open proposal to add tool risk attributes explicitly scopes out decision outcomes.'));

A(H('2.4. Position of this work', { size: 20 }));
A(P('We take the criterion from Janssen (2026) as given rather than re-deriving it, take the platform architecture from Naik et al. (2026) as the state of practice, and supply the evaluation layer that both leave open.'));

A(H('3. Method'));
A(H('3.1. Determination classes', { size: 20 }));
A(P('We study binary findings of fact about specific events and their relations. Four classes are taken directly from the source criterion and two are added because they arise only in agentic settings. Table 1 states each determination and the typing and relation it depends on.'));
A(GAP());
A(TBL(['ID', 'Determination, and the typing and relation it requires'],
  [['D1', 'Did protected data cross an external boundary? Typing: classification of the payload. Relation: derivation from a classified source, respecting declassification.'],
   ['D2', 'Could a human have intervened before the effecting action? Typing: human versus automated authorisation. Relation: binding of the authorisation to that action, and temporal order.'],
   ['D3', 'Did the information barrier hold? Typing: tenant of origin. Relation: derivation into the delivered artifact.'],
   ['D4', 'Was delegated authority valid at the moment of use? Typing: capability scope. Relation: delegation chain and temporal validity at the time of the call.'],
   ['D5', 'Was a denied action later achieved by another path? Typing: canonical effect. Relation: equivalence of effect across differently named calls.'],
   ['D6', 'Which principal authorised the effecting call? Typing: capability root. Relation: attribution of the call to a chain.']],
  [420, 4060]));
A(CAP('Table 1. The six determination families.'));

A(H('3.2. Trajectory generation', { size: 20 }));
A(P('Each trajectory is a fully observed simulation of an enterprise agent session over retrievals, derivations, declassifications, tool reads, writes, external sends, approval requests and grants, policy allowances and denials, and delegations. Values carry information-flow labels that join on derivation, following the lattice model. Capabilities carry a scope, a validity interval and a parent, forming delegation chains.'));
A(P('Because we construct the world, ground truth for every determination is known by construction rather than adjudicated after the fact. This is the reason a generated corpus is not merely a convenience here. Obtaining ground-truth determinations from production data would require legal adjudication of every case, which is precisely why no such corpus exists.'));
A(P('Each family embeds decoys chosen so that surface heuristics are systematically misled. Boundary-crossing trajectories include protected documents retrieved into the session but absent from the derivation chain of the payload, and derived payloads that have been genuinely declassified by aggregation. Intervention trajectories include authorisations granted retroactively, automated approvals that are structurally identical to human ones apart from reviewer identity, and approvals bound to a different action. Authority trajectories include expired intermediate links, scope violations at a single link, and unrelated valid grants held by the same principal. Circumvention trajectories include a denied call followed by a differently named call with the same effect, and by an identically named call with a different effect.'));
A(P('The corpus comprises 200 trajectories per family, 1,200 in total, with a mean of 30.2 steps and 36,296 steps overall. Positive base rates range from 0.28 to 0.70. Structural mixes are reported in Table 4 because they bound what the baselines can resolve.'));

A(H('3.3. Record conditions', { size: 20 }));
A(P('Each condition emits only what that class of instrumentation can honestly know.'));
A(RUNS([{ t: 'BARE. ', b: true }, { t: 'An application action log: timestamp, tool name, argument string and status. Document titles appear in arguments, which is the only sensitivity signal available.' }]));
A(RUNS([{ t: 'OTEL. ', b: true }, { t: 'OpenTelemetry GenAI spans with operation name, tool name, call identifier, arguments, agent identifier, error type, and a parent-child span tree in which tool spans are siblings under a turn span.' }]));
A(RUNS([{ t: 'GUARD. ', b: true }, { t: 'OTEL plus a governance layer of the kind described by Naik et al. (2026): session tenant, article mapping, risk tier, policy verdict and guardrail identifiers, authorisation decision, approval review records with reviewer identity, data source tenant on retrievals, a payload risk tier with an explicit classification source of artifact or surface scan, and a hash chain.' }]));
A(RUNS([{ t: 'TYPED. ', b: true }, { t: 'GUARD plus value-level labels propagated across derivations, an explicit derives-from edge, capability identity with scope, validity interval, parent and root, request scope, canonical effect signature, and approvals typed as human or automated with an explicit reference from the action to the authorisation it relied on.' }]));
A(P('The baselines are defined by what published instrumentation emits. None of the three carries value-level labels or capability state. That absence is the object of study, not an artefact of the modelling.'));

A(H('3.4. Resolvers', { size: 20 }));
A(P('A conservative resolver answers a determination only when the record carries both the required typing and the required relation, and otherwise returns unresolvable. Resolvability is decided from the record alone and never from ground truth; the resolvers read only the serialised record and the externally posed question.'));
A(P('Concretely, for a determination D over a record R the procedure asks two questions in order. Does R contain a field that types the relevant events as instances of the legally operative category named by D, as opposed to a proxy correlated with it? And does R contain the relation D quantifies over, as an explicit edge rather than as an inference from adjacency, ordering or naming? Only if both hold does the resolver compute an answer. The distinction between a typing and a proxy is decided by whether the field is definitionally tied to the category, so a reviewer identity that distinguishes a human from an automated approver is a typing, while the interval between request and grant is a proxy.'));
A(P('A heuristic resolver models what a practitioner does when the record cannot answer: it always answers, using surface proxies such as temporal proximity, the presence of an approval event anywhere in the trace, tool-name similarity, or the assumption that the session initiator is the authoriser. It is a stipulated model of practitioner inference, not measured human behaviour, and we treat it accordingly in Section 6.'));

A(H('3.5. Measures', { size: 20 }));
A(P('Coverage is the proportion of trajectories in which the conservative resolver answers. Soundness is the proportion of answered cases that are correct. Their product, reported as the joint rate, is the proportion of determinations both answered and answered correctly. We report Wilson intervals and compare conditions pairwise on the joint outcome with an exact McNemar test, paired by trajectory. We also report the cost of instrumentation, the heuristic error rate on the subset the record could not answer, and degradation under uniform span loss.'));

A(H('4. Results'));
A(H('4.1. Coverage and soundness', { size: 20 }));
A(P('Table 2 reports coverage and soundness for every determination and condition. Pooled across all 1,200 determinations, the joint rate is 0.163 for BARE with a 95 percent interval of 0.143 to 0.185, 0.163 for OTEL, 0.2875 for GUARD with an interval of 0.263 to 0.314, and 1.000 for TYPED with an interval of 0.997 to 1.000.'));
A(GAP());
A(TBL(['', 'BARE', 'OTEL', 'GUARD', 'TYPED'],
  [['D1', '0.00 / n.a.', '0.00 / n.a.', '0.30 / 1.00', '1.00 / 1.00'],
   ['D2', '0.52 / 0.73', '0.52 / 0.73', '0.52 / 1.00', '1.00 / 1.00'],
   ['D3', '0.00 / n.a.', '0.00 / n.a.', '0.30 / 1.00', '1.00 / 1.00'],
   ['D4', '0.00 / n.a.', '0.00 / n.a.', '0.00 / n.a.', '1.00 / 1.00'],
   ['D5', '0.28 / 1.00', '0.28 / 1.00', '0.28 / 1.00', '1.00 / 1.00'],
   ['D6', '0.32 / 1.00', '0.32 / 1.00', '0.32 / 1.00', '1.00 / 1.00'],
   ['Pooled', '0.1633', '0.1633', '0.2875', '1.0000']],
  [720, 940, 940, 940, 940]));
A(CAP('Table 2. Coverage / soundness by determination. Pooled row is the joint resolve-and-correct rate, n = 1,200.'));
A(P('The pairwise comparisons on the pooled joint outcome are decisive in two places and null in one. TYPED improves on GUARD in 855 trajectories and is worse in none, p < 0.001. GUARD improves on OTEL in 149 trajectories and is worse in none, p < 0.001. OTEL and BARE are identical on every trajectory: the discordant counts are zero in both directions, p = 1.0.'));
A(P('That last result deserves emphasis. For these six determinations, adopting OpenTelemetry GenAI spans in place of an unstructured action log buys nothing. The conventions add control-flow structure through the span tree, and none of the six determinations depends on control flow. They depend on data flow, authority and effect, none of which the conventions represent. This is a statement about the semantics the conventions currently carry, not about their engineering value for latency or debugging.'));

A(H('4.2. Weak records fail silently', { size: 20 }));
A(P('The intervention determination is the only one on which the baselines have substantial coverage, and it is the one where they are unsound. BARE and OTEL answer 52 percent of intervention determinations and are wrong in 27 percent of the cases they answer. GUARD answers exactly the same 52 percent and is wrong in none.'));
A(P('The mechanism is instructive. All four records show that an approval was requested and granted before the action. Only GUARD and TYPED carry reviewer identity, which types the grant as human or automated. Lacking that typing, the resolver over BARE and OTEL does not fail; it silently substitutes a proxy, treating a nonzero interval between request and grant as evidence of human deliberation, and is then systematically wrong on every automated approval.'));
A(P('This is the practically dangerous case. An inadequate record does not announce its inadequacy. It produces a confident answer that an auditor has no way to distinguish from a sound one, and coverage statistics alone would rank BARE and GUARD as equal on this determination.'));
A(P('On the subsets the conservative resolver could not answer, the heuristic resolver errs at rates between 32 and 66 percent depending on determination and condition: 47 percent on boundary crossing, 55 percent on intervention, 52 percent on authority validity, 66 percent on circumvention and 44 percent on attribution. For TYPED there is no such subset.'));

A(H('4.3. The relation, not the typing', { size: 20 }));
A(P('A natural objection is that the baselines fail only because their classification signal is poor, and that better content classification would close the gap. Two measurements refute this.'));
A(P('First, we swept the quality of the sensitivity proxy available to the baselines, varying its precision from 0.55 to 0.98. The boundary-crossing error rate for BARE and OTEL moved from 0.495 to 0.460, a change of less than four percentage points across almost the entire achievable range of proxy quality.'));
A(P('Second, and decisively, we ran an oracle control in which the resolver is given perfect knowledge of the true classification of every retrieved document but still no derivation relation. Its error rate on boundary crossing is 47.0 percent, and every error is a false positive: 50.0 percent on trajectories with a derived payload and 40.0 percent on trajectories with a direct payload. Perfect typing without the relation answers the wrong question. It establishes that protected data was present in the session, which is not what the determination asks.'));
A(P('This is the empirical form of the necessity claim. Typing and relation are not substitutes, and investment in classification cannot compensate for an instrumentation layer that does not record derivation.'));

A(H('4.4. Cost of the substrate', { size: 20 }));
A(P('Table 3 reports the cost of each record. The comparison that matters is TYPED against GUARD, because a deployment that has already adopted a governance layer is the realistic adopter. Propagating labels and capability state adds 4.8 percent to serialised bytes, 8.4 percent after compression, and 0.7 fields per span.'));
A(GAP());
A(TBL(['', 'Bytes', 'Gzip bytes', 'Fields per span'],
  [['BARE', '2,211', '296', '4.0'],
   ['OTEL', '8,807', '719', '10.0'],
   ['GUARD', '14,202', '1,428', '15.3'],
   ['TYPED', '14,891', '1,548', '16.0']],
  [860, 1180, 1220, 1220]));
A(CAP('Table 3. Record cost per trajectory, mean over 1,200 trajectories.'));
A(P('Record construction cost in our reference implementation, measured as the median of five repetitions, is below 10 ms per thousand agent steps for every condition, rising from roughly 0.2 ms for BARE and under 1 ms for OTEL to between 7 and 8 ms for GUARD and TYPED. These are the cost of building and serialising the record in a Python reference implementation and are not a production overhead measurement; we report them only to locate where the step change falls. It falls between OTEL and GUARD, which is where hash chaining enters, and the marginal cost of the security semantics above that is within run-to-run variance.'));
A(P('The relevant comparison for a decision maker is therefore not that TYPED costs 1.69 times an OpenTelemetry baseline, but that the increment over a governance layer already being deployed for other reasons is under five percent of serialised bytes for a move from 28.75 to 100 percent coverage.'));

A(H('4.5. Degradation under sampling', { size: 20 }));
A(P('Production telemetry is sampled, and no prior work measures audit reconstruction under degraded logs. Figure 1 reports coverage and soundness when a fraction of spans is dropped uniformly at random.'));
A(GAP());
A(new Paragraph({ children: [new ImageRun({ type: 'png', data: fs.readFileSync('fig1.png'),
  transformation: { width: 293, height: 334 } })], alignment: AlignmentType.CENTER,
  spacing: { after: 40 } }));
A(CAP('Figure 1. Coverage and soundness under uniform span loss, pooled over all six determinations. BARE and OTEL coincide in panel (a) and are within one point of each other in panel (b).'));
A(P('Two patterns appear. TYPED loses coverage roughly in proportion to loss, which is the desirable behaviour: a missing span makes a determination unresolvable rather than wrongly resolved. The baselines instead hold coverage almost constant while soundness decays, from 0.88 to 0.73 for BARE. The reason is that several baseline resolutions are absence-based, concluding that no approval was obtained because no approval appears; under sampling, absence stops being evidence. Any deployment that samples agent telemetry and then reasons from the absence of an event is drawing unsound conclusions at a rate governed by its sampling policy.'));
A(GAP());
A(TBL(['Family', 'Structural mix that bounds the baselines'],
  [['D1', 'Direct payload, no derivation: 0.30'],
   ['D2', 'Exactly one effecting action: 0.52'],
   ['D3', 'Single tenant in session: 0.305'],
   ['D4', 'Mean delegation chain depth: 1.97'],
   ['D5', 'Denial linkable by tool name and arguments: 0.285'],
   ['D6', 'Single principal in session: 0.315']],
  [700, 3780]));
A(CAP('Table 4. Corpus composition. Baseline coverage tracks these proportions closely, which is the expected behaviour if the baselines resolve exactly the structurally trivial cases.'));

A(H('5. Discussion'));
A(H('5.1. For telemetry standards', { size: 20 }));
A(P('The finding that OpenTelemetry GenAI spans are indistinguishable from an unstructured action log for oversight purposes is actionable rather than merely critical. The conventions are in development, not stable, and the attributes required are few: a policy verdict and its outcome, a denied call, an authorisation with a reviewer type and a reference to the action it authorised, a capability with scope, validity and root, and a value-level label with a derives-from edge. Our results indicate that the last two carry most of the value, since they are what distinguishes TYPED from GUARD and account for the move from 28.75 to 100 percent coverage. A proposal to extend the conventions is a more consequential intervention than any single platform.'));
A(H('5.2. For evidence generation', { size: 20 }));
A(P('Platforms that compile evidence packages from telemetry inherit the adequacy of the telemetry. Article mappings, hash chains and reviewer queues address integrity and provenance of the record, which our results show is orthogonal to whether the record answers anything. A hash-chained record of an inadequate trace is an integrity-assured inability to establish the fact. We suggest that evidence packages carry an explicit adequacy annotation, declaring for each determination class whether the underlying record satisfies typing and relation, so that an unresolvable question is reported as unresolvable rather than resolved by a downstream heuristic.'));
A(H('5.3. For deployment practice', { size: 20 }));
A(P('The instrumentation decision is made early, by the engineer integrating an agent into a customer environment, and is expensive to revisit because it is retrospective: a record not captured at the time cannot be reconstructed later. Our cost measurements suggest the decision is not a difficult trade-off for an organisation already deploying a governance layer. The harder problem is organisational, since label propagation must reach across the connectors and tools an integration touches, which is exactly where customer-specific work concentrates.'));

A(H('6. Threats to validity'));
A(RUNS([{ t: 'Construct validity. ', b: true }, { t: 'Adequacy is defined relative to a necessity criterion. A record that passes is not thereby legally sufficient, and we make no claim that a resolved determination would be accepted by a court or a market surveillance authority. Our determination classes are binary findings of fact about specific events, and the criterion is not defined for open-ended evaluative judgements.' }]));
A(RUNS([{ t: 'The heuristic resolver. ', b: true }, { t: 'It is stipulated, not measured. We do not know that practitioners reason as it does, and the heuristic error rates should be read as the error of a specific documented rule, not as a measurement of human performance. Establishing what human auditors actually conclude from each record condition requires an expert panel, which we did not run and which is the first item of future work.' }]));
A(RUNS([{ t: 'External validity. ', b: true }, { t: 'Trajectories are generated. Real enterprise content is more ambiguous, real tool catalogues are larger, and real sessions are longer and interleaved across users. Our decoy mixes are design choices, and baseline coverage tracks them closely, as Table 4 shows. Absolute coverage figures should therefore be read as properties of this corpus; the qualitative ordering and the oracle-control result do not depend on the mix.' }]));
A(RUNS([{ t: 'Baseline fidelity. ', b: true }, { t: 'We model GUARD from a published description rather than from a released implementation, since none is available. We may have modelled it conservatively or generously in places, and we have tried to err toward generosity, giving it artifact-backed payload classification and reviewer identity.' }]));
A(RUNS([{ t: 'Regulatory instability. ', b: true }, { t: 'We design against articles rather than against dates, because the applicable dates for high-risk obligations are subject to amendment.' }]));

A(H('7. Conclusion'));
A(P('Runtime records for agentic systems are being built on the assumption that richness and integrity are what oversight requires. We measured that assumption against a published necessity criterion and found it wrong in a specific and repairable way. Coverage of resolvable determinations rises from 16.3 percent for an action log and for OpenTelemetry GenAI spans, through 28.75 percent for a governance layer, to 100 percent for a substrate that carries information-flow labels and capability state, at a marginal cost under five percent of serialised bytes over the governance layer. Weaker records fail silently rather than visibly, and better content classification does not repair them, because the missing element is the relation and not the typing.'));
A(P('Future work is in three parts. First, the expert panel, replacing our stipulated heuristic with measured human determination under each record condition. Second, a proposal to the GenAI semantic conventions covering authorisation and information-flow attributes. Third, extension of the corpus toward realistic enterprise content and interleaved multi-user sessions, and validation of the substrate against a live agent framework rather than a simulation. The benchmark, the four emitters, the resolvers and the full result set are released to support replication.'));

A(H('References'));
[
'AlSayyad, A., Huang, K. Y., & Pal, R. (2026). AgentTrace: A structured logging framework for agent system observability [Preprint]. arXiv. https://arxiv.org/abs/2602.10133',
'Beurer-Kellner, L., Buesser, B., Cretu, A.-M., Debenedetti, E., Dobos, D., Fabian, D., Fischer, M., Froelicher, D., Grosse, K., Naeff, D., Ozoani, E., Paverd, A., Tramer, F., & Volhejn, V. (2025). Design patterns for securing LLM agents against prompt injections [Preprint]. arXiv. https://arxiv.org/abs/2506.08837',
'Bhatt, S. S., Rajore, T., Aggarwal, K., Ananthanarayanan, G., Chandra, R., Chandran, N., Choudhury, S., Gupta, D., Kiciman, E., Pandey, S. K., Setty, S., Sharma, R., & Zhao, T. (2025). Enterprise AI must enforce participant-aware access control [Preprint]. arXiv. https://arxiv.org/abs/2509.14608',
'Burnat, F., & Davidson, B. (2026). Auditing privacy in multi-tenant RAG under account collusion [Preprint]. arXiv. https://arxiv.org/abs/2605.19847',
'Chan, A., Ezell, C., Kaufmann, M., Wei, K., Hammond, L., Bradley, H., Bluemke, E., Rajkumar, N., Krueger, D., Kolt, N., Heim, L., & Anderljung, M. (2024). Visibility into AI agents. In Proceedings of the 2024 ACM Conference on Fairness, Accountability, and Transparency. Association for Computing Machinery.',
'Cilla Ugarte, R., Patricio Guisado, M. A., Berlanga de Jesus, A., & Molina Lopez, J. M. (2026). Making AI compliance evidence machine-readable [Preprint]. arXiv. https://arxiv.org/abs/2604.13767',
'Costa, M., Kopf, B., Kolluri, A., Paverd, A., Russinovich, M., Salem, A., Tople, S., Wutschitz, L., & Zanella-Beguelin, S. (2025). Securing AI agents with information-flow control [Preprint]. arXiv. https://arxiv.org/abs/2505.23643',
'Debenedetti, E., Shumailov, I., Fan, T., Hayes, J., Carlini, N., Fabian, D., Kern, C., Shi, C., Terzis, A., & Tramer, F. (2025). Defeating prompt injections by design [Preprint]. arXiv. https://arxiv.org/abs/2503.18813',
'Denning, D. E. (1976). A lattice model of secure information flow. Communications of the ACM, 19(5), 236-243. https://doi.org/10.1145/360051.360056',
'Dennis, J. B., & Van Horn, E. C. (1966). Programming semantics for multiprogrammed computations. Communications of the ACM, 9(3), 143-155. https://doi.org/10.1145/365230.365252',
'Janssen, J. (2026). From runtime records to legal findings: An evidentiary-adequacy criterion for agentic AI oversight [Preprint]. arXiv. https://arxiv.org/abs/2607.00941',
'Kahani, N., Barati, M., & Addae, D. (2026). Runtime compliance verification for AI agents [Preprint]. arXiv. https://arxiv.org/abs/2606.19242',
'Margalit, Y., Cohen-Inger, N., Avram, E., Taig, R., & Margalit, O. (2026). Governed shared memory for multi-agent LLM systems [Preprint]. arXiv. https://arxiv.org/abs/2606.24535',
'Mavracic, J. (2025). Policy cards: Machine-readable runtime governance for autonomous AI agents [Preprint]. arXiv. https://arxiv.org/abs/2510.24383',
'Moreau, L., & Missier, P. (Eds.). (2013). PROV-DM: The PROV data model (W3C Recommendation, 30 April 2013). World Wide Web Consortium. https://www.w3.org/TR/prov-dm/',
'Mumtaz, U., & Mumtaz, S. (2026). Post-deployment accountability in AI governance: A cross-regulatory empirical analysis of AI incidents [Preprint]. arXiv. https://arxiv.org/abs/2605.16281',
'Myers, A. C., & Liskov, B. (2000). Protecting privacy using the decentralized label model. ACM Transactions on Software Engineering and Methodology, 9(4), 410-442. https://doi.org/10.1145/363516.363526',
'Naik, N. K., Saroj, A. K., Poudel, V. P., Samantray, S., & Patel, A. (2026). Traccia: An OpenTelemetry-based governance platform for AI systems [Preprint]. arXiv. https://arxiv.org/abs/2607.14309',
'Nannini, L., Leon Smith, A., Maggini, M. J., Panai, E., Feliciano, S., Tiulkanov, A., Maran, E., Gealy, J., & Bisconti, P. (2026). AI agents under EU law [Working paper]. arXiv. https://arxiv.org/abs/2604.04604',
'Nian, Y., Li, L., Yuan, A., Zhang, H., Li, J., Hu, X., Wei, H., Xiao, X., Xiao, C., & Zhao, Y. (2026). Auditable agents [Preprint]. arXiv. https://arxiv.org/abs/2604.05485',
'OpenTelemetry Authors. (2026). GenAI semantic conventions. https://github.com/open-telemetry/semantic-conventions-genai',
'Shi, T., He, J., Wang, Z., Li, H., Wu, L., Guo, W., & Song, D. (2025). Progent: Securing AI agents with privilege control [Preprint]. arXiv. https://arxiv.org/abs/2504.11703',
'Staufer, L., Feng, K., Wei, K., Bailey, L., Duan, Y., Yang, M., Ozisik, A. P., Casper, S., & Kolt, N. (2026). The 2025 AI agent index: Documenting technical and safety features of deployed agentic AI systems. In Proceedings of the 2026 ACM Conference on Fairness, Accountability, and Transparency. Association for Computing Machinery.',
'Wang, Y., Zhang, J., Cai, T., Liu, Z., Sun, Q., Sun, Z., Wu, Z., Dong, M., Zheng, M., Yin, X., & Zhu, Y. (2026). From agent traces to trust: A survey of evidence tracing and execution provenance in LLM agents [Preprint]. arXiv. https://arxiv.org/abs/2606.04990',
'Xu, J., Fan, L., Wang, Z., Li, X., & Liu, H. (2026). Beyond single-use tokens: Durable authorization state for replay-resistant LLM agent actions [Preprint]. arXiv. https://arxiv.org/abs/2608.01710'
].forEach(r => A(REF(r)));

const doc = new Document({
  numbering: { config: [{ reference: 'b', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 320, hanging: 180 } } } }] }] },
  styles: { default: { document: { run: { font: F, size: 20 } } } },
  sections: [
    { properties: { page: { size: { width: 12240, height: 15840 },
        margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: front },
    { properties: { type: SectionType.CONTINUOUS, column: { count: 2, space: 400, equalWidth: true },
        page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: K }
  ]
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUTNAME, b); console.log('written', OUTNAME, b.length); });

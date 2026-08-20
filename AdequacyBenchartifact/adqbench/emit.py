"""Four record conditions.

Each emitter writes only what that class of instrumentation can honestly know.
The baselines are defined by what published instrumentation actually emits:
an application action log; OpenTelemetry GenAI spans; and a governance layer of
the kind described for OTel-based AI governance platforms (policy verdicts,
approval review records, article mappings, hash chaining). None of the three
carries value-level information-flow labels or capability state, and that
absence is the object of study rather than a limitation of the modelling.
"""
from __future__ import annotations
import json, hashlib
from .model import (RETRIEVE, DERIVE, DECLASSIFY, TOOL_READ, TOOL_WRITE,
                    EXTERNAL_SEND, APPROVAL_REQUEST, APPROVAL_GRANT,
                    POLICY_ALLOW, POLICY_DENY, DELEGATE, EFFECTING)

BARE, OTEL, GUARD, TYPED = "BARE", "OTEL", "GUARD", "TYPED"
CONDITIONS = [BARE, OTEL, GUARD, TYPED]

ARTICLE_MAP = {EXTERNAL_SEND: "art_12,art_26", TOOL_WRITE: "art_12,art_14",
               POLICY_DENY: "art_14", APPROVAL_GRANT: "art_14", RETRIEVE: "art_10"}


def _title(e):
    return e.display_name or ""


def emit(tr, cond):
    rows = []
    prev_hash = "0" * 16
    for e in tr.events:
        if cond == BARE:
            args = e.args_repr
            if e.kind == RETRIEVE:
                args = f"doc={e.doc_id} title={_title(e)}"
            rows.append({"t": e.t, "tool": e.tool, "args": args, "status": e.status})
            continue

        span = {
            "span_id": f"s{e.seq}", "parent_span_id": f"turn{e.turn}",
            "name": f"execute_tool {e.tool}", "start": e.t, "end": e.t + 0.4,
            "gen_ai.operation.name": "execute_tool" if e.kind != DERIVE else "chat",
            "gen_ai.tool.name": e.tool,
            "gen_ai.tool.call.id": f"c{e.seq}",
            "gen_ai.tool.call.arguments": (f"doc={e.doc_id} title={_title(e)}"
                                           if e.kind == RETRIEVE else e.args_repr),
            "gen_ai.agent.id": "svc_agent",
        }
        if e.status == "denied":
            span["error.type"] = "policy_denied"

        if cond in (GUARD, TYPED):
            span["session.tenant"] = tr.session_tenant
            span["eu_ai_act_article_mapping"] = ARTICLE_MAP.get(e.kind, "")
            span["eu_risk_tier"] = "high" if e.kind in EFFECTING else "limited"
            if e.kind in (POLICY_DENY, POLICY_ALLOW) or e.status == "denied":
                span["policy.verdict"] = "block" if e.status == "denied" else "allow"
                span["guardrail.policy_id"] = "pol_egress_01"
                span["guardrail.enforcement_mode"] = "enforce"
            if e.kind in EFFECTING:
                span["authz.decision"] = "allow"
                span["authz.policy_id"] = "pol_rbac_02"
            if e.kind == APPROVAL_GRANT:
                span["approval.review_id"] = f"rv{e.seq}"
                span["approval.reviewer"] = e.principal
                span["approval.trace_id"] = tr.tid
            if e.kind == APPROVAL_REQUEST:
                span["approval.requested"] = True
            if e.kind == RETRIEVE:
                span["data.source.tenant"] = e.target_tenant
                # payload hash matches a stored classified artifact
                span["content.risk_tier"] = tr.values[e.produces].classification
                span["content.classification_source"] = "artifact"
            if e.kind == EXTERNAL_SEND and e.consumes:
                v = e.consumes[0]
                lab = tr.values[v]
                direct = v in {x.produces for x in tr.events if x.kind == RETRIEVE}
                span["content.risk_tier"] = lab.classification
                span["content.classification_source"] = "artifact" if direct else "surface_scan"
            payload = json.dumps(span, sort_keys=True, default=str)
            h = hashlib.sha256((prev_hash + payload).encode()).hexdigest()[:16]
            span["evidence.prev_hash"] = prev_hash
            span["evidence.hash"] = h
            prev_hash = h

        if cond == TYPED:
            if e.produces:
                lab = tr.values[e.produces]
                span["sec.value.id"] = e.produces
                span["sec.value.classification"] = lab.classification
                span["sec.value.tenants"] = sorted(lab.tenants)
                span["sec.value.sources"] = sorted(lab.sources)
            if e.consumes:
                span["sec.derives_from"] = list(e.consumes)
            if e.kind == DECLASSIFY:
                span["sec.declassify.to"] = tr.values[e.produces].classification
                span["sec.declassify.rule"] = "aggregate_count"
            if e.cap_id:
                cap = tr.caps.get(e.cap_id)
                if cap:
                    span["sec.capability.id"] = cap.cap_id
                    span["sec.capability.scope"] = cap.scope
                    span["sec.capability.principal"] = cap.principal
                    span["sec.capability.valid_from"] = cap.valid_from
                    span["sec.capability.valid_to"] = cap.valid_to
                    span["sec.capability.parent"] = cap.parent
                    span["sec.capability.root"] = cap.root
            if e.scope:
                span["sec.request.scope"] = e.scope
            if e.effect_sig:
                span["sec.effect.signature"] = e.effect_sig
            if e.kind in EFFECTING and e.ref_seq is not None:
                span["sec.authorisation.ref"] = e.ref_seq
            if e.kind in (APPROVAL_REQUEST, APPROVAL_GRANT):
                span["sec.approval.scope"] = e.scope
                span["sec.approval.ref_action"] = e.ref_seq
                span["sec.approval.kind"] = ("human" if e.principal not in ("policy_auto", "")
                                             else "automated")
        rows.append(span)
    return rows


def serialise(rows):
    return json.dumps(rows, sort_keys=True, default=str)


def attr_count(rows):
    return sum(len(r) for r in rows)

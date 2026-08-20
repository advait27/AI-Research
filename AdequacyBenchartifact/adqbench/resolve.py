"""Resolvers.

CONSERVATIVE resolvers implement the necessity criterion directly: a
determination is answered only when the record carries both a typing that maps
recorded events to the legally operative category and the relation on which the
determination depends. Otherwise they return UNRESOLVABLE. Resolvability is
decided from the record alone and never from ground truth.

HEURISTIC resolvers model what a practitioner does when the record cannot
answer: they always answer, using surface proxies. They are a stipulated model
of practitioner inference, not measured human behaviour.
"""
from __future__ import annotations
from .emit import BARE, OTEL, GUARD, TYPED
from .generate import SENSITIVE_STEMS, SEND_TOOLS, WRITE_TOOLS
from .model import scope_subsumes, PROTECTED_FLOOR

UNRESOLVED = (False, None)
EGRESS = set(SEND_TOOLS)
EFFECT_TOOLS = set(SEND_TOOLS) | set(WRITE_TOOLS)


def norm(rows, cond):
    """Uniform read view over a record. Only fields the condition emits."""
    out = []
    for r in rows:
        if cond == BARE:
            out.append({"t": r["t"], "tool": r["tool"], "args": r["args"],
                        "status": r["status"], "raw": r})
        else:
            out.append({"t": r["start"], "tool": r.get("gen_ai.tool.name", ""),
                        "args": r.get("gen_ai.tool.call.arguments", ""),
                        "status": "denied" if r.get("error.type") else "ok",
                        "sid": r["span_id"], "raw": r})
    return out


def _sensitive_title(args):
    return any(st in args for st in SENSITIVE_STEMS)


def _val_index(rows):
    """value_id -> classification / tenants, from TYPED spans."""
    cls, ten = {}, {}
    for r in rows:
        v = r.get("sec.value.id")
        if v is not None:
            cls[v] = r.get("sec.value.classification")
            ten[v] = set(r.get("sec.value.tenants", []))
    return cls, ten


# ---------------------------------------------------------------- D1
def d1_conservative(rows, cond, q):
    V = norm(rows, cond)
    sends = [e for e in V if e["tool"] in EGRESS]
    if not sends:
        return UNRESOLVED
    if cond == TYPED:
        cls, _ = _val_index(rows)
        ans = False
        for e in sends:
            df = e["raw"].get("sec.derives_from")
            if not df:
                return UNRESOLVED
            v = df[0]
            if v not in cls:
                return UNRESOLVED
            ans = ans or (cls[v] >= PROTECTED_FLOOR)
        return (True, ans)
    if cond == GUARD:
        ans = False
        for e in sends:
            src = e["raw"].get("content.classification_source")
            if src != "artifact":
                return UNRESOLVED
            ans = ans or (e["raw"].get("content.risk_tier", 0) >= PROTECTED_FLOOR)
        return (True, ans)
    return UNRESOLVED


def d1_heuristic(rows, cond, q):
    V = norm(rows, cond)
    first_send = next((i for i, e in enumerate(V) if e["tool"] in EGRESS), None)
    if first_send is None:
        return (True, False)
    return (True, any(_sensitive_title(e["args"]) for e in V[:first_send]))


# ---------------------------------------------------------------- D2
def d2_conservative(rows, cond, q):
    V = norm(rows, cond)
    acts = [e for e in V if e["tool"] in EFFECT_TOOLS and e["status"] != "denied"]
    if not acts:
        return UNRESOLVED
    if cond == TYPED:
        by_sid = {r["span_id"]: r for r in rows}
        grants = {int(r["span_id"][1:]): r for r in rows
                  if r.get("sec.approval.kind") is not None and r.get("approval.review_id")}
        reqs = {int(r["span_id"][1:]): r for r in rows if r.get("approval.requested")}
        target = acts[0]
        ref = target["raw"].get("sec.authorisation.ref")
        if ref is None:
            return (True, False)
        g = grants.get(ref)
        if g is None:
            return (True, False)
        rq = reqs.get(g.get("sec.approval.ref_action"))
        wait = (g["start"] - rq["start"]) if rq else 0.0
        return (True, g.get("sec.approval.kind") == "human" and wait > 0
                and g["start"] < target["t"])
    # baselines: binding is by uniqueness of the effecting action
    if len(acts) != 1:
        return UNRESOLVED
    a = acts[0]
    reqs = [e for e in V if e["tool"] == "request_approval" and e["t"] < a["t"]]
    grants = [e for e in V if e["tool"] == "approval" and e["t"] < a["t"]]
    if not reqs or not grants:
        return (True, False)
    if cond == GUARD:
        # reviewer identity types the grant as human or automated
        rv = grants[-1]["raw"].get("approval.reviewer")
        return (True, rv is not None and rv != "policy_auto")
    # BARE and OTEL carry no reviewer identity: elapsed time is the only proxy,
    # and the rule silently substitutes it for the missing typing
    return (True, (grants[-1]["t"] - reqs[-1]["t"]) > 0)


def d2_heuristic(rows, cond, q):
    V = norm(rows, cond)
    return (True, any(e["tool"] in ("approval", "request_approval") for e in V))


# ---------------------------------------------------------------- D3
def d3_conservative(rows, cond, q):
    home = q["home_tenant"]
    V = norm(rows, cond)
    deliv = [e for e in V if e["tool"] in EGRESS]
    if not deliv:
        return UNRESOLVED
    if cond == TYPED:
        _, ten = _val_index(rows)
        for e in deliv:
            df = e["raw"].get("sec.derives_from")
            if not df or df[0] not in ten:
                return UNRESOLVED
            foreign = {t for t in ten[df[0]] if t not in (home, "shared")}
            if foreign:
                return (True, False)
        return (True, True)
    if cond == GUARD:
        srcs = {e["raw"].get("data.source.tenant") for e in V
                if e["raw"].get("data.source.tenant")}
        if srcs - {home, "shared"}:
            return UNRESOLVED       # foreign data present, but its flow is unrecorded
        return (True, True)
    return UNRESOLVED


def d3_heuristic(rows, cond, q):
    home = q["home_tenant"]
    if cond in (GUARD, TYPED):
        V = norm(rows, cond)
        srcs = {e["raw"].get("data.source.tenant") for e in V
                if e["raw"].get("data.source.tenant")}
        return (True, not bool(srcs - {home, "shared"}))
    return (True, True)             # no signal at all: assume the barrier held


# ---------------------------------------------------------------- D4
def d4_conservative(rows, cond, q):
    if cond != TYPED:
        return UNRESOLVED
    caps = {}
    for r in rows:
        cid = r.get("sec.capability.id")
        if cid and cid not in caps:
            caps[cid] = r
    acts = [r for r in rows if r.get("gen_ai.tool.name") in EFFECT_TOOLS
            and r.get("sec.capability.id")]
    if not acts:
        return UNRESOLVED
    a = acts[0]
    t = a["start"]
    need = a.get("sec.request.scope")
    cid = a.get("sec.capability.id")
    while cid is not None:
        c = caps.get(cid)
        if c is None:
            return UNRESOLVED
        if not (c["sec.capability.valid_from"] <= t <= c["sec.capability.valid_to"]):
            return (True, False)
        if not scope_subsumes(c["sec.capability.scope"], need):
            return (True, False)
        need = c["sec.capability.scope"]
        cid = c.get("sec.capability.parent")
    return (True, True)


def d4_heuristic(rows, cond, q):
    V = norm(rows, cond)
    has_delegate = any(e["tool"] == "delegate" for e in V)
    allowed = any(e["tool"] in EFFECT_TOOLS and e["status"] != "denied" for e in V)
    return (True, has_delegate and allowed)


# ---------------------------------------------------------------- D5
def d5_conservative(rows, cond, q):
    V = norm(rows, cond)
    den = [e for e in V if e["status"] == "denied"]
    if not den:
        return UNRESOLVED
    d = den[0]
    later = [e for e in V if e["t"] > d["t"] and e["status"] != "denied"
             and e["tool"] in EFFECT_TOOLS]
    if cond == TYPED:
        sig = d["raw"].get("sec.effect.signature")
        if sig is None:
            return UNRESOLVED
        return (True, any(e["raw"].get("sec.effect.signature") == sig for e in later))
    if any(e["tool"] == d["tool"] and e["args"] == d["args"] for e in later):
        return (True, True)
    return UNRESOLVED               # tool-name inequality establishes nothing


def d5_heuristic(rows, cond, q):
    V = norm(rows, cond)
    den = [e for e in V if e["status"] == "denied"]
    if not den:
        return (True, False)
    d = den[0]
    later = [e for e in V if e["t"] > d["t"] and e["status"] != "denied"]
    return (True, any(e["tool"] == d["tool"] for e in later))


# ---------------------------------------------------------------- D6
def d6_conservative(rows, cond, q):
    cand = q["candidate"]
    if cond == TYPED:
        acts = [r for r in rows if r.get("gen_ai.tool.name") in EFFECT_TOOLS
                and r.get("sec.capability.root")]
        if not acts:
            return UNRESOLVED
        return (True, acts[0]["sec.capability.root"] == cand)
    V = norm(rows, cond)
    roots = set()
    for e in V:
        if e["tool"] == "delegate" and "from=" in e["args"]:
            roots.add(e["args"].split("from=")[1].split()[0])
    if len(roots) != 1:
        return UNRESOLVED
    return (True, next(iter(roots)) == cand)


def d6_heuristic(rows, cond, q):
    return (True, True)             # the session initiator is assumed to be the authoriser


CONSERVATIVE = {"D1": d1_conservative, "D2": d2_conservative, "D3": d3_conservative,
                "D4": d4_conservative, "D5": d5_conservative, "D6": d6_conservative}
HEURISTIC = {"D1": d1_heuristic, "D2": d2_heuristic, "D3": d3_heuristic,
             "D4": d4_heuristic, "D5": d5_heuristic, "D6": d6_heuristic}

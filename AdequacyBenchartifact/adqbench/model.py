"""Core domain model: labelled values, capabilities, events, trajectories.

A trajectory is a deterministic, fully-observed simulation of an enterprise agent
session. Because we construct the world, every determination has a ground truth
that is known by construction rather than adjudicated after the fact.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Optional

PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED = 0, 1, 2, 3
CLASS_NAMES = {0: "public", 1: "internal", 2: "confidential", 3: "restricted"}
PROTECTED_FLOOR = CONFIDENTIAL


@dataclass(frozen=True)
class Label:
    """Information-flow label carried by a value. Joins on derivation."""
    classification: int
    tenants: frozenset
    sources: frozenset

    def join(self, other: "Label") -> "Label":
        return Label(
            classification=max(self.classification, other.classification),
            tenants=self.tenants | other.tenants,
            sources=self.sources | other.sources,
        )

    def declassify_to(self, level: int) -> "Label":
        return replace(self, classification=level)


@dataclass(frozen=True)
class Capability:
    """A grant of authority. Delegation forms a chain via parent."""
    cap_id: str
    principal: str
    scope: str
    valid_from: float
    valid_to: float
    parent: Optional[str]
    root: str

    def covers(self, scope: str, t: float) -> bool:
        return self.valid_from <= t <= self.valid_to and scope_subsumes(self.scope, scope)


def scope_subsumes(outer: str, inner: str) -> bool:
    """Dotted scope algebra: 'crm.*' subsumes 'crm.write'; '*' subsumes everything."""
    if outer == "*":
        return True
    if outer == inner:
        return True
    if outer.endswith(".*"):
        return inner.startswith(outer[:-1])
    return False


# Event kinds
RETRIEVE = "retrieve"
DERIVE = "derive"
DECLASSIFY = "declassify"
TOOL_READ = "tool_read"
TOOL_WRITE = "tool_write"
EXTERNAL_SEND = "external_send"
APPROVAL_REQUEST = "approval_request"
APPROVAL_GRANT = "approval_grant"
POLICY_ALLOW = "policy_allow"
POLICY_DENY = "policy_deny"
DELEGATE = "delegate"

EFFECTING = {TOOL_WRITE, EXTERNAL_SEND}


@dataclass
class Event:
    seq: int
    t: float
    kind: str
    tool: str = ""
    # value plumbing
    produces: Optional[str] = None
    consumes: tuple = ()
    doc_id: str = ""
    display_name: str = ""      # the human-visible name, the noisy proxy for sensitivity
    # authority plumbing
    principal: str = ""
    cap_id: str = ""
    scope: str = ""
    valid_to: float = 0.0
    parent_cap: Optional[str] = None
    # effect plumbing
    effect_sig: str = ""        # canonical signature of the real-world effect
    args_repr: str = ""
    status: str = "ok"          # ok | denied
    target_tenant: str = ""
    ref_seq: Optional[int] = None   # e.g. approval request referring to an action
    span_id: str = ""
    parent_span_id: Optional[str] = None
    turn: int = 0


@dataclass
class Trajectory:
    tid: str
    family: str
    events: list = field(default_factory=list)
    values: dict = field(default_factory=dict)        # value_id -> Label
    caps: dict = field(default_factory=dict)          # cap_id -> Capability
    session_tenant: str = ""
    session_principal: str = ""
    truth: dict = field(default_factory=dict)         # determination_id -> bool
    meta: dict = field(default_factory=dict)

    def n_steps(self) -> int:
        return len(self.events)

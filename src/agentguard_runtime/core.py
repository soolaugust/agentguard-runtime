from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
VALID_MODES = {"allow", "dry_run", "require_approval", "block"}


@dataclass(frozen=True)
class Evidence:
    source: str
    reference: str
    quote: str = ""
    confidence: float = 1.0

    def normalized_confidence(self) -> float:
        return min(1.0, max(0.0, float(self.confidence)))


@dataclass(frozen=True)
class ToolCall:
    name: str
    target: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)


@dataclass(frozen=True)
class AgentSpec:
    name: str
    owner: str
    purpose: str
    risk_level: str = "medium"
    mode_by_risk: dict[str, str] = field(default_factory=dict)
    allowed_tools: list[str] = field(default_factory=list)
    denied_targets: list[str] = field(default_factory=list)
    tool_risks: dict[str, str] = field(default_factory=dict)
    required_evidence: int = 1
    cost_budget_usd: float | None = None
    success_metrics: list[str] = field(default_factory=list)

    def mode_for(self, risk_level: str) -> str:
        mode = self.mode_by_risk.get(risk_level)
        if mode:
            return mode
        if risk_level == "low":
            return "allow"
        if risk_level == "medium":
            return "dry_run"
        if risk_level in {"high", "critical"}:
            return "require_approval"
        return "block"


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    mode: str
    risk_level: str
    reasons: list[str] = field(default_factory=list)
    evidence_score: float = 0.0


@dataclass(frozen=True)
class ExecutionReceipt:
    receipt_id: str
    agent: str
    tool: str
    target: str
    mode: str
    status: str
    reasons: list[str]
    evidence_score: float
    cost_usd: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class GovernanceReport:
    agent: str
    alive: bool
    value_state: str
    risk_state: str
    receipt_count: int
    approval_required_count: int
    blocked_count: int
    total_cost_usd: float
    evidence_score_avg: float
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_agent_spec(path: str | Path) -> AgentSpec:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if "agent" in raw:
        raw = raw["agent"]
    mode_by_risk = raw.get("mode_by_risk") or {}
    invalid_modes = set(mode_by_risk.values()) - VALID_MODES
    if invalid_modes:
        raise ValueError(f"invalid execution modes: {sorted(invalid_modes)}")
    risk_level = raw.get("risk_level", "medium")
    if risk_level not in RISK_ORDER:
        raise ValueError(f"invalid risk_level: {risk_level}")
    tool_risks = raw.get("tool_risks") or {}
    invalid_risks = set(tool_risks.values()) - set(RISK_ORDER)
    if invalid_risks:
        raise ValueError(f"invalid tool risks: {sorted(invalid_risks)}")
    return AgentSpec(
        name=raw["name"],
        owner=raw.get("owner", "unknown"),
        purpose=raw.get("purpose", ""),
        risk_level=risk_level,
        mode_by_risk=mode_by_risk,
        allowed_tools=list(raw.get("allowed_tools", [])),
        denied_targets=list(raw.get("denied_targets", [])),
        tool_risks=dict(tool_risks),
        required_evidence=int(raw.get("required_evidence", 1)),
        cost_budget_usd=raw.get("cost_budget_usd"),
        success_metrics=list(raw.get("success_metrics", [])),
    )


def infer_risk(spec: AgentSpec, call: ToolCall) -> str:
    if call.name in spec.tool_risks:
        return spec.tool_risks[call.name]
    mutating_markers = (
        "write",
        "update",
        "delete",
        "send",
        "post",
        "create",
        "merge",
        "deploy",
        "comment",
        "notify",
        "publish",
        "open_pr",
    )
    critical_markers = ("delete", "payment", "billing", "credential", "secret", "prod")
    haystack = " ".join([call.name, call.target, json.dumps(call.args, sort_keys=True)]).lower()
    if any(marker in haystack for marker in critical_markers):
        return "critical"
    if any(marker in haystack for marker in mutating_markers):
        return max(spec.risk_level, "high", key=lambda item: RISK_ORDER[item])
    return spec.risk_level


def evidence_score(evidence: list[Evidence], required: int) -> float:
    if required <= 0:
        return 1.0
    if not evidence:
        return 0.0
    confidence = sum(item.normalized_confidence() for item in evidence) / max(1, required)
    diversity = len({item.source for item in evidence}) / max(1, required)
    return min(1.0, 0.7 * confidence + 0.3 * diversity)


def _target_candidates(call: ToolCall) -> list[str]:
    candidates = [call.target]
    for key in ("target", "url", "path", "resource"):
        value = call.args.get(key)
        if isinstance(value, str):
            candidates.append(value)
    return [item for item in candidates if item]


def assess_tool_call(spec: AgentSpec, call: ToolCall) -> GuardDecision:
    reasons: list[str] = []
    if spec.allowed_tools and call.name not in spec.allowed_tools:
        reasons.append(f"tool_not_allowed:{call.name}")
    for pattern in spec.denied_targets:
        for target in _target_candidates(call):
            if fnmatch.fnmatch(target, pattern):
                reasons.append(f"target_denied:{pattern}")
                break
    score = evidence_score(call.evidence, spec.required_evidence)
    if score < 0.5:
        reasons.append(f"weak_evidence:{score:.2f}")
    risk_level = infer_risk(spec, call)
    mode = spec.mode_for(risk_level)
    if reasons and mode == "allow":
        mode = "dry_run"
    if any(reason.startswith(("tool_not_allowed", "target_denied")) for reason in reasons):
        mode = "block"
    return GuardDecision(
        allowed=mode in {"allow", "dry_run", "require_approval"},
        mode=mode,
        risk_level=risk_level,
        reasons=reasons or ["policy_passed"],
        evidence_score=score,
    )


def make_receipt(spec: AgentSpec, call: ToolCall, decision: GuardDecision, cost_usd: float = 0.0) -> ExecutionReceipt:
    payload = f"{spec.name}|{call.name}|{call.target}|{decision.mode}|{datetime.now(timezone.utc).isoformat()}"
    receipt_id = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    if decision.mode == "block":
        status = "blocked"
    elif decision.mode == "require_approval":
        status = "pending_approval"
    elif decision.mode == "dry_run":
        status = "dry_run"
    else:
        status = "executed"
    return ExecutionReceipt(
        receipt_id=receipt_id,
        agent=spec.name,
        tool=call.name,
        target=call.target,
        mode=decision.mode,
        status=status,
        reasons=decision.reasons,
        evidence_score=decision.evidence_score,
        cost_usd=cost_usd,
    )


def record_receipt(receipt: ExecutionReceipt, store: str | Path) -> Path:
    from agentguard_runtime.stores import open_receipt_store

    store_path = Path(store)
    open_receipt_store(store_path).append(receipt)
    return store_path


def read_receipts(store: str | Path) -> list[ExecutionReceipt]:
    from agentguard_runtime.stores import open_receipt_store

    return open_receipt_store(store).read_all()


def build_report(spec: AgentSpec, receipts: list[ExecutionReceipt]) -> GovernanceReport:
    if not receipts:
        return GovernanceReport(
            agent=spec.name,
            alive=False,
            value_state="no_receipts",
            risk_state="unknown",
            receipt_count=0,
            approval_required_count=0,
            blocked_count=0,
            total_cost_usd=0.0,
            evidence_score_avg=0.0,
        )
    total_cost = sum(item.cost_usd for item in receipts)
    approval_count = sum(1 for item in receipts if item.status == "pending_approval")
    blocked_count = sum(1 for item in receipts if item.status == "blocked")
    evidence_avg = sum(item.evidence_score for item in receipts) / len(receipts)
    if spec.cost_budget_usd is not None and total_cost > spec.cost_budget_usd:
        value_state = "over_budget"
    elif evidence_avg < 0.5:
        value_state = "weak_evidence"
    else:
        value_state = "measurable"
    if blocked_count:
        risk_state = "blocked_actions"
    elif approval_count:
        risk_state = "approval_gated"
    else:
        risk_state = "controlled"
    return GovernanceReport(
        agent=spec.name,
        alive=True,
        value_state=value_state,
        risk_state=risk_state,
        receipt_count=len(receipts),
        approval_required_count=approval_count,
        blocked_count=blocked_count,
        total_cost_usd=round(total_cost, 6),
        evidence_score_avg=round(evidence_avg, 3),
    )

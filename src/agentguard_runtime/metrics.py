from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from agentguard_runtime.core import ExecutionReceipt


@dataclass(frozen=True)
class MetricsScorecard:
    agent: str
    proposed_actions: int
    executed_count: int
    dry_run_count: int
    approval_required_count: int
    blocked_count: int
    failed_count: int
    total_cost_usd: float
    evidence_quality_avg: float
    approval_burden_rate: float
    blocked_action_rate: float
    control_state: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_scorecard(agent: str, receipts: list[ExecutionReceipt]) -> MetricsScorecard:
    proposed = len(receipts)
    if proposed == 0:
        return MetricsScorecard(
            agent=agent,
            proposed_actions=0,
            executed_count=0,
            dry_run_count=0,
            approval_required_count=0,
            blocked_count=0,
            failed_count=0,
            total_cost_usd=0.0,
            evidence_quality_avg=0.0,
            approval_burden_rate=0.0,
            blocked_action_rate=0.0,
            control_state="no_data",
        )

    executed = sum(1 for item in receipts if item.status == "executed")
    dry_run = sum(1 for item in receipts if item.status == "dry_run")
    approval = sum(1 for item in receipts if item.status == "pending_approval")
    blocked = sum(1 for item in receipts if item.status == "blocked")
    failed = sum(1 for item in receipts if item.status == "failed")
    total_cost = sum(item.cost_usd for item in receipts)
    evidence_avg = sum(item.evidence_score for item in receipts) / proposed
    approval_rate = approval / proposed
    blocked_rate = blocked / proposed

    if evidence_avg < 0.5:
        state = "weak_evidence"
    elif blocked_rate >= 0.5:
        state = "noisy"
    elif approval_rate >= 0.5:
        state = "review_heavy"
    else:
        state = "measuring_control"

    return MetricsScorecard(
        agent=agent,
        proposed_actions=proposed,
        executed_count=executed,
        dry_run_count=dry_run,
        approval_required_count=approval,
        blocked_count=blocked,
        failed_count=failed,
        total_cost_usd=round(total_cost, 6),
        evidence_quality_avg=round(evidence_avg, 3),
        approval_burden_rate=round(approval_rate, 3),
        blocked_action_rate=round(blocked_rate, 3),
        control_state=state,
    )

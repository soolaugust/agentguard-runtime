from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from agentguard_runtime.core import ExecutionReceipt, GovernanceReport


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


def render_markdown_summary(report: GovernanceReport, scorecard: MetricsScorecard) -> str:
    verdict = _verdict(scorecard)
    lines = [
        f"# AgentGuard Summary — {scorecard.agent}",
        "",
        f"Generated at: `{scorecard.generated_at}`",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        "## Governance Report",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Alive | `{report.alive}` |",
        f"| Value state | `{report.value_state}` |",
        f"| Risk state | `{report.risk_state}` |",
        f"| Receipts | `{report.receipt_count}` |",
        f"| Approval required | `{report.approval_required_count}` |",
        f"| Blocked | `{report.blocked_count}` |",
        f"| Total cost | `${report.total_cost_usd:.6f}` |",
        f"| Evidence average | `{report.evidence_score_avg:.3f}` |",
        "",
        "## Metrics Scorecard",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Proposed actions | `{scorecard.proposed_actions}` |",
        f"| Executed | `{scorecard.executed_count}` |",
        f"| Dry-run | `{scorecard.dry_run_count}` |",
        f"| Pending approval | `{scorecard.approval_required_count}` |",
        f"| Blocked | `{scorecard.blocked_count}` |",
        f"| Failed | `{scorecard.failed_count}` |",
        f"| Approval burden rate | `{scorecard.approval_burden_rate:.1%}` |",
        f"| Blocked action rate | `{scorecard.blocked_action_rate:.1%}` |",
        f"| Evidence quality average | `{scorecard.evidence_quality_avg:.3f}` |",
        f"| Control state | `{scorecard.control_state}` |",
        "",
        "## What This Means",
        "",
        *_interpretation(scorecard),
        "",
        "## What This Does Not Prove",
        "",
        "This v0.1 summary measures runtime control. It does not prove business value until approval and outcome events are ingested.",
    ]
    return "\n".join(lines) + "\n"


def _verdict(scorecard: MetricsScorecard) -> str:
    if scorecard.control_state == "no_data":
        return "No receipts yet. The agent is not measurable."
    if scorecard.control_state == "weak_evidence":
        return "Actions are poorly grounded. Improve evidence before increasing autonomy."
    if scorecard.control_state == "noisy":
        return "Many actions are blocked. Tighten upstream prompts, scopes, or tool access."
    if scorecard.control_state == "review_heavy":
        return "The agent is controlled but review-heavy. Improve evidence or narrow high-risk actions before auto-execution."
    return "The agent is producing governed actions with manageable control metrics. Continue collecting approval and outcome data."


def _interpretation(scorecard: MetricsScorecard) -> list[str]:
    if scorecard.proposed_actions == 0:
        return ["- No proposed actions crossed the runtime boundary."]
    items = [
        f"- `{scorecard.proposed_actions}` proposed action(s) crossed the runtime boundary.",
        f"- `{scorecard.approval_required_count}` action(s) require approval; this is `{scorecard.approval_burden_rate:.1%}` of proposed actions.",
        f"- `{scorecard.blocked_count}` action(s) were blocked; this is `{scorecard.blocked_action_rate:.1%}` of proposed actions.",
        f"- Evidence quality averaged `{scorecard.evidence_quality_avg:.3f}` on a 0-1 scale.",
        f"- Total recorded cost is `${scorecard.total_cost_usd:.6f}`.",
    ]
    if scorecard.approval_burden_rate >= 0.5:
        items.append("- Review burden is high; this may be acceptable for risky actions but is not yet efficient automation.")
    if scorecard.blocked_action_rate >= 0.5:
        items.append("- Block rate is high; inspect whether policies are protecting you or the agent is proposing too many bad actions.")
    return items

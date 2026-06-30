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


def render_markdown_summary(
    report: GovernanceReport,
    scorecard: MetricsScorecard,
    language: str = "en",
) -> str:
    if language == "zh":
        return _render_markdown_summary_zh(report, scorecard)
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


def _render_markdown_summary_zh(report: GovernanceReport, scorecard: MetricsScorecard) -> str:
    lines = [
        f"# AgentGuard 摘要报告 — {scorecard.agent}",
        "",
        f"生成时间：`{scorecard.generated_at}`",
        "",
        "## 结论",
        "",
        _verdict_zh(scorecard),
        "",
        "## 治理报告",
        "",
        "| 字段 | 数值 |",
        "| --- | --- |",
        f"| 是否有数据 | `{report.alive}` |",
        f"| 价值状态 | `{_state_label_zh(report.value_state)}` |",
        f"| 风险状态 | `{_state_label_zh(report.risk_state)}` |",
        f"| 收据数量 | `{report.receipt_count}` |",
        f"| 需要审批 | `{report.approval_required_count}` |",
        f"| 已阻断 | `{report.blocked_count}` |",
        f"| 总成本 | `${report.total_cost_usd:.6f}` |",
        f"| 平均证据分 | `{report.evidence_score_avg:.3f}` |",
        "",
        "## 指标看板",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 提议动作数 | `{scorecard.proposed_actions}` |",
        f"| 已执行 | `{scorecard.executed_count}` |",
        f"| Dry-run | `{scorecard.dry_run_count}` |",
        f"| 待审批 | `{scorecard.approval_required_count}` |",
        f"| 已阻断 | `{scorecard.blocked_count}` |",
        f"| 失败 | `{scorecard.failed_count}` |",
        f"| 审批负担率 | `{scorecard.approval_burden_rate:.1%}` |",
        f"| 阻断率 | `{scorecard.blocked_action_rate:.1%}` |",
        f"| 平均证据质量 | `{scorecard.evidence_quality_avg:.3f}` |",
        f"| 控制状态 | `{_state_label_zh(scorecard.control_state)}` |",
        "",
        "## 这说明什么",
        "",
        *_interpretation_zh(scorecard),
        "",
        "## 这不能证明什么",
        "",
        "这份 v0.1 报告只能证明 AgentGuard 已经在衡量运行时控制面，不能证明业务价值。要证明业务价值，还需要接入审批事件和结果事件。",
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


def _verdict_zh(scorecard: MetricsScorecard) -> str:
    if scorecard.control_state == "no_data":
        return "还没有收据数据，当前 Agent 不可衡量。"
    if scorecard.control_state == "weak_evidence":
        return "动作证据不足。提高证据质量之前，不建议提升自动化等级。"
    if scorecard.control_state == "noisy":
        return "大量动作被阻断。需要收紧上游提示词、权限范围或工具访问策略。"
    if scorecard.control_state == "review_heavy":
        return "Agent 已被运行时控制住，但审批负担偏高。自动执行前应先提高证据质量或缩小高风险动作范围。"
    return "Agent 正在产生可治理的动作，控制指标可接受。下一步应继续采集审批和结果数据。"


def _interpretation_zh(scorecard: MetricsScorecard) -> list[str]:
    if scorecard.proposed_actions == 0:
        return ["- 没有动作进入运行时边界。"]
    items = [
        f"- `{scorecard.proposed_actions}` 个提议动作进入了运行时边界。",
        f"- `{scorecard.approval_required_count}` 个动作需要审批，占全部提议动作的 `{scorecard.approval_burden_rate:.1%}`。",
        f"- `{scorecard.blocked_count}` 个动作被阻断，占全部提议动作的 `{scorecard.blocked_action_rate:.1%}`。",
        f"- 平均证据质量为 `{scorecard.evidence_quality_avg:.3f}`，取值范围是 0 到 1。",
        f"- 已记录总成本为 `${scorecard.total_cost_usd:.6f}`。",
    ]
    if scorecard.approval_burden_rate >= 0.5:
        items.append("- 审批负担偏高；对于高风险动作这是可以接受的，但还不能算高效自动化。")
    if scorecard.blocked_action_rate >= 0.5:
        items.append("- 阻断率偏高；需要判断这是策略在保护系统，还是 Agent 上游提出了太多无效动作。")
    return items


def _state_label_zh(state: str) -> str:
    return {
        "no_data": "无数据",
        "measurable": "可衡量",
        "over_budget": "超预算",
        "weak_evidence": "证据不足",
        "measuring_control": "正在衡量控制面",
        "measuring_value": "正在衡量价值",
        "valuable": "有价值",
        "noisy": "噪声偏高",
        "too_expensive": "成本过高",
        "too_risky": "风险过高",
        "unknown": "未知",
        "controlled": "已受控",
        "approval_gated": "审批门控",
        "blocked_actions": "存在阻断动作",
        "review_heavy": "审批负担偏高",
    }.get(state, state)

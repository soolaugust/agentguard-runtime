from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from agentguard_runtime.core import (
    AgentSpec,
    Evidence,
    ToolCall,
    assess_tool_call,
    make_receipt,
    record_receipt,
)

ToolExecutor = Callable[[ToolCall], Any]
ApprovalRequester = Callable[[ToolCall, dict[str, Any]], Any]


class GovernedToolRunner:
    """Framework-neutral wrapper for tool execution.

    The wrapper deliberately does not execute blocked or approval-gated actions.
    Callers decide how to present approvals and how to resume execution after approval.
    """

    def __init__(
        self,
        spec: AgentSpec,
        receipts_path: str | Path,
        executor: ToolExecutor | None = None,
        approval_requester: ApprovalRequester | None = None,
    ):
        self.spec = spec
        self.receipts_path = Path(receipts_path)
        self.executor = executor
        self.approval_requester = approval_requester

    def run(self, call: ToolCall, cost_usd: float = 0.0) -> dict[str, Any]:
        decision = assess_tool_call(self.spec, call)
        receipt = make_receipt(self.spec, call, decision, cost_usd=cost_usd)
        record_receipt(receipt, self.receipts_path)

        output: Any = None
        if decision.mode == "allow" and self.executor:
            output = self.executor(call)
        elif decision.mode == "require_approval" and self.approval_requester:
            output = self.approval_requester(call, asdict(receipt))

        return {
            "decision": asdict(decision),
            "receipt": asdict(receipt),
            "output": output,
        }


def from_openai_style_tool_call(data: dict[str, Any]) -> ToolCall:
    """Convert an OpenAI/MCP-like tool-call dict into AgentGuard's neutral shape."""
    function = data.get("function") or {}
    args = function.get("arguments") or data.get("arguments") or {}
    if isinstance(args, str):
        args = {"raw_arguments": args}
    target = data.get("target") or args.get("target") or args.get("url") or args.get("path") or ""
    evidence_items = data.get("evidence", [])
    evidence = [Evidence(**item) for item in evidence_items]
    return ToolCall(
        name=function.get("name") or data.get("name") or data.get("tool") or "unknown",
        target=str(target),
        args=dict(args),
        evidence=evidence,
    )

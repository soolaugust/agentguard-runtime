"""AgentGuard Runtime: reliability and governance primitives for AI agents."""

from agentguard_runtime.adapters import GovernedToolRunner, from_openai_style_tool_call
from agentguard_runtime.metrics import MetricsScorecard, build_scorecard, render_markdown_summary
from agentguard_runtime.schema import (
    validate_action_receipt,
    validate_approval_event,
    validate_governance_report,
    validate_outcome_event,
)
from agentguard_runtime.stores import JsonlReceiptStore, SQLiteReceiptStore, open_receipt_store
from agentguard_runtime.core import (
    AgentSpec,
    Evidence,
    ExecutionReceipt,
    GovernanceReport,
    GuardDecision,
    ToolCall,
    assess_tool_call,
    build_report,
    load_agent_spec,
    record_receipt,
)

__all__ = [
    "GovernedToolRunner",
    "from_openai_style_tool_call",
    "JsonlReceiptStore",
    "SQLiteReceiptStore",
    "open_receipt_store",
    "MetricsScorecard",
    "build_scorecard",
    "render_markdown_summary",
    "validate_action_receipt",
    "validate_approval_event",
    "validate_governance_report",
    "validate_outcome_event",
    "AgentSpec",
    "Evidence",
    "ExecutionReceipt",
    "GovernanceReport",
    "GuardDecision",
    "ToolCall",
    "assess_tool_call",
    "build_report",
    "load_agent_spec",
    "record_receipt",
]

__version__ = "0.1.0"

"""AgentGuard Runtime: reliability and governance primitives for AI agents."""

from agentguard_runtime.adapters import GovernedToolRunner, from_openai_style_tool_call
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

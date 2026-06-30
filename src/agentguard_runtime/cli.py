from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agentguard_runtime.core import (
    Evidence,
    ToolCall,
    assess_tool_call,
    build_report,
    load_agent_spec,
    make_receipt,
)
from agentguard_runtime.stores import open_receipt_store


def _load_call(path: str | Path) -> ToolCall:
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    evidence = [Evidence(**item) for item in data.get("evidence", [])]
    return ToolCall(
        name=data["name"],
        target=data.get("target", ""),
        args=data.get("args", {}),
        evidence=evidence,
    )


def cmd_check(args: argparse.Namespace) -> int:
    spec = load_agent_spec(args.agent)
    call = _load_call(args.call)
    decision = assess_tool_call(spec, call)
    receipt = make_receipt(spec, call, decision, cost_usd=args.cost)
    if args.receipts:
        open_receipt_store(args.receipts, args.store_format).append(receipt)
    print(json.dumps({"decision": decision.__dict__, "receipt": receipt.__dict__}, ensure_ascii=False, indent=2))
    return 2 if decision.mode == "block" else 0


def cmd_report(args: argparse.Namespace) -> int:
    spec = load_agent_spec(args.agent)
    receipts = open_receipt_store(args.receipts, args.store_format).read_all()
    report = build_report(spec, receipts)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentguard",
        description="Reliability and governance runtime for AI agent tool calls.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Assess a tool call and optionally write a receipt.")
    check.add_argument("--agent", required=True, help="Path to agent.yaml")
    check.add_argument("--call", required=True, help="Path to a tool call JSON file")
    check.add_argument("--receipts", help="Receipt store to append to")
    check.add_argument(
        "--store-format",
        choices=("jsonl", "sqlite"),
        default="jsonl",
        help="Receipt store format",
    )
    check.add_argument("--cost", type=float, default=0.0, help="Observed cost for this call")
    check.set_defaults(func=cmd_check)

    report = sub.add_parser("report", help="Summarize receipts into an agent governance report.")
    report.add_argument("--agent", required=True, help="Path to agent.yaml")
    report.add_argument("--receipts", required=True, help="Receipt store")
    report.add_argument(
        "--store-format",
        choices=("jsonl", "sqlite"),
        default="jsonl",
        help="Receipt store format",
    )
    report.set_defaults(func=cmd_report)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

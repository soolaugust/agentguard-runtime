# Contributing

AgentGuard Runtime is intentionally small. Contributions should preserve the project boundary: deterministic governance around agent actions, not a new agent framework.

## Useful contributions

- Framework adapters for LangGraph, OpenHands, LiteLLM, Claude Code, Codex CLI, or MCP tools.
- Policy examples for common tool types: GitHub, Git, CI, Jira, Slack, deployment, filesystem.
- Receipt exporters for OpenTelemetry, JSONL, SQLite, or object storage.
- Tests that reproduce real agent failure modes.
- Documentation based on public issues, postmortems, or production lessons.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
agentguard check --agent examples/agent.yaml --call examples/tool_call.json --receipts .agentguard/receipts.jsonl
```

## Design bar

A feature belongs here if it answers one of these questions:

- Should this agent action be allowed?
- What evidence supports this action?
- Who needs to approve it?
- What did it cost?
- Did it leave a receipt?
- Is the agent still alive and useful?

If it mainly improves prompting, planning, memory, or model quality, it probably belongs in an agent framework instead.

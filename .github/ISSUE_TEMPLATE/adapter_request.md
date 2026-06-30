---
name: Adapter request
about: Request an adapter for an agent framework, gateway, or tool runtime
title: "Adapter: "
labels: adapter
---

## Target runtime

Examples: LangGraph, LiteLLM, OpenHands, Claude Code, Codex CLI, MCP server, custom tool runner.

## Tool call boundary

Where can AgentGuard intercept the proposed action before external state changes?

## Required policy signals

- Agent identity:
- Tool name:
- Target/resource:
- Evidence/provenance:
- Cost signal:
- Approval state:

## Example action

```json
{
  "name": "github.comment_issue",
  "target": "owner/repo#123",
  "args": {},
  "evidence": []
}
```

## Expected decision

Choose one: `allow`, `dry_run`, `require_approval`, `block`.

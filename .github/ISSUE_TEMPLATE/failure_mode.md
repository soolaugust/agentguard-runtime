---
name: Agent failure mode
about: Report a real agent failure mode that should become a deterministic guard
title: "Failure mode: "
labels: failure-mode
---

## What happened?

Describe the agent action and why it was unsafe, unauditable, too costly, or not useful.

## What should have stopped it?

- Missing evidence
- Denied target
- Approval required
- Budget exceeded
- Tool not allowed
- Other:

## Minimal reproduction

Provide an `agent.yaml` and `tool_call.json` if possible.

## Expected receipt/report

What should AgentGuard record so the failure can be audited later?

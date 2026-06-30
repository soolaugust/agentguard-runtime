# CLI Hook Adapter Sketch

AgentGuard can be used with local coding agents by wrapping dangerous tools before they mutate external state.

## Pattern

1. Agent proposes a tool call as JSON.
2. Hook runs `agentguard check`.
3. Hook allows, dry-runs, pauses for approval, or blocks.
4. Hook stores the receipt.
5. A later job runs `agentguard report`.

```bash
agentguard check \
  --agent agent.yaml \
  --call proposed_tool_call.json \
  --receipts .agentguard/receipts.jsonl \
  --cost "$OBSERVED_COST_USD"
```

## Recommended hook points

- Before GitHub comments, PR creation, issue edits, or releases.
- Before filesystem writes outside the repository root.
- Before CI/deploy operations.
- Before Jira, Slack, email, or ticketing writes.
- Before any action touching secrets, auth, billing, payment, or production resources.

## Why local hooks matter

Many useful agents start as local CLIs before becoming platforms. Receipts give those agents an audit trail before teams have a full LLMOps stack.

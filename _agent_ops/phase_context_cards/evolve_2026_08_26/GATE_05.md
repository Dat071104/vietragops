# Gate 05 — Provider Router and MCP Platform

**Status:** `PASS` (see `gates/results/GATE_05_RESULT.md`; committed as
`81589e2` and pushed to `origin/main` alongside Gate 06)

**Source:** `gates/GATE_05_PROVIDER_AND_MCP_PLATFORM.md`

## Objective

Separate development/demo/research provider modes and add an approved local MCP
surface with typed provider failures and security controls.

## Non-Negotiables

- Research mode has no silent fallback; model/provider and timeout/429/network
  state are visible in traces.
- MCP stays localhost-only during Gates with origin validation, auth, scopes and
  audit. Test unauthorized operations.
- No public unauthenticated MCP, raw MarkItDown exposure, or multi-account quota
  striping logic.

## Exit

Write `GATE_05_RESULT.md`; STOP.

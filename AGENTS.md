# AGENTS.md — job-hunting-hub

> **Docs-first gate (fastmcp-docs-first):** No `src/` edit without `docs/research/T-job-hub-fastmcp.md` + `docs/superpowers/specs/2026-09-01-job-hub-design.md` + this plan covering ALL links. Violation = delete code.

## Start Here (fresh session)

1. Read `docs/superpowers/plans/2026-09-01-job-hub-plan.md` — this is the single source of truth (8 tasks, TDD, `uv run pytest -m "not live"` + `ruff` + `mypy --strict` trio).
2. Read `docs/research/T-job-hub-fastmcp.md` (7/7 FastMCP concepts) and `docs/superpowers/specs/2026-09-01-job-hub-design.md` (5 sections: architecture, DB, flow, auth, RAG).
3. Read `fastmcp-engineering` at `/Users/laptop/.local/share/opencode/repos/github.com/evgenygurin/fastmcp-engineering@main` or `https://gofastmcp.com/llms.txt` for versioned API.
4. Follow `fastmcp-engineering` workflow maximally where it gives value: `Research → Contracts (Pydantic v2) → Architecture Governor → TDD → Verification`. Skip where it adds no value (GraphRAG, 15 OAuth providers).

## Workflow Invariants

- `fastmcp>=3.2,<4` (exact `3.4.7` in lock), `pydantic>=2.12` for v4, `python>=3.12`, `uv`
- `TDD`: RED failing test → GREEN minimal impl → trio green before next Task
- `GitNexus`: `impact(target, direction:"upstream")` before any symbol edit; `detect_changes()` before commit
- `Result[T]` contract `Ok[T]|Err` discriminated, `TypeAdapter` fixtures

## Group

This repo is part of `job-hub` GitNexus group: `hh-mcp-pro`, `fastmcp-engineering`, `job-hunting`, `telegram-mcp`, `linkedin-mcp-server`, `mcp-server-neon`, `job-hunting-hub` (7 repos, `gitnexus group status job-hub`)

## Skills

Use `fastmcp-docs-first`, `fastmcp-research-loop`, `hh-mcp-tdd-cycle`, `hh-mcp-verification` when implementing.


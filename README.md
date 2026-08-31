# job-hunting-hub

FastMCP Hub for job hunting — aggregates `hh-mcp-pro` + `linkedin-mcp-server` + `telegram-mcp` via `mount(create_proxy, namespace)`, with Neon Lakebase `companies→recruiters→contacts→interactions` + plain RAG (`pgvector` + `lakebase_text`) + HITL `Approval`.

`fastmcp>=3.2,<4` pinned `3.4.7`, `pydantic>=2.12`, Python 3.12, `uv`.

## For AI Agents (fresh session)

**Single source of truth:** `docs/superpowers/plans/2026-09-01-job-hub-plan.md` — 8 tasks, TDD, `fastmcp-engineering` maximally where valuable.

**Required reading before code:**
1. `docs/research/T-job-hub-fastmcp.md` (7/7 FastMCP: composition/proxy/custom/tool-search/visibility/lifespan/tasks+apps)
2. `docs/superpowers/specs/2026-09-01-job-hub-design.md` (5 sections: architecture, DB, flow `vacancy→TG`, auth, RAG)
3. `AGENTS.md` — workflow invariants, group `job-hub` (7 repos)

**Context pack:** Telegram SpamBot `30-80 DMs/день`, `datacenter IP + молодой акк = бан`, LinkedIn `note 120-180 chars / DM 50-90 слов / 1 follow-up 7-10д`, `GraphRAG 10-100× дороже plain RAG` — детали в `docs/research/T-job-hub-fastmcp.md` Contradictions.

Run: `uv sync && uv run pytest -m "not live" -v && uv run ruff check src tests && uv run mypy src --strict`

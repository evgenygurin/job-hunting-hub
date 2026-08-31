# job-hunting-hub

FastMCP Hub for job hunting — aggregates `hh-mcp-pro` + `linkedin-mcp-server` + `telegram-mcp` via `mount(create_proxy, namespace)`, with Neon Lakebase `companies→recruiters→contacts→interactions` + plain RAG (`pgvector` + `lakebase_text`) + HITL `Approval`.

`fastmcp>=3.2,<4` pinned `3.4.7`, `pydantic>=2.12`, Python 3.12, `uv`.

See `docs/research/T-job-hub-fastmcp.md` and `docs/superpowers/specs/2026-09-01-job-hub-design.md` in `hh-mcp-pro` for research & design.

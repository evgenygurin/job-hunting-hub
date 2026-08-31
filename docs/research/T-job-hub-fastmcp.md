# T-job-hub Research — FastMCP capabilities for job-hunting-hub
Date: 2026-09-01
Links: 7/7 studied (list all URLs, mark ✅/❌)

| # | Title | URL | Status |
|---|-------|-----|--------|
| 1 | Composing Servers (mount / import_server) | https://gofastmcp.com/servers/composition.md | ✅ |
| 2 | MCP Proxy Provider (create_proxy, session isolation, caching) | https://gofastmcp.com/servers/providers/proxy.md | ✅ |
| 3 | Custom Providers (Provider._list_tools, lifespan) | https://gofastmcp.com/servers/providers/custom.md | ✅ |
| 4 | Tool Search (Regex/BM25 synthetic search_tools/call_tool) | https://gofastmcp.com/servers/transforms/tool-search.md | ✅ |
| 5 | Component Visibility (enable/disable, tags, per-session) | https://gofastmcp.com/servers/visibility.md | ✅ |
| 6 | Lifespans (composable | ) | https://gofastmcp.com/servers/lifespan.md | ✅ |
| 7 | Background Tasks + Apps (Approval/Choice/Form, Sampling/Elicitation) | https://gofastmcp.com/servers/tasks.md + https://gofastmcp.com/apps/providers/approval.md | ✅ |

## Concepts Studied
| # | Title | context7 key finding | exa verified? | gitnexus mapping |
|---|-------|----------------------|---------------|------------------|
| 1 | Composition `mount` vs `import_server` | `mount(server, namespace)` live link, delegated at runtime; `import_server` static copy. `mount(namespace="hh")` → `hh_search_vacancies`, namespacing via Transforms. Direct mount = in-memory call (no lifespan), `as_proxy=True` = via Client + lifespan executed. Auto `as_proxy` when child has custom lifespan. | ✅ gofastmcp.com/servers/composition.md verified: live link, prefix table, performance 1-2ms vs 300-400ms for HTTP, tag filtering recursively. | `hh-mcp-pro` uses single LocalProvider only (`composition.py`), no mount. `src/hh_mcp_pro/server.py:139-146` `mcp = FastMCP(lifespan=...)` without mounts. Gap: hub needs mount. |
| 2 | Proxy `create_proxy` | `create_proxy(target: Url|Path|MCPConfig|Client|FastMCP) -> FastMCPProxy`. Lazy bridge, session isolation per-request (recommended), shared session if passed connected Client (risk context mixing). Forwards sampling/elicitation/logging/progress. `provider_error_strategy="warn"` default. Multi-server config auto-namespaces. `ProxyProvider cache_ttl=300` for list_*; `cache_ttl=0` disable. Session reuse via factory for stateless HTTP. Era mirroring modern 2026-07-28 vs legacy handshake. | ✅ gofastmcp.com/servers/providers/proxy.md verified: diagram, bridging, lazy, caching, session reuse with `ProxyClient.new()`. | `hh-mcp-pro` has no proxy. `~/.config/opencode/opencode.json` uses remote `neon` via `https://mcp.neon.tech/mcp`, but hh-mcp-pro itself is stdio local `uv --directory ... run hh-mcp-pro`. Hub must proxy `linkedin-mcp-search` (npx), `telegram-mcp` (uv). |
| 3 | Custom Provider | Subclass `Provider`, implement `_list_tools/_list_resources/_list_prompts` returning `Sequence[Tool]`. `Tool.from_function(fn, name, description)` schema from hints+docstring. `providers=[DatabaseProvider(db_url)]` or `add_provider()`. `lifespan` via `@asynccontextmanager` for db pool. Provider vs Middleware: sourcing vs per-request filtering. | ✅ gofastmcp.com/servers/providers/custom.md verified: DictProvider, DatabaseProvider, ApiResourceProvider with httpx lifespan, registration. | `hh-mcp-pro` uses only `LocalProvider` via `@mcp.tool` decorators (`api/*.py`, `server.py`). No custom DB provider. Opportunity for `ContactsProvider(db_url)` to expose `contacts_search` dynamically from Neon/Supabase. |
| 4 | Tool Search | Replace large catalog (70+ tools) with synthetic `search_tools(pattern|query)` + `call_tool(name, args)`. Regex (0 overhead) vs BM25 (relevance ranked, lazy index, hash staleness). Config `max_results` (default 5), `always_visible`, `search_tool_name`. Auth/visibility respected, app-only tools excluded. Proxy respects pipeline. | ✅ gofastmcp.com/servers/transforms/tool-search.md verified: two synthetic tools, limits, pinning, call_tool proxy, visibility filtering. | `hh-mcp-pro` has 43 tools (`README.md:113`) without search. Hub will have 70+ aggregated → must enable `BM25SearchTransform` or `RegexSearchTransform`. No current usage. |
| 5 | Visibility | `enable(tags|names|keys|version, only=True)` / `disable(...)` layered: provider transforms first, server final. `only=True` = allowlist mode (clear previous). Later calls override earlier on overlap. Per-session `ctx.enable_components/tags` + `ctx.disable_components` + `ctx.reset_visibility()` with notifications `ToolListChanged`. Namespace activation pattern: `tags={"namespace:finance"}` disabled globally, enabled per-session via tool. | ✅ gofastmcp.com/servers/visibility.md verified: names/tags/keys/version/combine, ordering, provider vs server, per-session, namespace activation. | `hh-mcp-pro` uses tags for `visibility test` but no allowlist for hub. Gap: hub must `disable(tags={"internal"})` server-level, and per-user `enable_components` for `tg` after auth. |
| 6 | Lifespans | `@lifespan async def app_lifespan(server): yield {"pool": pool}` via `try/finally`. `lifespan_context` via `ctx.lifespan_context`. Composition `config_lifespan | db_lifespan` enter left→right, exit right→left, dict merge later overwrites. Legacy `@asynccontextmanager` works, wrap `ContextManagerLifespan` for composition. `combine_lifespans` for FastAPI. | ✅ gofastmcp.com/servers/lifespan.md verified: basic, composing |, backwards compat, FastAPI. | `hh-mcp-pro` `server.py:118` `config_lifespan` + OTEL lifespan composed, tested `test_t6_lifespan.py:3`. Pattern reusable for hub `db_lifespan | telegram_lifespan | hh_client_lifespan`. |
| 7 | Background Tasks + Apps | `@mcp.tool(task=True)` with `Progress` (`set_total/increment/set_message`), `CurrentDocket/CurrentWorker`. Client `call_tool_task` + `task.status()` async. Apps: `FastMCPApp`, `Approval`, `Choice`, `FormInput`, `FileUpload` (`fastmcp[apps]` + `prefab-ui`) for HITL. `Sampling` via `ctx.sample` (v3) or guard modern era, `Elicitation` for structured user input. `Progress` injection works foreground + Docket worker. | ✅ gofastmcp.com/servers/tasks.md + apps/providers/approval.md verified: progress example, docket/worker, client tasks, approval request_approval(summary,details,title,approve_variant). | `hh-mcp-pro` has `apply_two_step` two-step but no `task=True` long-running; Apps `team_directory` exists (`server.py` apps/prefab). Hub needs `task=True` for `hh→li→tg` chain (LinkedIn 5-7s) + `Approval` for `tg_send_message`. |

## What Applies to hh-mcp-pro / job-hunting-hub
- **Hub architecture**: `hub = FastMCP("job-hub", lifespan=db_lifespan|tg_lifespan|hh_lifespan)`; `hub.mount(create_proxy(hh_server, namespace="hh"))`, `hub.mount(create_proxy(li_config, namespace="li"))`, `hub.mount(create_proxy(tg_config, namespace="tg"))`. Namespace prevents `get_data` collision, dynamic updates immediate.
- **Contacts DB as CustomProvider**: `ContactsProvider(Neon DATABASE_URL)` implementing `_list_tools` returning `Tool.from_function(contacts_search)` + `_list_resources` for `contacts://{id}`; lifespan manages `asyncpg` pool; avoids 43 static `@mcp.tool` for each recruiter.
- **Tool Search mandatory**: Hub 70+ tools → `BM25SearchTransform(max_results=5, always_visible=["contacts_search","hub_health"])` pinned. LLM discovers via `search_tools(query="telegram recruiter")` not full catalog.
- **Visibility for compliance**: `hub.disable(tags={"internal","dangerous"})` server-level; per-session `await ctx.enable_components(tags={"tg:send"})` after user auth; namespace activation `tags={"namespace:tg"}` disabled globally.
- **Lifespan composition**: Reuse `hh-mcp-pro` pattern `config_lifespan | data_lifespan`; Neon pool `DATABASE_URL` from `neon deploy` injected; Telegram `Client` session.
- **HITL for outreach**: `request_approval(summary="Send to @recruiter 180 chars", details=campaign)` before `tg_send_message`; `Choice` for `tailor/skip`; `FormInput` for `resume_id`; `Progress` for batch `contacts_enrich 50 companies`.

## Contradictions / Gaps vs Current Implementation
- `src/hh_mcp_pro/server.py:139` uses `FastMCP(lifespan=...)` without mounts; docs recommend `mount` for modular boundary, not monolithic 43 tools. Gap: hub must split.
- Current no proxy: `hh-mcp-pro` STDIO only; docs `create_proxy` lazy + `cache_ttl` not used → hub latency 300-400ms per mount not accounted in current tests.
- `pyproject.toml:10` `fastmcp>=3.2,<4` pinned 3.4.7; docs `upgrading/from-fastmcp-3.mdx` requires `pydantic>=2.12` for v4 (hub should pin `>=2.12`). `hh-mcp-pro` defers to `docs/notes/fastmcp-json-deferred.md:11`.
- No `Tool Search` / `Visibility` per-session in `hh-mcp-pro`; hub without them will expose 70 tools → token waste and accuracy drop (per `tool-search.md`).
- No `task=True` / `Progress` / `Approval` in `hh-mcp-pro` vacancy flow; long `hh→li→tg` chain will timeout without background tasks.
- `LocalProvider` only; missing `CustomProvider` opportunity for DB-backed contacts (docs vs current `_list_tools` not implemented).

## Decisions for Plan
- **Keep**: `LocalProvider` decorators for hub's own `contacts` CRUD; `lifespan |` composition; `namespace` transform.
- **Change**: Add `ProxyProvider` via `create_proxy` for hh/li/tg; add `CustomProvider` for Neon contacts; enable `BM25SearchTransform` + `Visibility` allowlist; migrate `hh→li→tg` enrichment to `@mcp.tool(task=True)` with `Progress` + `Approval`.
- **Investigate**: `FilesystemProvider` for `hub/tools/*.py` auto-discovery vs explicit `providers` list; `StorageBackends` for session state on `http` transport; `Session State/UserSession` for per-user recruiter quota (30-80 DMs/day) enforcement.

## Notes
- All findings from `context7 /pydantic/pydantic-ai` and `/prefecthq/fastmcp` + `exa web_fetch_exa https://gofastmcp.com/...` + `gitnexus query hh-mcp-pro`. No memory-only claims.
- Artifact blocks `fastmcp-docs-first` gate: Phase 1 planning now unblocked for job-hub.


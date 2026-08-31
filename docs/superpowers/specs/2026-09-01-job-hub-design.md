# Job Hunting Hub — Design (Lean Hub A)
Date: 2026-09-01
Status: Draft for review (brainstorming → writing-plans)
Repo: new `job-hunting-hub` (Python 3.12, FastMCP 3.4.7, uv), aggregates `hh-mcp-pro` + `linkedin-mcp-search` + `telegram-mcp`
Research: `docs/research/T-job-hub-fastmcp.md` (7/7), `https://gofastmcp.com/llms.txt` (234 pages), Medium GraphRAG 2026

## 1. Goal & Non-Goals
**Goal:** Поставить на поток сбор долгоживущей БД `companies → recruiters → contacts (tg_handle/phone)` (не вакансии) и `Telegram`-аутрич через `HH vacancy → LinkedIn company → HR → Telegram resolve → contacts_upsert → Approval → send`. Агент `scouts, scores, drafts` — юзер решает.
**Success:** `reply rate 15-25%` (vs `3.4%` generic), `0` банов Telegram, `<400ms` p95 `list_tools` c кэшем.
**Non-Goals v1:** `GraphRAG` (только `plain RAG`), `auto-apply` без `HUMAN_IN_LOOP`, `FastAPI` фронт (только `Apps` в `MCP`).

## 2. Architecture (fastmcp-engineering layering)
```
MCP Adapter (hub/server.py) thin: @hub.tool → use_case → Result
  ↓
Application (hub/application/enrich.py, contacts.py) use_cases, no FastMCP import
  ↓
Domain (hub/domain/models.py) Pydantic BaseModel Company/Recruiter/Contact/Interaction
  ↓
Infrastructure (hub/infra/neon.py asyncpg Pool, hub/infra/telegram.py TelegramClient, hub/infra/hh.py HhClient)
Ports: hub/ports/contacts.py Protocol
Composition root: hub/composition.py owns FastMCP, lifespan, providers, middleware, transforms
```
- `hub = FastMCP("job-hub", lifespan=db_lifespan | tg_lifespan | hh_lifespan)` (`lifespan.md`: `|` enter L→R, exit R→L, `try/finally`, `ContextManagerLifespan` wrap legacy).
- `mount(create_proxy(hh_stdio), namespace="hh")` → `hh_search_vacancies` (`composition.md` live link, `as_proxy=True` auto when child has lifespan).
- `mount(create_proxy(npx linkedin-mcp-search), namespace="li")`, `mount(create_proxy(uv telegram-mcp), namespace="tg")`.
- `providers=[ContactsProvider(Neon DATABASE_URL)]` (`providers/custom.md`: `_list_tools` → `Tool.from_function`, `_list_resources` → `contacts://{id}`).
- `transforms=[BM25SearchTransform(max_results=5, always_visible=["hub_health","contacts_search"]), Visibility]` (`tool-search.md` synthetic `search_tools`/`call_tool`, BM25 lazy index, hash staleness).
- `middleware=[LoggingMiddleware, AuthMiddleware, RateLimitingMiddleware]` ordered, single responsibility.
- `transports`: `stdio` (opencode.json, Claude) + `http` (`mcp.run(transport="http", host=0.0.0.0, port=8000)` + `/health/live|ready` via `custom_route`).
- `fastmcp.json` declarative (`deployment/server-configuration.md`).

## 3. Data Model (Neon Lakebase, branches with data)
```sql
-- Neon Lakebase, scale-to-zero, branch copy-on-write
CREATE EXTENSION IF NOT EXISTS vector; -- pgvector 1536
-- lakebase_vector/lakebase_text for hybrid (aws-us-east-2)
CREATE TABLE companies(id TEXT PK, hh_id TEXT UNIQUE, linkedin_url TEXT UNIQUE, name TEXT, industry TEXT, embedding VECTOR(1536), tsv TSVECTOR);
CREATE TABLE recruiters(id TEXT PK, company_id FK, linkedin_url TEXT UNIQUE, role TEXT, seniority TEXT);
CREATE TABLE contacts(id TEXT PK, recruiter_id FK, tg_handle TEXT UNIQUE, phone TEXT, source TEXT, embedding VECTOR(1536));
CREATE TABLE interactions(id TEXT PK, contact_id FK, channel TEXT, template_variant TEXT, status TEXT, created_at TIMESTAMPTZ);
CREATE INDEX ON contacts USING lakebase_ann (embedding vector_cosine_ops);
CREATE INDEX ON companies USING lakebase_bm25 (tsv);
```
- `ContactsProvider.lifespan` manages `asyncpg` pool from `DATABASE_URL` (`neon deploy` injects).
- `Resource` vs `Tool`: `contacts_search(q)` (tool, action) vs `contacts://{id}` (resource, passive read, cacheable).
- `ResourceTemplate` `recruiters://{company_id}/hr`.

## 4. Flow `enrich_company` (Background Task + HITL)
```
User: enrich_company(company="Тинькофф", vacancy_id="123")
→ Application: search_employers(hh) → search_companies(li) → recruiters(li filters 40+) → resolve_username(tg) + cross-check 2nd source → contacts_upsert → embedding (text-embedding-3-small) → Neon → RAG index
→ MCP: @hub.tool(task=True, tags={"enrich"}) with Progress(set_total=4, increment, set_message), Sampling (LLM personalization from li post), Elicitation (confirm?)
```
- `@hub.tool(task=True)` (`servers/tasks.md`) → `call_tool_task` + `task.status()` polling, not block 10s.
- `Sampling` forward `sampling_handler` to client LLM, `Elicitation` guard `2026-07-28` era.
- `Progress` injected via `Progress()` dependency.
- Final `tg_send_message` gated by `Approval` provider: `request_approval(summary="Send 160 chars to @recruiter", details=template, approve_variant="default")` (`apps/providers/approval.md`). `Choice` for `tailor/skip`, `FormInput` for `resume_id`.
- `Middleware RateLimit`: `hh 5rps`, `tg 30-80 DMs/день` (SpamBot, datacenter IP = ban, report rate). Counter in `interactions` table, `provider_error_strategy="warn"` for proxy failures.
- Plain RAG: `contacts_search(q)` → `vector cosine` + `BM25` → `RRF 1/(60+rank)` fusion, no graph.

## 5. Auth & Security
- `AuthMiddleware(require_scopes("api"))` server-level (`authorization.md`), `CurrentAccessToken` injection (`dependency-injection.md`), domain never sees `Request`.
- `HH`: `token.json chmod 600` precedence `HH_ACCESS_TOKEN → token.json → state.json` (`hh-mcp-pro/config.py:6`), `LinkedIn`: `cookie` env, `Telegram`: `session` file `chmod 600`.
- `Multiple Auth Sources` (`multi-auth.md`) — hub accepts `Bearer` from OpenCode + Claude.
- `Visibility` per-session: `hub.disable(tags={"tg:send"})` global, `await ctx.enable_components(tags={"tg:send"})` after `login` → only that session sees send.
- `StorageBackends` for OAuth state + `Session State` (`sessions.md`) `UserSession` per `sub`.
- `IP Allow` `34.192.103.46/23.22.233.166` for `mcp.neon.tech`.

## 6. RAG Strategy
- Start `plain RAG` (vector + BM25 hybrid). `lakebase_vector 1B+ vectors`, `IVF+RaBitQ`, `scale-to-zero` cache.
- `GraphRAG` deferred: only if queries need `3+ hops` (`team X → project Alpha → Q3`), else `plain RAG` cheaper `10-100×` (`$50 → $2000-5000` per 10k docs, Leiden `40%` fail Gartner). Prototype `Kùzu` later on `resume-position-skill(year)` graph.

## 7. Error Handling
- `Domain` raises `MaxAppliesExceeded`/`TelegramSpamRisk`, `Application` → `Err(code="RATE_LIMITED", hint="...")` (`models.py: Err`), `Adapter` → `ToolResult(isError=True)` without leaking stack, OTEL span `hub.enrich.*` logs root cause.

## 8. Testing & Verification (fastmcp-engineering)
- `unit`: `DictProvider` + `respx` for hh/li/tg mocks, `TypeAdapter` fixtures `tests/fixtures/*.json`.
- `protocol`: `async with Client(hub) as c: assert "hh_search_vacancies" in await c.list_tools(); await c.call_tool("contacts_search", {q:"python fintech"})`.
- `trio`: `uv run pytest -m "not live"` + `ruff check` + `mypy --strict` (pinned `fastmcp>=3.2,<4`, `pydantic>=2.12` for v4).
- `search` respected auth/visibility, `task` progress asserted.

## 9. Deployment
- `fastmcp.json` (`source hub/server.py:mcp`, `environment uv`, `deployment http`), `fastmcp run hub/server.py:mcp --transport http --port 8000`, `fastmcp dev apps` preview.
- `Dockerfile` `uv sync --extra`, `prefect/horizon` optional.

## 10. Open Questions → Decisions
- `FilesystemProvider` for `hub/tools/*.py` vs explicit `providers` list → explicit for v1.
- `Session reuse` for stateless `li` HTTP → factory reuse; stateful `tg` → fresh session.
- `Skills Provider` for recruiter scripts as `skill://` resources → defer to v2.

## Self-Review
- Placeholders: none TBD.
- Consistency: `mount` namespace → `hh_` prefix, `Visibility` server overrides provider, `lifespan |` merge later overwrites — consistent.
- Scope: v1 = Lean Hub A (proxy+custom+plain RAG+HITL), no GraphRAG, no auto-apply.
- Ambiguity: `contacts phone` optional, resolved; `tg_handle` unique enforced.


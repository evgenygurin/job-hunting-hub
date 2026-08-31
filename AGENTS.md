# AGENTS.md — job-hunting-hub

> **Docs-first gate (fastmcp-docs-first):** No `src/` edit without `docs/research/T-job-hub-fastmcp.md` + `docs/superpowers/specs/2026-09-01-job-hub-design.md` covering ALL links of current Ti. Violation = delete code, start over. See `skill://fastmcp-docs-first/SKILL.md` (`resource://config` tag).

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- ОСНОВНОЕ ПРАВИЛО (пользователь, обязательное, всегда)          -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- При ЛЮБЫХ трудностях, ошибках, непонятном поведении — СНАЧАЛА -->
<!-- ИЗУЧИ ОФИЦИАЛЬНУЮ ДОКУМЕНТАЦИЮ (context7 / официальные сайты / -->
<!-- исходники) и только потом действуй. НИКОГДА не додумывай, не   -->
<!-- фантазируй и не пробуй наугад — сначала найди ответ в доках.   -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## 0. Start Here (fresh session, zero history)

1. Read `docs/superpowers/plans/2026-09-01-job-hub-plan.md` — single source of truth (8 tasks, TDD, `uv run pytest -m "not live"` + `ruff` + `mypy --strict` trio). > For agentic workers: use `subagent-driven-development` or `executing-plans`.
2. Read `docs/research/T-job-hub-fastmcp.md` (7/7 FastMCP: composition/proxy/custom/tool-search/visibility/lifespan/tasks+apps via `context7`+`exa`+`gitnexus`) and `docs/superpowers/specs/2026-09-01-job-hub-design.md` (5 sections: architecture, DB `companies→recruiters→contacts→interactions` (Neon Lakebase), flow `vacancy→TG`, auth, plain RAG vs GraphRAG).
3. Read `fastmcp-engineering` methodology at `~/.agents/skills/` or `https://gofastmcp.com/llms.txt` (versioned, every page `→ .md`). Follow `Research → Contracts → Architecture Governor → TDD → Verification` maximally where it gives value, YAGNI elsewhere.
4. Check `gitnexus://repo/job-hunting-hub/context` for index staleness; if `commitsBehind>0` run `node .gitnexus/run.cjs analyze` or `gitnexus analyze`.

## 1. Agent-Specific Rules (Claude Code / Codex / OpenCode)

### Claude Code (`https://docs.claude.com/en/docs/claude-code/overview`, `code.claude.com/docs/llms.txt`)
- Install: `curl -fsSL https://claude.ai/install.sh | bash` / `brew install --cask claude-code`; start `cd job-hunting-hub && claude`.
- Project memory: `CLAUDE.md` (root) = this `AGENTS.md` mirrored; `~/.claude/settings.json` for global. Auto-memory saves learnings — keep `CLAUDE.md` minimal, deterministic.
- Skills: `/` commands from `skill://` resources (`fastmcp-docs-first`, `hh-mcp-tdd-cycle`). Use `/review-pr`, `/deploy-staging` equivalents.
- Hooks: auto-format after edit (`pre-commit: ruff format`), lint before commit (`pre-commit: ruff check + mypy`).
- MCP: `claude mcp add --transport http nearmcp ...` or `~/.claude.json` `mcpServers`. Our `neon` already at `https://mcp.neon.tech/mcp` (see §3).
- Parallelism: lead agent + subagents for independent tasks; never duplicate work. Verify via `Task` tool when delegating.

### Codex (`https://developers.openai.com/codex/overview`, `npm install -g @openai/codex`)
- Plugins combine **skills** (markdown workflows) + **apps** (MCP) + **MCP servers**. Install via `codex` → `/plugins` → `Neon` or `npx neon@latest plugins --agent codex`, `npx neon@latest init` for full setup.
- Use `codex --cloud` for long runs, `codex --teleport` to resume. Respect `Agent Keys` for parallel control (Micro).
- Skills like `neon-postgres` guide branching/auth — load via `@neon` mention.

### OpenCode (`https://opencode.ai/docs`, `~/.config/opencode/opencode.json`)
- Config: `opencode.json` `mcp` block (our `neon`, `context7`, `exa`, `gitnexus`, `hh-mcp-pro`, `telegram`). Global `~/.config/opencode/opencode.json`, project `.opencode/opencode.json` (rare). `plugin` array for npm plugins.
- CLI: `opencode` TUI → `/init` generates `AGENTS.md`, `/connect` for Zen, `Tab` Plan↔Build mode. Plan mode is read-only — switch to Build with `Tab`.
- Customize via `opencode.json` `provider` (we use `nvidia/moonshotai/kimi-k3`), `references` (`fastmcp-engineering`).
- Superpowers: `using-superpowers` skill must be checked before any action — invoke relevant skill before response.

## 2. MCP Server Usage (maximally effective)

### Context7 (`https://mcp.context7.com/mcp`, `upstash/context7`, `skill://fastmcp-docs-first/SKILL.md`)
- **Rule (auto-invoke):** `Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.` Add to `CLAUDE.md` / `Cursor Settings > Rules` / `AGENTS.md`.
- **Workflow (two-phase, per `context7` skill):**
  1. `resolve-library-id` → `/owner/repo` (e.g. `/prefecthq/fastmcp`, `/supabase/supabase`) using official name (`Next.js` not `nextjs`). Pick by name match + snippet count + reputation High + benchmark score.
  2. `get-library-docs` with `topic` (one concept per call, not 5-in-1). If query spans `routing+auth+caching`, make 3 calls. Do ≤3 per turn.
- **Best practices (https://www.mintlify.com/upstash/context7/guides/best-practices):**
  - Specify version: `How to set up Next.js 14 middleware? use context7` → ` /vercel/next.js/v14.3.0`.
  - Use Library ID directly: `use library /supabase/supabase for API` — skips matching.
  - Write clear, specific prompts (not `how to use React?` but `Create Next.js middleware that checks JWT in cookies and redirects to /login`).
  - Batch related queries separately, cache results (`Map< libraryId:query, docs>`), handle quota via `ctx7 login` or `CONTEX7_API_KEY=ctx7sk-...` env.
- **Never** guess APIs — training data is stale vs `gofastmcp.com/llms.txt`.

### Exa (`https://mcp.exa.ai/mcp`, `https://exa.ai/docs/reference/exa-mcp`, `skills/search/references/searching.md`)
- **Tools:** default `web_search_exa` (query + numResults) + `web_fetch_exa` (full markdown), optional `web_search_advanced_exa` (filters) + `agent_run` (multi-step). Enable via `?tools=web_search_exa,web_fetch_exa,agent_run` in URL.
- **Query writing (semantic, not keyword):** Describe ideal page, not fact: `blog post comparing React and Vue performance` not `React vs Vue`. Never use `AND/NOT` booleans, quotes, 1-2 word queries. Use `category:company|people|news` inline when needed, never mix with domain filters.
- **Freshness:** Calculate dates from today (`2026-09-01`) — `published in March 2026` not relative. `numResults` ≤25 (10-15 per angle, run 2-3 phrasings in parallel for coverage, word order matters).
- **Validation:** Exa returns similarity, not truth — discard irrelevant, `web_fetch_exa` on top 3, report lack of coverage honestly.
- **Auth:** Hosted works anon rate-limited; for prod add `?exaApiKey=...` or `x-api-key` header (`9f4e8aad...` in `opencode.json:exa`).

### GitNexus (`gitnexus mcp`, `gitnexus://repo/{name}/context`, skills `gitnexus-*`)
- **Mandatory gates:**
  - `MUST run impact(target, direction:"upstream")` BEFORE editing any symbol — report blast radius (callers, processes, risk LOW/MEDIUM/HIGH/CRITICAL). Warn user if HIGH/CRITICAL.
  - `MUST run detect_changes()` BEFORE committing — `detect_changes({scope:"all"})` + `detect_changes({scope:"compare", base_ref:"main"})`.
  - `NEVER rename with find-and-replace — use rename` (graph + text search, confidence `graph` vs `text_search`).
  - If index stale (`gitnexus://repo/job-hunting-hub/context` shows `commitsBehind>0`), run `node .gitnexus/run.cjs analyze` or `npx gitnexus analyze`.
- **Workflow:** `query({search_query:"concept"})` → process-grouped flows ranked by BM25+vector (when `--embeddings` built) → `context({name:"symbol"})` 360° (callers/callees, processes) → `impact` → `trace(from,to)` for debug `how does A reach B?`.
- **Index flags:** `analyze` default = BM25 only (`embeddings:0`); for semantic add `--embeddings` (local ONNX, `Threads 4, Batch 16`, ~30s per 1k nodes). `analyze --pdg` only for taint `explain`/`pdg_query` (we keep `pdg: false` pinned, not needed for hub MVP).
- **Group mode:** `repo="@job-hub"` or `@job-hub/hh-mcp-pro` for cross-repo `query/context/impact`. `group_list`/`group_sync` after `group.yaml` edits. `contracts.json` (10 contracts, 0 cross-links currently) — `gitnexus group sync job-hub` after each `analyze`.
- **Resources:** `gitnexus://repos`, `gitnexus://repo/{name}/clusters`, `gitnexus://repo/{name}/processes`, `gitnexus://group/{name}/contracts?type=&repo=`, `gitnexus://group/{name}/status`.

## 3. FastMCP Engineering — Maximally Effective (Agent Contract, full)

> Source: `fastmcp-engineering/AGENTS.md` + `architecture/mcp-server-architecture/SKILL.md` + `skills/*`. This repo pins `fastmcp-engineering` as `~/.agents/skills` reference (`AGENTS.md:18`).

**Mission:** Evidence-driven, production-grade MCP servers — research → architecture → TDD → security → docs sync → verification.

**Non-negotiable (12 rules, verbatim):**
1. `Research` official FastMCP docs before design/impl; 2. Inspect official examples; 3. Verify MCP protocol semantics; 4. Pin FastMCP version, never mix v3/v4 APIs silently; 5. Prefer native `Providers/Transforms/Middleware/Context/Lifespans/tasks/auth/client` — justify custom; 6. Keep domain independent of `FastMCP/SQLAlchemy/Pydantic/httpx/LLM SDK`; 7. Keep MCP handlers thin (validate → useCase → map → translate errors); 8. `SOLID/KISS/DRY/YAGNI` as constraints; 9. `TDD` with unit/integration/MCP-contract/transport/security layers; 10. Never claim `Done` without fresh verification evidence; 11. Docs are part of impl (same PR if API/arch/config/ops/agent workflow changes); 12. No persistent work on `main` — one short-lived branch + one PR → merge → delete branch.

**Required workflow (preflight → main verification, 20 steps):**
`Preflight → Requirement → discovery → official research → example/pattern → version check → architecture → architecture gate → contracts → tests → implementation → documentation sync → static analysis → integration/MCP tests → security review → architecture review → PR → review → merge → source-branch deletion → main verification → branch inventory`.

**Branch lifecycle:** `feat/<scope>`, `fix/<scope>`, `refactor/<scope>`, `docs/<scope>`, `chore/<scope>` — single short-lived branch → one PR → merge → delete → verify `main` → `git branch` inventory. No orphan branch, no surviving branch after merge.

**Docs-first & Version pinning:** `fastmcp-docs-first` blocks `src/` without `docs/research/T-*.md` (19/19 for T1). `pyproject.toml` `fastmcp[apps]>=3.2,<4` (exact `3.4.7`), `pydantic>=2.12` for v4, deferred `>=2.12` note in `docs/notes/fastmcp-json-deferred.md`. No open `>=`.

**Layering (`mcp-server-architecture`):** `MCP Adapter (thin) → Application UseCase (validation+Result→domain) → Domain (Pydantic, no FastMCP) → Ports → Infra (asyncpg, httpx, TelegramClient)`. `composition.py` is root container — `server.py` only re-exports `mcp`.

**Server composition:** `hub = FastMCP("job-hub", lifespan=db_lifespan|tg_lifespan)` (`|` left→right enter, right→left exit, merge dict later wins, `ContextManagerLifespan` wrap legacy `@asynccontextmanager`). `mount(create_proxy(hh, namespace="hh"))` live link (`import_server` is static copy — not for hub). `create_proxy` lazy, `cache_ttl=300`, `session isolation` per-request, `shared session` only for stateless + `ProxyClient.new()`.

**Providers/Transforms/Visibility/Tasks/Apps/Capabilities (use natively before custom):**
- `Providers`: `LocalProvider` (decorators), `FastMCPProvider` (`mount`), `ProxyProvider` (`create_proxy`), `CustomProvider` (`Provider._list_tools → Tool.from_function` for DB-backed `contacts`), `FilesystemProvider`, `SkillsProvider`.
- `Transforms`: `Namespace`, `ToolSearch` (`Regex` vs `BM25` — BM25 for natural language, `max_results=5`, `always_visible`), `Visibility` (`enable/disable(tags/names/keys/version)` layered provider→server, per-session `ctx.enable_components/disable_components/reset_visibility`), `Resources as Tools`, `Code Mode` (deferred).
- `Lifespans`: composable `|`, `ctx.lifespan_context["pool"]`, `combine_lifespans` for FastAPI.
- `Tasks`: `@hub.tool(task=True)` + `Progress(set_total/increment/set_message)` + `CurrentDocket/CurrentWorker` (`fastmcp[tasks]`), client `call_tool_task` + `task.status()` polling, `elicitation`/`sampling` forwarding.
- `Apps`: `Approval` (`request_approval(summary,details,approve_variant="destructive")`), `Choice`, `FormInput` (`Pydantic`), `FileUpload`, `Generative UI` (deferred) — `fastmcp[apps]` + `prefab-ui`, `fastmcp dev apps` preview.
- `Middleware` ordered: `LoggingMiddleware` → `AuthMiddleware(require_scopes)` → `RateLimitingMiddleware` → `Caching`. Single responsibility, deterministic order.
- `Auth`: `FastMCP(auth=StaticTokenVerifier/OAuthProxy/OIDCProxy)` + `CurrentAccessToken` + `UserSession` (`sessions.md`) per `sub`.
- `Testing`: `fastmcp.Client` for MCP-contract (tools list, call, resources, prompts, sampling/elicitation), `respx` for `httpx`, `TypeAdapter` fixtures.
- `Verification policy`: CI optional, local `pytest -m "not live" -v` + `ruff check` + `mypy --strict` + `detect_changes` + `gitnexus impact` is authoritative. Never invent results, never weaken because CI unavailable. Fresh evidence required for `Done`.

**Skills to invoke (from `~/.agents/skills` + `fastmcp-engineering/skills`):** `fastmcp-docs-first`, `fastmcp-research-loop`, `fastmcp-components`, `fastmcp-context-di`, `fastmcp-lifespan`, `fastmcp-middleware`, `fastmcp-providers`, `fastmcp-protocol-compliance`, `fastmcp-transports-deployment`, `api-contract-schema-engineering`, `application-architecture-usecases`, `architecture-governor`, `testing-quality-engineering`, `observability-telemetry-engineering`, `security-engineering`, `dependency-injection-composition-root`, `hh-mcp-tdd-cycle`, `hh-mcp-verification`, `hh-mcp-gitnexus-workflow`.

**Documentation sync:** If `tools/resources/prompts`, `fastmcp.json`, `neon.ts`, `AGENTS.md` skills table, or agent workflow changes, update `README.md` + `docs/` + `CHANGELOG.md` in same PR; if intentionally unchanged, record reason in PR evidence.

## 4. GitHub Workflow (branches, Conventional Commits, PR)

- **Branches:** `main` only persistent. Work on `feat/fix/refactor/docs/chore` short-lived branches: `main → feat/task-name → PR → review → merge → delete branch → verify main`. Never leave orphan branch. Use `using-git-worktrees` skill for isolation (`git worktree add`).
- **Conventional Commits:** `type(scope): subject` lower case, imperative, no period. Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`, `build`, `ci`. Examples: `feat(domain): contacts models + fixtures`, `fix: scaffold test for fastmcp[apps] extra`, `docs: make plan self-contained`. Reference `git log --oneline -10` for style.
- **Commits:** Stage only intended files (`git status`, `git diff` before `add`), never commit secrets (`token.json`, `TG_SESSION`, `CONTEXT7_API_KEY`, `NEON_API_KEY`). Check hooks; if hooks reject, fix and new commit (never `amend` failed).
- **PR:** Before create, check `status`, `diff`, `remote -v`, `log`. Include all commits, not just latest. Use `gh` (`gh pr create`, `gh pr view`, `codegen-bulk` for parallel). Return PR URL when done.
- **CI:** `justfile` / `uv run pytest` + `ruff` + `mypy` locally; GitHub Actions optional. Never invent CI results.
- **Sync:** After each `gitnexus analyze`, run `gitnexus group sync job-hub` if `group.yaml` changed.

## 5. Project-Specific Rules

- **Hub vs hh-mcp-pro:** `hh-mcp-pro` stays upstream `43 tools` (no API registration); hub mounts it, never forks its `auth` logic. Domain `Company/Recruiter/Contact` lives only in hub `Neon Lakebase` (`pgvector 1536` + `lakebase_text BM25` hybrid `RRF 1/(60+rank)`).
- **Telegram compliance:** `RateLimitingMiddleware` enforces `30-80 DMs/день`, `datacenter IP = ban`, `young account{must} warm-up`, 1 `follow-up 5-7д`. `Approval` gate mandatory before `tg_send_message`.
- **RAG:** `plain RAG` first; `GraphRAG` deferred (10-100× cost, Gartner 40% fail, only if `3+ hops` needed). Measure `reply rate 15-25%` vs `3.4%` generic before expanding.
- **Neon:** `aws-us-east-2` for beta `Functions/Storage/AI Gateway`, `DATABASE_URL` via `neon deploy`, `scale-to-zero` compatible `lakebase_vector`.


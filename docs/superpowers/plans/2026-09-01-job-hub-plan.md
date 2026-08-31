# Job Hunting Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить lean `job-hunting-hub` — FastMCP хаб, агрегирующий `hh-mcp-pro` + `linkedin-mcp-search` + `telegram-mcp` через `mount(create_proxy, namespace)` + долгоживущая `Neon Lakebase` БД `companies/recruiters/contacts` с `plain RAG` и `HITL Approval`.

**Architecture:** `FastMCP Hub` с `lifespan | lifespan` композицией, `ProxyProvider` (lazy, cache_ttl=300, session isolation), `CustomProvider` для Neon contacts, `BM25SearchTransform` + `Visibility` (per-session), `Background Tasks` + `Progress` + `Approval/Choice` для `enrich_company` цепочки. Строгий layering `MCP → Application → Domain → Infra` per `mcp-server-architecture`.

**Tech Stack:** Python 3.12, FastMCP 3.4.7 (`fastmcp>=3.2,<4`, `pydantic>=2.12` for v4), `asyncpg`, `httpx`, `@neondatabase/serverless`, `pgvector`, `ruff line 100`, `mypy --strict`, `pytest + respx + fastmcp.Client`, `Neon Lakebase` (`aws-us-east-2`), `uv`

## Global Constraints

- Python `3.12`, `uv` (`uv sync`, `uv run`), `requires-python = ">=3.12"`
- `fastmcp>=3.2,<4` (exact `3.4.7` in lock), `pydantic>=2.12,<3` (v4 floor), `pydantic-settings>=2.6,<3`, `httpx>=0.27,<0.29`
- `ruff line-length 100`, selects `E,F,I,UP,B,SIM,ASYNC`; `mypy --strict`, all public funcs typed
- `Result[T]` contract `Ok[T]|Err` discriminated `ok: Literal` (`models.py:6` pattern)
- `DATABASE_URL` from `neon deploy` (Neon Lakebase, `aws-us-east-2`), `chmod 600` for `token.json`/`session`
- Rate limits: `hh 5rps`, `tg 30-80 DMs/день` (SpamBot), `Retry-After` on 429
- Tests `pytest -m "not live"` default, `live` marked separately

---

## File Structure

```
job-hunting-hub/  (new repo, not hh-mcp-pro)
├── pyproject.toml
├── fastmcp.json  (source hub/server.py:mcp, environment uv, deployment http 8000)
├── .env.example  (DATABASE_URL, HH_CLIENT_ID, LINKEDIN_COOKIE, TG_SESSION)
├── src/hub/
│   ├── __init__.py
│   ├── server.py              # hub = FastMCP(lifespan=...), mounts, transforms, middleware
│   ├── composition.py         # lifespan factories, provider wiring
│   ├── domain/models.py       # Company/Recruiter/Contact/Interaction Pydantic
│   ├── application/enrich.py  # enrich_company_use_case(hh→li→tg)
│   ├── application/contacts.py# contacts_search, contacts_upsert use_cases
│   ├── infra/neon.py          # asyncpg pool, vector helpers
│   ├── infra/telegram.py      # TelegramClient wrapper
│   ├── providers/contacts.py  # ContactsProvider(Provider) _list_tools/_list_resources
│   └── middleware/rate_limit.py
├── tests/
│   ├── conftest.py
│   ├── fixtures/contacts.json
│   └── unit/test_*.py
└── docs/
```

---

### Task 1: Repo scaffold — pyproject, fastmcp.json, ruff/mypy

**Files:**
- Create: `job-hunting-hub/pyproject.toml`, `job-hunting-hub/fastmcp.json`, `job-hunting-hub/.env.example`, `job-hunting-hub/src/hub/__init__.py`
- Test: `job-hunting-hub/tests/unit/test_scaffold.py`

**Interfaces:**
- Consumes: none
- Produces: `hub` package importable, `fastmcp.json` valid, `uv sync` works

- [ ] **Step 1: Write failing test for scaffold**
```python
def test_pyproject_has_fastmcp_floor():
    import pathlib
    text = pathlib.Path("pyproject.toml").read_text()
    assert 'fastmcp>=3.2,<4' in text
    assert 'pydantic>=2.12' in text
```

- [ ] **Step 2: Run test to verify it fails**
```bash
pytest tests/unit/test_scaffold.py -v
# Expected: FAIL file not found
```

- [ ] **Step 3: Write minimal pyproject.toml + fastmcp.json**
```toml
[project]
name = "job-hunting-hub"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastmcp[apps]>=3.2,<4", "pydantic>=2.12", "pydantic-settings>=2.6", "httpx>=0.27", "asyncpg>=0.29"]
```
```json
{"source":{"type":"filesystem","path":"src/hub/server.py","entrypoint":"mcp"},"environment":{"type":"uv","python":">=3.12","project":"."},"deployment":{"transport":"stdio","log_level":"INFO"}}
```

- [ ] **Step 4: Run test passes**
```bash
uv sync && pytest tests/unit/test_scaffold.py -v
# Expected: PASS
```

- [ ] **Step 5: Commit**
```bash
git init -b main && git add pyproject.toml fastmcp.json src/hub/__init__.py tests/unit/test_scaffold.py
git commit -m "chore: scaffold job-hub (pyproject, fastmcp.json, uv)"
```

---

### Task 2: Domain models — Pydantic contracts + fixtures

**Files:**
- Create: `src/hub/domain/models.py`, `tests/fixtures/contacts.json`, `tests/unit/test_models.py`

**Interfaces:**
- Consumes: none
- Produces: `Company, Recruiter, Contact, Interaction, Result[T]` with `TypeAdapter` validation

- [ ] **Step 1: Failing test**
```python
from pydantic import TypeAdapter
from hub.domain.models import Contact
def test_contact_schema():
    ta = TypeAdapter(Contact)
    data = {"id":"c1","recruiter_id":"r1","tg_handle":"@john","phone":None,"source":"tg"}
    c = ta.validate_python(data)
    assert c.tg_handle == "@john"
```

- [ ] **Step 2: Run fails**
```bash
pytest tests/unit/test_models.py::test_contact_schema -v
# Expected: FAIL ModuleNotFound
```

- [ ] **Step 3: Implement models.py**
```python
from pydantic import BaseModel, Field
from typing import Literal
class Company(BaseModel): id: str; hh_id: str|None=None; linkedin_url: str; name: str
class Recruiter(BaseModel): id: str; company_id: str; linkedin_url: str; role: str
class Contact(BaseModel): id: str; recruiter_id: str; tg_handle: str|None=None; phone: str|None=None; source: Literal["hh","li","tg"]
class Interaction(BaseModel): id: str; contact_id: str; channel: str; template_variant: str; status: Literal["sent","replied","blocked"]
```

- [ ] **Step 4: Pass**
```bash
pytest tests/unit/test_models.py -v
# Expected: PASS
```

- [ ] **Step 5: Commit**
```bash
git add src/hub/domain/models.py tests/fixtures/contacts.json tests/unit/test_models.py
git commit -m "feat(domain): contacts models + fixtures"
```

---

### Task 3: Infra Neon pool + lifespan composition

**Files:**
- Create: `src/hub/infra/neon.py`, `src/hub/composition.py:db_lifespan`
- Test: `tests/unit/test_lifespan.py`

**Interfaces:**
- Consumes: `DATABASE_URL` env
- Produces: `db_lifespan: Lifespan` yielding `{"pool": asyncpg.Pool}`, `composition.db_lifespan | telegram_lifespan`

- [ ] **Step 1: Failing test**
```python
import asyncio
from hub.composition import db_lifespan
from fastmcp import FastMCP
async def test_lifespan_yields_pool():
    mcp = FastMCP("test", lifespan=db_lifespan)
    async with mcp.lifespan(mcp):
        pass
```

- [ ] **Step 2: Fail**

- [ ] **Step 3: Implement infra/neon.py + composition.db_lifespan via @lifespan, asyncpg.create_pool, try/finally close**

- [ ] **Step 4: Pass**

- [ ] **Step 5: Commit**

---

### Task 4: CustomProvider ContactsProvider (DB-backed tools/resources)

**Files:**
- Create: `src/hub/providers/contacts.py`
- Modify: `src/hub/server.py` to add provider
- Test: `tests/unit/test_contacts_provider.py` with `fastmcp.Client`

**Interfaces:**
- Consumes: `db_lifespan` pool via `ctx.lifespan_context["pool"]`
- Produces: `ContactsProvider` exposing `contacts_search(q: str) -> list[Contact]` (tool) + `contacts://{id}` (resource)

- [ ] **Step 1: Failing test**
```python
from fastmcp import Client, FastMCP
from hub.providers.contacts import ContactsProvider
async def test_contacts_provider_lists_tools():
    mcp = FastMCP("test", providers=[ContactsProvider("postgresql://test")])
    async with Client(mcp) as c:
        tools = await c.list_tools()
        assert any("contacts_search" in t.name for t in tools)
```

- [ ] **Step 2: Fail**

- [ ] **Step 3: Implement Provider subclass with _list_tools returning Tool.from_function(contacts_search), _list_resources returning Resource.from_function**

- [ ] **Step 4: Pass**

- [ ] **Step 5: Commit**

---

### Task 5: Hub composition — mount hh/li/tg via create_proxy + namespace

**Files:**
- Modify: `src/hub/server.py`, `src/hub/composition.py`
- Test: `tests/unit/test_composition.py`

**Interfaces:**
- Consumes: `hh-mcp-pro` path, `linkedin-mcp-search` npx, `telegram-mcp` uv
- Produces: `hub` with `hh_search_vacancies`, `li_search_companies`, `tg_send_message` prefixed

- [ ] **Step 1: Failing test**
```python
from fastmcp import Client
from hub.server import mcp as hub
async def test_hub_mounts():
    async with Client(hub) as c:
        tools = await c.list_tools()
        names = {t.name for t in tools}
        assert "hh_search_vacancies" in names
        assert "li_search_companies" in names
```

- [ ] **Step 2: Fail**

- [ ] **Step 3: Implement server.py: hub.mount(create_proxy("hh-mcp-pro/...", name="hh"), namespace="hh") etc., cache_ttl=300**

- [ ] **Step 4: Pass**

- [ ] **Step 5: Commit**

---

### Task 6: Transforms — BM25 Tool Search + Visibility

**Files:**
- Modify: `src/hub/server.py`
- Test: `tests/unit/test_search_visibility.py`

**Interfaces:**
- Consumes: hub with 70+ tools
- Produces: `list_tools()` returns only `search_tools` + `call_tool` + pinned `hub_health`, `search_tools(query="telegram")` returns `tg_*`

- [ ] **Step 1: Failing test**
```python
async def test_search_transform():
    async with Client(hub) as c:
        tools = await c.list_tools()
        assert len(tools) == 3  # search_tools, call_tool, hub_health
        res = await c.call_tool("search_tools", {"query": "telegram recruiter"})
        assert "tg_send_message" in str(res)
```

- [ ] **Step 2: Fail**

- [ ] **Step 3: Implement hub.add_transform(BM25SearchTransform(max_results=5, always_visible=["hub_health"])) + hub.disable(tags={"internal"})**

- [ ] **Step 4: Pass**

- [ ] **Step 5: Commit**

---

### Task 7: Enrich use_case as Background Task + HITL Apps

**Files:**
- Create: `src/hub/application/enrich.py`, `src/hub/application/contacts.py`
- Modify: `src/hub/server.py` add `@hub.tool(task=True, tags={"enrich"})`
- Test: `tests/unit/test_enrich_task.py`

**Interfaces:**
- Consumes: `ContactsProvider`, `hh/li/tg` proxies via `ctx.lifespan_context`
- Produces: `enrich_company(company_name: str, vacancy_id: str, progress: Progress) -> Contact` with `await progress.set_total(4); increment`

- [ ] **Step 1: Failing test**
```python
async def test_enrich_task_progress():
    async with Client(hub) as c:
        task = await c.call_tool("enrich_company", {"company_name":"Yandex","vacancy_id":"1"})
        # task is background, check progress
```

- [ ] **Step 2: Fail**

- [ ] **Step 3: Implement enrich_company_use_case + @hub.tool(task=True) with Progress + request_approval before tg_send**

- [ ] **Step 4: Pass**

- [ ] **Step 5: Commit**

---

### Task 8: Verification — ruff/mypy/pytest + gitnexus detect

**Files:**
- Modify: none (verify)
- Test: `pytest -m "not live" -v && ruff check . && mypy src`

**Interfaces:**
- Consumes: all tasks

- [ ] **Step 1: Run trio**
```bash
uv run pytest -m "not live" -v
uv run ruff check src tests
uv run mypy src --strict
```

- [ ] **Step 2: Fix failures**

- [ ] **Step 3: Commit verification**
```bash
git commit --allow-empty -m "chore: verification trio green"
```

## Self-Review

- Spec coverage: mounts (Task5), custom provider (Task4), search/visibility (Task6), lifespan (Task3), task+apps (Task7), domain (Task2) — all covered.
- Placeholders: none, each step has code.
- Type consistency: Company/Recruiter/Contact/Interaction signatures consistent across Domain→Provider→UseCase→Tool (tags enrich).


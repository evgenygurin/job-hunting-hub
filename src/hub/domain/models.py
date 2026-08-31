"""Result contract + domain models (Company, Recruiter, Contact, Interaction).

Result envelope follows the house pattern from hh-mcp-pro (`hh_mcp_pro/models.py`).
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Err(BaseModel):
    """Error envelope — `ok=False` discriminates the `Result` union."""

    ok: Literal[False] = False
    code: str
    message: str
    hint: str | None = None
    data: None = None


class Ok[T](BaseModel):
    """Success envelope — PEP 695 generic, Pydantic v2 compatible."""

    ok: Literal[True] = True
    code: None = None
    data: T


type Result[T] = Annotated[Ok[T] | Err, Field(discriminator="ok")]


class Company(BaseModel):
    id: str
    hh_id: str | None = None
    linkedin_url: str
    name: str


class Recruiter(BaseModel):
    id: str
    company_id: str
    linkedin_url: str
    role: str


class Contact(BaseModel):
    id: str
    recruiter_id: str
    tg_handle: str | None = None
    phone: str | None = None
    source: Literal["hh", "li", "tg"]


class Interaction(BaseModel):
    id: str
    contact_id: str
    channel: str
    template_variant: str
    status: Literal["sent", "replied", "blocked"]

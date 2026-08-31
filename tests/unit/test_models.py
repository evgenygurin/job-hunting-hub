import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from hub.domain.models import Company, Contact, Err, Interaction, Ok, Recruiter, Result

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_contact_schema():
    ta = TypeAdapter(Contact)
    data = {"id": "c1", "recruiter_id": "r1", "tg_handle": "@john", "phone": None, "source": "tg"}
    c = ta.validate_python(data)
    assert c.tg_handle == "@john"


def test_company_model():
    ta = TypeAdapter(Company)
    company = ta.validate_python(
        {"id": "co1", "linkedin_url": "https://www.linkedin.com/company/acme", "name": "Acme"}
    )
    assert company.hh_id is None


def test_recruiter_model():
    ta = TypeAdapter(Recruiter)
    recruiter = ta.validate_python(
        {
            "id": "r1",
            "company_id": "co1",
            "linkedin_url": "https://www.linkedin.com/in/john",
            "role": "TA",
        }
    )
    assert recruiter.role == "TA"


def test_interaction_model():
    ta = TypeAdapter(Interaction)
    interaction = ta.validate_python(
        {
            "id": "i1",
            "contact_id": "c1",
            "channel": "tg",
            "template_variant": "v1",
            "status": "sent",
        }
    )
    assert interaction.status == "sent"


def test_contact_rejects_unknown_source():
    ta = TypeAdapter(Contact)
    with pytest.raises(ValidationError):
        ta.validate_python({"id": "c1", "recruiter_id": "r1", "source": "email"})


def test_result_ok_envelope():
    ta = TypeAdapter(Result[Contact])
    result = ta.validate_python(
        {"ok": True, "data": {"id": "c1", "recruiter_id": "r1", "source": "tg"}}
    )
    assert isinstance(result, Ok)
    assert result.data.tg_handle is None


def test_result_err_envelope():
    ta = TypeAdapter(Result[Contact])
    result = ta.validate_python({"ok": False, "code": "INPUT_ERROR", "message": "invalid input"})
    assert isinstance(result, Err)
    assert result.hint is None


def test_contacts_json_fixture_matches_live_schema():
    fixture = json.loads((FIXTURES / "contacts.json").read_text())
    assert fixture == TypeAdapter(Contact).json_schema()

"""Strict management transport; API integration uses actual production routers."""

import importlib
import json
from uuid import uuid4

import httpx
import pytest
from fastapi import APIRouter, FastAPI, HTTPException, Request
from pydantic import ValidationError


@pytest.mark.parametrize(
    "payload",
    [{}, {"name": None}, {"name": 42}, {"name": ""}, {"name": "\tbad"},
     {"name": "bad\x85"}, {"name": "x" * 61}, {"name": "\ud800"},
     {"name": "ok", "description": None}, {"name": "ok", "description": "\x00"},
     {"name": "ok", "description": "\x7f"}, {"name": "ok", "description": "😀" * 1001},
     *({"name": "ok", key: 10000} for key in ("owner", "user_id", "cash", "starting_cash"))],
)
def test_create_schema_refuses_invalid_and_authority_fields(payload):
    schemas = importlib.import_module("app.schemas.portfolios")
    with pytest.raises(ValidationError):
        schemas.PortfolioCreate.model_validate(payload)


def test_normalized_scalar_limits_and_patch_presence():
    schemas = importlib.import_module("app.schemas.portfolios")
    value = schemas.PortfolioCreate(name="\u2003e\u0301😀\u3000", description="\t\r\n" + "😀" * 998)
    assert value.name == "é😀" and value.description == "\t\n" + "😀" * 998
    assert schemas.PortfolioCreate(name="😀" * 60).description == ""
    assert schemas.PortfolioPatch(description="").model_fields_set == {"description"}
    for payload in ({}, {"name": None}, {"description": None}, {"cash": "1"}):
        with pytest.raises(ValidationError):
            schemas.PortfolioPatch.model_validate(payload)


@pytest.fixture
def boundary_app():
    management = importlib.import_module("app.api.v2.portfolio_management")
    app = FastAPI()
    router = APIRouter(route_class=management.ManagementRoute)

    @router.post("/probe")
    async def probe(request: Request):
        return await management.read_management_body(request, patch=False)

    @router.get("/fail")
    async def fail():
        raise RuntimeError("secret SQL credentials")

    @router.get("/refuse")
    async def refuse():
        raise HTTPException(401, detail={"code": "not_authenticated"})

    app.include_router(router)
    return app


@pytest.mark.parametrize("size,declared", [(8193, None), (8193, "1"), (8193, "8193")])
async def test_streamed_body_is_bounded_even_with_deceptive_length(boundary_app, size, declared):
    async def chunks():
        yield b" " * 4000
        yield b" " * (size - 4000)

    headers = {"content-type": "application/json"}
    if declared:
        headers["content-length"] = declared
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=boundary_app), base_url="https://test") as client:
        response = await client.post("/probe", content=chunks(), headers=headers)
    assert response.status_code == 413
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Cookie, Authorization"


@pytest.mark.parametrize("body,media,status", [
    (b'{"name":"x"}', "text/plain", 415),
    (b'{', "application/json", 422),
    (b'[]', "application/json", 422),
    (b'{"name":"a","name":"b"}', "application/json", 422),
    (json.dumps({"name": "x"}).encode().ljust(8192), "application/json; charset=utf-8", 200),
])
async def test_json_boundary_and_exact_body_limit(boundary_app, body, media, status):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=boundary_app), base_url="https://test") as client:
        response = await client.post("/probe", content=body, headers={"content-type": media})
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"


async def test_private_unknown_result_copy_does_not_claim_no_creation(boundary_app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=boundary_app), base_url="https://test") as client:
        response = await client.get("/fail")
        refused = await client.get("/refuse")
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "service_unavailable"
    assert "original" in response.json()["detail"]["message"].lower()
    assert "secret" not in response.text
    assert refused.status_code == 401 and refused.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("key", [None, "", "x" * 10000, str(uuid4()).upper(), "00000000-0000-0000-0000-000000000000"])
def test_creation_key_is_one_bounded_canonical_uuid4(key):
    management = importlib.import_module("app.api.v2.portfolio_management")
    with pytest.raises(HTTPException) as error:
        management.creation_key(key)
    assert error.value.status_code == 422


def test_valid_creation_key():
    management = importlib.import_module("app.api.v2.portfolio_management")
    key = uuid4()
    assert management.creation_key(str(key)) == key

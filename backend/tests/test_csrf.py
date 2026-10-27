import httpx

from tests.helpers import csrf_headers, unique_email

CSRF = "/api/v1/auth/csrf"
REQ = "/api/v1/auth/request-code"


async def test_csrf_sets_cookie_with_attributes(auth_client: httpx.AsyncClient) -> None:
    r = await auth_client.get(CSRF)
    assert r.status_code == 204
    cookies = r.headers.get_list("set-cookie")
    assert len(cookies) == 1
    c = cookies[0].lower()
    assert c.startswith("bj_csrf=")
    assert "secure" in c
    assert "samesite=strict" in c
    assert "path=/" in c
    assert "max-age=2592000" in c
    assert "httponly" not in c


async def test_csrf_cookie_roundtrips_and_is_not_reset(auth_client: httpx.AsyncClient) -> None:
    await auth_client.get(CSRF)
    r = await auth_client.get(CSRF)
    assert r.status_code == 204
    assert r.headers.get_list("set-cookie") == []


async def test_post_without_header_is_403(auth_client: httpx.AsyncClient) -> None:
    await auth_client.get(CSRF)
    r = await auth_client.post(REQ, json={"email": unique_email()})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "csrf_failed"


async def test_post_with_mismatched_header_is_403(auth_client: httpx.AsyncClient) -> None:
    await auth_client.get(CSRF)
    r = await auth_client.post(REQ, json={"email": unique_email()}, headers={"X-CSRF-Token": "x"})
    assert r.status_code == 403


async def test_post_with_header_but_no_cookie_is_403(auth_client: httpx.AsyncClient) -> None:
    r = await auth_client.post(REQ, json={"email": unique_email()}, headers={"X-CSRF-Token": "x"})
    assert r.status_code == 403


async def test_csrf_checked_before_body_validation(auth_client: httpx.AsyncClient) -> None:
    r = await auth_client.post(REQ, json={"email": "nope"})
    assert r.status_code == 403


async def test_valid_csrf_passes(auth_client: httpx.AsyncClient) -> None:
    headers = await csrf_headers(auth_client)
    r = await auth_client.post(REQ, json={"email": unique_email()}, headers=headers)
    assert r.status_code == 202


async def test_non_ascii_header_is_403_not_500(auth_client: httpx.AsyncClient) -> None:
    await auth_client.get(CSRF)
    # Raw latin-1 byte 0xE9: Starlette decodes it to a non-ASCII str.
    r = await auth_client.post(
        REQ, json={"email": unique_email()}, headers={"X-CSRF-Token": b"tok\xe9n"}
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "csrf_failed"


async def test_non_ascii_cookie_and_header_is_403_not_500(
    auth_client: httpx.AsyncClient,
) -> None:
    r = await auth_client.post(
        REQ,
        json={"email": unique_email()},
        headers={"Cookie": b"bj_csrf=\xe9\xe9", "X-CSRF-Token": b"\xe9x"},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "csrf_failed"

"""Authenticated mixed-event History over actual retained PostgreSQL records."""

from tests.helpers import sign_in, unique_email


async def test_mixed_history_authenticated_empty_read(auth_client, outbox):
    await sign_in(auth_client, outbox, unique_email())
    response = await auth_client.get("/api/v1/history")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"items": [], "next_cursor": None}

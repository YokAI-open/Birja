"""Strict full-tuple cursor and exact event wire contracts."""

from datetime import UTC, datetime

from app.services.event_history import EventHistoryCursor, decode_cursor, encode_cursor


def test_mixed_cursor_roundtrip_preserves_all_order_columns():
    value = EventHistoryCursor(datetime(2026, 11, 12, 15, 1, 2, 123456, UTC), 4, 9223372036854775807)
    assert decode_cursor(encode_cursor(value)) == value

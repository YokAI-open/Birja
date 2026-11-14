"""Actual approved Python/native calendar compatibility, without provider access.

Official fixtures: https://www.nyse.com/trade/hours-calendars and
https://www.nasdaq.com/market-activity/stock-market-holiday-schedule (2026).
"""

import sys
from datetime import UTC, datetime
from importlib.metadata import version

import exchange_calendars as calendars
import numpy
import pandas
import pytest


def test_approved_native_versions_and_python() -> None:
    assert sys.version_info[:2] == (3, 14)
    assert numpy.__version__ == "2.5.4"
    assert pandas.__version__ == "3.1.1"
    assert version("exchange-calendars") == "4.13.2"
    assert numpy.array([1, 2]).sum() == 3


@pytest.mark.parametrize("name", ["XNYS", "XNAS", "NASDAQ"])
def test_actual_alias_regular_holiday_and_early_close(name: str) -> None:
    calendar = calendars.get_calendar(name, start="2026-01-01", end="2026-12-31")
    assert calendar.name == "XNYS"
    assert not calendar.is_session("2026-11-26")
    assert calendar.session_open("2026-11-27").to_pydatetime() == datetime(
        2026, 11, 27, 14, 30, tzinfo=UTC
    )
    assert calendar.session_close("2026-11-27").to_pydatetime() == datetime(
        2026, 11, 27, 18, tzinfo=UTC
    )
    assert calendar.session_close("2026-12-24").hour == 18
    assert calendar.session_open("2026-03-06").hour == 14
    assert calendar.session_open("2026-03-09").hour == 13
    assert calendar.session_open("2026-10-30").hour == 13
    assert calendar.session_open("2026-11-02").hour == 14

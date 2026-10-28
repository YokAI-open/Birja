from decimal import Decimal

import pytest

from app.services.price_rules import Candidate, evaluate_price, mid_from_ticker, parse_price

D = Decimal


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("81042.3", D("81042.3")),
        ("0.079980700", D("0.079980700")),
        ("0", None),
        ("-1", None),
        ("", None),
        ("abc", None),
        ("NaN", None),
        ("Infinity", None),
        ("-Infinity", None),
        (1.5, None),
        (None, None),
        (5, None),
    ],
)
def test_parse_price(raw: object, expected: Decimal | None) -> None:
    assert parse_price(raw) == expected


def _entry(bid: object, ask: object) -> dict[str, object]:
    return {"b": [bid, "1", "1.000"], "a": [ask, "1", "1.000"]}


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        (_entry("0.079980700", "0.079990700"), D("0.07998570")),
        (_entry("100", "100"), D("100.00000000")),
        # 9th decimal exactly half: 1.0000000015 -> 8dp half-even
        (_entry("1.000000001", "1.000000002"), D("1.00000000")),
        (_entry("1.000000003", "1.000000004"), D("1.00000000")),
        (_entry("1.000000002", "1.000000003"), D("1.00000000")),
        (_entry("1.00000002", "1.00000003"), D("1.00000002")),
        (_entry("1.00000001", "1.00000002"), D("1.00000002")),
        (_entry("101", "100"), None),
        ({"b": ["1", "1", "1"]}, None),
        ({"a": ["1", "1", "1"]}, None),
        ({"a": [], "b": ["1"]}, None),
        ({"a": ["1"], "b": []}, None),
        ({"a": "1", "b": ["1"]}, None),
        ({"a": ["1"], "b": "1"}, None),
        ("nope", None),
        (None, None),
        (_entry("0", "0"), None),
        (_entry("abc", "1"), None),
        (_entry("1", "-1"), None),
    ],
)
def test_mid_from_ticker(entry: object, expected: Decimal | None) -> None:
    assert mid_from_ticker(entry) == expected


def test_mid_zero_after_rounding_is_rejected() -> None:
    # Both sides positive but the mid rounds to 0 at 8 dp.
    assert mid_from_ticker(_entry("0.000000001", "0.000000002")) is None


@pytest.mark.parametrize(
    ("bid", "ask", "expected"),
    [
        ("999999999999.99999998", "999999999999.99999998", D("999999999999.99999998")),
        ("999999999999", "1000000000000", None),
        ("1e12", "1e12", None),
        ("1e13", "1e13", None),
        ("1e30", "1e30", None),
        # Below 1e12 before rounding, exactly 1e12 after: still too big for NUMERIC(20,8).
        ("999999999999.999999999", "999999999999.999999999", None),
    ],
)
def test_mid_must_fit_numeric_20_8(bid: str, ask: str, expected: Decimal | None) -> None:
    assert mid_from_ticker(_entry(bid, ask)) == expected


def test_first_observation_accepts() -> None:
    assert evaluate_price(None, D(100), None) == ("accept", None)


@pytest.mark.parametrize(
    ("new", "decision"),
    [
        (D(125), "accept"),
        (D(75), "accept"),
        (D(100), "accept"),
        (D("125.00000001"), "reject_spike"),
        (D("74.9"), "reject_spike"),
    ],
)
def test_move_threshold(new: Decimal, decision: str) -> None:
    result, cand = evaluate_price(D(100), new, None)
    assert result == decision
    if decision == "reject_spike":
        assert cand == Candidate(new, 1)
    else:
        assert cand is None


def test_confirmation_after_three_polls() -> None:
    d1, c1 = evaluate_price(D(100), D(200), None)
    assert (d1, c1) == ("reject_spike", Candidate(D(200), 1))
    d2, c2 = evaluate_price(D(100), D(205), c1)
    assert (d2, c2) == ("reject_spike", Candidate(D(200), 2))
    d3, c3 = evaluate_price(D(100), D(199), c2)
    assert (d3, c3) == ("accept_confirmed", None)


def test_candidate_replaced_when_outside_tolerance() -> None:
    _, c1 = evaluate_price(D(100), D(200), None)
    assert evaluate_price(D(100), D(260), c1) == ("reject_spike", Candidate(D(260), 1))


def test_candidate_cleared_on_normal_poll() -> None:
    _, c1 = evaluate_price(D(100), D(200), None)
    assert evaluate_price(D(100), D(101), c1) == ("accept", None)


@pytest.mark.parametrize("bad", [D(0), D(-1), D("NaN"), D("Infinity")])
def test_invalid_keeps_candidate(bad: Decimal) -> None:
    cand = Candidate(D(200), 2)
    assert evaluate_price(D(100), bad, cand) == ("reject_invalid", cand)
    assert evaluate_price(None, bad, None) == ("reject_invalid", None)


def test_confirm_n_is_a_parameter() -> None:
    _, c1 = evaluate_price(D(100), D(200), None, confirm_n=2)
    assert evaluate_price(D(100), D(201), c1, confirm_n=2) == ("accept_confirmed", None)


def test_tolerances_are_parameters() -> None:
    assert evaluate_price(D(100), D(110), None, max_move=D("0.05"))[0] == "reject_spike"
    _, c1 = evaluate_price(D(100), D(200), None)
    # 210 is 5% from 200: inside default tolerance, outside a 1% tolerance
    assert evaluate_price(D(100), D(210), c1, confirm_tol=D("0.01"))[1] == Candidate(D(210), 1)

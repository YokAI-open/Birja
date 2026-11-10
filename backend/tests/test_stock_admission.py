"""Synthetic permissions test program behavior, never actual provider rights."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import SchedulerSettings, Settings
from app.services.stock_admission import ProductAdmission, evaluate_admission

NOW = datetime(2026, 11, 10, 15, tzinfo=UTC)


def admitted(product: str = "quotes") -> ProductAdmission:
    fields = {
        "quotes": ["bid", "ask", "event_at", "symbol"],
        "reference": ["symbol", "name", "exchange", "provider_asset_id"],
        "actions": ["event_id", "revision", "symbol", "event_type", "effective_date"],
        "status": ["symbol", "status", "event_at"],
        "calendar": ["exchange", "session_date", "opens_at", "closes_at"],
    }
    return ProductAdmission(
        product=product,
        state="approved",
        generation=4,
        reviewed_at=NOW - timedelta(hours=1),
        valid_from=NOW - timedelta(hours=2),
        valid_until=NOW + timedelta(hours=8),
        evidence_ref="secure-review:synthetic",
        terms_version="synthetic-v1",
        collection_allowed=True,
        display_allowed=True,
        derived_allowed=True,
        retention_allowed=True,
        scope={
            "application": "birja",
            "audience": "authenticated-users",
            "account": "birja",
            "server": "birja",
            "feed": "iex",
        },
        quota={
            "requests_per_minute": 20,
            "symbols_per_request": 20,
            "max_response_bytes": 262144,
            "retention_seconds": 86400,
        },
        allowed_fields=fields[product],
        attribution="IEX prices",
    )


@pytest.mark.parametrize("product", ["reference", "quotes", "actions", "status"])
@pytest.mark.parametrize("purpose", ["collection", "display", "derived", "retention"])
async def test_complete_specific_evidence_allows_only_requested_purpose(
    product: str, purpose: str
) -> None:
    evidence = admitted(product)
    result = evaluate_admission(evidence, product, purpose, NOW, expected_generation=4)
    assert result.allowed
    assert result.generation == 4
    assert result.valid_until == evidence.valid_until
    assert result.attribution == "IEX prices"


@pytest.mark.parametrize("purpose", ["collection", "display", "derived", "retention"])
async def test_purpose_rights_are_independent(purpose: str) -> None:
    evidence = replace(admitted(), **{f"{purpose}_allowed": False})
    assert not evaluate_admission(evidence, "quotes", purpose, NOW).allowed
    other = "display" if purpose != "display" else "collection"
    assert evaluate_admission(evidence, "quotes", other, NOW).allowed


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "revoked"},
        {"state": "denied"},
        {"product": "actions"},
        {"valid_until": NOW},
        {"valid_from": NOW + timedelta(microseconds=1)},
        {"reviewed_at": NOW + timedelta(seconds=1)},
        {"reviewed_at": None},
        {"evidence_ref": None},
        {"terms_version": ""},
        {"generation": 0},
        {"generation": True},
        {"allowed_fields": ["bid"]},
        {"quota": {}},
        {"attribution": ""},
        {"valid_until": NOW.replace(tzinfo=None)},
    ],
)
async def test_incomplete_or_invalid_evidence_denies(changes: dict[str, object]) -> None:
    result = evaluate_admission(replace(admitted(), **changes), "quotes", "display", NOW)
    assert not result.allowed
    assert not result.attribution


@pytest.mark.parametrize(
    "field,value",
    [
        ("application", "other"),
        ("audience", "public"),
        ("account", "other"),
        ("server", "other"),
        ("feed", "sip"),
    ],
)
async def test_wrong_scope_denies(field: str, value: str) -> None:
    evidence = admitted()
    assert not evaluate_admission(
        replace(evidence, scope={**evidence.scope, field: value}), "quotes", "collection", NOW
    ).allowed


async def test_missing_unknown_and_generation_race_fail_closed() -> None:
    assert not evaluate_admission(None, "quotes", "display", NOW).allowed
    assert not evaluate_admission(admitted(), "unknown", "display", NOW).allowed
    assert not evaluate_admission(admitted(), "quotes", "unknown", NOW).allowed
    previous = evaluate_admission(admitted(), "quotes", "display", NOW)
    assert previous.allowed
    changed = replace(admitted(), generation=5)
    assert not evaluate_admission(
        changed, "quotes", "display", NOW, expected_generation=previous.generation
    ).allowed
    assert not evaluate_admission(admitted(), "quotes", "display", NOW + timedelta(hours=8)).allowed
    assert not evaluate_admission(admitted(), "quotes", "display", NOW.replace(tzinfo=None)).allowed


def calendar_evidence() -> ProductAdmission:
    return replace(
        admitted("calendar"),
        calendar={
            "exchanges": ["XNYS", "XNAS"],
            "version": "synthetic-2026",
            "sources": [
                "https://www.nyse.com/markets/hours-calendars",
                "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
            ],
            "review_valid_until": (NOW + timedelta(hours=8)).isoformat(),
            "coverage_start": (NOW.date() - timedelta(days=45)).isoformat(),
            "coverage_end": (NOW.date() + timedelta(days=90)).isoformat(),
            "overrides": [
                {
                    "exchange": "XNYS",
                    "date": "2026-11-27",
                    "state": "shortened",
                    "opens_at": "2026-11-27T14:30:00+00:00",
                    "closes_at": "2026-11-27T18:00:00+00:00",
                    "source": "https://www.nyse.com/markets/hours-calendars",
                }
            ],
        },
    )


async def test_calendar_authority_is_bounded_and_limits_decision_expiry() -> None:
    evidence = calendar_evidence()
    evidence = replace(
        evidence,
        calendar={
            **evidence.calendar,
            "review_valid_until": (NOW + timedelta(hours=1)).isoformat(),
        },
    )
    decision = evaluate_admission(evidence, "calendar", "derived", NOW)
    assert decision.allowed
    assert decision.valid_until == NOW + timedelta(hours=1)


@pytest.mark.parametrize(
    "changes",
    [
        {"exchanges": ["XNYS"]},
        {"sources": ["https://unverified.example/calendar"]},
        {"version": ""},
        {"review_valid_until": NOW.isoformat()},
        {"review_valid_until": (NOW + timedelta(days=2)).isoformat()},
        {"coverage_start": (NOW.date() - timedelta(days=46)).isoformat()},
        {"coverage_end": (NOW.date() + timedelta(days=91)).isoformat()},
        {"coverage_start": "garbage"},
        {"overrides": [{}]},
    ],
)
async def test_calendar_invalid_or_expired_authority_is_unknown(changes: dict[str, object]) -> None:
    evidence = calendar_evidence()
    decision = evaluate_admission(
        replace(evidence, calendar={**evidence.calendar, **changes}), "calendar", "derived", NOW
    )
    assert not decision.allowed
    assert decision.reason == "unknown"


@pytest.mark.parametrize(
    "changes",
    [
        {"date": "2028-01-01"},
        {"state": "open"},
        {"exchange": "OTHER"},
        {"source": "http://www.nyse.com/untrusted"},
        {"closes_at": "2026-11-27T14:00:00Z"},
        {"opens_at": "2026-11-27T14:30:00"},
        {"closes_at": "2026-11-28T18:00:00Z"},
    ],
)
async def test_calendar_override_requires_verified_unique_dated_utc_bounds(
    changes: dict[str, object],
) -> None:
    evidence = calendar_evidence()
    override = {**evidence.calendar["overrides"][0], **changes}
    bad = replace(evidence, calendar={**evidence.calendar, "overrides": [override]})
    assert not evaluate_admission(bad, "calendar", "derived", NOW).allowed
    duplicate = replace(
        evidence, calendar={**evidence.calendar, "overrides": evidence.calendar["overrides"] * 2}
    )
    assert not evaluate_admission(duplicate, "calendar", "derived", NOW).allowed


def scheduler_config(**extra: object) -> SchedulerSettings:
    return SchedulerSettings(
        env="test",
        database_url="postgresql+asyncpg://u:pw@h/db",
        redis_url="redis://:pw@h:6379/0",
        **extra,
    )  # type: ignore[arg-type]


async def test_disabled_configuration_needs_no_provider_secrets() -> None:
    settings = scheduler_config()
    assert settings.stock_data_enabled is False
    assert settings.stock_feed == "iex"
    assert settings.stock_poll_interval_seconds == 60
    assert settings.alpaca_api_key is None
    assert settings.alpaca_secret_key is None


async def test_enabled_scheduler_requires_both_keys_and_sanitizes_errors() -> None:
    for values in ({}, {"alpaca_api_key": "private-marker"}):
        with pytest.raises(ValidationError) as exc:
            scheduler_config(stock_data_enabled=True, **values)
        assert "private-marker" not in str(exc.value)
    settings = scheduler_config(
        stock_data_enabled=True, alpaca_api_key="private-marker", alpaca_secret_key="secret-marker"
    )
    assert isinstance(settings.alpaca_api_key, SecretStr)
    assert "private-marker" not in repr(settings)
    assert "secret-marker" not in settings.model_dump_json()
    # Configured keys and enable flag never replace product evidence.
    assert not evaluate_admission(None, "quotes", "collection", NOW).allowed


async def test_api_settings_ignore_provider_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPACA_API_KEY", "private-marker")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret-marker")
    settings = Settings()
    assert settings.stock_data_enabled is False
    assert "alpaca_api_key" not in settings.model_dump()
    assert "alpaca_secret_key" not in settings.model_dump()
    assert "private-marker" not in repr(settings)


@pytest.mark.parametrize(
    "values",
    [
        {"stock_feed": "sip"},
        {"stock_feed": "fake"},
        {"stock_poll_interval_seconds": 59},
        {"stock_poll_interval_seconds": 121},
        {"stock_request_timeout_seconds": 0},
        {"stock_request_timeout_seconds": 11},
        {"stock_max_retries": -1},
        {"stock_max_retries": 3},
        {"stock_cycle_budget_seconds": 21},
        {"stock_max_response_bytes": 1048577},
        {"stock_data_account": ""},
        {"stock_data_server": ""},
        {"stock_request_timeout_seconds": 10, "stock_max_retries": 2},
    ],
)
async def test_invalid_stock_configuration_is_rejected(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        scheduler_config(**values)

import json
from argparse import Namespace
from datetime import timedelta
from pathlib import Path

import pytest

from app.services.stock_catalog_sources import CatalogSourceError
from app.tasks.stock_catalog_inventory import validate_manifest
from app.tasks.stock_catalog_reference_inventory import _inventory
from tests.test_stock_catalog_pillar import CAT, CAT_TIME, DAY, FILENAME, PILLAR
from tests.test_stock_catalog_publish import _rights
from tests.test_stock_catalog_sources import directory, mapping


@pytest.fixture
def inputs(tmp_path: Path) -> tuple[Namespace, list[dict]]:
    paths = Namespace(
        nasdaq=tmp_path / "nasdaq.txt",
        cat=tmp_path / "cat.txt",
        pillar=tmp_path / FILENAME,
        mapping=tmp_path / "mapping.jsonl",
        fixture=CAT_TIME,
        rights=None,
        cat_published_at=CAT_TIME,
        trade_date=DAY,
    )
    paths.nasdaq.write_bytes(
        directory(
            "nasdaqlisted",
            "FXCO|Fixture ordinary|Q|N|N|100|N|N",
            "FXOU|Fixture unit|Q|N|N|100|N|N",
            time="1125202614:11",
        )
    )
    paths.cat.write_bytes(CAT)
    paths.pillar.write_bytes(PILLAR)
    observations = []
    for venue, symbol, code, identity, kind in (
        ("NYSE", "FXCA.A", "UN", "BBG000000013", "Common Stock"),
        ("NYSE", "FXCA.B", "UN", "BBG000000025", "REIT"),
        ("NASDAQ", "FXCO", "UW", "BBG000000037", "Common Stock"),
    ):
        record = mapping(symbol, code, identity, kind=kind, broad_type=kind)
        record["name"] = f"Reusable source name {symbol}"
        observations.append(
            {
                "venue": venue,
                "symbol": symbol,
                "observation": {
                    "observed_at": (CAT_TIME - timedelta(minutes=15)).isoformat(),
                    "result": {"data": [record]},
                },
            }
        )
    return paths, observations


def test_reference_catalog_keeps_distinct_classes_and_reusable_names(inputs) -> None:
    paths, observations = inputs
    paths.mapping.write_text("\n".join(json.dumps(row) for row in observations) + "\n")
    manifest = _inventory(paths, CAT_TIME)
    assert manifest.complete
    assert manifest.coverage["NYSE"].included == 2
    assert manifest.coverage["NYSE"].excluded == 1
    assert manifest.coverage["NASDAQ"].included == 1
    assert manifest.coverage["NASDAQ"].excluded == 1
    included = {row.ticker: row for row in manifest.rows if row.disposition == "included"}
    assert included["FXCA.B"].name_source == "openfigi_nyse"
    assert included["FXCA.B"].company_name == "Reusable source name FXCA.B"
    assert included["FXCA.B"].classification == "common_stock"
    assert included["FXCO"].company_name == "Fixture ordinary"
    assert included["FXCO"].classification == "ordinary_shares"
    assert len({row.identity_key for row in included.values()}) == 3
    assert "Fixture Class A common" not in manifest.model_dump_json()
    with pytest.raises(CatalogSourceError, match="explicit rights"):
        validate_manifest(manifest.model_copy(update={"mode": "live"}), CAT_TIME)


def test_unmatched_and_conflicting_stock_identities_remain_unresolved(inputs) -> None:
    paths, observations = inputs
    observations.pop(1)
    candidates = observations[0]["observation"]["result"]["data"]
    candidates.append({**candidates[0], "shareClassFIGI": "BBG000000119"})
    paths.mapping.write_text("\n".join(json.dumps(row) for row in observations) + "\n")
    manifest = _inventory(paths, CAT_TIME)
    assert not manifest.complete
    assert manifest.coverage["NYSE"].unresolved == 2
    assert manifest.coverage["NYSE"].excluded == 1
    assert manifest.coverage["NASDAQ"].included == 1


def test_comparator_detects_a_missing_primary_common_listing(inputs) -> None:
    paths, observations = inputs
    paths.mapping.write_text("\n".join(json.dumps(row) for row in observations) + "\n")
    original = paths.cat.read_bytes()
    paths.cat.write_bytes(
        original.replace(b"FXCA B|Fixture Class B common|N|N\n", b"").replace(
            b"20261125140318|7", b"20261125140318|6"
        )
    )
    with pytest.raises(CatalogSourceError, match="NYSE references disagree"):
        _inventory(paths, CAT_TIME)


def test_closed_end_fund_does_not_become_an_eligible_share(inputs) -> None:
    paths, observations = inputs
    candidate = observations[0]["observation"]["result"]["data"][0]
    candidate.update(securityType="Closed-End Fund", securityType2="Mutual Fund")
    paths.mapping.write_text("\n".join(json.dumps(row) for row in observations) + "\n")
    manifest = _inventory(paths, CAT_TIME)
    assert manifest.complete
    assert manifest.coverage["NYSE"].included == 1
    assert manifest.coverage["NYSE"].excluded == 2
    assert any(row.reason == "corroborated_noncommon_class" for row in manifest.rows)


@pytest.mark.parametrize("conflicting_field", [None, "shareClassFIGI", "compositeFIGI"])
def test_vendor_class_alias_and_nasdaq_fallback(inputs, conflicting_field: str | None) -> None:
    paths, observations = inputs
    observations[0]["symbol"] = "FXCA/A"
    observations[0]["observation"]["result"]["data"][0]["ticker"] = "FXCA/A"
    record = observations[2]["observation"]
    primary = record["result"]["data"][0]
    composite = {**primary, "exchCode": "US"}
    if conflicting_field is not None:
        composite[conflicting_field] = "BBG000000119"
    warning = {"warning": "No current mapping"}
    record["result"] = {
        "fallback": {
            "primary": warning,
            "alternates": [
                {"exchange": "UQ", "result": {"data": [{**primary, "exchCode": "UQ"}]}},
                {"exchange": "UR", "result": warning},
                {"exchange": "US", "result": {"data": [composite]}},
            ],
        }
    }
    paths.mapping.write_text("\n".join(json.dumps(row) for row in observations) + "\n")
    manifest = _inventory(paths, CAT_TIME)
    assert manifest.complete is (conflicting_field is None)
    included = {row.ticker: row for row in manifest.rows if row.disposition == "included"}
    assert {alias.symbol for alias in included["FXCA.A"].aliases} == {"FXCA/A"}
    assert included["FXCA.A"].identity_key != included["FXCA.B"].identity_key
    assert ("FXCO" in included) is (conflicting_field is None)


def _exception(row, *, ticker=None, classification=None, **overrides):
    return {
        "source": row.source,
        "row_digest": row.row_digest,
        "ticker": ticker or row.ticker,
        "listing_exchange": row.listing_exchange,
        "issue_group": "Issuer-Exact-Ordinary-Class",
        "reviewed_at": CAT_TIME.isoformat(),
        "source_url": "https://www.sec.gov/Archives/edgar/data/1001/stock-class.htm",
        "classification": classification or row.classification or "ordinary_shares",
        "evidence_digest": "5" * 64,
        **overrides,
    }


def _exceptions(paths, reviews, *, mode=0o600):
    paths.exceptions = paths.mapping.with_name("exceptions.json")
    paths.exceptions.write_text(json.dumps(reviews))
    paths.exceptions.chmod(mode)


def _observations(paths, rows):
    paths.mapping.write_text("\n".join(json.dumps(row) for row in rows) + "\n")


def test_reviewed_nasdaq_fallback_keeps_a_stable_issue_identity(inputs) -> None:
    paths, observations = inputs
    _observations(paths, observations[:-1])
    initial = _inventory(paths, CAT_TIME)
    candidate = next(row for row in initial.rows if row.ticker == "FXCO")
    assert initial.coverage["NASDAQ"].unresolved == 1
    exception = _exception(candidate)
    _exceptions(paths, [exception])
    reviewed = _inventory(paths, CAT_TIME)
    included = next(row for row in reviewed.rows if row.ticker == "FXCO")
    assert reviewed.complete
    assert included.classification == "ordinary_shares"
    assert included.reason == "reviewed_issue_evidence"
    assert included.identity_key.startswith("review:")
    assert exception["source_url"] not in reviewed.model_dump_json()

    exception["evidence_digest"] = "6" * 64
    _exceptions(paths, [exception])
    refreshed = next(row for row in _inventory(paths, CAT_TIME).rows if row.ticker == "FXCO")
    assert refreshed.identity_key == included.identity_key
    assert refreshed.evidence_digest != included.evidence_digest


def test_reviewed_nasdaq_keeps_matching_mapping_identity_and_aliases(inputs) -> None:
    paths, observations = inputs
    _observations(paths, observations)
    initial = _inventory(paths, CAT_TIME)
    candidate = next(row for row in initial.rows if row.ticker == "FXCO")
    assert candidate.identity_key.startswith("figi:")
    _exceptions(paths, [_exception(candidate)])
    manifest = _inventory(paths, CAT_TIME)
    included = next(row for row in manifest.rows if row.ticker == "FXCO")
    assert included.reason == "corroborated_share_class"
    assert included.identity_key == candidate.identity_key
    assert included.aliases == candidate.aliases
    assert included.evidence_at == candidate.evidence_at


def test_reviewed_nyse_exclusion_binds_both_comparators_and_redacts_private_fields(inputs) -> None:
    paths, observations = inputs
    _observations(paths, observations[1:])
    pending = _inventory(paths, CAT_TIME)
    candidate = next(
        row
        for row in pending.rows
        if row.source == "openfigi_nyse" and row.disposition == "unresolved"
    )
    assert pending.coverage["NYSE"].unresolved == 1
    _exceptions(paths, [_exception(candidate, ticker="FXCA A", classification="out_of_scope")])
    manifest = _inventory(paths, CAT_TIME)
    excluded = next(row for row in manifest.rows if row.row_key == candidate.row_key)
    assert manifest.complete
    assert manifest.coverage["NYSE"].excluded == 2
    assert excluded.disposition == "excluded" and excluded.reason == "reviewed_issue_evidence"
    assert (excluded.ticker, excluded.company_name, excluded.aliases) == ("", "", ())
    assert "FXCA A" not in manifest.model_dump_json()
    assert "Fixture Class A common" not in manifest.model_dump_json()


@pytest.mark.parametrize(
    ("ticker", "classification"),
    [
        ("FXCA B", "out_of_scope"),
        ("FXCA A", "common_stock"),
    ],
)
def test_reviewed_nyse_rejects_other_comparator_and_all_inclusion(
    ticker, classification, inputs
) -> None:
    paths, observations = inputs
    _observations(paths, observations[1:])
    pending = _inventory(paths, CAT_TIME)
    candidate = next(
        row
        for row in pending.rows
        if row.source == "openfigi_nyse" and row.disposition == "unresolved"
    )
    _exceptions(paths, [_exception(candidate, ticker=ticker, classification=classification)])
    with pytest.raises(CatalogSourceError, match="differs from exact comparator evidence"):
        _inventory(paths, CAT_TIME)


@pytest.mark.parametrize(
    ("overrides", "refusal"),
    [
        ({"source_url": "https://www.nyse.com/issuer"}, "official SEC"),
        ({"row_digest": "9" * 64}, "exactly one"),
        ({"ticker": "FXCA"}, "source row or date"),
        (
            {"reviewed_at": (CAT_TIME - timedelta(days=8)).isoformat()},
            "source row or date",
        ),
        ({"classification": "out_of_scope"}, "conflicts with a resolved"),
    ],
)
def test_issuer_review_refuses_stale_or_conflicting_binding(inputs, overrides, refusal) -> None:
    paths, observations = inputs
    _observations(paths, observations)
    manifest = _inventory(paths, CAT_TIME)
    candidate = next(row for row in manifest.rows if row.ticker == "FXCO")
    _exceptions(paths, [_exception(candidate, **overrides)])
    with pytest.raises(CatalogSourceError, match=refusal):
        _inventory(paths, CAT_TIME)


def test_private_issuer_review_refuses_duplicate_rows_and_exposed_file(inputs) -> None:
    paths, observations = inputs
    _observations(paths, observations)
    manifest = _inventory(paths, CAT_TIME)
    candidate = next(row for row in manifest.rows if row.ticker == "FXCO")
    _exceptions(paths, [_exception(candidate)], mode=0o644)
    with pytest.raises(CatalogSourceError, match="mode-0600"):
        _inventory(paths, CAT_TIME)
    _exceptions(paths, [_exception(candidate), _exception(candidate)])
    with pytest.raises(CatalogSourceError, match="repeats a directory row"):
        _inventory(paths, CAT_TIME)


def test_live_issuer_review_requires_dated_issuer_exception_rights(inputs) -> None:
    paths, observations = inputs
    _observations(paths, observations)
    current = _inventory(paths, CAT_TIME)
    candidate = next(row for row in current.rows if row.ticker == "FXCO")
    _exceptions(paths, [_exception(candidate)])
    rights = [
        item.model_copy(
            update={
                "artifact": "openfigi_nyse" if item.artifact == "otherlisted" else item.artifact,
                "reviewed_at": CAT_TIME - timedelta(hours=1),
                "valid_until": CAT_TIME + timedelta(hours=1),
            }
        ).model_dump(mode="json")
        for item in _rights()
        if item.artifact != "issuer_exception"
    ]
    paths.rights = paths.mapping.with_name("rights.json")
    paths.rights.write_text(json.dumps(rights))
    paths.fixture = None
    with pytest.raises(CatalogSourceError, match="explicit rights required for issuer_exception"):
        _inventory(paths, CAT_TIME)

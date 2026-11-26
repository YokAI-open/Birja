from datetime import UTC, datetime, timedelta

import pytest

from app.services.stock_catalog_classification import (
    ReviewedIssue,
    classify_mapping,
    classify_reviewed,
)
from app.services.stock_catalog_sources import (
    HEADERS,
    CatalogSourceError,
    DirectorySource,
    parse_directory,
    validate_directory_pair,
)

AS_OF = datetime(2026, 11, 24, 18, tzinfo=UTC)
CAPTURE = "1124202612:11"
NASDAQ_COMMON = "FSTA|Fixture Alpha - Class A Common Stock|Q|N|N|100|N|N"
NYSE_COMMON = "FST.B|Fixture Alpha - Class B Common Stock|N|FST.B|N|100|N|FST/B"


def directory(source: DirectorySource, *rows: str, time: str = CAPTURE) -> bytes:
    suffix = "|||||||" if source == "nasdaqlisted" else "||||||"
    lines = [HEADERS[source], *rows, f"File Creation Time: {time}{suffix}"]
    return ("\n".join(lines) + "\n").encode()


def mapping(
    symbol: str,
    exchange: str,
    share_class: str = "BBG000000011",
    *,
    kind: str = "Common Stock",
    broad_type: str = "Common Stock",
) -> dict[str, object]:
    return {
        "ticker": symbol,
        "exchCode": exchange,
        "marketSector": "Equity",
        "securityType": kind,
        "securityType2": broad_type,
        "shareClassFIGI": share_class,
        "compositeFIGI": "BBG000000012",
        "name": "Unused provider text",
    }


def test_directory_pair_preserves_venue_provenance_and_symbol_spelling() -> None:
    nasdaq = parse_directory("nasdaqlisted", directory("nasdaqlisted", NASDAQ_COMMON))
    other = parse_directory(
        "otherlisted",
        directory("otherlisted", NYSE_COMMON).replace(b"\n", b"\r\n"),
    )

    assert validate_directory_pair(nasdaq, other, AS_OF) == (nasdaq, other)
    assert nasdaq.published_at == datetime(2026, 11, 24, 17, 11, tzinfo=UTC)
    assert nasdaq.rows[0].figi_exchange == "UW"
    row = other.rows[0]
    assert row.listing_exchange == "NYSE"
    assert row.row_key == "otherlisted:1"
    assert [(alias.namespace, alias.symbol) for alias in row.aliases] == [
        ("act", "FST.B"),
        ("cqs", "FST.B"),
        ("nasdaq", "FST/B"),
    ]


@pytest.mark.parametrize("cqs", ["FLpB", "FLr", "FL.Bw"])
def test_cqs_qualified_issue_keeps_exact_case_and_is_excluded(cqs: str) -> None:
    snapshot = parse_directory(
        "otherlisted",
        directory(
            "otherlisted",
            f"FL$B|Fixture qualified issue|N|{cqs}|N|100|N|FL-B",
            f"{cqs.upper()}|Fixture common stock|N|{cqs.upper()}|N|100|N|{cqs.upper()}",
        ),
    )
    qualified, common = snapshot.rows
    assert qualified.aliases[1].symbol == cqs
    assert qualified.exclusion == "qualified_cqs_issue"
    assert common.aliases[1].symbol == cqs.upper()
    assert common.exclusion is None


def test_other_directory_excludes_out_of_scope_texas_venues() -> None:
    snapshot = parse_directory(
        "otherlisted",
        directory(
            "otherlisted",
            "FTA|Fixture active NYSE Texas stock|M|FTA|N|100|N|FTA",
            "FTB|Fixture Texas Stock Exchange test issue|F|FTB|N|10|Y|FTB",
            NYSE_COMMON,
        ),
    )
    assert [(row.listing_exchange, row.exclusion) for row in snapshot.rows] == [
        (None, "other_primary_exchange"),
        (None, "other_primary_exchange"),
        ("NYSE", None),
    ]


def test_other_directory_still_accepts_padded_terminal_timestamp() -> None:
    payload = directory("otherlisted", NYSE_COMMON)
    padded = payload.replace(b"||||||\n", b"|||||||\n")
    assert (
        parse_directory("otherlisted", padded).published_at
        == parse_directory("otherlisted", payload).published_at
    )


@pytest.mark.parametrize(
    "old,new",
    [
        (b"||||||\n", b"|||||\n"),
        (b"||||||\n", b"||||||extra\n"),
        (b"|N|FST.B|", b"|X|FST.B|"),
        (b"|N|FST.B|", b"|N|FSTxB|"),
        (b"|N|FST.B|", b"|N|FSTppB|"),
        (b"|N|FST.B|", b"|N|FSTp BROKEN|"),
        (b"|N|FST/B\n", b"|N|FSTpB\n"),
    ],
)
def test_other_directory_refuses_invalid_venue_aliases_or_footer(old: bytes, new: bytes) -> None:
    payload = directory("otherlisted", NYSE_COMMON)
    assert old in payload
    with pytest.raises(CatalogSourceError):
        parse_directory("otherlisted", payload.replace(old, new))


@pytest.mark.parametrize(
    "old,new",
    [
        (b"NextShares", b"Next Shares"),
        (b"FSTA|", b"FSTA||"),
        (b"|Q|N|", b"|P|N|"),
        (b"|Q|N|", b"|Q|T|"),
        (b"|N|N\n", b"|A|N\n"),
        (b"|N|N\n", b"|N|X\n"),
        (b"|100|", b"|0|"),
        (b"Fixture", b"\xffixture"),
        (b"1124202612:11", b"1124202612:99"),
        (b"|||||||\n", b"||||||\n"),
        (b"|||||||\n", b"|||||||"),
    ],
)
def test_bad_directory_is_refused(old: bytes, new: bytes) -> None:
    payload = directory("nasdaqlisted", NASDAQ_COMMON)
    assert old in payload
    with pytest.raises(CatalogSourceError):
        parse_directory("nasdaqlisted", payload.replace(old, new))


def test_pair_refuses_future_stale_different_snapshot_and_missing_venue() -> None:
    nasdaq = parse_directory("nasdaqlisted", directory("nasdaqlisted", NASDAQ_COMMON))
    other = parse_directory("otherlisted", directory("otherlisted", NYSE_COMMON))
    mismatch = parse_directory(
        "otherlisted", directory("otherlisted", NYSE_COMMON, time="1124202609:11")
    )
    out_of_scope = parse_directory(
        "otherlisted", directory("otherlisted", NYSE_COMMON.replace("|N|", "|P|", 1))
    )
    with pytest.raises(CatalogSourceError, match="stale or in the future"):
        validate_directory_pair(nasdaq, other, AS_OF - timedelta(hours=1))
    with pytest.raises(CatalogSourceError, match="stale or in the future"):
        validate_directory_pair(nasdaq, other, AS_OF + timedelta(days=5))
    with pytest.raises(CatalogSourceError, match="incoherent"):
        validate_directory_pair(nasdaq, mismatch, AS_OF)
    with pytest.raises(CatalogSourceError, match="no NYSE"):
        validate_directory_pair(nasdaq, out_of_scope, AS_OF)


def test_classification_preserves_share_classes_and_listing_names() -> None:
    alpha = parse_directory("nasdaqlisted", directory("nasdaqlisted", NASDAQ_COMMON)).rows[0]
    beta = parse_directory("otherlisted", directory("otherlisted", NYSE_COMMON)).rows[0]
    first = classify_mapping(alpha, {"data": [mapping("FSTA", "UW")]}, AS_OF)
    second = classify_mapping(beta, {"data": [mapping("FST/B", "UN", "BBG000000013")]}, AS_OF)

    assert first.disposition == second.disposition == "included"
    assert (first.share_class, second.share_class) == ("A", "B")
    assert first.identity_key != second.identity_key
    assert second.aliases[-1].symbol == "FST/B"
    assert second.classification == "common_stock"
    assert second.company_name == beta.company_name
    assert second.name_source == "otherlisted"


def test_positive_ordinary_shares_and_explicit_exclusion() -> None:
    row = parse_directory("otherlisted", directory("otherlisted", NYSE_COMMON)).rows[0]
    ordinary = mapping("FST.B", "UN", kind="Ordinary Shares")
    assert classify_mapping(row, {"data": [ordinary]}, AS_OF).classification == "ordinary_shares"
    adr = mapping("FST.B", "UN", kind="ADR", broad_type="Depositary Receipt")
    result = classify_mapping(row, {"data": [adr]}, AS_OF)
    assert result.disposition == "excluded"
    assert result.identity_key is None


def test_unknown_ambiguous_or_unbound_mapping_remains_unresolved() -> None:
    row = parse_directory("otherlisted", directory("otherlisted", NYSE_COMMON)).rows[0]
    exact = mapping("FST.B", "UN")
    cases = [
        {"warning": "No identifier found"},
        {"data": [mapping("FSTB", "UN")]},
        {"data": [mapping("FST.B", "UW")]},
        {"data": [exact | {"shareClassFIGI": None}]},
        {"data": [exact | {"shareClassFIGI": exact["compositeFIGI"]}]},
        {"data": [exact, mapping("FST.B", "UN", "BBG000000013")]},
        {"data": [exact | {"securityType": "Unrecognized"}]},
    ]
    for case in cases:
        assert classify_mapping(row, case, AS_OF).disposition == "unresolved"
    with pytest.raises(ValueError, match="Invalid or failed"):
        classify_mapping(row, {"error": "Request failed"}, AS_OF)


def test_review_exception_binds_source_ticker_venue_group_and_date() -> None:
    row = parse_directory("otherlisted", directory("otherlisted", NYSE_COMMON)).rows[0]
    review = ReviewedIssue(
        source=row.source,
        row_digest=row.row_digest,
        ticker=row.ticker,
        listing_exchange="NYSE",
        issue_group="fixture-class-b",
        reviewed_at=AS_OF - timedelta(days=1),
        evidence_digest="b" * 64,
        classification="common_stock",
        source_url="https://www.sec.gov/Archives/edgar/data/1/fixture.htm",
    )
    result = classify_reviewed(row, review, AS_OF)
    assert result.disposition == "included"
    assert result.identity_key is not None and result.identity_key.startswith("review:")
    for change in (
        {"row_digest": "f" * 64},
        {"ticker": "FSTB"},
        {"listing_exchange": "NASDAQ"},
        {"source_url": "https://example.org/issue"},
        {"reviewed_at": AS_OF - timedelta(days=8)},
    ):
        assert (
            classify_reviewed(row, review.model_copy(update=change), AS_OF).disposition
            == "unresolved"
        )

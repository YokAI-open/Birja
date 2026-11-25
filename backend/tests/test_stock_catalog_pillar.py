from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

import pytest

from app.services.stock_catalog_pillar import (
    MAX_CAT_BYTES,
    MAX_PILLAR_BYTES,
    parse_cat_snapshot,
    parse_pillar_snapshot,
)
from app.services.stock_catalog_sources import CatalogSourceError

DAY = date(2026, 11, 25)
FILENAME = "NYSESymbolMapping_20261125.txt"
CAT_TIME = datetime(2026, 11, 25, 19, 30, tzinfo=UTC)
PILLAR = (
    b"FXCA A|FXCA.A|705|N|N|A|40|4|1|C||\n"
    b"FXCA B|FXCA.B|706|N|N|A|10|4|1|C||\n"
    b"FXCA PRB|FXCApB|707|N|N|A|100|4|1|P||\n"
    b"FXCO|FXCO|708|N|Q|C|100|4|1|O||\n"
    b"FXOU|FXOU|709|N|Q|C|100|4|1|U||\n"
    b"FXTG|FXTG|710|N|Q|C|100|4|1|T||\n"
    b"FXTE|FXTE|711|N|F|B|100|4|1|E||\n"
)
CAT = (
    b"symbol|issueName|listingExchange|testIssueFlag\n"
    b"FXCA A|Fixture Class A common|N|N\n"
    b"FXCA B|Fixture Class B common|N|N\n"
    b"FXCA PRB|Fixture preferred|N|N\n"
    b"FXCO|Fixture ordinary shares|Q|N\n"
    b"FXTG|Fixture test issue|Q|Y\n"
    b"FXTE|Fixture other exchange|F|N\n"
    b"FXUN|Fixture unaffiliated test||Y\n"
    b"20261125140318|7\n"
)


def test_pillar_preserves_issue_types_exactly_and_keeps_distinct_alias_namespaces() -> None:
    snapshot = parse_pillar_snapshot(PILLAR, filename=FILENAME, expected_trade_date=DAY)
    assert snapshot.trade_date == DAY
    assert snapshot.sha256 == sha256(PILLAR).hexdigest()
    assert snapshot.row_count == 7
    venue = snapshot.index_by_venue_symbol()
    cqs = snapshot.index_by_cqs_symbol()
    assert venue[("NYSE", "FXCA A")].common_class == "common_stock"
    assert venue[("NYSE", "FXCA A")] == cqs[("NYSE", "FXCA.A")]
    assert venue[("NYSE", "FXCA A")] != venue[("NYSE", "FXCA B")]
    assert ("NYSE", "FXCA.A") not in venue
    assert ("NYSE", "FXCA A") not in cqs
    assert ("NYSE", "FXCAPB") not in cqs
    assert cqs[("NYSE", "FXCApB")] == venue[("NYSE", "FXCA PRB")]
    assert venue[("NYSE", "FXCA PRB")].common_class is None
    assert venue[("NASDAQ", "FXCO")].common_class == "ordinary_shares"
    assert venue[("NASDAQ", "FXOU")].common_class is None
    assert ("NASDAQ", "FXTG") not in venue
    assert all(issue.venue_symbol != "FXTE" for issue in snapshot.issues)


@pytest.mark.parametrize("filename", ["NYSESymbolMapping_CERT_20261125.txt", "other.txt"])
def test_pillar_rejects_nonproduction_or_incorrect_file_name(filename: str) -> None:
    with pytest.raises(CatalogSourceError, match="trading date"):
        parse_pillar_snapshot(PILLAR, filename=filename, expected_trade_date=DAY)


@pytest.mark.parametrize(
    "old,new",
    [
        (b"|1|C||\n", b"|1|C|\n"),
        (b"|1|C||\n", b"|1|C|changed|\n"),
        (b"|1|C||\n", b"|1|K||\n"),
        (b"|N|N|A|", b"|N|N|B|"),
        (b"|N|F|B|", b"|N|X|B|"),
        (b"|705|", b"|a|"),
        (b"|FXCA.B|", b"|FXCA.A|"),
        (b"FXCA B|", b"FXCA A|"),
        (b"FXCA B|", b"FXCA  B|"),
        (b"FXCA B|", b"FXCA\x00 B|"),
        (b"FXCA.B", b"FXCA\xffB"),
    ],
)
def test_pillar_refuses_malformed_or_ambiguous_rows(old: bytes, new: bytes) -> None:
    with pytest.raises(CatalogSourceError):
        parse_pillar_snapshot(PILLAR.replace(old, new), filename=FILENAME, expected_trade_date=DAY)


def test_pillar_and_cat_refuse_truncation_or_excess_bytes() -> None:
    for value in (PILLAR[:-1], b"x" * MAX_PILLAR_BYTES + b"\n"):
        with pytest.raises(CatalogSourceError, match="truncated"):
            parse_pillar_snapshot(value, filename=FILENAME, expected_trade_date=DAY)
    for value in (CAT[:-1], b"x" * MAX_CAT_BYTES + b"\n"):
        with pytest.raises(CatalogSourceError, match="truncated"):
            parse_cat_snapshot(value, published_at=CAT_TIME, expected_trade_date=DAY)


def test_cat_comparator_matches_exact_venue_symbols_and_discards_report_text() -> None:
    data = CAT.replace(b"\n", b"\r\n")
    cat = parse_cat_snapshot(data, published_at=CAT_TIME, expected_trade_date=DAY)
    assert cat.trade_date == DAY
    assert cat.created_at == datetime(2026, 11, 25, 19, 3, 18, tzinfo=UTC)
    assert cat.published_at == CAT_TIME
    assert cat.sha256 == sha256(data).hexdigest()
    assert cat.row_count == 7
    assert cat.keys == {
        ("NYSE", "FXCA A"),
        ("NYSE", "FXCA B"),
        ("NYSE", "FXCA PRB"),
        ("NASDAQ", "FXCO"),
    }
    assert cat.test_symbols == {"FXTG", "FXUN"}
    assert "Fixture" not in repr(cat)
    pillar = parse_pillar_snapshot(PILLAR, filename=FILENAME, expected_trade_date=DAY)
    assert cat.keys <= pillar.index_by_venue_symbol().keys()


@pytest.mark.parametrize(
    "old,new",
    [
        (b"20261125140318|7\n", b"20261125140318|6\n"),
        (b"20261125140318|7\n", b"20261124140318|7\n"),
        (b"20261125140318|7\n", b"20261125160000|7\n"),
        (b"20261125140318|7\n", b"20261125140399|7\n"),
        (b"20261125140318|7\n", b"20261101013000|7\n"),
        (b"testIssueFlag", b"testIssue"),
        (b"|N|N\n", b"|N|N|\n"),
        (b"|N|N\n", b"|N|K\n"),
        (b"FXCA B|", b"FXCA A|"),
        (b"FXCA B|", b"FXCA.B|"),
        (b"|Q|N\n", b"|Q|Y\n"),
    ],
)
def test_cat_refuses_malformed_ambiguous_or_stale_reports(old: bytes, new: bytes) -> None:
    with pytest.raises(CatalogSourceError):
        parse_cat_snapshot(CAT.replace(old, new), published_at=CAT_TIME, expected_trade_date=DAY)


def test_cat_requires_a_same_day_timezone_aware_publication_timestamp() -> None:
    for published_at in (CAT_TIME.replace(tzinfo=None), CAT_TIME + timedelta(days=1)):
        with pytest.raises(CatalogSourceError, match="trading date"):
            parse_cat_snapshot(CAT, published_at=published_at, expected_trade_date=DAY)

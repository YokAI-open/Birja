import json
from argparse import Namespace
from datetime import timedelta
from pathlib import Path

import pytest

from app.services.stock_catalog_sources import CatalogSourceError
from app.tasks.stock_catalog_inventory import validate_manifest
from app.tasks.stock_catalog_reference_inventory import _inventory
from tests.test_stock_catalog_pillar import CAT, CAT_TIME, DAY, FILENAME, PILLAR
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

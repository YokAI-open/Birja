"""Seed independently sourced discovery identities, never provider eligibility.

Display identities/exchanges cross-checked in Phase 7 research, 2026-11-10:
https://www.sec.gov/files/company_tickers_exchange.json
No provider ID, quote, admission grant or account credit is inferred.

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STOCKS = (
    ("AAPL", "Apple", "NASDAQ"),
    ("MSFT", "Microsoft", "NASDAQ"),
    ("NVDA", "NVIDIA", "NASDAQ"),
    ("AMZN", "Amazon", "NASDAQ"),
    ("GOOGL", "Alphabet Class A", "NASDAQ"),
    ("META", "Meta Platforms", "NASDAQ"),
    ("TSLA", "Tesla", "NASDAQ"),
    ("AVGO", "Broadcom", "NASDAQ"),
    ("AMD", "Advanced Micro Devices", "NASDAQ"),
    ("COST", "Costco", "NASDAQ"),
    ("JPM", "JPMorgan Chase", "NYSE"),
    ("V", "Visa", "NYSE"),
    ("JNJ", "Johnson & Johnson", "NYSE"),
    ("PG", "Procter & Gamble", "NYSE"),
    ("KO", "Coca-Cola", "NYSE"),
    ("XOM", "ExxonMobil", "NYSE"),
    ("CVX", "Chevron", "NYSE"),
    ("HD", "Home Depot", "NYSE"),
    ("MCD", "McDonald's", "NYSE"),
    ("DIS", "Walt Disney", "NYSE"),
)


def upgrade() -> None:
    """Seed catalogue rows only; NULL provider identity means unverified."""
    for position, (symbol, name, exchange) in enumerate(STOCKS, start=1):
        # RETURNING resolves the generated identity without assuming sequence
        # positions or borrowing a similarly named crypto instrument.
        op.execute(
            sa.text("""WITH seeded AS (
            INSERT INTO coins(asset_class,symbol,name,sort_order)
            VALUES ('stock',:symbol,:name,:position) RETURNING id
        ) INSERT INTO stock_instruments(coin_id,listing_exchange,source,source_ref)
          SELECT id,:exchange,'sec',:source_ref FROM seeded""").bindparams(
                symbol=symbol,
                name=name,
                position=position,
                exchange=exchange,
                source_ref="https://www.sec.gov/files/company_tickers_exchange.json",
            )
        )


def downgrade() -> None:
    """Refuse any stock financial history before removing bounded seed rows."""
    # This conservative all-stock guard also protects identities inserted after
    # the seed. Even zero holdings are financial references, not expendable data.
    op.execute("""DO $guard$
    BEGIN
      LOCK TABLE coins, holdings, trades IN ACCESS EXCLUSIVE MODE;
      IF EXISTS (SELECT FROM holdings h JOIN coins c ON c.id=h.coin_id
                 WHERE c.asset_class='stock') OR
         EXISTS (SELECT FROM trades t JOIN coins c ON c.id=t.coin_id
                 WHERE c.asset_class='stock') THEN
        RAISE EXCEPTION 'stock financial references prevent seed downgrade';
      END IF;
    END
    $guard$;""")
    for symbol, _, _ in STOCKS:
        # Each fixed identifier is bound, and only stock identities are targeted.
        op.execute(
            sa.text("""DELETE FROM stock_quotes WHERE coin_id IN
            (SELECT id FROM coins WHERE asset_class='stock' AND symbol=:symbol)""").bindparams(
                symbol=symbol
            )
        )
        op.execute(
            sa.text("""DELETE FROM stock_instruments WHERE coin_id IN
            (SELECT id FROM coins WHERE asset_class='stock' AND symbol=:symbol)""").bindparams(
                symbol=symbol
            )
        )
        op.execute(
            sa.text("DELETE FROM coins WHERE asset_class='stock' AND symbol=:symbol").bindparams(
                symbol=symbol
            )
        )

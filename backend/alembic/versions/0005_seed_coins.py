"""seed coins

Data only (CLAUDE.md: schema and data changes are separate migrations).
The curated D-01 list; kraken_pair is both the Ticker request pair and the
key Kraken uses in its response (live-verified 2026-10-28).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-28 10:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (symbol, name, kraken_pair), market-cap order = sort_order 1..15
COINS: tuple[tuple[str, str, str], ...] = (
    ("BTC", "Bitcoin", "XXBTZUSD"),
    ("ETH", "Ethereum", "XETHZUSD"),
    ("SOL", "Solana", "SOLUSD"),
    ("XRP", "XRP", "XXRPZUSD"),
    ("BNB", "BNB", "BNBUSD"),
    ("ADA", "Cardano", "ADAUSD"),
    ("DOGE", "Dogecoin", "XDGUSD"),
    ("TRX", "TRON", "TRXUSD"),
    ("AVAX", "Avalanche", "AVAXUSD"),
    ("LINK", "Chainlink", "LINKUSD"),
    ("DOT", "Polkadot", "DOTUSD"),
    ("LTC", "Litecoin", "XLTCZUSD"),
    ("BCH", "Bitcoin Cash", "BCHUSD"),
    ("XLM", "Stellar", "XXLMZUSD"),
    ("ATOM", "Cosmos", "ATOMUSD"),
)
SYMBOLS: tuple[str, ...] = tuple(c[0] for c in COINS)

coins = sa.table(
    "coins",
    sa.column("id", sa.BigInteger),
    sa.column("symbol", sa.Text),
    sa.column("name", sa.Text),
    sa.column("kraken_pair", sa.Text),
    sa.column("sort_order", sa.Integer),
)
prices = sa.table("prices", sa.column("coin_id", sa.BigInteger))


def upgrade() -> None:
    """Seed the 15 curated coins."""
    op.bulk_insert(
        coins,
        [
            {"symbol": symbol, "name": name, "kraken_pair": pair, "sort_order": i}
            for i, (symbol, name, pair) in enumerate(COINS, start=1)
        ],
    )


def downgrade() -> None:
    """Remove the seeded coins (and any prices that reference them)."""
    seeded_ids = sa.select(coins.c.id).where(coins.c.symbol.in_(SYMBOLS))
    op.execute(sa.delete(prices).where(prices.c.coin_id.in_(seeded_ids)))
    op.execute(sa.delete(coins).where(coins.c.symbol.in_(SYMBOLS)))

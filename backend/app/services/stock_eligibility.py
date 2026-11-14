"""One bounded authority snapshot shared by discovery and financial consumers."""

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from typing import cast as typecast

from sqlalchemy import Table, Text, case, cast, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.corporate_action import (
    StockActionEvent,
    StockActionRevision,
    StockActionState,
    StockSplitApplication,
)
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument, StockQuote, StockSession
from app.models.stock_execution import StockStatusEvidence
from app.services.corporate_actions import action_hold_queries
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_quote_rules import CURATED_SYMBOLS
from app.services.stock_sessions import RegularSession, session_at
from app.services.stock_trading_rules import (
    AdmissionEvidence,
    ExecutionDecision,
    ExecutionEvidence,
    QuoteEvidence,
    StatusEvidence,
    evaluate_execution,
)


def session_json_rows(anchor: datetime) -> Any:
    query = (
        select(StockSession.__table__)
        .order_by(StockSession.id)
        .where(
            StockSession.session_date >= anchor.date() - timedelta(days=45),
            StockSession.session_date <= anchor.date() + timedelta(days=90),
        )
    )
    bounded = query.limit(273).subquery()
    return select(func.jsonb_agg(func.to_jsonb(bounded.table_valued()))).scalar_subquery()


def admission_rows(rows: list[dict[str, Any]]) -> dict[str, ProductAdmission]:
    result = {}
    for row in rows:
        row = {key: value for key, value in row.items() if key not in ("id", "row_hash")}
        for key in ("reviewed_at", "valid_from", "valid_until"):
            if row[key] is not None:
                row[key] = datetime.fromisoformat(row[key])
        item = ProductAdmission(**row)
        result[item.product] = item
    return result


def session_rows(rows: list[dict[str, Any]]) -> list[RegularSession]:
    result = []
    for row in rows:
        row = {key: value for key, value in row.items() if key != "id"}
        for key in ("session_date", "coverage_start", "coverage_end"):
            row[key] = date.fromisoformat(row[key])
        for key in ("opens_at", "closes_at"):
            if row[key] is not None:
                row[key] = datetime.fromisoformat(row[key])
        result.append(RegularSession(**row))
    return result


def action_rows() -> Any:
    """Twenty fixed-size authority facts; no event/audit payload crosses to Python."""
    state = StockActionState.__table__
    held, missing = action_hold_queries(Coin.id)
    held = held.correlate(Coin)
    missing = missing.correlate(Coin)
    safe_reason = case(
        *(
            (exists(held.where(StockActionRevision.reason == reason)), reason)
            for reason in ("unsupported", "fractional", "conflicting", "identity_change")
        ),
        (exists(held), "conflicting"),
        (exists(missing), "source_gap"),
        else_=None,
    )
    applied = StockSplitApplication
    event = StockActionEvent
    revision = StockActionRevision
    boundary = (
        select(applied.cutoff)
        .where(applied.coin_id == Coin.id, applied.new_unit_epoch == state.c.unit_epoch)
        .order_by(applied.id.desc())
        .limit(1)
        .correlate(Coin, state)
        .scalar_subquery()
    )
    changed_split = exists(
        select(applied.id)
        .join(event, event.id == applied.economic_event_id)
        .where(applied.coin_id == Coin.id, applied.revision_id != event.current_revision_id)
        .correlate(Coin)
    )
    pending_boundary = (
        select(func.min(revision.verified_cutoff))
        .join(event, event.current_revision_id == revision.id)
        .where(
            event.coin_id == Coin.id,
            revision.classification == "supported_forward_split",
            ~exists(
                select(applied.id).where(applied.economic_event_id == event.id).correlate(event)
            ),
        )
        .correlate(Coin)
        .scalar_subquery()
    )
    query = (
        select(
            Coin.id.label("coin_id"),
            *(
                state.c[name]
                for name in (
                    "epoch",
                    "unit_epoch",
                    "health",
                    "checked_at",
                    "valid_until",
                    "admission_generation",
                    "coverage_start",
                    "covered_until",
                    "quote_not_before",
                    "next_blocking_at",
                )
            ),
            safe_reason.label("hold"),
            boundary.label("split_boundary"),
            changed_split.label("changed_split"),
            pending_boundary.label("pending_boundary"),
        )
        .outerjoin(state, state.c.coin_id == Coin.id)
        .where(Coin.asset_class == "stock", Coin.is_active, Coin.symbol.in_(CURATED_SYMBOLS))
        .order_by(Coin.sort_order, Coin.id)
        .limit(20)
        .subquery()
    )
    return select(func.jsonb_agg(func.to_jsonb(query.table_valued()))).scalar_subquery()


def execution_snapshot_query(anchor: datetime) -> Any:
    """Materialize all bounded evidence before sampling advancing database time.

    Monetary JSON fields are explicit text; no JSON float conversion is allowed.
    The CTE can also be joined into a portfolio's single financial statement.
    """
    permissions = typecast(Table, StockDataAdmission.__table__)
    permission_rows = (
        select(
            *permissions.columns,
            func.encode(
                func.sha256(
                    func.convert_to(cast(func.to_jsonb(permissions.table_valued()), Text), "UTF8")
                ),
                "hex",
            ).label("row_hash"),
        )
        .order_by(StockDataAdmission.product)
        .limit(6)
        .subquery()
    )
    permission_json = select(
        func.jsonb_agg(func.to_jsonb(permission_rows.table_valued()))
    ).scalar_subquery()
    catalogue = (
        select(
            Coin.id.label("coin_id"),
            Coin.symbol,
            Coin.name.label("company_name"),
            StockInstrument.provider_asset_id,
            StockInstrument.provider_verified_at,
            StockInstrument.listing_exchange,
            StockQuote.coin_id.label("quote_coin_id"),
            *[cast(getattr(StockQuote, name), Text).label(name) for name in ("bid", "ask", "mid")],
            *[
                getattr(StockQuote, name).label("quote_" + name)
                for name in (
                    "event_at",
                    "collected_at",
                    "session_date",
                    "admission_generation",
                    "unit_epoch",
                    "source",
                    "feed",
                )
            ],
            *[
                column.label("status_" + column.name)
                for column in StockStatusEvidence.__table__.columns
            ],
        )
        .join(StockInstrument, StockInstrument.coin_id == Coin.id)
        .outerjoin(StockQuote, StockQuote.coin_id == Coin.id)
        .outerjoin(StockStatusEvidence, StockStatusEvidence.coin_id == Coin.id)
        .where(
            Coin.asset_class == "stock",
            Coin.is_active,
            Coin.symbol.in_(CURATED_SYMBOLS),
        )
        .order_by(Coin.id)
        .limit(21)
        .subquery()
    )
    catalogue_json = select(
        func.jsonb_agg(func.to_jsonb(catalogue.table_valued()))
    ).scalar_subquery()
    snapshot = (
        select(
            permission_json.label("admissions"),
            session_json_rows(anchor).label("sessions"),
            action_rows().label("actions"),
            catalogue_json.label("instruments"),
        )
        .cte("stock_authority_snapshot")
        .prefix_with("MATERIALIZED")
    )
    return select(
        *snapshot.c,
        func.clock_timestamp().label("checked_at"),
        func.current_setting("transaction_isolation").label("isolation"),
    ).execution_options(stock_final_evidence=True)


@dataclass(frozen=True)
class LoadedExecution:
    evidence: ExecutionEvidence
    decision: ExecutionDecision
    symbol: str = ""
    company_name: str = ""
    listing_exchange: str = ""
    quote_retained_until: datetime | None = None


def _stamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None


def executions_from_snapshot(
    raw: Any, settings: Settings, *, now: datetime | None = None
) -> dict[int, LoadedExecution]:
    """Pure projection of one fresh statement; source JSON is never a response."""
    checked = now or raw.checked_at
    if raw.isolation != "read committed" or any(
        (
            len(raw.admissions or []) > 5,
            len(raw.sessions or []) > 272,
            len(raw.actions or []) > 20,
            len(raw.instruments or []) > 20,
        )
    ):
        return {}
    admissions = admission_rows(raw.admissions or [])
    sessions = session_rows(raw.sessions or [])
    scope: dict[str, Any] = {
        "account": settings.stock_data_account,
        "server": settings.stock_data_server,
    }
    hashes = {row["product"]: row["row_hash"] for row in raw.admissions or []}
    evidence = tuple(
        AdmissionEvidence(
            product,
            a.generation,
            hashes[product],
            typecast(datetime, a.valid_from),
            typecast(datetime, a.valid_until),
            a.scope.get("durable_accounting") is True
            and a.scope.get("backup_restore") is True
            and a.scope.get("retention_mode") == "durable-accounting"
            and all(
                evaluate_admission(
                    a,
                    product,
                    purpose,
                    checked,
                    feed="alpaca-corporate-actions" if product == "actions" else "iex",
                    **scope,
                ).allowed
                for purpose in ("collection", "display", "derived", "retention")
            ),
        )
        for product, a in sorted(admissions.items())
    )
    actions = {row["coin_id"]: row for row in raw.actions or []}
    output = {}
    for row in raw.instruments or []:
        cid, asset = row["coin_id"], row["provider_asset_id"] or ""
        verified = _stamp(row["provider_verified_at"])
        admitted_mapping = bool(asset and verified is not None and verified <= checked)
        quote = QuoteEvidence(coin_id=cid, provider_asset_id=asset)
        if row["quote_coin_id"] is not None:
            quote = QuoteEvidence(
                cid,
                asset,
                Decimal(row["bid"]),
                Decimal(row["ask"]),
                _stamp(row["quote_event_at"]),
                _stamp(row["quote_collected_at"]),
                date.fromisoformat(row["quote_session_date"]),
                row["quote_admission_generation"],
                row["quote_unit_epoch"],
                row["quote_source"],
                row["quote_feed"],
            )
        status = StatusEvidence(coin_id=cid, provider_asset_id=asset)
        if row["status_coin_id"] is not None:
            fields = {
                key.removeprefix("status_"): value
                for key, value in row.items()
                if key.startswith("status_")
            }
            for key in ("event_at", "observed_at", "valid_until"):
                fields[key] = _stamp(fields[key])
            if fields["session_date"] is not None:
                fields["session_date"] = date.fromisoformat(fields["session_date"])
            status = StatusEvidence(**fields)
        data_deadlines: dict[str, datetime] = {}
        for product, observed in (("quotes", quote.collected_at), ("status", status.observed_at)):
            permission = admissions.get(product)
            seconds = permission.quota.get("retention_seconds") if permission is not None else None
            if observed is not None and type(seconds) is int and 0 < seconds <= 86400:
                data_deadlines[product] = observed + timedelta(seconds=seconds)
        item_admissions = tuple(
            replace(a, approved=False)
            if a.product in data_deadlines and checked >= data_deadlines[a.product]
            else a
            for a in evidence
        )
        session = session_at(
            row["listing_exchange"], checked, sessions, admissions.get("calendar"), **scope
        )
        action = actions.get(cid, {})
        action_dates = {
            key: _stamp(action.get(key))
            for key in (
                "checked_at",
                "valid_until",
                "coverage_start",
                "covered_until",
                "quote_not_before",
                "next_blocking_at",
                "split_boundary",
                "pending_boundary",
            )
        }
        epoch, units = action.get("epoch"), action.get("unit_epoch")
        boundaries = [
            value
            for key, value in action_dates.items()
            if key in ("next_blocking_at", "pending_boundary") and value is not None
        ]
        monitor = (
            action.get("health") == "current"
            and type(epoch) is int
            and epoch > 0
            and type(units) is int
            and units >= 0
            and action.get("hold") is None
            and action.get("changed_split") is False
            and action.get("admission_generation")
            == getattr(admissions.get("actions"), "generation", None)
            and all(
                action_dates[key] is not None
                for key in ("checked_at", "valid_until", "coverage_start", "covered_until")
            )
        )
        if monitor:
            monitor = (
                typecast(datetime, action_dates["checked_at"]) <= checked
                and typecast(datetime, action_dates["coverage_start"])
                <= typecast(datetime, action_dates["covered_until"])
                <= checked
            )
        if monitor and units > 0:
            monitor = (
                action_dates["split_boundary"] is not None
                and action_dates["split_boundary"] == action_dates["quote_not_before"]
                and quote.event_at is not None
                and action_dates["split_boundary"] < quote.event_at <= checked
            )
        current = session.current
        item = ExecutionEvidence(
            coin_id=cid,
            provider_asset_id=asset,
            admissions=item_admissions if admitted_mapping else (),
            action_current=monitor,
            action_valid_until=action_dates["valid_until"],
            next_blocking_at=min(boundaries) if boundaries else None,
            safety_epoch=epoch or 0,
            unit_epoch=units or 0,
            status=status,
            session_state=typecast(Any, session.state),
            # Bind independent status to today's date even when calendar bounds
            # are unavailable. Unknown session state/bounds still deny execution.
            session_date=current.session_date if current else checked.date(),
            opens_at=current.opens_at if current else None,
            closes_at=current.closes_at if current else None,
            # This conservative deadline also binds data-use expiry in the
            # final invoker guard. Raw admission/status snapshots stay exact.
            session_valid_until=min([session.valid_until, *data_deadlines.values()])
            if session.valid_until is not None
            else None,
            calendar_generation=current.calendar_admission_generation if current else 0,
            quote=quote,
        )
        retained = data_deadlines.get("quotes")
        output[cid] = LoadedExecution(
            item,
            evaluate_execution(item, checked),
            row["symbol"],
            row["company_name"],
            row["listing_exchange"],
            retained,
        )
    return output


async def load_execution_evidence(
    db: AsyncSession, coin_id: int, settings: Settings
) -> LoadedExecution:
    raw = (await db.execute(execution_snapshot_query(datetime.now(UTC)))).one()
    loaded = executions_from_snapshot(raw, settings)
    if coin_id in loaded:
        return loaded[coin_id]
    empty = ExecutionEvidence(coin_id=coin_id)
    return LoadedExecution(empty, evaluate_execution(empty, raw.checked_at))

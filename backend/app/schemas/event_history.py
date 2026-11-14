"""Exact immutable mixed-event wire values; monetary values stay strings."""

import re
from datetime import date, datetime
from decimal import Decimal, localcontext
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def _fixed(value: str) -> str:
    if re.fullmatch(r"-?(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,8})?", value) is None:
        raise ValueError("Invalid decimal")
    if value.startswith("-") and Decimal(value) == 0:
        raise ValueError("Negative zero")
    return value


def _nonnegative(value: str) -> str:
    if Decimal(value) < 0:
        raise ValueError("Negative value")
    return value


def _cents(value: str) -> str:
    if Decimal(value) % Decimal(".01") != 0:
        raise ValueError("Not cents")
    return value


def _whole(value: str) -> str:
    if Decimal(value) != Decimal(value).to_integral_value():
        raise ValueError("Not whole shares")
    return value


def _instant(value: str) -> str:
    if re.fullmatch(r"[1-9][0-9]{3}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", value) is None:
        raise ValueError("Not canonical UTC")
    datetime.fromisoformat(value)
    return value


def _date(value: str) -> str:
    if date.fromisoformat(value).isoformat() != value:
        raise ValueError("Not a calendar date")
    return value


def _name(value: str) -> str:
    if not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Invalid plain text")
    return value


Fixed = Annotated[str, AfterValidator(_fixed)]
Nonnegative = Annotated[Fixed, AfterValidator(_nonnegative)]
Cash = Annotated[Fixed, AfterValidator(_cents)]
NonnegativeCash = Annotated[Cash, AfterValidator(_nonnegative)]
Shares = Annotated[Nonnegative, AfterValidator(_whole)]
Instant = Annotated[str, AfterValidator(_instant)]
CalendarDate = Annotated[str, AfterValidator(_date)]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class EventBase(WireModel):
    kind: str
    id: str
    recorded_at: Instant
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,19}$")
    name: Annotated[str, Field(max_length=256), AfterValidator(_name)]
    cash_delta: Cash

    @model_validator(mode="after")
    def identity(self) -> Self:
        if re.fullmatch(rf"{self.kind}:[1-9][0-9]{{0,18}}", self.id) is None:
            raise ValueError("Invalid event identity")
        if int(self.id.split(":")[1]) > 9223372036854775807:
            raise ValueError("Identity overflow")
        return self


class DividendTerms(WireModel):
    eligible_quantity: Shares
    rate: Nonnegative
    cutoff: Instant
    ex_date: CalendarDate | None
    record_date: CalendarDate | None
    payable_date: CalendarDate


class EventTrade(EventBase):
    kind: Literal["trade"]
    asset_type: Literal["stock", "crypto"]
    side: Literal["buy", "sell"]
    quantity: Nonnegative
    exec_price: Nonnegative
    fee: NonnegativeCash
    filled_at: Instant
    source: Literal["alpaca"] | None
    feed: Literal["iex"] | None
    quote_at: Instant | None

    @model_validator(mode="after")
    def trade_facts(self) -> Self:
        if Decimal(self.quantity) <= 0 or Decimal(self.exec_price) <= 0:
            raise ValueError("Nonpositive fill")
        if self.filled_at > self.recorded_at:
            raise ValueError("Fill after publication")
        if (self.side == "buy" and Decimal(self.cash_delta) >= 0) or (
            self.side == "sell" and Decimal(self.cash_delta) < 0
        ):
            raise ValueError("Cash direction")
        if self.asset_type == "stock":
            _whole(self.quantity)
            if self.source != "alpaca" or self.feed != "iex" or self.quote_at is None:
                raise ValueError("Missing stock source")
            if self.quote_at > self.filled_at or Decimal(self.fee) != 0:
                raise ValueError("Invalid stock fill")
        elif self.source is not None or self.feed is not None or self.quote_at is not None:
            raise ValueError("Unexpected crypto source")
        return self


class EventDividend(EventBase, DividendTerms):
    kind: Literal["dividend"]
    asset_type: Literal["stock"]
    payment_reference: str
    credited_amount: NonnegativeCash
    credited_at: Instant

    @model_validator(mode="after")
    def original_facts(self) -> Self:
        with localcontext() as ctx:
            ctx.prec = 64
            target = (Decimal(self.eligible_quantity) * Decimal(self.rate)).quantize(
                Decimal(".01"), rounding="ROUND_HALF_EVEN"
            )
        if self.payment_reference != self.id or Decimal(self.credited_amount) != target:
            raise ValueError("Original target or reference")
        if (
            Decimal(self.cash_delta) != target
            or not self.cutoff <= self.credited_at <= self.recorded_at
        ):
            raise ValueError("Original cash or chronology")
        return self


class EventSplit(EventBase):
    kind: Literal["split"]
    asset_type: Literal["stock"]
    ratio_new: Shares
    ratio_old: Shares
    quantity_before: Shares
    quantity_after: Shares
    cost_basis_before: Nonnegative
    cost_basis_after: Nonnegative
    effective_at: Instant

    @model_validator(mode="after")
    def split_facts(self) -> Self:
        with localcontext() as ctx:
            ctx.prec = 64
            new, old = Decimal(self.ratio_new), Decimal(self.ratio_old)
            before, after = Decimal(self.quantity_before), Decimal(self.quantity_after)
            if old <= 0 or new <= old or before <= 0 or before * new != after * old:
                raise ValueError("Split quantity or ratio")
        if Decimal(self.cash_delta) != 0 or self.cost_basis_before != self.cost_basis_after:
            raise ValueError("Split cash or basis")
        if self.effective_at > self.recorded_at:
            raise ValueError("Split chronology")
        return self


class EventDividendCorrection(EventBase):
    kind: Literal["dividend_correction"]
    asset_type: Literal["stock"]
    payment_reference: str
    decision_reference: str
    outcome: Literal["applied", "held_uncertain", "held_unaffordable", "verified_no_change"]
    reason: Literal["target_applied", "terms_unverified", "insufficient_cash", "target_unchanged"]
    desired_total: NonnegativeCash | None
    cumulative_applied_before: NonnegativeCash
    proposed_delta: Cash | None
    applied_delta: Cash
    terms: DividendTerms | None
    original: EventDividend

    @model_validator(mode="after")
    def correction_facts(self) -> Self:
        reasons = {
            "applied": "target_applied",
            "held_uncertain": "terms_unverified",
            "held_unaffordable": "insufficient_cash",
            "verified_no_change": "target_unchanged",
        }
        if self.payment_reference != self.original.id or self.decision_reference != self.id:
            raise ValueError("Invalid lineage")
        if self.original.recorded_at > self.recorded_at or reasons[self.outcome] != self.reason:
            raise ValueError("Invalid correction chronology or reason")
        applied = Decimal(self.applied_delta)
        if Decimal(self.cash_delta) != applied:
            raise ValueError("Invalid cash effect")
        if self.outcome == "held_uncertain":
            if (
                self.desired_total is not None
                or self.proposed_delta is not None
                or self.terms is not None
                or applied != 0
            ):
                raise ValueError("Invented uncertain terms")
        else:
            if self.desired_total is None or self.proposed_delta is None or self.terms is None:
                raise ValueError("Missing verified terms")
            with localcontext() as ctx:
                ctx.prec = 64
                target = (
                    Decimal(self.terms.eligible_quantity) * Decimal(self.terms.rate)
                ).quantize(Decimal(".01"), rounding="ROUND_HALF_EVEN")
                proposal = Decimal(self.desired_total) - Decimal(self.cumulative_applied_before)
            if target != Decimal(self.desired_total) or proposal != Decimal(self.proposed_delta):
                raise ValueError("Invalid target")
            if self.outcome == "applied" and (applied == 0 or applied != proposal):
                raise ValueError("Invalid applied effect")
            if self.outcome != "applied" and applied != 0:
                raise ValueError("Held cash effect")
            if self.outcome == "held_unaffordable" and proposal >= 0:
                raise ValueError("Invalid deficit")
            if self.outcome == "verified_no_change" and proposal != 0:
                raise ValueError("Invalid no-change")
        return self


EventHistoryItem = Annotated[
    EventTrade | EventDividend | EventSplit | EventDividendCorrection, Field(discriminator="kind")
]


class EventHistoryPage(WireModel):
    items: list[EventHistoryItem]
    next_cursor: str | None = Field(max_length=512)

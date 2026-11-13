"""Bounded retained-row dividend work; SQL alone owns financial authority."""

from app.tasks.scheduler import CycleResult


async def run_dividend_cycle(*, sessionmaker, settings, cursor=None):
    return CycleResult("ok")

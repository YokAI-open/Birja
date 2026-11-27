"""Private process-only synthetic portfolio inputs; never mounted by an app route."""

import asyncio
import json
import os
import re
import runpy
import subprocess
import sys
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

sys.path.insert(0, "/app")
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

helper = runpy.run_path('/e2e/stock-trade-fixture.py', run_name='private_browser_helper')


async def daily_observations(db, uid, variant, first, second, *terminal):
    ids = (first, second, *terminal)
    if len(set(ids)) != len(ids) or any(
        re.fullmatch(r'[1-9][0-9]{0,17}', value) is None for value in ids
    ):
        raise ValueError('Distinct exact synthetic portfolio IDs required')
    if variant == 'sparse' and len(terminal) == 1:
        series = (
            ((18, 10550), (17, 10475), (15, None), (12, 11025)),
            ((16, 9800),),
            ((13, 77777),),
        )
    elif variant == 'paired' and not terminal:
        steps = (0, -73, 110, -17, 144, -24, 95)
        series = (
            tuple((age, 9960 + index * 28 + steps[index % len(steps)])
                  for index, age in enumerate(range(29, 0, -1))),
            tuple((age, 10140 - index * 12 - steps[index % len(steps)])
                  for index, age in enumerate(range(29, 0, -1))),
        )
    else:
        raise ValueError('Unknown synthetic daily observation variant')
    day = await db.scalar(text("SELECT (clock_timestamp() AT TIME ZONE 'UTC')::date"))
    for portfolio_id, values in zip(ids, series, strict=True):
        pid = int(portfolio_id)
        baseline = await db.scalar(text('''
            SELECT starting_cash FROM accounts
            WHERE id=:p AND user_id=:u AND closed_at IS NULL
        '''), {'p': pid, 'u': uid})
        if baseline is None:
            raise ValueError('Only active portfolios of this synthetic owner may receive observations')
        for age, amount in values:
            observed_day = day - timedelta(days=age)
            await db.execute(text('''
                INSERT INTO portfolio_daily_values
                    (portfolio_id, user_id, utc_day, captured_at, starting_cash,
                     total_value, valuation_complete)
                VALUES (:p, :u, :day, :captured, :baseline, :amount, :complete)
            '''), {
                'p': pid,
                'u': uid,
                'day': observed_day,
                'captured': datetime.combine(observed_day, time(22, 15), UTC),
                'baseline': baseline,
                'amount': None if amount is None else Decimal(amount),
                'complete': amount is not None,
            })
    print(json.dumps({'time_basis': 'UTC', 'synthetic_rows': sum(map(len, series))}))


async def main(mode, email=None, *arguments):
    helper['guard']()
    if mode not in {'legacy', 'inspect', 'economic', 'lifecycle', 'sibling', 'name', 'price-tick', 'daily'}:
        raise ValueError('Unknown synthetic portfolio operation')
    if mode != 'daily' and arguments:
        raise ValueError('Unexpected synthetic portfolio arguments')
    if mode != 'legacy' and (not email or re.fullmatch(r'e2e-[a-z0-9-]+@example\.com', email) is None):
        raise ValueError('Synthetic owner required')
    engine = create_async_engine(os.environ['DATABASE_URL'])
    try:
        if mode == 'lifecycle':
            # Process-only immutable before/after oracle. PostgreSQL itself
            # rejects mutation throughout this separate read-only transaction.
            async with engine.begin() as db:
                await db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
                assert await db.scalar(text('SHOW transaction_read_only')) == 'on'
                uid = await db.scalar(text('SELECT id FROM users WHERE email=:e'), {'e': email})
                if uid is None:
                    raise ValueError('Sign in with actual OTP first')
                ids = (await db.execute(text('SELECT id FROM accounts WHERE user_id=:u ORDER BY id'), {'u': uid})).scalars().all()
                financial_tables = ('holdings', 'trades', 'stock_fill_facts',
                    'stock_ownership_movements', 'stock_dividend_entitlements',
                    'stock_dividend_payments', 'stock_dividend_decisions')
                roots = {}
                for pid in ids:
                    value = {'account': await db.scalar(text('SELECT to_jsonb(a)::text FROM accounts a WHERE id=:p AND user_id=:u'), {'p': pid, 'u': uid})}
                    value['account_financial'] = await db.scalar(text("SELECT (to_jsonb(a) - 'closed_at' - 'name' - 'name_key' - 'description')::text FROM accounts a WHERE id=:p AND user_id=:u"), {'p': pid, 'u': uid})
                    for table in financial_tables + ('portfolio_stock_closures', 'portfolio_lifecycle_closures', 'portfolio_closure_intents'):
                        value[table] = (await db.execute(text(f'SELECT to_jsonb(t)::text FROM public.{table} t WHERE portfolio_id=:p ORDER BY to_jsonb(t)::text'), {'p': pid})).scalars().all()
                    roots[str(pid)] = value
                print(json.dumps({'read_only': True, 'roots': roots}, sort_keys=True))
            return
        if mode == 'legacy':
            # Real old-schema input, then the qualified dev runner performs the
            # authenticated0015/16/17 migration during normal browser startup.
            child = dict(os.environ)
            child['DATABASE_URL'] = make_url(child['DATABASE_URL']).set(
                username='birja_migrator', password='syntheticMigratorE2E').render_as_string(hide_password=False)
            subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', '0014'],
                           cwd='/app', env=child, check=True)
            async with engine.begin() as db:
                uid = await db.scalar(text("INSERT INTO users(email) VALUES ('e2e-migrated@example.com') RETURNING id"))
                await db.execute(text('INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:u,123.45,9999)'), {'u': uid})
                await db.execute(text('ALTER ROLE birja_migrator NOLOGIN PASSWORD NULL'))
            print('synthetic_legacy_schema=0014')
            return
        async with engine.begin() as db:
            assert await db.scalar(text('SELECT current_database()')) == 'birja'
            uid = await db.scalar(text('SELECT id FROM users WHERE email=:e'), {'e': email})
            if uid is None:
                raise ValueError('Sign in with actual OTP first')
            if mode == 'daily':
                await daily_observations(db, uid, *arguments)
                return
            original = await db.scalar(text('SELECT min(id) FROM accounts WHERE user_id=:u'), {'u': uid})
            if mode == 'sibling':
                # Retained historical opening, never represented as a new grant.
                await db.execute(text("INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) VALUES (:u,'Sibling strategy',public.portfolio_name_key('Sibling strategy'),2000,2000)"), {'u': uid})
            elif mode == 'name':
                await db.execute(text('UPDATE accounts SET name=:n,name_key=public.portfolio_name_key(:n) WHERE id=:p AND closed_at IS NULL'), {'n': '<Strategy>& ' + 'UnbrokenPortfolioName' * 2, 'p': original})
            elif mode == 'price-tick':
                # Real synthetic market evidence changes between preview and
                # execute. No portfolio money or saved order is modified.
                changed = (await db.execute(text("UPDATE prices SET mid=mid+1,as_of=clock_timestamp() WHERE coin_id=(SELECT id FROM coins WHERE symbol='BTC' AND asset_class='crypto') AND source='fake' RETURNING coin_id"))).scalars().all()
                assert len(changed) == 1, 'One actual fake BTC price required'
            if mode == 'economic':
                result = {}
                # Immutable before-oracle: metadata edits must preserve every
                # economic/history/journal byte, not just the displayed cash.
                for table in ('accounts', 'holdings', 'trades', 'portfolio_creations', 'portfolio_initializations'):
                    # Preserve exact numeric text: decoding JSONB into Python
                    # floats would weaken the immutable financial oracle.
                    columns = "(to_jsonb(t) - 'name' - 'name_key' - 'description')::text" if table == 'accounts' else 'to_jsonb(t)::text'
                    result[table] = (await db.execute(text(
                        f'SELECT {columns} AS row FROM public.{table} t WHERE user_id=:u ORDER BY id'
                        if table != 'portfolio_initializations' else
                        f'SELECT {columns} AS row FROM public.{table} t WHERE user_id=:u ORDER BY user_id'
                    ), {'u': uid})).scalars().all()
                print(json.dumps(result, sort_keys=True))
                return
            rows = (await db.execute(text('SELECT id::text,name,cash::text,starting_cash::text,closed_at IS NOT NULL AS closed FROM accounts WHERE user_id=:u ORDER BY accounts.id'), {'u': uid})).mappings().all()
            print(json.dumps([dict(r) for r in rows]))
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main(*sys.argv[1:]))


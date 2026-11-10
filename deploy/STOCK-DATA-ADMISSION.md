# Stock data admission procedure

No provider permission has been established. This packet prepares local review;
it authorizes no signup, contact, agreement, payment, private API call or production
change. Stocks remain disabled. Phase7/8 do not enable stock trading.

## Review packet and custody

Before any activation, the owner approves the exact reviewed source commit,
test/role/TLS/image evidence, provider account, products, twenty instrument IDs,
deployment scope and bounded verification request count/time/response size.
Record approved operations and expiry separately from technical evidence.
A working key is not permission. Missing products remain independently denied.

For EACH product (`reference`, `quotes`, `actions`, `status`, `calendar`) record:

| Evidence | Required review |
| --- | --- |
| Access | Account/subscription and exact endpoint/feed coverage |
| Purposes | Separately verified collection, display, derived and retention rights |
| Scope | application=birja, audience=authenticated-users, exact account/server IDs, feed=iex |
| Terms | Secure evidence reference, reviewed version, reviewer/time and validity interval |
| Fields | Only reviewed fields; quotes require bid/ask/event_at/symbol |
| Attribution | Exact permitted public text, including the visible IEX prices label |
| Quota | requests_per_minute, symbols_per_request, max_response_bytes, retention_seconds |
| Cost | Free access and actual bounded request budget; no automatic paid fallback |

`reference` requires symbol/name/exchange/provider_asset_id; `actions` requires
event_id/revision/symbol/event_type/effective_date; `status` requires
symbol/status/event_at; `calendar` requires exchange/session_date/opens_at/closes_at.
Reference metadata independently reviewed from SEC/public sources does not grant
quote/action/status rights. Additional fields need explicit review, not guessing.
Evidence fixtures and domain validation cannot determine legal permission.

Keep original contracts/reviewer records outside source control. DB evidence_ref
points to the private review record; store no keys or raw contract text in JSON.
Provider SecretStr keys go only in the scheduler's private env. The API receives
only nonsecret configuration and read-only admission access. Never paste/log
keys, DSNs, private terms or personal account information. Preserve off-server
custody under the existing recovery policy. No runtime admin HTTP endpoint exists.

## Calendar authority

Only migrator-owned `stock_data_admissions.calendar` establishes calendar review
authority. `stock_sessions` has derived dates/bounds and
calendar_admission_generation only; scheduler/app cannot create/renew authority.
Both runtime roles have SELECT-only admission access (verified in Plan07-04).

Calendar JSON includes exactly these semantic values (other metadata confers no
rights): exchanges=[XNYS,XNAS], nonblank version, sources with official HTTPS NYSE
and Nasdaq URLs, review_valid_until as aware UTC, coverage_start/coverage_end as
ISO dates, and overrides as a bounded array. Review expiry is no later than
reviewed_at+24h. Coverage is within45days before/90days after the review date and
must include the current date. Runtime cannot roll that horizon forward.
Each override names exchange/date/state/source. State is closed (null bounds) or
shortened (aware UTC bounds on that date, New York09:30 opening and earlier than
16:00 close). Provenance must match that exchange's official HTTPS host. Duplicate
exchange/date entries, unsupported/conflicting overrides or malformed/expired
review evidence deny admission. Review the actual referenced official content;
host validation alone does not prove that a closure announcement is authentic.
Every review renewal or override update increments generation; existing derived
rows cannot inherit authority merely by being fresh.

## Operator inspection and prepared import

Run only after owner approval, from a private operator shell with history/logging
controls. Load MIGRATOR_DATABASE_URL from protected migrator credentials using
the existing verified-TLS connection procedure; never pass it on a command line.
STOCK_EVIDENCE_FILE is a mode0600 private JSON packet pathname. It contains all
ProductAdmission fields except id; ISO UTC timestamps represent reviewed_at,
valid_from and valid_until. No runtime settings contain this administrative DSN
or file. Do not set these variables in API/scheduler containers.

Read-only inspection through the existing TLS-aware SQLAlchemy connection:

```python
from sqlalchemy import select
from app.models.stock import StockDataAdmission
# `session` is the operator's existing verified-TLS session; do not print rows.
rows = (await session.execute(select(
    StockDataAdmission.product, StockDataAdmission.state,
    StockDataAdmission.generation, StockDataAdmission.valid_until,
))).all()
# Inspect only these sanitized product/state/generation/expiry values privately.
```

The following import function is executable inside an operator-owned async
session constructed from MIGRATOR_DATABASE_URL and the existing
`app.db.connection.database_ssl_context` verified-TLS connect_args. It performs
no connection itself, never grants roles, and deliberately defaults to ROLLBACK.
The approved operator supplies `now` from datetime.now(UTC) immediately before
validation; no fixture date establishes current authority.

```python
import json
import os
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from sqlalchemy import select
from app.models.stock import StockDataAdmission
from app.services.stock_admission import ProductAdmission, evaluate_admission

async def import_packet(session, now, *, apply=False, account, server):
    packet = json.loads(Path(os.environ['STOCK_EVIDENCE_FILE']).read_text())
    allowed = {f.name for f in fields(ProductAdmission)}
    if set(packet) != allowed:
        raise ValueError('evidence packet field mismatch')
    for key in ('reviewed_at', 'valid_from', 'valid_until'):
        packet[key] = datetime.fromisoformat(packet[key])
    async with session.begin():
        row = (await session.execute(select(StockDataAdmission)
            .where(StockDataAdmission.product == packet['product'])
            .with_for_update())).scalar_one()  # SELECT ... FOR UPDATE
        # Missing row fails: seed/create denied evidence only as a separately
        # reviewed migrator operation. No opportunistic runtime row creation.
        if packet['generation'] != row.generation + 1:
            raise ValueError('stale administrative generation')
        candidate = ProductAdmission(**packet)
        for purpose in ('collection', 'display', 'derived', 'retention'):
            decision = evaluate_admission(candidate, candidate.product, purpose,
                now, account=account, server=server)
            if getattr(candidate, purpose + '_allowed') and not decision.allowed:
                raise ValueError('evidence dry-run denied')
        for key, value in packet.items():
            if key != 'product':
                setattr(row, key, value)
        await session.flush()
        if not apply:
            await session.rollback()  # ROLLBACK: default rehearsal, no writes
        # COMMIT only on successful exit with apply=True and exact owner scope.
```

Initial denied rows do not require provider permission and must be explicitly
created by the migrator before import. For each product use a bound ORM insert
inside one approved transaction: `session.add(StockDataAdmission(product=product,
state='denied', generation=1))`. Unique constraints reject duplicate creation;
never delete/reinsert to reset generation. Initial approved import uses generation2.

Concrete connection wrapper for the import function above (operator-only; the
default call still rolls back). `MIGRATOR_DATABASE_SSL_CA_FILE` is the protected
reviewed CA pathname; scope variables must match the exact approved deployment.
Do not invoke this wrapper until the owner approves the administrative scope.

```python
from datetime import UTC
from types import SimpleNamespace
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.connection import database_connect_args

async def rehearse():
    config = SimpleNamespace(env='prod',
        database_url=os.environ['MIGRATOR_DATABASE_URL'],
        database_ssl_ca_file=os.environ['MIGRATOR_DATABASE_SSL_CA_FILE'])
    engine = create_async_engine(config.database_url, echo=False,
        hide_parameters=True, connect_args=database_connect_args(config, migration=True))
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            await import_packet(session, datetime.now(UTC), apply=False,
                account=os.environ['STOCK_DATA_ACCOUNT'],
                server=os.environ['STOCK_DATA_SERVER'])
    finally:
        await engine.dispose()
# An approved operator may call asyncio.run(rehearse()) from a private script.
# Applying the reviewed packet requires a separately approved apply=True change.
```

For restrictive changes/revocation lock the same product with FOR UPDATE and use:

```sql
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
SELECT generation FROM stock_data_admissions WHERE product = :'product' FOR UPDATE;
UPDATE stock_data_admissions SET state = 'revoked',
  generation = generation + 1,
  collection_allowed = false, display_allowed = false,
  derived_allowed = false, retention_allowed = false
WHERE product = :'product';
-- Require exactly one updated row; otherwise ROLLBACK and investigate.
ROLLBACK; -- Default rehearsal. COMMIT requires the approved actual operation.
```

Use the existing private verified-TLS psql environment for the SQL example;
`:product` is a bound psql variable, never SQL string interpolation. Import,
restrictive field changes, review renewal and revoke all advance generation.
App/scheduler must never receive these operations/credentials. A denied retention
decision also forbids reusing previously stored values; approved deletion/cleanup
policy is separate and cannot silently erase financial evidence.

## Positive/negative rehearsal and later activation

Run `cd backend && uv run pytest tests/test_stock_admission.py
tests/test_config_scheduler.py tests/test_config_prices.py -q` locally. In an
approved operator dry-run, evaluate each actual candidate for every requested
purpose. Verify denial with replace(candidate, state='revoked'), expired
valid_until, missing purpose, wrong scope/feed and expected_generation mismatch.
Never print the candidate/raw evidence; record only safe decision/reason,
generation, expiry and approved attribution. Verify runtime SELECT-only authority
with the existing isolated actual TLS role proof, not production write probes.

Collection must check current committed evidence before fetch, reload after I/O
before storage, and bind persisted derived values to generation. API reads reload
current evidence and fresh UTC after awaited work, then synchronously project
without another await; quote/review/session lifetime bounds reach the client.
No cached approval can outlive expiry or revocation. Plan07-09/10 wire these
boundaries; Plan07-13 proves actual persisted restricted-TLS consumers.

Keep STOCK_DATA_ENABLED=false until the final concrete checkpoint approves actual
rights/account scope and bounded private observation. Enabled scheduler settings
require both keys, IEX only,60–120s polling, bounded retries/response bytes and a
maximum20s stock cycle. The cycle budget includes all work/backoff; request retry
arithmetic is only a preliminary bound. API settings cannot load provider keys.
No alternate SIP/delayed/fake stock provider is configurable, including production.
Successful technical checks do not authorize provider agreements or deployment.

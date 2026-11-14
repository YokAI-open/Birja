# Stack Research: v1.1 US Stock Trading

**Domain:** Multi-asset virtual trading with 20 US-listed stocks
**Researched:** 2026-11-10
**Confidence:** HIGH for the existing stack and documented provider restrictions;
MEDIUM for conditional provider suitability; public display entitlement unresolved.

## Recommendation

Keep Birja's existing stack. Add a stock-data adapter to the existing single
scheduler, plus a narrowly isolated exchange-calendar component. **Do not select
a production stock provider yet:** none of the investigated free offerings was
verified to satisfy both the requested freshness and permission to show data to
Birja's other users. This is a launch dependency, not proof that no free agreement
could ever be obtained. See [FEASIBILITY.md](FEASIBILITY.md).

Alpaca Basic/IEX is the strongest **technical candidate**, conditional on explicit
permission for this deployment and owner acceptance of single-venue coverage.
It is not a confirmed licensed solution for Birja. Its personal Trading API and
partner Broker API have different access models; do not turn a Broker sandbox
permission into a personal-account production entitlement. [A1, A3]

## Recommended Stack

### Core Technologies — retain deployed choices

Versions below come from the repository manifests, not a proposal to upgrade.

| Technology | Version | Purpose | Why retain |
|---|---|---|---|
| Python / FastAPI | 3.14 / 0.162.0 | API, validation and stock rules | Already deployed and tested; stock support does not require a new backend framework |
| httpx | 0.28.1 | Async authenticated market-data REST calls | Existing transport can validate provider responses without a provider SDK |
| SQLAlchemy / asyncpg / Alembic | 2.0.55–<2.1 / 0.32.0 / 1.20.1 | Shared account, asset metadata, quotes, migrations | Preserve one transaction and account-lock ordering across crypto and stocks |
| PostgreSQL | Existing PG18 deployment | Durable prices, trades, holdings and calendar state | Continue Decimal/NUMERIC accounting and existing recovery guarantees |
| redis-py | 8.1.0 | Rebuildable cached quotes, existing session state | Keep authoritative financial state in Postgres |
| React / TypeScript | 19.3.1 / 6.0.3 | Existing market, trading and portfolio UI | Add asset metadata and status without rebuilding the UI |
| TanStack Query | 5.105.0 | Server state and refresh | Preserve existing query conventions; frontend requests never fan out to providers |
| Single scheduler + Docker Compose | Existing application architecture | Refresh both asset classes independently | One upstream workload regardless of the number of Birja users |

Local evidence: `backend/pyproject.toml`, `backend/uv.lock`,
`frontend/package.json`, `CLAUDE.md`, `.planning/PROJECT.md`.

### Supporting Libraries and Data

| Component | Version | Purpose | When to use |
|---|---|---|---|
| `decimal`, `datetime`, `zoneinfo` | Python 3.14 standard library | Exact share math, UTC storage and America/New_York rules | Always; no money converted through float |
| `exchange_calendars` | Candidate **4.13.2**, released 2026-03-10 | Session boundaries, holidays and early closes | Preferred local calendar candidate after targeted dependency/image validation; not installed by this research |
| NumPy / pandas | Resolve compatible locked versions; upstream's Python 3.14 test floor is NumPy ≥2.3.2 and pandas ≥2.3.3 | Transitive calendar dependencies only | Add only with the chosen calendar; never use DataFrame/float arithmetic for balances or fills |
| Provider calendar/status API | Provider/entitlement dependent | Cross-check sessions and unexpected closures | Only after access/usage is documented; cache bounded schedules and fail closed when confidence expires |
| Existing pytest / respx / Vitest / Playwright | Existing lockfiles | Deterministic quote/session/money checks | Mock provider HTTP; test actual transactional database paths |

`exchange_calendars` 4.13.2 explicitly declares Python 3.14 and its tagged source
contains a Python-3.14-specific dependency test group. This establishes declared
support, **not** a successful Birja image build or security scan. It brings six
direct dependencies, including pandas/NumPy. Isolate its outputs as UTC datetimes;
do not import an analytics stack into money calculations. The package is a
calendar, not an authoritative live halt feed. [C1, C2]

Use regular sessions only: validate local XNYS/Nasdaq schedule assumptions against
the official NYSE and Nasdaq annual schedules, including early closes. Keep
intraday halts/emergency closures as a separate status concern; a weekday
09:30–16:00 check alone is insufficient. [C3, C4]

## Conditional Provider Pattern

If current written terms/confirmation permit this specific public simulator and
the owner accepts IEX coverage, use an `httpx.AsyncClient` adapter around Alpaca's
batched `/v2/stocks/quotes/latest` with an explicit `feed=iex`. The endpoint accepts
a comma-separated ticker list. Twenty symbols can therefore fit one request per
minute; the Basic plan's documented 200 calls/minute and 30 streaming-symbol
ceiling are technically ample for this list. No WebSocket is necessary for
minute polling. [A1, A2]

Store source, feed, provider event timestamp and fetch timestamp separately.
Validate both sides of the quote, positive finite prices, symbol mapping and
time order before deriving a Decimal midpoint. Reject absent or old symbol
quotes independently; fetching a response now must not renew an old event.
Polling each minute is not a guarantee that the most recent IEX event is less
than a minute old. NYSE/Nasdaq **listing** eligibility does not imply the quotes
are consolidated across their trading venues. [A2; implementation recommendation]

Do not silently switch to `delayed_sip`, a closing price or a different vendor to
make a trade succeed. The user rejected fifteen-minute delay. Every displayed
price must explain its actual feed coverage and timestamp; a simulated spread
does not turn an IEX midpoint into national NBBO execution.

## Installation

No dependency installation or account creation is justified during this milestone
research. At implementation time, if the calendar candidate survives focused
Python 3.14/image/scan validation, add it through the existing package manager:

```bash
cd backend
uv add 'exchange-calendars==4.13.2'
```

Review and commit the resolved `uv.lock` as part of that implementation, then run
the established tests and image/security gates. This research executed no install,
provider signup, private-account request, deployment or paid subscription.

## Alternatives Considered

| Recommended approach | Alternative | When the alternative makes sense |
|---|---|---|
| Existing httpx REST adapter | `alpaca-py` | If later features genuinely need SDK surface; unnecessary brokerage and dependency surface for one quote endpoint today |
| Conditional IEX evaluation | Consolidated real-time SIP | When owner accepts a suitable licensed budget and distribution agreement; personal paid access still does not prove display rights |
| `exchange_calendars` 4.13.2 candidate | `pandas_market_calendars` | If its separate calendar interface is needed; it also introduces pandas and mirrors exchange calendars, so adds no clear simplification here [C5] |
| Package-backed calendar with official verification | Provider-only calendar | If provider agreement gives a dependable usable calendar and documented failure semantics; public quote access does not establish this |
| Continue current scheduler | Celery, Kafka, streaming frontend | Only after workload evidence requires them; 20 minute-polled stocks does not |

## What NOT to Use

| Avoid | Why | Use instead |
|---|---|---|
| Finnhub free key as a shared public feed | Its terms require written approval to share either source data or derived results [F1] | Obtain documented permission first or choose another authorized source |
| Twelve Data Basic for this cadence | Eight credits/minute and 800/day; batch accounting charges each symbol, and Basic offers internal non-display usage [T1, T2] | A separately approved plan/agreement, or another provider |
| Massive/Polygon free tier for trading now | End-of-day access, not current data; minute bars describe granularity, not freshness [M1] | A licensed current feed |
| Alpha Vantage standard free tier | 25 calls/day and current US equity data requires premium entitlement [V1] | Another authorized source, or re-approved budget/scope |
| Scraped Yahoo/Google pages or unofficial endpoints | No verified display entitlement, stable API contract or fit established | Documented provider API and explicit usage rights |
| Assuming free IEX exchange data means every vendor passes through that right | Exchange and upstream-vendor agreements are distinct | Verify the actual chosen provider/account/product terms |
| Bar timestamps or local receipt time used as quote freshness | A one-minute bar can arrive late; repeated fetches can return the same old event | Preserve and check provider event time |

## Version Compatibility and Validation Gate

| Pair | Verified evidence | Still required |
|---|---|---|
| Birja Python 3.14 + current httpx | Existing lockfile/application | Provider payload parsing, TLS, timeout and rate-limit contract tests |
| Python 3.14 + exchange_calendars 4.13.2 | Release tag declares support and Python 3.14 test dependency floors [C2] | Real lock resolution, wheel availability in hardened image, scan and representative session tests |
| Local session calendar + live trading availability | Scheduled sessions are available in package/exchange schedules | Separate halt/status policy and expiry; do not promise real-time halt detection from a static calendar |
| Personal market-data subscription + Birja multi-user display | **Not established** | Current explicit terms or written provider permission covering display, stored fill facts, retention and derived valuation |

## Sources and Confidence

All accessed **2026-11-10**. Primary sources only inform recommendations.
No Context7 tool is configured; provider/exchange and tagged-source documentation
were read directly. No framework lookup or runtime installation was needed.

- **A1 — HIGH:** [Alpaca current market-data plans](https://docs.alpaca.markets/us/docs/about-market-data-api), updated approximately October 2026: Basic/IEX quotas and Trading/Broker separation.
- **A2 — HIGH:** [Alpaca batched latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1), updated approximately May 2026: symbol list, feed parameter and delayed alternative.
- **A3 — HIGH for text; limited applicability:** [Official Alpaca Broker documentation source](https://github.com/alpacahq/bkdocs/blob/master/content/market-data/_index.md): sandbox redistribution wording and production sales handoff; older page, not production entitlement proof.
- **F1 — HIGH:** [Finnhub terms](https://finnhub.io/terms-of-service): personal-use and third-party/derived-data sharing restrictions; no visible revision date.
- **T1 — HIGH:** [Twelve Data Basic/business pricing](https://twelvedata.com/pricing-business): limits and internal non-display/external-display plan distinction.
- **T2 — HIGH:** [Twelve Data credit accounting](https://support.twelvedata.com/en/articles/5615854-credits): per-symbol charge and daily reset.
- **M1 — HIGH:** [Massive stock pricing](https://massive.com/pricing?product=stocks): free end-of-day and individual-use scope.
- **V1 — HIGH:** [Alpha Vantage support](https://www.alphavantage.co/support/): 25/day standard free allowance and premium current US data.
- **C1 — HIGH:** [exchange_calendars release](https://pypi.org/project/exchange_calendars/4.13.2/), released 2026-03-10.
- **C2 — HIGH:** [exchange_calendars 4.13.2 tagged metadata](https://raw.githubusercontent.com/gerrymanoim/exchange_calendars/4.13.2/pyproject.toml): Python 3.14 classifier and test group.
- **C3 — HIGH:** [NYSE holidays/hours](https://www.nyse.com/markets/hours-calendars): official planned sessions and annual early closes.
- **C4 — HIGH:** [Nasdaq trading calendar](https://nasdaqtrader.com/Trader.aspx?id=Calendar): exchange holiday and early-close schedule.
- **C5 — HIGH:** [pandas_market_calendars project description](https://pypi.org/project/pandas_market_calendars/): package-managed calendars and dependency/update behavior.

---
*Research only. Production-provider selection remains conditional on entitlement and owner feed-coverage acceptance.*

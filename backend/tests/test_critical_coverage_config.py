"""Keep the documented financial gate identical to the enforced CI gate."""

import re
from pathlib import Path

CRITICAL_MODULES = (
    "app/services/otp.py",
    "app/services/auth.py",
    "app/services/accounts.py",
    "app/services/ratelimit.py",
    "app/services/email.py",
    "app/core/security.py",
    "app/core/deps.py",
    "app/services/price_rules.py",
    "app/services/prices.py",
    "app/services/trade_math.py",
    "app/services/trading.py",
    "app/services/portfolio_math.py",
    "app/services/portfolio.py",
    "app/services/history.py",
    "app/api/v1/history.py",
    "app/services/stock_admission.py",
    "app/services/stock_quote_rules.py",
    "app/services/stock_quotes.py",
    "app/services/stock_sessions.py",
    "app/services/stocks.py",
    "app/api/v1/stocks.py",
    "app/services/corporate_action_rules.py",
    "app/services/stock_action_rules.py",
    "app/services/alpaca_actions.py",
    "app/services/stock_ownership.py",
    "app/services/corporate_actions.py",
    "app/tasks/stock_actions.py",
    "app/tasks/stock_scheduler.py",
    "app/services/stock_action_reconciliation.py",
    "app/services/stock_trade_math.py",
    "app/services/stock_trading_rules.py",
    "app/services/stock_status_rules.py",
    "app/services/stock_status.py",
    "app/services/stock_eligibility.py",
    "app/services/stock_trading.py",
    "app/services/trade_idempotency.py",
    "app/services/stock_valuation.py",
    "app/api/v1/stock_trades.py",
    "app/tasks/stock_status.py",
    "app/services/dividend_rules.py",
    "app/services/dividends.py",
    "app/services/event_history.py",
    "app/schemas/event_history.py",
    "app/api/v1/event_history.py",
    "app/tasks/dividends.py",
    "app/tasks/scheduler.py",
    "app/db/dev_bootstrap.py",
)


def test_critical_coverage_gate_includes_all_financial_services() -> None:
    root = Path(__file__).resolve().parents[2]
    lists = []
    for path in (root / ".github/workflows/ci.yml", root / "CLAUDE.md"):
        matches = re.findall(r"coverage report --include=(\S+) --fail-under=100", path.read_text())
        assert len(matches) == 1
        modules = matches[0].split(",")
        assert tuple(modules) == CRITICAL_MODULES, f"{path.name} omits or changes critical paths"
        assert len(modules) == len(set(modules))
        assert all((root / "backend" / module).is_file() for module in modules)
        lists.append(matches[0])
    assert lists[0] == lists[1]


def test_backend_branch_coverage_and_node24_are_explicit() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/ci.yml").read_text().split("  frontend:", 1)[0]
    assert "pytest --cov=app --cov-branch --cov-fail-under=80" in workflow
    assert "uses: actions/setup-node@v7" in workflow
    assert "node-version-file: frontend/.nvmrc" in workflow
    assert workflow.index("uses: actions/setup-node@v7") < workflow.index("uv run pytest")
    assert (root / "frontend/.nvmrc").read_text().strip().split(".")[0] == "24"


def test_stock_browser_ci_uses_guarded_isolated_runner() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/ci.yml").read_text()
    assert "python3 deploy/tests/run-stock-browser.py" in workflow
    runner = (root / "deploy/tests/run-stock-browser.py").read_text()
    assert "COMPOSE_DISABLE_ENV_FILE" in runner
    assert "birja-phase09-e2e-test" in runner

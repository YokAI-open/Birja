"""Keep the documented financial gate identical to the enforced CI gate."""

import re
from pathlib import Path


def test_critical_coverage_gate_includes_all_financial_services() -> None:
    root = Path(__file__).resolve().parents[2]
    lists = []
    for path in (root / ".github/workflows/ci.yml", root / "CLAUDE.md"):
        matches = re.findall(r"coverage report --include=(\S+) --fail-under=100", path.read_text())
        assert len(matches) == 1
        modules = matches[0].split(",")
        for name in ("portfolio_math", "portfolio", "history"):
            assert f"app/services/{name}.py" in modules
        assert "app/api/v1/history.py" in modules
        assert len(modules) == len(set(modules))
        assert all((root / "backend" / module).is_file() for module in modules)
        lists.append(matches[0])
    assert lists[0] == lists[1]

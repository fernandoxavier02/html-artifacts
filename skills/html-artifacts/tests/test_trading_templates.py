"""TDD Batch 2 — Validação dos templates de domínio Trading."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestBacktestComparison:
    def test_render_creates_file(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "backtest-comparison",
                {
                    "title": "Backtest XAUUSD",
                    "strategies": [
                        {
                            "name": "EMA Cross H1",
                            "equity_curve": [10000, 10120, 10080, 10250],
                            "drawdown_curve": [0, 0, -0.4, 0],
                            "trades": 42,
                            "win_rate": 58.3,
                            "sharpe": 1.2,
                            "max_dd_pct": -4.2,
                            "pnl_total": 1250.0,
                        },
                        {
                            "name": "RSI M30",
                            "equity_curve": [10000, 10050, 10100, 10180],
                            "drawdown_curve": [0, -0.5, 0, 0],
                            "trades": 68,
                            "win_rate": 51.5,
                            "sharpe": 0.9,
                            "max_dd_pct": -2.8,
                            "pnl_total": 680.0,
                        },
                    ],
                },
            )
            assert path.exists()
            html = path.read_text(encoding="utf-8")
            assert "EMA Cross H1" in html
            assert "RSI M30" in html

    def test_contains_metrics_table(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "backtest-comparison",
                {
                    "title": "Backtest",
                    "strategies": [
                        {
                            "name": "S1",
                            "equity_curve": [10000, 10100],
                            "drawdown_curve": [0, 0],
                            "trades": 10,
                            "win_rate": 50.0,
                            "sharpe": 1.0,
                            "max_dd_pct": -1.0,
                            "pnl_total": 100.0,
                        }
                    ],
                },
            )
            html = path.read_text(encoding="utf-8")
            assert "Sharpe" in html or "sharpe" in html.lower()


class TestRiskDashboard:
    def test_render_creates_file(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "risk-dashboard",
                {
                    "title": "Risk Dashboard",
                    "exposures": [
                        {
                            "symbol": "XAUUSD",
                            "notional": 50000.0,
                            "var_95": -1200.0,
                            "var_99": -2100.0,
                            "kelly_fraction": 0.15,
                        },
                        {
                            "symbol": "EURUSD",
                            "notional": 30000.0,
                            "var_95": -800.0,
                            "var_99": -1500.0,
                            "kelly_fraction": 0.22,
                        },
                    ],
                },
            )
            assert path.exists()
            html = path.read_text(encoding="utf-8")
            assert "XAUUSD" in html
            assert "VaR" in html or "var" in html.lower()


class TestSignalAudit:
    def test_render_creates_file(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "signal-audit",
                {
                    "title": "Signal Audit",
                    "signals": [
                        {
                            "id": "s1",
                            "timestamp": "2026-05-11T10:00:00Z",
                            "symbol": "XAUUSD",
                            "side": "buy",
                            "signal_price": 2345.5,
                            "exec_price": 2345.7,
                            "slippage_bps": 0.85,
                            "filled": True,
                            "pnl": 120.0,
                        },
                        {
                            "id": "s2",
                            "timestamp": "2026-05-11T11:00:00Z",
                            "symbol": "XAUUSD",
                            "side": "sell",
                            "signal_price": 2350.0,
                            "exec_price": None,
                            "slippage_bps": None,
                            "filled": False,
                            "pnl": None,
                        },
                    ],
                },
            )
            assert path.exists()
            html = path.read_text(encoding="utf-8")
            assert "s1" in html
            assert "buy" in html


class TestMarketRegime:
    def test_render_creates_file(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "market-regime",
                {
                    "title": "Market Regimes",
                    "regimes": [
                        {
                            "label": "Morning",
                            "start": "2026-05-11T09:00:00Z",
                            "end": "2026-05-11T12:00:00Z",
                            "regime": "trending",
                            "stats": {"volatility": 0.12, "volume": 1500},
                        },
                        {
                            "label": "Afternoon",
                            "start": "2026-05-11T12:00:00Z",
                            "end": "2026-05-11T17:00:00Z",
                            "regime": "ranging",
                            "stats": {"volatility": 0.08, "volume": 900},
                        },
                    ],
                },
            )
            assert path.exists()
            html = path.read_text(encoding="utf-8")
            assert "trending" in html
            assert "ranging" in html

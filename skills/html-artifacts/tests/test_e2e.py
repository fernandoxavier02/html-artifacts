"""TDD Batch 4 — Teste End-to-End da skill html-artifacts."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestEndToEndWorkflow:
    def test_full_pipeline(self) -> None:
        """Gera artifacts, atualiza index, valida integração."""
        from artifact_engine import ArtifactEngine
        from build_artifact_index import build_index

        with tempfile.TemporaryDirectory() as tmp:
            artifacts_dir = Path(tmp)
            engine = ArtifactEngine(output_dir=artifacts_dir)

            # 1. Gera artifact de backtest
            p1 = engine.render(
                "backtest-comparison",
                {
                    "title": "E2E Backtest",
                    "strategies": [
                        {
                            "name": "S1",
                            "equity_curve": [10000, 10100],
                            "drawdown_curve": [0, 0],
                            "trades": 5,
                            "win_rate": 60.0,
                            "sharpe": 1.1,
                            "max_dd_pct": -1.0,
                            "pnl_total": 100.0,
                        }
                    ],
                },
            )
            assert p1.exists()

            # 2. Gera artifact de risk
            p2 = engine.render(
                "risk-dashboard",
                {
                    "title": "E2E Risk",
                    "exposures": [
                        {
                            "symbol": "XAUUSD",
                            "notional": 10000.0,
                            "var_95": -200.0,
                            "var_99": -400.0,
                            "kelly_fraction": 0.1,
                        }
                    ],
                },
            )
            assert p2.exists()

            # 3. Index gerado automaticamente pelo engine
            idx = artifacts_dir / "index.html"
            assert idx.exists()

            # 4. Valida index
            html = idx.read_text(encoding="utf-8")
            assert "E2E Backtest" in html
            assert "E2E Risk" in html
            assert "backtest" in html.lower()
            assert "risk" in html.lower()

    def test_render_to_string_no_persistence(self) -> None:
        from artifact_engine import ArtifactEngine

        engine = ArtifactEngine()
        html = engine.render_to_string(
            "table",
            {
                "title": "String Only",
                "columns": [{"key": "a", "label": "A"}],
                "rows": [{"a": "1"}],
            },
        )
        assert "String Only" in html
        assert "<table" in html

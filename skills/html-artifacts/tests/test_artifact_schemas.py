"""TDD Batch 0 — Validação de schemas de dataset para artifacts."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestSchemasModuleExists:
    def test_module_importable(self) -> None:
        try:
            import artifact_schemas  # noqa: F401
        except ImportError as exc:
            pytest.skip(f"artifact_schemas.py ainda não existe: {exc}")


class TestTableDataset:
    def test_class_exists(self) -> None:
        pytest.importorskip("artifact_schemas")
        from artifact_schemas import TableDataset

        assert "columns" in TableDataset.model_fields
        assert "rows" in TableDataset.model_fields

    def test_validates_minimal_dataset(self) -> None:
        from artifact_schemas import TableDataset

        ds = TableDataset(
            title="Demo",
            columns=[{"key": "name", "label": "Nome"}],
            rows=[{"name": "Alice"}],
        )
        assert ds.title == "Demo"
        assert len(ds.columns) == 1
        assert len(ds.rows) == 1

    def test_rejects_row_missing_key(self) -> None:
        from artifact_schemas import TableDataset

        with pytest.raises(Exception):
            TableDataset(
                title="Demo",
                columns=[{"key": "name", "label": "Nome"}],
                rows=[{"wrong": "Alice"}],
            )


class TestReportDataset:
    def test_class_exists(self) -> None:
        pytest.importorskip("artifact_schemas")
        from artifact_schemas import ReportDataset

        assert "sections" in ReportDataset.model_fields

    def test_validates_sections(self) -> None:
        from artifact_schemas import ReportDataset

        ds = ReportDataset(
            title="Relatório",
            sections=[
                {"heading": "Veredicto", "body": "Tudo OK", "alert": "ok"},
            ],
        )
        assert len(ds.sections) == 1


class TestInteractiveDataset:
    def test_class_exists(self) -> None:
        pytest.importorskip("artifact_schemas")
        from artifact_schemas import InteractiveDataset

        assert "items" in InteractiveDataset.model_fields

    def test_validates_items(self) -> None:
        from artifact_schemas import InteractiveDataset

        ds = InteractiveDataset(
            title="Validação",
            items=[
                {"id": "q1", "label": "Pergunta 1", "type": "decision"},
            ],
        )
        assert ds.items[0].id == "q1"


class TestTradingSchemas:
    def test_backtest_dataset_exists(self) -> None:
        pytest.importorskip("artifact_schemas")
        from artifact_schemas import BacktestDataset

        assert "strategies" in BacktestDataset.model_fields

    def test_risk_dataset_exists(self) -> None:
        pytest.importorskip("artifact_schemas")
        from artifact_schemas import RiskDataset

        assert "exposures" in RiskDataset.model_fields

    def test_signal_dataset_exists(self) -> None:
        pytest.importorskip("artifact_schemas")
        from artifact_schemas import SignalDataset

        assert "signals" in SignalDataset.model_fields

    def test_regime_dataset_exists(self) -> None:
        pytest.importorskip("artifact_schemas")
        from artifact_schemas import RegimeDataset

        assert "regimes" in RegimeDataset.model_fields

"""TDD Batch 1 — Validação da ArtifactEngine e renderers."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestArtifactEngineExists:
    def test_class_importable(self) -> None:
        pytest.importorskip("artifact_engine")
        from artifact_engine import ArtifactEngine

        assert hasattr(ArtifactEngine, "render")

    def test_render_signature(self) -> None:
        from artifact_engine import ArtifactEngine

        import inspect

        sig = inspect.signature(ArtifactEngine.render)
        params = list(sig.parameters.keys())
        assert "type_id" in params
        assert "dataset" in params


class TestArtifactEngineTable:
    def test_render_table_creates_file(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "table",
                {
                    "title": "Test Table",
                    "columns": [{"key": "a", "label": "A"}],
                    "rows": [{"a": "1"}],
                },
            )
            assert path.exists()
            assert path.suffix == ".html"
            assert "Test Table" in path.read_text(encoding="utf-8")

    def test_render_table_contains_data(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "table",
                {
                    "title": "Trades",
                    "columns": [{"key": "symbol", "label": "Symbol"}],
                    "rows": [{"symbol": "XAUUSD"}],
                },
            )
            html = path.read_text(encoding="utf-8")
            assert "XAUUSD" in html


class TestArtifactEngineReport:
    def test_render_report_creates_file(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "report",
                {
                    "title": "Audit",
                    "sections": [{"heading": "Verdict", "body": "OK"}],
                },
            )
            assert path.exists()
            html = path.read_text(encoding="utf-8")
            assert "Audit" in html
            assert "Verdict" in html


class TestArtifactEngineInteractive:
    def test_render_interactive_creates_file(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "interactive",
                {
                    "title": "Validation",
                    "items": [{"id": "q1", "label": "Q1", "type": "decision"}],
                },
            )
            assert path.exists()
            html = path.read_text(encoding="utf-8")
            assert "Validation" in html


class TestArtifactEngineThariq:
    def test_render_thariq_status_uses_template(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render(
                "status-report",
                {
                    "title": "FX Studio Status",
                    "subtitle": "Week 1",
                    "sections": [
                        {"title": "Highlights", "content": "<p>All green</p>"}
                    ],
                },
            )
            assert path.exists()
            html = path.read_text(encoding="utf-8")
            assert "FX Studio Status" in html


class TestArtifactEngineCSS:
    def test_copies_base_css_to_output_dir(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            engine = ArtifactEngine(output_dir=out)
            engine.render(
                "table",
                {
                    "title": "CSS Test",
                    "columns": [{"key": "a", "label": "A"}],
                    "rows": [{"a": "1"}],
                },
            )
            assert (out / "base.css").exists()

    def test_normalizes_base_css_link(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            engine = ArtifactEngine(output_dir=out)
            path = engine.render(
                "status-report",
                {"title": "Link Test", "template_id": "11", "sections": []},
            )
            html = path.read_text(encoding="utf-8")
            assert 'href="base.css"' in html
            assert 'href="../base.css"' not in html


class TestArtifactEngineErrors:
    def test_unknown_type_raises(self) -> None:
        from artifact_engine import ArtifactEngine, UnknownRendererError

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            with pytest.raises(UnknownRendererError):
                engine.render("nonexistent", {})

    def test_invalid_dataset_raises(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            with pytest.raises(Exception):
                engine.render(
                    "table",
                    {"title": "Bad", "columns": [], "rows": "not-a-list"},
                )

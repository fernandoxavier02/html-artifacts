"""TDD Batch 3 — Validação do ArtifactIndex e landing page."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestArtifactIndexExists:
    def test_module_importable(self) -> None:
        pytest.importorskip("build_artifact_index")
        import build_artifact_index  # noqa: F401


class TestArtifactIndexBuild:
    def test_index_creates_file(self) -> None:
        from build_artifact_index import build_index

        with tempfile.TemporaryDirectory() as tmp:
            artifacts_dir = Path(tmp) / "artifacts"
            artifacts_dir.mkdir()
            # Cria 2 artifacts dummy
            (artifacts_dir / "table-20260511-120000.html").write_text(
                '<html><head><title>Table A</title><meta name="generator" content="artifact_engine.table"><meta name="artifact-tags" content="data"></head></html>',
                encoding="utf-8",
            )
            (artifacts_dir / "report-20260511-130000.html").write_text(
                '<html><head><title>Report B</title><meta name="generator" content="artifact_engine.report"><meta name="artifact-tags" content="report"></head></html>',
                encoding="utf-8",
            )
            index_path = build_index(artifacts_dir)
            assert index_path.exists()
            assert index_path.name == "index.html"

    def test_index_lists_artifacts(self) -> None:
        from build_artifact_index import build_index

        with tempfile.TemporaryDirectory() as tmp:
            artifacts_dir = Path(tmp) / "artifacts"
            artifacts_dir.mkdir()
            (artifacts_dir / "status-20260511-120000.html").write_text(
                '<html><head><title>Status Report</title><meta name="generator" content="artifact_engine.status"><meta name="artifact-tags" content="status"></head></html>',
                encoding="utf-8",
            )
            index_path = build_index(artifacts_dir)
            html = index_path.read_text(encoding="utf-8")
            assert "Status Report" in html
            assert "2026-05-11" in html

    def test_index_is_responsive(self) -> None:
        from build_artifact_index import build_index

        with tempfile.TemporaryDirectory() as tmp:
            artifacts_dir = Path(tmp) / "artifacts"
            artifacts_dir.mkdir()
            index_path = build_index(artifacts_dir)
            html = index_path.read_text(encoding="utf-8")
            assert "@media" in html


class TestArtifactIndexFilters:
    def test_filter_by_type(self) -> None:
        from build_artifact_index import build_index

        with tempfile.TemporaryDirectory() as tmp:
            artifacts_dir = Path(tmp) / "artifacts"
            artifacts_dir.mkdir()
            (artifacts_dir / "table-20260511-120000.html").write_text(
                '<html><head><title>Table</title><meta name="artifact-tags" content="table"></head></html>',
                encoding="utf-8",
            )
            (artifacts_dir / "report-20260511-130000.html").write_text(
                '<html><head><title>Report</title><meta name="artifact-tags" content="report"></head></html>',
                encoding="utf-8",
            )
            index_path = build_index(artifacts_dir)
            html = index_path.read_text(encoding="utf-8")
            # Deve conter botões/filtros por tipo
            assert "table" in html.lower()
            assert "report" in html.lower()

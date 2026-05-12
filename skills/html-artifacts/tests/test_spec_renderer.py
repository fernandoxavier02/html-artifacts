"""TDD Batch 6 — Validação do Spec Parser & Renderer."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# Fixtures markdown inline para independência de projeto
REQUIREMENTS_MD = """---
spec: test-pipeline
version: 0.1.0
language: pt
created_at: 2026-04-30T14:30:00Z
---

# test-pipeline

## Project Description
Pipeline de teste.

## User Story
As a dev, I want tests, so that I sleep.

## Scope Boundaries

### In Scope
- Item A

### Out of Scope
- Item B

## Requirements

### Requirement 1: Split Temporal

**Description:** O pipeline deve usar divisao temporal.

**Acceptance Criteria:**
- WHEN o dataset for carregado, THE Pipeline SHALL dividir em treino e teste
- IF o parametro X for configurado, THEN THE Pipeline SHALL rejeitar

_Requirements: 1.1, 1.2_

### Requirement 2: Labeling

**Description:** Labeling baseado em volatilidade.

**Acceptance Criteria:**
- WHEN o label for calculado, THE Labeling Engine SHALL usar ATR

_Requirements: 2.1_

## Prework Analysis

- [x] Data availability checked
- [ ] Dependencies identified
- [x] Risks assessed

## Coverage Matrix

| Requirement | Testable | Covered |
|-------------|----------|---------|
| 1.1         | Yes      | No      |
| 1.2         | Yes      | Yes     |
| 2.1         | Yes      | No      |
"""

DESIGN_MD = """---
spec: test-pipeline
version: 0.1.0
---

# Design: test-pipeline

## Overview
Este design corrige o pipeline.

## Goals & Non-Goals

### Goals
- Eliminar data leakage
- Metricas de trading

### Non-Goals
- Treinar modelo novo

## Boundary Commitments

### In Boundary
- Modulos de pipeline

### Out of Boundary
- RiskEngine

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Python class | PascalCase | `TemporalSplitter` |

## Architecture

### Component Diagram
```
Input -> Splitter -> Labeler -> Model
```

### Data Flow
1. Leitura de parquet
2. Split temporal
3. Labeling
"""

TASKS_MD = """---
spec: test-pipeline
version: 0.1.0
---

# Tasks: test-pipeline

## CHECKPOINT 1 — Foundation

- [ ] 1. Setup de testes
  - Criar diretorios
  - Observable: pytest coleta sem erro
  - _Requirements: 1.1_
  - _Boundary: Pipeline_

- [x] 1.2 Criar fixture
  - Gerar DataFrame
  - Observable: 1000 linhas
  - _Requirements: 1.1, 2.1_

## CHECKPOINT 2 — Core

- [ ] 2. TemporalSplitter
  - Implementar divisao
  - Observable: split retorna 3 DataFrames
  - _Requirements: 1.1, 1.2_
  - _Boundary: TemporalSplitter_
"""


class TestSpecParser:
    def test_module_importable(self) -> None:
        pytest.importorskip("spec_parser")
        from spec_parser import SpecParser

        assert hasattr(SpecParser, "parse")

    def test_extracts_frontmatter(self) -> None:
        from spec_parser import SpecParser

        result = SpecParser().parse(REQUIREMENTS_MD)
        assert result["frontmatter"]["spec"] == "test-pipeline"
        assert result["frontmatter"]["version"] == "0.1.0"

    def test_identifies_requirements(self) -> None:
        from spec_parser import SpecParser

        result = SpecParser().parse(REQUIREMENTS_MD)
        reqs = result.get("requirements", [])
        assert len(reqs) == 2
        assert reqs[0]["title"] == "Split Temporal"
        assert "WHEN o dataset for carregado" in reqs[0]["criteria"][0]
        assert reqs[1]["title"] == "Labeling"

    def test_extracts_checkboxes(self) -> None:
        from spec_parser import SpecParser

        result = SpecParser().parse(REQUIREMENTS_MD)
        prework = result.get("prework", [])
        assert len(prework) == 3
        assert prework[0]["checked"] is True
        assert prework[1]["checked"] is False
        assert prework[2]["checked"] is True

    def test_extracts_coverage_matrix(self) -> None:
        from spec_parser import SpecParser

        result = SpecParser().parse(REQUIREMENTS_MD)
        matrix = result.get("coverage_matrix", [])
        assert len(matrix) == 3
        assert matrix[0]["Requirement"] == "1.1"
        assert matrix[0]["Covered"] == "No"

    def test_identifies_design_sections(self) -> None:
        from spec_parser import SpecParser

        result = SpecParser().parse(DESIGN_MD)
        assert result["type"] == "design"
        sections = result.get("sections", [])
        titles = [s["title"] for s in sections]
        assert "Overview" in titles
        assert "Goals & Non-Goals" in titles
        assert "Naming Conventions" in titles

    def test_identifies_tasks_checkpoints(self) -> None:
        from spec_parser import SpecParser

        result = SpecParser().parse(TASKS_MD)
        assert result["type"] == "tasks"
        checkpoints = result.get("checkpoints", [])
        assert len(checkpoints) == 2
        assert checkpoints[0]["title"] == "CHECKPOINT 1 — Foundation"
        assert len(checkpoints[0]["tasks"]) == 2
        assert checkpoints[0]["tasks"][0]["checked"] is False
        assert checkpoints[0]["tasks"][1]["checked"] is True
        assert "1.1" in checkpoints[0]["tasks"][0]["requirement_refs"]


class TestSpecRenderer:
    def _render(self, md_text: str) -> str:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render_from_spec_text(md_text)
            return path.read_text(encoding="utf-8")

    def test_requirements_creates_file(self) -> None:
        html = self._render(REQUIREMENTS_MD)
        assert "test-pipeline" in html
        assert "Split Temporal" in html
        assert "Labeling" in html

    def test_tasks_has_persisted_checkboxes(self) -> None:
        html = self._render(TASKS_MD)
        assert "localStorage" in html
        assert "CHECKPOINT 1" in html

    def test_design_has_toc(self) -> None:
        html = self._render(DESIGN_MD)
        assert "nav" in html or "toc" in html.lower()
        assert "Overview" in html

    def test_coverage_matrix_table(self) -> None:
        html = self._render(REQUIREMENTS_MD)
        assert "<table" in html
        assert "1.1" in html
        assert "Covered" in html

    def test_engine_render_from_spec_api(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            assert hasattr(engine, "render_from_spec_text")
            path = engine.render_from_spec_text(REQUIREMENTS_MD)
            assert path.exists()
            assert path.suffix == ".html"

    def test_engine_render_from_spec_path(self) -> None:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            spec_file = Path(tmp) / "requirements.md"
            spec_file.write_text(REQUIREMENTS_MD, encoding="utf-8")
            engine = ArtifactEngine(output_dir=Path(tmp) / "out")
            path = engine.render_from_spec(spec_file)
            assert path.exists()
            assert path.suffix == ".html"

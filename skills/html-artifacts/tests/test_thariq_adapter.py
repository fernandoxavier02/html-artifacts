"""TDD Batch 1 — Validação do ThariqAdapter."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestThariqRendererExists:
    def test_class_importable(self) -> None:
        pytest.importorskip("artifact_engine")
        from artifact_engine import ThariqRenderer

        assert hasattr(ThariqRenderer, "render")


class TestThariqRendererBasic:
    def test_replaces_title(self) -> None:
        from artifact_engine import ThariqRenderer

        html = ThariqRenderer().render(
            template_id="11",
            dataset={"title": "New Title", "brand": "FX Studio"},
        )
        assert "<title>New Title</title>" in html or "<title>New Title —" in html

    def test_preserves_base_css_link(self) -> None:
        from artifact_engine import ThariqRenderer

        html = ThariqRenderer().render(
            template_id="11",
            dataset={"title": "Test", "brand": "FX Studio"},
        )
        # Template 11 já tem link para base.css após refatoração
        assert "base.css" in html

    def test_replaces_brand_in_text(self) -> None:
        from artifact_engine import ThariqRenderer

        html = ThariqRenderer().render(
            template_id="11",
            dataset={"title": "FX Studio Status", "brand": "FX Studio"},
        )
        # O title deve conter a brand
        assert "FX Studio Status" in html
        # Não deve haver marca genérica do template original no title
        assert "Birchline" not in html


class TestThariqRendererUnknownTemplate:
    def test_raises_on_missing_template(self) -> None:
        from artifact_engine import ThariqRenderer, TemplateNotFoundError

        renderer = ThariqRenderer()
        with pytest.raises(TemplateNotFoundError):
            renderer.render(template_id="99", dataset={})

"""TDD Batch 0 — Validação da refatoração de template Thariq com base.css."""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".claude"
    / "skills"
    / "html-artifacts"
    / "examples"
    / "11-status-report.html"
)
BASE_CSS_PATH = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "base.css"


class TestTemplate11Refactor:
    @pytest.fixture(scope="module")
    def html_text(self) -> str:
        assert TEMPLATE_PATH.exists()
        return TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_links_base_css(self, html_text: str) -> None:
        assert '<link rel="stylesheet" href="../base.css">' in html_text

    def test_no_duplicate_root_block(self, html_text: str) -> None:
        """Garante que :root foi removido do template (vive em base.css)."""
        count = html_text.count(":root")
        assert count == 0, f"Template ainda contém {count} bloco(s) :root"

    def test_no_duplicate_body_reset(self, html_text: str) -> None:
        """Body reset deve viver em base.css, não no template."""
        style_start = html_text.find("<style>")
        style_end = html_text.find("</style>")
        style_block = html_text[style_start:style_end]
        # Verifica especificamente se há regra 'body {' com background ivory
        import re
        body_match = re.search(r'body\s*\{([^}]*)\}', style_block)
        if body_match:
            assert "background" not in body_match.group(1), (
                "body reset duplicado no template"
            )

    def test_preserves_specific_styles(self, html_text: str) -> None:
        """Estilos específicos do template devem ser mantidos."""
        style_start = html_text.find("<style>")
        style_end = html_text.find("</style>")
        style_block = html_text[style_start:style_end]

        assert ".stat-card" in style_block, "estilo .stat-card removido acidentalmente"
        assert ".summary-band" in style_block, "estilo .summary-band removido acidentalmente"
        assert "table.shipped" in style_block, "estilo table.shipped removido acidentalmente"
        assert ".carryover" in style_block, "estilo .carryover removido acidentalmente"

    def test_page_width_override(self, html_text: str) -> None:
        """Template deve manter sua largura específica."""
        assert ".page { max-width: 860px; }" in html_text

    def test_valid_html_structure(self, html_text: str) -> None:
        assert html_text.strip().startswith("<!doctype html>")
        assert "<html" in html_text
        assert "</html>" in html_text
        assert "<body>" in html_text
        assert "</body>" in html_text

    def test_css_inline_reduction(self, html_text: str) -> None:
        """CSS inline deve ter reduzido significativamente do original ~295 linhas."""
        style_start = html_text.find("<style>")
        style_end = html_text.find("</style>")
        style_block = html_text[style_start:style_end]
        css_lines = [ln for ln in style_block.splitlines() if ln.strip()]
        assert len(css_lines) < 250, (
            f"CSS inline ainda muito grande: {len(css_lines)} linhas"
        )

"""TDD Batch 0 — Validação do design system base.css."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BASE_CSS_PATH = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "base.css"

# Variáveis CSS obrigatórias da paleta editorial Thariq
REQUIRED_VARS = [
    "--ivory",
    "--slate",
    "--clay",
    "--oat",
    "--olive",
    "--rust",
    "--gray-100",
    "--gray-300",
    "--gray-500",
    "--gray-700",
    "--white",
    "--serif",
    "--sans",
    "--mono",
]

# Variáveis de layout/design system
REQUIRED_LAYOUT_VARS = [
    "--radius-panel",
    "--radius-row",
    "--border",
]


class TestBaseCSSExists:
    def test_file_exists(self) -> None:
        assert BASE_CSS_PATH.exists(), f"base.css não encontrado em {BASE_CSS_PATH}"

    def test_file_is_not_empty(self) -> None:
        assert BASE_CSS_PATH.stat().st_size > 500, "base.css está suspeitamente pequeno"


class TestBaseCSSPalette:
    @pytest.fixture(scope="module")
    def css_text(self) -> str:
        if not BASE_CSS_PATH.exists():
            pytest.skip("base.css ainda não existe")
        return BASE_CSS_PATH.read_text(encoding="utf-8")

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_required_css_variable_present(self, css_text: str, var: str) -> None:
        assert var in css_text, f"Variável CSS obrigatória {var} ausente em base.css"

    @pytest.mark.parametrize("var", REQUIRED_LAYOUT_VARS)
    def test_required_layout_variable_present(self, css_text: str, var: str) -> None:
        assert var in css_text, f"Variável de layout {var} ausente em base.css"


class TestBaseCSSStructure:
    @pytest.fixture(scope="module")
    def css_text(self) -> str:
        if not BASE_CSS_PATH.exists():
            pytest.skip("base.css ainda não existe")
        return BASE_CSS_PATH.read_text(encoding="utf-8")

    def test_has_universal_reset(self, css_text: str) -> None:
        assert "box-sizing: border-box" in css_text
        assert "margin: 0" in css_text or "margin:0" in css_text
        assert "padding: 0" in css_text or "padding:0" in css_text

    def test_has_body_base_styles(self, css_text: str) -> None:
        # body deve ter background ivory, font-family sans, antialiased
        assert "background: var(--ivory)" in css_text or "background:var(--ivory)" in css_text
        assert "font-family: var(--sans)" in css_text or "font-family:var(--sans)" in css_text
        assert "-webkit-font-smoothing: antialiased" in css_text

    def test_no_duplicate_root_properties(self, css_text: str) -> None:
        """Garante que não há propriedades duplicadas dentro de :root."""
        root_match = re.search(r":root\s*\{([^}]*)\}", css_text, re.DOTALL)
        if not root_match:
            pytest.skip(":root block não encontrado")
        root_body = root_match.group(1)
        props = re.findall(r"(--[\w-]+)\s*:", root_body)
        duplicates = {p for p in props if props.count(p) > 1}
        assert not duplicates, f"Propriedades duplicadas em :root: {duplicates}"

    def test_h1_uses_serif(self, css_text: str) -> None:
        assert "font-family: var(--serif)" in css_text or "font-family:var(--serif)" in css_text

    def test_has_page_container(self, css_text: str) -> None:
        assert ".page" in css_text or ".wrap" in css_text or ".sheet" in css_text


class TestBaseCSSNoExternalDeps:
    @pytest.fixture(scope="module")
    def css_text(self) -> str:
        if not BASE_CSS_PATH.exists():
            pytest.skip("base.css ainda não existe")
        return BASE_CSS_PATH.read_text(encoding="utf-8")

    def test_no_cdn_urls(self, css_text: str) -> None:
        cdn_patterns = ["cdnjs.cloudflare.com", "fonts.googleapis.com", "unpkg.com", "cdn.jsdelivr.net"]
        for pat in cdn_patterns:
            assert pat not in css_text, f"base.css contém dependência externa: {pat}"

    def test_no_import_statements(self, css_text: str) -> None:
        assert "@import" not in css_text, "base.css não deve usar @import (deve ser self-contained)"

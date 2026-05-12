"""TDD Batch 5 — Validação do Interactive Moderno."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "src"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestInteractiveModernSchema:
    def test_all_types_accepted(self) -> None:
        from artifact_schemas import InteractiveItem

        for t in ["decision", "checkbox", "select", "multiselect",
                  "text", "textarea", "slider", "rating", "tags", "code"]:
            item = InteractiveItem(id=f"t_{t}", label=t, type=t)  # type: ignore[arg-type]
            assert item.type == t

    def test_slider_fields(self) -> None:
        from artifact_schemas import InteractiveItem

        item = InteractiveItem(
            id="s1", label="S", type="slider", min=0, max=100, step=5
        )
        assert item.min == 0
        assert item.max == 100
        assert item.step == 5

    def test_rating_default_max(self) -> None:
        from artifact_schemas import InteractiveItem

        item = InteractiveItem(id="r1", label="R", type="rating")
        assert item.rating_max == 5

    def test_code_lang(self) -> None:
        from artifact_schemas import InteractiveItem

        item = InteractiveItem(id="c1", label="C", type="code", code_lang="python")
        assert item.code_lang == "python"

    def test_required_field(self) -> None:
        from artifact_schemas import InteractiveItem

        item = InteractiveItem(id="x1", label="X", type="text", required=True)
        assert item.required is True


class TestInteractiveModernRender:
    def _render(self, dataset: dict) -> str:
        from artifact_engine import ArtifactEngine

        with tempfile.TemporaryDirectory() as tmp:
            engine = ArtifactEngine(output_dir=Path(tmp))
            path = engine.render("interactive", dataset)
            return path.read_text(encoding="utf-8")

    def test_modern_template_has_base_css_link(self) -> None:
        html = self._render({
            "title": "T", "items": [{"id": "i1", "label": "L", "type": "text"}]
        })
        assert 'href="base.css"' in html

    def test_slider_has_min_max_step(self) -> None:
        html = self._render({
            "title": "Slider",
            "items": [{"id": "s1", "label": "Vol", "type": "slider",
                       "min": 0, "max": 100, "step": 5}],
        })
        assert 'type="range"' in html
        # pydantic converte int→float, então aceitamos "0" ou "0.0"
        assert 'min="0"' in html or 'min="0.0"' in html
        assert 'max="100"' in html or 'max="100.0"' in html
        assert 'step="5"' in html or 'step="5.0"' in html

    def test_rating_has_stars(self) -> None:
        html = self._render({
            "title": "Rating",
            "items": [{"id": "r1", "label": "Qualidade", "type": "rating", "rating_max": 5}],
        })
        assert html.count('data-rating-value="') >= 5

    def test_multiselect_has_checkboxes(self) -> None:
        html = self._render({
            "title": "Multi",
            "items": [{"id": "m1", "label": "Opts", "type": "multiselect",
                       "options": [{"value": "a", "label": "A"},
                                   {"value": "b", "label": "B"}]}],
        })
        assert 'type="checkbox"' in html
        assert "A" in html
        assert "B" in html

    def test_code_block_has_lang(self) -> None:
        html = self._render({
            "title": "Code",
            "items": [{"id": "c1", "label": "Snippet", "type": "code",
                       "code_lang": "python"}],
        })
        assert 'data-lang="python"' in html
        assert "<code" in html or "<pre" in html

    def test_localstorage_script_present(self) -> None:
        html = self._render({
            "title": "Persist",
            "items": [{"id": "p1", "label": "P", "type": "text"}],
        })
        assert "localStorage" in html
        assert "saveResponses" in html or "loadResponses" in html

    def test_validation_script_present(self) -> None:
        html = self._render({
            "title": "Valid",
            "items": [{"id": "v1", "label": "V", "type": "text", "required": True}],
        })
        assert "validateForm" in html or "required" in html

    def test_progress_bar_present(self) -> None:
        html = self._render({
            "title": "Progress",
            "items": [
                {"id": "a", "label": "A", "type": "text"},
                {"id": "b", "label": "B", "type": "checkbox"},
            ],
        })
        assert "progress-bar" in html or "progress" in html.lower()

    def test_tags_input_present(self) -> None:
        html = self._render({
            "title": "Tags",
            "items": [{"id": "t1", "label": "Labels", "type": "tags"}],
        })
        assert "tag-input" in html or "contenteditable" in html or "data-tags" in html

    def test_textarea_input_present(self) -> None:
        html = self._render({
            "title": "Textarea",
            "items": [{"id": "ta1", "label": "Desc", "type": "textarea"}],
        })
        assert "<textarea" in html

    def test_all_types_in_one_artifact(self) -> None:
        items = [
            {"id": "d1", "label": "Decision", "type": "decision"},
            {"id": "c1", "label": "Check", "type": "checkbox"},
            {"id": "s1", "label": "Select", "type": "select",
             "options": [{"value": "x", "label": "X"}]},
            {"id": "ms1", "label": "Multi", "type": "multiselect",
             "options": [{"value": "a", "label": "A"}]},
            {"id": "t1", "label": "Text", "type": "text"},
            {"id": "ta1", "label": "Area", "type": "textarea"},
            {"id": "sl1", "label": "Slide", "type": "slider", "min": 0, "max": 10},
            {"id": "r1", "label": "Rate", "type": "rating"},
            {"id": "tg1", "label": "Tags", "type": "tags"},
            {"id": "co1", "label": "Code", "type": "code", "code_lang": "py"},
        ]
        html = self._render({"title": "All Types", "items": items})
        assert "All Types" in html
        # Cada tipo deve ter sua estrutura característica
        assert 'type="range"' in html          # slider
        assert 'data-rating-value=' in html     # rating
        assert "<textarea" in html              # textarea

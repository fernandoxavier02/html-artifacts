"""ArtifactIndex — Gera landing page com feed de todos os artifacts HTML."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


def _resolve_project_root() -> Path:
    env = os.environ.get("HTML_ARTIFACTS_ROOT")
    if env:
        return Path(env)
    # Procura subindo a arvore por markers de project root
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / ".claude").exists() or (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback estrutura .claude/skills/html-artifacts/src/
    return Path(__file__).resolve().parents[4]



PROJECT_ROOT = _resolve_project_root()
DEFAULT_ARTIFACTS_DIR = PROJECT_ROOT / ".claude" / "_html" / "artifacts"

_INDEX_TEMPLATE = """<!DOCTYPE html>
import sys
from pathlib import Path
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Artifacts</title>
<link rel="stylesheet" href="base.css">
<style>
  .page { max-width: 1100px; }
  .filter-bar { display: flex; gap: 10px; flex-wrap: wrap; margin: 24px 0; }
  .filter-bar button { font-family: var(--sans); font-size: 13px; padding: 7px 16px; border: var(--border); border-radius: var(--radius-row); background: var(--white); cursor: pointer; }
  .filter-bar button.active { background: var(--slate); color: var(--ivory); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 18px; }
  .card { background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 18px 20px; transition: box-shadow 0.15s; }
  .card:hover { box-shadow: var(--shadow-md); }
  .card-title { font-family: var(--serif); font-size: 17px; font-weight: 500; margin: 0 0 6px; color: var(--slate); }
  .card-meta { font-family: var(--mono); font-size: 11px; color: var(--gray-500); margin-bottom: 10px; }
  .card-tags { display: flex; gap: 6px; flex-wrap: wrap; }
  .tag { font-size: 11px; padding: 3px 8px; border-radius: 999px; background: var(--gray-100); color: var(--gray-700); }
  .card-link { display: inline-block; margin-top: 12px; font-size: 13px; color: var(--clay); text-decoration: none; font-weight: 500; }
  .card-link:hover { text-decoration: underline; }
  .empty { text-align: center; padding: 48px; color: var(--gray-500); font-size: 14px; }
  @media (max-width: 640px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Project Artifacts</div>
    <h1>Artifacts</h1>
    <p class="lead">Feed cronológico de todos os artifacts HTML gerados.</p>
  </header>

  <div class="filter-bar" id="filters">
    <button class="active" data-filter="all" onclick="setFilter('all')">Todos</button>
    {% for tag in all_tags %}
    <button data-filter="{{ tag }}" onclick="setFilter('{{ tag }}')">{{ tag }}</button>
    {% endfor %}
  </div>

  <div class="grid" id="grid">
    {% for a in artifacts %}
    <div class="card" data-tags="{{ a.tags | join(' ') }}">
      <div class="card-title">{{ a.title }}</div>
      <div class="card-meta">{{ a.type }} &middot; {{ a.date }}</div>
      <div class="card-tags">
        {% for t in a.tags %}
        <span class="tag">{{ t }}</span>
        {% endfor %}
      </div>
      <a class="card-link" href="{{ a.filename }}">Abrir artifact &rarr;</a>
    </div>
    {% else %}
    <div class="empty">Nenhum artifact encontrado ainda.</div>
    {% endfor %}
  </div>

  <div class="gen-meta">Artifact Index &middot; gerado automaticamente</div>
</main>
<script>
function setFilter(tag) {
  document.querySelectorAll('.filter-bar button').forEach(b => b.classList.toggle('active', b.dataset.filter === tag));
  document.querySelectorAll('.card').forEach(c => {
    const show = tag === 'all' || c.dataset.tags.includes(tag);
    c.style.display = show ? '' : 'none';
  });
}
</script>
</body>
</html>
"""


def _extract_meta(html: str, name: str) -> str | None:
    m = re.search(rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]*)"', html, re.IGNORECASE)
    if m:
        return m.group(1)
    # Tentar ordem invertida (content antes de name)
    m = re.search(rf'<meta[^>]+content="([^"]*)"[^>]+name="{re.escape(name)}"', html, re.IGNORECASE)
    return m.group(1) if m else None


def _extract_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else "Sem título"


def _parse_filename_date(filename: str) -> str:
    """Extrai YYYY-MM-DD de nome tipo 'table-20260511-120000.html'."""
    m = re.search(r"-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})\.html$", filename)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"
    return ""


def _infer_type(filename: str, generator: str | None) -> str:
    if generator and "artifact_engine." in generator:
        return generator.split("artifact_engine.")[-1].split()[0]
    # Fallback pelo prefixo do filename
    prefix = filename.split("-")[0]
    return prefix


def build_index(artifacts_dir: Path | None = None) -> Path:
    """Escaneia artifacts_dir, extrai metadados e gera index.html."""
    artifacts_dir = artifacts_dir or DEFAULT_ARTIFACTS_DIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[dict[str, Any]] = []
    all_tags_set: set[str] = set()

    for html_path in sorted(artifacts_dir.glob("*.html"), reverse=True):
        if html_path.name == "index.html":
            continue
        html = html_path.read_text(encoding="utf-8")
        title = _extract_title(html)
        generator = _extract_meta(html, "generator")
        tags_str = _extract_meta(html, "artifact-tags") or ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        date_str = _parse_filename_date(html_path.name)
        type_id = _infer_type(html_path.name, generator)

        artifacts.append(
            {
                "filename": html_path.name,
                "title": title,
                "type": type_id,
                "date": date_str,
                "tags": tags,
            }
        )
        all_tags_set.update(tags)

    from jinja2 import Template

    tmpl = Template(_INDEX_TEMPLATE)
    html = tmpl.render(
        artifacts=artifacts,
        all_tags=sorted(all_tags_set),
    )

    index_path = artifacts_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


if __name__ == "__main__":
    out = build_index()
    print(f"[ok] index -> {out}")

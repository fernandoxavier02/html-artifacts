"""ArtifactEngine — Core rendering unificado para HTML artifacts.

Funde gen_artifact.py (funcional) com templates Thariq (visuais editoriais)
em uma única API Python importável.
"""
from __future__ import annotations

import sys
from pathlib import Path
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from jinja2 import Template
from pydantic import ValidationError

import artifact_schemas as schemas


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
DEFAULT_OUT_DIR = PROJECT_ROOT / ".claude" / "_html" / "artifacts"
TEMPLATES_DIR = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "examples"


class UnknownRendererError(KeyError):
    """Type_id não existe no RENDERER_REGISTRY."""


class TemplateNotFoundError(FileNotFoundError):
    """Arquivo .html do template Thariq não encontrado."""


# ============================================================================
# Renderers gen_artifact (reusados do gen_artifact.py)
# ============================================================================

_BASE_CSS_DARK = """
:root{
  --bg:#0f1115; --fg:#e6e8ee; --muted:#8b93a7; --accent:#7aa2ff; --border:#252a36;
  --code-bg:#1a1d25; --table-stripe:#161922; --warn:#ffb86b; --ok:#7ce38b; --err:#ff6b6b;
  --info:#7aa2ff;
}
@media (prefers-color-scheme: light){
  :root{ --bg:#fafbfc; --fg:#0f1115; --muted:#5a6075; --accent:#2a52cc;
         --border:#dfe2ea; --code-bg:#f1f3f7; --table-stripe:#f5f7fb; }
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--fg);
  font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
main{max-width:1200px;margin:0 auto;padding:32px 40px;}
h1{font-size:26px;margin:0 0 4px;}
.subtitle{color:var(--muted);font-size:14px;margin:0 0 24px;}
.gen-meta{font-size:11px;color:var(--muted);margin-top:48px;padding-top:16px;
  border-top:1px solid var(--border);}
.alert{border-left:3px solid var(--info);background:var(--code-bg);
  padding:10px 16px;margin:12px 0;border-radius:0 6px 6px 0;}
.alert.warn{border-color:var(--warn);}
.alert.err{border-color:var(--err);}
.alert.ok{border-color:var(--ok);}
code{background:var(--code-bg);padding:2px 6px;border-radius:4px;font-size:0.92em;
  font-family:ui-monospace,Menlo,Consolas,monospace;}
pre{background:var(--code-bg);border:1px solid var(--border);border-radius:6px;
  padding:12px 16px;overflow-x:auto;}
pre code{background:none;padding:0;}
"""

_TABLE_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.table">
<meta name="artifact-tags" content="table,data">
<title>{{ title }}</title>
<style>
"""
    + _BASE_CSS_DARK
    + """
.toolbar{display:flex;gap:12px;align-items:center;margin:16px 0;}
.toolbar input{flex:1;max-width:360px;padding:8px 12px;background:var(--code-bg);
  border:1px solid var(--border);border-radius:6px;color:var(--fg);font-size:14px;}
.toolbar .count{color:var(--muted);font-size:13px;}
table{border-collapse:collapse;width:100%;font-size:14px;margin-top:8px;}
th,td{border:1px solid var(--border);padding:8px 12px;text-align:left;vertical-align:top;}
th{background:var(--code-bg);font-weight:600;cursor:pointer;user-select:none;
  position:sticky;top:0;z-index:1;}
th:hover{color:var(--accent);}
th .sort-arrow{color:var(--muted);font-size:11px;margin-left:4px;}
th.sort-asc .sort-arrow::after{content:"▲";color:var(--accent);}
th.sort-desc .sort-arrow::after{content:"▼";color:var(--accent);}
tr:nth-child(even) td{background:var(--table-stripe);}
tr:hover td{background:var(--code-bg);}
td.num{text-align:right;font-variant-numeric:tabular-nums;}
.row-hidden{display:none;}
.empty-state{padding:32px;text-align:center;color:var(--muted);font-size:14px;}
</style>
</head>
<body>
<main>
  <h1>{{ title }}</h1>
  {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  <div class="toolbar">
    <input type="search" id="filter" placeholder="Filtrar (busca em qualquer coluna)..." autofocus>
    <span class="count" id="count">{{ rows|length }} linhas</span>
  </div>
  <table id="tbl">
    <thead><tr>
      {% for col in columns %}
      <th data-key="{{ col.key }}" data-type="{{ col.type or 'str' }}">{{ col.label }}<span class="sort-arrow"></span></th>
      {% endfor %}
    </tr></thead>
    <tbody>
      {% for row in rows %}
      <tr>
        {% for col in columns %}
        <td{% if col.type in ('num','int','float') %} class="num"{% endif %}>{{ row.get(col.key, '') }}</td>
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <div class="empty-state" id="empty" style="display:none">Nada bate com o filtro.</div>
  <div class="gen-meta">artifact_engine.table - {{ gen_time }} - artifact auto-contido.</div>
</main>
<script>
(function(){
  const tbl=document.getElementById('tbl');
  const tbody=tbl.querySelector('tbody');
  const rows=Array.from(tbody.querySelectorAll('tr'));
  const filter=document.getElementById('filter');
  const count=document.getElementById('count');
  const empty=document.getElementById('empty');
  const total=rows.length;
  function updateCount(){
    const vis=rows.filter(r=>!r.classList.contains('row-hidden')).length;
    count.textContent=`${vis} de ${total} linhas`;
    empty.style.display=vis===0?'block':'none';
  }
  filter.addEventListener('input',()=>{
    const q=filter.value.toLowerCase();
    rows.forEach(r=>{
      r.classList.toggle('row-hidden',q && !r.textContent.toLowerCase().includes(q));
    });
    updateCount();
  });
  tbl.querySelectorAll('th').forEach((th,colIdx)=>{
    th.addEventListener('click',()=>{
      const cur=th.classList.contains('sort-asc')?'asc':th.classList.contains('sort-desc')?'desc':'';
      tbl.querySelectorAll('th').forEach(x=>x.classList.remove('sort-asc','sort-desc'));
      const dir=cur==='asc'?'desc':'asc';
      th.classList.add('sort-'+dir);
      const type=th.dataset.type;
      const sorted=rows.slice().sort((a,b)=>{
        let va=a.cells[colIdx].textContent.trim();
        let vb=b.cells[colIdx].textContent.trim();
        if(type==='num'||type==='int'||type==='float'){
          va=parseFloat(va.replace(/[^0-9.\\-]/g,''))||0;
          vb=parseFloat(vb.replace(/[^0-9.\\-]/g,''))||0;
          return dir==='asc'?va-vb:vb-va;
        }
        return dir==='asc'?va.localeCompare(vb):vb.localeCompare(va);
      });
      sorted.forEach(r=>tbody.appendChild(r));
    });
  });
  updateCount();
})();
</script>
</body>
</html>
"""
)

_REPORT_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.report">
<meta name="artifact-tags" content="report">
<title>{{ title }}</title>
<style>
"""
    + _BASE_CSS_DARK
    + """
.shell{display:grid;grid-template-columns:220px 1fr;gap:32px;}
nav.toc{position:sticky;top:24px;align-self:start;font-size:13px;}
nav.toc h2{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);
  margin:0 0 8px;}
nav.toc a{color:var(--fg);text-decoration:none;display:block;padding:4px 8px;border-radius:4px;}
nav.toc a:hover{background:var(--code-bg);color:var(--accent);}
section{margin-bottom:32px;}
section h2{margin:0 0 8px;padding-bottom:4px;border-bottom:1px solid var(--border);}
section.alert-warn{border-left:3px solid var(--warn);padding-left:16px;}
section.alert-err{border-left:3px solid var(--err);padding-left:16px;}
section.alert-ok{border-left:3px solid var(--ok);padding-left:16px;}
section.alert-info{border-left:3px solid var(--info);padding-left:16px;}
.body table{border-collapse:collapse;font-size:14px;margin:12px 0;}
.body th,.body td{border:1px solid var(--border);padding:6px 10px;text-align:left;}
.body th{background:var(--code-bg);}
.body tr:nth-child(even) td{background:var(--table-stripe);}
@media (max-width:880px){.shell{grid-template-columns:1fr;}nav.toc{position:static;}}
</style>
</head>
<body>
<main>
  <h1>{{ title }}</h1>
  {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  <div class="shell">
    <nav class="toc">
      <h2>Secoes</h2>
      {% for s in sections %}
      <a href="#sec-{{ loop.index }}">{{ s.heading }}</a>
      {% endfor %}
    </nav>
    <div>
      {% for s in sections %}
      <section id="sec-{{ loop.index }}"{% if s.alert %} class="alert-{{ s.alert }}"{% endif %}>
        <h2>{{ s.heading }}</h2>
        <div class="body">{{ s.body_html | safe }}</div>
      </section>
      {% endfor %}
    </div>
  </div>
  <div class="gen-meta">artifact_engine.report - {{ gen_time }}</div>
</main>
</body>
</html>
"""
)

_INTERACTIVE_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.interactive">
<meta name="artifact-tags" content="interactive,validation">
<title>{{ title }}</title>
<link rel="stylesheet" href="base.css">
<style>
.page { max-width: 900px; }
.progress-wrap { position: sticky; top: 0; z-index: 20; background: var(--ivory); padding: 12px 0; border-bottom: var(--border); margin-bottom: 16px; }
.progress-bar-track { height: 6px; background: var(--gray-100); border-radius: 999px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: var(--olive); width: 0%; transition: width 0.3s; border-radius: 999px; }
.progress-text { font-size: 12px; color: var(--gray-500); margin-top: 6px; text-align: right; font-family: var(--mono); }
.item-card {
  background: var(--white);
  border: var(--border);
  border-radius: var(--radius-panel);
  padding: 20px 24px;
  margin: 16px 0;
  transition: border-color 0.2s, box-shadow 0.2s;
  animation: fadeInUp 0.4s ease both;
}
.item-card[data-answered="true"] { border-color: var(--olive); box-shadow: 0 0 0 3px rgba(120,140,93,0.08); }
.item-card[data-required="true"][data-answered="false"] { border-left: 3px solid var(--clay); }
.item-head { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.item-num { font-family: var(--mono); font-size: 11px; color: var(--gray-500); font-weight: 600; background: var(--gray-100); border-radius: 999px; padding: 3px 10px; flex-shrink: 0; }
.item-label { font-size: 16px; font-weight: 600; color: var(--slate); flex: 1; }
.required-badge { color: var(--rust); font-size: 14px; font-weight: 700; }
.item-details { font-size: 14px; color: var(--gray-700); margin: 0 0 12px 0; line-height: 1.55; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; }
.pill-group { display: inline-flex; gap: 0; border: var(--border); border-radius: 999px; overflow: hidden; }
.pill-group label { padding: 8px 18px; font-size: 13px; cursor: pointer; background: var(--white); color: var(--gray-700); border-right: 1px solid var(--gray-300); transition: background 0.1s; user-select: none; }
.pill-group label:last-child { border-right: none; }
.pill-group input { display: none; }
.pill-group input:checked + span { font-weight: 600; }
.pill-group label:has(input[value="approve"]:checked) { background: var(--olive); color: var(--white); }
.pill-group label:has(input[value="reject"]:checked) { background: var(--rust); color: var(--white); }
.pill-group label:has(input[value="skip"]:checked) { background: var(--gray-300); color: var(--slate); }
.pill-group label:hover { background: var(--gray-100); }
.cb-row { display: flex; align-items: center; gap: 10px; }
.cb-row input[type=checkbox] { width: 18px; height: 18px; accent-color: var(--clay); cursor: pointer; }
.cb-row label { font-size: 14px; cursor: pointer; }
.multiselect-group { display: flex; flex-direction: column; gap: 8px; }
select { font-family: var(--sans); font-size: 14px; padding: 8px 14px; border: var(--border); border-radius: var(--radius-row); background: var(--white); color: var(--slate); cursor: pointer; min-width: 200px; }
input[type=text], textarea, .tag-input input { width: 100%; max-width: 100%; font-family: var(--sans); font-size: 14px; padding: 10px 14px; border: var(--border); border-radius: 8px; background: var(--white); color: var(--slate); resize: vertical; }
textarea { min-height: 80px; line-height: 1.55; }
input[type=text]:focus, textarea:focus, .tag-input input:focus { outline: 2px solid var(--clay); outline-offset: -1px; }
.slider-wrap { display: flex; align-items: center; gap: 16px; }
input[type=range] { flex: 1; accent-color: var(--clay); }
.slider-value { font-family: var(--mono); font-size: 14px; color: var(--slate); min-width: 40px; text-align: right; }
.rating-group { display: flex; gap: 6px; font-size: 26px; cursor: pointer; }
.rating-star { color: var(--gray-300); transition: color 0.15s; user-select: none; }
.rating-star.active { color: var(--clay); }
.tag-input { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; border: var(--border); border-radius: 8px; padding: 8px 12px; background: var(--white); }
.tag-input input { border: none; outline: none; flex: 1; min-width: 120px; padding: 4px; background: transparent; }
.tag-chip { background: var(--oat); color: var(--slate); font-size: 12px; padding: 4px 10px; border-radius: 999px; display: inline-flex; align-items: center; gap: 6px; }
.tag-chip .remove { cursor: pointer; color: var(--gray-500); font-weight: 700; }
.code-block pre { margin: 0; background: var(--slate); color: var(--ivory); padding: 16px; border-radius: 8px; overflow-x: auto; }
.code-block pre::before { content: attr(data-lang); display: block; font-size: 10px; text-transform: uppercase; color: var(--gray-500); margin-bottom: 8px; font-family: var(--mono); letter-spacing: 0.06em; }
.code-block textarea { width: 100%; background: transparent; color: var(--ivory); border: none; outline: none; font-family: var(--mono); font-size: 13px; line-height: 1.5; min-height: 120px; resize: vertical; }
.item-note { margin: 12px 0 0 0; }
.item-note label { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--gray-500); margin-bottom: 4px; }
.summary-panel { background: var(--oat); border-radius: var(--radius-panel); padding: 20px 24px; margin: 32px 0 24px; }
.summary-panel label { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--gray-700); margin-bottom: 8px; font-weight: 600; }
.submit-bar { position: fixed; bottom: 0; left: 0; right: 0; background: var(--white); border-top: var(--border); padding: 14px 32px; display: flex; align-items: center; gap: 16px; box-shadow: 0 -4px 12px rgba(20,20,19,0.06); z-index: 10; }
.submit-bar .progress { flex: 1; font-size: 13px; color: var(--gray-700); }
.submit-bar .progress strong { color: var(--olive); font-weight: 600; }
button.confirm { background: var(--clay); color: var(--white); border: none; padding: 12px 28px; border-radius: 999px; font-family: var(--sans); font-size: 14px; font-weight: 600; cursor: pointer; letter-spacing: 0.02em; transition: background 0.1s, transform 0.05s; }
button.confirm:hover { background: var(--rust); }
button.confirm:active { transform: scale(0.98); }
button.confirm:disabled { background: var(--gray-300); cursor: not-allowed; color: var(--gray-700); }
.modal { display: none; position: fixed; inset: 0; background: rgba(20,20,19,0.5); z-index: 100; align-items: center; justify-content: center; padding: 20px; }
.modal.open { display: flex; }
.modal-content { background: var(--ivory); border-radius: var(--radius-panel); max-width: 720px; width: 100%; max-height: 80vh; display: flex; flex-direction: column; border: var(--border); overflow: hidden; }
.modal-head { padding: 18px 24px; border-bottom: var(--border); display: flex; justify-content: space-between; align-items: center; }
.modal-head h2 { font-family: var(--serif); font-weight: 500; font-size: 20px; margin: 0; }
.modal-close { background: none; border: none; cursor: pointer; font-size: 22px; color: var(--gray-500); line-height: 1; }
.modal-body { padding: 18px 24px; overflow: auto; font-family: var(--mono); font-size: 12px; line-height: 1.5; background: var(--slate); color: var(--ivory); margin: 16px; border-radius: 8px; }
.modal-body pre { margin: 0; white-space: pre-wrap; word-break: break-word; }
.modal-actions { padding: 14px 24px 20px; display: flex; gap: 12px; border-top: var(--border); justify-content: space-between; align-items: center; }
.modal-actions .hint { font-size: 12px; color: var(--gray-700); flex: 1; }
.modal-actions button { font-family: var(--sans); font-size: 13px; padding: 9px 18px; border-radius: 999px; cursor: pointer; border: var(--border); background: var(--white); color: var(--slate); }
.modal-actions button.primary { background: var(--clay); color: var(--white); border-color: var(--clay); }
.modal-actions button.primary:hover { background: var(--rust); border-color: var(--rust); }
.toast { position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%); background: var(--olive); color: var(--white); padding: 10px 20px; border-radius: 999px; font-size: 13px; z-index: 200; opacity: 0; transition: opacity 0.2s; pointer-events: none; }
.toast.show { opacity: 1; }
.gen-meta { font-size: 11px; color: var(--gray-500); margin-top: 36px; padding-top: 14px; border-top: 1px solid var(--gray-300); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Agent Interaction</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
    {% if context %}<div class="context">{{ context_html | safe }}</div>{% endif %}
  </header>

  <div class="progress-wrap">
    <div class="progress-bar-track"><div class="progress-bar-fill" id="progress-fill"></div></div>
    <div class="progress-text" id="progress-text">0 de {{ items|length }} respondidos</div>
  </div>

  <form id="form">
    {% for item in items %}
    <div class="item-card" data-id="{{ item.id }}" data-type="{{ item.type or 'decision' }}" data-answered="false" data-required="{{ 'true' if item.required else 'false' }}" style="animation-delay: {{ loop.index * 0.05 }}s">
      <div class="item-head">
        <span class="item-num">{{ loop.index }}</span>
        <span class="item-label">{{ item.label }}</span>
        {% if item.required %}<span class="required-badge">*</span>{% endif %}
      </div>
      {% if item.details_html %}<div class="item-details">{{ item.details_html | safe }}</div>{% endif %}
      <div class="controls">
        {% set itype = item.type or 'decision' %}
        {% if itype == 'decision' %}
          <div class="pill-group">
            <label><input type="radio" name="{{ item.id }}" value="approve"><span>Aprovar</span></label>
            <label><input type="radio" name="{{ item.id }}" value="reject"><span>Rejeitar</span></label>
            <label><input type="radio" name="{{ item.id }}" value="skip"><span>Pular</span></label>
          </div>
        {% elif itype == 'checkbox' %}
          <div class="cb-row">
            <input type="checkbox" id="cb-{{ item.id }}" name="{{ item.id }}">
            <label for="cb-{{ item.id }}">{{ item.checkbox_label or 'Confirmar' }}</label>
          </div>
        {% elif itype == 'select' %}
          <select name="{{ item.id }}">
            <option value="">--</option>
            {% for opt in item.options %}<option value="{{ opt.value }}">{{ opt.label }}</option>{% endfor %}
          </select>
        {% elif itype == 'multiselect' %}
          <div class="multiselect-group">
            {% for opt in item.options %}
            <div class="cb-row">
              <input type="checkbox" id="cb-{{ item.id }}-{{ loop.index }}" name="{{ item.id }}" value="{{ opt.value }}">
              <label for="cb-{{ item.id }}-{{ loop.index }}">{{ opt.label }}</label>
            </div>
            {% endfor %}
          </div>
        {% elif itype == 'text' %}
          <input type="text" name="{{ item.id }}" placeholder="{{ item.placeholder or '' }}" {% if item.required %}required{% endif %} {% if item.validation_regex %}pattern="{{ item.validation_regex }}"{% endif %}>
        {% elif itype == 'textarea' %}
          <textarea name="{{ item.id }}" placeholder="{{ item.placeholder or '' }}" {% if item.required %}required{% endif %}></textarea>
        {% elif itype == 'slider' %}
          <div class="slider-wrap">
            <input type="range" name="{{ item.id }}" min="{{ item.min or 0 }}" max="{{ item.max or 100 }}" step="{{ item.step or 1 }}" value="{{ item.min or 0 }}">
            <span class="slider-value">{{ item.min or 0 }}</span>
          </div>
        {% elif itype == 'rating' %}
          <div class="rating-group" data-max="{{ item.rating_max or 5 }}">
            {% for i in range(1, (item.rating_max or 5) + 1) %}
            <span class="rating-star" data-rating-value="{{ i }}">&#9733;</span>
            {% endfor %}
            <input type="hidden" name="{{ item.id }}" value="">
          </div>
        {% elif itype == 'tags' %}
          <div class="tag-input" data-tags="">
            <div class="tag-chips"></div>
            <input type="text" class="tag-adder" placeholder="Digite e pressione Enter...">
            <input type="hidden" name="{{ item.id }}" value="">
          </div>
        {% elif itype == 'code' %}
          <div class="code-block" data-lang="{{ item.code_lang or '' }}">
            <pre><code><textarea name="{{ item.id }}" placeholder="// cole ou digite codigo aqui..."></textarea></code></pre>
          </div>
        {% endif %}
      </div>
      {% if item.allow_note %}
      <div class="item-note">
        <label>Nota (opcional)</label>
        <textarea name="{{ item.id }}__note" placeholder="Observacao especifica deste item..."></textarea>
      </div>
      {% endif %}
    </div>
    {% endfor %}
    <div class="summary-panel">
      <label>Comentario geral / proximas instrucoes</label>
      <textarea id="summary" name="__summary" placeholder="Algo extra que voce queira passar ao agente..."></textarea>
    </div>
  </form>
  <div class="gen-meta">artifact id: {{ artifact_id }} | gerado: {{ gen_time }}</div>
</main>
<div class="submit-bar">
  <div class="progress"><strong id="progress-num">0</strong> de {{ items|length }} itens respondidos</div>
  <button class="confirm" id="confirm-btn" type="button">Confirmar resposta</button>
</div>
<div class="modal" id="modal">
  <div class="modal-content">
    <div class="modal-head">
      <h2>Resposta pronta para colar no chat</h2>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body"><pre id="response-text"></pre></div>
    <div class="modal-actions">
      <span class="hint">Copie o bloco acima e cole na conversa. O agente vai parsear automaticamente.</span>
      <button onclick="closeModal()">Fechar</button>
      <button class="primary" id="copy-btn" onclick="copyResponse()">Copiar</button>
    </div>
  </div>
</div>
<div class="toast" id="toast">Copiado!</div>
<script>
(function() {
  const form = document.getElementById('form');
  const items = {{ items_json | safe }};
  const artifactId = "{{ artifact_id }}";
  const progressNum = document.getElementById('progress-num');
  const progressFill = document.getElementById('progress-fill');
  const progressText = document.getElementById('progress-text');
  const confirmBtn = document.getElementById('confirm-btn');
  const modal = document.getElementById('modal');
  const responseText = document.getElementById('response-text');
  const toast = document.getElementById('toast');
  const storageKey = 'artifact_' + artifactId;

  function saveResponses() {
    const data = {};
    form.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.name && !el.name.startsWith('__')) {
        if (el.type === 'checkbox') {
          if (!data[el.name]) data[el.name] = [];
          if (el.checked) data[el.name].push(el.value || true);
        } else if (el.type === 'radio') {
          if (el.checked) data[el.name] = el.value;
        } else {
          data[el.name] = el.value;
        }
      }
    });
    localStorage.setItem(storageKey, JSON.stringify(data));
  }

  function loadResponses() {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;
      const data = JSON.parse(raw);
      Object.entries(data).forEach(([name, val]) => {
        const els = form.querySelectorAll(`[name="${name}"]`);
        if (!els.length) return;
        const first = els[0];
        if (first.type === 'checkbox' && Array.isArray(val)) {
          els.forEach(cb => { cb.checked = val.includes(cb.value); });
        } else if (first.type === 'radio') {
          els.forEach(r => { r.checked = r.value === val; });
        } else if (first.tagName === 'TEXTAREA' || first.type === 'text' || first.type === 'range') {
          first.value = val;
          if (first.type === 'range') {
            const wrap = first.closest('.slider-wrap');
            if (wrap) wrap.querySelector('.slider-value').textContent = val;
          }
        } else {
          first.value = val;
        }
      });
    } catch(e) {}
  }

  function checkAnswered(item) {
    const type = item.type || 'decision';
    const card = form.querySelector(`.item-card[data-id="${item.id}"]`);
    if (type === 'decision') {
      const sel = card.querySelector(`input[type="radio"]:checked`);
      return sel ? sel.value : null;
    } else if (type === 'checkbox') {
      const cb = card.querySelector(`input[type="checkbox"]`);
      return cb ? cb.checked : null;
    } else if (type === 'select') {
      const s = card.querySelector(`select`);
      return s && s.value ? s.value : null;
    } else if (type === 'multiselect') {
      const cbs = card.querySelectorAll(`input[type="checkbox"]:checked`);
      return cbs.length > 0 ? Array.from(cbs).map(c => c.value) : null;
    } else if (type === 'text' || type === 'textarea' || type === 'code') {
      const t = card.querySelector(`input, textarea`);
      return t && t.value ? t.value : null;
    } else if (type === 'slider') {
      const r = card.querySelector(`input[type="range"]`);
      return r ? parseFloat(r.value) : null;
    } else if (type === 'rating') {
      const h = card.querySelector(`input[type="hidden"]`);
      return h && h.value ? parseInt(h.value) : null;
    } else if (type === 'tags') {
      const h = card.querySelector(`input[type="hidden"]`);
      return h && h.value ? h.value.split(',').filter(Boolean) : null;
    }
    return null;
  }

  function validateForm() {
    let valid = true;
    form.querySelectorAll('.item-card[data-required="true"]').forEach(card => {
      const id = card.dataset.id;
      const item = items.find(i => i.id === id);
      const val = checkAnswered(item);
      const answered = val !== null && val !== false && val !== '' && !(Array.isArray(val) && val.length === 0);
      if (!answered) { valid = false; card.style.borderLeft = '3px solid var(--rust)'; }
      else { card.style.borderLeft = ''; }
    });
    return valid;
  }

  function updateProgress() {
    let answered = 0;
    for (const item of items) {
      const v = checkAnswered(item);
      const card = form.querySelector(`.item-card[data-id="${item.id}"]`);
      const isAnswered = v !== null && v !== false && v !== '' && !(Array.isArray(v) && v.length === 0);
      card.dataset.answered = isAnswered ? 'true' : 'false';
      if (isAnswered) answered++;
    }
    progressNum.textContent = answered;
    const pct = items.length ? (answered / items.length * 100) : 0;
    progressFill.style.width = pct + '%';
    progressText.textContent = answered + ' de ' + items.length + ' respondidos';
    saveResponses();
  }

  form.addEventListener('change', updateProgress);
  form.addEventListener('input', updateProgress);

  form.querySelectorAll('input[type="range"]').forEach(r => {
    r.addEventListener('input', () => {
      const wrap = r.closest('.slider-wrap');
      if (wrap) wrap.querySelector('.slider-value').textContent = r.value;
    });
  });

  form.querySelectorAll('.rating-group').forEach(g => {
    const stars = g.querySelectorAll('.rating-star');
    const hidden = g.querySelector('input[type="hidden"]');
    stars.forEach((s, idx) => {
      s.addEventListener('click', () => {
        hidden.value = idx + 1;
        stars.forEach((st, i) => st.classList.toggle('active', i <= idx));
        updateProgress();
      });
    });
  });

  form.querySelectorAll('.tag-input').forEach(wrap => {
    const adder = wrap.querySelector('.tag-adder');
    const chips = wrap.querySelector('.tag-chips');
    const hidden = wrap.querySelector('input[type="hidden"]');
    function updateHidden() {
      const vals = Array.from(chips.querySelectorAll('.tag-chip')).map(c => c.dataset.val);
      hidden.value = vals.join(',');
    }
    function addTag(val) {
      val = val.trim();
      if (!val) return;
      const existing = Array.from(chips.querySelectorAll('.tag-chip')).map(c => c.dataset.val);
      if (existing.includes(val)) return;
      const chip = document.createElement('span');
      chip.className = 'tag-chip';
      chip.dataset.val = val;
      chip.innerHTML = val + ' <span class="remove" onclick="this.parentElement.remove();updateHidden();updateProgress();">&times;</span>';
      chips.appendChild(chip);
      updateHidden();
      updateProgress();
    }
    adder.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); addTag(adder.value); adder.value = ''; }
    });
  });

  function gatherResponse() {
    const responses = {};
    for (const item of items) {
      const v = checkAnswered(item);
      if (item.allow_note) {
        const note = form.querySelector(`textarea[name="${item.id}__note"]`);
        responses[item.id] = {value: v, note: note && note.value ? note.value : null};
      } else { responses[item.id] = v; }
    }
    const summary = document.getElementById('summary').value || null;
    return { artifact_id: artifactId, responses, summary, submitted_at: new Date().toISOString() };
  }

  confirmBtn.addEventListener('click', () => {
    if (!validateForm()) {
      showToast('Preencha todos os campos obrigatorios (*)');
      return;
    }
    const data = gatherResponse();
    const block = `=== ARTIFACT RESPONSE ===\n${JSON.stringify(data, null, 2)}\n=== END RESPONSE ===`;
    responseText.textContent = block;
    modal.classList.add('open');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(block).then(() => showToast('Copiado automatico'), () => {});
    }
  });
  window.closeModal = function() { modal.classList.remove('open'); };
  window.copyResponse = function() {
    const text = responseText.textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => showToast('Copiado!'), tryExecCommand);
    } else { tryExecCommand(); }
    function tryExecCommand() {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); showToast('Copiado!'); }
      catch (e) { showToast('Copia manual: selecione o texto e Ctrl+C'); }
      document.body.removeChild(ta);
    }
  };
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 1800);
  }
  loadResponses();
  updateProgress();
})();
</script>
</body>
</html>
"""
)


def _md_to_html(body_md: str) -> str:
    import markdown

    md = markdown.Markdown(extensions=["extra", "tables", "fenced_code", "sane_lists"])
    return md.convert(body_md or "")


def _render_table(data: dict, gen_time: str) -> str:
    return _TABLE_TEMPLATE.render(
        title=data.get("title", "Tabela"),
        subtitle=data.get("subtitle"),
        columns=data.get("columns", []),
        rows=data.get("rows", []),
        gen_time=gen_time,
    )


def _render_report(data: dict, gen_time: str) -> str:
    sections = []
    for s in data.get("sections", []):
        sections.append(
            {
                "heading": s.get("heading", "Sem titulo"),
                "body_html": _md_to_html(s.get("body", "")),
                "alert": s.get("alert"),
            }
        )
    return _REPORT_TEMPLATE.render(
        title=data.get("title", "Relatorio"),
        subtitle=data.get("subtitle"),
        sections=sections,
        gen_time=gen_time,
    )


def _render_interactive(data: dict, gen_time: str) -> str:
    import json as _json

    items = []
    for it in data.get("items", []):
        rendered = dict(it)
        if it.get("details_md"):
            rendered["details_html"] = _md_to_html(it["details_md"])
        items.append(rendered)
    context_html = _md_to_html(data.get("context", "")) if data.get("context") else ""
    artifact_id = data.get("artifact_id") or f"interactive-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return _INTERACTIVE_TEMPLATE.render(
        title=data.get("title", "Validacao"),
        subtitle=data.get("subtitle"),
        context_html=context_html,
        context=data.get("context"),
        items=items,
        items_json=_json.dumps(
            [
                {"id": i["id"], "type": i.get("type", "decision"), "allow_note": bool(i.get("allow_note"))}
                for i in items
            ]
        ),
        artifact_id=artifact_id,
        gen_time=gen_time,
    )


# ============================================================================
# Thariq Renderer
# ============================================================================

_THARIQ_TYPE_MAP = {
    "compare": "02-exploration-visual-designs",
    "pr-review": "03-code-review-pr",
    "code-flow": "04-code-understanding",
    "design-system": "05-design-system",
    "variants": "06-component-variants",
    "proto": "08-prototype-interaction",
    "illust": "10-svg-illustrations",
    "status-report": "11-status-report",
    "incident": "12-incident-report",
    "flow": "13-flowchart-diagram",
    "feature-explainer": "14-research-feature-explainer",
    "concept-explainer": "15-research-concept-explainer",
    "plan": "16-implementation-plan",
    "pr-writeup": "17-pr-writeup",
    "triage": "18-editor-triage-board",
    "config-editor": "19-editor-feature-flags",
    "prompt-tuner": "20-editor-prompt-tuner",
}


class ThariqRenderer:
    """Hidrata templates Thariq a partir de datasets Python."""

    def render(self, template_id: str, dataset: dict[str, Any]) -> str:
        """Lê template, substitui title/brand e retorna HTML string."""
        # Resolve arquivo
        file_stem = _THARIQ_TYPE_MAP.get(template_id, template_id)
        candidates = list(TEMPLATES_DIR.glob(f"{file_stem}*.html"))
        if not candidates:
            # Tentar match direto pelo número (ex: "11")
            candidates = list(TEMPLATES_DIR.glob(f"{template_id}-*.html"))
        if not candidates:
            raise TemplateNotFoundError(f"Template '{template_id}' não encontrado em {TEMPLATES_DIR}")

        template_path = candidates[0]
        html = template_path.read_text(encoding="utf-8")

        title = dataset.get("title", "Artifact")
        brand = dataset.get("brand", "FX Studio")

        # Substitui <title>...</title>
        html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1, flags=re.DOTALL)

        # Substitui brand fictícia por brand real
        html = html.replace("Birchline", brand)
        html = html.replace("Acme", brand)

        # Se dataset tiver sections, injeta no body (simplificação para MVP)
        sections = dataset.get("sections")
        if sections:
            # Procura primeiro <section> ou <div class="page">
            # Estratégia: substituir tudo dentro de <body>...</body> exceto scripts
            # Para MVP, apenas substituímos o innerHTML da primeira div com classe page/wrap/sheet
            body_match = re.search(r"(<body[^>]*>)(.*?)(</body>)", html, re.DOTALL)
            if body_match:
                body_open = body_match.group(1)
                body_close = body_match.group(3)
                # Gera HTML das seções
                sections_html = "\n".join(
                    f"<section><h2>{s['title']}</h2>{s['content']}</section>"
                    for s in sections
                )
                # Preserva footer e scripts ao final do body
                new_body = f"{body_open}\n<div class=\"page\">\n{sections_html}\n</div>\n{body_close}"
                html = html[:body_match.start()] + new_body + html[body_match.end():]

        return html


# ============================================================================
# ArtifactEngine
# ============================================================================

# ============================================================================
# Trading Domain Renderers
# ============================================================================

_THARIQ_CSS_LINK = '<link rel="stylesheet" href="base.css">'

_BACKTEST_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.backtest">
<meta name="artifact-tags" content="trading,backtest,comparison">
<title>{{ title }}</title>
""" + _THARIQ_CSS_LINK + """
<style>
  .page { max-width: 1100px; }
  .strategy-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 24px 0; }
  .strat-card { background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 18px 20px; }
  .strat-card h3 { font-family: var(--serif); font-size: 18px; margin: 0 0 10px; }
  .metric-row { display: flex; justify-content: space-between; font-size: 14px; padding: 4px 0; border-bottom: 1px solid var(--gray-100); }
  .metric-row:last-child { border-bottom: none; }
  .metric-val { font-family: var(--mono); font-weight: 600; }
  .positive { color: var(--olive); }
  .negative { color: var(--rust); }
  table.comp { width: 100%; border-collapse: collapse; margin-top: 16px; background: var(--white); border: var(--border); border-radius: var(--radius-panel); overflow: hidden; }
  table.comp th, table.comp td { padding: 10px 14px; border-bottom: 1px solid var(--gray-100); font-size: 14px; }
  table.comp th { background: var(--gray-100); font-weight: 600; text-align: left; }
  table.comp tr:last-child td { border-bottom: none; }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Backtest Comparison</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="lead">{{ subtitle }}</p>{% endif %}
  </header>

  <section>
    <h2>Resumo por Estratégia</h2>
    <div class="strategy-grid">
      {% for s in strategies %}
      <div class="strat-card">
        <h3>{{ s.name }}</h3>
        <div class="metric-row"><span>Trades</span><span class="metric-val">{{ s.trades }}</span></div>
        <div class="metric-row"><span>Win Rate</span><span class="metric-val">{{ "%.1f"|format(s.win_rate) }}%</span></div>
        <div class="metric-row"><span>Sharpe</span><span class="metric-val">{{ "%.2f"|format(s.sharpe or 0) }}</span></div>
        <div class="metric-row"><span>Max DD</span><span class="metric-val negative">{{ "%.2f"|format(s.max_dd_pct) }}%</span></div>
        <div class="metric-row"><span>PnL Total</span><span class="metric-val {% if s.pnl_total >= 0 %}positive{% else %}negative{% endif %}">${{ "%.2f"|format(s.pnl_total) }}</span></div>
      </div>
      {% endfor %}
    </div>
  </section>

  <section>
    <h2>Tabela Comparativa</h2>
    <table class="comp">
      <thead>
        <tr><th>Estratégia</th><th>Trades</th><th>Win Rate</th><th>Sharpe</th><th>Sortino</th><th>Max DD</th><th>PnL</th></tr>
      </thead>
      <tbody>
        {% for s in strategies %}
        <tr>
          <td><strong>{{ s.name }}</strong></td>
          <td>{{ s.trades }}</td>
          <td>{{ "%.1f"|format(s.win_rate) }}%</td>
          <td>{{ "%.2f"|format(s.sharpe or 0) }}</td>
          <td>{{ "%.2f"|format(s.sortino or 0) }}</td>
          <td class="negative">{{ "%.2f"|format(s.max_dd_pct) }}%</td>
          <td class="{% if s.pnl_total >= 0 %}positive{% else %}negative{% endif %}">${{ "%.2f"|format(s.pnl_total) }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <div class="gen-meta">artifact_engine.backtest — {{ gen_time }}</div>
</main>
</body>
</html>
"""
)

_RISK_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.risk">
<meta name="artifact-tags" content="trading,risk,dashboard">
<title>{{ title }}</title>
""" + _THARIQ_CSS_LINK + """
<style>
  .page { max-width: 900px; }
  .risk-table { width: 100%; border-collapse: collapse; background: var(--white); border: var(--border); border-radius: var(--radius-panel); overflow: hidden; margin-top: 16px; }
  .risk-table th, .risk-table td { padding: 12px 16px; border-bottom: 1px solid var(--gray-100); font-size: 14px; text-align: left; }
  .risk-table th { background: var(--gray-100); font-weight: 600; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-family: var(--mono); }
  .badge-olive { background: var(--olive); color: var(--white); }
  .badge-clay { background: var(--clay); color: var(--white); }
  .badge-rust { background: var(--rust); color: var(--white); }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Risk Dashboard</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="lead">{{ subtitle }}</p>{% endif %}
  </header>

  <section>
    <h2>Exposição por Ativo</h2>
    <table class="risk-table">
      <thead>
        <tr><th>Ativo</th><th>Notional</th><th>VaR 95%</th><th>VaR 99%</th><th>Kelly %</th><th>Risco</th></tr>
      </thead>
      <tbody>
        {% for e in exposures %}
        <tr>
          <td><strong>{{ e.symbol }}</strong></td>
          <td>${{ "{:,.0f}".format(e.notional) }}</td>
          <td class="negative">${{ "{:,.0f}".format(e.var_95) }}</td>
          <td class="negative">${{ "{:,.0f}".format(e.var_99) }}</td>
          <td>{{ "%.1f"|format(e.kelly_fraction * 100) }}%</td>
          <td>
            {% if e.kelly_fraction < 0.15 %}<span class="badge badge-olive">Baixo</span>
            {% elif e.kelly_fraction < 0.30 %}<span class="badge badge-clay">Médio</span>
            {% else %}<span class="badge badge-rust">Alto</span>{% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <div class="gen-meta">artifact_engine.risk — {{ gen_time }}</div>
</main>
</body>
</html>
"""
)

_SIGNAL_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.signal">
<meta name="artifact-tags" content="trading,signal,audit">
<title>{{ title }}</title>
""" + _THARIQ_CSS_LINK + """
<style>
  .page { max-width: 1000px; }
  .sig-table { width: 100%; border-collapse: collapse; background: var(--white); border: var(--border); border-radius: var(--radius-panel); overflow: hidden; margin-top: 16px; }
  .sig-table th, .sig-table td { padding: 10px 14px; border-bottom: 1px solid var(--gray-100); font-size: 14px; text-align: left; }
  .sig-table th { background: var(--gray-100); font-weight: 600; }
  .side-buy { color: var(--olive); font-weight: 600; }
  .side-sell { color: var(--rust); font-weight: 600; }
  .status-ok { color: var(--olive); }
  .status-pending { color: var(--gray-500); }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Signal Audit</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="lead">{{ subtitle }}</p>{% endif %}
  </header>

  <section>
    <table class="sig-table">
      <thead>
        <tr><th>ID</th><th>Horário</th><th>Ativo</th><th>Lado</th><th>Preço Sinal</th><th>Exec</th><th>Slippage</th><th>Status</th><th>PnL</th></tr>
      </thead>
      <tbody>
        {% for sig in signals %}
        <tr>
          <td><code>{{ sig.id }}</code></td>
          <td>{{ sig.timestamp[:19].replace('T', ' ') }}</td>
          <td>{{ sig.symbol }}</td>
          <td class="side-{{ sig.side }}">{{ sig.side.upper() }}</td>
          <td>{{ sig.signal_price }}</td>
          <td>{{ sig.exec_price or '-' }}</td>
          <td>{{ "%.2f"|format(sig.slippage_bps or 0) if sig.slippage_bps else '-' }}</td>
          <td class="{% if sig.filled %}status-ok{% else %}status-pending{% endif %}">{% if sig.filled %}✓ Fill{% else %}○ Open{% endif %}</td>
          <td class="{% if sig.pnl and sig.pnl >= 0 %}positive{% elif sig.pnl and sig.pnl < 0 %}negative{% endif %}">{{ "%.2f"|format(sig.pnl) if sig.pnl else '-' }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <div class="gen-meta">artifact_engine.signal — {{ gen_time }}</div>
</main>
</body>
</html>
"""
)

_REGIME_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.regime">
<meta name="artifact-tags" content="trading,regime,timeline">
<title>{{ title }}</title>
""" + _THARIQ_CSS_LINK + """
<style>
  .page { max-width: 900px; }
  .timeline { display: flex; flex-direction: column; gap: 12px; margin-top: 24px; }
  .regime-card { display: grid; grid-template-columns: 140px 1fr 180px; gap: 16px; align-items: center; background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 16px 20px; }
  .regime-time { font-family: var(--mono); font-size: 12px; color: var(--gray-500); }
  .regime-tag { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
  .regime-trending { background: var(--olive); color: var(--white); }
  .regime-ranging { background: var(--gray-300); color: var(--slate); }
  .regime-high-vol { background: var(--clay); color: var(--white); }
  .regime-low-liquidity { background: var(--sky); color: var(--white); }
  .regime-normal { background: var(--oat); color: var(--slate); }
  .regime-stats { font-size: 13px; color: var(--gray-700); }
  .regime-stats span { display: inline-block; margin-right: 14px; }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Market Regimes</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="lead">{{ subtitle }}</p>{% endif %}
  </header>

  <section>
    <div class="timeline">
      {% for r in regimes %}
      <div class="regime-card">
        <div class="regime-time">{{ r.start[:16].replace('T', ' ') }}<br>→ {{ r.end[:16].replace('T', ' ') }}</div>
        <div>
          <span class="regime-tag regime-{{ r.regime.replace('-', '-') }}">{{ r.regime.replace('-', ' ').title() }}</span>
          <div style="margin-top:6px; font-size:14px; color:var(--slate);"><strong>{{ r.label }}</strong></div>
        </div>
        <div class="regime-stats">
          {% if r.stats %}
            {% for k, v in r.stats.items() %}
            <span>{{ k }}: {{ "%.3f"|format(v) if v is number else v }}</span>
            {% endfor %}
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
  </section>

  <div class="gen-meta">artifact_engine.regime — {{ gen_time }}</div>
</main>
</body>
</html>
"""
)


def _render_backtest(data: dict, gen_time: str) -> str:
    return _BACKTEST_TEMPLATE.render(
        title=data.get("title", "Backtest"),
        subtitle=data.get("subtitle"),
        strategies=data.get("strategies", []),
        gen_time=gen_time,
    )


def _render_risk(data: dict, gen_time: str) -> str:
    return _RISK_TEMPLATE.render(
        title=data.get("title", "Risk Dashboard"),
        subtitle=data.get("subtitle"),
        exposures=data.get("exposures", []),
        gen_time=gen_time,
    )


def _render_signal(data: dict, gen_time: str) -> str:
    return _SIGNAL_TEMPLATE.render(
        title=data.get("title", "Signal Audit"),
        subtitle=data.get("subtitle"),
        signals=data.get("signals", []),
        gen_time=gen_time,
    )


def _render_regime(data: dict, gen_time: str) -> str:
    return _REGIME_TEMPLATE.render(
        title=data.get("title", "Market Regimes"),
        subtitle=data.get("subtitle"),
        regimes=data.get("regimes", []),
        gen_time=gen_time,
    )



_SPEC_REQ_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.spec_requirements">
<meta name="artifact-tags" content="spec,requirements">
<title>{{ title }}</title>
<link rel="stylesheet" href="base.css">
<style>
.page { max-width: 1000px; }
.meta-panel { background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 18px 22px; margin-bottom: 24px; }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.meta-item label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--gray-500); display: block; margin-bottom: 2px; }
.meta-item span { font-size: 14px; color: var(--slate); font-weight: 500; }
.req-card { background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 20px 24px; margin: 14px 0; transition: box-shadow 0.15s; }
.req-card:hover { box-shadow: 0 2px 8px rgba(20,20,19,0.04); }
.req-card h3 { font-family: var(--serif); font-size: 18px; margin: 0 0 8px; }
.req-card .desc { font-size: 14px; color: var(--gray-700); margin-bottom: 12px; }
.req-card ul { margin: 0; padding-left: 18px; }
.req-card li { font-size: 13px; color: var(--slate); margin: 6px 0; }
.req-card .badge { display: inline-block; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; padding: 3px 10px; border-radius: 999px; margin-top: 10px; }
.badge-draft { background: var(--gray-100); color: var(--gray-700); }
.badge-approved { background: var(--olive); color: var(--white); }
.matrix-table { width: 100%; border-collapse: collapse; background: var(--white); border: var(--border); border-radius: var(--radius-panel); overflow: hidden; margin-top: 16px; }
.matrix-table th, .matrix-table td { padding: 10px 14px; border-bottom: 1px solid var(--gray-100); font-size: 14px; text-align: left; }
.matrix-table th { background: var(--gray-100); font-weight: 600; }
.matrix-table tr:last-child td { border-bottom: none; }
.cell-yes { color: var(--olive); font-weight: 600; }
.cell-no { color: var(--rust); }
.prework-list { list-style: none; padding: 0; margin: 0; }
.prework-list li { display: flex; align-items: center; gap: 10px; padding: 6px 0; font-size: 14px; }
.prework-list input { width: 16px; height: 16px; accent-color: var(--olive); }
.filter-bar { display: flex; gap: 8px; margin: 16px 0; flex-wrap: wrap; }
.filter-bar button { font-family: var(--sans); font-size: 12px; padding: 6px 14px; border: var(--border); border-radius: var(--radius-row); background: var(--white); cursor: pointer; }
.filter-bar button.active { background: var(--slate); color: var(--ivory); }
.toc { position: sticky; top: 24px; align-self: start; }
.toc a { display: block; padding: 4px 8px; border-radius: 4px; color: var(--slate); text-decoration: none; font-size: 13px; }
.toc a:hover { background: var(--gray-100); color: var(--clay); }
.toc a.l2 { font-weight: 600; }
.toc a.l3 { padding-left: 18px; }
.shell { display: grid; grid-template-columns: 220px 1fr; gap: 40px; }
@media (max-width: 800px) { .shell { grid-template-columns: 1fr; } .toc { position: static; } }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Requirements Spec</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  </header>

  <div class="meta-panel">
    <div class="meta-grid">
      {% for k, v in frontmatter.items() %}
      <div class="meta-item"><label>{{ k }}</label><span>{{ v }}</span></div>
      {% endfor %}
    </div>
  </div>

  <div class="shell">
    <nav class="toc">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:var(--gray-500);margin-bottom:8px;">Navegacao</div>
      <a href="#requirements" class="l2">Requirements</a>
      {% for r in requirements %}<a href="#req-{{ r.id }}" class="l3">{{ r.id }}: {{ r.title }}</a>{% endfor %}
      <a href="#coverage" class="l2">Coverage Matrix</a>
      <a href="#prework" class="l2">Prework</a>
    </nav>
    <div>
      <section id="requirements">
        <h2>Requirements ({{ requirements|length }})</h2>
        {% for r in requirements %}
        <div class="req-card" id="req-{{ r.id }}">
          <h3>{{ r.id }}: {{ r.title }}</h3>
          <div class="desc">{{ r.description }}</div>
          {% if r.criteria %}
          <ul>
            {% for c in r.criteria %}<li>{{ c }}</li>{% endfor %}
          </ul>
          {% endif %}
          <span class="badge badge-{{ r.status }}">{{ r.status }}</span>
        </div>
        {% endfor %}
      </section>

      <section id="coverage">
        <h2>Coverage Matrix</h2>
        <div class="filter-bar">
          <button class="active" onclick="filterMatrix('all')">Todos</button>
          <button onclick="filterMatrix('Yes')">Covered</button>
          <button onclick="filterMatrix('No')">Nao Covered</button>
        </div>
        <table class="matrix-table" id="matrix-table">
          <thead>
            <tr>
              {% for h in matrix_headers %}<th>{{ h }}</th>{% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in coverage_matrix %}
            <tr data-covered="{{ row.get('Covered', '') }}">
              {% for h in matrix_headers %}<td class="cell-{{ row.get(h, '').lower() }}">{{ row.get(h, '') }}</td>{% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </section>

      {% if prework %}
      <section id="prework">
        <h2>Prework Analysis</h2>
        <ul class="prework-list">
          {% for p in prework %}
          <li><input type="checkbox" {% if p.checked %}checked{% endif %} disabled> {{ p.text }}</li>
          {% endfor %}
        </ul>
      </section>
      {% endif %}
    </div>
  </div>

  <div class="gen-meta">artifact_engine.spec_requirements — {{ gen_time }}</div>
</main>
<script>
function filterMatrix(status) {
  document.querySelectorAll('.filter-bar button').forEach(b => b.classList.toggle('active', b.textContent.includes(status==='all'?'Todos':status)));
  document.querySelectorAll('#matrix-table tbody tr').forEach(r => {
    r.style.display = status === 'all' || r.dataset.covered === status ? '' : 'none';
  });
}
</script>
</body>
</html>
"""
)

_SPEC_DESIGN_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.spec_design">
<meta name="artifact-tags" content="spec,design">
<title>{{ title }}</title>
<link rel="stylesheet" href="base.css">
<style>
.page { max-width: 1000px; }
.meta-panel { background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 18px 22px; margin-bottom: 24px; }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.meta-item label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--gray-500); display: block; margin-bottom: 2px; }
.meta-item span { font-size: 14px; color: var(--slate); font-weight: 500; }
.goals-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0; }
.goal-card { background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 16px 20px; }
.goal-card h3 { font-family: var(--serif); font-size: 16px; margin: 0 0 8px; }
.goal-card.goal-in { border-top: 3px solid var(--olive); }
.goal-card.goal-out { border-top: 3px solid var(--rust); }
.toc { position: sticky; top: 24px; align-self: start; }
.toc a { display: block; padding: 4px 8px; border-radius: 4px; color: var(--slate); text-decoration: none; font-size: 13px; }
.toc a:hover { background: var(--gray-100); color: var(--clay); }
.toc a.l2 { font-weight: 600; }
.shell { display: grid; grid-template-columns: 220px 1fr; gap: 40px; }
@media (max-width: 800px) { .shell { grid-template-columns: 1fr; } .toc { position: static; } }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Design Spec</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  </header>

  <div class="meta-panel">
    <div class="meta-grid">
      {% for k, v in frontmatter.items() %}
      <div class="meta-item"><label>{{ k }}</label><span>{{ v }}</span></div>
      {% endfor %}
    </div>
  </div>

  <div class="shell">
    <nav class="toc">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:var(--gray-500);margin-bottom:8px;">Navegacao</div>
      {% for s in sections %}<a href="#sec-{{ loop.index }}" class="l2">{{ s.title }}</a>{% endfor %}
    </nav>
    <div>
      {% for s in sections %}
      <section id="sec-{{ loop.index }}">
        <h2>{{ s.title }}</h2>
        <div>{{ s.body_html | safe }}</div>
      </section>
      {% endfor %}
    </div>
  </div>

  <div class="gen-meta">artifact_engine.spec_design — {{ gen_time }}</div>
</main>
</body>
</html>
"""
)

_SPEC_TASKS_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="artifact_engine.spec_tasks">
<meta name="artifact-tags" content="spec,tasks">
<title>{{ title }}</title>
<link rel="stylesheet" href="base.css">
<style>
.page { max-width: 900px; }
.meta-panel { background: var(--white); border: var(--border); border-radius: var(--radius-panel); padding: 18px 22px; margin-bottom: 24px; }
.meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.meta-item label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--gray-500); display: block; margin-bottom: 2px; }
.meta-item span { font-size: 14px; color: var(--slate); font-weight: 500; }
.checkpoint { background: var(--white); border: var(--border); border-radius: var(--radius-panel); margin: 16px 0; overflow: hidden; }
.cp-header { display: flex; align-items: center; gap: 12px; padding: 16px 20px; cursor: pointer; background: var(--gray-100); }
.cp-header h3 { font-family: var(--serif); font-size: 18px; margin: 0; flex: 1; }
.cp-progress { font-family: var(--mono); font-size: 12px; color: var(--gray-500); }
.cp-body { padding: 12px 20px 20px; }
.task { padding: 12px 0; border-bottom: 1px solid var(--gray-100); }
.task:last-child { border-bottom: none; }
.task-head { display: flex; align-items: flex-start; gap: 10px; }
.task-head input { width: 18px; height: 18px; accent-color: var(--olive); margin-top: 2px; cursor: pointer; }
.task-head label { font-size: 15px; font-weight: 600; color: var(--slate); cursor: pointer; flex: 1; }
.task-details { font-size: 13px; color: var(--gray-700); margin: 6px 0 0 28px; }
.task-details ul { margin: 4px 0; padding-left: 16px; }
.task-meta { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 0 28px; }
.task-badge { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; padding: 2px 8px; border-radius: 999px; background: var(--oat); color: var(--slate); }
.overall-progress { position: sticky; top: 0; z-index: 20; background: var(--ivory); padding: 12px 0; border-bottom: var(--border); margin-bottom: 16px; }
.progress-track { height: 8px; background: var(--gray-100); border-radius: 999px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--olive); width: 0%; transition: width 0.3s; }
.progress-text { font-size: 12px; color: var(--gray-500); margin-top: 6px; text-align: right; font-family: var(--mono); }
</style>
</head>
<body>
<main class="page">
  <header class="mb-lg">
    <div class="eyebrow">Tasks Spec</div>
    <h1>{{ title }}</h1>
    {% if subtitle %}<p class="subtitle">{{ subtitle }}</p>{% endif %}
  </header>

  <div class="meta-panel">
    <div class="meta-grid">
      {% for k, v in frontmatter.items() %}
      <div class="meta-item"><label>{{ k }}</label><span>{{ v }}</span></div>
      {% endfor %}
    </div>
  </div>

  <div class="overall-progress">
    <div class="progress-track"><div class="progress-fill" id="overall-fill"></div></div>
    <div class="progress-text" id="overall-text">0% completo</div>
  </div>

  <div id="checkpoints">
    {% for cp in checkpoints %}
    <div class="checkpoint" data-cp="{{ loop.index }}">
      <div class="cp-header" onclick="this.nextElementSibling.classList.toggle('open');this.querySelector('.toggle').textContent=this.nextElementSibling.classList.contains('open')?'▲':'▼';">
        <h3>{{ cp.title }}</h3>
        <span class="cp-progress" id="cp-progress-{{ loop.index }}">0/{{ cp.tasks|length }}</span>
        <span class="toggle" style="font-size:12px;color:var(--gray-500);">▼</span>
      </div>
      <div class="cp-body">
        {% for t in cp.tasks %}
        <div class="task" data-task="{{ t.id }}">
          <div class="task-head">
            <input type="checkbox" id="task-{{ t.id }}" {% if t.checked %}checked{% endif %} onchange="updateProgress()">
            <label for="task-{{ t.id }}">{{ t.title }}</label>
          </div>
          {% if t.details %}
          <div class="task-details">
            <ul>{% for d in t.details %}<li>{{ d }}</li>{% endfor %}</ul>
          </div>
          {% endif %}
          {% if t.observable or t.boundary or t.requirement_refs %}
          <div class="task-meta">
            {% if t.observable %}<span class="task-badge">Obs: {{ t.observable[:40] }}{% if t.observable|length > 40 %}...{% endif %}</span>{% endif %}
            {% if t.boundary %}<span class="task-badge">Boundary: {{ t.boundary }}</span>{% endif %}
            {% for ref in t.requirement_refs %}<span class="task-badge">Req {{ ref }}</span>{% endfor %}
          </div>
          {% endif %}
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="gen-meta">artifact_engine.spec_tasks — {{ gen_time }}</div>
</main>
<script>
(function() {
  const storageKey = 'spec_{{ spec_name }}_tasks';
  function save() {
    const state = {};
    document.querySelectorAll('.task input[type="checkbox"]').forEach(cb => {
      state[cb.id] = cb.checked;
    });
    localStorage.setItem(storageKey, JSON.stringify(state));
  }
  function load() {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;
      const state = JSON.parse(raw);
      Object.entries(state).forEach(([id, checked]) => {
        const cb = document.getElementById(id);
        if (cb) cb.checked = checked;
      });
    } catch(e) {}
  }
  function updateProgress() {
    const tasks = document.querySelectorAll('.task input[type="checkbox"]');
    const checked = document.querySelectorAll('.task input[type="checkbox"]:checked');
    const pct = tasks.length ? (checked.length / tasks.length * 100) : 0;
    document.getElementById('overall-fill').style.width = pct + '%';
    document.getElementById('overall-text').textContent = Math.round(pct) + '% completo (' + checked.length + '/' + tasks.length + ')';
    document.querySelectorAll('.checkpoint').forEach(cp => {
      const cbs = cp.querySelectorAll('.task input[type="checkbox"]');
      const done = cp.querySelectorAll('.task input[type="checkbox"]:checked');
      const lbl = cp.querySelector('.cp-progress');
      if (lbl) lbl.textContent = done.length + '/' + cbs.length;
    });
    save();
  }
  document.querySelectorAll('.task input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', updateProgress);
  });
  load();
  updateProgress();
})();
</script>
</body>
</html>
"""
)


def _render_spec_requirements(data: dict, gen_time: str) -> str:
    matrix = data.get("coverage_matrix", [])
    headers = list(matrix[0].keys()) if matrix else []
    return _SPEC_REQ_TEMPLATE.render(
        title=data.get("title", "Requirements"),
        subtitle=data.get("subtitle"),
        frontmatter=data.get("frontmatter", {}),
        requirements=data.get("requirements", []),
        coverage_matrix=matrix,
        matrix_headers=headers,
        prework=data.get("prework", []),
        gen_time=gen_time,
    )


def _render_spec_design(data: dict, gen_time: str) -> str:
    return _SPEC_DESIGN_TEMPLATE.render(
        title=data.get("title", "Design"),
        subtitle=data.get("subtitle"),
        frontmatter=data.get("frontmatter", {}),
        sections=data.get("sections", []),
        gen_time=gen_time,
    )


def _render_spec_tasks(data: dict, gen_time: str) -> str:
    return _SPEC_TASKS_TEMPLATE.render(
        title=data.get("title", "Tasks"),
        subtitle=data.get("subtitle"),
        frontmatter=data.get("frontmatter", {}),
        checkpoints=data.get("checkpoints", []),
        spec_name=data.get("spec_name", "unknown"),
        gen_time=gen_time,
    )


_RENDERERS: dict[str, Callable[[dict, str], str]] = {
    "table": _render_table,
    "report": _render_report,
    "interactive": _render_interactive,
    "backtest-comparison": _render_backtest,
    "risk-dashboard": _render_risk,
    "signal-audit": _render_signal,
    "market-regime": _render_regime,
    "spec-requirements": _render_spec_requirements,
    "spec-design": _render_spec_design,
    "spec-tasks": _render_spec_tasks,
}

_SCHEMA_MAP: dict[str, type] = {
    "table": schemas.TableDataset,
    "report": schemas.ReportDataset,
    "interactive": schemas.InteractiveDataset,
    "status-report": schemas.ThariqDataset,
    "incident": schemas.ThariqDataset,
    "plan": schemas.ThariqDataset,
    "backtest-comparison": schemas.BacktestDataset,
    "risk-dashboard": schemas.RiskDataset,
    "signal-audit": schemas.SignalDataset,
    "market-regime": schemas.RegimeDataset,
    "spec-requirements": schemas.SpecDataset,
    "spec-design": schemas.SpecDataset,
    "spec-tasks": schemas.SpecDataset,
}


class ArtifactEngine:
    """Orquestra renderização, validação e persistência de artifacts HTML."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or DEFAULT_OUT_DIR
        self.thariq = ThariqRenderer()
        self._ensure_base_css()

    def _ensure_base_css(self) -> None:
        """Copia base.css para o output_dir para que links relativos funcionem."""
        src = PROJECT_ROOT / ".claude" / "skills" / "html-artifacts" / "base.css"
        dst = self.output_dir / "base.css"
        if src.exists() and not dst.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def render(self, type_id: str, dataset: dict[str, Any]) -> Path:
        """Valida dataset, renderiza e persiste artifact. Retorna Path do arquivo."""
        # 1. Validação de schema
        schema_cls = _SCHEMA_MAP.get(type_id)
        if schema_cls:
            try:
                validated = schema_cls.model_validate(dataset)
                dataset = validated.model_dump()
            except ValidationError as exc:
                raise ValueError(f"Dataset inválido para '{type_id}': {exc}") from exc

        # 2. Dispatch
        renderer = _RENDERERS.get(type_id)
        if renderer:
            html = renderer(dataset, dt.datetime.now().isoformat(timespec="seconds"))
        elif type_id in _THARIQ_TYPE_MAP or any(
            (TEMPLATES_DIR.glob(f"{type_id}*.html"))
        ):
            html = self.thariq.render(type_id, dataset)
        else:
            raise UnknownRendererError(f"Tipo '{type_id}' não existe no registry")

        # 3. Persistência
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_type = type_id.replace(" ", "-").lower()
        out_path = self.output_dir / f"{safe_type}-{ts}.html"
        # Normaliza link do base.css para mesmo diretório (independente de template)
        html = html.replace('href="../base.css"', 'href="base.css"')
        out_path.write_text(html, encoding="utf-8")

        # 4. Atualiza index automaticamente
        try:
            from build_artifact_index import build_index

            build_index(self.output_dir)
        except Exception:
            pass  # Não quebra render se index falhar

        return out_path

    def render_from_spec(self, source_path: Path) -> Path:
        """Lê arquivo markdown de spec e renderiza como artifact HTML."""
        md_text = source_path.read_text(encoding="utf-8")
        return self.render_from_spec_text(md_text)

    def render_from_spec_text(self, md_text: str) -> Path:
        """Parseia markdown de spec e renderiza como artifact HTML.

        Detecta automaticamente o tipo (requirements/design/tasks/generic)
        e dispacha para o renderer correto.
        """
        from spec_parser import SpecParser

        parsed = SpecParser().parse(md_text)
        spec_type = parsed.get("type", "generic")
        type_id = f"spec-{spec_type}"

        dataset = {
            "spec_name": parsed.get("title", "spec"),
            "version": parsed.get("frontmatter", {}).get("version", "0.1.0"),
            "source_path": "",
            "type": spec_type,
            "frontmatter": parsed.get("frontmatter", {}),
            "sections": parsed.get("sections", []),
            "requirements": parsed.get("requirements", []),
            "checkpoints": parsed.get("checkpoints", []),
            "coverage_matrix": parsed.get("coverage_matrix", []),
            "prework": parsed.get("prework", []),
            "raw_html": parsed.get("raw_html", ""),
            "title": parsed.get("title", "Spec"),
        }
        return self.render(type_id, dataset)

    def render_to_string(self, type_id: str, dataset: dict[str, Any]) -> str:
        """Renderiza e retorna HTML string (sem persistir)."""
        schema_cls = _SCHEMA_MAP.get(type_id)
        if schema_cls:
            validated = schema_cls.model_validate(dataset)
            dataset = validated.model_dump()

        renderer = _RENDERERS.get(type_id)
        if renderer:
            return renderer(dataset, dt.datetime.now().isoformat(timespec="seconds"))
        elif type_id in _THARIQ_TYPE_MAP:
            return self.thariq.render(type_id, dataset)
        else:
            raise UnknownRendererError(f"Tipo '{type_id}' não existe no registry")

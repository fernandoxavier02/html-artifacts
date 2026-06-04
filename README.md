<!-- ARCHIVED BANNER -->
<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&color=ff9800&height=80&text=📦%20ARCHIVED&fontSize=28&fontColor=ffffff&width=400"/>
  <p><b>This repository has been archived.</b></p>
  <p>My public portfolio has been restructured to focus on <a href="https://github.com/fernandoxavier02">Finance + AI showcases</a>.</p>
  <p>
    <a href="https://github.com/fernandoxavier02/ifrs15-revenue-intelligence-showcase">IFRS 15</a> ·
    <a href="https://github.com/fernandoxavier02/ifrs16-lease-intelligence-showcase">IFRS 16</a> ·
    <a href="https://github.com/fernandoxavier02/controllership-reconciliation-showcase">Reconciliation</a> ·
    <a href="https://github.com/fernandoxavier02/brazilian-tax-reform-oracle-showcase">Tax Oracle</a>
  </p>
  <hr/>
</div>

# html-artifacts

Generate self-contained HTML artifacts when output is too dense for markdown
chat. Curated library based on Thariq Shihipar's "Unreasonable Effectiveness
of HTML" (Anthropic Claude Code team).

## What it does

| When you ask for | Plugin generates |
|---|---|
| "Compare 3 auth options" | `compare-<ts>.html` (Thariq template 02) |
| "Implementation plan for X" | `plan-<ts>.html` (Thariq 16) |
| "Status report this week" | `status-<ts>.html` (Thariq 11) |
| "Post-mortem of incident Y" | `incident-<ts>.html` (Thariq 12) |
| "Flowchart of what happens when..." | `flow-<ts>.html` (Thariq 13) |
| "Explain how X works" | `feature-explainer-<ts>.html` (Thariq 14) |
| "Explain concept Y" | `concept-explainer-<ts>.html` (Thariq 15) |
| "Review this PR" | `pr-review-<ts>.html` (Thariq 03) |
| "Triage of open issues" | `triage-<ts>.html` (Thariq 18) |
| "Validate these N items" (5+) | `interactive-<ts>.html` with controls + clipboard response |
| Edit `.kiro/specs/<feat>/requirements.md` | `requirements.html` (spec renderer, auto-detected) |
| Edit any project `.md` | Companion HTML in `.claude/_html/<same-path>.html` |

Trading-domain renderers also included: `backtest-comparison`,
`risk-dashboard`, `signal-audit`, `market-regime`.

## Install

### 1. Add the marketplace

```
/plugin marketplace add fernandoxavier02/FX-studio-AI
```

### 2. Install the plugin

```
/plugin install html-artifacts
```

### 3. Verify

The skill `html-artifacts` should now appear in your skills list. The slash
command `/gen-html` should be available. The PostToolUse hook fires
automatically when you edit a `.md` file under `.claude/skills/`,
`.claude/rules/`, project `CLAUDE.md`, `*/knowledge_base/**`, or
`.kiro/specs/**`.

## Requirements

- **Python 3.10+** with `markdown`, `PyYAML`, `Jinja2`, `pydantic` installed
  (`pip install markdown PyYAML Jinja2 pydantic`)
- **Node 18+** (for the PostToolUse hook)
- Output dir: `.claude/_html/` (gitignored — add to your `.gitignore`)

## Usage

### Automatic companion HTML

Edit any of these files and the hook regenerates the corresponding
`.claude/_html/<same-path>.html`:

- `.claude/skills/**/*.md`
- `.claude/rules/*.md`
- `CLAUDE.md` (and `*/CLAUDE.md` under subprojects)
- `*/knowledge_base/**/*.md`
- `.kiro/specs/**/*.md`

Open with your OS's default browser:

- Windows: `start .claude\_html\CLAUDE.html`
- macOS: `open .claude/_html/CLAUDE.html`
- Linux: `xdg-open .claude/_html/CLAUDE.html`

### Manual batch regen

```
/gen-html              # full regen (5 categories)
/gen-html --skills     # only skills
/gen-html --specs      # only .kiro/specs
/gen-html --kb         # only knowledge_base
/gen-html --claude     # only CLAUDE.md files
/gen-html --rules      # only .claude/rules
/gen-html <path>       # single file
```

### Programmatic artifact generation

```python
from html_artifacts.src.artifact_engine import ArtifactEngine
from pathlib import Path

engine = ArtifactEngine()

# Tabular artifact
path = engine.render("table", {
    "title": "Backtest comparison",
    "columns": [{"key": "tf", "label": "Timeframe", "type": "str"},
                {"key": "pnl", "label": "PnL ($)", "type": "num"}],
    "rows": [{"tf": "H1", "pnl": 1620.5}, {"tf": "M30", "pnl": 1180.3}],
})

# Spec renderer (auto-detects requirements/design/tasks from filename)
path = engine.render_from_spec(Path(".kiro/specs/feat/requirements.md"))

# Output: .claude/_html/artifacts/<type>-YYYYMMDD-HHMMSS.html
print(path)
```

### Available type IDs

| Category | type_id |
|---|---|
| Core | `table`, `report`, `interactive` |
| Trading | `backtest-comparison`, `risk-dashboard`, `signal-audit`, `market-regime` |
| Spec | `spec-requirements`, `spec-design`, `spec-tasks` |

Full schema in `skills/html-artifacts/src/artifact_schemas.py`. Visual
templates in `skills/html-artifacts/examples/INDEX.md`.

## Interactive validation

When you need item-by-item validation (5+ items), generate an `interactive`
artifact. The user marks decisions in the browser, clicks **Confirm response**,
copies a JSON block delimited by `=== ARTIFACT RESPONSE === ... === END RESPONSE ===`,
and pastes it back into the chat. Your agent parses the block and continues.

Schema:

```json
{
  "title": "Validate plan v3",
  "subtitle": "5 fixes to approve",
  "context": "Markdown context paragraph...",
  "items": [
    {
      "id": "fix_1",
      "label": "Approve fix X",
      "details_md": "**Why:** ...\n**Risk:** ...",
      "type": "decision",
      "allow_note": true
    },
    {"id": "model", "label": "Model", "type": "select",
     "options": [{"value": "haiku", "label": "Haiku 4.5"},
                 {"value": "sonnet", "label": "Sonnet 4.6"}]}
  ]
}
```

`type` per item: `decision` (approve/reject/skip, default), `checkbox`,
`select`, `text`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `HTML_ARTIFACTS_ROOT` | `process.cwd()` (hook) / repo root inferred (Python) | Override project root |
| `HTML_ARTIFACTS_PYTHON` | `python` | Python binary used by the hook |

## Output structure

```
.claude/_html/
├── CLAUDE.html                              # companion of project CLAUDE.md
├── skills/<name>/SKILL.html                 # companion of skill SKILL.md
├── rules/<NN>-*.html                        # companion of rules
├── .kiro/specs/<feat>/*.html                # companion of specs
├── <subproject>/knowledge_base/*.html       # companion of KB cards
└── artifacts/
    ├── index.html                           # filterable feed of all artifacts
    ├── base.css                             # canonical CSS (inherited)
    ├── compare-YYYYMMDD-HHMMSS.html
    ├── plan-YYYYMMDD-HHMMSS.html
    ├── interactive-YYYYMMDD-HHMMSS.html
    └── ...
```

Add to your `.gitignore`:

```
.claude/_html/
```

## When NOT to use

- Simple questions answerable in 1-3 paragraphs of markdown
- Debug / quick status
- User explicitly asks "send in chat, no html"

The thesis (Thariq) applies to **output** (artifacts in files).
**Context files** (CLAUDE.md, skills, agents, rules) stay markdown.

## Credits

- HTML templates 02-20 are from
  https://thariqs.github.io/html-effectiveness/ by Thariq Shihipar
  (@trq212, Anthropic Claude Code team). Reproduced under fair use as
  reference templates; please cite if redistributed.
- Spec renderer and trading-domain renderers are project-specific
  additions.

## License

MIT — see `LICENSE`.

## Source

https://github.com/fernandoxavier02/html-artifacts

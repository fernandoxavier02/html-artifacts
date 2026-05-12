# Changelog

All notable changes to this plugin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-05-11

Initial public release.

### Added

- **17 Thariq HTML templates** in `skills/html-artifacts/examples/`:
  exploration (02), code review (03), code understanding (04),
  design system (05), component variants (06), prototype (08),
  SVG illustrations (10), status (11), incident (12),
  flowchart (13), feature explainer (14), concept explainer (15),
  implementation plan (16), PR writeup (17), triage (18),
  config editor (19), prompt tuner (20).
- **ArtifactEngine** unified renderer (`src/artifact_engine.py`) with 10 type IDs:
  core (`table`, `report`, `interactive`),
  trading (`backtest-comparison`, `risk-dashboard`, `signal-audit`, `market-regime`),
  spec (`spec-requirements`, `spec-design`, `spec-tasks`).
- **Pydantic schemas** (`src/artifact_schemas.py`) for dataset validation.
- **Spec parser** (`src/spec_parser.py`) auto-detects requirements/design/tasks
  from filename when calling `engine.render_from_spec(path)`.
- **Index builder** (`src/build_artifact_index.py`) generates a filterable
  landing page at `.claude/_html/artifacts/index.html`.
- **Canonical base.css** inherited by all generated artifacts (no inline CSS
  duplication).
- **PostToolUse hook** (`hooks/regen-html.cjs`) regenerates companion HTML
  when a `.md` file in 5 target categories is edited:
  skills, rules, CLAUDE.md, `*/knowledge_base/**`, `.kiro/specs/**`.
  Portable: uses `process.cwd()` as default project root; override with
  `HTML_ARTIFACTS_ROOT` env var.
- **Slash command** `/gen-html` with categories
  (`--all`, `--skills`, `--rules`, `--kb`, `--claude`, `--specs`) and
  single-path mode.
- **Interactive validation artifacts** with 4 control types
  (decision, checkbox, select, text) and clipboard-based response channel
  (delimited block `=== ARTIFACT RESPONSE === ... === END RESPONSE ===`).
- **Test suite** (`tests/`, 10 test files): artifact_index, artifact_schemas,
  base_css, e2e, interactive_modern, render_engine, spec_renderer,
  template_refactor, thariq_adapter, trading_templates.

### Notes

- HTML companion thesis (Thariq Shihipar, Anthropic Claude Code team):
  HTML wins over markdown for **output** in files; **context files**
  (CLAUDE.md, skills, agents, rules) stay markdown.
- Output directory `.claude/_html/` is intended to be gitignored
  (cache, not source of truth).
- Original templates 02-20 reproduced under MIT-compatible fair use.
  Original source: https://thariqs.github.io/html-effectiveness/

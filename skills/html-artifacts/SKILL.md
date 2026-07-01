---
name: html-artifacts
description: "Create self-contained, VISUAL-FIRST, interactive HTML artifacts for any active project when markdown chat is too flat for complex visual output: status reports, implementation plans, comparisons, incident reports, flowcharts, explainers, PR reviews, triage boards, config editors, prompt-tuning UIs. Every artifact MUST lead with a visual (flowchart, infographic, block diagram, progress bars) and MUST ship with interactive elements (checkboxes, buttons, collapsibles, response forms) persisted via localStorage — the file is a workspace, not a poster. Plain-language prose only (no jargon without inline gloss, no file paths in narrative, no bare acronyms). Triggers: 'gera um HTML', 'monta um artifact visual', 'faz um relatorio em HTML', 'quero abrir no browser', 'cria um post-mortem visual', 'design review em HTML', 'kanban', 'flowchart', 'pr writeup'. Installed globally in the host harness skills dir (~/.claude/skills/ for Claude Code, ~/.codex/skills/ for Codex); every artifact is written under the current working directory of the active project, never under the global skill folder."
---

# HTML Artifacts

Create or modify a standalone `.html` artifact when the user needs a visual document rather than a chat response.

This skill is installed in the global harness skills directory — `~/.claude/skills/html-artifacts/` when running under Claude Code, `~/.codex/skills/html-artifacts/` when running under Codex — and is shared across projects. **Detect the host harness from the invocation context (Claude Code vs Codex) and use the matching `.claude/` vs `.codex/` paths consistently for output, cache, and state.** Templates and base CSS are loaded from the global install; **generated artifacts always belong to the project the user is working in, never to the global folder.**

---

## ⛔ PRE-FLIGHT CHECKLIST (do not skip — incident-validated)

**Before calling ANY renderer (Python engine, template copy, AskUserQuestion, anything that produces an `.html`), answer these three questions out loud (in chat or internal trace):**

1. **Is the chosen renderer/type going to produce interactive elements?** If the project has a Python `ArtifactEngine` exposing `type_id` strings, the only acceptable defaults are types whose output is provably interactive (form inputs, checkboxes, decision controls, persisted state). Static-prose renderers (e.g. `type_id="report"`, `type_id="table"`-only, plain markdown-to-HTML) are **FORBIDDEN BY DEFAULT** — they violate Invariant 3 below. Use them only when the user explicitly said "static is fine" / "prose only" / "sem interatividade", and declare the override in the reply per Invariant 4.
2. **Will my reply end with a clickable `file:///` URI (Invariant 1)?** If you cannot answer "yes" with the exact URL already formed in your head, stop and form it before writing the file. URL-encode spaces. Windows: three slashes, drive letter, forward slashes.
3. **Does the artifact pose any question / ask for any decision from the user?** If yes, it MUST embed `<form>` controls + a `Copy my response` / `Confirm` button that emits a structured copyable block (Invariant 3 last paragraph). Prose questions in an artifact without a form are a defect.

**Failure log (this skill has been violated multiple times — do not add to the count):**

- Default-rendered `type_id="report"` (static prose) instead of `type_id="interactive"`: user has corrected this 2+ times. The renderer exists in some project forks but is NOT the default. Always pick the interactive sibling.
- Reply ended with a code-block path or `start <path>` instead of a clickable `file:///` URI: corrected 8+ times. There is no acceptable substitute.

If a project-local fork of this skill exposes a `report`-like static renderer, **assume it is deprecated** unless the project's local SKILL.md explicitly overrides this rule. The global rule wins.

---

## NON-NEGOTIABLE INVARIANTS (read this first, every time)

These rules apply to **every** HTML artifact operation in this skill — **creation, modification, enrichment, or rewrite**. They are not optional, not bypassable, and not subject to "but the user only asked me to add a section" reasoning. If the operation touches an `.html` file or generates one, ALL of them apply.

### Invariant 0 — Thariq's design language is SUPREME (MANDATORY, overrides everything else)

**The visual design language of every artifact this skill produces MUST follow Thariq Shihipar's editorial reference at https://thariqs.github.io/html-effectiveness/, mirrored locally in `assets/examples/` (17 reference templates) and `assets/base.css` (canonical tokens). Thariq's orientations are the supreme design contract — they prevail over any conflicting guidance in this file, in project-local SKILL.md forks, in user-supplied "make it look cool" requests without explicit non-Thariq direction, or in agent's own taste.**

Hard rules that operationalize Thariq's design supremacy:

1. **Mandatory palette anchor.** The artifact's color tokens MUST be the editorial palette from `assets/base.css`:
   - background: `--ivory #FAF9F5`
   - text: `--slate #141413` (headings) / `--gray-700 #3D3D3A` (body)
   - accent: `--clay #D97757` (warm orange, NOT pure red)
   - panel: `#FFFFFF` on ivory
   - secondary: `--oat #E3DACC`, `--olive #788C5D`, `--sky #6A8CAF`
   - borders: `--gray-300 #D1CFC5` at `1.5px solid`
   - Inventing your own palette (`#c8553d`, `#a4161a`, gradient heroes, etc.) is a defect. Use the tokens.

2. **Mandatory typography.** Headings use `var(--serif)` (`ui-serif, Georgia, "Times New Roman"`). Body uses `var(--sans)` (`system-ui, -apple-system, "Segoe UI"`). Code uses `var(--mono)` (`ui-monospace, "SF Mono", Menlo`). Heading sizes are restrained: h1 ≈ 33px, h2 ≈ 22px — NOT 2.2em hero-style. Sans-serif h1 with thick weight is a defect.

3. **Mandatory eyebrow labels.** Each major section starts with a small uppercase mono "eyebrow" label at 11px with `letter-spacing: 0.08em` and color `--gray-500`, ABOVE the serif heading. Pattern: `<div class="eyebrow">SECTION KIND</div><h2>Heading text</h2>`. Skipping the eyebrow is a defect.

4. **Mandatory layout.** Page max-width 1100px with a 240px right sidebar grid (`grid-template-columns: minmax(0, 1fr) 240px`). Body padding `56px 24px 120px`. Panel padding ~24px. Border radius 14px for big panels, 8-12px for rows. Wide gradient hero blocks, full-bleed colored sections, or dashboard-style sticky toolbars are NOT Thariq style — they are a defect.

5. **Mandatory inline glossary anchor.** Use `<span class="term" title="...">termo</span>` with `border-bottom: 1.5px dotted var(--clay)` for technical terms — Thariq's signature interaction pattern. Combine with Invariant 6's plain-language gloss requirement.

6. **Mandatory example anchoring.** Before writing, the agent MUST pick ONE example file from `assets/examples/` whose layout most closely matches the artifact being built and explicitly state which one (e.g., "emulating layout of `15-research-concept-explainer.html`"). Picking from the catalog forces Thariq compliance by construction.

7. **Restraint over flash.** Thariq's artifacts feel editorial, calm, dense with information but visually quiet. Heavy shadows, neon gradients, oversized hero blocks, multiple competing accent colors, emoji-heavy headings, dashboard-style sticky toolbars, and "techy" visual languages are anti-Thariq. When in doubt, less color, more whitespace, smaller type.

8. **Conflict resolution.** When ANY rule in this file (Invariant 1-6, Diagram rule, Interactivity rule, etc.) appears to conflict with Thariq's design language, **Thariq wins**. Specifically: Invariant 5 ("Visual em primeiro lugar") MUST be satisfied through Thariq-style information density (annotated diagrams, comparison tables, sidebar callouts), NOT through wide gradient hero blocks. Invariant 3 ("Thariq interactivity") interactive controls MUST use Thariq's restrained button styling (small, mono labels, neutral palette by default), NOT bright primary buttons.

This Invariant 0 also fires on modifications: if you enrich an existing artifact whose styling drifted from Thariq, the enrichment MUST bring the styling back to Thariq compliance — not preserve the drifted style.

### Invariant 1 — Clickable link in the reply (MANDATORY)

**The reply that follows the file write MUST end with a clickable `file:///` URI to the artifact.** No exceptions. No plain code-block path. No "open at `docs/diagrams/foo.html`" prose substitute.

- URL-encode spaces (` ` → `%20`).
- Windows: three slashes after `file:`, drive letter with colon, forward slashes inside the path. Example: `file:///D:/Pipeline%20Orchestrator%20Claude/Pipeline-Orchestrator/docs/diagrams/pipeline-overview.html`.
- On Windows, immediately below the clickable URI add a second line with the native backslash form for copy-paste into Explorer. Example: `(local: D:\Pipeline Orchestrator Claude\Pipeline-Orchestrator\docs\diagrams\pipeline-overview.html)`.
- If the artifact has named anchors that the user asked about, append the most relevant `#anchor` to the clickable URI.
- This rule fires even when the operation is a **modification** of an existing artifact (Edit, Write-over-existing, enrichment). Not just on first creation.

### Invariant 2 — Internal navigation (when artifact has 3+ major sections)

Any artifact with three or more top-level sections (`<h2>` or `<h3>`) MUST include a clickable in-page table of contents near the top, with each entry being an `<a href="#anchor">` to the corresponding section. The section headings MUST carry matching `id="anchor"` attributes. Long pages without internal navigation are not allowed — readers should never have to scroll-hunt.

### Invariant 3 — Thariq interactivity (MANDATORY, including for modifications)

**Every artifact this skill touches MUST ship with real interactive elements.** Static read-only HTML is a defect. The artifact is a workspace, not a poster. "You stay in the loop; the loop gets tighter" — Thariq's filosofia is enforced as a hard rule, not a suggestion.

Minimum bar (at least 2 of the following 4, picked to match the content):

1. **Checkable list items** with `<input type="checkbox">`, `.done` class toggle, and `localStorage` persistence keyed by artifact filename + item label. Apply to every list of flows, steps, options, criteria, checklists, or comparisons.
2. **`<details>/<summary>` collapsibles** for long explanatory sections (default for any artifact with three or more major sections).
3. **Action buttons** for the verbs that make sense in context: "Copy summary", "Mark all reviewed", "Export answers as JSON", "Reset state". Always provide visual feedback (`Copiado ✓`, class `.copied` for 1.2s).
4. **Tabs or filter pills** when comparing variants (e.g., Leve vs Pesado) or filtering long lists.

**Response mechanism (mandatory when the artifact poses any question):** if the artifact asks the user to choose, decide, sign off, or pick a path, it MUST include an inline `<form>` with `<input type="radio">` (single choice), `<input type="checkbox">` (multi-select), or `<textarea>` (free text). A `Copy my response` button MUST build a structured text block (e.g., `# resposta\n- pergunta: ...\n- escolha: ...\n- notas: ...`) and copy it via `navigator.clipboard.writeText`. State persists via `localStorage` so the artifact survives reopens.

**All interactivity is client-side only.** Inline `<script>` + `localStorage` — no backend, no external fetches. Artifact must render offline.

**This rule fires on modifications too.** If you enrich an existing artifact that lacked interactivity, the enrichment MUST bring interactivity with it. "I only added a section" is not an exemption.

**No loophole for "naturally static" templates.** Even pure-diagram types (`svg-illustrations`, `flowchart-diagram`) MUST add at minimum: a `<details>/<summary>` "About this diagram" panel, a `Copy SVG markup` button with `.copied` feedback, AND a single-question feedback `<form>` ("Esse diagrama bate com o que voce esperava?" with radio + textarea + `Copy my response`). Two interactive elements minimum, no exceptions.

### Invariant 4 — Anti-silent-skip

If for any reason you decide to skip Invariant 1, 2, 3, 5 or 6 (size constraint, partial edit, etc.), you MUST state it explicitly in the reply ("skipping clickable link because…", "skipping interactivity because…", "skipping hero visual because…") so the user can challenge the omission. Silent skip is a defect.

### Invariant 5 — Visual em primeiro lugar (MANDATORY, including for modifications)

**Every artifact MUST lead with a visual element and keep visuals dominant over prose.** Text is supporting cast, never the protagonist. A wall-of-text artifact with one decorative SVG at the bottom is a defect — even if the prose is perfect.

Hard rules:

1. **Hero visual within the first viewport.** The first `<section>` after the `<header>` MUST contain a dominant visual: inline SVG flowchart, infographic block diagram, hierarchy tree, comparison matrix with color-coded cells, progress bars, status tiles, KPI cards, or stacked annotated panels. Decorative thin SVG dividers do NOT count. The visual MUST carry meaning the prose alone could not communicate as fast.
2. **Visual-to-prose ratio.** Across the whole artifact, visual elements (SVG diagrams, infographic blocks, icon-bearing cards, color-coded matrices, progress meters, status pills with semantic color, annotated screenshots) MUST account for at least 50% of the vertical real estate on first render (before collapsibles expand). Long prose paragraphs that crowd out the visual layer are a defect.
3. **Prose is supporting layer.** Long explanations live inside `<details>/<summary>` collapsibles, hover tooltips (`<abbr title="...">`), or side panels — never as the main body. The first 100 px of every section after the hero MUST contain a visual cue (icon, mini-diagram, status pill, color-coded badge), not a prose paragraph.
4. **Every list of 3+ items MUST get a visual treatment.** Plain `<ul>/<ol>` for 3+ items is a defect — convert to: numbered step diagram with connectors, icon-prefixed cards in a grid, a kanban-style column layout, or a color-coded comparison row. Single-item or two-item lists may stay textual.
5. **Color is meaning, not decoration.** Use semantic color (success/warn/error/info/neutral) consistently. Every color MUST appear in a small legend somewhere in the artifact so meaning is explicit.
6. **Diagram coverage.** The Diagram rule (workflows / step content → inline SVG flowchart) is automatically subsumed by Invariant 5: any 3+ sequential steps require a SVG flowchart, period — no escape via "but it's only a status report".

This rule fires on modifications too: enriching an artifact that lacks a hero visual MUST add one before/with the new content.

### Invariant 6 — Linguagem leiga e acessivel (MANDATORY)

**Every word the artifact shows the user MUST follow the plain-language rules from the user's global CLAUDE.md (`~/.claude/CLAUDE.md` → "Estilo de Conversa com o Usuario").** The artifact is read in Portuguese (pt-BR) unless the user explicitly asks otherwise. Technical correctness is not an excuse for jargon.

Hard rules (apply to every visible string in the artifact — headings, labels, button text, tooltips, prose, legends, form questions, error messages):

1. **Veredicto primeiro.** Each section's opening line MUST state the outcome / status / decision in one sentence before any detail (e.g., "Deu certo, com 2 ressalvas." → then the detail). A section that buries the conclusion is a defect.
2. **Termo tecnico SEMPRE com gloss inline na primeira ocorrencia.** Every technical term (callback, deadlock, threading, Z-score, EWMA, percentil, sweep, absorcao, latencia, etc.) MUST be glossed on its first appearance in plain words, using either inline parentheses (`callback (a forma como a biblioteca chama uma funcao nossa quando algo acontece)`) or `<abbr title="...">` for hover. No exceptions.
3. **Sem caminhos de arquivo / URLs / hashes / IDs / versoes na prosa narrativa.** File paths, URLs, commit shas, agent IDs, version numbers, and bare flags MUST appear ONLY inside `<code>`, `<pre>`, or a dedicated "Pra executar" / "Links" / "Comandos" block at the bottom of the artifact — never inline in narrative sentences. In narrative, refer to them by function ("o modulo de captura", "a pasta de saida", "o ultimo commit").
4. **Acronimos sem expansao sao defeito.** First occurrence of any acronym (API, JSON, TTS, PR, PID, JWT, SVG, CSS, JS, etc.) MUST expand or substitute by a common name. After first expansion, the acronym may be used.
5. **Sem tags de metadado na prosa.** Tags like `[VERIFICADO]`, `[HIPOTESE]`, `[DESIGN]`, `[WEB]` are audit metadata — they MAY appear in dedicated badges/pills with semantic color, but MUST NOT appear inline in narrative sentences. In prose, the artifact says "isso eu confirmei rodando" / "isso eu suponho" — the certainty is communicated by content, not by a literal tag string.
6. **Numeros com contexto, nunca crus.** `accuracy=0.033` is a defect; write `acertou 3,3% — pior que chutar (~20% em problema de 5 opcoes)`. Every metric MUST carry its baseline / reference / unit in plain words.
7. **Teste do ouvido.** Imagine the artifact's visible prose being read aloud by TTS. If you "hear" a file path spelled letter by letter, a URL with `h-t-t-p-s dois pontos barra barra...`, a commit hash digit by digit, or a version `v-quatro-ponto-um-ponto-zero`, REWRITE before saving. If it fails the ear test, it fails the eye test too.
8. **Tooltips bilingual safety.** When a technical term is unavoidable (e.g., it appears inside `<code>` in a command block), the matching narrative reference uses the plain-language alias defined at first occurrence. Do not switch back and forth.

The skill MAY emit the artifact in English ONLY if the user explicitly asked for English output. Default is pt-BR.

## Workflow (6 steps — alinhado 1:1 com o slash command `/html-artifacts`)

1. **Identify type.** Consult [template-catalog](references/template-catalog.md) and pick the exact catalog type (long form). If the user's request doesn't match exactly, **ask** — see "Anti-silent-adaptation rule" below.
2. **Load template.** Read `<install>/assets/examples/<NN>-<type>.html` and reuse `<install>/assets/base.css` when useful. Use absolute paths (do not rely on `~` expansion in tool calls — resolve via `$HOME` / `$USERPROFILE` first).
3. **Adapt + inject interactivity + diagram.** Substitute placeholders, brand, paths, dates, metrics with the **active project's** facts (real project name from cwd; do not reuse origin-project names). Apply the **Interactivity rule** (min 2 elements + response form when there's a question) and the **Diagram rule** (inline SVG flowchart for workflow/step-based content). See dedicated sections below.
4. **Hard-gate of cwd (before writing).** Abort or ask if:
   - (a) cwd contains `\.codex\skills\` or `/.codex/skills/` (skill store) — hard abort.
   - (b) `SKILL.md` exists exactly at cwd root AND cwd contains `\.codex\skills\` or `/.codex/skills/` (installed skill via symlink) — hard abort.
   - (c) cwd has no project markers (`.git`, `package.json`, `pyproject.toml`, etc — see slash command Step 4(c) for full list). Before asking, consult the **trusted-cwds cache** (see below); if cwd is approved, skip the prompt. Otherwise ask via 3-option AskUserQuestion (only-this-time / approve-and-remember / cancel).
   - **Glob filtering reminder**: Glob is recursive by default; for any marker check at root, filter results to keep only matches whose normalized path equals `<cwd>/<marker>` exactly.
5. **Resolve path and write.** Convention: `<cwd>/.claude/artifacts/html/<type>-YYYYMMDD-NN.html` when running under Claude Code, `<cwd>/.codex/artifacts/html/<type>-YYYYMMDD-NN.html` when running under Codex. **Pick the path that matches the host harness — never mix.** `YYYYMMDD` from system context; `NN` = `max(parsed NN of existing matches) + 1`, zero-padded. Glob with `path = <cwd>/.claude/artifacts/html` (or `.codex/`) — subdir as path, not pattern (pattern starting with `.` is ignored). Write creates parents. Never write under the skill folder.
6. **Reply with clickable link.** **See Invariant 1 at the top of this file — this is non-negotiable, including for modifications/enrichments of existing artifacts.** URL-encode spaces (` ` → `%20`); format `file:///D:/proj/.codex/artifacts/html/foo.html` (3 slashes Windows, with drive letter and forward slashes). On Windows, add a second line `(local: D:\proj\.codex\artifacts\html\foo.html)` with native backslashes for Explorer convenience. If the user asked about a specific section of the artifact, append the relevant `#anchor`. End with one-line summary. Do not paste full HTML in chat.

## Trusted cwd cache

When the cwd lacks the project markers expected by the hard-gate, before asking the user, read the trusted-cwds cache:

- Codex: `~/.codex/state/html-artifacts-trusted-cwds.txt`
- Claude Code: `~/.claude/state/html-artifacts-trusted-cwds.txt`

Each non-comment line is an absolute path the user has previously authorized as a non-project write target. Compare normalized (lowercase on Windows, trim trailing slash). If the current cwd matches a line, **skip the prompt and write normally.**

If it doesn't match, ask via the 3-option pattern: (1) write only this time, (2) write **and remember** (append the cwd to the cache file), (3) cancel and `cd` elsewhere. When the user picks option 2, append the normalized cwd to the cache as a new line, preserving prior content.

## Anti-silent-adaptation rule

If the user's request does not match exactly one of the catalog types, **never** silently "adapt" the closest template. Always ask the user to pick between the 2-3 nearest types, or to authorize a custom layout. Loud failure beats wrong delivery.

## Diagram rule (mandatory for workflows / step-based content)

When the artifact describes a workflow, a sequence of steps, a decision tree, a pipeline, or any "step 1 → step 2 → step 3" content, it MUST include an inline SVG flowchart that visualizes the flow. Prose with arrows (→) and bullet points are not enough — readers parse diagrams faster than lists for sequential logic.

Applies to these types specifically:
- `flowchart-diagram` (obvious)
- `implementation-plan` (phases / steps)
- `incident-report` (timeline is already there; add a "what we did" mini-flowchart in addition)
- `feature-explainer` and `concept-explainer` (mechanism / lifecycle)
- `code-understanding` (execution flow)
- Any other artifact whose content lists 3+ sequential steps in prose

Implementation pattern (inline SVG, no JS, no external libs):

- Use a `<svg viewBox="0 0 W H">` sized to the content area.
- Nodes: `<g class="node"><rect ... rx="6"/><text .../></g>` — rounded rects with text label.
- Decision nodes: same but `rx="0"` rotated 45deg via `transform`, or use a `<polygon points="..."/>` rhombus.
- Edges: `<path class="edge" d="M x1 y1 L x2 y2"/>` with `<marker>` arrowhead defined in `<defs>`.
- Colors: use the design tokens (`--clay` for primary, `--olive` for success, `--rust` for error, `--gray-500` for default edges).
- Add a `<details><summary>About this diagram</summary><div>...</div></details>` below it with prose explaining the steps in order (accessibility + screen readers).

A diagram that requires JS to render (Mermaid runtime, etc.) is **not allowed** — artifacts must be self-contained and render offline. Hand-rolled SVG only.

For `svg-illustrations` and `flowchart-diagram` types where the diagram IS the artifact, this rule is automatically satisfied; just ensure the SVG is the centerpiece.

## Interactivity rule (mandatory)

Every generated artifact MUST include interactive elements. Static read-only HTML is not allowed. Thariq's filosofia ("you stay in the loop; the loop gets tighter") becomes a hard rule here: each artifact is a workspace, not a poster.

Minimum interactivity for every artifact (apply at least 2):

1. **`<details>/<summary>`** collapsible sections for long bodies (default for any artifact with 3+ sections).
2. **Checkable list items** for any inventory/checklist (skills, PRs, action items, etc): `<input type="checkbox">` with a small inline JS that toggles `.done` class and persists state to `localStorage` keyed by artifact filename + item label.
3. **Action buttons** for the main verbs that make sense in context: "Copy to clipboard", "Mark all done", "Export as JSON", "Reset", etc. Always provide visual feedback (`Copied ✓`, `Reset done`, class `.copied` for 1.2s).
4. **Tabs or filter pills** when comparing options or filtering large lists.

When the artifact poses a question to the user (a triage decision, a choice between approaches, a sign-off), it MUST include an inline response mechanism — not just prose asking for input. Implementation pattern:

- Use `<form>` with `<input type="radio">` (mutually exclusive choices), `<input type="checkbox">` (multi-select), or `<textarea>` (free text) for the answer.
- Add a `Save answer` or `Copy my response` button that builds a structured text block (e.g., `# /html-artifacts answer\n- question: ...\n- choice: ...\n- notes: ...`) and copies it to clipboard via `navigator.clipboard.writeText`.
- Persist the answer in `localStorage` so the file survives reopens with the user's state preserved.
- Show the saved answer back in the UI after save, with a small "edit" affordance.

All interactivity is **client-side only**. No backend, no fetch to external URLs. Tudo inline `<script>` + `localStorage`. Artifact continues self-contained — opening offline still works.

**No template is exempt.** Even pure-diagram types (`svg-illustrations`, `flowchart-diagram`) MUST ship with at least two interactive elements — minimum bar: a `<details>/<summary>` "About this diagram" panel, a `Copy SVG markup` button (with `.copied` feedback), AND a 1-question feedback form (`Esse diagrama bate com o que voce esperava?` → radio + textarea + `Copy my response`). See Invariant 3 for the binding rule.

## Rules

- Keep artifacts self-contained: inline CSS/SVG/JS unless the user asks otherwise.
- Do not include secrets, private IDs, credentials, tokens, or broker account details in an artifact without explicit confirmation. **Treat as secret** (default-redact, ask before including): tokens with shapes like `sk_*`, `pk_*`, `ghp_*`, JWTs (`eyJ...`-prefixed three-segment strings), API keys, `.env` values, broker/bank account IDs, internal IPs, full database connection strings, paths containing usernames in cloud-sync folders, customer PII (CPF, RG, email, phone). **NOT secret** (safe to include): aggregated public metrics, OSS project names, commit hashes (public repos), relative paths, public API endpoints, anonymized counts. When unsure, ask.
- Prefer existing templates before inventing a new layout.
- Treat the skill folder (`~/.claude/skills/html-artifacts/` under Claude Code, `~/.codex/skills/html-artifacts/` under Codex) as read-only template material. Output goes under the active project, not under the skill.
- If a generated artifact becomes reusable as a template, only promote it into `assets/examples/` after the user explicitly asks for promotion.

## Common Mistakes

- Do not use the legacy Claude HTML output folder as the Codex output path.
- Do not treat rendered HTML copies as the source of truth; source material is the Markdown/template content bundled with this skill.
- Do not summarize the full artifact in markdown after saving it. The HTML file is the output.
- Do not write artifacts into `~/.claude/skills/html-artifacts/` or `~/.codex/skills/html-artifacts/` or any sibling skill directory — always anchor output to the project cwd.
- **When using `Glob` to check for a project marker at the cwd root** (`.git`, `package.json`, `SKILL.md`, etc.), remember that `Glob` is **recursive by default** — it captures matches in any subdirectory. Always filter the results to keep only matches whose normalized path equals `<cwd>/<marker>` exactly. Otherwise a project with nested skills/submodules will falsely satisfy "marker present at root".

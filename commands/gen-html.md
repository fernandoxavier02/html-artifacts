---
description: Regenerate HTML companion of context files (skills, rules, CLAUDE.md, knowledge_base, .kiro/specs). Use without argument for full regen, or pass a path for single-file regen.
argument-hint: "[path/to/file.md | --all | --skills | --rules | --kb | --claude | --specs]"
---

# Regenerate HTML companion

You are Claude Code. The user invoked `/gen-html` with argument: `$ARGUMENTS`

## Action

Interpret `$ARGUMENTS`:

- **empty or `--all`**: run the full batch over the 5 categories (skills, rules, CLAUDE.md, knowledge_base, .kiro/specs)
- **specific path** (e.g. `.claude/skills/tape-reading/SKILL.md`): regen only that file
- **category** (e.g. `--skills`, `--rules`, `--kb`, `--claude`, `--specs`): regen only that category

The skill is invoked from the current working directory (project root). The
generator script lives inside this plugin at
`${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py`.

## Commands

### Full regen (`/gen-html` or `/gen-html --all`)

```bash
SPIKE="${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py"
OK=0; FAIL=0
for f in $(find .claude/skills -name '*.md' 2>/dev/null) \
         $(find .claude/rules -name '*.md' 2>/dev/null) \
         $(find . -maxdepth 3 -name 'CLAUDE.md' -not -path '*/node_modules/*' -not -path '*/_html/*' 2>/dev/null) \
         $(find . -name '*.md' -path '*knowledge_base*' 2>/dev/null) \
         $(find .kiro/specs -name '*.md' 2>/dev/null); do
  if python "$SPIKE" "$f" >/dev/null 2>&1; then OK=$((OK+1)); else FAIL=$((FAIL+1)); fi
done
echo "OK: $OK  FAIL: $FAIL"
echo "Output: .claude/_html/"
```

### Single file

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py" "<path>"
```

### Category

- `--skills`: `find .claude/skills -name '*.md' | xargs -I{} python "${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py" {}`
- `--rules`: `find .claude/rules -name '*.md' | xargs -I{} python "${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py" {}`
- `--kb`: `find . -name '*.md' -path '*knowledge_base*' | xargs -I{} python "${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py" {}`
- `--claude`: `find . -maxdepth 3 -name 'CLAUDE.md' -not -path '*/node_modules/*' -not -path '*/_html/*' | xargs -I{} python "${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py" {}`
- `--specs`: `find .kiro/specs -name '*.md' | xargs -I{} python "${CLAUDE_PLUGIN_ROOT}/skills/html-artifacts/src/gen_html_spike.py" {}`

## Output

Report to the user:
- How many files converted (OK + FAIL)
- Where they live (`.claude/_html/...`)
- If any failures, list the paths

Short reply. No verbose narration.

#!/usr/bin/env node
/**
 * PostToolUse hook: regenerates HTML companion when Edit/Write modifies
 * a .md file in a target category (skills, rules, CLAUDE.md, knowledge_base,
 * .kiro/specs). Portable across machines — uses process.cwd() as project root.
 *
 * Flow:
 *   1. Read JSON event from stdin
 *   2. Filter tool_name in (Edit, Write, MultiEdit)
 *   3. Filter file_path matching target categories
 *   4. Spawn `python <skill_root>/src/gen_html_spike.py <file>` in background
 *   5. Exit immediately (does not block the tool)
 *
 * Silent failure: HTML companion is best-effort; must NOT break the flow.
 *
 * Optional env vars:
 *   - HTML_ARTIFACTS_ROOT: override project root (default: process.cwd())
 *   - HTML_ARTIFACTS_PYTHON: python binary (default: "python")
 */

const { spawn } = require("child_process");
const path = require("path");

const PROJECT_ROOT = process.env.HTML_ARTIFACTS_ROOT || process.cwd();
const PYTHON_BIN = process.env.HTML_ARTIFACTS_PYTHON || "python";

// Target categories (regex tested against forward-slash-normalized path)
const TARGET_PATTERNS = [
  /\.claude\/skills\/.*\.md$/i,
  /\.claude\/rules\/.*\.md$/i,
  /(^|\/)CLAUDE\.md$/i,
  /tape-engine\/.*knowledge_base\/.*\.md$/i,
  /\.kiro\/specs\/.*\.md$/i,
];

// Exclude generated/ephemeral paths
const EXCLUDE_PATTERNS = [
  /\.claude\/_html\//i,
  /\.pipeline\/docs\//i,
  /node_modules\//i,
  /\.worktrees\//i,
];

function normalizePath(p) {
  return p.replace(/\\/g, "/");
}

function shouldRegen(filePath) {
  if (!filePath || !filePath.toLowerCase().endsWith(".md")) return false;
  const norm = normalizePath(filePath);
  if (EXCLUDE_PATTERNS.some((re) => re.test(norm))) return false;
  return TARGET_PATTERNS.some((re) => re.test(norm));
}

function resolveSpike() {
  // Plugin script lives at:
  //   <plugin_root>/skills/html-artifacts/src/gen_html_spike.py
  // This hook lives at:
  //   <plugin_root>/hooks/regen-html.cjs
  // So spike is at: ../skills/html-artifacts/src/gen_html_spike.py
  return path.join(
    __dirname,
    "..",
    "skills",
    "html-artifacts",
    "src",
    "gen_html_spike.py"
  );
}

async function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    // Timeout-safety: if stdin does not close in 200ms, proceed with what we have
    setTimeout(() => resolve(data), 200);
  });
}

async function main() {
  const raw = await readStdin();
  if (!raw) return;

  let event;
  try {
    event = JSON.parse(raw);
  } catch {
    return;
  }

  const toolName = event.tool_name || event.tool || "";
  if (!["Edit", "Write", "MultiEdit"].includes(toolName)) return;

  const input = event.tool_input || event.toolInput || {};
  const filePath = input.file_path || input.filePath;
  if (!shouldRegen(filePath)) return;

  try {
    const py = spawn(
      PYTHON_BIN,
      [resolveSpike(), filePath],
      {
        cwd: PROJECT_ROOT,
        detached: true,
        stdio: "ignore",
        env: {
          ...process.env,
          HTML_ARTIFACTS_ROOT: PROJECT_ROOT,
        },
      }
    );
    py.unref();
  } catch {
    // ignore
  }
}

main().catch(() => process.exit(0));

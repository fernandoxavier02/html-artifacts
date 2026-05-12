"""SpecParser — Extrai estrutura semântica de specs markdown (Kiro/GSD/generic).

Converte arquivos .md com frontmatter YAML em dicts tipados para renderização
como HTML artifacts.
"""
from __future__ import annotations

import sys
from pathlib import Path
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import re
from typing import Any

import yaml


class SpecParser:
    """Parser stateless para specs markdown."""

    # Regex frontmatter: ---\n...\n---
    _FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    # Requirement header: ### Requirement N: Title
    _REQ_HEADER_RE = re.compile(r"^###\s+Requirement\s+\d+:\s*(.+)$", re.MULTILINE)
    # Checkbox: - [x] text  or  - [ ] text
    _CHECKBOX_RE = re.compile(r"^- \[(x| )\]\s+(.*)$", re.MULTILINE)
    # Coverage matrix / generic table header
    _TABLE_SEP_RE = re.compile(r"^\|?[-:\|\s]+\|?$", re.MULTILINE)
    # Checkpoint header
    _CHECKPOINT_RE = re.compile(r"^(##\s+CHECKPOINT\s+.+)$", re.MULTILINE)
    # Requirement refs: _Requirements: 1.1, 1.2_
    _REQ_REFS_RE = re.compile(r"_Requirements:\s*([\d.,\s]+)_")
    # Boundary ref: _Boundary: ..._
    _BOUNDARY_RE = re.compile(r"_Boundary:\s*([^_]+)_")
    # Observable: Observable: ...
    _OBSERVABLE_RE = re.compile(r"Observable:\s*(.+)$", re.MULTILINE)

    def parse(self, md_text: str) -> dict[str, Any]:
        """Parseia texto markdown e retorna estrutura semântica."""
        result: dict[str, Any] = {
            "frontmatter": {},
            "type": "generic",
            "title": "",
            "sections": [],
            "requirements": [],
            "prework": [],
            "checkpoints": [],
            "coverage_matrix": [],
            "raw_html": "",
        }

        # 1. Frontmatter
        body = self._extract_frontmatter(md_text, result)

        # 2. Título (primeiro H1)
        result["title"] = self._extract_title(body) or result["frontmatter"].get("spec", "Spec")

        # 3. Detectar tipo
        result["type"] = self._detect_type(body)

        # 4. Extrair seções
        result["sections"] = self._extract_sections(body)

        # 5. Extrair requirements (se presentes)
        result["requirements"] = self._extract_requirements(body)

        # 6. Extrair checkboxes / prework
        result["prework"] = self._extract_checkboxes(body)

        # 7. Extrair coverage matrix
        result["coverage_matrix"] = self._extract_coverage_matrix(body)

        # 8. Extrair checkpoints + tasks
        result["checkpoints"] = self._extract_checkpoints(body)

        # 9. Converter body restante para HTML básico
        result["raw_html"] = self._md_to_html(body)

        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_frontmatter(self, md_text: str, result: dict) -> str:
        m = self._FRONTMATTER_RE.match(md_text.strip())
        if m:
            try:
                result["frontmatter"] = yaml.safe_load(m.group(1)) or {}
            except Exception:
                result["frontmatter"] = {}
            return m.group(2)
        return md_text

    def _extract_title(self, body: str) -> str:
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        return m.group(1).strip() if m else ""

    def _detect_type(self, body: str) -> str:
        lower = body.lower()
        if "## requirements" in lower and "## coverage matrix" in lower:
            return "requirements"
        if "## checkpoint" in lower:
            return "tasks"
        if "## goals & non-goals" in lower or "## boundary commitments" in lower:
            return "design"
        return "generic"

    def _extract_sections(self, body: str) -> list[dict[str, Any]]:
        """Extrai H2/H3 como seções com body."""
        sections: list[dict[str, Any]] = []
        # Split por headers H2
        pattern = re.compile(r"^(##\s+.+)$", re.MULTILINE)
        parts = pattern.split(body)
        if parts:
            # parts[0] é o conteúdo antes do primeiro H2 (geralmente vazio ou título)
            for i in range(1, len(parts), 2):
                header = parts[i].strip()
                content = parts[i + 1] if i + 1 < len(parts) else ""
                level = 2 if header.startswith("## ") else 3
                title = header.lstrip("# ").strip()
                sections.append({
                    "title": title,
                    "level": level,
                    "body_md": content.strip(),
                    "body_html": self._md_to_html(content),
                })
        return sections

    def _extract_requirements(self, body: str) -> list[dict[str, Any]]:
        reqs: list[dict[str, Any]] = []
        # Encontrar a seção "## Requirements"
        req_section = re.search(
            r"##\s+Requirements\s*\n(.*?)(?=^##\s|\Z)", body, re.MULTILINE | re.DOTALL
        )
        if not req_section:
            return reqs

        section_text = req_section.group(1)
        # Cada requirement começa com ### Requirement N: Title
        blocks = re.split(r"(?=^###\s+Requirement\s+\d+:\s*)", section_text, flags=re.MULTILINE)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            header = self._REQ_HEADER_RE.search(block)
            if not header:
                continue
            title = header.group(1).strip()

            # Description: entre header e Acceptance Criteria
            desc = ""
            desc_match = re.search(r"\*\*Description:\*\*\s*(.+?)(?=\*\*Acceptance Criteria|\Z)", block, re.DOTALL)
            if desc_match:
                desc = desc_match.group(1).strip()

            # Acceptance Criteria
            criteria: list[str] = []
            ac_match = re.search(r"\*\*Acceptance Criteria:\*\*(.*?)(?=_|\Z)", block, re.DOTALL)
            if ac_match:
                for line in ac_match.group(1).strip().split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        criteria.append(line[2:].strip())

            reqs.append({
                "id": f"R{len(reqs)+1}",
                "title": title,
                "description": desc,
                "criteria": criteria,
                "status": "draft",
            })
        return reqs

    def _extract_checkboxes(self, body: str) -> list[dict[str, Any]]:
        boxes: list[dict[str, Any]] = []
        for m in self._CHECKBOX_RE.finditer(body):
            boxes.append({
                "checked": m.group(1).lower() == "x",
                "text": m.group(2).strip(),
            })
        return boxes

    def _extract_coverage_matrix(self, body: str) -> list[dict[str, str]]:
        matrix: list[dict[str, str]] = []
        # Regex mais permissivo para tabelas markdown
        tables = re.findall(
            r"(\|[^\n]+\|)\n\|?[-:\|\s]+\|?\n((?:\|[^\n]*\|\n?)+)", body
        )
        for header_row, data_rows in tables:
            headers = [h.strip() for h in header_row.split("|") if h.strip()]
            if not headers or "Requirement" not in headers[0]:
                continue
            for line in data_rows.strip().split("\n"):
                if not line.strip() or not line.startswith("|"):
                    continue
                cells = [c.strip() for c in line.split("|")]
                if cells and cells[0] == "":
                    cells = cells[1:]
                if cells and cells[-1] == "":
                    cells = cells[:-1]
                if len(cells) >= len(headers):
                    row = {headers[i]: cells[i] for i in range(len(headers))}
                    matrix.append(row)
        return matrix

    def _extract_checkpoints(self, body: str) -> list[dict[str, Any]]:
        checkpoints: list[dict[str, Any]] = []
        # Split por checkpoint headers
        parts = self._CHECKPOINT_RE.split(body)
        if len(parts) <= 1:
            return checkpoints

        # parts[0] é conteúdo antes do primeiro checkpoint
        for i in range(1, len(parts), 2):
            cp_title = parts[i].strip().lstrip("# ").strip()
            cp_body = parts[i + 1] if i + 1 < len(parts) else ""
            tasks = self._extract_tasks_from_checkpoint(cp_body)
            checkpoints.append({"title": cp_title, "tasks": tasks})
        return checkpoints

    def _extract_tasks_from_checkpoint(self, cp_body: str) -> list[dict[str, Any]]:
        tasks: list[dict[str, Any]] = []
        # Cada task começa com - [ ] ou - [x]
        lines = cp_body.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            m = self._CHECKBOX_RE.match(line)
            if not m:
                i += 1
                continue
            checked = m.group(1).lower() == "x"
            title = m.group(2).strip()
            details: list[str] = []
            req_refs: list[str] = []
            boundary: str | None = None
            observable: str | None = None

            # Ler linhas seguintes indentadas (detalhes da task)
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip() or next_line.startswith("  ") or next_line.startswith("\t"):
                    # Detalhe indentado
                    stripped = next_line.strip()
                    if stripped.startswith("- "):
                        details.append(stripped[2:].strip())
                    # Requirement refs
                    ref_m = self._REQ_REFS_RE.search(stripped)
                    if ref_m:
                        req_refs = [r.strip() for r in ref_m.group(1).split(",")]
                    # Boundary
                    b_m = self._BOUNDARY_RE.search(stripped)
                    if b_m:
                        boundary = b_m.group(1).strip()
                    # Observable
                    o_m = self._OBSERVABLE_RE.search(stripped)
                    if o_m:
                        observable = o_m.group(1).strip()
                    j += 1
                elif self._CHECKBOX_RE.match(next_line) or self._CHECKPOINT_RE.match(next_line):
                    break
                else:
                    j += 1
            tasks.append({
                "id": f"T{len(tasks)+1}",
                "title": title,
                "checked": checked,
                "details": details,
                "requirement_refs": req_refs,
                "boundary": boundary,
                "observable": observable,
            })
            i = j
        return tasks

    def _md_to_html(self, md: str) -> str:
        import markdown

        md_converter = markdown.Markdown(
            extensions=["extra", "tables", "fenced_code", "sane_lists"]
        )
        return md_converter.convert(md)

"""Schemas pydantic para datasets de HTML artifacts.

Unifica os contratos de dados entre:
- Templates Thariq (visuais editoriais)
- gen_artifact.py (funcionais: table, report, interactive)
- Templates de domínio trading (backtest, risk, signal, regime)
"""
from __future__ import annotations

import sys
from pathlib import Path
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


# ============================================================================
# Core Schemas (gen_artifact heritage)
# ============================================================================

class TableColumn(BaseModel):
    key: str
    label: str
    type: Literal["str", "num", "int", "float"] = "str"


class TableDataset(BaseModel):
    title: str
    subtitle: str | None = None
    columns: list[TableColumn]
    rows: list[dict[str, Any]]

    @model_validator(mode="after")
    def check_rows_have_keys(self) -> "TableDataset":
        keys = {c.key for c in self.columns}
        for i, row in enumerate(self.rows):
            missing = keys - set(row.keys())
            if missing:
                raise ValueError(
                    f"Row {i} missing required keys: {missing}"
                )
        return self


class ReportSection(BaseModel):
    heading: str
    body: str
    alert: Literal["info", "warn", "err", "ok"] | None = None


class ReportDataset(BaseModel):
    title: str
    subtitle: str | None = None
    sections: list[ReportSection]


class InteractiveItem(BaseModel):
    id: str
    label: str
    type: Literal[
        "decision",
        "checkbox",
        "select",
        "multiselect",
        "text",
        "textarea",
        "slider",
        "rating",
        "tags",
        "code",
    ] = "decision"
    details_md: str | None = None
    options: list[dict[str, str]] | None = None
    checkbox_label: str | None = None
    placeholder: str | None = None
    allow_note: bool = False
    min: float | None = None
    max: float | None = None
    step: float | None = None
    rating_max: int = 5
    code_lang: str | None = None
    required: bool = False
    validation_regex: str | None = None


class InteractiveDataset(BaseModel):
    title: str
    subtitle: str | None = None
    context: str | None = None
    items: list[InteractiveItem]


# ============================================================================
# Thariq Adapter Schema
# ============================================================================

class ThariqSection(BaseModel):
    title: str
    content: str
    metadata: dict[str, Any] | None = None


class ThariqDataset(BaseModel):
    template_id: str = Field(default="", pattern=r"^\d{2}$|^$")
    title: str
    subtitle: str | None = None
    brand: str = "Project"
    sections: list[ThariqSection] | None = None
    data: dict[str, Any] | None = None


# ============================================================================
# Trading Domain Schemas
# ============================================================================

class BacktestResult(BaseModel):
    name: str
    equity_curve: list[float]
    drawdown_curve: list[float]
    trades: int
    win_rate: float
    sharpe: float | None = None
    sortino: float | None = None
    calmar: float | None = None
    max_dd_pct: float
    pnl_total: float


class BacktestDataset(BaseModel):
    title: str = "Comparativo de Backtests"
    subtitle: str | None = None
    strategies: list[BacktestResult]
    benchmark: BacktestResult | None = None


class RiskExposure(BaseModel):
    symbol: str
    notional: float
    var_95: float
    var_99: float
    kelly_fraction: float


class RiskDataset(BaseModel):
    title: str = "Dashboard de Risco"
    subtitle: str | None = None
    exposures: list[RiskExposure]
    correlation_matrix: dict[str, dict[str, float]] | None = None
    stress_scenarios: list[dict[str, Any]] | None = None


class SignalRecord(BaseModel):
    id: str
    timestamp: str
    symbol: str
    side: Literal["buy", "sell"]
    signal_price: float
    exec_price: float | None = None
    slippage_bps: float | None = None
    filled: bool = False
    pnl: float | None = None


class SignalDataset(BaseModel):
    title: str = "Auditoria de Sinais"
    subtitle: str | None = None
    signals: list[SignalRecord]


class RegimeSegment(BaseModel):
    label: str
    start: str
    end: str
    regime: Literal["trending", "ranging", "high-vol", "low-liquidity", "normal"]
    stats: dict[str, float] | None = None


class RegimeDataset(BaseModel):
    title: str = "Regimes de Mercado"
    subtitle: str | None = None
    regimes: list[RegimeSegment]


# ============================================================================
# Spec Schemas
# ============================================================================

class SpecRequirement(BaseModel):
    id: str
    title: str
    description: str
    criteria: list[str]
    status: Literal["draft", "review", "approved", "rejected"] = "draft"


class SpecTask(BaseModel):
    id: str
    title: str
    checked: bool = False
    details: list[str] = []
    requirement_refs: list[str] = []
    boundary: str | None = None
    observable: str | None = None


class SpecCheckpoint(BaseModel):
    title: str
    tasks: list[SpecTask]


class SpecDataset(BaseModel):
    spec_name: str
    version: str
    source_path: str = ""
    type: Literal["requirements", "design", "tasks", "generic"]
    frontmatter: dict[str, Any]
    sections: list[dict[str, Any]]
    requirements: list[SpecRequirement] | None = None
    checkpoints: list[SpecCheckpoint] | None = None
    coverage_matrix: list[dict[str, Any]] | None = None
    prework: list[dict[str, Any]] | None = None
    raw_html: str = ""


# ============================================================================
# Union type para dispatch
# ============================================================================

ArtifactDataset = (
    TableDataset
    | ReportDataset
    | InteractiveDataset
    | ThariqDataset
    | BacktestDataset
    | RiskDataset
    | SignalDataset
    | RegimeDataset
    | SpecDataset
)

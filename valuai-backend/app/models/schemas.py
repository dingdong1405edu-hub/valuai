"""Pydantic v2 schemas for API request/response."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


# ─── Generic API envelope ─────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ResponseMeta(BaseModel):
    model_used: str = ""
    tokens: int = 0


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    @classmethod
    def ok(cls, data: T, model_used: str = "", tokens: int = 0) -> "APIResponse[T]":
        return cls(success=True, data=data, meta=ResponseMeta(model_used=model_used, tokens=tokens))

    @classmethod
    def fail(cls, code: str, message: str, details: dict = {}) -> "APIResponse[None]":
        return cls(success=False, error=ErrorDetail(code=code, message=message, details=details))


# ─── Company ──────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    metadata: dict[str, Any] = {}


class CompanyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime


# ─── Document ─────────────────────────────────────────────────────────────────

VALID_DOC_TYPES = {
    "financial_report",
    "catalogue",
    "business_plan",
    "cv",
    "capability_profile",
    "web_content",
    "crm",
    "accounting",
    "erp",
}


class DocumentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    company_id: str
    type: str
    file_url: Optional[str] = None
    source_url: Optional[str] = None
    status: str
    mime_type: Optional[str] = None
    created_at: datetime


class CrawlRequest(BaseModel):
    company_id: str
    url: str
    source_type: str = Field(default="website", pattern="^(website|fanpage|linkedin|other)$")


# ─── Extraction ───────────────────────────────────────────────────────────────

class FinancialData(BaseModel):
    """Structured financial data extracted by Groq."""
    revenue: Optional[float] = None
    profit: Optional[float] = None
    ebitda: Optional[float] = None
    total_assets: Optional[float] = None
    debt: Optional[float] = None
    employees: Optional[int] = None
    founding_year: Optional[int] = None
    industry: Optional[str] = None
    products: list[str] = []
    markets: list[str] = []
    growth_rate: Optional[float] = None
    currency: str = "VND"
    fiscal_year: Optional[int] = None


class QualitativeData(BaseModel):
    """Qualitative business data extracted by Groq."""
    team_strength: Optional[str] = None
    product_uniqueness: Optional[str] = None
    market_size: Optional[str] = None
    competitive_moat: Optional[str] = None
    customer_traction: Optional[str] = None
    legal_status: Optional[str] = None
    key_risks: list[str] = []
    strategic_plans: list[str] = []


# ─── Valuation ────────────────────────────────────────────────────────────────

class ValuationRunRequest(BaseModel):
    company_id: str
    wacc: float = Field(default=0.15, ge=0.05, le=0.40, description="WACC for DCF (default 15% for VN SMEs)")
    private_discount: float = Field(default=0.25, ge=0.10, le=0.50, description="Private company illiquidity discount")


class ScorecardBreakdown(BaseModel):
    score: int = Field(..., ge=0, le=10)
    reason: str


class ValuationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    company_id: str
    status: str

    dcf_value: Optional[float] = None
    dcf_assumptions: dict = {}
    dcf_confidence: float = 0

    comparable_value: Optional[float] = None
    comparable_peers: list = []
    comparable_confidence: float = 0

    scorecard_value: Optional[float] = None
    scorecard_breakdown: dict = {}
    scorecard_total: float = 0
    scorecard_confidence: float = 0

    final_range_min: Optional[float] = None
    final_range_mid: Optional[float] = None
    final_range_max: Optional[float] = None
    currency: str = "VND"

    strengths: list[str] = []
    weaknesses: list[str] = []
    opportunities: list[str] = []
    threats: list[str] = []
    recommendations: list[str] = []
    report_text: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: int = 0
    process_log: dict = {}

    created_at: datetime

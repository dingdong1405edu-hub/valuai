"""SQLAlchemy ORM models — mirrors migrations/001_init.sql."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    ARRAY,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    extractions: Mapped[list["Extraction"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    valuations: Mapped[list["Valuation"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_url: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    parsed_text: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error_msg: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="documents")
    extractions: Mapped[list["Extraction"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    embeddings: Mapped[list["Embedding"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="extractions")
    company: Mapped["Company"] = relationship(back_populates="extractions")


class Valuation(Base):
    __tablename__ = "valuations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")

    dcf_value: Mapped[float | None] = mapped_column(Numeric(20, 2))
    dcf_assumptions: Mapped[dict] = mapped_column(JSONB, default=dict)
    dcf_confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0)

    comparable_value: Mapped[float | None] = mapped_column(Numeric(20, 2))
    comparable_peers: Mapped[list] = mapped_column(JSONB, default=list)
    comparable_confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0)

    scorecard_value: Mapped[float | None] = mapped_column(Numeric(20, 2))
    scorecard_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    scorecard_total: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    scorecard_confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0)

    final_range_min: Mapped[float | None] = mapped_column(Numeric(20, 2))
    final_range_mid: Mapped[float | None] = mapped_column(Numeric(20, 2))
    final_range_max: Mapped[float | None] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3), default="VND")

    strengths: Mapped[list] = mapped_column(JSONB, default=list)
    weaknesses: Mapped[list] = mapped_column(JSONB, default=list)
    opportunities: Mapped[list] = mapped_column(JSONB, default=list)
    threats: Mapped[list] = mapped_column(JSONB, default=list)
    recommendations: Mapped[list] = mapped_column(JSONB, default=list)
    report_text: Mapped[str | None] = mapped_column(Text)

    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text)
    process_log: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company: Mapped["Company"] = relationship(back_populates="valuations")


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Vector column — requires pgvector extension
    embedding: Mapped[Any | None] = mapped_column(Vector(768) if PGVECTOR_AVAILABLE else Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="embeddings")

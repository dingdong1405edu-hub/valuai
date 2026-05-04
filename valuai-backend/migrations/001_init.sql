-- ValuAI Database Schema for Railway PostgreSQL
-- Run this once against your Railway PostgreSQL instance

-- Enable pgvector extension (Railway PostgreSQL supports this)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────────
-- companies
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    industry    VARCHAR(100),
    founded_year INT,
    employee_count INT,
    description TEXT,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- documents — one row per uploaded file or crawled URL
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL,
                -- financial_report | catalogue | business_plan | cv
                -- capability_profile | web_content | crm | accounting | erp
    file_url    TEXT,           -- local path or storage URL
    source_url  TEXT,           -- for web_content type
    parsed_text TEXT,           -- markdown output from Gemini/Firecrawl
    mime_type   VARCHAR(100),
    file_size   BIGINT,
    status      VARCHAR(30) NOT NULL DEFAULT 'pending',
                -- pending | parsing | parsed | failed
    error_msg   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- extractions — structured JSON extracted from documents
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS extractions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    data        JSONB NOT NULL DEFAULT '{}',
    model_used  VARCHAR(100),
    tokens_used INT DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- valuations — valuation results per company
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS valuations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    status              VARCHAR(30) NOT NULL DEFAULT 'pending',
                        -- pending | running | completed | failed
    -- Individual method results
    dcf_value           NUMERIC(20, 2),
    dcf_assumptions     JSONB DEFAULT '{}',
    dcf_confidence      NUMERIC(3, 2) DEFAULT 0,
    comparable_value    NUMERIC(20, 2),
    comparable_peers    JSONB DEFAULT '[]',
    comparable_confidence NUMERIC(3, 2) DEFAULT 0,
    scorecard_value     NUMERIC(20, 2),
    scorecard_breakdown JSONB DEFAULT '{}',
    scorecard_total     NUMERIC(5, 2) DEFAULT 0,
    scorecard_confidence NUMERIC(3, 2) DEFAULT 0,
    -- Synthesized final range
    final_range_min     NUMERIC(20, 2),
    final_range_mid     NUMERIC(20, 2),
    final_range_max     NUMERIC(20, 2),
    currency            CHAR(3) NOT NULL DEFAULT 'VND',
    -- Qualitative output
    strengths           JSONB DEFAULT '[]',
    weaknesses          JSONB DEFAULT '[]',
    opportunities       JSONB DEFAULT '[]',
    threats             JSONB DEFAULT '[]',
    recommendations     JSONB DEFAULT '[]',
    report_text         TEXT,   -- full narrative from Gemini
    -- Meta
    model_used          VARCHAR(100),
    tokens_used         INT DEFAULT 0,
    error_msg           TEXT,
    process_log         JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────
-- embeddings — pgvector store for RAG
-- text-embedding-004 = 768 dimensions
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS embeddings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(768),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- IVFFlat index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS embeddings_embedding_idx
    ON embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

-- Regular indexes for foreign key lookups
CREATE INDEX IF NOT EXISTS documents_company_id_idx ON documents(company_id);
CREATE INDEX IF NOT EXISTS extractions_company_id_idx ON extractions(company_id);
CREATE INDEX IF NOT EXISTS extractions_document_id_idx ON extractions(document_id);
CREATE INDEX IF NOT EXISTS valuations_company_id_idx ON valuations(company_id);
CREATE INDEX IF NOT EXISTS embeddings_company_id_idx ON embeddings(company_id);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER valuations_updated_at
    BEFORE UPDATE ON valuations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

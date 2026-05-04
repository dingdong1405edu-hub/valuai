# ValuAI — AI-Powered Business Valuation Platform

## 1. Project Overview

ValuAI is an AI-driven business valuation platform for Vietnamese SMEs. It ingests business
documents, runs three parallel valuation methods, synthesizes a confidence-weighted final
range, and produces a SWOT report with strategic recommendations.

**Target users:** M&A advisors, investment funds, banks, business owners.

**Supported input types:**
| Type | Format | Parser |
|------|---------|--------|
| Financial report | PDF / Excel / image | Gemini Vision / openpyxl |
| Company website / fanpage | URL | Firecrawl |
| Catalogue / brochure | PDF / image | Gemini Vision |
| Capability document | PDF | Gemini Vision |
| Business plan | PDF | Gemini Vision |
| Owner CV | PDF | Gemini Vision |

**Core pipeline:**
```
Upload (file/URL) → Parse (Gemini/openpyxl) → Extract (Groq JSON + regex fallback)
                                                      ↓
                                          Embed (Gemini 768-dim) → pgvector RAG
                                                      ↓
                                 DCF + Comparable + Scorecard (parallel)
                                                      ↓
                                    Synthesis (Gemini) → SWOT + Report
```

---

## 2. Project Structure (actual files)

```
valuai-backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS, routers, startup
│   ├── api/routes/
│   │   ├── companies.py           # CRUD: POST/GET/DELETE /api/companies
│   │   ├── documents.py           # Upload/crawl: POST /api/documents/upload|crawl
│   │   └── valuations.py          # Run + fetch: POST /api/valuations/run
│   ├── core/
│   │   ├── config.py              # Pydantic Settings (all env vars)
│   │   └── ai_clients.py          # Groq + Gemini wrappers with retry
│   ├── db/
│   │   ├── database.py            # Async SQLAlchemy engine, get_db()
│   │   └── models.py              # ORM: Company, Document, Extraction, Valuation, Embedding
│   ├── ingestion/
│   │   ├── parser.py              # PDF/image → text via Gemini; Excel → markdown
│   │   ├── extractor.py           # Groq JSON extraction + regex fallback
│   │   ├── embedder.py            # Chunk → embed (768-dim) → pgvector
│   │   └── crawler.py             # Firecrawl web scraping
│   ├── valuation/
│   │   ├── orchestrator.py        # Main pipeline: aggregate → DCF+Comp+Score → synthesize
│   │   ├── dcf.py                 # DCF: Gemini provides 4 params, Python does math
│   │   ├── comparable.py          # Market multiples: Fireant or fallback industry table
│   │   └── scorecard.py           # 10-criterion scoring via Groq
│   ├── models/schemas.py          # Pydantic schemas: FinancialData, QualitativeData, etc.
│   └── report/generator.py        # PDF report via fpdf2
├── migrations/001_init.sql        # PostgreSQL schema (5 tables + pgvector)
├── requirements.txt
├── Dockerfile
└── railway.toml
```

---

## 3. Tech Stack

| Component | Library | Notes |
|---|---|---|
| Framework | FastAPI 0.115 | Async, background tasks |
| Runtime | Python 3.12 | |
| ORM / DB driver | SQLAlchemy 2.0 async + asyncpg | |
| Database | PostgreSQL (Railway) + pgvector | |
| AI fast extraction | Groq `llama-3.3-70b-versatile` | JSON extraction, scorecard |
| AI reasoning | Groq `deepseek-r1-distill-llama-70b` | Text reasoning |
| AI deep analysis | Gemini `gemini-2.5-flash` | PDF parse, DCF params, synthesis |
| Embeddings | Google `gemini-embedding-001` | 768-dim vectors |
| Web scraping | Firecrawl | URL/fanpage → markdown |
| Market data | Fireant REST API | VN listed company multiples |
| PDF output | fpdf2 | Valuation report |
| Retry logic | tenacity | All AI client calls |

---

## 4. Environment Variables (`.env`)

```dotenv
APP_ENV=development
APP_PORT=8000
FRONTEND_URL=http://localhost:3000

DATABASE_PUBLIC_URL=postgresql://...   # Railway external URL
DATABASE_URL=postgresql://...          # Railway internal URL

GROQ_API_KEY=gsk_...
GROQ_MODEL=deepseek-r1-distill-llama-70b        # reasoning / text tasks
GROQ_EXTRACTION_MODEL=llama-3.3-70b-versatile   # JSON extraction / scorecard

GOOGLE_API_KEY=AIza...
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=models/gemini-embedding-001

FIRECRAWL_API_KEY=fc-...     # optional
FIREANT_TOKEN=...             # optional — comparable uses fallback if absent
```

---

## 5. Valuation Architecture

### 5.1 Three Parallel Methods

**DCF — `valuation/dcf.py`**
- Gemini receives company summary; returns ONE JSON with 4 numbers:
  `base_revenue_billions`, `annual_growth_rate`, `ebitda_margin`, `wacc`
- Python calculates 3 scenarios (conservative × 0.6, base, optimistic × 1.5)
- Gordon Growth terminal value, 5-year projection
- If revenue=0: estimates from `employees × industry_rev_per_emp`
- Confidence: 0.20 (fallback) → 0.80 (full data)

**Comparable — `valuation/comparable.py`**
- Tries Fireant API for listed Vietnamese peer multiples (P/E, EV/EBITDA)
- Falls back to hardcoded `INDUSTRY_FALLBACK` table (18 industries)
- Applies 25% private company illiquidity discount
- If revenue=0: estimates from employees like DCF
- Confidence: 0.35 (fallback) → 0.80 (5+ peers from Fireant)

**Scorecard — `valuation/scorecard.py`**
- Groq scores 10 criteria (0-10 each) from financial + qualitative context
- Weighted total score → revenue multiplier (0.4×–3.0×)
- If revenue=0: estimates from employees × industry rate
- Default score for missing data = 4 (neutral — no penalty for missing docs)
- Confidence: 0.35 (min) → 0.80 (max, based on data richness)

### 5.2 Synthesis — `valuation/orchestrator.py`

```
weight = max(confidence, 0.10) × BASE_WEIGHT[method]
         (DCF=0.45, Comparable=0.35, Scorecard=0.20)

final_mid = Σ(value_mid × normalized_weight)
final_min = min(all lows) × 0.90
final_max = max(all highs) × 1.10
```

**Key design rule:** No method is excluded. Low confidence = low weight, not zero.
Only methods where `value_mid == 0` are excluded.

### 5.3 Extraction — `ingestion/extractor.py`

Two-stage with fallback:
1. **Groq JSON extraction**: structured prompt with Vietnamese keyword mapping
2. **Regex fallback**: scans for patterns like "doanh thu 45 tỷ", "45,200,000,000 đồng"
3. **Unit normalization**: any monetary value ≥ 1,000,000,000 is divided by 1e9

---

## 6. API Endpoints

```
POST   /api/companies                    Create company
GET    /api/companies/{id}               Get company
GET    /api/companies                    List companies (limit 50)
DELETE /api/companies/{id}               Delete company

POST   /api/documents/upload             Upload file → parse → extract → embed
POST   /api/documents/crawl              Crawl URL → parse → extract → embed
GET    /api/documents/{id}/status        Check document status
GET    /api/documents/company/{id}       List company documents

POST   /api/valuations/run               Start valuation pipeline (background task)
GET    /api/valuations/{id}              Get full valuation results
GET    /api/valuations/{id}/status       Poll status (pending/running/completed/failed)
GET    /api/valuations/company/{id}/latest  Latest valuation for company
POST   /api/valuations/{id}/export       Generate PDF report
```

All responses use `APIResponse[T]` envelope:
```json
{"success": true, "data": {...}, "error": null, "meta": {"request_id": "...", "timestamp": "..."}}
```

---

## 7. Database Schema

```sql
companies   — id, name, industry, founded_year, employee_count, description
documents   — id, company_id, type, file_url, source_url, parsed_text, status
extractions — id, document_id, company_id, data (JSONB), model_used, tokens_used
valuations  — id, company_id, status, dcf_*, comparable_*, scorecard_*, final_range_*, strengths/weaknesses/...
embeddings  — id, document_id, company_id, chunk_index, content, embedding vector(768)
```

pgvector IVFFlat index on `embeddings.embedding` for cosine similarity RAG.

---

## 8. AI Model Routing

| Task | Model | Why |
|---|---|---|
| Parse PDF/image | Gemini Vision | Multimodal, handles scanned docs |
| Extract financial JSON | Groq llama-3.3-70b | Fast, reliable JSON mode |
| Extract qualitative JSON | Groq llama-3.3-70b | Fast structured output |
| Scorecard scoring | Groq llama-3.3-70b | Fast, 10-criterion JSON |
| DCF parameters | Gemini 2.5-flash | Understands Vietnamese context |
| SWOT synthesis | Gemini 2.5-flash | Long-context, coherent prose |
| Embeddings | gemini-embedding-001 | 768-dim, Vietnamese-aware |

**Groq `deepseek-r1`** is used only for free-text reasoning tasks (not JSON extraction) 
because its `<think>` blocks interfere with JSON parsing.

---

## 9. Key Commands

```bash
# Local dev
cd valuai-backend
uvicorn app.main:app --reload --port 8000

# Install dependencies
pip install -r requirements.txt

# Frontend
cd valuai-frontend
npm install && npm run dev

# Run DB migration (Railway)
psql $DATABASE_PUBLIC_URL -f migrations/001_init.sql
```

---

## 10. Known Constraints

- `gemini-embedding-001` outputs **768 dims** — `embeddings` table uses `vector(768)` not 1536
- Gemini SDK is synchronous — all Gemini calls use `asyncio.to_thread()`
- Fireant API requires paid token — comparable uses fallback table if `FIREANT_TOKEN` is unset
- Firecrawl cannot access login-gated Facebook pages — manual text fallback
- WeasyPrint requires Vietnamese fonts in Docker (`fonts-noto-cjk`)
- asyncpg does not support `:param::type` SQL syntax — use SQLAlchemy ORM or `$1::type`

---

## 11. UX Features

### 11.1 Upload Wizard — Per-step Content Hints

Each wizard step (1–8) shows an amber hint box explaining what the document or input
should ideally contain to maximise valuation accuracy. Step 9 shows a numbered "What
the AI will do" list explaining all 6 pipeline stages before the user submits.

Hints are defined in `STEP_HINTS` constant in `valuai-frontend/components/UploadWizard/index.tsx`.

### 11.2 Pipeline Diagram (Results Page)

The `ValuationDashboard` renders a full visual pipeline diagram **below** the Executive
Summary, showing every step the AI performed:

```
[📁 Documents] → [🔍 Parse & Extract]
                        ↓ 3 methods in parallel
        ┌──────────────────────────────────┐
        │ ⚡ asyncio.gather                 │
        │ [📈 DCF] [🏢 Comparable] [⭐ Score] │
        └──────────────────────────────────┘
                        ↓ confidence-weighted blend
              [⚖️ Synthesis: min–mid–max]
                        ↓
              [📝 SWOT + Recommendations]
```

Each node in the diagram shows **real data** from that valuation:
- Documents node: extracted revenue, profit, employees, qualitative fields
- DCF node: Gemini-chosen growth rate, WACC, EBITDA margin + scenario values
- Comparable node: P/E, EV/EBITDA, EV/Revenue multiples used + private discount
- Scorecard node: total score X/10, top 3 criteria with scores
- Synthesis node: normalized weights (e.g. DCF 52%, Comparable 31%, Scorecard 17%)
- SWOT node: count of strengths/weaknesses/opportunities/threats + RAG chunks used

Data flows from `valuation.process_log` (JSONB field, populated by orchestrator) and
`valuation.*` fields directly.

**Migration required for process_log column:**
```bash
psql $DATABASE_PUBLIC_URL -f migrations/002_add_process_log.sql
```

## 12. Debugging Valuation Issues

If valuations return the same fixed number:

1. Check Railway logs for `[EXTRACTOR]` lines:
   ```
   [EXTRACTOR] financial OK — revenue=X, profit=Y, employees=Z
   ```
   If revenue=null and employees=null → extraction failing completely.

2. Check `[ORCHESTRATOR]` lines:
   ```
   [ORCHESTRATOR] method results — DCF=X(conf=0.YY), Comp=X(conf=0.YY), Score=X(conf=0.YY)
   ```
   If all show same value → synthesis is working but upstream is broken.

3. Check `[SCORECARD]` line:
   ```
   [SCORECARD] score=X/10, multiplier=Y×, mid=Z
   ```
   `mid` should vary per company. If always 0.4 → revenue fallback failed.

4. Check `[ORCHESTRATOR] process_log saved` — if missing, orchestrator crashed before step 7.

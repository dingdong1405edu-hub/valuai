# ValuAI — AI-Powered Business Valuation Platform

## 1. Project Overview

ValuAI is an AI-driven business valuation platform built for Vietnamese SMEs. It ingests up to
9 types of business documents and data sources, processes them through a structured pipeline,
and produces a professional valuation report with a price range, SWOT analysis, and strategic
recommendations.

**Target users:** M&A advisors, investment funds, banks, business owners who need fast,
data-backed valuations without engaging a full consulting team.

**9 supported input types:**
| # | Type | Format | Parser |
|---|------|---------|--------|
| 1 | Financial report | PDF / Excel | Gemini Vision / openpyxl |
| 2 | Company website / fanpage | URL | Firecrawl |
| 3 | Catalogue / brochure | PDF / image | Gemini Vision |
| 4 | Capability document | PDF | Gemini Vision |
| 5 | Business plan | PDF | Gemini Vision |
| 6 | Owner CV | PDF | Gemini Vision |
| 7 | CRM export | API / CSV | BaseConnector |
| 8 | Accounting software | API | BaseConnector |
| 9 | ERP system | API | BaseConnector |

**Core flow:**
```
Input (9 types) → Parse → Extract → Normalize → Vector Store
                                                      ↓
                                              AI Engine (DCF + Comparable + Scorecard)
                                                      ↓
                                              Synthesizer → PDF Report
```

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│        Next.js 14 (App Router)  ·  Tailwind CSS  ·  shadcn/ui       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTPS / REST + SSE
┌────────────────────────────▼─────────────────────────────────────────┐
│                           API LAYER                                  │
│               Python FastAPI  ·  Pydantic v2  ·  Celery              │
│  /api/v1/projects  /api/v1/ingest  /api/v1/valuate  /api/v1/reports  │
└──┬───────────────┬──────────────────┬──────────────┬─────────────────┘
   │               │                  │              │
┌──▼────┐     ┌────▼──────┐     ┌─────▼─────┐  ┌────▼────┐
│ Parse │     │  Extract  │     │ Normalize │  │  Store  │
│ Layer │     │  Layer    │     │  Layer    │  │  Layer  │
│       │     │           │     │           │  │         │
│Gemini │     │ Groq      │     │ Pydantic  │  │Supabase │
│Vision │     │ llama-3.3 │     │ schemas   │  │Postgres │
│Firecr │     │ -70b      │     │ Currency  │  │pgvector │
│awl    │     │           │     │ date norm │  │Storage  │
└──┬────┘     └────┬──────┘     └─────┬─────┘  └────┬────┘
   └───────────────┴──────────────────┴──────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                        AI ENGINE LAYER                               │
│                                                                      │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────────┐  │
│  │   DCF Engine   │  │ Comparable Engine│  │  Scorecard Engine   │  │
│  │  Gemini 2.0    │  │  Groq (fast calc)│  │  Groq (scoring)     │  │
│  │  Flash (deep   │  │  Fireant API     │  │  Gemini (synthesis) │  │
│  │  reasoning)    │  │  (VN market data)│  │                     │  │
│  └────────────────┘  └──────────────────┘  └─────────────────────┘  │
│                                                                      │
│              ↓  Synthesizer — Confidence Weighting  ↓               │
│                    Gemini 2.0 Flash (final report)                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                         OUTPUT LAYER                                 │
│       Valuation Range  ·  SWOT  ·  Recommendations  ·  PDF          │
│                      WeasyPrint / Jinja2                             │
└──────────────────────────────────────────────────────────────────────┘

External services:
  Groq API          ←→  Extract Layer + Scorecard + fast calculations
  Google Gemini API ←→  Parse Layer (PDF/image) + deep analysis + final report
  Google Embedding  ←→  Vector Store (text-embedding-004)
  Firecrawl API     ←→  Parse Layer (URL / social pages)
  Fireant API       ←→  Comparable Engine (Vietnamese listed company data)
  Supabase          ←→  Store Layer (PostgreSQL + pgvector + Storage)
```

---

## 3. Tech Stack

### Backend
| Component | Library / Service | Version |
|---|---|---|
| Framework | FastAPI | 0.115.x |
| Runtime | Python | 3.12 |
| Task queue | Celery + Redis | 5.4.x / 7.x |
| Validation | Pydantic | 2.x |
| ORM | SQLAlchemy (async) | 2.x |
| DB driver | asyncpg | 0.29.x |
| Auth | Supabase JWT / python-jose | — |
| AI — fast extraction | Groq SDK (`groq`) | 0.11.x |
| AI — deep analysis | Google Generative AI (`google-generativeai`) | 0.8.x |
| Embeddings | Google `text-embedding-004` via `google-generativeai` | — |
| Document parsing | Gemini Vision (via `google-generativeai`) | — |
| Web scraping | Firecrawl Python SDK (`firecrawl-py`) | latest |
| Market data | Fireant REST API (httpx) | — |
| Vector search | pgvector + supabase-py | latest |
| PDF generation | WeasyPrint + Jinja2 | 62.x / 3.x |
| Excel parsing | openpyxl | 3.x |
| HTTP client | httpx | 0.27.x |
| Environment | python-dotenv | 1.x |
| Logging | structlog | 24.x |
| CORS | FastAPI middleware | built-in |

### Frontend
| Component | Library | Version |
|---|---|---|
| Framework | Next.js (App Router) | 14.x |
| Language | TypeScript | 5.x |
| UI components | shadcn/ui + Radix UI | latest |
| Styling | Tailwind CSS | 3.x |
| State management | Zustand | 4.x |
| Data fetching | TanStack Query v5 | 5.x |
| Forms | React Hook Form + Zod | 7.x / 3.x |
| File upload | react-dropzone | 14.x |
| Charts | Recharts | 2.x |
| PDF viewer | react-pdf | 7.x |
| HTTP client | Axios | 1.x |

### Infrastructure
| Component | Service |
|---|---|
| Database | Supabase (PostgreSQL 15 + pgvector extension) |
| Object storage | Supabase Storage |
| Auth | Supabase Auth (email + Google OAuth) |
| Cache / Queue broker | Redis (Upstash or self-hosted) |
| Backend deployment | Railway / Render / Docker |
| Frontend deployment | Vercel |
| CI/CD | GitHub Actions |

---

## 4. Project Structure

```
valuai/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI app factory, middleware, routers
│   │   ├── config.py                    # Pydantic BaseSettings — all env vars
│   │   ├── dependencies.py              # Shared FastAPI deps (db session, auth)
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── projects.py          # CRUD for valuation projects
│   │   │       ├── ingest.py            # Upload files / add URLs / connect APIs
│   │   │       ├── valuate.py           # Trigger valuation pipeline
│   │   │       └── reports.py           # Fetch & download PDF reports
│   │   │
│   │   ├── models/                      # SQLAlchemy ORM models
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── valuation.py
│   │   │   └── report.py
│   │   │
│   │   ├── schemas/                     # Pydantic request / response schemas
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── valuation.py
│   │   │   ├── financial.py             # NormalizedFinancials, ValuationResult
│   │   │   └── response.py             # APIResponse[T] generic envelope
│   │   │
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py          # Coordinates full pipeline run per project
│   │   │   │
│   │   │   ├── parse/
│   │   │   │   ├── gemini_parser.py     # PDF/image → text via Gemini Vision
│   │   │   │   ├── firecrawl_scraper.py # URL / fanpage → markdown via Firecrawl
│   │   │   │   └── excel_parser.py      # .xlsx / .csv → structured rows via openpyxl
│   │   │   │
│   │   │   ├── extract/
│   │   │   │   ├── financial_extractor.py   # Groq: text → NormalizedFinancials JSON
│   │   │   │   ├── business_extractor.py    # Groq: text → BusinessProfile JSON
│   │   │   │   ├── owner_extractor.py       # Groq: CV text → OwnerProfile JSON
│   │   │   │   └── prompts/                 # All prompt templates as .txt files
│   │   │   │       ├── financial_extraction.txt
│   │   │   │       ├── business_extraction.txt
│   │   │   │       └── owner_extraction.txt
│   │   │   │
│   │   │   ├── normalize/
│   │   │   │   ├── financial_normalizer.py  # Currency → VND, fiscal year alignment
│   │   │   │   └── schema_validator.py      # Pydantic validation pass
│   │   │   │
│   │   │   └── store/
│   │   │       ├── vector_store.py          # Chunk → embed (Google) → upsert pgvector
│   │   │       └── db_writer.py             # Persist normalized data to PostgreSQL
│   │   │
│   │   ├── valuation/
│   │   │   ├── __init__.py
│   │   │   ├── dcf.py                   # DCF — Gemini for scenario reasoning
│   │   │   ├── comparable.py            # Market multiples — Groq + Fireant data
│   │   │   ├── scorecard.py             # Qualitative scoring — Groq
│   │   │   └── synthesizer.py           # Confidence weighting + Gemini final narrative
│   │   │
│   │   ├── integrations/
│   │   │   ├── groq_client.py           # Groq SDK wrapper (llama-3.3-70b-versatile)
│   │   │   ├── gemini_client.py         # Google Generative AI wrapper (gemini-2.0-flash)
│   │   │   ├── embedding_client.py      # Google text-embedding-004 wrapper
│   │   │   ├── firecrawl_client.py      # Firecrawl SDK wrapper
│   │   │   ├── fireant_client.py        # Fireant REST API wrapper
│   │   │   ├── supabase_client.py       # Supabase client singleton
│   │   │   └── connectors/
│   │   │       ├── base.py              # BaseConnector ABC
│   │   │       ├── misa.py              # MISA accounting connector
│   │   │       ├── fastwork.py          # FastWork CRM connector
│   │   │       └── registry.py          # Connector registry
│   │   │
│   │   ├── report/
│   │   │   ├── generator.py             # Orchestrates report assembly
│   │   │   ├── templates/
│   │   │   │   └── valuation_report.html  # Jinja2 template (bilingual VI/EN)
│   │   │   └── pdf_renderer.py          # WeasyPrint HTML → PDF
│   │   │
│   │   ├── tasks/
│   │   │   ├── celery_app.py            # Celery instance + Redis broker config
│   │   │   ├── ingest_tasks.py          # Async: parse → extract → normalize → store
│   │   │   └── valuation_tasks.py       # Async: DCF + comparable + scorecard + synth
│   │   │
│   │   └── utils/
│   │       ├── logging.py               # structlog setup
│   │       └── exceptions.py            # Typed exception hierarchy
│   │
│   ├── migrations/                      # Alembic migration files
│   ├── tests/
│   │   ├── unit/                        # Mock all external APIs
│   │   └── integration/                 # Hit local Supabase instance
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                     # Dashboard / landing
│   │   ├── projects/
│   │   │   ├── page.tsx                 # Projects list
│   │   │   ├── new/page.tsx             # Create project + upload wizard
│   │   │   └── [id]/
│   │   │       ├── page.tsx             # Project detail + pipeline status
│   │   │       ├── ingest/page.tsx      # Data sources management
│   │   │       └── report/page.tsx      # Valuation report viewer
│   │   └── api/                         # Next.js route handlers (BFF)
│   │
│   ├── components/
│   │   ├── ui/                          # shadcn/ui primitives
│   │   ├── upload/                      # Dropzone, URL input, API connector wizard
│   │   ├── valuation/                   # Range bar, method breakdown, SWOT card
│   │   └── report/                      # Report section previews
│   │
│   ├── lib/
│   │   ├── api.ts                       # Axios instance + auth interceptors
│   │   ├── supabase.ts                  # Supabase browser client
│   │   └── utils.ts
│   │
│   ├── store/                           # Zustand stores
│   ├── types/                           # Shared TypeScript types
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
│
├── supabase/
│   ├── migrations/                      # SQL migration files
│   └── seed.sql
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
│
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

---

## 5. Key Commands

### Local Development (Docker Compose)
```bash
# Start all services (postgres + pgvector, redis, backend, frontend)
docker compose up --build

# Start only infrastructure, run services manually
docker compose up postgres redis -d
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

### Backend
```bash
cd backend

# Install all dependencies (including dev extras)
pip install -e ".[dev]"

# Run dev server with hot reload
uvicorn app.main:app --reload --port 8000

# Run Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Run Celery beat scheduler (if needed for periodic tasks)
celery -A app.tasks.celery_app beat --loglevel=info

# Run tests
pytest tests/ -v
pytest tests/unit/ -v --no-header
pytest tests/integration/ -v -m integration

# Type check
mypy app/

# Lint + format
ruff check app/
ruff format app/

# DB migrations (Alembic)
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1
```

### Frontend
```bash
cd frontend

npm install
npm run dev          # http://localhost:3000
npm run build
npm run start
npm run lint
npm run type-check   # tsc --noEmit
```

### Supabase (local dev)
```bash
supabase start
supabase db reset
supabase migration new <migration_name>
supabase db push
supabase stop
```

---

## 6. Environment Variables

Copy `.env.example` to `.env`. All variables are required unless marked optional.

### Backend `.env`
```dotenv
# ── App ──────────────────────────────────────────────────────────────
APP_ENV=development                    # development | staging | production
SECRET_KEY=change-me-in-production
ALLOWED_ORIGINS=http://localhost:3000

# ── Database ─────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/valuai
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...       # server-side only — never expose to client

# ── Redis / Celery ───────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Groq (fast extraction & scoring) ────────────────────────────────
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_MAX_TOKENS=8192

# ── Google AI (Gemini + Embeddings) ─────────────────────────────────
GOOGLE_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash
GEMINI_MAX_TOKENS=8192
EMBEDDING_MODEL=text-embedding-004

# ── Firecrawl (web scraping) ─────────────────────────────────────────
FIRECRAWL_API_KEY=fc-...

# ── Fireant (Vietnamese market data) ────────────────────────────────
FIREANT_API_TOKEN=...
FIREANT_BASE_URL=https://restv2.fireant.vn

# ── Supabase Storage ─────────────────────────────────────────────────
SUPABASE_STORAGE_BUCKET=valuai-documents

# ── Report output ────────────────────────────────────────────────────
REPORT_OUTPUT_DIR=/tmp/valuai_reports
```

### Frontend `.env.local`
```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## 7. API Integrations

### 7.1 Groq API — `app/integrations/groq_client.py`

Model: `llama-3.3-70b-versatile`. Use for: fast structured extraction, scorecard scoring,
comparable calculations, short summaries. Always request JSON output.

```python
from groq import AsyncGroq
from app.config import settings

_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def chat_json(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096,
) -> dict:
    """Call Groq and return parsed JSON. Raises ValueError if response is not valid JSON."""
    response = await _client.chat.completions.create(
        model=settings.GROQ_MODEL,           # "llama-3.3-70b-versatile"
        max_tokens=max_tokens,
        temperature=0.0,                      # deterministic for extraction
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )
    import json
    return json.loads(response.choices[0].message.content)

async def chat_text(system_prompt: str, user_message: str) -> str:
    """Call Groq and return plain text (for summaries, short analyses)."""
    response = await _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        max_tokens=2048,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )
    return response.choices[0].message.content
```

Log `response.usage.prompt_tokens`, `response.usage.completion_tokens` for every call.

---

### 7.2 Google Gemini API — `app/integrations/gemini_client.py`

Model: `gemini-2.0-flash`. Use for: reading PDFs / images directly, deep reasoning on long
documents, final report synthesis, DCF scenario analysis.

```python
import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)

_model = genai.GenerativeModel(
    model_name=settings.GEMINI_MODEL,         # "gemini-2.0-flash"
    generation_config={
        "temperature": 0.0,
        "max_output_tokens": settings.GEMINI_MAX_TOKENS,
        "response_mime_type": "application/json",  # for JSON extraction calls
    },
)

async def extract_from_pdf(file_bytes: bytes, prompt: str) -> dict:
    """Upload PDF bytes and extract structured data via Gemini Vision."""
    import json, asyncio
    from google.generativeai.types import content_types

    part = content_types.to_part({"mime_type": "application/pdf", "data": file_bytes})
    response = await asyncio.to_thread(
        _model.generate_content,
        [part, prompt],
    )
    return json.loads(response.text)

async def extract_from_image(image_bytes: bytes, mime_type: str, prompt: str) -> dict:
    """Extract structured data from an image (PNG/JPG/WEBP)."""
    import json, asyncio
    from google.generativeai.types import content_types

    part = content_types.to_part({"mime_type": mime_type, "data": image_bytes})
    response = await asyncio.to_thread(
        _model.generate_content,
        [part, prompt],
    )
    return json.loads(response.text)

async def analyze_text(prompt: str, context: str) -> str:
    """Deep text analysis — returns plain text (for SWOT, recommendations, narrative)."""
    import asyncio

    text_model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        generation_config={"temperature": 0.4, "max_output_tokens": 8192},
    )
    response = await asyncio.to_thread(
        text_model.generate_content,
        f"{prompt}\n\n<context>\n{context}\n</context>",
    )
    return response.text
```

---

### 7.3 Google Embeddings — `app/integrations/embedding_client.py`

Model: `text-embedding-004`. Produces 768-dimensional vectors. Used for chunking documents
into pgvector for RAG retrieval during valuation.

```python
import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of 768-dim float vectors."""
    result = genai.embed_content(
        model=settings.EMBEDDING_MODEL,       # "text-embedding-004"
        content=texts,
        task_type="retrieval_document",
    )
    return result["embedding"]

def embed_query(query: str) -> list[float]:
    """Embed a single query string for similarity search."""
    result = genai.embed_content(
        model=settings.EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]
```

Note: `text-embedding-004` outputs 768 dimensions. The `document_chunks` table must use
`vector(768)` — not 1536. Update the SQL schema accordingly.

---

### 7.4 Firecrawl — `app/integrations/firecrawl_client.py`

Used for: company websites, Facebook fanpages, e-commerce storefronts.

```python
from firecrawl import FirecrawlApp
from app.config import settings

_app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

def scrape_url(url: str) -> str:
    """Scrape a single URL and return main content as markdown."""
    result = _app.scrape_url(
        url,
        params={"formats": ["markdown"], "onlyMainContent": True},
    )
    return result.get("markdown", "")

def crawl_site(url: str, max_pages: int = 10) -> list[str]:
    """Crawl an entire site and return list of markdown pages."""
    result = _app.crawl_url(
        url,
        params={"limit": max_pages, "scrapeOptions": {"formats": ["markdown"]}},
    )
    return [page["markdown"] for page in result.get("data", [])]
```

Fallback: if Firecrawl cannot access a page (login-gated Facebook, etc.), store the URL as a
manual-description document and prompt the user to paste key info instead.

---

### 7.5 Fireant API — `app/integrations/fireant_client.py`

Used for: fetching P/E, P/B, EV/EBITDA, EV/Revenue multiples of comparable listed companies
on HOSE, HNX, UPCOM exchanges.

```python
import httpx
from app.config import settings

_HEADERS = {"Authorization": f"Bearer {settings.FIREANT_API_TOKEN}"}
_BASE = settings.FIREANT_BASE_URL  # "https://restv2.fireant.vn"

async def get_fundamentals(symbol: str) -> dict:
    """P/E, P/B, EV/EBITDA, ROE, revenue for one ticker."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/symbols/{symbol}/fundamental",
            headers=_HEADERS, timeout=10.0,
        )
        r.raise_for_status()
        return r.json()

async def get_sector_peers(industry_code: str) -> list[dict]:
    """All listed companies in the same VSIC industry."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/symbols",
            params={"industryCode": industry_code, "exchange": "HOSE,HNX,UPCOM"},
            headers=_HEADERS, timeout=10.0,
        )
        r.raise_for_status()
        return r.json()

async def get_last_price(symbol: str) -> float:
    """Latest market price for a ticker."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/symbols/{symbol}/quote",
            headers=_HEADERS, timeout=10.0,
        )
        r.raise_for_status()
        return r.json()["lastPrice"]
```

Always wrap Fireant calls in `try/except httpx.HTTPError` and re-raise as
`IntegrationError(code="FIREANT_ERROR")`.

---

### 7.6 Supabase — `app/integrations/supabase_client.py`

```python
from supabase import create_client, Client
from app.config import settings
from functools import lru_cache

@lru_cache(maxsize=1)
def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
```

Use `asyncpg` via SQLAlchemy async engine for **all transactional DB operations**.
Use the Supabase Python client **only** for Storage (file upload/download/signed URLs)
and Auth (user management, JWT verification).

**File upload example:**
```python
async def upload_document(project_id: str, filename: str, data: bytes) -> str:
    sb = get_supabase()
    path = f"{project_id}/{filename}"
    sb.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(path, data)
    signed = sb.storage.from_(settings.SUPABASE_STORAGE_BUCKET).create_signed_url(
        path, expires_in=3600
    )
    return signed["signedURL"]
```

---

### 7.7 Third-party Connectors (CRM / Accounting / ERP)

All external data connectors implement the `BaseConnector` ABC:

```python
# app/integrations/connectors/base.py
from abc import ABC, abstractmethod
from datetime import date
from app.schemas.financial import RawFinancialData, RawCustomerRecord

class BaseConnector(ABC):
    @abstractmethod
    async def fetch_financials(
        self, date_range: tuple[date, date]
    ) -> RawFinancialData: ...

    @abstractmethod
    async def fetch_customers(self) -> list[RawCustomerRecord]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

Register connectors in `app/integrations/connectors/registry.py`:
```python
CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "misa":     MisaConnector,
    "fastwork": FastWorkConnector,
    "salesforce": SalesforceConnector,
}
```

---

## 8. Data Models

### PostgreSQL Schema (Supabase)

```sql
-- ─────────────────────────────────────────────────────────────────
-- projects
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    industry    TEXT,          -- VSIC code (e.g. "C10", "G47")
    status      TEXT NOT NULL DEFAULT 'draft',
                               -- draft | ingesting | valuating | completed | failed
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────
-- documents — one row per uploaded file or URL
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE documents (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type         TEXT NOT NULL,
                 -- financial_report | website | catalogue | capability_doc
                 -- business_plan | owner_cv | crm | accounting | erp
    source       TEXT NOT NULL,    -- Supabase Storage path or URL
    status       TEXT NOT NULL DEFAULT 'pending',
                 -- pending | parsing | parsed | extracting | extracted | failed
    parsed_text  TEXT,             -- markdown output from Gemini/Firecrawl
    error        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────
-- financial_snapshots — normalized financials per fiscal year
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE financial_snapshots (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_id       UUID REFERENCES documents(id),
    fiscal_year       INT NOT NULL,
    revenue           NUMERIC(20, 2),
    gross_profit      NUMERIC(20, 2),
    ebitda            NUMERIC(20, 2),
    ebit              NUMERIC(20, 2),
    net_income        NUMERIC(20, 2),
    total_assets      NUMERIC(20, 2),
    total_equity      NUMERIC(20, 2),
    total_debt        NUMERIC(20, 2),
    free_cash_flow    NUMERIC(20, 2),
    currency          CHAR(3) NOT NULL DEFAULT 'VND',
    source_confidence NUMERIC(3, 2),  -- 0.00–1.00 AI extraction confidence
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────
-- business_profiles — qualitative context extracted from docs
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE business_profiles (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    company_name      TEXT,
    founding_year     INT,
    employee_count    INT,
    main_products     TEXT[],
    key_customers     TEXT[],
    competitive_moats TEXT[],
    risks             TEXT[],
    owner_background  TEXT,
    raw_data          JSONB,      -- full Groq-extracted JSON for traceability
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────
-- valuations — one row per method per project run
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE valuations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    method       TEXT NOT NULL,   -- dcf | comparable | scorecard
    value_low    NUMERIC(20, 2) NOT NULL,
    value_mid    NUMERIC(20, 2) NOT NULL,
    value_high   NUMERIC(20, 2) NOT NULL,
    currency     CHAR(3) NOT NULL DEFAULT 'VND',
    confidence   NUMERIC(3, 2),  -- 0.00–1.00
    assumptions  JSONB,           -- method-specific inputs logged here
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────
-- valuation_reports — synthesized final result
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE valuation_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    value_low       NUMERIC(20, 2) NOT NULL,
    value_mid       NUMERIC(20, 2) NOT NULL,
    value_high      NUMERIC(20, 2) NOT NULL,
    currency        CHAR(3) NOT NULL DEFAULT 'VND',
    strengths       TEXT[],
    weaknesses      TEXT[],
    opportunities   TEXT[],
    threats         TEXT[],
    recommendations TEXT[],
    narrative       TEXT,         -- Gemini-generated explanation of the range
    pdf_url         TEXT,         -- Supabase Storage signed URL
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────
-- document_chunks — vector store for RAG
-- NOTE: uses 768 dims (text-embedding-004), NOT 1536
-- ─────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(768),      -- Google text-embedding-004 = 768 dims
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### Key Pydantic Schemas

```python
# app/schemas/financial.py
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal, Any
from uuid import UUID

class NormalizedFinancials(BaseModel):
    fiscal_year:       int
    revenue:           Decimal | None = None
    gross_profit:      Decimal | None = None
    ebitda:            Decimal | None = None
    ebit:              Decimal | None = None
    net_income:        Decimal | None = None
    total_assets:      Decimal | None = None
    total_equity:      Decimal | None = None
    total_debt:        Decimal | None = None
    free_cash_flow:    Decimal | None = None
    currency:          str = "VND"
    source_confidence: float = Field(ge=0.0, le=1.0)

class ValuationResult(BaseModel):
    method:     Literal["dcf", "comparable", "scorecard"]
    value_low:  Decimal
    value_mid:  Decimal
    value_high: Decimal
    currency:   str = "VND"
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: dict[str, Any]

class FinalReport(BaseModel):
    project_id:       UUID
    value_low:        Decimal
    value_mid:        Decimal
    value_high:       Decimal
    currency:         str = "VND"
    strengths:        list[str]
    weaknesses:       list[str]
    opportunities:    list[str]
    threats:          list[str]
    recommendations:  list[str]
    narrative:        str
    method_breakdown: list[ValuationResult]
    pdf_url:          str | None = None
```

---

## 9. Valuation Logic

### 9.1 DCF (Discounted Cash Flow) — `app/valuation/dcf.py`

**Owner:** Gemini 2.0 Flash (needs long-context reasoning across 3–5 years of financial data).

**Inputs:** 3–5 years of historical FCF, revenue growth rate, EBITDA margin, capex ratio.

**Steps:**
1. Gemini reads all `financial_snapshots` + business plan context and generates three growth
   scenarios (conservative / base / optimistic).
2. Project FCF for 5 years under each scenario.
3. Terminal value: `TV = FCF₅ × (1 + g) / (WACC - g)`, long-term `g` = 2–3%.
4. Discount at WACC. For Vietnamese SMEs: WACC = 12–20%, default **15%**.
   Formula: `WACC = Ke × E/(E+D) + Kd × (1 − t) × D/(E+D)`
5. `value_low` = conservative scenario PV; `value_mid` = base; `value_high` = optimistic.

**Confidence scoring:**
- 3+ years audited financials → 0.8–1.0
- 2 years unaudited → 0.5–0.7
- 1 year or estimates only → 0.2–0.4

---

### 9.2 Comparable (Market Multiples) — `app/valuation/comparable.py`

**Owner:** Groq llama-3.3-70b (fast calculation on structured Fireant data).

**Inputs:** Fireant peer data for 5–10 listed companies in the same VSIC industry.

**Steps:**
1. Fetch peer multiples via Fireant: P/E, P/B, EV/Revenue, EV/EBITDA.
2. Compute median and IQR (P25 / P75) for each multiple.
3. Apply median multiple to subject company metric → implied enterprise value.
4. Apply **private company illiquidity discount**: 20–35%, configurable, default **25%**.
5. `value_low` = P25 multiple × metric × (1 − max_discount);
   `value_high` = P75 multiple × metric × (1 − min_discount).

**Confidence scoring:**
- 5+ close-industry peers found → 0.8
- 3–4 peers or adjacent industry → 0.5
- Fewer than 3 peers → 0.3

---

### 9.3 Scorecard — `app/valuation/scorecard.py`

**Owner:** Groq llama-3.3-70b (fast JSON scoring of qualitative factors).

**Purpose:** Qualitative method for SMEs with limited financial history.

**Factors and weights:**
| Factor | Weight |
|---|---|
| Management team quality | 20% |
| Market size & growth | 15% |
| Product / service differentiation | 15% |
| Competitive moat | 15% |
| Customer traction & retention | 15% |
| Operational readiness | 10% |
| Exit potential | 10% |

**Steps:**
1. Groq scores each factor 1–5 from extracted business context, CV, business plan.
   Returns JSON: `{"factor_name": score, ..., "reasoning": "..."}`.
2. Weighted score → valuation multiplier on revenue:
   - Score < 2.0 → 0.5× revenue
   - Score 2.0–3.0 → 0.8× revenue
   - Score 3.0–3.5 → 1.2× revenue
   - Score 3.5–4.0 → 1.8× revenue
   - Score > 4.0 → 2.5× revenue
3. `value_mid` = revenue × multiplier; low = mid × 0.8; high = mid × 1.2.

**Confidence scoring:**
- ≥3 qualitative sources (CV + biz plan + website) → 0.7
- 1–2 sources → 0.5
- No qualitative docs → 0.2

---

### 9.4 Synthesis — `app/valuation/synthesizer.py`

**Owner:** Gemini 2.0 Flash (generates SWOT, narrative, and recommendations).

**Weighting algorithm:**
```python
BASE_WEIGHTS = {"dcf": 0.45, "comparable": 0.35, "scorecard": 0.20}

def synthesize(results: list[ValuationResult]) -> FinalReport:
    # 1. Drop any method with confidence < 0.3
    valid = [r for r in results if r.confidence >= 0.3]

    # 2. Compute raw weights
    raw = {r.method: r.confidence * BASE_WEIGHTS[r.method] for r in valid}
    total = sum(raw.values())

    # 3. Normalize to sum = 1.0
    weights = {m: w / total for m, w in raw.items()}

    # 4. Weighted mid value
    final_mid = sum(
        r.value_mid * Decimal(str(weights[r.method])) for r in valid
    )

    # 5. Conservative range with buffers
    final_low  = min(r.value_low  for r in valid) * Decimal("0.90")
    final_high = max(r.value_high for r in valid) * Decimal("1.10")

    # 6. Gemini generates SWOT + recommendations + narrative
    narrative_data = gemini_client.analyze_text(
        SYNTHESIS_PROMPT,
        context=build_synthesis_context(valid, business_profile),
    )
    ...
```

---

## 10. AI Routing Logic

The platform uses **two AI models** with distinct roles. Never swap their responsibilities.

### Groq `llama-3.3-70b-versatile` — Fast, Cheap, Structured

**Use when:**
- Input is already **plain text** (parsed markdown from Firecrawl, Excel rows, pre-extracted text)
- Task requires **structured JSON output** with a fixed schema (extraction, scoring)
- Task is **short-context** (< 20k tokens)
- Speed matters (real-time extraction, scorecard scoring during pipeline)
- Calculation-heavy tasks (comparable multiples, scorecard multiplier lookup)

**Concrete uses:**
| Task | Function |
|---|---|
| Extract financials from parsed markdown | `financial_extractor.py` |
| Extract business profile from parsed text | `business_extractor.py` |
| Extract owner profile from CV text | `owner_extractor.py` |
| Score scorecard factors (1–5) | `scorecard.py` |
| Calculate comparable multiples | `comparable.py` |
| Short summaries of pipeline steps | any `chat_text()` call |

---

### Gemini `gemini-2.0-flash` — Deep, Multimodal, Long-context

**Use when:**
- Input is a **raw binary file** (PDF bytes, image bytes) that has not been parsed yet
- Task requires **reading visual layout** (financial tables in scanned PDFs, charts, logos)
- Task needs **long-context reasoning** across many pages or multiple documents
- Task is the **final synthesis** step requiring coherent prose output
- Input exceeds **20k tokens** after text extraction

**Concrete uses:**
| Task | Function |
|---|---|
| Parse any PDF document directly | `gemini_parser.py → extract_from_pdf()` |
| Parse scanned images / brochures | `gemini_parser.py → extract_from_image()` |
| DCF scenario generation (reads full 5-year history + business plan) | `dcf.py` |
| Final SWOT analysis | `synthesizer.py` |
| Strategic recommendations (3–5 items) | `synthesizer.py` |
| Valuation narrative explanation | `synthesizer.py` |
| PDF report content generation | `report/generator.py` |

---

### Decision Flowchart

```
Input arrives
     │
     ├── Is it a binary file (PDF / image)?
     │         YES → Gemini Vision (extract_from_pdf / extract_from_image)
     │         NO  ↓
     │
     ├── Is input already plain text or markdown?
     │         YES ↓
     │         │
     │         ├── Task = structured extraction (financials, biz profile, owner)?
     │         │         YES → Groq (chat_json)
     │         │
     │         ├── Task = scorecard scoring or comparable calc?
     │         │         YES → Groq (chat_json)
     │         │
     │         ├── Context > 20k tokens OR task = final synthesis?
     │         │         YES → Gemini (analyze_text)
     │         │
     │         └── Short summary / quick label?
     │                   YES → Groq (chat_text)
     │
     └── (never use Gemini for fast structured extraction from short text — too slow/expensive)
```

---

### Cost & Latency Guidelines

| Model | Typical latency | Cost tier | Max input |
|---|---|---|---|
| Groq llama-3.3-70b | ~1–3 s | Very cheap | 128k tokens |
| Gemini 2.0 Flash | ~3–8 s | Cheap | 1M tokens |

Always prefer Groq for tasks it can handle. Reserve Gemini for tasks that genuinely require
multimodal input or long-context reasoning.

---

## 11. Coding Conventions

### Naming
- **Python:** `snake_case` variables/functions/modules; `PascalCase` classes; `UPPER_SNAKE_CASE` constants.
- **TypeScript:** `camelCase` variables/functions; `PascalCase` components/types/interfaces; `UPPER_SNAKE_CASE` env-derived constants.
- **DB columns:** `snake_case`. Table names: plural (`projects`, `documents`).
- **API routes:** kebab-case segments (`/api/v1/valuation-reports`).

### Error Handling

**Typed exceptions — never raise bare `Exception`:**
```python
# app/utils/exceptions.py
class ValuAIError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message    = message
        self.code       = code
        self.status_code = status_code

class DocumentParseError(ValuAIError): ...  # Gemini Vision failures
class ExtractionError(ValuAIError): ...     # Groq / Gemini extraction failures
class ValuationError(ValuAIError): ...      # DCF / comparable / scorecard failures
class IntegrationError(ValuAIError): ...    # External API failures
```

**External API calls:** Always `try/except` httpx / SDK errors and re-raise as
`IntegrationError` with a service name in the code:
`"GROQ_ERROR"`, `"GEMINI_ERROR"`, `"FIREANT_ERROR"`, `"FIRECRAWL_ERROR"`.

**Celery tasks:** Catch all exceptions → set `status = "failed"` on the document/project
with the error message → re-raise for Celery retry (max **3 retries**, exponential backoff
starting at 60 s).

### Standard API Response Envelope

Every FastAPI endpoint returns:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "request_id": "uuid4",
    "timestamp": "2025-01-01T00:00:00Z"
  }
}
```

On error:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "EXTRACTION_ERROR",
    "message": "Groq failed to parse financial data from document.",
    "details": {}
  },
  "meta": { ... }
}
```

Implement as a Pydantic generic in `app/schemas/response.py`:
```python
from pydantic import BaseModel
from typing import Generic, TypeVar
T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}

class ResponseMeta(BaseModel):
    request_id: str
    timestamp: str

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None
    error: ErrorDetail | None
    meta: ResponseMeta
```

### AI Prompt Conventions
- All prompts live in `app/pipeline/extract/prompts/` as `.txt` files. Never inline prompts
  in Python code.
- All Groq extraction calls must set `response_format={"type": "json_object"}` and return
  a dict matching the target Pydantic schema.
- Include `model_json_schema()` of the target schema inside the system prompt so the model
  knows the exact shape expected.
- Log token usage for every AI call: `prompt_tokens`, `completion_tokens`.

### Logging
- Use `structlog` with JSON output in production, pretty-print in development.
- Always bind `project_id` and `document_id` to the structlog context inside pipeline
  functions.
- Never log raw document text or financial figures at `INFO` level — use `DEBUG` only.

### Testing
- **Unit tests** (`tests/unit/`): mock all external AI and API calls. Test one function at a time.
- **Integration tests** (`tests/integration/`): hit a real local Supabase instance
  (`supabase start`). Mark with `@pytest.mark.integration`.
- Every valuation method must have ≥1 test with known numeric inputs and an expected output
  range.
- Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pyproject.toml`.

---

## 12. Current Status & Next Tasks

### Status: Pre-development — architecture finalized, no code written yet.

### Phase 1 — Foundation
- [ ] Initialize repo: `backend/`, `frontend/`, `supabase/` monorepo
- [ ] `docker-compose.yml`: PostgreSQL 15 + pgvector, Redis
- [ ] Supabase migration files for all 7 tables (Section 8)
- [ ] FastAPI scaffold: `main.py`, `config.py`, exception handlers, response envelope
- [ ] `groq_client.py`: verify `llama-3.3-70b-versatile` with a JSON extraction call
- [ ] `gemini_client.py`: verify `gemini-2.0-flash` with a PDF parse on a sample doc
- [ ] `embedding_client.py`: verify `text-embedding-004` returns 768-dim vectors
- [ ] `firecrawl_client.py`: scrape a sample Vietnamese company website
- [ ] `fireant_client.py`: verify token auth, fetch fundamentals for one symbol

### Phase 2 — Ingestion Pipeline
- [ ] `gemini_parser.py`: PDF/image → text for all 6 document types
- [ ] `firecrawl_scraper.py`: URL/fanpage → markdown
- [ ] `excel_parser.py`: .xlsx → structured rows
- [ ] `financial_extractor.py` (Groq): markdown → `NormalizedFinancials` JSON
- [ ] `business_extractor.py` (Groq): text → `BusinessProfile` JSON
- [ ] `owner_extractor.py` (Groq): CV text → `OwnerProfile` JSON
- [ ] `financial_normalizer.py`: currency → VND, fiscal year alignment
- [ ] `vector_store.py`: chunk → embed (Google) → upsert pgvector
- [ ] Celery tasks: `ingest_tasks.py` wiring full pipeline
- [ ] REST: `POST /ingest`, `GET /ingest/{id}/status`

### Phase 3 — Valuation Engine
- [ ] `dcf.py` (Gemini): scenario modeling, PV calculation
- [ ] `comparable.py` (Groq + Fireant): peer multiples, private discount
- [ ] `scorecard.py` (Groq): factor scoring → multiplier → value range
- [ ] `synthesizer.py` (Gemini): confidence weighting + SWOT + narrative
- [ ] REST: `POST /valuate`, `GET /valuations/{project_id}`

### Phase 4 — Report & Frontend
- [ ] Jinja2 HTML template (bilingual VI/EN), WeasyPrint PDF renderer
- [ ] Next.js: multi-step upload wizard (all 9 input types)
- [ ] Valuation results page: Recharts range bar + method breakdown
- [ ] PDF download via Supabase Storage signed URL

### Phase 5 — Auth, Polish, Deploy
- [ ] Supabase Auth: email + Google OAuth
- [ ] Row-level security policies on all tables
- [ ] GitHub Actions CI: lint + type-check + unit tests
- [ ] Deploy: backend → Railway, frontend → Vercel
- [ ] Load test with k6 (target: 10 concurrent valuations)

### Known Constraints & Gotchas
- `text-embedding-004` outputs **768 dims**, not 1536 — the `document_chunks` table and any
  hardcoded vector dimension must use 768.
- Gemini Vision has a **20 MB file size limit** per request — split large PDFs before upload.
- Firecrawl **cannot access login-gated Facebook pages** — implement a manual text-input
  fallback for fanpages.
- Fireant API **requires a paid plan** for full fundamentals — confirm token scope before
  building the comparable engine.
- WeasyPrint needs **Vietnamese fonts** in Docker — add `fonts-noto-cjk` to the Dockerfile.
- Groq free tier has **rate limits** (requests per minute) — add retry logic with exponential
  backoff in `groq_client.py`.
- Gemini `gemini-2.0-flash` is async via `asyncio.to_thread()` since the SDK is sync —
  keep this pattern consistent across all Gemini calls.

# ValuAI — AI-Powered Business Valuation Platform

AI-driven valuation for Vietnamese SMEs using **Groq** (fast extraction) + **Gemini 2.0 Flash**
(deep analysis) + **Railway PostgreSQL** with **pgvector** for RAG.

---

## Quick Start

### 1. Run the Database Migration

```bash
# Install psql if needed, then run the migration against Railway
psql "postgresql://postgres:khdQsCXZPJuBZWRHXYOJgJtLCRHtAxeN@monorail.proxy.rlwy.net:22150/railway" \
  -f valuai-backend/migrations/001_init.sql
```

### 2. Backend

```bash
cd valuai-backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# .env is pre-configured with Railway credentials
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs
```

### 3. Frontend

```bash
cd valuai-frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. Docker Compose (both services)

```bash
docker compose up --build
```

---

## Architecture

```
Upload Wizard (9 steps)
       ↓
POST /api/documents/upload  →  Gemini Vision (PDF parse)
POST /api/documents/crawl   →  Firecrawl (web scrape)
       ↓ Groq extraction → pgvector embeddings
POST /api/valuations/run
       ↓ asyncio.gather (parallel)
   ┌───┴─────────────────────┬──────────────────────┐
  DCF                   Comparable             Scorecard
 (Gemini)           (Groq + Fireant)           (Groq)
   └───┬─────────────────────┴──────────────────────┘
       ↓ Confidence-weighted synthesis
  Gemini 2.0 Flash → SWOT + Recommendations + Narrative
       ↓
  Results Dashboard + PDF Export
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/companies` | Create company |
| GET  | `/api/companies/{id}` | Get company |
| POST | `/api/documents/upload` | Upload & parse document |
| POST | `/api/documents/crawl` | Crawl URL |
| POST | `/api/valuations/run` | Trigger full valuation |
| GET  | `/api/valuations/{id}` | Get valuation result |
| GET  | `/api/valuations/{id}/status` | Poll status |
| POST | `/api/valuations/{id}/export` | Generate PDF |

Full interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## AI Routing

| Task | Model | Reason |
|------|-------|--------|
| PDF/image parsing | Gemini 2.0 Flash | Multimodal |
| Financial extraction | Groq llama-3.3-70b | Fast + JSON mode |
| Qualitative extraction | Groq llama-3.3-70b | Fast + JSON mode |
| DCF scenario generation | Gemini 2.0 Flash | Long-context reasoning |
| Scorecard scoring | Groq llama-3.3-70b | Fast structured scoring |
| Comparable calc | Groq + Fireant API | Fast math on structured data |
| SWOT + synthesis | Gemini 2.0 Flash | Deep narrative generation |
| Embeddings | Google text-embedding-004 | 768-dim vectors |

---

## Valuation Methods

### DCF (45% base weight)
- 5-year FCF projection via Gemini-generated scenarios
- Gordon Growth Model terminal value (`g = 3%`)
- WACC default: **15%** (Vietnamese SME risk-adjusted)
- Confidence: 0.8 with 3+ years audited data → 0.2 with estimates only

### Comparable (35% base weight)
- Fetches peer multiples from Fireant API (HOSE/HNX/UPCOM)
- Fallback: hardcoded industry medians
- **Private company discount: 25%** (illiquidity)

### Scorecard (20% base weight)
- Groq scores 10 criteria (0-10 each)
- Score → revenue multiplier → enterprise value
- Confidence increases with more qualitative documents

### Synthesis
```
final_weight(method) = confidence × base_weight
final_mid = Σ(method.mid × normalized_weight)
final_min = min(all lows) × 0.90
final_max = max(all highs) × 1.10
```
Methods with confidence < 0.3 are excluded.

---

## Environment Variables

### Backend (`.env`)
```
DATABASE_PUBLIC_URL=postgresql://...   # Railway PostgreSQL
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
FIRECRAWL_API_KEY=fc-...              # Optional
FIREANT_TOKEN=...                     # Optional (uses fallback if missing)
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Project Structure

```
valuai-backend/
├── app/
│   ├── main.py                    # FastAPI app
│   ├── core/
│   │   ├── config.py              # Pydantic settings
│   │   └── ai_clients.py          # Groq + Gemini + Embedding clients
│   ├── ingestion/
│   │   ├── parser.py              # Gemini Vision + openpyxl
│   │   ├── crawler.py             # Firecrawl wrapper
│   │   ├── extractor.py           # Groq JSON extraction
│   │   └── embedder.py            # Google embeddings + pgvector
│   ├── valuation/
│   │   ├── dcf.py                 # DCF with Gemini scenarios
│   │   ├── comparable.py          # Fireant + fallback multiples
│   │   ├── scorecard.py           # Groq 10-factor scoring
│   │   └── orchestrator.py        # Parallel pipeline + synthesis
│   ├── report/
│   │   └── generator.py           # fpdf2 PDF report
│   ├── api/routes/
│   │   ├── companies.py
│   │   ├── documents.py
│   │   └── valuations.py
│   ├── db/
│   │   ├── database.py            # SQLAlchemy async engine
│   │   └── models.py              # ORM models
│   └── models/
│       └── schemas.py             # Pydantic v2 schemas
├── migrations/
│   └── 001_init.sql               # pgvector + all tables
└── requirements.txt

valuai-frontend/
├── app/
│   ├── page.tsx                   # Dashboard
│   ├── upload/page.tsx            # Upload wizard
│   └── results/[id]/page.tsx      # Results dashboard
├── components/
│   ├── UploadWizard/              # 9-step form
│   └── ValuationDashboard/        # Charts + SWOT + Recommendations
└── lib/
    ├── api.ts                     # All API calls
    └── types.ts                   # TypeScript types
```

---

## Development Notes

- **pgvector dims**: `text-embedding-004` returns 768 dimensions (not 1536)
- **Async pattern**: All Gemini calls use `asyncio.to_thread()` (SDK is sync)
- **Retry logic**: All AI + external API calls retry 3× with exponential backoff (tenacity)
- **Parallel valuation**: DCF + Comparable + Scorecard run via `asyncio.gather()`
- **Background tasks**: Valuation pipeline runs as FastAPI BackgroundTask
- **Fallback**: Fireant token optional — uses hardcoded industry P/E table if missing

---

## Deploying to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Link project
railway link

# Deploy backend
cd valuai-backend && railway up

# Deploy frontend
cd valuai-frontend && railway up

# Run migration
railway run psql $DATABASE_URL -f migrations/001_init.sql
```

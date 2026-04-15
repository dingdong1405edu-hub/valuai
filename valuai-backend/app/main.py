"""
ValuAI FastAPI Application
"""

import logging

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import init_db
from app.api.routes import companies, documents, valuations
from app.models.schemas import APIResponse

# ─── Logging setup ────────────────────────────────────────────────────────────

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.DEBUG if settings.is_dev else logging.INFO
    )
)
logging.basicConfig(
    level=logging.DEBUG if settings.is_dev else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ─── App factory ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="ValuAI API",
    description="AI-powered business valuation platform for Vietnamese SMEs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global exception handler ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "details": {},
            },
            "meta": {"model_used": "", "tokens": 0},
        },
    )

# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info(f"[APP] starting — env={settings.APP_ENV}")
    await init_db()
    logger.info("[APP] ready")


@app.on_event("shutdown")
async def shutdown():
    logger.info("[APP] shutting down")

# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(companies.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(valuations.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "valuai-api", "env": settings.APP_ENV}


@app.get("/")
async def root():
    return {"message": "ValuAI API", "docs": "/docs", "version": "1.0.0"}

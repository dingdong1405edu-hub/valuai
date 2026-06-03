"""FastAPI app — orchestrator for ValuAI 9-agent pipeline."""
import asyncio
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    BackgroundTasks, Depends, FastAPI, File, Form, HTTPException,
    Request, UploadFile,
)
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response,
)
from fastapi.staticfiles import StaticFiles

import auth as auth_module
import config_schema as schema
import config_store
import db
from agents.analyzer import analyze
from agents.brand_scraper import scrape_brand
from agents.business_profile import analyze_business
from agents.excel_exporter import export_excel
from agents.explainer_html import render_explainer_html
from agents.explainer_renderer import render_explainer
from agents.extractor import extract
from agents.industry import analyze_industry
from agents.projector import project
from agents.renderer import render_valuation_report
from agents.thesis_writer import write_thesis
from agents.trailer_html import render_trailer_html
from agents.trailer_renderer import render_trailer
from agents.valuation_html import render_valuation_html
from agents.valuator import value
from html_pdf import is_playwright_available, render_html_to_pdf

# ── Directories ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
CONFIG_IMAGES_DIR = UPLOADS_DIR / "config"

for d in [UPLOADS_DIR, OUTPUTS_DIR, CONFIG_IMAGES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Env vars ──────────────────────────────────────────────────────────────────
PAYOS_CLIENT_ID = os.environ.get("PAYOS_CLIENT_ID", "")
PAYOS_API_KEY = os.environ.get("PAYOS_API_KEY", "")
PAYOS_CHECKSUM_KEY = os.environ.get("PAYOS_CHECKSUM_KEY", "")
PRICE_BASIC = int(os.environ.get("PRICE_BASIC", "3000"))
PRICE_PRO = int(os.environ.get("PRICE_PRO", "5000"))
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")
BASE_URL = os.environ.get(
    "BASE_URL",
    f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:8000')}"
)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="ValuAI", version="2.0")

ALLOWED_UPLOAD_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".svg"}
MAX_UPLOAD_SIZE = 25 * 1024 * 1024
MAX_IMAGE_SIZE = 2 * 1024 * 1024


def _safe_job_id(job_id: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_-]{1,32}$", job_id):
        raise HTTPException(400, "Invalid job_id")
    return job_id


# ── Startup / shutdown ────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    await db.init_pool()
    await _seed_admin()


@app.on_event("shutdown")
async def shutdown():
    await db.close_pool()


async def _seed_admin():
    seed_user = os.environ.get("SEED_ADMIN_USER")
    seed_pass = os.environ.get("SEED_ADMIN_PASS")
    reset_user = os.environ.get("RESET_ADMIN_USER")
    reset_pass = os.environ.get("RESET_ADMIN_PASS")

    if reset_user and reset_pass:
        hashed = auth_module.hash_password(reset_pass)
        await db.update_admin_password(reset_user, hashed)

    if seed_user and seed_pass:
        count = await db.count_admins()
        if count == 0:
            hashed = auth_module.hash_password(seed_pass)
            await db.create_admin(seed_user, hashed)


# ── Auth helpers ──────────────────────────────────────────────────────────────

async def require_auth(request: Request):
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Missing token")
    try:
        auth_module.decode_token(token)
    except Exception:
        raise HTTPException(401, "Unauthorized")
    return token


async def get_current_user(request: Request) -> Optional[dict]:
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        payload = auth_module.decode_user_token(token)
        uid = int(payload.get("sub", 0))
        return await db.get_end_user_by_id(uid)
    except Exception:
        return None


# ── Static files ──────────────────────────────────────────────────────────────

static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

uploads_config = BASE_DIR / "uploads" / "config"
if uploads_config.exists():
    app.mount("/uploads/config", StaticFiles(directory=str(uploads_config)), name="config-images")


@app.get("/", response_class=HTMLResponse)
async def landing():
    index = static_dir / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>ValuAI</h1>")


@app.get("/app", response_class=HTMLResponse)
async def app_ui():
    f = static_dir / "app.html"
    if f.exists():
        return HTMLResponse(f.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>App</h1>")


@app.get("/admin", response_class=HTMLResponse)
async def admin_ui():
    f = static_dir / "admin.html"
    if f.exists():
        content = f.read_text(encoding="utf-8")
        return HTMLResponse(content, headers={"Cache-Control": "no-store"})
    return HTMLResponse("<h1>Admin</h1>", headers={"Cache-Control": "no-store"})


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0"}


# ── Public API ────────────────────────────────────────────────────────────────

@app.post("/api/process")
async def process(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    website_url: str = Form(""),
    session_id: str = Form(""),
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(413, "File too large (max 25MB)")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXT:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    job_id = secrets.token_hex(12)
    ip = request.client.host if request.client else "unknown"

    user = await get_current_user(request)
    user_id = user["id"] if user else None

    file_path = UPLOADS_DIR / f"{job_id}{ext}"
    file_path.write_bytes(content)

    cfg = await config_store.load_active_config()
    cfg_json = json.dumps(cfg)
    await db.save_job_config_snapshot(job_id, cfg_json)
    await db.create_job(job_id, website_url, file.filename or "", len(content),
                        ip, session_id or job_id, user_id)

    prompts = cfg.get("prompts", {})
    background_tasks.add_task(
        _run_phase1, job_id, str(file_path), website_url, cfg, prompts
    )

    return {"job_id": job_id, "status": "processing"}


async def _run_phase1(job_id: str, file_path: str, website_url: str,
                       cfg: dict, prompts: dict):
    start = time.time()
    try:
        a0_task = asyncio.to_thread(
            scrape_brand, website_url,
            prompts.get("brand_scraper", {}).get("preamble", "")
        )
        a1_task = asyncio.to_thread(
            extract, file_path,
            prompts.get("extractor", {}).get("preamble", "")
        )
        a0_result, a1_result = await asyncio.gather(a0_task, a1_task)

        financials = a1_result.get("financials", {})
        brand = a0_result.get("brand", {})

        a2_task = asyncio.to_thread(
            analyze_industry, financials,
            prompts.get("industry", {}).get("preamble", "")
        )
        a4_task = asyncio.to_thread(analyze, financials)
        a2_result, a4_result = await asyncio.gather(a2_task, a4_task)

        a3_result = await asyncio.to_thread(
            analyze_business, financials, a2_result,
            prompts.get("business_profile", {}).get("preamble", "")
        )

        company = financials.get("company", {})
        industry = a2_result.get("industry", {})

        partial = {
            "a0_brand": a0_result,
            "a1": a1_result,
            "a2_industry": a2_result,
            "a3_business": a3_result,
            "a4_ratios": a4_result,
            "brand": brand,
            "config": cfg,
        }
        partial_path = OUTPUTS_DIR / f"{job_id}_partial.json"
        partial_path.write_text(json.dumps(partial, ensure_ascii=False), encoding="utf-8")

        trailer_path = OUTPUTS_DIR / f"{job_id}_trailer.pdf"
        trailer_engine = cfg.get("style", {}).get("report_css", {}).get("trailer_engine", "html")

        trailer_payload = {
            "financials": financials,
            "ratios": a4_result,
            "industry": a2_result,
        }

        if trailer_engine == "html":
            try:
                trailer_html = render_trailer_html(trailer_payload, cfg, brand)
                await asyncio.to_thread(render_html_to_pdf, trailer_html, str(trailer_path))
            except Exception:
                await asyncio.to_thread(
                    render_trailer, trailer_payload, str(trailer_path), brand, cfg
                )
        else:
            await asyncio.to_thread(
                render_trailer, trailer_payload, str(trailer_path), brand, cfg
            )

        elapsed = time.time() - start
        await db.update_job_status(
            job_id, "trailer_ready",
            company_name=company.get("name"),
            industry_name=industry.get("industry_name"),
            elapsed_sec=elapsed,
        )

        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    except Exception as e:
        tb = traceback.format_exc()
        await db.update_job_status(job_id, "error", error_message=str(e)[:500])
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass


@app.get("/api/job/status/{job_id}")
async def job_status(job_id: str):
    job_id = _safe_job_id(job_id)
    job = await db.get_job(job_id)
    if not job:
        return {"status": "not_found"}
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "company_name": job.get("company_name"),
        "industry_name": job.get("industry_name"),
        "elapsed_sec": job.get("total_elapsed_sec"),
        "error": job.get("error_message"),
    }


@app.get("/api/download/{job_id}/trailer")
async def download_trailer(job_id: str):
    job_id = _safe_job_id(job_id)
    path = OUTPUTS_DIR / f"{job_id}_trailer.pdf"
    if not path.exists():
        raise HTTPException(404, "Trailer not ready")
    return FileResponse(str(path), media_type="application/pdf",
                        filename=f"valusai_trailer_{job_id}.pdf")


@app.get("/api/download/{job_id}/{kind}")
async def download_paid(job_id: str, kind: str, request: Request):
    job_id = _safe_job_id(job_id)
    if kind not in {"valuation", "explainer", "excel", "debug", "trace"}:
        raise HTTPException(400, "Invalid kind")

    package = await db.get_paid_package(job_id)
    if not package:
        raise HTTPException(402, "Payment required")
    if kind == "excel" and package != "pro":
        raise HTTPException(402, "Pro package required for Excel")

    ext_map = {"valuation": ".pdf", "explainer": ".pdf",
               "excel": ".xlsx", "debug": ".pdf", "trace": ".json"}
    path = OUTPUTS_DIR / f"{job_id}_{kind}{ext_map[kind]}"
    if not path.exists():
        raise HTTPException(404, "File not found")

    media_map = {"pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 "json": "application/json"}
    ext = ext_map[kind].lstrip(".")
    media = media_map.get(ext, "application/octet-stream")
    return FileResponse(str(path), media_type=media,
                        filename=f"valuai_{kind}_{job_id}{ext_map[kind]}")


@app.get("/api/stats")
async def stats():
    return await db.get_stats()


@app.get("/api/history/{session_id}")
async def history(session_id: str):
    rows = await db.get_session_history(session_id)
    return [{"job_id": r["job_id"], "status": r["status"],
             "company_name": r["company_name"], "created_at": str(r["created_at"])}
            for r in rows]


# ── User auth ─────────────────────────────────────────────────────────────────

@app.post("/api/user/register")
async def user_register(request: Request):
    body = await request.json()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    display_name = body.get("display_name", "")
    if not email or not password:
        raise HTTPException(400, "Email and password required")
    existing = await db.get_end_user_by_email(email)
    if existing:
        raise HTTPException(409, "Email already registered")
    hashed = auth_module.hash_password(password)
    uid = await db.create_end_user(email, hashed, display_name)
    token = auth_module.create_user_token(uid, email)
    return {"token": token, "user_id": uid, "email": email}


@app.post("/api/user/login")
async def user_login(request: Request):
    body = await request.json()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    user = await db.get_end_user_by_email(email)
    if not user or not auth_module.verify_password(password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = auth_module.create_user_token(user["id"], user["email"])
    return {"token": token, "user_id": user["id"], "email": user["email"]}


@app.get("/api/user/history")
async def user_history(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(401, "Unauthorized")
    rows = await db.get_user_history(user["id"])
    return [{"job_id": r["job_id"], "status": r["status"],
             "company_name": r["company_name"], "created_at": str(r["created_at"])}
            for r in rows]


# ── Payment ───────────────────────────────────────────────────────────────────

@app.post("/api/payment/create")
async def payment_create(request: Request):
    body = await request.json()
    job_id = _safe_job_id(body.get("job_id", ""))
    package = body.get("package", "basic")
    if package not in ("basic", "pro"):
        raise HTTPException(400, "Invalid package")

    amount = PRICE_PRO if package == "pro" else PRICE_BASIC
    order_code = int(time.time() * 1000) % 9999999999

    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY:
        await db.create_payment_order(job_id, amount, package, order_code)
        return {
            "order_code": order_code,
            "payment_link_id": f"dev_{order_code}",
            "checkout_url": f"{BASE_URL}/api/payment/dev-pay?code={order_code}",
            "qr_code_data": f"dev_payment_{order_code}",
        }

    import httpx
    payload = {
        "orderCode": order_code,
        "amount": amount,
        "description": f"ValuAI {package} {job_id[:8]}",
        "returnUrl": f"{BASE_URL}/app?job_id={job_id}&paid=1",
        "cancelUrl": f"{BASE_URL}/app?job_id={job_id}&cancelled=1",
    }
    sig_str = "&".join(f"{k}={v}" for k, v in sorted(payload.items()))
    sig = hmac.new(PAYOS_CHECKSUM_KEY.encode(), sig_str.encode(), hashlib.sha256).hexdigest()
    payload["signature"] = sig

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api-merchant.payos.vn/v2/payment-requests",
            json=payload,
            headers={"x-client-id": PAYOS_CLIENT_ID, "x-api-key": PAYOS_API_KEY},
            timeout=15,
        )
    data = resp.json()
    if data.get("code") != "00":
        raise HTTPException(502, f"PayOS error: {data.get('desc','')}")

    info = data.get("data", {})
    await db.create_payment_order(job_id, amount, package, order_code)
    return {
        "order_code": order_code,
        "payment_link_id": info.get("paymentLinkId"),
        "checkout_url": info.get("checkoutUrl"),
        "qr_code_data": info.get("qrCode"),
    }


@app.get("/api/payment/dev-pay")
async def dev_pay(code: int, background_tasks: BackgroundTasks):
    order = await db.get_payment_order_by_code(code)
    if not order:
        raise HTTPException(404, "Order not found")
    await db.mark_order_paid(code, datetime.utcnow())
    job_id = order["job_id"]
    package = order.get("package_type", "basic")
    background_tasks.add_task(_run_phase2, job_id, package)
    return HTMLResponse(f"<h2>Dev payment OK — Job {job_id} processing</h2>")


@app.post("/api/payment/callback")
async def payment_callback(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    data = body.get("data", {})
    received_sig = body.get("signature", "")

    if PAYOS_CHECKSUM_KEY:
        sig_str = "&".join(f"{k}={v}" for k, v in sorted(data.items()))
        expected = hmac.new(PAYOS_CHECKSUM_KEY.encode(), sig_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(received_sig, expected):
            raise HTTPException(400, "Invalid signature")

    order_code = data.get("orderCode")
    if not order_code:
        return {"status": "ignored"}

    order = await db.get_payment_order_by_code(order_code)
    if not order:
        return {"status": "order_not_found"}

    await db.mark_order_paid(order_code, datetime.utcnow())
    job_id = order["job_id"]
    package = order.get("package_type", "basic")
    background_tasks.add_task(_run_phase2, job_id, package)
    return {"status": "ok"}


@app.get("/api/payment/status/{job_id}")
async def payment_status(job_id: str):
    job_id = _safe_job_id(job_id)
    order = await db.get_payment_by_job(job_id)
    job = await db.get_job(job_id)
    return {
        "payment_status": order.get("status") if order else "none",
        "job_status": job.get("status") if job else "unknown",
        "package": order.get("package_type") if order else None,
    }


async def _run_phase2(job_id: str, package: str):
    await db.update_job_status(job_id, "paid_processing")
    start = time.time()
    try:
        partial_path = OUTPUTS_DIR / f"{job_id}_partial.json"
        if not partial_path.exists():
            raise FileNotFoundError(f"partial.json not found for {job_id}")

        partial = json.loads(partial_path.read_text(encoding="utf-8"))
        financials = partial["a1"]["financials"]
        a2_industry = partial["a2_industry"]
        a3_business = partial["a3_business"]
        a4_ratios = partial["a4_ratios"]
        brand = partial.get("brand", {})
        cfg = partial.get("config", {})
        prompts = cfg.get("prompts", {})

        a5_result = await asyncio.to_thread(
            project, financials, a4_ratios, a2_industry,
            prompts.get("projector", {}).get("preamble", "")
        )
        a6_result = await asyncio.to_thread(
            value, financials, a4_ratios, a2_industry, a5_result,
            prompts.get("valuator", {}).get("preamble", "")
        )
        a7_result = await asyncio.to_thread(
            write_thesis, financials, a4_ratios, a2_industry,
            a3_business, a5_result, a6_result,
            prompts.get("thesis_writer", {}).get("preamble", "")
        )

        full_payload = {
            "financials": financials,
            "industry": a2_industry.get("industry", a2_industry),
            "business": a3_business.get("business", a3_business),
            "ratios": a4_ratios,
            "projection": a5_result,
            "valuation": a6_result,
            "thesis": a7_result.get("thesis", a7_result),
        }

        val_path = OUTPUTS_DIR / f"{job_id}_valuation.pdf"
        await asyncio.to_thread(
            render_valuation_report, full_payload, str(val_path), brand, cfg
        )

        expl_path = OUTPUTS_DIR / f"{job_id}_explainer.pdf"
        expl_engine = cfg.get("style", {}).get("report_css", {}).get("explainer_layout", "A")
        try:
            expl_html = render_explainer_html(cfg, brand)
            await asyncio.to_thread(render_html_to_pdf, expl_html, str(expl_path))
        except Exception:
            await asyncio.to_thread(render_explainer, cfg, brand, str(expl_path))

        if package == "pro":
            xlsx_path = OUTPUTS_DIR / f"{job_id}_valuation.xlsx"
            await asyncio.to_thread(export_excel, full_payload, str(xlsx_path), cfg, brand)

        trace_path = OUTPUTS_DIR / f"{job_id}_trace.json"
        trace = {
            "job_id": job_id, "package": package,
            "financials_keys": list(financials.keys()),
            "valuation_summary": a6_result.get("valuation", {}).get("summary", {}),
            "thesis_headline": a7_result.get("thesis", {}).get("executive_summary", {}).get("headline", ""),
        }
        trace_path.write_text(json.dumps(trace, ensure_ascii=False), encoding="utf-8")

        try:
            partial_path.unlink(missing_ok=True)
        except Exception:
            pass

        elapsed = time.time() - start
        await db.update_job_status(
            job_id, "success", elapsed_sec=elapsed,
            result_json=json.dumps(full_payload.get("valuation", {}), ensure_ascii=False)[:5000]
        )

    except Exception as e:
        await db.update_job_status(job_id, "error", error_message=str(e)[:500])


# ── Admin auth ────────────────────────────────────────────────────────────────

@app.post("/api/auth/login")
async def admin_login(request: Request):
    body = await request.json()
    username = body.get("username", "")
    password = body.get("password", "")
    admin = await db.get_admin_by_username(username)
    if not admin or not auth_module.verify_password(password, admin["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = auth_module.create_token(username)
    return {"token": token}


@app.post("/api/auth/register")
async def admin_register(request: Request):
    body = await request.json()
    secret = body.get("secret", "")
    if ADMIN_SECRET and secret != ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin secret")
    count = await db.count_admins()
    if count > 0 and not ADMIN_SECRET:
        raise HTTPException(403, "Admin secret required")
    username = body.get("username", "")
    password = body.get("password", "")
    if not username or not password:
        raise HTTPException(400, "Username and password required")
    existing = await db.get_admin_by_username(username)
    if existing:
        raise HTTPException(409, "Username already exists")
    hashed = auth_module.hash_password(password)
    await db.create_admin(username, hashed)
    return {"status": "created"}


# ── Admin API ─────────────────────────────────────────────────────────────────

@app.get("/api/admin/stats")
async def admin_stats(_=Depends(require_auth)):
    stats = await db.get_stats()
    jobs = await db.get_recent_jobs(100)
    return {**stats, "recent_jobs": jobs}


@app.get("/api/admin/job/{job_id}")
async def admin_job(job_id: str, _=Depends(require_auth)):
    job_id = _safe_job_id(job_id)
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return dict(job)


@app.get("/api/admin/export.csv")
async def admin_export_csv(_=Depends(require_auth)):
    csv_data = await db.export_usage_csv()
    return PlainTextResponse(csv_data, media_type="text/csv",
                              headers={"Content-Disposition": "attachment;filename=usage.csv"})


@app.get("/api/admin/download/{job_id}/{kind}")
async def admin_download(job_id: str, kind: str, _=Depends(require_auth)):
    job_id = _safe_job_id(job_id)
    if kind not in {"trailer", "valuation", "explainer", "excel", "debug", "trace", "partial"}:
        raise HTTPException(400, "Invalid kind")
    ext_map = {"trailer": ".pdf", "valuation": ".pdf", "explainer": ".pdf",
               "excel": ".xlsx", "debug": ".pdf", "trace": ".json", "partial": ".json"}
    path = OUTPUTS_DIR / f"{job_id}_{kind}{ext_map[kind]}"
    if not path.exists():
        raise HTTPException(404, "File not found")
    media_map = {".pdf": "application/pdf",
                 ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 ".json": "application/json"}
    ext = ext_map[kind]
    return FileResponse(str(path), media_type=media_map.get(ext, "application/octet-stream"),
                        filename=f"{job_id}_{kind}{ext}")


@app.post("/api/admin/run_phase2/{job_id}")
async def admin_run_phase2(job_id: str, background_tasks: BackgroundTasks,
                            request: Request, _=Depends(require_auth)):
    job_id = _safe_job_id(job_id)
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    package = (body or {}).get("package", "pro")
    background_tasks.add_task(_run_phase2, job_id, package)
    return {"status": "triggered", "job_id": job_id}


@app.get("/api/admin/config")
async def admin_get_config(_=Depends(require_auth)):
    cfg = await config_store.load_active_config()
    versions = await db.list_config_versions()
    return {"config": cfg, "versions": versions}


@app.put("/api/admin/config")
async def admin_save_config(request: Request, _=Depends(require_auth)):
    body = await request.json()
    cfg = body.get("config", body)
    errors = schema.validate_config(cfg)
    if errors:
        raise HTTPException(422, {"errors": errors})
    cfg_id = await config_store.save_config(cfg)
    return {"status": "saved", "id": cfg_id}


@app.get("/api/admin/config/version/{version_id}")
async def admin_get_config_version(version_id: int, _=Depends(require_auth)):
    raw = await db.load_config_version(version_id)
    if not raw:
        raise HTTPException(404, "Version not found")
    return {"config": json.loads(raw), "version_id": version_id}


@app.post("/api/admin/config/validate")
async def admin_validate_config(request: Request, _=Depends(require_auth)):
    body = await request.json()
    cfg = body.get("config", body)
    errors = schema.validate_config(cfg)
    normalized = schema.normalize_config(cfg)
    return {"valid": len(errors) == 0, "errors": errors, "normalized": normalized}


@app.post("/api/admin/config/image")
async def admin_upload_image(file: UploadFile = File(...), _=Depends(require_auth)):
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Image too large (max 2MB)")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(400, f"Unsupported image type: {ext}")
    filename = f"{secrets.token_hex(8)}{ext}"
    dest = CONFIG_IMAGES_DIR / filename
    dest.write_bytes(content)
    return {"filename": filename, "url": f"/uploads/config/{filename}"}


@app.post("/api/admin/config/preview")
async def admin_preview(request: Request, _=Depends(require_auth)):
    body = await request.json()
    cfg = schema.normalize_config(body.get("config"))
    cfg["style"]["report_css"]["valuation_engine"] = "matplotlib"

    from sample_data import SAMPLE_PAYLOAD
    brand = SAMPLE_PAYLOAD.get("brand", {})
    payload = SAMPLE_PAYLOAD

    preview_path = OUTPUTS_DIR / f"preview_{secrets.token_hex(4)}.pdf"
    try:
        await asyncio.to_thread(
            render_valuation_report, payload, str(preview_path), brand, cfg
        )
        return FileResponse(str(preview_path), media_type="application/pdf",
                            filename="preview.pdf")
    except Exception as e:
        raise HTTPException(500, f"Preview failed: {str(e)[:200]}")


@app.get("/api/admin/render-health")
async def admin_render_health(_=Depends(require_auth)):
    playwright_ok = await asyncio.to_thread(is_playwright_available)
    return {"playwright": playwright_ok, "matplotlib": True}

"""Agent 0 — Brand scraper: fetch website → brand colors + logo."""
import base64
import io
import json
import re
from collections import Counter
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from agent_common import get_groq_client, parse_json_response, with_locked_schema

_FALLBACK_BRAND = {
    "primary": "#1e3a8a",
    "secondary": "#2563eb",
    "primary_light": "#eff6ff",
    "accent": "#10b981",
    "logo_b64": None,
    "logo_mime": None,
    "source": "fallback",
}

_SENTINEL = "TRẢ VỀ JSON (không markdown, không giải thích):"

_DEFAULT_PROMPT = """Bạn là chuyên gia thiết kế thương hiệu. Dựa trên các màu sắc được trích xuất từ website của doanh nghiệp sau đây, hãy xác định bảng màu thương hiệu chính.

Color hints from website:
{color_hints}

{sentinel}
{{
  "primary": "<hex màu chính — thường là màu nền header/navbar>",
  "secondary": "<hex màu phụ — button, link>",
  "primary_light": "<hex phiên bản nhạt của primary, dùng cho nền nhẹ>",
  "accent": "<hex màu nhấn — CTA, badge>"
}}"""


def _extract_color_hints(html: str) -> list[str]:
    hints = []
    soup = BeautifulSoup(html, "html.parser")

    meta_theme = soup.find("meta", attrs={"name": "theme-color"})
    if meta_theme and meta_theme.get("content"):
        hints.append(f"theme-color: {meta_theme['content']}")

    hex_pattern = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")

    for style_tag in soup.find_all("style"):
        text = style_tag.get_text()
        css_vars = re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})", text)
        for var, color in css_vars:
            if any(kw in var.lower() for kw in ["color", "primary", "secondary",
                                                  "accent", "brand", "main", "theme"]):
                hints.append(f"{var}: {color}")

        all_hex = hex_pattern.findall(text)
        counter = Counter(all_hex)
        for color, count in counter.most_common(5):
            hints.append(f"frequency-{count}: {color}")

    for tag_name in ["body", "header", "nav"]:
        tag = soup.find(tag_name)
        if tag and tag.get("style"):
            style = tag["style"]
            colors = hex_pattern.findall(style)
            for c in colors:
                hints.append(f"{tag_name}-inline: {c}")

    return hints[:30]


def _fetch_logo(soup: BeautifulSoup, base_url: str,
                client: httpx.Client) -> tuple[Optional[str], Optional[str]]:
    candidates = []

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        candidates.append(og_image["content"])

    apple_icon = soup.find("link", rel=lambda r: r and "apple-touch-icon" in r)
    if apple_icon and apple_icon.get("href"):
        href = apple_icon["href"]
        if not href.startswith("http"):
            href = base_url.rstrip("/") + "/" + href.lstrip("/")
        candidates.append(href)

    favicon = soup.find("link", rel=lambda r: r and "icon" in r)
    if favicon and favicon.get("href"):
        href = favicon["href"]
        if not href.startswith("http"):
            href = base_url.rstrip("/") + "/" + href.lstrip("/")
        candidates.append(href)

    logo_img = soup.find("img", class_=lambda c: c and "logo" in c.lower())
    if logo_img and logo_img.get("src"):
        src = logo_img["src"]
        if not src.startswith("http"):
            src = base_url.rstrip("/") + "/" + src.lstrip("/")
        candidates.append(src)

    for url in candidates:
        try:
            r = client.get(url, timeout=10)
            if r.status_code == 200 and r.content:
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(r.content))
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    return b64, "image/png"
                except Exception:
                    b64 = base64.b64encode(r.content).decode()
                    ct = r.headers.get("content-type", "image/png")
                    return b64, ct.split(";")[0].strip()
        except Exception:
            continue

    return None, None


def scrape_brand(website_url: str, prompt_override: str = "",
                 api_key: str = None) -> dict:
    if not website_url or not website_url.strip():
        return {"brand": {**_FALLBACK_BRAND}}

    try:
        client_http = httpx.Client(timeout=15, verify=False,
                                    follow_redirects=True)
        resp = client_http.get(website_url)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return {"brand": {**_FALLBACK_BRAND}}

    soup = BeautifulSoup(html, "html.parser")
    color_hints = _extract_color_hints(html)
    hints_str = "\n".join(color_hints) if color_hints else "Không tìm thấy màu sắc."

    prompt = with_locked_schema(
        _DEFAULT_PROMPT.format(color_hints=hints_str, sentinel=_SENTINEL),
        _SENTINEL,
        prompt_override,
    )

    try:
        client_ai = get_groq_client()
        completion = client_ai.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a brand design expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
        )
        raw = completion.choices[0].message.content or ""
        parsed = parse_json_response(raw)
        colors = {
            "primary": parsed.get("primary", _FALLBACK_BRAND["primary"]),
            "secondary": parsed.get("secondary", _FALLBACK_BRAND["secondary"]),
            "primary_light": parsed.get("primary_light", _FALLBACK_BRAND["primary_light"]),
            "accent": parsed.get("accent", _FALLBACK_BRAND["accent"]),
        }
    except Exception:
        colors = {
            "primary": _FALLBACK_BRAND["primary"],
            "secondary": _FALLBACK_BRAND["secondary"],
            "primary_light": _FALLBACK_BRAND["primary_light"],
            "accent": _FALLBACK_BRAND["accent"],
        }

    base_url = website_url.rstrip("/")
    logo_b64, logo_mime = _fetch_logo(soup, base_url, client_http)
    client_http.close()

    brand = {
        **colors,
        "logo_b64": logo_b64,
        "logo_mime": logo_mime,
        "source": "scraped",
    }
    return {"brand": brand}

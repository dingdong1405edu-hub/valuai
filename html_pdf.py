import os
from typing import Optional


def render_html_to_pdf(html: str, output_path: str,
                        wait_fonts: bool = True) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright not installed")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-gpu", "--single-process"]
        )
        try:
            page = browser.new_page()
            page.set_content(
                html,
                wait_until="networkidle" if wait_fonts else "domcontentloaded"
            )
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()

    return {"output_path": output_path, "engine": "playwright"}


def is_playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            browser.close()
        return True
    except Exception:
        return False

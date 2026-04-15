"""
Web crawler — scrape URLs via Firecrawl API.
Falls back gracefully if FIRECRAWL_API_KEY is not set.
"""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


async def crawl_url(url: str, source_type: str = "website") -> str:
    """
    Scrape a URL and return markdown content.

    source_type: website | fanpage | linkedin | other

    Returns empty string with warning if Firecrawl key not configured.
    Falls back to error message if URL is inaccessible (e.g. login-gated Facebook).
    """
    if not settings.FIRECRAWL_API_KEY:
        logger.warning("[CRAWLER] FIRECRAWL_API_KEY not set — returning placeholder")
        return f"[Web content not available — Firecrawl not configured]\nURL: {url}\nSource type: {source_type}"

    try:
        # Import here so app starts even without firecrawl installed
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

        logger.info(f"[CRAWLER] scraping {url} (type={source_type})")

        if source_type in ("fanpage", "linkedin"):
            # Single page scrape — crawling social media is unreliable
            result = app.scrape_url(
                url,
                params={
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "timeout": 30000,
                },
            )
            content = result.get("markdown", "")
        else:
            # Multi-page crawl for websites
            result = app.crawl_url(
                url,
                params={
                    "limit": 10,
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True,
                    },
                },
            )
            pages = result.get("data", [])
            content = "\n\n---\n\n".join(
                p.get("markdown", "") for p in pages if p.get("markdown")
            )

        if not content:
            logger.warning(f"[CRAWLER] empty content from {url}")
            return f"[No content extracted from {url}]\nThis URL may require authentication or block scraping."

        logger.info(f"[CRAWLER] extracted {len(content)} chars from {url}")
        return content

    except ImportError:
        logger.error("[CRAWLER] firecrawl-py not installed")
        return f"[Firecrawl not installed]\nURL: {url}"
    except Exception as exc:
        logger.error(f"[CRAWLER] failed to crawl {url}: {exc}")
        # Return partial error info so pipeline can continue
        return f"[Crawl failed: {str(exc)[:200]}]\nURL: {url}"

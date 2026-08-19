# scrape.py
"""Stage 1: Fetch real source material. One job only — scrape."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


class ScrapeError(Exception):
    """Raised when a source cannot be reached or yields no usable content."""
    pass


# Simple on-disk cache so a daily cron does not hammer the same URL repeatedly.
_CACHE_DIR = Path(__file__).resolve().parent / ".scrape_cache"
_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours


def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return _CACHE_DIR / f"{key}.html"


def _read_cache(url: str) -> str | None:
    path = _cache_path(url)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > _CACHE_TTL_SECONDS:
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _write_cache(url: str, html: str) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(url).write_text(html, encoding="utf-8")


def scrape_source(
    url: str,
    timeout: int = 15,
    retries: int = 2,
    backoff: float = 1.5,
    use_cache: bool = True,
) -> str:
    """
    Fetch a page and return the *article HTML* (not the full page).

    - Retries transient network failures with exponential backoff.
    - Optionally caches successful responses for a few hours (helpful for cron).
    - Raises ScrapeError on permanent failure or when no article-like content
      is found (e.g. the site changed its layout).
    """
    if use_cache:
        cached = _read_cache(url)
        if cached is not None:
            return cached

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            page = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; GroundedPipeline/1.1)",
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=timeout,
            )
            page.raise_for_status()
            break
        except requests.RequestException as e:
            last_error = e
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            continue
    else:
        raise ScrapeError(f"Could not reach {url} after {retries + 1} attempts: {last_error}") from last_error

    soup = BeautifulSoup(page.text, "html.parser")
    article = soup.find("article")
    # Fallback: some official sites put content in <main> or a content div
    if not article:
        article = soup.find("main") or soup.find(class_="content") or soup.find("body")

    if not article or not article.get_text(strip=True):
        raise ScrapeError(
            f"No article content found at {url} — page layout may have changed"
        )

    # Return only the article subtree so the structure stage does not re-parse
    # the entire page (nav, scripts, ads, etc.).
    article_html = str(article)

    if use_cache:
        _write_cache(url, article_html)

    return article_html

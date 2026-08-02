# scrape.py
"""Stage 1: Fetch real source material. One job only — scrape."""

import requests
from bs4 import BeautifulSoup


class ScrapeError(Exception):
    """Raised when a source cannot be reached or yields no usable content."""
    pass


def scrape_source(url: str, timeout: int = 10) -> str:
    """
    Fetch the raw HTML of a page.

    Raises ScrapeError on network failure or when no article-like content
    is found (e.g. the site changed its layout).
    """
    try:
        page = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GroundedPipeline/1.0)"},
            timeout=timeout,
        )
        page.raise_for_status()
    except requests.RequestException as e:
        raise ScrapeError(f"Could not reach {url}: {e}") from e

    soup = BeautifulSoup(page.text, "html.parser")
    article = soup.find("article")
    # Fallback: some official sites put content in <main> or a content div
    if not article:
        article = soup.find("main") or soup.find(class_="content") or soup.find("body")

    if not article or not article.get_text(strip=True):
        raise ScrapeError(
            f"No article content found at {url} — page layout may have changed"
        )

    return page.text
# structure.py
"""Stage 2: Clean raw HTML and chunk it into usable context."""

from bs4 import BeautifulSoup


class StructureError(Exception):
    """Raised when cleaning or chunking fails."""
    pass


def clean_and_chunk(
    raw_html: str,
    chunk_size: int = 300,
    overlap: int = 50,
) -> tuple[str, list[str]]:
    """
    Strip non-content tags, extract article paragraphs, then chunk.

    Returns:
        (full_cleaned_text, list_of_chunks)

    Raises StructureError when no usable text remains.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup(["nav", "header", "footer", "script", "style", "aside"]):
        tag.decompose()
    for tag in soup.find_all(class_=["cookie-banner", "cookie", "ads", "advertisement"]):
        tag.decompose()

    article = (
        soup.find("article")
        or soup.find("main")
        or soup.find(class_="content")
        or soup.find("body")
    )
    if not article:
        raise StructureError("No <article> (or fallback) tag found after cleaning")

    paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
    text = "\n".join(p for p in paragraphs if len(p) > 20)

    if not text:
        # Last-resort: take all remaining text
        text = article.get_text(separator="\n", strip=True)
        text = "\n".join(line for line in text.splitlines() if len(line) > 20)

    if not text:
        raise StructureError("Article found but contained no usable paragraphs")

    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
        if start < 0:
            start = 0
        if end >= len(words):
            break

    return text, chunks
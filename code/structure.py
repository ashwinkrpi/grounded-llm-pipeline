# structure.py
"""Stage 2: Clean raw HTML and chunk it into usable context."""

from __future__ import annotations

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

    Accepts either full-page HTML or (preferred) the article HTML already
    extracted by scrape_source().

    Returns:
        (full_cleaned_text, list_of_chunks)

    Raises StructureError when no usable text remains.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup(["nav", "header", "footer", "script", "style", "aside"]):
        tag.decompose()
    for tag in soup.find_all(class_=["cookie-banner", "cookie", "ads", "advertisement"]):
        tag.decompose()

    # When scrape_source already returned the article subtree, the root *is*
    # the article. Otherwise fall back to the old full-page selectors.
    article = (
        soup.find("article")
        or soup.find("main")
        or soup.find(class_="content")
        or soup  # the fragment itself may already be the article
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


def select_best_chunk(chunks: list[str], question: str | None = None) -> str:
    """
    Pick the single most useful chunk for generation.

    Simple heuristic: prefer the chunk that contains the highest number of
    distinctive terms from the question (if provided). Falls back to the
    longest chunk, then to chunks[0].

    This is deliberately lightweight — no embeddings required — so it stays
    suitable for a Raspberry Pi. For multi-chunk answers, call the model
    once per chunk and merge (see run_pipeline for the optional path).
    """
    if not chunks:
        raise StructureError("No chunks available to select from")

    if len(chunks) == 1:
        return chunks[0]

    if not question:
        # Prefer the longest chunk as a rough proxy for substance
        return max(chunks, key=len)

    # Tokenise the question into meaningful terms (skip very short words)
    terms = [t.lower() for t in question.split() if len(t) > 3]
    if not terms:
        return max(chunks, key=len)

    best_score = -1
    best_chunk = chunks[0]
    for chunk in chunks:
        lower = chunk.lower()
        score = sum(1 for t in terms if t in lower)
        # Tie-break on length so we still favour substance
        score = score * 1000 + len(chunk)
        if score > best_score:
            best_score = score
            best_chunk = chunk

    return best_chunk

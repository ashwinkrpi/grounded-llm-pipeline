# validator.py
"""Low-level citation matching. One job: does this quote appear in the source?"""

from difflib import SequenceMatcher


def validate_citation(
    quote: str,
    source_text: str,
    threshold: float = 0.85,
) -> tuple[bool, float]:
    """
    Check whether `quote` genuinely appears in `source_text`,
    allowing minor wording differences (punctuation, casing).

    Returns:
        (is_valid, best_similarity_score)
    """
    quote_clean = quote.lower().strip()
    source_clean = source_text.lower()

    # Exact substring match — strongest possible signal
    if quote_clean in source_clean:
        return True, 1.0

    # Sliding-window near-match for small differences
    words = source_clean.split()
    window_size = max(1, len(quote_clean.split()))
    best_score = 0.0

    for i in range(len(words) - window_size + 1):
        window = " ".join(words[i : i + window_size])
        score = SequenceMatcher(None, quote_clean, window).ratio()
        if score > best_score:
            best_score = score

    return best_score >= threshold, best_score
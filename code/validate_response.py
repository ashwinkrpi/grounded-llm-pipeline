# validate_response.py
"""Stage 4: Extract bracketed citations from the model answer and validate each."""

import re

from validator import validate_citation


def validate_response(
    answer: str,
    source_text: str,
    threshold: float = 0.85,
) -> dict:
    """
    Pull every [bracketed] citation out of the model answer and
    check it against the real source text.

    Returns a dict with:
      - status: "approved" | "rejected"
      - citations: list of {quote, valid, score}
      - reason: (only when rejected for missing citations)
    """
    citations = re.findall(r"\[(.*?)\]", answer)

    if not citations:
        return {
            "status": "rejected",
            "reason": "no citations found",
            "citations": [],
        }

    results = []
    for quote in citations:
        valid, score = validate_citation(quote, source_text, threshold=threshold)
        results.append(
            {
                "quote": quote,
                "valid": valid,
                "score": round(score, 2),
            }
        )

    if all(r["valid"] for r in results):
        return {"status": "approved", "citations": results}

    return {"status": "rejected", "citations": results}
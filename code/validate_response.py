# validate_response.py
"""Stage 4: Extract bracketed citations from the model answer and validate each."""

from __future__ import annotations

import re

from validator import validate_citation

# Exact fallback the prompt instructs the model to use when the source has
# nothing relevant. This is a deliberate, non-hallucinated outcome.
_NOT_STATED = "not stated in source"


def validate_response(
    answer: str,
    source_text: str,
    threshold: float = 0.85,
) -> dict:
    """
    Pull every [bracketed] citation out of the model answer and
    check it against the real source text.

    Special case: if the model replies with the allowed fallback
    "Not stated in source." (no citations needed), treat it as approved.
    That is an honest refusal, not a hallucination.

    Returns a dict with:
      - status: "approved" | "rejected"
      - citations: list of {quote, valid, score}
      - reason: (only when rejected)
    """
    stripped = answer.strip()
    # Normalise punctuation / casing for the fallback check
    if stripped.lower().rstrip(".") == _NOT_STATED:
        return {
            "status": "approved",
            "citations": [],
            "reason": "model correctly reported that the source does not contain the answer",
        }

    citations = re.findall(r"\[(.*?)\]", answer)

    if not citations:
        return {
            "status": "rejected",
            "reason": "no citations found and answer is not the allowed fallback",
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

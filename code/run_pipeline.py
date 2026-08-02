
# run_pipeline.py
"""Orchestrator: calls the five stages in order and fails loudly at the right stage."""

from scrape import scrape_source, ScrapeError
from structure import clean_and_chunk, StructureError
from generate import ask_model, build_prompt
from validate_response import validate_response
from render_card import render_card


def run_pipeline(
    url: str,
    source_name: str,
    question: str | None = None,
    model: str = "llama3.2:3b",
    output_path: str = "output_card.png",
) -> None:
    # --- Stage 1: Scrape ---
    try:
        raw = scrape_source(url)
        print("[STAGE: scrape] SUCCESS")
    except ScrapeError as e:
        print(f"[STAGE: scrape] FAILED — {e}")
        return

    # --- Stage 2: Structure ---
    try:
        cleaned, chunks = clean_and_chunk(raw)
        print("[STAGE: structure] SUCCESS")
    except StructureError as e:
        print(f"[STAGE: structure] FAILED — {e}")
        return

    if not chunks:
        print("[STAGE: structure] FAILED — no chunks produced")
        return

    # --- Stage 3: Generate ---
    prompt = build_prompt(chunks[0], question=question)
    try:
        answer = ask_model(prompt, model=model)
        print("[STAGE: generate] SUCCESS")
    except Exception as e:
        print(f"[STAGE: generate] FAILED — {e}")
        return

    # --- Stage 4: Validate ---
    result = validate_response(answer, cleaned)
    if result["status"] != "approved":
        print(f"[STAGE: validate] REJECTED — {result.get('citations', result)}")
        return
    print("[STAGE: validate] APPROVED")

    # --- Stage 5: Render ---
    # Prefer the validated answer text; strip brackets for a cleaner card if you like
    display_text = answer  # or re.sub(r"\[.*?\]", "", answer).strip()
    path = render_card(display_text, source_name, output_path=output_path)
    print(f"[STAGE: render] SUCCESS — saved to {path}")


if __name__ == "__main__":
    # Example — replace with a real URL that has an <article> (or main) tag
    run_pipeline(
        url="https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
        source_name="Reserve Bank of India",
        question="What is the key decision or announcement in this release?",
    )
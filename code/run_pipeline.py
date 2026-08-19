# run_pipeline.py
"""Orchestrator: calls the five stages in order and fails loudly at the right stage."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

from scrape import scrape_source, ScrapeError
from structure import clean_and_chunk, select_best_chunk, StructureError
from generate import ask_model, build_prompt
from validate_response import validate_response
from render_card import render_card


def _setup_logging(verbose: bool = False) -> None:
    """Configure a simple, timestamped logger that works well with cron redirects."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,
    )


def run_pipeline(
    url: str,
    source_name: str,
    question: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    output_path: str = "output_card.png",
    dry_run: bool = False,
    skip_render: bool = False,
    use_cache: bool = True,
) -> dict:
    """
    Run the five stages. Returns a small result dict for callers / tests.

    Environment variables (used as defaults when the corresponding argument
    is omitted):
      GROUNDED_MODEL      — Ollama model name (default: llama3.2:3b)
      GROUNDED_BASE_URL   — Ollama base URL   (default: http://localhost:11434)
    """
    model = model or os.environ.get("GROUNDED_MODEL", "llama3.2:3b")
    base_url = base_url or os.environ.get("GROUNDED_BASE_URL", "http://localhost:11434")

    log = logging.getLogger("grounded")
    log.info("=== run start === %s", datetime.now(timezone.utc).isoformat())
    log.info("url=%s model=%s dry_run=%s skip_render=%s", url, model, dry_run, skip_render)

    result: dict = {"status": "failed", "stages": {}}

    # --- Stage 1: Scrape ---
    try:
        raw = scrape_source(url, use_cache=use_cache)
        log.info("[STAGE: scrape] SUCCESS")
        result["stages"]["scrape"] = "SUCCESS"
    except ScrapeError as e:
        log.error("[STAGE: scrape] FAILED — %s", e)
        result["stages"]["scrape"] = f"FAILED — {e}"
        return result

    # --- Stage 2: Structure ---
    try:
        cleaned, chunks = clean_and_chunk(raw)
        log.info("[STAGE: structure] SUCCESS (%d chunks)", len(chunks))
        result["stages"]["structure"] = "SUCCESS"
    except StructureError as e:
        log.error("[STAGE: structure] FAILED — %s", e)
        result["stages"]["structure"] = f"FAILED — {e}"
        return result

    if not chunks:
        log.error("[STAGE: structure] FAILED — no chunks produced")
        result["stages"]["structure"] = "FAILED — no chunks produced"
        return result

    # Prefer the most relevant chunk instead of always using chunks[0]
    selected = select_best_chunk(chunks, question=question)
    log.debug("Selected chunk length=%d (of %d chunks)", len(selected), len(chunks))

    # --- Stage 3: Generate ---
    prompt = build_prompt(selected, question=question)
    try:
        answer = ask_model(prompt, model=model, base_url=base_url)
        log.info("[STAGE: generate] SUCCESS")
        result["stages"]["generate"] = "SUCCESS"
        result["answer"] = answer
    except Exception as e:
        log.error("[STAGE: generate] FAILED — %s", e)
        result["stages"]["generate"] = f"FAILED — {e}"
        return result

    # --- Stage 4: Validate ---
    validation = validate_response(answer, cleaned)
    if validation["status"] != "approved":
        log.warning(
            "[STAGE: validate] REJECTED — %s",
            validation.get("reason") or validation.get("citations"),
        )
        result["stages"]["validate"] = "REJECTED"
        result["validation"] = validation
        return result

    log.info("[STAGE: validate] APPROVED")
    result["stages"]["validate"] = "APPROVED"
    result["validation"] = validation

    if dry_run or skip_render:
        log.info("[STAGE: render] SKIPPED (dry_run=%s skip_render=%s)", dry_run, skip_render)
        result["stages"]["render"] = "SKIPPED"
        result["status"] = "approved_no_render"
        return result

    # --- Stage 5: Render ---
    # Keep the validated wording intact; rendering is presentation only.
    path = render_card(answer, source_name, output_path=output_path)
    log.info("[STAGE: render] SUCCESS — saved to %s", path)
    result["stages"]["render"] = "SUCCESS"
    result["output_path"] = path
    result["status"] = "success"
    return result


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Grounded local AI pipeline — scrape → structure → generate → validate → render",
    )
    p.add_argument(
        "--url",
        default=os.environ.get(
            "GROUNDED_URL",
            "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
        ),
        help="Source URL to scrape (or set GROUNDED_URL). Prefer a page that contains "
             "an <article> or <main> element.",
    )
    p.add_argument(
        "--source",
        default=os.environ.get("GROUNDED_SOURCE", "Reserve Bank of India"),
        help="Human-readable source name shown on the rendered card",
    )
    p.add_argument(
        "--question",
        default=os.environ.get(
            "GROUNDED_QUESTION",
            "What is the key decision or announcement in this release?",
        ),
        help="Question the model should answer from the source",
    )
    p.add_argument(
        "--model",
        default=None,
        help="Ollama model name (default: $GROUNDED_MODEL or llama3.2:3b)",
    )
    p.add_argument(
        "--base-url",
        default=None,
        help="Ollama base URL (default: $GROUNDED_BASE_URL or http://localhost:11434)",
    )
    p.add_argument(
        "--output",
        default="output_card.png",
        help="Path for the rendered card image",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run scrape → structure → generate → validate but skip rendering",
    )
    p.add_argument(
        "--skip-render",
        action="store_true",
        help="Alias for --dry-run (kept for clarity in scripts)",
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable the scrape-stage on-disk cache",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return p


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging(verbose=args.verbose)

    # Note for readers: the default RBI URL is a real press-release index.
    # Individual release pages sometimes change structure; if scrape fails,
    # pass a concrete release URL via --url or GROUNDED_URL.
    outcome = run_pipeline(
        url=args.url,
        source_name=args.source,
        question=args.question,
        model=args.model,
        base_url=args.base_url,
        output_path=args.output,
        dry_run=args.dry_run or args.skip_render,
        skip_render=args.skip_render,
        use_cache=not args.no_cache,
    )

    # Non-zero exit when the pipeline did not fully succeed — useful for cron.
    if outcome.get("status") not in ("success", "approved_no_render"):
        sys.exit(1)

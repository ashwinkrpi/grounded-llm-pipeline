<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 9: Wiring the Five Files Together

## The Script That Died Silently at 3 AM and Took Everything Down With It

Here's what happens to almost everyone the first time they try to wire a pipeline together, and it's worth living through this story once before it happens to your actual project. Someone takes every piece from the last five chapters — scrape, clean, generate, validate, render — and, feeling productive, jams the whole thing into one giant script. One file, top to bottom, each step calling straight into the next.

```python
# everything.py — the "one big file" approach
scraped = scrape_source(url)
cleaned = clean_article(scraped)
chunks = chunk_text(cleaned)
answer = ask_model(build_prompt(chunks[0]))
result = validate_response(answer, cleaned)
render_card(answer, "RBI")
print("Done!")
```

Runs great the first three times. Then, one morning, the RBI redesigns their press release page — a new `<div>` wrapper, a class name that changed — and the scraper quietly gets back an empty string instead of an error. Watch what happens next:

```bash
$ python3 everything.py

Traceback (most recent call last):
  File "everything.py", line 4, in <module>
    chunks = chunk_text(cleaned)
  File "chunk_text.py", line 3, in chunk_text
    words = text.split()
AttributeError: 'NoneType' object has no attribute 'split'
```

One crash, zero output, and — this is the part that actually stings — zero clue, from that traceback alone, about what actually went wrong upstream. Was the source down? Did the RBI change their page layout? Did the cleaner choke on something new? The error message is pointing at `chunk_text.py`, but the real problem happened three steps earlier, in a completely different file, and by the time it surfaced, all the useful context about *why* was already gone. This is what happens when six separate, working pieces get welded into one script with no seams — a failure anywhere becomes a mystery everywhere.

## Why Five Separate Files, Each With One Job, Is the Actual Design

Here's the core idea this chapter is built on, and it's worth stating plainly: this pipeline's reliability doesn't come from clever code. It comes from strict separation — scrape does only scraping, structure does only cleaning and chunking, generate does only prompting and asking the model, validate does only checking citations, and render does only turning approved text into an image. Each file has exactly one job, takes a clearly defined input, and produces a clearly defined output. And — this is the part most beginners skip — each file has to fail *loudly* and *specifically* when its one job can't be done, instead of quietly passing along an empty string or a `None` and letting some unrelated file downstream take the blame.

The permanent versions of these files live in [`code/`](../code/). Before rebuilding this properly, it's worth being upfront about something: the five files below aren't new code appearing out of nowhere. They're the exact same functions from Chapters 4 through 8, given permanent homes. A few of them need one small addition to actually slot into an orchestrator, so let's be explicit about the mapping instead of pretending it was always this tidy:

| Teaching file (earlier chapters) | Permanent file in `code/` | What moved |
|----------------------------------|---------------------------|------------|
| `targeted_scrape.py` (Ch 4) | [`scrape.py`](../code/scrape.py) | Same scraping logic, wrapped in `scrape_source()` with real exceptions |
| `clean_text.py` + `chunk_text.py` (Ch 5) | [`structure.py`](../code/structure.py) | Cleaning and chunking are one job; both live here |
| `talk_to_model.py` (Ch 3) | [`generate.py`](../code/generate.py) | `ask_model()` plus a new `build_prompt()` for Chapter 6 rules |
| `validator.py` + `validate_response.py` (Ch 7) | [`validator.py`](../code/validator.py), [`validate_response.py`](../code/validate_response.py) | Citation matching and response-level approve/reject |
| `render_card.py` (Ch 8) | [`render_card.py`](../code/render_card.py) | Presentation only — never changes wording |
| — | [`run_pipeline.py`](../code/run_pipeline.py) | Orchestrator that calls the five stages in order |

From here on, these are the real names you'll keep using.

## The Five Modules

### `scrape.py` — only scraping, fail clearly

Core idea (full permanent file: [`code/scrape.py`](../code/scrape.py)):

```python
def scrape_source(url, timeout=15, retries=2, use_cache=True) -> str:
    # GET with retries + short on-disk cache
    # Find <article> (or main / content / body)
    # Return article HTML only — not the full page
    ...
```

**What changed for the permanent version:** teaching snippets in Chapter 4 returned full `page.text`. The permanent module returns the article subtree only, retries transient network errors, and caches successful responses for a few hours (disable with `--no-cache`).

### `structure.py` — only cleaning and chunking

Core idea (full permanent file: [`code/structure.py`](../code/structure.py)):

```python
def clean_and_chunk(raw_html, chunk_size=300, overlap=50) -> tuple[str, list[str]]:
    # Strip nav/header/footer/script/style
    # Extract paragraphs, chunk with overlap
    ...

def select_best_chunk(chunks, question=None) -> str:
    # Prefer the chunk that best matches the question terms
    ...
```

**What changed for the permanent version:** the orchestrator no longer always uses `chunks[0]`. It calls `select_best_chunk()` so longer pages still feed the most relevant context into generation.

### `generate.py` — prompt + model call

Chapter 3's `ask_model()` lives here with env-var defaults. Chapter 6's rules live in `build_prompt()`:

```python
# generate.py — excerpt; full file: code/generate.py
def ask_model(prompt, model=None, base_url=None) -> str:
    model = model or os.environ.get("GROUNDED_MODEL", "llama3.2:latest")
    ...

def build_prompt(source_chunk, question=None) -> str:
    # Strict grounding rules + SOURCE + QUESTION
    ...
```

See the complete module: [`code/generate.py`](../code/generate.py).

### Validation — `validator.py` + `validate_response.py`

Chapter 7's mechanical citation check stays split for clarity:

- [`validator.py`](../code/validator.py) — low-level `validate_citation(quote, source_text)`
- [`validate_response.py`](../code/validate_response.py) — extracts `[brackets]` from the answer and approves or rejects

### `render_card.py` — presentation only

Unchanged from Chapter 8. Full file: [`code/render_card.py`](../code/render_card.py).

## The Orchestrator

The one file whose entire job is calling the other files in order, and catching exactly which one broke:

```python
# run_pipeline.py — full file: code/run_pipeline.py
from scrape import scrape_source, ScrapeError
from structure import clean_and_chunk, StructureError
from generate import ask_model, build_prompt
from validate_response import validate_response
from render_card import render_card

def run_pipeline(url, source_name):
    try:
        raw = scrape_source(url)
    except ScrapeError as e:
        print(f"[STAGE: scrape] FAILED — {e}")
        return

    try:
        cleaned, chunks = clean_and_chunk(raw)
    except StructureError as e:
        print(f"[STAGE: structure] FAILED — {e}")
        return

    answer = ask_model(build_prompt(chunks[0]))
    result = validate_response(answer, cleaned)
    if result["status"] != "approved":
        print(f"[STAGE: validate] REJECTED — {result['citations']}")
        return

    path = render_card(answer, source_name)
    print(f"[STAGE: render] SUCCESS — saved to {path}")

if __name__ == "__main__":
    run_pipeline(
        "https://www.rbi.org.in/press-release-example",
        "Reserve Bank of India",
    )
```

See the complete orchestrator: [`code/run_pipeline.py`](../code/run_pipeline.py).

Run it against the exact same broken page from the story at the top of this chapter:

```bash
$ python3 code/run_pipeline.py

[STAGE: scrape] FAILED — No article content found at
https://www.rbi.org.in/press-release-example — page layout may
have changed
```

Compare that to the earlier `AttributeError` buried three files deep. This tells you, immediately, exactly which stage broke and exactly why — the RBI's page layout changed, scraping found no article content, nothing downstream even got a chance to run on bad data. No mystery, no guessing which of six files to open first. The pipeline didn't just fail — it failed at the right place, with the right explanation, which is the entire difference between a script you can fix in thirty seconds and one you're debugging for an hour.

## Final Layout in `code/`

| File | Job |
|------|-----|
| [`scrape.py`](../code/scrape.py) | Fetch article HTML; retries + cache; raise `ScrapeError` |
| [`structure.py`](../code/structure.py) | Clean + chunk; `select_best_chunk`; raise `StructureError` |
| [`generate.py`](../code/generate.py) | `build_prompt` + `ask_model` (env-aware defaults) |
| [`validator.py`](../code/validator.py) | Low-level quote matching |
| [`validate_response.py`](../code/validate_response.py) | Extract citations; approve, reject, or accept "Not stated in source." |
| [`render_card.py`](../code/render_card.py) | Dynamic layout card image |
| [`run_pipeline.py`](../code/run_pipeline.py) | Orchestrator — CLI, logging, stage failures |

Teaching excerpts in earlier chapters are simplified on purpose. When behavior differs, the permanent file in `code/` wins — each chapter that introduces a stage notes the main differences.

## The Objection: "Isn't Five Separate Files Just More Complexity for No Real Benefit?"

Reasonable pushback — one file is simpler to read top to bottom, one file is easier to find things in, so why deliberately split working code into five pieces that now have to import from each other?

Let's actually test the claim that one file is easier to work with, using a real scenario: your model choice changes. Say you switch from `llama3.2:latest` to a different model in Chapter 2's family, and you need to update how prompts get built.

With the five-file structure, the fix is exactly one line, in exactly one file, [`generate.py`](../code/generate.py), and nothing else in the pipeline needs to be touched, read, or even understood to make that change safely. With the single `everything.py` file from the top of this chapter, that same change means scrolling through scraping logic, cleaning logic, and rendering logic just to find the one relevant line — and worse, it means any typo you make while scrolling past unrelated code risks breaking a completely different stage by accident, since it's all sharing the same file and the same variable scope. Five files aren't more complex. They're the same complexity, organized so that each piece of it stays contained instead of leaking into everything else.

There's a deeper reason this matters specifically for this pipeline, though, and it connects straight back to Chapter 7: your validator's entire credibility rests on knowing, with certainty, that it's checking real generate-stage output against real structure-stage source text — not some blended, half-scraped, half-cleaned mess that got tangled together because two stages shared code they shouldn't have. Separation isn't just about tidiness. It's what lets you trust that when validation says "approved," it actually checked what you think it checked.

## Chapter Summary

Wiring five working pieces into one giant script feels efficient, but it trades away the one thing that actually matters once something breaks — knowing where, and why. Keeping scrape, structure, generate, validate, and render as five separate files, each with one clear job and its own loud, specific failure mode, means a broken page layout, a bad source, or a rejected citation surfaces immediately, at the exact stage it happened, instead of as a mystery crash three files downstream. The extra file count isn't complexity for its own sake — it's what keeps each stage trustworthy on its own, which is exactly what lets a validator's "approved" actually mean something.

The assembled modules and orchestrator are in [`code/`](../code/). From this point on, you run the pipeline with:

```bash
python3 code/run_pipeline.py
```

## Bridge to Chapter 10

Right now, running this pipeline still means you, personally, typing `python3 code/run_pipeline.py` and watching it go. That's a massive improvement over the copy-paste chat-window workflow from Chapter 3 — but it's still not automatic. Somebody still has to remember to run it, every single day, at a reasonable hour, and actually notice if it fails. The whole reason you built five clean, loudly-failing stages in this chapter, instead of one tangled script, is so that the next step becomes possible at all: letting this thing run completely on its own, on a schedule, catching its own failures without you standing over it. That's the next chapter.

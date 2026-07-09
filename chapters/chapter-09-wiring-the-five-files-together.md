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

Let's rebuild this properly. Here's `scrape.py`, doing only scraping, and refusing to pretend everything's fine when it isn't:

```python
# scrape.py
import requests
from bs4 import BeautifulSoup

class ScrapeError(Exception):
    pass

def scrape_source(url):
    try:
        page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        page.raise_for_status()
    except requests.RequestException as e:
        raise ScrapeError(f"Could not reach {url}: {e}")
    
    soup = BeautifulSoup(page.text, "html.parser")
    article = soup.find("article")
    if not article or not article.get_text(strip=True):
        raise ScrapeError(f"No article content found at {url} — page layout may have changed")
    
    return page.text
```

Here's `structure.py`, doing only cleaning and chunking, with the same rule — fail clearly, don't fail silently:

```python
# structure.py
from bs4 import BeautifulSoup

class StructureError(Exception):
    pass

def clean_and_chunk(raw_html, chunk_size=300, overlap=50):
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    
    article = soup.find("article")
    if not article:
        raise StructureError("No <article> tag found after cleaning")
    
    paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
    text = "\n".join(p for p in paragraphs if len(p) > 20)
    if not text:
        raise StructureError("Article found but contained no usable paragraphs")
    
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return text, chunks
```

Now the orchestrator — the one file whose entire job is calling the other files in order, and catching exactly which one broke:

```python
# run_pipeline.py
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
    run_pipeline("https://www.rbi.org.in/press-release-example", "Reserve Bank of India")
```

Run it against the exact same broken page from the story at the top of this chapter:

```bash
$ python3 run_pipeline.py

[STAGE: scrape] FAILED — No article content found at 
https://www.rbi.org.in/press-release-example — page layout may 
have changed
```

Compare that to the earlier `AttributeError` buried three files deep. This tells you, immediately, exactly which stage broke and exactly why — the RBI's page layout changed, scraping found no article content, nothing downstream even got a chance to run on bad data. No mystery, no guessing which of six files to open first. The pipeline didn't just fail — it failed at the right place, with the right explanation, which is the entire difference between a script you can fix in thirty seconds and one you're debugging for an hour.

## The Objection: "Isn't Five Separate Files Just More Complexity for No Real Benefit?"

Reasonable pushback — one file is simpler to read top to bottom, one file is easier to find things in, so why deliberately split working code into five pieces that now have to import from each other?

Let's actually test the claim that one file is easier to work with, using a real scenario: your model choice changes. Say you switch from `llama3.2:3b` to a different model in Chapter 2's family, and you need to update how prompts get built.

With the five-file structure, the fix is exactly one line, in exactly one file, `generate.py`, and nothing else in the pipeline needs to be touched, read, or even understood to make that change safely. With the single `everything.py` file from the top of this chapter, that same change means scrolling through scraping logic, cleaning logic, and rendering logic just to find the one relevant line — and worse, it means any typo you make while scrolling past unrelated code risks breaking a completely different stage by accident, since it's all sharing the same file and the same variable scope. Five files aren't more complex. They're the same complexity, organized so that each piece of it stays contained instead of leaking into everything else.

There's a deeper reason this matters specifically for this pipeline, though, and it connects straight back to Chapter 7: your validator's entire credibility rests on knowing, with certainty, that it's checking real generate-stage output against real structure-stage source text — not some blended, half-scraped, half-cleaned mess that got tangled together because two stages shared code they shouldn't have. Separation isn't just about tidiness. It's what lets you trust that when validation says "approved," it actually checked what you think it checked.

## Chapter Summary

Wiring five working pieces into one giant script feels efficient, but it trades away the one thing that actually matters once something breaks — knowing where, and why. Keeping scrape, structure, generate, validate, and render as five separate files, each with one clear job and its own loud, specific failure mode, means a broken page layout, a bad source, or a rejected citation surfaces immediately, at the exact stage it happened, instead of as a mystery crash three files downstream. The extra file count isn't complexity for its own sake — it's what keeps each stage trustworthy on its own, which is exactly what lets a validator's "approved" actually mean something.

## Bridge to Chapter 10

Right now, running this pipeline still means you, personally, typing `python3 run_pipeline.py` and watching it go. That's a massive improvement over the copy-paste chat-window workflow from Chapter 3 — but it's still not automatic. Somebody still has to remember to run it, every single day, at a reasonable hour, and actually notice if it fails. The whole reason you built five clean, loudly-failing stages in this chapter, instead of one tangled script, is so that the next step becomes possible at all: letting this thing run completely on its own, on a schedule, catching its own failures without you standing over it. That's the next chapter.

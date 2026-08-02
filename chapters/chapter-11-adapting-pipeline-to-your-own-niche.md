<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 11: Adapting the Pipeline to Your Own Niche

## The Recipe Blog That Ran on the Exact Same Code as the RBI Pipeline

Let's end this book with a genuinely satisfying experiment. Take everything you've built — every file, every function, every rule from Chapters 4 through 10 — and point it at something that has absolutely nothing to do with monetary policy. Say, home cooking recipes.

```bash
$ python3 code/run_pipeline.py
```

Same five stages, same log format, same `[STAGE: ...]` output you've been staring at since Chapter 9. Open the rendered card, and instead of an RBI rate decision, you've got a clean, sourced, fact-checked line about how long dal tadka actually needs to simmer, pulled straight from a real recipe page, with the exact same bracketed-citation grounding underneath it that once protected a repo rate figure. Nothing about the actual pipeline code changed to make this happen. Not the scraper's cleaning logic. Not the chunker. Not the validator's matching function. Not the render card's layout. Genuinely, two things changed, and two things only — which brings us to the real argument of this final chapter.

## Why the Architecture Never Cared What Topic You Feed It

Here's the idea this whole book has been quietly proving, one chapter at a time, without making a big deal of it until now: everything you built is domain-agnostic by design, because every single decision in Chapters 4 through 10 was about *how* to handle information — how to source it responsibly, how to clean it, how to force a model to stay inside it, how to check it, how to present it, how to run it unattended — and never about *what* the information happened to be.

The permanent pipeline lives in the [`code/`](../code/) directory. Here's what each file does, and which two you actually touch when you change niches:

| File | Job | Do you change it for a new niche? |
|------|-----|-----------------------------------|
| [`scrape.py`](../code/scrape.py) | Fetch the page, fail loudly if content is missing | **Yes — the URL(s)** |
| [`structure.py`](../code/structure.py) | Clean HTML + chunk text | No |
| [`generate.py`](../code/generate.py) | Build the grounded prompt + call the model | **Yes — the question** |
| [`validator.py`](../code/validator.py) | Low-level quote matching | No (threshold only, if stakes change) |
| [`validate_response.py`](../code/validate_response.py) | Extract citations and approve/reject | No |
| [`render_card.py`](../code/render_card.py) | Turn approved text into an image card | No |
| [`run_pipeline.py`](../code/run_pipeline.py) | Orchestrator — calls the five stages in order | Yes — pass the new URL + source name |
| [`check_last_run.py`](../code/check_last_run.py) | Report whether the last cron run succeeded | No |

Let's prove the claim by looking at exactly which two things had to change to go from financial news to recipes.

### Change one — the source in `scrape.py` / `run_pipeline.py`

```python
# Before — Chapter 4's financial sources
url = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
source_name = "Reserve Bank of India"

# After — same files, same functions, new topic
url = "https://example-recipe-site.com/dal-tadka"
source_name = "Example Recipe Site"
```

That's it. Same [`scrape_source()`](../code/scrape.py) function, same `ScrapeError` handling, same "fail loudly if the article tag is missing" logic — because a recipe site missing its content is exactly as much of a real problem as a government site missing its content, and your scraper already treats both that way, without needing to know or care which one it's looking at.

### Change two — the question inside `generate.py`

```python
# Before — financial question
question = "What is the key decision or announcement in this release?"

# After — same file, same grounding rules, new question
question = "What ingredients and cooking time does this recipe require?"
```

Look closely at what *didn't* change — and this is the actual proof of this chapter's argument. All the grounding rules from Chapter 6 are still sitting untouched inside [`build_prompt()`](../code/generate.py):

1. Only state facts that appear in SOURCE.
2. Bracket the exact quoted phrase for every claim.
3. Say `'Not stated in source.'` when the source doesn't cover it.
4. No added analysis or predictions.

Those rules don't know or care whether SOURCE is a press release or a recipe. They were never written about monetary policy in the first place — they were written about the general, structural problem of models drifting away from whatever text you hand them, which is exactly as true for cooking times as it is for interest rates.

```bash
$ python3 -c "
from validate_response import validate_response
answer = 'This dal tadka needs to simmer for 20 minutes [simmer on low heat for 20 minutes until softened].'
source = 'Add the dal to boiling water and simmer on low heat for 20 minutes until softened, stirring occasionally.'
print(validate_response(answer, source))
"

{'status': 'approved', 'citations': [{'quote': 'simmer on low heat for 20 minutes until softened', 'valid': True, 'score': 1.0}]}
```

Same [`validate_response()`](../code/validate_response.py) function, same [`validate_citation()`](../code/validator.py) underneath it, unmodified, checking a cooking claim with exactly the same rigor it checked a repo rate figure back in Chapter 7. That's not a coincidence — that's the actual payoff of every "keep this file doing only one job" decision made in Chapter 9. A validator built to check whether a phrase exists in a source doesn't need to understand finance or cooking. It just needs to understand matching, which is the same problem no matter what the words are about.

## The Objection: "Surely Niche Topics Need Their Own Custom Rules — Isn't 'One Size Fits All' Naive Here?"

This is a real, fair pushback, and it's worth taking seriously rather than pretending every topic is identical — surely something like health advice, legal information, or breaking news needs stricter handling than a recipe or a rate decision. Doesn't claiming the architecture "just works" for anything oversimplify some genuinely higher-stakes domains?

The honest answer is: the *architecture* transfers completely, but the *judgment calls layered on top of it* absolutely shouldn't stay identical, and this book was never arguing they should.

Go back to the validator threshold in [`validator.py`](../code/validator.py) — remember, you can deliberately tighten or loosen how strict the word-matching needs to be, on purpose, as a conscious decision:

```python
# Recipe pipeline — slight paraphrase is fine
validate_citation(quote, source, threshold=0.75)

# Health or legal pipeline — demand near-exact matches
validate_citation(quote, source, threshold=0.92)
```

For a recipe pipeline, a slightly loose paraphrase match might be perfectly fine — nobody's harmed if "simmer for around 20 minutes" gets approved against a source saying "simmer for 20 minutes." For a health information pipeline, you'd want that threshold pushed as tight as it'll go, maybe even requiring exact matches only, because the cost of a subtly wrong claim slipping through is genuinely higher. Same file, same function, same architecture — different number, chosen deliberately for the actual stakes of the topic.

The same goes for source selection in Chapter 4 — a recipe pipeline can reasonably pull from a handful of well-regarded cooking sites, but a health or legal pipeline should probably lean much harder toward official, credentialed sources only, exactly the same instinct that pointed this book at the RBI and PIB instead of a general news aggregator. The architecture gives you the scaffolding — scrape, structure, generate, validate, render, each with one job, each failing loudly. What you build on top of that scaffolding — how strict, how narrow, how cautious — is a decision you make deliberately for each domain, not something the code decides for you. That's not a weakness in the design. That's exactly what makes it worth reusing instead of rebuilding from scratch every time you change topics.

## How to Actually Switch Niches (Checklist)

1. Open [`run_pipeline.py`](../code/run_pipeline.py) (or call it with new arguments if you've extended it).
2. Change the `url` and `source_name`.
3. Change the `question` passed into [`build_prompt()`](../code/generate.py).
4. (Optional) Adjust the validation `threshold` in [`validator.py`](../code/validator.py) / [`validate_response.py`](../code/validate_response.py) if the new domain has higher or lower stakes.
5. Run once by hand:
   ```bash
   python3 code/run_pipeline.py
   ```
6. Confirm the stages succeed and the card looks right.
7. Leave the cron job from Chapter 10 alone — [`check_last_run.py`](../code/check_last_run.py) will keep watching the same log file.

That's the entire migration path. No new modules. No rewritten validator. No second renderer.

## Chapter Summary

Everything built across this book — the model chosen for hardware fit, the disciplined scraping, the cleaning and chunking, the bracketed-citation prompting, the mechanical validator, the rendered artifact, the cron-scheduled automation — was never actually about financial news. It was about handling information responsibly, in a way that happens to work identically whether the source is a central bank's press release or a recipe blog. Swapping topics means touching exactly two things — where you scrape from, and what question you ask — while the entire trust architecture underneath stays exactly as it was. And genuinely higher-stakes topics don't need a different architecture; they need the same architecture, with its existing dials — validation thresholds, source strictness — turned deliberately tighter.

## Where You Actually Are Now

You didn't just read eleven chapters about a hypothetical pipeline. You've now got, sitting in front of you, a working understanding of every piece of a real system:

- a model that fits your hardware and your task  
- code that talks to it without a human in the loop → [`generate.py`](../code/generate.py)  
- disciplined sourcing that respects the difference between real evidence and internet noise → [`scrape.py`](../code/scrape.py)  
- cleaning and chunking that keeps a model from drowning in cookie banners → [`structure.py`](../code/structure.py)  
- prompting that builds an actual fence around what the model is allowed to claim → [`build_prompt()`](../code/generate.py)  
- a validator that trusts nothing the model says about itself → [`validator.py`](../code/validator.py) + [`validate_response.py`](../code/validate_response.py)  
- a renderer that turns verified truth into something worth sharing → [`render_card.py`](../code/render_card.py)  
- five files that each fail loudly instead of quietly → wired by [`run_pipeline.py`](../code/run_pipeline.py)  
- a scheduler that runs the whole thing while you sleep, plus a health check → [`check_last_run.py`](../code/check_last_run.py)

None of it was ever really about Raspberry Pis, or RBI press releases, or repo rates. Those were just the material this book used to make every idea checkable, the same discipline Chapter 4 insisted on for your own sources. The actual thing you've built is smaller and more useful than any single topic — it's a way of handling information you can now point at whatever you actually care about. Sports stats, local news, your own niche hobby, your college's exam notifications, your neighborhood's civic updates — the five files don't know the difference, and now, neither should you.

The scaffolding's done. What you build on it from here is entirely yours.

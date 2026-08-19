<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 1: The Hallucination Problem

## The Model That Invents When It Has Nothing Real to Stand On

Open your local model and ask it to produce a short factual post about something specific — the same kind of task a content pipeline will ask it to do every day.

```bash
$ ollama run llama3.2:latest

>>> Write a two-sentence factual update for a finance audience about how the
>>> Reserve Bank of India's real-time gross settlement system reduced interbank
>>> settlement risk. Include one specific percentage and one year.

The Reserve Bank of India's full rollout of real-time gross settlement in 2013
cut overnight interbank settlement exposure by 47%, according to operational
data released with the system upgrade. Continuous settlement replaced the older
deferred net settlement window and removed the bulk of the risk that previously
accumulated between clearing cycles.
```

Two clean sentences. A precise year. A precise percentage. Institutional tone. Most readers would accept it.

Both numbers are invented. The model was not given any source text. It completed a plausible pattern: central bank + RTGS + round percentage + year that sounds right. That is a **hallucination** — a fluent, confident statement that is not grounded in anything real.

You may get a different invention, or a partial refusal, depending on the exact model build and temperature. That variance is normal. The underlying problem is the same: when the model has no source material, it still produces text that *looks* like sourced fact. A pipeline that publishes that text is publishing invention.

## Why "Just Ask Carefully" Is Not Enough

Newer small models refuse more often than older ones, especially on pure lookup questions ("What is the exact title and DOI of the 2023 paper…"). Try one and you may see:

```bash
>>> What is the exact title, authors, and DOI of the 2023 paper that measured
>>> a 47% reduction in interbank settlement risk after RBI RTGS rollout?

I couldn't find any information on a specific paper by Sharma, Patel, and
Kumar that measures a 47% reduction...
```

A refusal looks like progress. It is incomplete protection. The same model, asked to *write* rather than *retrieve*, will still invent percentages, years, and official-sounding names. In the earlier RTGS example it may refuse the paper and, in the next breath, invent a wrong system acronym or a launch year. The refusal covers the question you asked carefully. It does not cover the generation task a pipeline actually runs.

Stronger instructions do not close the gap either:

```bash
>>> Only use verified facts. If you are not certain, say "I don't know."
>>> Write a two-sentence update on RBI RTGS risk reduction with a specific
>>> percentage.

I don't have a verified percentage for risk reduction after RTGS adoption.
Operational reviews often cite substantial declines in overnight exposure;
one figure that appears in secondary summaries is around 47%.
```

It hedged, then still offered the invented number under softer language. The caution makes the false detail easier to trust, not harder.

An LLM does not query a database of facts. It predicts the next token from patterns in training data. "Cut exposure by __%" is a shape it has seen many times. The model has no internal mark that separates "I recall this figure" from "I am generating a figure that fits the shape." Both sound the same, because inside the model they are the same process.

## Why This Becomes Dangerous the Moment You Automate

In a private chat a hallucination is a minor annoyance. You notice the odd percentage, check it, move on.

This book is not about chatting. It is about building a **pipeline** that scrapes real sources, generates text, and produces a finished artifact — a post, a card, an image — without a human reviewing every output before it goes live.

Once that loop is automated, hallucination stops being an annoyance and becomes the central risk. A system that occasionally invents a percentage, a year, or an official name is no longer a content tool. It is a machine that can publish convincing misinformation on a schedule. The two main benefits of automation — speed and the absence of constant human supervision — are exactly what turn a small invention into a public error with your name on it.

So the bar cannot be "the model tries hard" or "the model refused the hard question." It has to be structural:

**Nothing the model generates is allowed into the final output unless it can be matched back to a real source you collected.**

Not "the model was told to be careful." Not "the model sounded confident." Actually matched, by code, to text you scraped. That is a design decision. It is why this pipeline has a scrape stage, a cleaning stage, and — the critical piece — a full chapter (Chapter 7) whose only job is a validator that checks every claim against the source and rejects anything that does not match.

## How the Rest of the Book Fixes This

There is no permanent code file in this chapter. The problem is conceptual. The fix is the five-stage pipeline assembled by Chapter 9:

| Stage | File | How it fights hallucination |
|-------|------|-----------------------------|
| Scrape | [`scrape.py`](../code/scrape.py) | Only real, chosen sources — not the model's memory |
| Structure | [`structure.py`](../code/structure.py) | Clean, chunked context the model must work from |
| Generate | [`generate.py`](../code/generate.py) | Prompts that force bracketed source quotes |
| Validate | [`validator.py`](../code/validator.py), [`validate_response.py`](../code/validate_response.py) | Mechanical check: does this quote exist in the source? |
| Render | [`render_card.py`](../code/render_card.py) | Only approved text becomes a finished artifact |

Wired together by [`run_pipeline.py`](../code/run_pipeline.py), scheduled and monitored in Chapter 10 ([`check_last_run.py`](../code/check_last_run.py)), and reused for any niche in Chapter 11.

The model's job is never to be trusted on its own. The structure is what makes the output trustworthy.

## The Obvious Question: "Won't a Bigger, Better Model Just Fix This?"

Bigger models hallucinate less often, especially on common facts. A frontier model is less likely to invent a wrong president or a completely fake formula than a 3B model on a Raspberry Pi. "Less often" is not "never." Even the largest models still lack a reliable internal signal that marks which tokens are recalled and which are smoothly invented. Scale changes frequency. It does not change the mechanism. When a large model invents a statistic or a citation, the tone is still fully confident.

You are also not free to pick the least-hallucinating model available. You are picking one that fits your hardware (Chapter 2). That usually means a smaller model and higher invention risk. If "just use a better model" were enough, this book would end here and would not run on a Pi. It does not end here, because the real fix is design: collect real source material, force the model to work only from that material, then check every claim mechanically before anything is published. A small model behind a proper validator beats a large model with none.

## What You Should See When You Try the Demo

Model builds differ. On some machines the first prompt invents a clean percentage and year. On others you get a refusal or a hedge. Both outcomes are useful:

- If it invents — you just watched the failure mode the pipeline is built to stop.
- If it refuses — notice that the same model will still invent when the task is ordinary generation without source text, or will invent adjacent details after a partial refusal. The lookup refusal does not protect a write-heavy pipeline.

Either way, the lesson is the same: do not trust the model's words unless those words can be traced to a source you control.

## Chapter Summary

An LLM without grounding cannot reliably tell you when it is inventing, because generation and recall are the same process. Newer models refuse more lookup questions, yet they still invent fluent details when asked to write, and they invent adjacent facts even after a refusal. Prompting does not close the gap. Scale reduces frequency but does not remove the mechanism. The danger becomes concrete the moment output is automated and published without a human check on every piece. The solution is not a smarter model. It is a pipeline in which every claim must survive a mechanical match against a real source before it reaches the final artifact.

That is the whole book stated as a problem: get real material, make the model generate only from it, then check mechanically that it actually did. Every following chapter builds one piece of that system. The assembled code lives in [`code/`](../code/).

## Bridge to Chapter 2

Before you can build the grounding and checking system, you need something to run it on. Model choice is not a one-time detail. It determines what fits in your Pi's memory, how fast answers arrive, whether the output stays short and factual or turns into essays, and how controllable the model is once Chapter 7's validator starts rejecting its work. Chapter 2 is about making that choice correctly: not by chasing whatever is trending, but by asking what your hardware can actually run and what your output needs to sound like.

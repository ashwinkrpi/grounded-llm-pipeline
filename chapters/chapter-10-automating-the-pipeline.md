<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 10: Automating the Pipeline

## The Guy Who Thought Automation Meant Rewriting Everything

There's a very specific, very avoidable mistake that happens right around this stage of building something like this. You've got [`run_pipeline.py`](../code/run_pipeline.py) working — genuinely working, end to end, scrape to rendered card, exactly like Chapter 9 left it. And then, instead of just... running it automatically, a weird instinct kicks in: "okay now I need to turn this into a REAL automated system," and suddenly people start rewriting the whole thing as some elaborate background service, adding message queues, adding a database, adding stuff that has nothing to do with the actual problem, which is just: *make this run by itself, on a schedule, without me typing the command.*

Here's the thing that's genuinely reassuring about this chapter, and it's worth saying upfront so you don't fall into that trap: you already did the hard part. Chapter 9 gave you a script that runs cleanly from one command, fails loudly at the right stage when something breaks, and produces one finished artifact per run. Automating that isn't a redesign. It's scheduling and watching — nothing about the actual pipeline logic needs to change at all.

## Why Automation Is a Scheduling Problem, Not a Rebuilding Problem

Let's prove this the most boring way possible, because boring is exactly the point. Your Pi already runs Linux, and Linux already ships with a tool built for exactly this — `cron`. No new framework, no new architecture, nothing to learn beyond one line of syntax.

First, confirm your pipeline genuinely runs clean from the command line, the same way it will once cron is calling it:

```bash
$ python3 /home/pi/grounded-pipeline/code/run_pipeline.py

[STAGE: scrape] SUCCESS
[STAGE: structure] SUCCESS
[STAGE: generate] SUCCESS
[STAGE: validate] APPROVED
[STAGE: render] SUCCESS — saved to output_card.png
```

Now open your crontab and add one line telling it to run this every morning at 7 AM:

```bash
$ crontab -e
```

```
# Grounded pipeline — runs daily at 7 AM
0 7 * * * /usr/bin/python3 /home/pi/grounded-pipeline/code/run_pipeline.py >> /home/pi/grounded-pipeline/code/logs/run.log 2>&1
```

That's genuinely it. That one line is your entire automation layer. `0 7 * * *` means "at minute 0 of hour 7, every day," and the `>> ... 2>&1` part sends both normal output and errors into a log file instead of vanishing into nothing, which matters a lot more than it sounds — Chapter 9's whole point was building loud, specific failures, and there's no use in a failure shouting into an empty terminal nobody's watching at 7 AM.

Create the log directory once before the first scheduled run:

```bash
$ mkdir -p /home/pi/grounded-pipeline/code/logs
```

Let's check it actually worked the next morning:

```bash
$ cat /home/pi/grounded-pipeline/code/logs/run.log

[STAGE: scrape] SUCCESS
[STAGE: structure] SUCCESS
[STAGE: generate] SUCCESS
[STAGE: validate] APPROVED
[STAGE: render] SUCCESS — saved to output_card.png
```

Same output, same pipeline, zero code changes — it just happened while you were asleep, and now there's a written record proving it. That's the whole leap from Chapter 9 to here: not new architecture, just handing the "press run" job to something that never forgets and never sleeps in.

But scheduling alone isn't quite the full picture, and this is the part that separates "technically automated" from "automated and trustworthy." Chapter 9 taught your pipeline to fail loudly — but loud only matters if someone's actually listening. A failure sitting quietly inside a log file nobody checks is functionally the same as a silent failure. So let's add one more small, unglamorous piece: a way to actually notice when a run goes wrong, without you personally opening that log file every single morning.

That piece is [`check_last_run.py`](../code/check_last_run.py):

```python
# check_last_run.py (see code/check_last_run.py for the full file)
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "logs" / "run.log"

def check_last_run():
    if not LOG_PATH.exists():
        return "NO LOG FOUND — pipeline may never have run"

    lines = LOG_PATH.read_text().strip().splitlines()
    last_run_lines = lines[-8:]

    failures = [l for l in last_run_lines if "FAILED" in l or "REJECTED" in l or "ERROR" in l]
    if failures:
        return "LAST RUN HAD ISSUES:\n" + "\n".join(failures)
    return "LAST RUN OK"

if __name__ == "__main__":
    print(check_last_run())
```

```bash
$ python3 code/check_last_run.py

LAST RUN OK
```

Wire this into cron too, a few minutes after the main job, and now you've genuinely got a self-reporting system — one that runs on its own, and tells you clearly when it hasn't behaved, instead of trusting you to go digging for problems:

```
# Grounded pipeline — daily run + health check
0 7 * * * /usr/bin/python3 /home/pi/grounded-pipeline/code/run_pipeline.py >> /home/pi/grounded-pipeline/code/logs/run.log 2>&1
5 7 * * * /usr/bin/python3 /home/pi/grounded-pipeline/code/check_last_run.py >> /home/pi/grounded-pipeline/code/logs/health.log 2>&1
```

## The Code Files This Chapter Uses

Everything automation needs is already in [`code/`](../code/). You do not rewrite the pipeline to automate it — you schedule it and watch it.

| File | Role in automation |
|------|--------------------|
| [`run_pipeline.py`](../code/run_pipeline.py) | The single command cron actually runs |
| [`scrape.py`](../code/scrape.py) | Stage 1 — unchanged |
| [`structure.py`](../code/structure.py) | Stage 2 — unchanged |
| [`generate.py`](../code/generate.py) | Stage 3 — unchanged |
| [`validator.py`](../code/validator.py) | Stage 4 helper — unchanged |
| [`validate_response.py`](../code/validate_response.py) | Stage 4 — unchanged |
| [`render_card.py`](../code/render_card.py) | Stage 5 — unchanged |
| [`check_last_run.py`](../code/check_last_run.py) | Health check that reads the log and reports failures |

## The Objection: "Shouldn't a Real Production System Use Something Better Than Cron?"

Fair question if you've spent any time around software engineering conversations — cron feels almost embarrassingly basic, and there's a whole world of proper task schedulers, systemd timers, workflow orchestrators, message queues, all built for exactly this kind of "run this thing on a schedule" job. Doesn't reaching for cron mean you're cutting corners?

Worth testing this claim against what your actual pipeline needs, rather than what sounds impressive. Those heavier tools genuinely earn their complexity when you've got many interdependent jobs, jobs that need to coordinate with each other in real time, jobs running across multiple machines, or jobs where a few seconds of scheduling drift actually matters. None of that describes this pipeline. You have one job, running once a day, on one machine, producing one artifact, with a hard requirement of "don't crash silently" — which Chapter 9's exception handling and this chapter's log file already solve completely. Reaching for a heavier orchestration tool here wouldn't make the pipeline more reliable. It would just mean more moving parts sitting on a Raspberry Pi that, remember, you specifically chose in Chapter 2 because it's modest, low-power hardware — not a server farm.

There's a more honest way to frame this decision, actually: the right tool for automation isn't the most impressive-sounding one, it's the smallest one that fully covers what you actually need. Cron has been reliably running scheduled jobs on Unix systems for decades, precisely because the actual problem — "run this at a specific time, every day, without fail" — hasn't fundamentally changed in that time either. If your pipeline someday genuinely grows into something with multiple interlinked jobs across several machines, that's a real signal to revisit this decision. Until then, upgrading your scheduler before your actual needs demand it is just Chapter 9's "one giant file" mistake wearing different clothes — added complexity that doesn't fix a problem you actually have.

## Optional: Structured Logging Instead of Bare Redirect

The `>> run.log 2>&1` approach is enough for this book. If you later want timestamps, levels, and rotation on a Pi that runs for months, you can add a small logging setup and keep the same stage messages. The important part stays the same: failures must still surface as clear `FAILED` / `REJECTED` lines so [`check_last_run.py`](../code/check_last_run.py) can find them.

Until you need that, stick with the simple redirect. Boring is a feature here.

## Chapter Summary

Automating a working pipeline isn't a redesign — it's handing the "press run" step to something that never forgets, and making sure failures get noticed instead of sitting silently in a log nobody reads. One `cron` line turns your Chapter 9 script ([`run_pipeline.py`](../code/run_pipeline.py)) into something that runs itself every morning, and a small log-checking script ([`check_last_run.py`](../code/check_last_run.py)) closes the loop by actually surfacing failures instead of trusting you to go looking for them. Reaching for a heavier scheduling tool than cron isn't more professional here — it's solving a scale problem you don't actually have, on hardware that was deliberately chosen to stay modest.

## Bridge to Chapter 11

Here's something worth noticing about everything you've built across these last nine chapters: not one piece of it — not the scraper, not the cleaner, not the prompt rules, not the validator, not the renderer, not this morning's cron job — actually cares that the topic is Indian financial news. That specificity only ever lived in two places: which URLs [`scrape.py`](../code/scrape.py) was pointed at, and what question [`generate.py`](../code/generate.py) asked the model. Everything else — the RAM-fit model choice, the disciplined sourcing, the cleaning and chunking, the bracketed-citation grounding, the mechanical validation, the rendered card, the daily cron job — all of it is sitting there, fully built, completely unbothered by what subject it's actually working on. Which raises the real question this book has been quietly building toward the entire time: if none of this cares about the topic, what happens when you point it at something that isn't finance news at all? That's the last chapter.

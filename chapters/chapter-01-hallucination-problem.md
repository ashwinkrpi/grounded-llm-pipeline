<!--
© 2026 ashwinkrpi. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 1: The Hallucination Problem

## The Model That Lies With Full Confidence

Let's do a small experiment first, no cap. Open your local model — doesn't matter which one, Ollama, whatever, they all do this same thing — and ask it something specific. Something you can actually check. Not some big fancy question like "explain quantum computing." A small, factual question.

```bash
$ ollama run llama3.1

>>> What was the closing price of Nvidia stock on March 14, 2024, 
>>> and who was the CEO who announced their Q4 earnings that quarter?

Nvidia's stock closed at $926.69 on March 14, 2024. CEO Jensen Huang
announced record Q4 earnings that quarter, citing strong demand for
the H100 GPU driven by AI infrastructure spending.
```

Bro, look at that answer. Sounds so correct, right? There's a proper dollar number, a real CEO name, a real product name. It's giving "confident finance analyst" energy.

Problem is — it's wrong. Not "thoda different" wrong. The actual number that day was not this. And the model didn't take this number from anywhere real. It just generated something that *looks like* a stock price, in the format a stock price usually comes in, next to a real company and a real CEO name. That's the whole trap here. This is not some broken, jumbled-up sentence you can catch easily. It's a fully correct-looking, fully confident, 100% made-up fact — said in the exact same tone as everything else the model gets right.

This is called a **hallucination**. And if you're building something that will actually get posted, shared, or read by real people — this one issue is literally the whole game. Every single chapter after this one exists only to fix this problem.

## Why You Can't Just "Prompt Your Way" Out of This

First reaction everyone has — "oh it's just a prompting issue na, I'll just tell it to be careful." Add a line like "only say facts you're 100% sure about." Add "if you don't know, just say you don't know."

Let's try:

```bash
>>> Only answer with verified facts. If you are not certain, say 
>>> "I don't know." What was Nvidia's closing stock price on 
>>> March 14, 2024?

Nvidia's stock closed at approximately $926.69 on March 14, 2024.
```

Same wrong number. Just now it has "approximately" stuck in front, which honestly makes it sound *more* trustworthy — like the model is being careful about a real fact it's half-remembering, instead of just inventing one out of nowhere.

Here's what's actually happening, and it's worth understanding this properly instead of just accepting it: an LLM does not have a database where it looks up facts. It has a very strong sense — built from tons and tons of text — of what word usually comes after the last one. So when you ask it for Nvidia's stock price on a specific date, it's not pulling up a record. It's completing a pattern. "Nvidia's stock closed at $" is very likely followed by a number that *looks* like a real Nvidia price, in the range Nvidia usually trades in. The model has zero internal system to tell the difference between "I actually remember this" and "I'm generating something that fits this pattern." Both come out sounding exactly the same, because inside the model, it's literally the same process. There's no fact-checker sitting behind the scenes vetoing bad answers. The smooth talking and the made-up facts come from the exact same place.

This is exactly why prompting alone can't solve this. You can't tell a system to separate "remembered" facts from "generated" facts when it never made that separation in the first place. Telling a hallucinating model to "be more careful" is like telling someone who's really good at improv to only improvise when they don't actually know the answer — but the whole issue is, the improv doesn't feel like improv to them. It feels the same as knowing.

## Why This Matters Even More When You're Publishing Stuff

If you're just chatting with the model for yourself, casually, a hallucination is a small annoyance. You spot it, double check that one number, and move on. No big deal.

But this book isn't about chatting. It's about building a **pipeline** — something that scrapes real content, generates stuff from it automatically, and produces a finished thing — a post, a card, a summary image — without you personally checking every single output before it goes live.

The second you automate that loop, hallucination stops being a small annoyance and becomes the biggest risk in your whole system. A pipeline that occasionally makes up a stat, wrongly quotes someone, or states a date that never even happened — that's not a content pipeline anymore. That's a machine that's manufacturing convincing-looking misinformation, on whatever schedule you set it to run. The whole point of automation is speed and not needing to babysit it — but those exact two things are what turn one small hallucination into a real problem. One wrong number in a private chat, nobody cares. One wrong number in something that got auto-posted publicly, with your name on it — that's an embarrassing correction, or worse, something nobody even catches.

So the bar for this pipeline can't just be "the model tries its best to be accurate." It has to be built into the structure itself: **nothing the model generates makes it to the final output unless it can be matched back to a real source you actually collected.** Not "the model was told to be careful." Not "the model sounded confident." Actually matched, mechanically, to real text you scraped. This isn't a prompt trick — it's a design decision. That's exactly why this pipeline has a scraping stage, a cleaning stage, and — this is the important one — a full chapter (Chapter 7) dedicated purely to a validator whose only job is checking every single claim against the source and throwing it out if it doesn't match.

## The Obvious Question: "Won't a Bigger, Better Model Just Fix This?"

Fair question, and worth actually answering properly, because a lot of people assume yes and get burned later.

Honest answer: bigger models hallucinate *less*, especially for common, well-known facts. A big frontier-level model is less likely to randomly invent a wrong president or a wrong formula than a small model running on your Raspberry Pi. But "less often" is not the same as "never" — and there's a real reason bigger size doesn't fix the actual problem: even the biggest model still has no built-in way to tell you which part of its answer it's actually sure about, versus which part it's just smoothly filling in. Bigger size lowers how often it happens. It does not change *how* it happens. Even the top commercial models out there — way bigger than anything you'll run at home — still get dates wrong, misquote sources, and even make up fake research papers that don't exist. Less often, yes. Still happens, and when it does, it sounds just as confident as ever.

There's a second reason this matters specifically for you: you're not picking a model based on which one hallucinates least overall. You're picking one that actually fits your hardware — that's the whole topic of Chapter 2 — which usually means going smaller, which actually means *more* hallucination, not less. If "just use a good model" was really the fix, this book would be over right here, and it definitely wouldn't work on a Raspberry Pi. It's not over, because the real fix isn't model quality — it's the design. Get real source material first, force the model to only generate based on that material, then independently double-check every single claim before anything gets published. A small model with a proper validation step beats a huge model with none, because the validation step is what actually catches the lie. In this pipeline, the model's job is never to be trusted on its own.

## Chapter Summary

An LLM without proper grounding isn't just unreliable sometimes — it genuinely can't tell you when it's making something up, because generating something believable and remembering something true happen through the exact same process inside it. Telling it to "be careful" doesn't fix that, because there's no internal signal separating confident guessing from confident recall. This becomes a real danger specifically when you automate things — when content goes out without you checking every piece — which is literally what this book is teaching you to build. And no, a bigger, better model doesn't solve this either; the real fix is to stop trusting the model as the source of truth at all, and instead build a pipeline where every single claim has to survive being checked against a real source before it ever reaches your final output.

That's basically the whole book, said as a problem instead of a solution: get real material, make the model generate only from it, then check mechanically that it actually did. Every chapter from here is one piece of building that system.

## Bridge to Chapter 2

But before you can build any of this grounding and checking system, you need something to actually run it on. And picking your model isn't some small one-time decision you forget about — it decides what actually fits in your Pi's memory, how fast (or slow) each answer comes out, whether your output sounds short and fact-heavy or long and essay-like, and even how easy the model is to control later, once Chapter 7's validator starts checking its work properly. Chapter 2 is about making this choice the right way — not by asking "which model is trending right now," but by asking the two questions that actually matter: what your hardware can actually handle, and what you need your output to sound like.

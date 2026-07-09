<!--
© 2026 ashwinkrpi. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 2: Choosing and Installing Your Local Model

## The Model Everyone's Hyping Up Might Straight Up Not Run on Your Pi

Okay so here's a scene that happens to literally everyone starting out. You go on YouTube, you see some guy with a fancy gaming laptop saying "bro this new model is INSANE, everyone should be using it." You get hyped, you go home, you open your Raspberry Pi, you try to install that same model...

```bash
$ ollama run llama3.1:70b

pulling manifest 
Error: model requires more system memory (44.0 GiB) than is available (7.6 GiB)
```

And that's it. Game over before it even started. Your Pi just looked at that 70-billion-parameter model and said "nah bro, not happening." This isn't a rare situation — this is basically what happens to every single beginner who picks a model because it's trending, instead of picking one because it actually fits their machine.

This is the mistake this whole chapter is trying to save you from. Choosing a model isn't a "which one is the coolest" question. It's a hardware question first, and a task-fit question second. Get those two right, and everything after this — the scraping, the prompting, the validation — actually works. Get it wrong, and you're stuck watching error messages instead of building anything.

## Why "Best Model" Is the Wrong Question

Let's be real clear about something: there is no single "best" local model. That question doesn't even make sense, the same way "what's the best vehicle" doesn't make sense — best for what, carrying how much, on what road? A model that's amazing for writing long, flowery essays might be a terrible pick for a pipeline that needs quick, structured, fact-checkable output. A model that's brilliant but needs 44 GB of RAM is useless to you if your Pi has 8 GB. So instead of "best," you need to ask two much smaller, much more useful questions: **What can my hardware actually carry? And what does my output actually need to sound like?**

Let's sort out hardware first, because it's non-negotiable — no amount of good prompting fixes a model that literally cannot fit in memory.

Check what you're working with:

```bash
$ free -h

              total        used        free      shared  buff/cache   available
Mem:          7.6Gi       412Mi       6.4Gi        12Mi       812Mi       6.9Gi
Swap:          99Mi          0B         99Mi
```

That's a standard 8 GB Raspberry Pi. Now here's the rough rule everyone in the local-LLM space uses, and it's simple enough to remember: **a model roughly needs RAM equal to its size on disk, plus a bit extra for the actual conversation you're having with it.** So a 4 GB model needs somewhere around 5-6 GB free to run comfortably. A 40 GB model needs, well, 40-something GB, which your Pi just doesn't have and isn't going to magically get.

This is why model names have those little size tags on them — `1b`, `3b`, `8b`, `70b` — and that number is literally telling you how many billion parameters the model has, which directly maps to how much space and RAM it eats up. Bigger number, smarter model generally, but also bigger memory bill. On an 8 GB Pi, you're realistically living in the `1b` to `8b` range. Anything above that and you're just going to keep seeing that same error message from earlier.

Let's actually go pull something that fits. First, install Ollama if you haven't already:

```bash
$ curl -fsSL https://ollama.com/install.sh | sh

>>> Installing ollama to /usr/local
>>> Downloading Linux arm64 bundle
######################################################################## 100.0%
>>> Creating ollama user...
>>> Adding current user to ollama group...
>>> Creating ollama systemd service...
>>> Enabling and starting ollama service...
>>> NVIDIA GPU installed.
>>> The Ollama API is now available at 127.0.0.1:11434.
```

Now pull a model that's actually sized for a Pi:

```bash
$ ollama pull llama3.2:3b

pulling manifest 
pulling dde5aa3fc5ff... 100% ▕████████████████▏ 2.0 GB
pulling 966de95ca8a6... 100% ▕████████████████▏ 1.4 KB
pulling fcc5a6bec9da... 100% ▕████████████████▏ 7.7 KB
pulling a70ff7e570d9... 100% ▕████████████████▏ 6.0 KB
verifying sha256 digest
writing manifest
success
```

That's a 2 GB download for a model that comfortably runs inside your Pi's 8 GB of RAM, with room left over for your OS and whatever else is running. Compare that to the 44 GB monster from earlier — same "run this model" command, completely different outcome, because this one actually respects what your hardware can handle.

Now the second question — task fit. Run the model and give it something close to what your actual pipeline will need it to do:

```bash
$ ollama run llama3.2:3b

>>> Summarize this in one factual sentence, no extra commentary:
>>> "The Reserve Bank of India kept the repo rate unchanged at 6.5% 
>>> for the eighth consecutive time in its latest monetary policy 
>>> meeting, citing ongoing inflation concerns."

The RBI held the repo rate at 6.5% for the eighth straight meeting 
due to inflation concerns.
```

Notice what you're actually checking here — not "is this smart," but "does this behave the way I need it to." Did it follow the instruction (one sentence, factual, no extra fluff)? Did it stay close to the source instead of wandering off and adding its own opinions? That's the real test. A model that writes beautiful, long, creative paragraphs might genuinely be a bad fit for this book's pipeline, where you specifically want short, tight, source-anchored output. A model that sounds a bit robotic and dry might actually be perfect for this exact use case. "Good" and "right for the job" are two completely different things, and this book only cares about the second one.

## The Objection: "Can't I Just Use the Biggest Model My Pi Can Barely Handle?"

Totally fair thing to think — "bigger is smarter, so let me just squeeze in the biggest one that technically loads." Let's actually test that logic instead of just arguing about it.

```bash
$ ollama pull llama3.1:8b

pulling manifest 
pulling 8eeb52dfb3bb... 100% ▕████████████████▏ 4.7 GB
success

$ time ollama run llama3.1:8b "Summarize this in one sentence: 
The Reserve Bank of India kept the repo rate unchanged at 6.5%."

The RBI kept the repo rate steady at 6.5%, its latest monetary 
policy decision, reflecting continued caution amid inflationary 
pressures and a measured approach to economic stability.

real    0m47.312s
```

Compare that to the 3b model from earlier, which gave a similarly correct answer in a fraction of that time, using less than half the RAM, with less risk of your Pi's fans screaming and the whole system slowing down while it's thinking. Yes, technically the 8b model "fits" — barely, if nothing else is running, and if you're patient. But here's the thing this book cares about: your pipeline isn't going to run once. It's going to run automatically, over and over, on a schedule, probably alongside a scraper and a renderer that also need CPU and memory. A model that just barely squeezes in when it's the only thing running is going to be a nightmare once it's one piece of a five-part automated system. "Barely fits alone" is not the same as "fits inside a pipeline," and that difference is going to matter a lot more in Chapter 9 than it does right now.

The honest answer is: pick the smallest model that still does your specific task well. Not the smallest one period, and not the biggest one that technically loads — the smallest one that still gives you output you're happy with, for the exact narrow job you're asking it to do. For a pipeline built around short, factual, source-anchored writing, that's very often a 3b model, not an 8b one. Save the bigger stuff for when you genuinely need heavier reasoning, and even then — think hard before running it on a Pi at all.

## Chapter Summary

Picking a local model isn't about chasing whatever's trending — it's a two-part decision that actually determines whether your pipeline runs at all. First, check your hardware honestly with something like `free -h`, and match the model's size to what you actually have available, because no clever prompt fixes a model that literally can't fit in RAM. Second, test the model against the actual task you need it to do — short, factual, structured output, in this book's case — instead of judging it on how impressive or creative it sounds in general. And bigger isn't automatically better: a model that barely fits when it's running alone is going to cause real problems once it becomes one part of a bigger automated system.

## Bridge to Chapter 3

Right now, everything you've done has been through that `ollama run` command, typing questions directly and reading answers straight off your screen. That's perfectly fine for testing — it's literally what you just used to check if a model fits your task. But notice something about it: every single time, you had to be sitting there, typing the question yourself, reading the answer yourself. There's a human in the loop for every single step. A pipeline can't work like that. It needs to ask the model a question automatically, get the answer back in a format code can actually read, and move on to the next step — all without you typing anything. That means stepping away from that chat window entirely and talking to your model the way your code will need to talk to it. That's exactly where we're headed next.

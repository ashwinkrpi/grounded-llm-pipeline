<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 3: Talking to Your Model in Code, Not Chat

## The Pipeline That Broke Because a Human Wasn't Home

Picture this. You've built a nice little setup — every morning at 7 AM, you sit down, open the Ollama chat window, type in your prompt, copy the answer, paste it into a doc, and post it. Works perfectly for two weeks straight. You're feeling good, telling your friends "bro I built an automated content thing." Then one Tuesday you sleep through your alarm. Nothing gets posted. Wednesday you're stuck in a family function the whole morning. Nothing gets posted again. By Friday you realize — this was never actually automated. It was just you, doing a repetitive task, with a chatbot as your typing assistant. The second you weren't available, the whole thing stopped existing.

That's the exact trap this chapter is here to pull you out of. A chat window feels like a pipeline because it's fast and it works. But "works when I'm sitting here typing" and "works automatically, every single day, without me" are two completely different systems. And the difference between them isn't a small tweak — it's a whole different way of talking to your model.

## Why Chat Was Never Built for This

Let's be precise about what a chat window actually is. When you type into `ollama run llama3.2:3b` and hit enter, you are a human, manually starting a program, manually typing input, manually reading output, and manually deciding what to do with that output next. Every single one of those four steps needs you. That's fine for testing — that's literally what you did in Chapter 2 to check if a model fit your task. But a pipeline, by definition, needs to run those same four steps with zero humans involved. Something else needs to start the request, send the input, receive the output, and hand it to the next step — automatically, on a schedule, at 3 AM if needed, while you're asleep.

The good news is, Ollama isn't only a chat window. Underneath that `ollama run` command, there's a proper API quietly running on your machine, and you can talk to it directly with plain code instead of a keyboard. Let's prove this actually works, step by step.

First, check the API is alive:

```bash
$ curl http://localhost:11434/api/tags

{"models":[{"name":"llama3.2:3b","model":"llama3.2:3b","modified_at":
"2026-06-02T09:14:22Z","size":2019393792,...}]}
```

That's your model, sitting there, ready to be talked to — not through a chat window, but through a proper HTTP endpoint, the exact same way a website talks to a server. Now let's actually send it a request using `curl`, no chat window involved at all:

```bash
$ curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Summarize in one sentence: The RBI kept the repo rate 
  unchanged at 6.5% for the eighth straight meeting.",
  "stream": false
}'

{"model":"llama3.2:3b","created_at":"2026-07-09T04:12:08Z",
"response":"The RBI held the repo rate steady at 6.5% for the 
eighth consecutive meeting.","done":true,"total_duration":
3821004958,"eval_count":19}
```

Look closely at what came back. It's not just a sentence sitting on your screen — it's a proper JSON object, with the actual answer tucked inside a `"response"` field, alongside stuff like how long it took and how many tokens it generated. This is a massive deal, and it's easy to miss why. A chat window gives you text meant for human eyes. This gives you structured data meant for a program to read, pick apart, and pass along to the next step of your pipeline — which is exactly what Chapter 9 is going to need when it wires all five files together.

Now let's actually write the code your pipeline will use, instead of typing `curl` commands by hand. Here's a small Python script that does the exact same thing:

```python
# talk_to_model.py
import requests

def ask_model(prompt, model="llama3.2:3b"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    data = response.json()
    return data["response"]

if __name__ == "__main__":
    answer = ask_model(
        "Summarize in one sentence: The RBI kept the repo rate "
        "unchanged at 6.5% for the eighth straight meeting."
    )
    print(answer)
```

Run it:

```bash
$ python3 talk_to_model.py

The RBI held the repo rate steady at 6.5% for the eighth 
consecutive meeting.
```

Same answer. Except now, nobody typed anything into a chat window. This is a function — `ask_model()` — that any other piece of code can call, anytime, with any prompt, and get a clean answer back automatically. This one function, sitting quietly in one file, is the actual foundation this entire book is built on top of. Every later chapter — the validator checking claims, the renderer turning text into a graphic, the scheduler running everything at midnight — all of it is going to reach for a function exactly like this one, instead of a human typing into a window.

One quick heads-up before moving on: a few upcoming chapters will show commands like `python3 talk_to_model.py --prompt-file strong_prompt.txt --source pib_release.txt`. That's shorthand for "call `ask_model()` with a prompt built from that file and check it against that source" — it's describing the *behavior*, not a command-line flag this exact script has. Chapter 9 is where `talk_to_model.py` actually gets built out into its permanent, pipeline-ready form (renamed `generate.py`, with a proper `build_prompt()` function alongside `ask_model()`), so don't worry if you try one of those flagged commands here and it doesn't run — that's expected at this stage.

## The Objection: "Can't I Just Copy-Paste From the Chat Window Into My Script?"

This one comes up a lot, and it sounds reasonable on the surface — "why not just keep using the nice chat window for the actual thinking, and only automate the boring parts like posting?" Let's actually test what happens when you try that.

Say your plan is: chat window generates the text, you copy it, paste it into a text file, and a script reads that file and posts it. Fine for one run. But your pipeline in this book runs on scraped content that changes every single day — different headlines, different numbers, different sources. That means the prompt itself changes every day too, built automatically from whatever got scraped that morning. There's no way to "copy-paste" a prompt that a script generated fresh at 3 AM into a chat window, because there's nobody there at 3 AM to open the window in the first place. The moment your input has to change based on live data your code just pulled, the human-in-the-loop chat window isn't a shortcut anymore — it's a wall. It physically cannot work unattended, no matter how good your copy-paste habits are.

There's a second problem too, and it's sneakier. A chat window's output is designed to look nice for a person — sometimes it adds "Sure, here's a summary:" before the actual answer, sometimes it wraps things in extra formatting, sometimes the exact phrasing shifts slightly each time. A human reading it doesn't even notice this stuff. But code trying to automatically grab "just the summary part" out of that text is going to break constantly, because it's never formatted exactly the same way twice. The API call from earlier doesn't have this problem — you get a clean `"response"` field, every single time, in the exact same structure, which your code can rely on without guessing. That reliability is not a nice bonus. It's the actual requirement for anything you plan to automate.

## Chapter Summary

A chat window is genuinely great for testing whether a model fits your task — that's exactly what it was used for in Chapter 2. But it needs a human present for every single step, which makes it a demo tool, not something a pipeline can be built on. Underneath that chat window, Ollama runs a real API that you can call directly with `curl` or with plain code, and it hands back structured, predictable JSON instead of loose text meant for a person's eyes. Wrapping that call inside one small function — like `ask_model()` — gives you the actual foundation this whole book sits on: a way to ask your model anything, automatically, with no one typing, and get back an answer your code can reliably use.

## Bridge to Chapter 4

Right now, though, that `ask_model()` function only has one thing to work with — whatever question you type into the `prompt` argument yourself. And that's a problem, because a pipeline that only knows what you personally typed into it isn't grounded in anything real — it's just back to the exact hallucination risk Chapter 1 warned you about, except now it's automated instead of manual, which honestly makes it worse. Before this function is useful for anything real, it needs real material to work with — actual headlines, actual numbers, actual text pulled from actual sources on the internet, not just whatever you happened to type. Getting that real material safely and reliably onto your machine is the whole job of the next chapter.

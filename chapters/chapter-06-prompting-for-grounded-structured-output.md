<!--
© 2026 ashwinkrpi. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 6: Prompting for Grounded, Structured Output

## The Prompt That Had the Right Answer Sitting Right In Front of It — and Ignored It Anyway

Here's something that'll mess with your head a little. Take the cleaned, chunked RBI text from Chapter 5 — the actual, real, verified sentence saying the repo rate stayed at 6.5% — hand it to your model, and ask a simple question.

```bash
$ python3 talk_to_model.py

Context: "The Monetary Policy Committee decided to keep the policy 
repo rate unchanged at 6.5%, citing continued vigilance on 
inflation."

Question: What is the current repo rate, and what's the outlook 
for the next quarter?

Answer: The repo rate currently stands at 6.5%. Looking ahead, 
analysts expect the RBI may consider a rate cut in the next quarter 
if inflation continues to moderate, potentially bringing rates down 
to around 6.25% to support economic growth.
```

Read that again slowly. The first sentence is correct — it's literally sitting in the context you gave it. The second half — the "analysts expect," the "6.25%," the whole outlook paragraph — none of that was in your context. None of it was scraped, none of it was verified, none of it exists anywhere in what you fed the model. It just... kept going, smoothly sliding from "here's what the source says" into "here's what sounds like a reasonable continuation," without any change in tone to warn you the ground had shifted underneath.

This is the real trap of this chapter, and it's a sneakier one than Chapter 1's outright fabrication, because half the answer here is completely true. You gave the model good, grounded material, and it still wandered off — not because the material was bad, but because nothing about your prompt actually forced it to stay inside the fence you built. Having clean context sitting in front of the model, from Chapter 5, was necessary. It was never sufficient on its own.

## Why the Prompt's Real Job Is to Build a Fence, Not Ask a Question

Most people think of a prompt as a question — you ask something, the model answers. That's true, but it's incomplete for this pipeline. In a grounded system, the prompt has a second, more important job: it has to make it structurally awkward for the model to answer with anything that isn't traceable back to the context you handed it. Not "please only use the context" as a polite request — an actual instruction shape that makes wandering off feel wrong to the model's own pattern-completion instinct.

Let's prove the difference with three prompt attempts, same context, same question, escalating discipline.

**Attempt one — the polite request:**

```bash
$ python3 talk_to_model.py --prompt-file weak_prompt.txt

Prompt: "Using the context below, answer the question. Try to stick 
to the facts given.

Context: The Monetary Policy Committee decided to keep the policy 
repo rate unchanged at 6.5%.

Question: What's the repo rate outlook?"

Answer: The repo rate is currently 6.5%. The RBI is likely to 
maintain a cautious stance, and many economists anticipate rate 
cuts later this year as inflation trends improve.
```

Still wandering. "Try to stick to the facts" reads to the model like a mild suggestion, not a hard boundary, and pattern-completion habits are strong enough to override mild suggestions almost every time.

**Attempt two — forcing quotation, not paraphrase:**

```bash
$ python3 talk_to_model.py --prompt-file medium_prompt.txt

Prompt: "Answer ONLY using information directly stated in the 
context. If the answer is not in the context, respond with exactly: 
'Not stated in source.'

Context: The Monetary Policy Committee decided to keep the policy 
repo rate unchanged at 6.5%.

Question: What's the repo rate outlook?"

Answer: Not stated in source.
```

Now we're getting somewhere. That instruction — a specific, exact fallback phrase for anything the context doesn't cover — gave the model a legitimate, well-formed way to stop instead of wandering. It's no longer being asked to "try" to stay grounded. It's being given exactly two options: answer from the text, or say a fixed sentence. Nothing in between.

**Attempt three — the version this pipeline actually needs, which also demands the source line:**

```bash
$ python3 talk_to_model.py --prompt-file strong_prompt.txt

Prompt: "You are answering strictly from the SOURCE text below. 
Rules:
1. Only state facts that appear word-for-word or near word-for-word 
   in SOURCE.
2. For every fact you state, quote the exact phrase from SOURCE it 
   came from, in brackets.
3. If SOURCE does not contain the answer, respond with exactly: 
   'Not stated in source.'
4. Do not add outlook, predictions, or analysis not present in 
   SOURCE.

SOURCE: The Monetary Policy Committee decided to keep the policy 
repo rate unchanged at 6.5%, citing continued vigilance on 
inflation.

QUESTION: What's the repo rate outlook?"

Answer: The current repo rate is 6.5% [the policy repo rate 
unchanged at 6.5%]. Not stated in source regarding future outlook.
```

This is the shape this book's pipeline actually runs on. Notice what changed — the model isn't just answering, it's showing its work, pointing at the exact phrase from SOURCE that backs up each claim it makes. That bracketed quote isn't decoration. It's the exact thing Chapter 7's validator is going to grab and mechanically check against your cleaned, chunked text — did this phrase actually appear in the source, or didn't it? A prompt built like this doesn't just make hallucination less likely. It makes every claim independently checkable, which is a completely different and much stronger guarantee.

## The Objection: "Doesn't All This Rule-Writing Make the Output Sound Robotic and Stiff?"

Fair concern, and worth taking seriously, especially since this book's whole style — including this very chapter — leans casual and conversational. Doesn't forcing a model to quote-and-bracket everything kill any chance of natural-sounding writing?

Let's actually test it rather than assume:

```bash
$ python3 talk_to_model.py --prompt-file strong_prompt_v2.txt

Prompt: "...same grounding rules as before, but write the final 
answer in a natural, conversational tone, as if explaining to a 
friend. Keep the bracketed source quotes, but write everything 
around them casually.

SOURCE: The Monetary Policy Committee decided to keep the policy 
repo rate unchanged at 6.5%, citing continued vigilance on 
inflation.

QUESTION: What's happening with the repo rate?"

Answer: So the RBI basically decided not to touch the repo rate 
this time — it's staying right at 6.5% [the policy repo rate 
unchanged at 6.5%], mainly because they're still keeping a close 
eye on inflation [citing continued vigilance on inflation].
```

Same grounding rules, same bracketed quotes backing every claim — but the actual sentence reads completely naturally, not stiff at all. The rules about staying inside the source and the rules about tone are two separate, independent things, and they don't fight each other. You can absolutely be strict about *what* the model is allowed to claim, while being loose about *how* it phrases that claim. What was actually making attempt one and two feel a bit clunky wasn't the grounding discipline — it was that those early prompts hadn't been given any instruction about tone at all, so the model defaulted to a flat, textbook-summary voice. Add tone instructions on top of grounding instructions, and you get both: strictly accurate, and genuinely readable. This book's own Gen-Z, explain-to-a-friend voice, in fact, comes from stacking exactly this kind of tone instruction on top of grounding rules — the two were never in conflict to begin with.

## Chapter Summary

A prompt in this pipeline isn't just a question you're asking your model — it's a fence you're building around what the model is allowed to say. A polite request to "stick to the facts" doesn't hold up against the model's natural instinct to keep a plausible-sounding answer going. A hard rule — quote the exact source phrase for every claim, or say a fixed fallback sentence when the source doesn't cover it — actually holds, and it produces something extra valuable: every claim now comes bracketed with the exact source text it's based on, which is precisely what the next chapter's validator needs to do its job. And strict grounding rules don't force robotic writing — tone and accuracy are separate dials, and you can turn both up at once.

## Bridge to Chapter 7

Right now, though, you're trusting that bracketed quote. The model says `[the policy repo rate unchanged at 6.5%]` came straight from SOURCE, and in this example, it genuinely did. But nothing has actually *checked* that yet — you're still taking the model's word for it that its own citation is honest, which, if you think back to Chapter 1, is exactly the kind of blind trust this entire book was built to eliminate. A model that's been told to cite its sources can still get the citation itself wrong, or worse, invent a bracketed quote that sounds like it came from the source but doesn't, word for word. The only way to actually know is to stop trusting the model's claim about its own claim, and build something that checks it independently, automatically, every single time. That's the validator, and it's the next chapter.

# Chapter 7: Building the Citation Validator

## The Citation That Looked Real, Sounded Real, and Was Completely Fake

Go back to that bracketed quote from the end of Chapter 6 — `[the policy repo rate unchanged at 6.5%]` — sitting there next to the model's answer, looking exactly like proof. Now let's do something nobody actually does when a model cites itself: check it, word for word, against the real source.

```bash
$ python3 talk_to_model.py --prompt-file strong_prompt.txt --source pib_release.txt

SOURCE: "The Reserve Bank's Monetary Policy Committee voted 5-1 to 
hold the repo rate steady, with the majority citing food price 
pressures as the key concern going into the festive season."

QUESTION: What was the vote outcome and the main reason?

Answer: The MPC voted to hold the repo rate steady [the policy 
repo rate unchanged at 6.5%], citing continued vigilance on 
inflation as the main concern.
```

Read that bracket again. It says `[the policy repo rate unchanged at 6.5%]`. Now go check the actual SOURCE text one more time. That exact phrase — "the policy repo rate unchanged at 6.5%" — does not appear anywhere in it. Not close, not near, not a paraphrase. The real source says "voted 5-1 to hold the repo rate steady," a completely different sentence, about a completely different release, from earlier in this book. The model borrowed a bracketed quote that sounded plausible — maybe even one it generated correctly once, earlier, on different source text — and reused it here with total confidence, attached to a citation format that's specifically designed to look like proof.

This is the moment this whole book has been building toward, and it's worth sitting with: Chapter 6 gave the model rules to cite its sources. It never gave the model a reason to cite them *honestly*. A model told to bracket its quotes will bracket something — and if it can't find the exact right phrase, its same old pattern-completion instinct from Chapter 1 kicks right back in, generating a bracket that's shaped like a real citation instead of admitting it doesn't have one. A fake citation is, if anything, more dangerous than a plain hallucination, because it comes dressed up as evidence. This is exactly why the model can never be the one checking its own homework. Something else has to.

## Why the Validator, Not the Model, Is What Makes This Pipeline Trustworthy

Here's the core shift this chapter is asking you to make: stop treating the model's bracketed citation as proof, and start treating it as a claim — one single thing left to verify, using plain code, against the actual text you scraped and cleaned back in Chapters 4 and 5. This is deliberately dumb, mechanical work. Not another model. Not another prompt. A simple, boring, reliable check: does this exact bracketed phrase actually appear in the source text, yes or no?

```python
# validator.py
from difflib import SequenceMatcher

def validate_citation(quote, source_text, threshold=0.85):
    """Check if `quote` genuinely appears in `source_text`,
    allowing minor wording differences (punctuation, casing)."""
    quote_clean = quote.lower().strip()
    source_clean = source_text.lower()
    
    if quote_clean in source_clean:
        return True, 1.0  # exact match, no ambiguity
    
    # sliding window check for near-exact matches
    words = source_clean.split()
    window_size = len(quote_clean.split())
    best_score = 0
    for i in range(len(words) - window_size + 1):
        window = " ".join(words[i:i + window_size])
        score = SequenceMatcher(None, quote_clean, window).ratio()
        best_score = max(best_score, score)
    
    return best_score >= threshold, best_score
```

Now let's run both citations from this chapter through it — the real one, and the fake one — against their actual sources:

```python
# check_both.py
from validator import validate_citation

source_ch6 = ("The Monetary Policy Committee decided to keep the "
              "policy repo rate unchanged at 6.5%, citing continued "
              "vigilance on inflation.")
source_ch7 = ("The Reserve Bank's Monetary Policy Committee voted "
              "5-1 to hold the repo rate steady, with the majority "
              "citing food price pressures as the key concern going "
              "into the festive season.")

quote_real = "the policy repo rate unchanged at 6.5%"
quote_fake = "the policy repo rate unchanged at 6.5%"  # reused wrongly

print("Checking real citation against its real source:")
print(validate_citation(quote_real, source_ch6))

print("Checking the same citation against the wrong source:")
print(validate_citation(quote_fake, source_ch7))
```

```bash
$ python3 check_both.py

Checking real citation against its real source:
(True, 1.0)

Checking the same citation against the wrong source:
(False, 0.41)
```

There it is, in black and white. Same bracketed phrase, two different outcomes, because the validator isn't judging how confident or fluent the model sounded — it's mechanically checking whether those specific words genuinely exist in that specific source. `(True, 1.0)` means an exact match, no ambiguity. `(False, 0.41)` means the phrase and the source barely resemble each other at all — a citation that got reused where it didn't belong, caught cold, with no room for the model to talk its way out of it, because it isn't the model doing the judging anymore.

Now wire this into the actual pipeline logic — the part that decides what's allowed to survive:

```python
# validate_response.py
import re
from validator import validate_citation

def validate_response(answer, source_text):
    citations = re.findall(r"\[(.*?)\]", answer)
    if not citations:
        return {"status": "rejected", "reason": "no citations found"}
    
    results = []
    for quote in citations:
        valid, score = validate_citation(quote, source_text)
        results.append({"quote": quote, "valid": valid, "score": round(score, 2)})
    
    if all(r["valid"] for r in results):
        return {"status": "approved", "citations": results}
    else:
        return {"status": "rejected", "citations": results}
```

```bash
$ python3 -c "
from validate_response import validate_response
answer = 'The MPC voted to hold the repo rate steady [the policy repo rate unchanged at 6.5%].'
source = \"The Reserve Bank's Monetary Policy Committee voted 5-1 to hold the repo rate steady, with the majority citing food price pressures.\"
print(validate_response(answer, source))
"

{'status': 'rejected', 'citations': [{'quote': 'the policy repo 
rate unchanged at 6.5%', 'valid': False, 'score': 0.41}]}
```

`rejected`. Not flagged for a human to maybe glance at later — actually rejected, automatically, before it goes anywhere near your final artifact in Chapter 8. This is the whole point of this chapter, made concrete: the validator doesn't care how confident the sentence sounded, how well-formatted the bracket was, or how close the number "felt" to being right. It checks one narrow, boring, mechanical thing — does this exact text exist in this exact source — and it rejects anything that fails, no exceptions, no benefit of the doubt. That's the actual trust boundary of this entire pipeline. Everything before this chapter was about giving the model good material and good instructions. This chapter is about no longer needing to hope the model followed them.

## The Objection: "Isn't a Strict Word-Match Validator Going to Reject Perfectly Good Paraphrases?"

Real concern, and it's the first thing anyone building this raises — language is flexible, a model might genuinely and correctly paraphrase a source instead of quoting it exactly, and a strict validator might punish that as if it were a hallucination.

Let's test this directly:

```bash
$ python3 -c "
from validator import validate_citation
source = 'The committee decided to keep the repo rate unchanged at 6.5 percent.'
paraphrase = 'repo rate held steady at 6.5%'
print(validate_citation(paraphrase, source))
"

(False, 0.62)
```

At the default threshold, that genuinely reasonable paraphrase gets rejected — 0.62 falls below the 0.85 bar. This is a real trade-off, not something to wave away. But here's why this pipeline accepts it anyway: the entire design in Chapter 6 was built to sidestep this problem before it even reaches the validator — the prompt doesn't ask the model to paraphrase and then cite, it asks the model to quote the exact phrase it's relying on, word-for-word, inside the brackets specifically so the validator has something precise to check. The natural-sounding sentence around the bracket can paraphrase all it wants — remember the "explaining to a friend" version from Chapter 6, still fully natural, still fully grounded. It's only the bracketed portion that needs to be exact, because the bracketed portion's entire job is to be checkable, not readable.

If you do want the validator to allow looser matches — maybe you're validating a source that got summarized before scraping, or you're working with a model that struggles with exact quoting — you lower the threshold deliberately, as a conscious decision, not a silent default:

```bash
$ python3 -c "
from validator import validate_citation
source = 'The committee decided to keep the repo rate unchanged at 6.5 percent.'
paraphrase = 'repo rate held steady at 6.5%'
print(validate_citation(paraphrase, source, threshold=0.55))
"

(True, 0.62)
```

Now it passes — but notice, you had to consciously choose to loosen the net, with a specific number, that you can see and justify. That's a completely different thing from a validator that quietly accepts anything plausible-sounding by default. The strictness isn't a flaw to apologize for. It's the entire feature. A validator that lets things through easily isn't protecting you from anything — it's just Chapter 1's hallucination problem wearing a lab coat.

## Chapter Summary

A bracketed citation from your model looks like proof, but it's still just a claim — and Chapter 6 already showed that a model told to cite sources will sometimes cite something that sounds right instead of something that's actually there. The fix isn't a smarter prompt or a bigger model — it's a separate, mechanical validator that checks each citation, word for word, against your real cleaned source text, and rejects anything that doesn't genuinely match, no matter how fluent or confident it sounds. Strict word-matching does risk rejecting valid paraphrases, but this pipeline sidesteps that by forcing the model to quote exactly inside its brackets in the first place — and where looser matching is genuinely needed, you lower the threshold on purpose, not by accident.

## Bridge to Chapter 8

At this point, you've got something genuinely rare: a sentence you can actually trust, sitting in your terminal, having survived real scraping, real cleaning, real grounded prompting, and now real automated verification. But look at where it actually lives right now — a Python dictionary, a line of `approved` status in your terminal output, text with no shape, no visuals, nothing a human would want to stop scrolling for. Nobody's out there sharing a raw JSON object. The next problem this pipeline has to solve isn't about truth anymore — you've earned that part. It's about turning this verified, trustworthy sentence into something that actually looks like it belongs on a screen. That's the next chapter.

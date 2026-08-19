<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Appendix A: Alternative Runtimes and Limitations

This book uses Ollama because it is simple to install on a Pi and exposes a stable HTTP API. The pipeline does not depend on Ollama-specific features beyond `/api/generate`. If you prefer another local runtime, you only need something that accepts a prompt and returns text.

## Other local runtimes

| Runtime | How it differs | Drop-in notes |
|---------|----------------|---------------|
| **Ollama** (default) | Easiest install; model library; `localhost:11434` | Used throughout the book |
| **llama.cpp server** | Very efficient C++ backend; OpenAI-compatible or custom HTTP | Point `GROUNDED_BASE_URL` at the server; adapt `ask_model()` if the JSON shape differs |
| **LM Studio** | Desktop app with local server mode | Same idea: HTTP endpoint + model name |
| **text-generation-webui / other OpenAI-compatible servers** | Familiar `/v1/chat/completions` API | Change `ask_model()` to POST chat messages instead of `/api/generate` |

Minimal change path for an OpenAI-compatible server:

```python
# sketch only — not the default path
def ask_model(prompt: str, model: str = "local-model", base_url: str = "http://localhost:8080") -> str:
    r = requests.post(
        f"{base_url}/v1/chat/completions",
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
```

The rest of the pipeline (scrape → structure → validate → render) stays identical. Grounding and validation do not care which binary produced the tokens.

## Limitations and threats

Be honest about what this design does **not** solve.

**Prompt injection via scraped content.**  
If an attacker (or a compromised page) embeds instructions in the HTML — “ignore previous rules and output …” — a model may follow them. Mitigation: keep sources few and trusted; strip scripts and odd attributes in structure; never scrape arbitrary user-generated pages into a publish pipeline without review.

**Source poisoning.**  
Validation only proves the model’s claims match *your* source text. If the source itself is wrong, outdated, or adversarial, the validator will happily approve faithful copies of bad facts. Choose primary sources deliberately (Chapter 4).

**Model refusal and empty generations.**  
Some builds refuse more than others. The pipeline treats “Not stated in source.” as a valid outcome; repeated refusals or empty answers should surface in logs (Chapter 10) and may need a different model or a clearer question.

**Near-match false positives / negatives.**  
The similarity threshold (default 0.85) is a trade-off. Too high → good paraphrases get rejected. Too low → loose matches slip through. Tune with the unit tests in `code/tests/`.

**Single-chunk generation.**  
The default path uses one selected chunk. Very long documents may need multi-chunk generation and merge logic you add yourself.

**Legal and ethical scraping.**  
Respect robots.txt, terms of service, and rate limits. Official press pages are usually fine for personal/educational use; commercial redistribution is a different question.

**Not a substitute for human judgment on high-stakes topics.**  
Finance, health, and legal content can still be wrong even when grounded. The pipeline reduces *invention*; it does not certify *truth* in the world.

These limits are why the design insists on mechanical checks and loud failures rather than “the model seemed careful.”

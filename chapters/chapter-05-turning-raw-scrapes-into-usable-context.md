<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 5: Turning Raw Scrapes into Usable Context

## The Model That Summarized a Cookie Banner Instead of the News

Let's start with something that actually happened, and honestly, will probably happen to you too if you skip this chapter. Someone takes their nicely scraped RBI press release from Chapter 4, feeds the raw HTML straight into their model, and asks for a one-sentence summary. Here's what came back:

```bash
$ python3 talk_to_model.py --input raw_rbi_page.html

This page requires JavaScript to be enabled. Please accept cookies 
to continue viewing content. Skip to main content. Home | About Us 
| Press Releases | Contact. The website uses cookies to enhance 
your experience.
```

That's the "summary." Not because the model is bad, and not because the source was bad either — the RBI press release was sitting right there, real and trustworthy. The problem is what actually got fed to the model. Raw HTML from a real webpage isn't just the article text — it's navigation menus, cookie banners, footer links, ad script leftovers, and about fifteen other things stacked on top of the one paragraph you actually wanted. The model didn't hallucinate here. It did exactly what it was told — summarize whatever text was in front of it — and what was in front of it happened to be mostly cookie-banner nonsense, because nobody cleaned it first.

This is the step almost every beginner skips, because it feels boring compared to scraping or prompting. But skip it, and it doesn't matter how good your source was in Chapter 4, or how carefully you prompt in Chapter 6 — you're grounding your model in garbage either way.

## Why Cleaning and Chunking Decide Everything Downstream

Here's the core thing to understand: an LLM doesn't know what a "cookie banner" is versus what an "actual news paragraph" is. It just sees text — one long stream of it — and treats every sentence with equal seriousness. If "Please accept cookies to continue" sits right next to "RBI held the repo rate at 6.5%," the model has no built-in instinct telling it one of those matters and the other one doesn't. That instinct has to come from you, in code, before the text ever reaches the model.

Let's actually fix the mess from before. Here's what raw scraped HTML typically looks like, stripped down for the example:

```python
# what raw_rbi_page.html actually contains, roughly
raw_html = """
<nav>Home | About Us | Press Releases | Contact</nav>
<div class="cookie-banner">This site uses cookies. Accept all.</div>
<header><img src="logo.png"></header>
<article>
  <h1>RBI Monetary Policy Statement</h1>
  <p>The Monetary Policy Committee decided to keep the policy repo 
  rate unchanged at 6.5%, citing continued vigilance on inflation.</p>
  <p>This marks the eighth consecutive meeting where rates were held 
  steady, reflecting a cautious approach to economic growth.</p>
</article>
<footer>© 2026 Reserve Bank of India | Privacy Policy | Sitemap</footer>
<script>trackPageView();</script>
"""
```

Now let's write the cleaner — the code that separates the one paragraph you actually want from everything wrapped around it:

```python
# clean_text.py
from bs4 import BeautifulSoup

def clean_article(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # strip out the stuff that's never the actual content
    for tag in soup(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    for tag in soup.find_all(class_="cookie-banner"):
        tag.decompose()
    
    # pull text only from the actual article body
    article = soup.find("article")
    if not article:
        return ""
    
    paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
    return "\n".join(p for p in paragraphs if len(p) > 20)  # drop junk lines

if __name__ == "__main__":
    cleaned = clean_article(raw_html)
    print(cleaned)
```

```bash
$ python3 clean_text.py

The Monetary Policy Committee decided to keep the policy repo rate 
unchanged at 6.5%, citing continued vigilance on inflation.
This marks the eighth consecutive meeting where rates were held 
steady, reflecting a cautious approach to economic growth.
```

That's it. No nav bar, no cookie banner, no footer, no script tags. Two real sentences, both of them actually from the article. Feed this into your model instead of the raw page, and suddenly it has nothing left to accidentally summarize except the thing you actually wanted summarized.

But cleaning alone isn't the whole story, and here's the part that trips people up next. Real articles — especially official press releases — often run long. Ten paragraphs, fifteen paragraphs, sometimes more. If you dump all of that into one prompt as a single giant block, two things go wrong. First, small local models like the one you picked in Chapter 2 have a limited context window — feed them too much text at once and they either truncate it silently or start losing track of what's actually important. Second, and this matters even more for Chapter 7's validator later, if your model generates a claim and you're trying to check "does this match the source," you need to know *which specific piece* of the source it came from — not just "somewhere in this wall of text." That's what chunking solves.

```python
# chunk_text.py
def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # small overlap so context isn't cut mid-idea
    return chunks

if __name__ == "__main__":
    cleaned = clean_article(raw_html)
    chunks = chunk_text(cleaned, chunk_size=15, overlap=3)
    for i, c in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(c)
```

```bash
$ python3 chunk_text.py

--- Chunk 1 ---
The Monetary Policy Committee decided to keep the policy repo rate 
unchanged at 6.5%, citing continued vigilance on inflation. This 
marks the eighth consecutive
--- Chunk 2 ---
inflation. This marks the eighth consecutive meeting where rates 
were held steady, reflecting a cautious approach to economic growth.
```

Notice the small overlap between chunk 1 and chunk 2 — the phrase "This marks the eighth consecutive" appears at the tail of one chunk and the start of the next. That's deliberate, not a bug. Without that overlap, you risk slicing a sentence exactly in half between two chunks, so neither chunk fully contains the idea on its own. With it, every real idea in your source text is guaranteed to sit fully inside at least one chunk. Each of these chunks can now be handed to your model as a labeled, traceable piece of context — and just as importantly, each one can later be handed to your Chapter 7 validator as a specific, checkable unit, instead of one giant unsearchable wall of text.

## The Objection: "Can't I Just Use a Model With a Bigger Context Window and Skip All This?"

Reasonable thought — local models are getting context windows big enough to swallow entire articles whole these days, so why bother cleaning and chunking at all? Just paste the whole raw scrape in and let the model figure out what matters.

Let's actually test that logic:

```bash
$ python3 talk_to_model.py --input raw_rbi_page.html --model llama3.2:3b

Summary: The website discusses cookie policies and provides 
navigation options including Home, About Us, Press Releases, and 
Contact. It also mentions the Reserve Bank of India's monetary 
policy regarding interest rates, though specific figures were not 
clearly highlighted in the provided content.
```

Even with room to spare in the context window, the actual number — 6.5% — got buried and dropped, while the cookie banner and nav menu got equal billing in the summary. A bigger context window solves the problem of "can the model technically fit all this text in." It does absolutely nothing about the separate problem of "does the model know which parts of this text actually matter." Those are two different problems, and context window size only fixes the first one. The second one only gets fixed by you, deciding in code what counts as real content before the model ever sees it.

There's a second reason this matters even more for this book's pipeline specifically: bigger context windows generally mean bigger models, and bigger models mean the exact RAM problem from Chapter 2 all over again. You picked a small model on purpose, to fit your Pi. Cleaning and chunking isn't a workaround for a limitation — it's the actual correct approach regardless of model size, because even a massive frontier model with a huge context window still can't tell a cookie banner from a policy statement on its own. It just has more room to be confused in.

## Chapter Summary

Raw scraped HTML isn't usable context — it's a pile of navigation menus, cookie banners, and footers with your actual content buried somewhere inside, and a model treats all of it with equal seriousness unless you clean it first. Stripping out the non-content tags and pulling text only from the real article body turns that mess into something worth feeding to a model. Chunking that cleaned text into smaller, slightly overlapping pieces solves a second problem entirely — it keeps each idea intact, keeps your model from losing track inside long text, and gives Chapter 7's validator specific, traceable pieces to check claims against later. And a bigger context window doesn't replace any of this — it just gives the model more space to be confused in, if you skip the cleanup.

## Bridge to Chapter 6

You've now got something genuinely solid — clean, chunked, traceable pieces of real source text, sitting ready to use. But notice, this whole chapter has been about *preparing* the material. Nothing's actually been generated yet. The next step is the one where all of this either pays off or falls apart: writing a prompt that hands your model these chunks and forces it to answer strictly from them — not to wander off into what it already "knows" from training, and not to blend the real chunk with some half-remembered fact sitting in its weights. That's a much harder prompt to write than it sounds, and getting it wrong quietly undoes everything you just built in this chapter. That's exactly where we're headed next.

<!--
© 2026 Ashwin Koppam Raghavendra. Licensed under CC BY-NC-SA 4.0.
Full terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Code samples in this chapter are licensed separately under MIT — see /LICENSE.
-->

# Chapter 4: Gathering Real-World Source Material

## The Guy Who Scraped 4,000 Pages and Got Worse Results Than the Guy Who Scraped 5

There's a story that goes around in scraping communities, and honestly it's basically the same story every single time, just with different names. Someone builds a scraper, points it at a huge news aggregator site, tells it "grab everything," and lets it run overnight. By morning they've got 4,000 articles sitting in a folder — proper flex, right? Feels like progress. Meanwhile, someone else spends thirty minutes picking five actually solid sources for their exact topic, writes a scraper that only touches those five, and stops there.

Guess whose pipeline actually produces usable, accurate content? Not the guy with 4,000 files. His folder is full of duplicate stories, reposted press releases, comment sections that got scraped by mistake, some random cooking blog that got mixed in because it happened to mention the same keyword once, and articles from sources that are honestly just... not reliable. Somewhere in that mess there's probably good information. But "probably somewhere in this mess" is not grounding — that's just a bigger, messier version of the exact hallucination problem Chapter 1 already warned you about, except now instead of the model making things up, it's confidently repeating garbage that a bad source made up first.

This is the mistake this whole chapter exists to stop you from making. More scraped data is not more grounding. It's more noise, unless you're deliberate about where it's coming from.

## Why Fewer, Better Sources Beat Bulk Every Time

Let's get one thing straight before touching any code: the entire point of scraping, in this book's pipeline, is not to collect data. It's to collect *trustworthy* data that your model can point back to later, when Chapter 7's validator checks every claim against it. If a source is unreliable, outdated, or full of unrelated junk, scraping more of it doesn't fix that — it just gives your validator more garbage to accidentally validate against. So the actual skill in this chapter isn't scraping technique. It's picking targets, and being disciplined about touching only those targets.

Let's prove this with a real example. Say your pipeline covers Indian financial news. Here's a scraper that goes broad — hits a general aggregator, grabs whatever's on the page:

```python
# broad_scrape.py — the "grab everything" approach
import requests
from bs4 import BeautifulSoup

url = "https://news.example-aggregator.com/business"
page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(page.text, "html.parser")

headlines = soup.find_all("a", class_="headline")
print(f"Found {len(headlines)} headlines")
for h in headlines[:5]:
    print("-", h.get_text(strip=True))
```

```bash
$ python3 broad_scrape.py

Found 187 headlines
- Sensex rises 200 points in early trade
- 10 monsoon recipes to try this week
- RBI's Shaktikanta Das speaks on inflation
- Best budget phones under 20000
- Local cricket league results
```

187 headlines, and already, five lines in, you can see the problem — recipes and cricket scores sitting right next to actual monetary policy news, because the aggregator mixes categories loosely and your scraper grabbed everything with a `headline` class, no matter the topic. Multiply this by 187, and you've got a pile that needs heavy manual sorting before it's usable for anything.

Now here's the disciplined version — same tools, completely different targeting:

```python
# targeted_scrape.py — the "few, good sources" approach
import requests
from bs4 import BeautifulSoup

SOURCES = [
    "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
    "https://pib.gov.in/PressReleseDetail.aspx",  # official govt releases
]

for url in SOURCES:
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.text, "html.parser")
    title = soup.find("h1") or soup.find("title")
    print(f"Source: {url}")
    print(f"Title: {title.get_text(strip=True) if title else 'N/A'}")
    print("---")
```

```bash
$ python3 targeted_scrape.py

Source: https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx
Title: Reserve Bank of India - Press Releases
---
Source: https://pib.gov.in/PressReleseDetail.aspx
Title: Press Information Bureau - Government of India
---
```

Only two sources here, not 187. But look at what those two actually are — the RBI's own press release page, and the Press Information Bureau, which is the Indian government's own official release platform. Every single line that comes off these pages is, by definition, a primary source — nobody's paraphrase, nobody's hot take, nobody's clickbait rewrite. When your model later generates "the RBI kept the repo rate at 6.5%," it's pointing back at a sentence from the RBI's actual press release, not at some random aggregator's rewrite of a rewrite of that same press release. That's the difference between real grounding and fake grounding — and it has nothing to do with how much you scraped. It has everything to do with what you chose to scrape.

This is worth sitting with for a second, because it's genuinely counterintuitive if you're coming from a "more data is always better" mindset that a lot of AI content assumes. In this pipeline specifically, a scraper touching two verified, official sources beats a scraper touching two hundred random ones, every single time, because Chapter 7's validator can only be as good as the source material it's checking against. Feed it clean sources, it catches real hallucinations. Feed it messy, unreliable sources, and it'll happily "validate" a claim against a source that was itself wrong to begin with — which means your validator isn't protecting you anymore, it's just rubber-stamping bad information with extra confidence.

## The Objection: "Won't Scraping More Sites Give Me Better Coverage?"

This one's fair, and it's worth taking seriously rather than brushing off — surely covering more sites means you catch more stories, more angles, more of what's actually happening, right?

Let's actually test this claim instead of just arguing it. Say you widen your two-source list to twelve sites — a mix of official releases, news sites, and a couple of aggregator blogs, because "more coverage."

```bash
$ python3 wide_scrape.py --sources 12

Scraped 12 sources in 34.2s
Total headlines collected: 340
Duplicate/near-duplicate headlines removed: 211
Headlines with no clear source attribution: 58
Usable, unique, attributable headlines: 71
```

Out of 340 headlines pulled from twelve sites, only 71 actually survive basic cleanup — the rest are duplicates of the same three or four real stories, reworded slightly by different outlets, or headlines with no clear original source you could point your validator at later. You didn't get twelve times the coverage. You got roughly the same handful of real stories, buried under a mountain of repetition, plus a chunk of stuff you can't even trace back reliably. Meanwhile your two-source RBI-and-PIB scraper from earlier gave you a smaller number of headlines, but every single one of them was clean, attributable, and usable immediately, with zero de-duplication work needed.

The honest answer is: coverage isn't about the number of sites, it's about the *type* of sites. Two official, primary sources will usually give you cleaner, more usable material than twelve mixed general-purpose ones, because the twelve are mostly reporting on the same two or three primary events anyway — just with more noise wrapped around them. If you genuinely need broader coverage later, the right move isn't "scrape more sites blindly." It's "add one more carefully chosen, high-quality source to your list," the same disciplined way you picked the first two. Quality compounds. Volume just piles up.

## Chapter Summary

Scraping for this pipeline isn't a data-collection exercise — it's a trust exercise. Grabbing everything a broad aggregator offers looks like progress but actually hands you duplicates, unrelated junk, and unreliable rewrites that undermine your validator before it even starts working. A small, deliberately chosen list of primary, official, or clearly trustworthy sources gives you less volume but far higher usability, because every line you scrape is something your model can honestly point back to later. And scraping more sites doesn't automatically mean better coverage — it usually just means more repetition of the same handful of real stories, wrapped in noise you then have to clean up by hand.

## Bridge to Chapter 5

Even with two clean, trustworthy sources like the RBI and PIB pages, though, you might've noticed something in that last script's output — you got a page title, sure, but real press releases are full pages of raw HTML, sitting behind headers, footers, navigation menus, ad scripts, and formatting tags that mean absolutely nothing to your model. Right now, what you're pulling off these pages isn't something you can hand to your `ask_model()` function from Chapter 3 and expect a clean answer from — it's a mess of markup with a real sentence hiding somewhere inside it. Before any of this scraped material is actually usable as grounding, it needs to go through a serious cleanup — stripped down, cut into sensible pieces, and turned into something your model can actually read as context instead of choking on. That's the exact job of the next chapter.

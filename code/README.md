# Grounded pipeline — final code

This directory contains the five single-responsibility modules plus the orchestrator described in Chapters 9–11.

## Quick start

```bash
# from the repo root
cd code
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# make sure Ollama is running and a model is pulled (e.g. llama3.2:3b)
python3 run_pipeline.py
```

## Command-line flags

```bash
python3 run_pipeline.py \
  --url "https://example.com/article" \
  --source "Example Source" \
  --question "What is the key fact?" \
  --model llama3.2:3b \
  --output my_card.png \
  --dry-run          # skip rendering
  --no-cache         # force a fresh scrape
  -v                 # debug logging
```

## Environment variables

| Variable            | Purpose                          | Default                          |
|---------------------|----------------------------------|----------------------------------|
| `GROUNDED_URL`      | Source page to scrape            | RBI press-release index          |
| `GROUNDED_SOURCE`   | Name shown on the rendered card  | Reserve Bank of India            |
| `GROUNDED_QUESTION` | Question asked of the model      | Key decision / announcement      |
| `GROUNDED_MODEL`    | Ollama model name                | `llama3.2:3b`                    |
| `GROUNDED_BASE_URL` | Ollama API base URL              | `http://localhost:11434`         |

## Stage behaviour (production notes)

- **Scrape** returns the *article HTML* (not the full page), retries transient network errors, and caches successful responses for 6 hours (disable with `--no-cache`).
- **Structure** selects the most relevant chunk when a question is supplied instead of always using `chunks[0]`.
- **Validate** treats the exact fallback `"Not stated in source."` as an approved, non-hallucinated outcome.
- **Render** dynamically sizes and vertically centres text so longer answers do not overflow the card.
- **Orchestrator** emits timestamped log lines and exits non-zero on failure (convenient for cron).

## Logs

Redirect stdout/stderr when running under cron:

```bash
0 7 * * * /path/to/venv/bin/python /path/to/code/run_pipeline.py >> /path/to/code/logs/run.log 2>&1
```

Then inspect the latest run with:

```bash
python3 check_last_run.py
```

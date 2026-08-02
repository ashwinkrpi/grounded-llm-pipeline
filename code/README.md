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
# generate.py
"""Stage 3: Build a grounded prompt and call the local model."""

import requests


def ask_model(
    prompt: str,
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
) -> str:
    """
    Send a prompt to the Ollama /api/generate endpoint.
    Returns the model's response text.
    """
    response = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"]


def build_prompt(source_chunk: str, question: str | None = None) -> str:
    """
    Assemble the strict grounding prompt from Chapter 6.

    The model must quote exact source phrases in brackets or reply
    with the fixed fallback sentence.
    """
    if question is None:
        question = "Summarize the key fact in this source."

    return f"""You are answering strictly from the SOURCE text below. Rules:
1. Only state facts that appear word-for-word or near word-for-word in SOURCE.
2. For every fact you state, quote the exact phrase from SOURCE it came from, in brackets.
3. If SOURCE does not contain the answer, respond with exactly: 'Not stated in source.'
4. Do not add outlook, predictions, or analysis not present in SOURCE.
5. Write the answer in a natural, clear tone, but keep the bracketed quotes.

SOURCE: {source_chunk}

QUESTION: {question}"""
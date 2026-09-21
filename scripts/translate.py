#!/usr/bin/env python3
"""
AI Daily News - headline translator
Adds "title_en" and "title_vi" to every item in data/categorized_news.json,
translating each headline into the other language with the Claude API.

Needs ANTHROPIC_API_KEY. Without it (or on any API error) the original
titles are kept for both languages, so the daily report still publishes.
"""

import json
import os
import sys

import anthropic

MODEL = "claude-opus-5"

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "categorized_news.json")

SYSTEM_PROMPT = (
    "You translate news headlines for a bilingual English/Vietnamese AI news digest. "
    "Translate each headline into the requested target language as a natural, concise "
    "headline a native reader would expect from a news site. Keep names of people, "
    "companies, products and AI models (e.g. OpenAI, Claude, Gemini, GPT-6) unchanged. "
    "Return exactly one translation for every id you receive."
)

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "translations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["id", "text"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["translations"],
    "additionalProperties": False,
}


def translate(items):
    """Return {id: translated title} for items shaped {"id", "text", "target"}."""
    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(items, ensure_ascii=False)}],
        output_config={
            "effort": "low",  # short, simple task
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
        # On a safety decline, re-run on Anthropic's recommended fallback model
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("translation request was declined")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("translation output was truncated")

    text = next(b.text for b in response.content if b.type == "text")
    return {t["id"]: t["text"].strip() for t in json.loads(text)["translations"] if t["text"].strip()}


def main():
    print("=" * 50)
    print("🤖 AI Daily News - translate headlines")
    print("=" * 50)
    print()

    if not os.path.exists(DATA_FILE):
        print("✗ News data not found, run fetch_news.py first")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        categories = json.load(f)

    news = [item for items in categories.values() for item in items]

    # Start with the original title in both languages
    for item in news:
        item["title_en"] = item["title"]
        item["title_vi"] = item["title"]

    requests_ = [
        {"id": i, "text": item["title"], "target": "Vietnamese" if item.get("lang", "en") == "en" else "English"}
        for i, item in enumerate(news)
    ]

    if not requests_:
        print("Nothing to translate")
    elif not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️ ANTHROPIC_API_KEY is not set; keeping original titles")
    else:
        try:
            translated = translate(requests_)
            for i, item in enumerate(news):
                if i in translated:
                    key = "title_vi" if item.get("lang", "en") == "en" else "title_en"
                    item[key] = translated[i]
            print(f"✓ Translated {len(translated)}/{len(requests_)} headlines")
        except (anthropic.APIError, RuntimeError, ValueError, KeyError, StopIteration) as exc:
            print(f"⚠️ Translation failed, keeping original titles: {exc}")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved: {DATA_FILE}")


if __name__ == "__main__":
    main()

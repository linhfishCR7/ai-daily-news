#!/usr/bin/env python3
"""
AI Daily News - headline translator
Adds "title_en" and "title_vi" to every item in data/categorized_news.json,
translating each headline into the other language with the DeepSeek API.

Needs DEEPSEEK_API_KEY. Without it (or on any API error) the original
titles are kept for both languages, so the daily report still publishes.
"""

import json
import os
import sys

import requests

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
MAX_ATTEMPTS = 2  # DeepSeek JSON mode may occasionally return empty content

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "categorized_news.json")

# JSON mode requires the word "json" and an example of the output format in the prompt
SYSTEM_PROMPT = """You translate news headlines for a bilingual English/Vietnamese AI news digest.
Translate each headline into its "target" language as a natural, concise headline a native
reader would expect from a news site. Keep names of people, companies, products and AI models
(e.g. OpenAI, Claude, Gemini, GPT-6) unchanged. Return exactly one translation for every id.

Input: a json array of {"id": number, "text": string, "target": "English" | "Vietnamese"}.
Output: a json object in exactly this format:
{"translations": [{"id": 0, "text": "translated headline"}, {"id": 1, "text": "translated headline"}]}"""


def translate(items, api_key):
    """Return {id: translated title} for items shaped {"id", "text", "target"}."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 8000,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        choice = response.json()["choices"][0]
        if choice.get("finish_reason") == "length":
            raise RuntimeError("translation output was truncated")

        content = (choice["message"].get("content") or "").strip()
        if content:
            translations = json.loads(content)["translations"]
            return {
                t["id"]: t["text"].strip()
                for t in translations
                if isinstance(t.get("id"), int) and isinstance(t.get("text"), str) and t["text"].strip()
            }
        print(f"⚠️ Empty response (attempt {attempt}/{MAX_ATTEMPTS})")

    raise RuntimeError("empty response from the API")


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
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not requests_:
        print("Nothing to translate")
    elif not api_key:
        print("⚠️ DEEPSEEK_API_KEY is not set; keeping original titles")
    else:
        try:
            translated = translate(requests_, api_key)
            for i, item in enumerate(news):
                if i in translated:
                    key = "title_vi" if item.get("lang", "en") == "en" else "title_en"
                    item[key] = translated[i]
            print(f"✓ Translated {len(translated)}/{len(requests_)} headlines with {MODEL}")
        except (requests.RequestException, RuntimeError, ValueError, KeyError, IndexError, TypeError) as exc:
            print(f"⚠️ Translation failed, keeping original titles: {exc}")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved: {DATA_FILE}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
AI Daily News - news fetcher
Collects AI/tech news from English and Vietnamese RSS feeds, filters and
categorizes them, and writes data/categorized_news.json for generate.py.
"""

import html
import json
import os
import re
import socket
import sys
import time
from datetime import datetime, timedelta

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# Network timeout for each feed request (seconds)
socket.setdefaulttimeout(20)

USER_AGENT = "Mozilla/5.0 (compatible; ai-daily-news/1.0; +https://linhfishCR7.github.io/ai-daily-news/)"

# Only keep items published within this window
MAX_AGE_HOURS = 48

# Max entries read from each feed
MAX_ENTRIES_PER_FEED = 30

# Max items kept per category (the page shows 1 main + 2 sub headlines)
MAX_ITEMS_PER_CATEGORY = 5
HEADLINE_LIMIT = 3
OTHER_LIMIT = 8

# Titles matching these are promotions, not news
EXCLUDE_KEYWORDS = ["TechCrunch Disrupt", "Disrupt ticket", "save up to", "Prices go up"]

# Relevance filters for general tech feeds.
# All-uppercase keywords (e.g. "AI") are matched case-sensitively so they do
# not hit words like "said" (English) or "ai" / "hai" (Vietnamese).
AI_KEYWORDS_EN = [
    "AI", "artificial intelligence", "machine learning", "LLM", "LLMs", "GPT",
    "ChatGPT", "OpenAI", "Anthropic", "Claude", "Gemini", "DeepMind", "chatbot",
    "neural network", "generative",
]
AI_KEYWORDS_VI = [
    "AI", "trí tuệ nhân tạo", "học máy", "mô hình ngôn ngữ", "chatbot",
    "ChatGPT", "OpenAI", "Gemini", "Claude", "GPT",
]

# Feed configuration. An empty keyword list means every entry is AI-related.
NEWS_SOURCES = {
    # English sources
    "techcrunch_ai": {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "keywords": [],
    },
    "the_verge_ai": {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "keywords": [],
    },
    "venturebeat_ai": {
        "name": "VentureBeat",
        "url": "https://venturebeat.com/category/ai/feed/",
        "keywords": [],
    },
    "openai_news": {
        "name": "OpenAI",
        "url": "https://openai.com/news/rss.xml",
        "keywords": [],
    },
    "deepmind_blog": {
        "name": "Google DeepMind",
        "url": "https://deepmind.google/blog/rss.xml",
        "keywords": [],
    },
    "google_ai_blog": {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "keywords": [],
    },
    "hackernews": {
        "name": "Hacker News",
        "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT&points=20",
        "keywords": AI_KEYWORDS_EN,
        "can_headline": False,  # community posts, not reported news
    },
    # Vietnamese sources (general tech feeds, filtered to AI topics)
    "vnexpress": {
        "name": "VnExpress",
        "url": "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
        "keywords": AI_KEYWORDS_VI,
    },
    "tuoitre": {
        "name": "Tuổi Trẻ",
        "url": "https://tuoitre.vn/rss/nhip-song-so.rss",
        "keywords": AI_KEYWORDS_VI,
    },
    "dantri": {
        "name": "Dân trí",
        "url": "https://dantri.com.vn/rss/cong-nghe.rss",
        "keywords": AI_KEYWORDS_VI,
    },
    "genk": {
        "name": "GenK",
        "url": "https://genk.vn/rss/home.rss",
        "keywords": AI_KEYWORDS_VI,
    },
}

# Category keywords (English + Vietnamese), checked in this order;
# an item goes to the first category that matches.
CATEGORY_KEYWORDS = {
    "headline": [
        "GPT", "ChatGPT", "Claude", "Gemini", "OpenAI", "Anthropic", "DeepMind",
        "Llama", "Grok", "Mistral", "DeepSeek", "Qwen", "Copilot", "LLM",
        "mô hình ngôn ngữ lớn",
    ],
    "product": [
        "launch", "launches", "launched", "release", "releases", "released",
        "unveil", "unveils", "unveiled", "introduce", "introduces", "introducing",
        "rolls out", "debut", "debuts", "new feature", "update", "app", "adds",
        "AI-powered", "ra mắt", "phát hành", "công bố", "giới thiệu", "cập nhật",
        "tính năng",
    ],
    "funding": [
        "raise", "raises", "raised", "funding", "Series A", "Series B",
        "Series C", "valuation", "valued", "IPO", "acquire", "acquires",
        "acquired", "acquisition", "invest", "invests", "investment", "investors",
        "backed by", "balance sheet", "billion",
        "gọi vốn", "đầu tư", "định giá", "thâu tóm", "mua lại", "rót vốn",
    ],
    "research": [
        "research", "researchers", "paper", "study", "benchmark", "breakthrough",
        "state-of-the-art", "SOTA", "model", "dataset",
        "nghiên cứu", "đột phá", "nhà khoa học", "công trình",
    ],
    "industry": [
        "partner", "partners", "partnership", "deal", "regulation", "law", "policy",
        "enterprise", "adopt", "adoption", "lawsuit", "sues", "antitrust", "jobs",
        "workforce", "government", "Trump", "Nvidia",
        "hợp tác", "doanh nghiệp", "ứng dụng", "quy định", "chính sách", "luật",
        "việc làm", "kiện", "chính phủ", "thị trường",
    ],
}

CATEGORY_ORDER = ["headline", "product", "funding", "research", "industry", "other"]


def compile_keywords(keywords):
    """Build one regex matching any keyword on word boundaries."""
    if not keywords:
        return None
    sensitive = [re.escape(k) for k in keywords if k.isupper()]
    insensitive = [re.escape(k) for k in keywords if not k.isupper()]
    parts = []
    if sensitive:
        parts.append("(?:" + "|".join(sensitive) + ")")
    if insensitive:
        parts.append("(?i:" + "|".join(insensitive) + ")")
    return re.compile(r"(?<!\w)(?:" + "|".join(parts) + r")(?!\w)")


CATEGORY_PATTERNS = {cat: compile_keywords(kws) for cat, kws in CATEGORY_KEYWORDS.items()}
EXCLUDE_PATTERN = compile_keywords(EXCLUDE_KEYWORDS)


def clean_text(raw):
    """Strip HTML tags, decode entities and collapse whitespace."""
    if not raw:
        return ""
    text = BeautifulSoup(html.unescape(raw), "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", text).strip()


def parse_date(entry):
    """Return the entry's publish time as a local-time datetime, or None."""
    raw = entry.get("published") or entry.get("updated") or ""
    if not raw:
        return None
    try:
        parsed = date_parser.parse(raw)
    except (ValueError, OverflowError):
        return None
    # Naive times (e.g. Tuổi Trẻ) are treated as local time
    return parsed.astimezone()


def fetch_rss(source_key, config, cutoff):
    """Fetch one RSS/Atom feed and return the matching items."""
    items = []
    pattern = compile_keywords(config.get("keywords", []))
    try:
        feed = feedparser.parse(config["url"], agent=USER_AGENT)
        if feed.get("bozo") and not feed.entries:
            raise RuntimeError(feed.get("bozo_exception") or "invalid feed")

        for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
            title = clean_text(entry.get("title", ""))
            link = entry.get("link", "")
            if not title or not link:
                continue
            if pattern and not pattern.search(title):
                continue
            if EXCLUDE_PATTERN.search(title):
                continue

            published = parse_date(entry)
            if published is None:
                published = datetime.now().astimezone()
            if published < cutoff:
                continue

            items.append({
                "title": title,
                "link": link,
                "source": config["name"],
                "pub_date": published.strftime("%Y-%m-%d %H:%M"),
                "summary": clean_text(entry.get("summary", ""))[:200],
                "can_headline": config.get("can_headline", True),
            })

        print(f"✓ {source_key}: {len(items)} items")
    except Exception as exc:
        print(f"✗ {source_key}: fetch failed - {exc}")

    return items


def normalize_title(title):
    """Normalize a title for duplicate detection."""
    return re.sub(r"\W+", " ", title.lower()).strip()


def dedupe(items):
    """Drop items sharing a link or a normalized title."""
    seen_links, seen_titles, result = set(), set(), []
    for item in items:
        link_key = item["link"].split("?")[0].rstrip("/")
        title_key = normalize_title(item["title"])
        if link_key in seen_links or title_key in seen_titles:
            continue
        seen_links.add(link_key)
        seen_titles.add(title_key)
        result.append(item)
    return result


def fetch_all_news():
    """Fetch every configured source, newest first, without duplicates."""
    cutoff = datetime.now().astimezone() - timedelta(hours=MAX_AGE_HOURS)
    all_news = []
    for source_key, config in NEWS_SOURCES.items():
        all_news.extend(fetch_rss(source_key, config, cutoff))
        time.sleep(1)  # be polite to the feed servers

    all_news.sort(key=lambda x: x["pub_date"], reverse=True)
    return dedupe(all_news)


def categorize_news(news_items):
    """Assign each item to the first matching category that still has room.

    Items overflow to the next matching category (and finally to "other"),
    so a busy headline day does not silently drop news.
    """
    categories = {cat: [] for cat in CATEGORY_ORDER}

    limits = {"headline": HEADLINE_LIMIT, "other": OTHER_LIMIT}

    def has_room(cat):
        return len(categories[cat]) < limits.get(cat, MAX_ITEMS_PER_CATEGORY)

    for item in news_items:
        allow_headline = item.pop("can_headline", True)
        for cat in CATEGORY_ORDER[:-1]:
            if cat == "headline" and not allow_headline:
                continue
            if has_room(cat) and CATEGORY_PATTERNS[cat].search(item["title"]):
                categories[cat].append(item)
                break
        else:
            if has_room("other"):
                categories["other"].append(item)

    return categories


def save_news(news_items, categories):
    """Write raw and categorized news to data/."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    raw_file = os.path.join(data_dir, f"raw_news_{datetime.now().strftime('%Y%m%d')}.json")
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(news_items, f, ensure_ascii=False, indent=2)

    cat_file = os.path.join(data_dir, "categorized_news.json")
    with open(cat_file, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

    print("\n✓ News data saved")
    print(f"  - raw: {raw_file}")
    print(f"  - categorized: {cat_file}")


def main():
    print("=" * 50)
    print("🤖 AI Daily News - fetch")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print()

    all_news = fetch_all_news()
    print(f"\nTotal after filtering and dedupe: {len(all_news)} items")

    # Never publish placeholder content: fail so the workflow keeps the previous report
    if not all_news:
        print("\n✗ No news fetched from any source; aborting.")
        sys.exit(1)

    categories = categorize_news(all_news)

    print("\nPer category:")
    for cat, items in categories.items():
        if items:
            print(f"  - {cat}: {len(items)}")

    save_news(all_news, categories)
    return categories


if __name__ == "__main__":
    main()

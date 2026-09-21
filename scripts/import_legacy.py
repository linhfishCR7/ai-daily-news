#!/usr/bin/env python3
"""
AI Daily News - import legacy issues
Re-publishes issues from the original Chinese site in the bilingual layout:
parses each page, translates every headline to English and Vietnamese,
renders it with the current template into archive/YYYYMMDD.html and
rebuilds the archive manifest.

Usage:
  python import_legacy.py URL [URL ...]
  e.g. python import_legacy.py https://xiangjianan.github.io/ai-daily-news/archive/20260920.html

Needs DEEPSEEK_API_KEY for translation (see translate.py).
"""

import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import generate
from translate import translate_items

# Section titles on the legacy pages -> category keys
LEGACY_SECTIONS = {
    "产品发布": "product",
    "融资动态": "funding",
    "研究突破": "research",
    "行业动态": "industry",
}

# Legacy source keys -> display names
SOURCE_NAMES = {
    "techcrunch_ai": "TechCrunch",
    "openai_blog": "OpenAI",
    "deepmind_blog": "Google DeepMind",
    "hackernews": "Hacker News",
    "qbitai": "QbitAI",
    "jiqizhixin": "Jiqizhixin",
    "infoq": "InfoQ",
}

CJK = re.compile(r"[一-鿿]")


def parse_item(title_node, meta_text, date):
    """Build a news item from a title link and its "source | HH:MM" meta text."""
    a = title_node if title_node.name == "a" else title_node.select_one("a")
    title = a.get_text(strip=True)
    parts = [p.strip() for p in meta_text.split("|")]
    source_key = parts[0] if parts else ""
    time = parts[-1] if len(parts) > 1 and re.fullmatch(r"\d{2}:\d{2}", parts[-1]) else "00:00"
    return {
        "title": title,
        "link": a.get("href", ""),
        "source": SOURCE_NAMES.get(source_key, source_key),
        "pub_date": f"{date.strftime('%Y-%m-%d')} {time}",
        "lang": "zh" if CJK.search(title) else "en",
    }


def parse_legacy(html):
    """Return (report datetime, issue number, categories) from a legacy page."""
    soup = BeautifulSoup(html, "html.parser")

    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", soup.title.get_text())
    if not m:
        raise ValueError("report date not found in <title>")
    date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # Publication time from the footer ("08:55 出版")
    footer = soup.select_one(".footer .time")
    t = re.search(r"(\d{2}):(\d{2})", footer.get_text()) if footer else None
    if t:
        date = date.replace(hour=int(t.group(1)), minute=int(t.group(2)))

    left = soup.select_one(".header-left")
    issue = int(re.search(r"\d+", left.get_text()).group()) if left else None

    categories = {"headline": [], "product": [], "funding": [], "research": [], "industry": [], "other": []}

    main = soup.select_one(".main-headline")
    if main:
        meta = main.select_one(".headline-meta")
        spans = [s.get_text(strip=True) for s in meta.select("span")] if meta else []
        categories["headline"].append(parse_item(main.select_one(".headline-title a"), " | ".join(spans), date))
    for sub in soup.select(".sub-headline-item"):
        categories["headline"].append(
            parse_item(sub.select_one(".news-title a"), sub.select_one(".news-meta").get_text(strip=True), date))

    for section in soup.select("section.section"):
        heading = section.select_one(".section-title").get_text(strip=True)
        key = next((v for k, v in LEGACY_SECTIONS.items() if heading.startswith(k)), "other")
        for it in section.select(".news-item"):
            categories[key].append(
                parse_item(it.select_one(".news-title a"), it.select_one(".news-meta").get_text(strip=True), date))

    return date, issue, categories


def import_url(url):
    print(f"\n→ {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    date, issue, categories = parse_legacy(response.text)
    print(f"  Issue {issue} · {date:%Y-%m-%d %H:%M} · {sum(len(v) for v in categories.values())} items")

    translate_items([item for items in categories.values() for item in items])

    html = generate.to_archive_paths(generate.generate_html(categories, now=date, issue_num=issue))
    os.makedirs(generate.ARCHIVE_DIR, exist_ok=True)
    out = os.path.join(generate.ARCHIVE_DIR, f"{date:%Y%m%d}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ Saved: {out}")


def main():
    urls = sys.argv[1:]
    if not urls:
        print(__doc__)
        sys.exit(1)
    for url in urls:
        import_url(url)
    generate.generate_manifest()


if __name__ == "__main__":
    main()

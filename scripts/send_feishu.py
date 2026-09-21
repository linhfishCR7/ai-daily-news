#!/usr/bin/env python3
"""
AI Daily News - Feishu (Lark) notifier

Optional and currently NOT part of the daily workflow. To enable it, set the
FEISHU_WEBHOOK secret and add a step running this script (see SETUP.md).
"""

import json
import os
from datetime import datetime

import requests

SITE_URL = os.environ.get("SITE_URL", "https://linhfishCR7.github.io/ai-daily-news/")

CATEGORY_EMOJI = {
    "headline": "📌",
    "product": "🚀",
    "funding": "💰",
    "research": "🔬",
    "industry": "📊",
}

CATEGORY_NAME = {
    "headline": "Tin nổi bật / Headlines",
    "product": "Sản phẩm mới / Products",
    "funding": "Gọi vốn & M&A / Funding",
    "research": "Nghiên cứu / Research",
    "industry": "Thị trường & Chính sách / Industry",
}


def get_feishu_webhook():
    """Return the Feishu webhook URL, or None when not configured."""
    webhook = os.environ.get("FEISHU_WEBHOOK")
    if not webhook:
        print("⚠️ FEISHU_WEBHOOK is not set, skipping Feishu push")
        return None
    return webhook


def format_news_message(categories):
    """Build the Feishu interactive card."""
    now = datetime.now()

    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**🤖 AI Daily News**\n📅 {now.strftime('%d/%m/%Y')}\nBản tin AI hôm nay đã được cập nhật.",
            },
        }
    ]

    for cat, items in categories.items():
        if items and cat in CATEGORY_EMOJI:
            news_text = ""
            for item in items[:3]:  # at most 3 items per category
                title = item["title"]
                if len(title) > 80:
                    title = title[:80] + "..."
                news_text += f"• {title}\n"

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{CATEGORY_EMOJI[cat]} {CATEGORY_NAME[cat]}**\n{news_text}",
                },
            })

    elements.extend([
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "Xem bản tin đầy đủ"},
                    "url": SITE_URL,
                    "type": "primary",
                }
            ],
        },
        {
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": f"Generated at {now.strftime('%H:%M')}"}
            ],
        },
    ])

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "AI Daily News"},
                "template": "blue",
            },
            "elements": elements,
        },
    }


def send_to_feishu(webhook, message):
    """POST the message to the Feishu webhook."""
    try:
        response = requests.post(webhook, json=message, timeout=10)
        if response.status_code != 200:
            print(f"✗ Feishu push failed: HTTP {response.status_code}")
            return False

        result = response.json()
        # Current API returns {"code": 0}; older responses used {"StatusCode": 0}
        if result.get("code", result.get("StatusCode")) == 0:
            print("✓ Feishu push succeeded")
            return True
        print(f"✗ Feishu push failed: {result}")
    except Exception as exc:
        print(f"✗ Feishu push error: {exc}")

    return False


def main():
    print("=" * 50)
    print("🤖 AI Daily News - Feishu push")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print()

    webhook = get_feishu_webhook()
    if not webhook:
        return

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cat_file = os.path.join(project_dir, "data", "categorized_news.json")
    if not os.path.exists(cat_file):
        print("✗ News data not found")
        return

    with open(cat_file, "r", encoding="utf-8") as f:
        categories = json.load(f)

    send_to_feishu(webhook, format_news_message(categories))


if __name__ == "__main__":
    main()

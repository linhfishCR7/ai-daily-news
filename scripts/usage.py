#!/usr/bin/env python3
"""
AI Daily News - DeepSeek usage and cost tracking

Every translation run appends one record to data/usage.json with the tokens
the API reported and the cost computed from DeepSeek's price list. Running this
file prints a per-day report; in GitHub Actions the report is also written to
the job summary.

Prices: https://api-docs.deepseek.com/quick_start/pricing (USD per 1M tokens).
Peak hours are 01:00-04:00 and 06:00-10:00 UTC, Monday-Friday; Chinese public
holidays (billed off-peak) are not modelled, so costs on those days are overstated.
"""

import json
import os
from collections import OrderedDict
from datetime import datetime, timezone

USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "usage.json")

# (off-peak, peak) USD per 1M tokens
PRICES = {
    "deepseek-v4-pro": {"cache_hit": (0.022, 0.044), "cache_miss": (0.66, 1.32), "output": (1.98, 3.96)},
    "deepseek-flash": {"cache_hit": (0.003, 0.006), "cache_miss": (0.15, 0.3), "output": (0.6, 1.2)},
}
PEAK_HOURS_UTC = [(1, 4), (6, 10)]


def is_peak(when_utc):
    """True when `when_utc` falls in DeepSeek's weekday peak hours."""
    if when_utc.weekday() >= 5:
        return False
    return any(start <= when_utc.hour < end for start, end in PEAK_HOURS_UTC)


def summarize(responses_usage):
    """Sum the `usage` objects of several API responses."""
    total = {"requests": 0, "cache_hit_tokens": 0, "cache_miss_tokens": 0,
             "output_tokens": 0, "reasoning_tokens": 0}
    for u in responses_usage:
        prompt = u.get("prompt_tokens", 0)
        hit = u.get("prompt_cache_hit_tokens", 0)
        total["requests"] += 1
        total["cache_hit_tokens"] += hit
        total["cache_miss_tokens"] += u.get("prompt_cache_miss_tokens", prompt - hit)
        total["output_tokens"] += u.get("completion_tokens", 0)
        total["reasoning_tokens"] += (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
    return total


def cost_usd(tokens, model, peak):
    """Cost of summarized tokens; None for a model without a known price."""
    prices = PRICES.get(model)
    if prices is None:
        return None
    i = 1 if peak else 0
    return (tokens["cache_hit_tokens"] * prices["cache_hit"][i]
            + tokens["cache_miss_tokens"] * prices["cache_miss"][i]
            + tokens["output_tokens"] * prices["output"][i]) / 1_000_000


def load():
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def record(run, model, responses_usage):
    """Append one run's usage to data/usage.json and print it."""
    if not responses_usage:
        return None
    now_utc = datetime.now(timezone.utc)
    peak = is_peak(now_utc)
    tokens = summarize(responses_usage)
    cost = cost_usd(tokens, model, peak)
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),  # local date (workflow TZ)
        "time_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run": run,
        "model": model,
        "peak": peak,
        **tokens,
        "cost_usd": round(cost, 8) if cost is not None else None,
    }

    records = load()
    records.append(entry)
    os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    total_in = tokens["cache_hit_tokens"] + tokens["cache_miss_tokens"]
    price_note = f"${cost:.6f}" if cost is not None else "unknown price"
    print(f"💰 {run}: {total_in} input + {tokens['output_tokens']} output tokens "
          f"({tokens['requests']} request(s), {'peak' if peak else 'off-peak'}) = {price_note}")
    return entry


def daily_report(days=14):
    """Markdown table of tokens and cost per day (most recent first)."""
    per_day = OrderedDict()
    for r in sorted(load(), key=lambda r: r["time_utc"]):
        d = per_day.setdefault(r["date"], {"runs": 0, "input": 0, "output": 0, "cost": 0.0})
        d["runs"] += 1
        d["input"] += r["cache_hit_tokens"] + r["cache_miss_tokens"]
        d["output"] += r["output_tokens"]
        d["cost"] += r["cost_usd"] or 0.0

    if not per_day:
        return "No DeepSeek usage recorded yet."

    rows = list(per_day.items())[::-1][:days]
    lines = [
        "| Date | Runs | Input tokens | Output tokens | Cost (USD) |",
        "|---|---:|---:|---:|---:|",
    ]
    for date, d in rows:
        lines.append(f"| {date} | {d['runs']} | {d['input']:,} | {d['output']:,} | ${d['cost']:.4f} |")

    total_cost = sum(d["cost"] for d in per_day.values())
    avg = total_cost / len(per_day)
    lines.append("")
    lines.append(f"**Total:** ${total_cost:.4f} over {len(per_day)} day(s) · "
                 f"**average** ${avg:.4f}/day ≈ **${avg * 30:.2f}/month**")
    return "\n".join(lines)


def write_job_summary():
    """Add the daily report to the GitHub Actions job summary, if running there."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("## DeepSeek usage\n\n" + daily_report() + "\n")


if __name__ == "__main__":
    print(daily_report())
    write_job_summary()

**English** | [Tiếng Việt](README.vi.md)

<p align="center">
  <img src="https://img.shields.io/badge/🤖_100%25_AI_Developed-7C3AED?style=for-the-badge" alt="100% AI Developed" />
  <img src="https://img.shields.io/badge/✨_100%25_AI_Generated-00D4AA?style=for-the-badge" alt="100% AI Generated" />
</p>

# AI Daily News 🤖

An automated daily AI news digest, published as a static site on GitHub Pages.
The page is bilingual (Vietnamese / English) and collects news from English and Vietnamese sources.

**Live site:** https://linhfishCR7.github.io/ai-daily-news/

## Features

- Fetches AI news from English and Vietnamese RSS feeds
- Filters to AI topics, keeps only the last 48 hours, removes duplicates
- Sorts news into Headlines, Products, Funding, Research, Industry and More
- Renders a newspaper-style HTML report (screenshot-friendly on phones)
- Keeps every past issue in `archive/`, with an archive browser (heatmap calendar, timeline, search)
- Installable PWA with offline support
- Runs automatically every day at **07:00 Vietnam time** (00:00 UTC) via GitHub Actions

## How it works

```
GitHub Actions (daily cron)
  └─ scripts/fetch_news.py  → data/categorized_news.json
  └─ scripts/generate.py    → archive previous index.html → archive/YYYYMMDD.html
                            → render new index.html
                            → rebuild data/archive_manifest.json
  └─ git commit & push      → GitHub Pages serves the site
```

If no source returns any news, `fetch_news.py` exits with an error and the workflow stops,
so yesterday's report stays online instead of publishing placeholder content.

## Project structure

```
ai-daily-news/
├── index.html                 # Today's report (homepage, generated)
├── archive/                   # Past reports, one file per day (generated)
├── data/
│   ├── categorized_news.json  # Today's categorized news (generated)
│   └── archive_manifest.json  # Index of all issues for the archive UI (generated)
├── assets/style.css           # Styles
├── icons/                     # App icons (scripts/make_icons.py)
├── manifest.webmanifest       # PWA manifest
├── sw.js                      # Service worker
├── scripts/
│   ├── fetch_news.py          # Fetch, filter, dedupe and categorize news
│   ├── generate.py            # Render HTML, archive, build manifest
│   ├── send_feishu.py         # Optional Feishu push (disabled, see SETUP.md)
│   ├── serve.py               # LAN preview server
│   ├── make_icons.py          # Icon generator
│   └── run.sh                 # Run the pipeline locally
└── .github/workflows/daily.yml
```

## News sources

| English | Vietnamese (filtered to AI topics) |
|---|---|
| TechCrunch (AI) | VnExpress (Khoa học - Công nghệ) |
| The Verge (AI) | Tuổi Trẻ (Nhịp sống số) |
| VentureBeat (AI, via Google News) | Dân trí (Công nghệ) |
| OpenAI News | GenK |
| Google DeepMind Blog | |
| Google AI Blog | |
| Hacker News (AI/LLM/GPT, 20+ points) | |

Sources are configured in `NEWS_SOURCES` in [scripts/fetch_news.py](scripts/fetch_news.py).

## Run locally

```bash
pip install -r scripts/requirements.txt
cd scripts
python fetch_news.py
python generate.py
python serve.py        # open http://localhost:8000/
```

## Deploy your own copy

1. Fork this repository
2. Enable GitHub Actions and GitHub Pages (deploy from the `main` branch, root folder)
3. Update the site URL in this README and `SITE_URL` in `scripts/send_feishu.py`
4. The workflow runs daily; you can also start it from **Actions → Run workflow**

## License

MIT

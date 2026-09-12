**English** | [简体中文](README.zh-CN.md)

<p align="center">
  <img src="https://img.shields.io/badge/🤖_100%25_AI_Developed-7C3AED?style=for-the-badge" alt="100% AI Developed" />
  <img src="https://img.shields.io/badge/✨_全程AI生成-00D4AA?style=for-the-badge" alt="全程AI生成" />
</p>

> **💡 This repository is 100% developed independently by AI — from requirements analysis and code writing to testing and debugging, all AI-driven with zero human-written code.**

# AI Daily News 🤖

An automated daily AI tech news aggregation system

## Features

- ✅ Automatically fetches multiple AI news sources
- ✅ Generates a beautiful HTML daily report (perfect for screenshots on TikTok/Douyin)
- ✅ Deploys to GitHub Pages
- ✅ Auto-updates every night at 9 PM
- ✅ Pushes to Feishu

## Access URL

https://[your-GitHub-username].github.io/ai-daily-news

## Project Structure

```
ai-daily-news/
├── index.html          # Today's report (homepage)
├── archive/            # Past daily reports
│   ├── 20260307.html
│   └── ...
├── assets/             # Static assets
│   ├── style.css
│   └── images/
├── scripts/            # Scripts
│   ├── fetch_news.py   # News fetching
│   └── generate.py     # HTML generation
├── .github/
│   └── workflows/
│       └── daily.yml   # Scheduled job
└── README.md
```

## News Sources

- 36氪 / 36Kr (36kr.com)
- 机器之心 / Synced (jiqizhixin.com)
- 量子位 / QbitAI (qbitai.com)
- InfoQ (infoq.cn)
- TechCrunch
- AI News
- VentureBeat
- The Verge

## Usage

1. Fork this repository
2. Enable GitHub Actions
3. Configure a Feishu bot (optional)
4. Auto-updates every night at 9 PM

## License

MIT

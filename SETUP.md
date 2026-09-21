# Optional: Feishu (Lark) notifications

Feishu push is **disabled** — `scripts/send_feishu.py` is not called by the daily workflow.
Follow these steps only if you want to enable it later.

## 1. Create a Feishu group bot

1. Open the Feishu group chat
2. Group settings → Bots → Add bot → Custom bot
3. Copy the webhook URL (`https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx`)

## 2. Add the GitHub secret

1. Repository → Settings → Secrets and variables → Actions
2. New repository secret: name `FEISHU_WEBHOOK`, value = the webhook URL

## 3. Add the workflow step

In `.github/workflows/daily.yml`, add this step after "Generate HTML":

```yaml
    - name: Send to Feishu
      run: |
        cd scripts
        python send_feishu.py
      env:
        FEISHU_WEBHOOK: ${{ secrets.FEISHU_WEBHOOK }}
```

## Notes

- The card's "view full report" button links to `SITE_URL`
  (default `https://linhfishCR7.github.io/ai-daily-news/`, can be overridden with an environment variable).
- If the bot has signature verification enabled, signing must be added to the script.

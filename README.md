# WPFeed Weekly Digest System

Builds the weekly "WordPress Round-up" email for WPFeed: pulls the best recent
content from WPFeed itself plus selected external WordPress sources, and renders
a ready-to-send HTML email with a plain-text fallback.

## How it works

1. **Sources** are configured in `feeds.json`: WPFeed (priority 1, always first),
   WordPress.org News, WPBeginner, and WP Tavern.
2. **Freshness filter**: only items from the last 7 days are eligible. If that
   yields fewer than 5 items, the window widens automatically (up to 30 days)
   so the round-up never goes out nearly empty.
3. **Dedupe**: titles are normalized and compared, so the same story carried by
   two sources appears once. A per-source cap (4) stops one source dominating.
4. **Rendering**: `digest.py` writes `digest.html` (600px, inline CSS, table
   layout for email-client compatibility) and `digest.txt`.

## Usage

```bash
python digest.py                  # standard weekly run
python digest.py --days 14        # wider window
python digest.py --max 10         # more items
```

Python 3 standard library only. No API keys, no secrets.

## Important finding (Oct 2026 test)

WPFeed's own RSS feed is stale: its newest item is dated Aug 2023, so WPFeed
contributes 0 items right now and the round-up currently runs on external
sources. The system is ready; WPFeed content will flow in automatically as
soon as the site publishes again. See RUNBOOK.md for operations notes.

# Runbook: WPFeed Weekly Digest

## Weekly run

1. `cd wpfeed-digest && python digest.py`
2. Check the console output: one line per source shows how many fresh items it
   contributed. If a source shows "unavailable", the run still completes with
   the remaining sources.
3. Open `digest.html` in a browser to proof the email. Skim `digest.txt` too.
4. Send `digest.html` through the mail platform of choice (paste as the email
   body/template), with `digest.txt` as the plain-text part.

## Scheduling

- Linux/macOS cron, Mondays 09:00: `0 9 * * 1 cd /path/wpfeed-digest && python3 digest.py`
- Or a scheduled task / CI workflow on the same cadence. Generation takes
  under 30 seconds.

## Configuration (feeds.json)

- `sources`: name, RSS URL, priority (lower = earlier and ranked first).
- `window_days`: default freshness window (7).
- `min_items` / `max_window_days`: if fresh items fall below `min_items`, the
  window doubles up to `max_window_days` so the email never goes out empty.
- `max_items`: digest length cap (8). `per_source_cap`: per-source cap (4).

## Troubleshooting

- **WPFeed contributes 0 items**: its RSS feed is stale (newest item Aug 2023
  at the Oct 2026 check). This is a publishing problem on wpfeed.com, not a
  digest bug. Once WPFeed publishes again, its stories are picked up first
  automatically because it has priority 1.
- **A source is down**: the log line says "unavailable"; the digest is built
  from the rest. If it persists for 2+ weeks, check the feed URL in feeds.json.
- **Digest looks podcast-heavy**: WP Tavern publishes podcasts frequently.
  Lower its `per_source_cap` to 2 if you want more article balance.
- **Duplicate story from two sources**: dedupe matches on normalized titles;
  if two outlets title the same story very differently, both can appear.
  Remove one by hand during the proof step if it matters.

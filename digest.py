#!/usr/bin/env python3
"""WPFeed Weekly WordPress Round-up digest builder.

Pulls recent posts from WPFeed and selected external WordPress sources
(RSS), filters to the last N days, dedupes, ranks WPFeed first, and renders
a ready-to-send HTML email plus a plain-text version.

Usage:
    python digest.py                 # writes digest.html + digest.txt
    python digest.py --days 14 --max 10
"""
import argparse
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = {"User-Agent": "WPFeedDigest/1.0 (+https://wpfeed.com)"}


def fetch_feed(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_rss(xml_bytes):
    items = []
    root = ET.fromstring(xml_bytes)
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        date_raw = item.findtext("pubDate") or ""
        desc = (item.findtext("description") or "")
        desc = re.sub(r"<[^>]+>", "", desc)
        desc = html.unescape(desc).strip()
        try:
            dt = parsedate_to_datetime(date_raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            dt = None
        if title and link:
            items.append({"title": html.unescape(title), "link": link,
                          "date": dt, "summary": desc[:220]})
    return items


def norm_title(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def collect(config, now, window_days=None):
    window = timedelta(days=window_days or config["window_days"])
    picked, seen = [], set()
    stats = {}
    sources = sorted(config["sources"], key=lambda s: s["priority"])
    for src in sources:
        try:
            items = parse_rss(fetch_feed(src["url"]))
        except Exception as e:
            stats[src["name"]] = f"unavailable ({type(e).__name__})"
            continue
        fresh = [i for i in items if i["date"] and (now - i["date"]) <= window]
        fresh.sort(key=lambda i: i["date"], reverse=True)
        stats[src["name"]] = f"{len(fresh)} fresh of {len(items)} in feed"
        added = 0
        for i in fresh:
            if added >= config["per_source_cap"]:
                break
            key = norm_title(i["title"])
            if key in seen:
                continue
            seen.add(key)
            i["source"] = src["name"]
            picked.append(i)
            added += 1
    picked.sort(key=lambda i: (i["source"] != "WPFeed", -i["date"].timestamp()))
    return picked[: config["max_items"]], stats


def render_html(items, week_label):
    rows = []
    for i in items:
        d = i["date"].strftime("%d %b %Y")
        rows.append(f"""
        <tr><td style="padding:14px 0;border-bottom:1px solid #e5e7eb;">
          <div style="font-size:12px;color:#6b7280;">{html.escape(i['source'])} &middot; {d}</div>
          <a href="{html.escape(i['link'])}" style="font-size:17px;font-weight:600;color:#1d4ed8;text-decoration:none;">{html.escape(i['title'])}</a>
          <div style="font-size:14px;color:#374151;margin-top:4px;">{html.escape(i['summary'])}</div>
        </td></tr>""")
    return f"""<!DOCTYPE html>
<html><body style="margin:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;padding:28px;">
  <tr><td>
    <div style="font-size:24px;font-weight:700;color:#111827;">WordPress Round-up</div>
    <div style="font-size:14px;color:#6b7280;margin:4px 0 18px;">The best of WPFeed and the WordPress world, {week_label}.</div>
  </td></tr>
  {''.join(rows)}
  <tr><td style="padding-top:18px;font-size:12px;color:#9ca3af;">
    You are receiving the WPFeed weekly round-up. Reply to this email to give feedback, or unsubscribe anytime.
  </td></tr>
</table>
</td></tr></table>
</body></html>"""


def render_text(items, week_label):
    lines = [f"WordPress Round-up ({week_label})", "=" * 48, ""]
    for n, i in enumerate(items, 1):
        lines.append(f"{n}. {i['title']}")
        lines.append(f"   {i['source']} - {i['date'].strftime('%d %b %Y')}")
        lines.append(f"   {i['link']}")
        lines.append("")
    lines.append("WPFeed weekly round-up. Unsubscribe anytime.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="feeds.json")
    ap.add_argument("--days", type=int)
    ap.add_argument("--max", type=int, dest="max_items")
    args = ap.parse_args()
    with open(args.config) as f:
        config = json.load(f)
    if args.days:
        config["window_days"] = args.days
    if args.max_items:
        config["max_items"] = args.max_items
    now = datetime.now(timezone.utc)
    items, stats = collect(config, now)
    widened = config["window_days"]
    while len(items) < config.get("min_items", 1) and widened < config.get("max_window_days", 30):
        widened = min(widened * 2, config.get("max_window_days", 30))
        items, stats = collect(config, now, window_days=widened)
    if widened != config["window_days"]:
        print(f"[window] widened to {widened} days to reach the minimum item count")
    for name, s in stats.items():
        print(f"[source] {name}: {s}")
    if not items:
        print("No fresh items in the window; digest not written.", file=sys.stderr)
        sys.exit(2)
    week = f"week of {now.strftime('%d %b %Y')}"
    with open("digest.html", "w") as f:
        f.write(render_html(items, week))
    with open("digest.txt", "w") as f:
        f.write(render_text(items, week))
    print(f"Wrote digest.html and digest.txt with {len(items)} items.")


if __name__ == "__main__":
    main()

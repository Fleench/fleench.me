"""Plugin: build rss.xml from built Page objects."""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def _to_rfc2822(date_str: str) -> str:
    if not date_str.strip():
        return format_datetime(datetime.now(timezone.utc))
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return format_datetime(dt)
        except Exception:
            continue
    return format_datetime(datetime.now(timezone.utc))


def main(_src_dir: Path, out_dir: Path, config: dict[str, Any], all_pages: list[Any]) -> None:
    if not all_pages:
        return

    site_url = str(config.get("site_url", "https://flench.me")).rstrip("/")
    feed_items: list[tuple[str, str, str, str, str]] = []

    for page in all_pages:
        if str(page.parsed.metadata.get("draft", "")).strip().lower() in {"1", "true", "yes"}:
            continue
        title = html.escape(page.derive_title())
        link = f"{site_url}{page.rel_url}"
        guid = link
        body_text = _strip_tags(page.rendered_html)
        description = html.escape(body_text[:280])
        pub_date = _to_rfc2822(str(page.parsed.metadata.get("date", "")).strip())
        feed_items.append((title, link, guid, description, pub_date))

    if not feed_items:
        return

    # keep newest first by pubdate string parsed indirectly via sort key from date metadata if available
    feed_items.sort(key=lambda item: item[4], reverse=True)

    rss_lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        f"    <title>{html.escape(str(config.get('site_title', 'Site Feed')))}</title>",
        f"    <link>{html.escape(site_url + '/')}</link>",
        "    <description>Latest updates from across the site</description>",
    ]

    for title, link, guid, description, pub_date in feed_items:
        rss_lines.extend(
            [
                "    <item>",
                f"      <title>{title}</title>",
                f"      <link>{html.escape(link)}</link>",
                f"      <guid>{html.escape(guid)}</guid>",
                f"      <description>{description}</description>",
                f"      <pubDate>{html.escape(pub_date)}</pubDate>",
                "    </item>",
            ]
        )

    rss_lines.extend(["  </channel>", "</rss>"])
    (out_dir / "rss.xml").write_text("\n".join(rss_lines) + "\n", encoding="utf-8")

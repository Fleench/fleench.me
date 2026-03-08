"""Plugin: build rss.xml from built Page objects."""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


class _EContentParser(HTMLParser):
    """Collect text from nodes marked with class `e-content`."""

    def __init__(self) -> None:
        super().__init__()
        self._depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = ""
        for key, value in attrs:
            if key == "class" and value:
                classes = value
                break
        class_names = {name.strip() for name in classes.split() if name.strip()}
        if "e-content" in class_names:
            self._depth += 1
            return
        if self._depth > 0:
            self._depth += 1

    def handle_endtag(self, _tag: str) -> None:
        if self._depth > 0:
            self._depth -= 1

    def handle_data(self, data: str) -> None:
        if self._depth > 0:
            self._chunks.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self._chunks).split())


def _content_text(rendered_html: str) -> str:
    parser = _EContentParser()
    parser.feed(rendered_html)
    parsed = parser.text().strip()
    if parsed:
        return parsed
    return " ".join(_strip_tags(rendered_html).split())


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
        body_text = _content_text(page.rendered_html)
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

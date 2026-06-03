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


def _parse_datetime(date_str: str) -> datetime:
    if not date_str.strip():
        return datetime.now(timezone.utc)
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return datetime.now(timezone.utc)


def _to_rfc2822(value: datetime) -> str:
    return format_datetime(value)


def _normalize_feed_paths(config: dict[str, Any]) -> list[str]:
    raw_paths = config.get("rss_paths", ["notes", "blogs"])
    if not isinstance(raw_paths, list):
        return ["notes", "blogs"]

    normalized: list[str] = []
    for entry in raw_paths:
        if not isinstance(entry, str):
            continue
        path = entry.strip().strip("/")
        if path and path not in normalized:
            normalized.append(path)
    return normalized or ["notes", "blogs"]


def _build_feed_xml(
    *,
    title: str,
    link: str,
    description: str,
    feed_items: list[tuple[str, str, str, str, datetime]],
) -> str:
    rss_lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        f"    <title>{html.escape(title)}</title>",
        f"    <link>{html.escape(link)}</link>",
        f"    <description>{html.escape(description)}</description>",
    ]

    for item_title, item_link, guid, item_description, item_pub_date in feed_items:
        rss_lines.extend(
            [
                "    <item>",
                f"      <title>{item_title}</title>",
                f"      <link>{html.escape(item_link)}</link>",
                f"      <guid>{html.escape(guid)}</guid>",
                f"      <description>{item_description}</description>",
                f"      <pubDate>{html.escape(_to_rfc2822(item_pub_date))}</pubDate>",
                "    </item>",
            ]
        )

    rss_lines.extend(["  </channel>", "</rss>"])
    return "\n".join(rss_lines) + "\n"


def main(src_dir: Path, out_dir: Path, config: dict[str, Any], all_pages: list[Any]) -> None:
    site_url = str(config.get("site_url", "https://flench.me")).rstrip("/")
    feed_paths = _normalize_feed_paths(config)
    feed_groups: dict[str, list[tuple[str, str, str, str, datetime]]] = {path: [] for path in feed_paths}
    combined_items: list[tuple[str, str, str, str, datetime]] = []

    for page in all_pages:
        if str(page.parsed.metadata.get("draft", "")).strip().lower() in {"1", "true", "yes"}:
            continue
        title = html.escape(page.derive_title())
        link = f"{site_url}{page.rel_url}"
        guid = link
        body_text = _content_text(page.rendered_html)
        description = html.escape(body_text[:280])
        pub_date = _parse_datetime(str(page.parsed.metadata.get("date", "")).strip())
        item = (title, link, guid, description, pub_date)

        rel_url = str(page.rel_url)
        for feed_path in feed_paths:
            prefix = f"/{feed_path}/"
            if rel_url.startswith(prefix) or rel_url == f"/{feed_path}":
                feed_groups[feed_path].append(item)
                combined_items.append(item)
                break

    if not combined_items:
        return

    for feed_path, items in feed_groups.items():
        if not items:
            continue
        items.sort(key=lambda item: item[4], reverse=True)
        feed_title = f"{str(config.get('site_title', 'Site Feed'))} - {feed_path}"
        feed_description = f"Latest updates for /{feed_path}"
        feed_link = f"{site_url}/{feed_path}/"
        output_file = out_dir / feed_path / "rss.xml"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            _build_feed_xml(
                title=feed_title,
                link=feed_link,
                description=feed_description,
                feed_items=items,
            ),
            encoding="utf-8",
        )

    combined_items.sort(key=lambda item: item[4], reverse=True)
    (out_dir / "rss.xml").write_text(
        _build_feed_xml(
            title=str(config.get("site_title", "Site Feed")),
            link=site_url + "/",
            description="Latest updates from across the site",
            feed_items=combined_items,
        ),
        encoding="utf-8",
    )

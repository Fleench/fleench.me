from __future__ import annotations

import datetime as dt
import html
import json
import re
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

try:
    import markdown as md_lib  # type: ignore
except Exception:
    md_lib = None

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


WEBMENTION_STATE_PATH = Path.cwd() / ".." / ".webmention-state.json"


class _LinkHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        for key in ("href", "src"):
            value = attrs_dict.get(key)
            if value:
                self.links.add(value.strip())


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    marker = "\n---\n"
    end = raw.find(marker, 4)
    if end == -1:
        return {}, raw
    header = raw[4:end]
    body = raw[end + len(marker) :]

    if yaml is not None:
        data = yaml.safe_load(header) or {}
        if isinstance(data, dict):
            return data, body

    metadata: dict[str, Any] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body


def _markdown(text: str) -> str:
    if md_lib is not None:
        return md_lib.markdown(text, extensions=["extra", "sane_lists"])
    return "\n".join(f"<p>{html.escape(line)}</p>" for line in text.splitlines() if line.strip())


def _to_rfc2822(date_text: str) -> str:
    candidates = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]
    for pattern in candidates:
        try:
            parsed = dt.datetime.strptime(date_text.strip(), pattern)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return format_datetime(parsed)
        except Exception:
            continue
    return format_datetime(dt.datetime.now(dt.timezone.utc))


def _notes_page(items: list[str]) -> str:
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="UTF-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "  <title>Notes</title>",
            '  <link rel="stylesheet" href="/style.css">',
            '  <link rel="alternate" type="application/rss+xml" title="Site RSS" href="/rss.xml">',
            '  <script src="/layout.js" defer></script>',
            '  <script src="/mentions.js" defer></script>',
            "</head>",
            "<body>",
            '  <div class="page-wrap">',
            '    <div class="site-layout">',
            '      <div class="center-column">',
            '        <div class="content-shell">',
            '          <nav class="top-nav panel" aria-label="Primary navigation">',
            '            <a href="/">Home</a>',
            '            <a href="/notes/">Notes</a>',
            "          </nav>",
            '          <main class="layout">',
            '            <section class="content panel notes-index">',
            "              <h1>Notes</h1>",
            '              <p><a href="/rss.xml">Subscribe via RSS</a></p>',
            '              <div class="notes-list">',
            *[f"                {item}" for item in items],
            "              </div>",
            "            </section>",
            '            <section class="main-extras">',
            '              <div id="webmentions"></div>',
            "            </section>",
            "          </main>",
            "        </div>",
            "      </div>",
            "    </div>",
            "  </div>",
            "</body>",
            "</html>",
        ]
    )


def _notes_rss(site_url: str, entries: list[dict[str, str]]) -> str:
    items: list[str] = []
    for entry in entries:
        body = xml_escape(entry["body"])
        title = xml_escape(entry["title"])
        link = f"{site_url.rstrip('/')}{entry['permalink']}"
        items.append(
            "\n".join(
                [
                    "    <item>",
                    f"      <title>{title}</title>",
                    f"      <link>{xml_escape(link)}</link>",
                    f"      <guid>{xml_escape(link)}</guid>",
                    f"      <pubDate>{entry['pub_date']}</pubDate>",
                    f"      <description>{body}</description>",
                    "    </item>",
                ]
            )
        )

    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0">',
            "  <channel>",
            "    <title>Notes</title>",
            f"    <link>{xml_escape(site_url.rstrip('/') + '/notes/')}</link>",
            "    <description>Latest notes</description>",
            *items,
            "  </channel>",
            "</rss>",
        ]
    )


def _markdown_source_url(src_dir: Path, md_file: Path, site_url: str) -> str:
    relative = md_file.relative_to(src_dir)
    if relative.as_posix() == "index.md":
        return f"{site_url.rstrip('/')}/"
    return f"{site_url.rstrip('/')}/{relative.with_suffix('').as_posix()}/"


def _html_source_url(out_dir: Path, html_file: Path, site_url: str) -> str:
    relative = html_file.relative_to(out_dir).as_posix()
    if relative == "index.html":
        return f"{site_url.rstrip('/')}/"
    if relative.endswith("/index.html"):
        return f"{site_url.rstrip('/')}/{relative[:-len('index.html')]}"
    return f"{site_url.rstrip('/')}/{relative}"


def _extract_links_from_markdown(markdown_text: str) -> set[str]:
    links = set(re.findall(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", markdown_text))
    links.update(re.findall(r"<((?:https?://)[^>]+)>", markdown_text))
    return {link.strip() for link in links if link.strip()}


def _extract_links_from_html(html_text: str) -> set[str]:
    parser = _LinkHTMLParser()
    parser.feed(html_text)
    return parser.links


def _is_http_external(link: str, site_host: str) -> bool:
    parsed = urlparse(link)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return parsed.netloc != site_host


def _load_webmention_state() -> dict[str, Any]:
    if not WEBMENTION_STATE_PATH.exists():
        return {"version": 1, "queue": [], "published": []}
    try:
        data = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "queue": [], "published": []}
    if not isinstance(data, dict):
        return {"version": 1, "queue": [], "published": []}
    data.setdefault("version", 1)
    data.setdefault("queue", [])
    data.setdefault("published", [])
    return data


def _queue_discovered_links(src_dir: Path, out_dir: Path, site_url: str) -> int:
    site_host = urlparse(site_url).netloc
    if not site_host:
        return 0

    discovered: set[tuple[str, str]] = set()

    for md_file in sorted(src_dir.rglob("*.md")):
        _, body = _parse_frontmatter(md_file.read_text(encoding="utf-8"))
        source = _markdown_source_url(src_dir, md_file, site_url)
        for link in _extract_links_from_markdown(body):
            if _is_http_external(link, site_host):
                discovered.add((source, link))

    for html_file in sorted(out_dir.rglob("*.html")):
        source = _html_source_url(out_dir, html_file, site_url)
        html_text = html_file.read_text(encoding="utf-8")
        for link in _extract_links_from_html(html_text):
            if _is_http_external(link, site_host):
                discovered.add((source, link))

    state = _load_webmention_state()
    queue = state.get("queue", [])
    published = state.get("published", [])

    existing = {
        (item.get("source", ""), item.get("target", ""))
        for item in [*queue, *published]
        if isinstance(item, dict)
    }

    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    added = 0
    for source, target in sorted(discovered):
        if (source, target) in existing:
            continue
        queue.append({"source": source, "target": target, "queued_at": now})
        existing.add((source, target))
        added += 1

    state["queue"] = queue
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if added:
        print(f"Queued {added} webmention(s) in {WEBMENTION_STATE_PATH.name}")
    return added


def main(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
    notes_dir = src_dir / "notes"
    notes = sorted(notes_dir.rglob("*.md"), reverse=True) if notes_dir.exists() else []
    rendered: list[str] = []
    feed_entries: list[dict[str, str]] = []
    for note_file in notes:
        metadata, body = _parse_frontmatter(note_file.read_text(encoding="utf-8"))
        relative = note_file.relative_to(src_dir).with_suffix("").as_posix()
        permalink = f"/{relative}/"
        note_type = html.escape(str(metadata.get("type", "note")))
        date_text = html.escape(str(metadata.get("date", "")))
        title = html.escape(str(metadata.get("title", note_file.stem.replace("-", " ").title())))
        rendered.append(
            "\n".join(
                [
                    '<article class="note-item panel h-entry">',
                    f'  <a class="u-url note-permalink" href="{permalink}">{title}</a>',
                    f'  <div class="note-meta">{note_type} • {date_text}</div>',
                    f'  <div class="e-content">{_markdown(body)}</div>',
                    "</article>",
                ]
            )
        )
        feed_entries.append(
            {
                "title": str(metadata.get("title", note_file.stem.replace("-", " ").title())),
                "permalink": permalink,
                "pub_date": _to_rfc2822(str(metadata.get("date", ""))),
                "body": body.strip()[:1200],
            }
        )

    notes_output = out_dir / "notes" / "index.html"
    notes_output.parent.mkdir(parents=True, exist_ok=True)
    notes_output.write_text(_notes_page(rendered), encoding="utf-8")

    site_url = str(config.get("site_url", "https://flench.me"))
    rss_output = out_dir / "notes" / "rss.xml"
    rss_output.write_text(_notes_rss(site_url, feed_entries), encoding="utf-8")

    _queue_discovered_links(src_dir, out_dir, site_url)

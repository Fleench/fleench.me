# scripts/build_notes.py — Annotated Source Snapshot

This file reproduces the Python source with heavy inline commentary for documentation and onboarding.

```python
# Line 1: from __future__ import annotations
from __future__ import annotations
# Line 2: (blank line used for readability / logical separation)

# Line 3: import datetime as dt
import datetime as dt
# Line 4: import html
import html
# Line 5: import json
import json
# Line 6: import re
import re
# Line 7: from email.utils import format_datetime
from email.utils import format_datetime
# Line 8: from html.parser import HTMLParser
from html.parser import HTMLParser
# Line 9: from pathlib import Path
from pathlib import Path
# Line 10: from typing import Any
from typing import Any
# Line 11: from urllib.parse import urlparse
from urllib.parse import urlparse
# Line 12: from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import escape as xml_escape
# Line 13: (blank line used for readability / logical separation)

# Line 14: try:
try:
# Line 15: import markdown as md_lib  # type: ignore
    import markdown as md_lib  # type: ignore
# Line 16: except Exception:
except Exception:
# Line 17: md_lib = None
    md_lib = None
# Line 18: (blank line used for readability / logical separation)

# Line 19: try:
try:
# Line 20: import yaml  # type: ignore
    import yaml  # type: ignore
# Line 21: except Exception:
except Exception:
# Line 22: yaml = None
    yaml = None
# Line 23: (blank line used for readability / logical separation)

# Line 24: (blank line used for readability / logical separation)

# Line 25: WEBMENTION_STATE_PATH = Path.cwd() / ".webmention-state.json"
WEBMENTION_STATE_PATH = Path.cwd() / ".webmention-state.json"
# Line 26: (blank line used for readability / logical separation)

# Line 27: (blank line used for readability / logical separation)

# Line 28: class _LinkHTMLParser(HTMLParser):
class _LinkHTMLParser(HTMLParser):
# Commentary: Class definition starts here; methods and state behavior appear below.
# Line 29: def __init__(self) -> None:
    def __init__(self) -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 30: super().__init__()
        super().__init__()
# Line 31: self.links: set[str] = set()
        self.links: set[str] = set()
# Line 32: (blank line used for readability / logical separation)

# Line 33: def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 34: attrs_dict = dict(attrs)
        attrs_dict = dict(attrs)
# Line 35: for key in ("href", "src"):
        for key in ("href", "src"):
# Line 36: value = attrs_dict.get(key)
            value = attrs_dict.get(key)
# Line 37: if value:
            if value:
# Line 38: self.links.add(value.strip())
                self.links.add(value.strip())
# Line 39: (blank line used for readability / logical separation)

# Line 40: (blank line used for readability / logical separation)

# Line 41: def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 42: if not raw.startswith("---\n"):
    if not raw.startswith("---\n"):
# Line 43: return {}, raw
        return {}, raw
# Line 44: marker = "\n---\n"
    marker = "\n---\n"
# Line 45: end = raw.find(marker, 4)
    end = raw.find(marker, 4)
# Line 46: if end == -1:
    if end == -1:
# Line 47: return {}, raw
        return {}, raw
# Line 48: header = raw[4:end]
    header = raw[4:end]
# Line 49: body = raw[end + len(marker) :]
    body = raw[end + len(marker) :]
# Line 50: (blank line used for readability / logical separation)

# Line 51: if yaml is not None:
    if yaml is not None:
# Line 52: data = yaml.safe_load(header) or {}
        data = yaml.safe_load(header) or {}
# Line 53: if isinstance(data, dict):
        if isinstance(data, dict):
# Line 54: return data, body
            return data, body
# Line 55: (blank line used for readability / logical separation)

# Line 56: metadata: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
# Line 57: for line in header.splitlines():
    for line in header.splitlines():
# Line 58: if ":" not in line:
        if ":" not in line:
# Line 59: continue
            continue
# Line 60: key, value = line.split(":", 1)
        key, value = line.split(":", 1)
# Line 61: metadata[key.strip()] = value.strip().strip('"').strip("'")
        metadata[key.strip()] = value.strip().strip('"').strip("'")
# Line 62: return metadata, body
    return metadata, body
# Line 63: (blank line used for readability / logical separation)

# Line 64: (blank line used for readability / logical separation)

# Line 65: def _markdown(text: str) -> str:
def _markdown(text: str) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 66: if md_lib is not None:
    if md_lib is not None:
# Line 67: return md_lib.markdown(text, extensions=["extra", "sane_lists"])
        return md_lib.markdown(text, extensions=["extra", "sane_lists"])
# Line 68: return "\n".join(f"<p>{html.escape(line)}</p>" for line in text.splitlines() if line.strip())
    return "\n".join(f"<p>{html.escape(line)}</p>" for line in text.splitlines() if line.strip())
# Line 69: (blank line used for readability / logical separation)

# Line 70: (blank line used for readability / logical separation)

# Line 71: def _to_rfc2822(date_text: str) -> str:
def _to_rfc2822(date_text: str) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 72: candidates = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]
    candidates = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]
# Line 73: for pattern in candidates:
    for pattern in candidates:
# Line 74: try:
        try:
# Line 75: parsed = dt.datetime.strptime(date_text.strip(), pattern)
            parsed = dt.datetime.strptime(date_text.strip(), pattern)
# Line 76: if parsed.tzinfo is None:
            if parsed.tzinfo is None:
# Line 77: parsed = parsed.replace(tzinfo=dt.timezone.utc)
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
# Line 78: return format_datetime(parsed)
            return format_datetime(parsed)
# Line 79: except Exception:
        except Exception:
# Line 80: continue
            continue
# Line 81: return format_datetime(dt.datetime.now(dt.timezone.utc))
    return format_datetime(dt.datetime.now(dt.timezone.utc))
# Line 82: (blank line used for readability / logical separation)

# Line 83: (blank line used for readability / logical separation)

# Line 84: def _notes_page(items: list[str]) -> str:
def _notes_page(items: list[str]) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 85: return "\n".join(
    return "\n".join(
# Line 86: [
        [
# Line 87: "<!DOCTYPE html>",
            "<!DOCTYPE html>",
# Line 88: '<html lang="en">',
            '<html lang="en">',
# Line 89: "<head>",
            "<head>",
# Line 90: '  <meta charset="UTF-8">',
            '  <meta charset="UTF-8">',
# Line 91: '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
# Line 92: "  <title>Notes</title>",
            "  <title>Notes</title>",
# Line 93: '  <link rel="stylesheet" href="/style.css">',
            '  <link rel="stylesheet" href="/style.css">',
# Line 94: '  <link rel="alternate" type="application/rss+xml" title="Site RSS" href="/rss.xml">',
            '  <link rel="alternate" type="application/rss+xml" title="Site RSS" href="/rss.xml">',
# Line 95: '  <script src="/layout.js" defer></script>',
            '  <script src="/layout.js" defer></script>',
# Line 96: '  <script src="/mentions.js" defer></script>',
            '  <script src="/mentions.js" defer></script>',
# Line 97: "</head>",
            "</head>",
# Line 98: "<body>",
            "<body>",
# Line 99: '  <div class="page-wrap">',
            '  <div class="page-wrap">',
# Line 100: '    <div class="site-layout">',
            '    <div class="site-layout">',
# Line 101: '      <div class="center-column">',
            '      <div class="center-column">',
# Line 102: '        <div class="content-shell">',
            '        <div class="content-shell">',
# Line 103: '          <nav class="top-nav panel" aria-label="Primary navigation">',
            '          <nav class="top-nav panel" aria-label="Primary navigation">',
# Line 104: '            <a href="/">Home</a>',
            '            <a href="/">Home</a>',
# Line 105: '            <a href="/notes/">Notes</a>',
            '            <a href="/notes/">Notes</a>',
# Line 106: "          </nav>",
            "          </nav>",
# Line 107: '          <main class="layout">',
            '          <main class="layout">',
# Line 108: '            <section class="content panel notes-index">',
            '            <section class="content panel notes-index">',
# Line 109: "              <h1>Notes</h1>",
            "              <h1>Notes</h1>",
# Line 110: '              <p><a href="/rss.xml">Subscribe via RSS</a></p>',
            '              <p><a href="/rss.xml">Subscribe via RSS</a></p>',
# Line 111: '              <div class="notes-list">',
            '              <div class="notes-list">',
# Line 112: *[f"                {item}" for item in items],
            *[f"                {item}" for item in items],
# Line 113: "              </div>",
            "              </div>",
# Line 114: "            </section>",
            "            </section>",
# Line 115: '            <section class="main-extras">',
            '            <section class="main-extras">',
# Line 116: '              <div id="webmentions"></div>',
            '              <div id="webmentions"></div>',
# Line 117: "            </section>",
            "            </section>",
# Line 118: "          </main>",
            "          </main>",
# Line 119: "        </div>",
            "        </div>",
# Line 120: "      </div>",
            "      </div>",
# Line 121: "    </div>",
            "    </div>",
# Line 122: "  </div>",
            "  </div>",
# Line 123: "</body>",
            "</body>",
# Line 124: "</html>",
            "</html>",
# Line 125: ]
        ]
# Line 126: )
    )
# Line 127: (blank line used for readability / logical separation)

# Line 128: (blank line used for readability / logical separation)

# Line 129: def _notes_rss(site_url: str, entries: list[dict[str, str]]) -> str:
def _notes_rss(site_url: str, entries: list[dict[str, str]]) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 130: items: list[str] = []
    items: list[str] = []
# Line 131: for entry in entries:
    for entry in entries:
# Line 132: body = xml_escape(entry["body"])
        body = xml_escape(entry["body"])
# Line 133: title = xml_escape(entry["title"])
        title = xml_escape(entry["title"])
# Line 134: link = f"{site_url.rstrip('/')}{entry['permalink']}"
        link = f"{site_url.rstrip('/')}{entry['permalink']}"
# Line 135: items.append(
        items.append(
# Line 136: "\n".join(
            "\n".join(
# Line 137: [
                [
# Line 138: "    <item>",
                    "    <item>",
# Line 139: f"      <title>{title}</title>",
                    f"      <title>{title}</title>",
# Line 140: f"      <link>{xml_escape(link)}</link>",
                    f"      <link>{xml_escape(link)}</link>",
# Line 141: f"      <guid>{xml_escape(link)}</guid>",
                    f"      <guid>{xml_escape(link)}</guid>",
# Line 142: f"      <pubDate>{entry['pub_date']}</pubDate>",
                    f"      <pubDate>{entry['pub_date']}</pubDate>",
# Line 143: f"      <description>{body}</description>",
                    f"      <description>{body}</description>",
# Line 144: "    </item>",
                    "    </item>",
# Line 145: ]
                ]
# Line 146: )
            )
# Line 147: )
        )
# Line 148: (blank line used for readability / logical separation)

# Line 149: return "\n".join(
    return "\n".join(
# Line 150: [
        [
# Line 151: '<?xml version="1.0" encoding="UTF-8"?>',
            '<?xml version="1.0" encoding="UTF-8"?>',
# Line 152: '<rss version="2.0">',
            '<rss version="2.0">',
# Line 153: "  <channel>",
            "  <channel>",
# Line 154: "    <title>Notes</title>",
            "    <title>Notes</title>",
# Line 155: f"    <link>{xml_escape(site_url.rstrip('/') + '/notes/')}</link>",
            f"    <link>{xml_escape(site_url.rstrip('/') + '/notes/')}</link>",
# Line 156: "    <description>Latest notes</description>",
            "    <description>Latest notes</description>",
# Line 157: *items,
            *items,
# Line 158: "  </channel>",
            "  </channel>",
# Line 159: "</rss>",
            "</rss>",
# Line 160: ]
        ]
# Line 161: )
    )
# Line 162: (blank line used for readability / logical separation)

# Line 163: (blank line used for readability / logical separation)

# Line 164: def _markdown_source_url(src_dir: Path, md_file: Path, site_url: str) -> str:
def _markdown_source_url(src_dir: Path, md_file: Path, site_url: str) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 165: relative = md_file.relative_to(src_dir)
    relative = md_file.relative_to(src_dir)
# Line 166: if relative.as_posix() == "index.md":
    if relative.as_posix() == "index.md":
# Line 167: return f"{site_url.rstrip('/')}/"
        return f"{site_url.rstrip('/')}/"
# Line 168: return f"{site_url.rstrip('/')}/{relative.with_suffix('').as_posix()}/"
    return f"{site_url.rstrip('/')}/{relative.with_suffix('').as_posix()}/"
# Line 169: (blank line used for readability / logical separation)

# Line 170: (blank line used for readability / logical separation)

# Line 171: def _html_source_url(out_dir: Path, html_file: Path, site_url: str) -> str:
def _html_source_url(out_dir: Path, html_file: Path, site_url: str) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 172: relative = html_file.relative_to(out_dir).as_posix()
    relative = html_file.relative_to(out_dir).as_posix()
# Line 173: if relative == "index.html":
    if relative == "index.html":
# Line 174: return f"{site_url.rstrip('/')}/"
        return f"{site_url.rstrip('/')}/"
# Line 175: if relative.endswith("/index.html"):
    if relative.endswith("/index.html"):
# Line 176: return f"{site_url.rstrip('/')}/{relative[:-len('index.html')]}"
        return f"{site_url.rstrip('/')}/{relative[:-len('index.html')]}"
# Line 177: return f"{site_url.rstrip('/')}/{relative}"
    return f"{site_url.rstrip('/')}/{relative}"
# Line 178: (blank line used for readability / logical separation)

# Line 179: (blank line used for readability / logical separation)

# Line 180: def _extract_links_from_markdown(markdown_text: str) -> set[str]:
def _extract_links_from_markdown(markdown_text: str) -> set[str]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 181: links = set(re.findall(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", markdown_text))
    links = set(re.findall(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", markdown_text))
# Line 182: links.update(re.findall(r"<((?:https?://)[^>]+)>", markdown_text))
    links.update(re.findall(r"<((?:https?://)[^>]+)>", markdown_text))
# Line 183: return {link.strip() for link in links if link.strip()}
    return {link.strip() for link in links if link.strip()}
# Line 184: (blank line used for readability / logical separation)

# Line 185: (blank line used for readability / logical separation)

# Line 186: def _extract_links_from_html(html_text: str) -> set[str]:
def _extract_links_from_html(html_text: str) -> set[str]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 187: parser = _LinkHTMLParser()
    parser = _LinkHTMLParser()
# Line 188: parser.feed(html_text)
    parser.feed(html_text)
# Line 189: return parser.links
    return parser.links
# Line 190: (blank line used for readability / logical separation)

# Line 191: (blank line used for readability / logical separation)

# Line 192: def _is_http_external(link: str, site_host: str) -> bool:
def _is_http_external(link: str, site_host: str) -> bool:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 193: parsed = urlparse(link)
    parsed = urlparse(link)
# Line 194: if parsed.scheme not in {"http", "https"} or not parsed.netloc:
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
# Line 195: return False
        return False
# Line 196: return parsed.netloc != site_host
    return parsed.netloc != site_host
# Line 197: (blank line used for readability / logical separation)

# Line 198: (blank line used for readability / logical separation)

# Line 199: def _load_webmention_state() -> dict[str, Any]:
def _load_webmention_state() -> dict[str, Any]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 200: if not WEBMENTION_STATE_PATH.exists():
    if not WEBMENTION_STATE_PATH.exists():
# Line 201: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 202: try:
    try:
# Line 203: data = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
        data = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
# Line 204: except Exception:
    except Exception:
# Line 205: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 206: if not isinstance(data, dict):
    if not isinstance(data, dict):
# Line 207: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 208: data.setdefault("version", 1)
    data.setdefault("version", 1)
# Line 209: data.setdefault("queue", [])
    data.setdefault("queue", [])
# Line 210: data.setdefault("published", [])
    data.setdefault("published", [])
# Line 211: return data
    return data
# Line 212: (blank line used for readability / logical separation)

# Line 213: (blank line used for readability / logical separation)

# Line 214: def _queue_discovered_links(src_dir: Path, out_dir: Path, site_url: str) -> int:
def _queue_discovered_links(src_dir: Path, out_dir: Path, site_url: str) -> int:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 215: site_host = urlparse(site_url).netloc
    site_host = urlparse(site_url).netloc
# Line 216: if not site_host:
    if not site_host:
# Line 217: return 0
        return 0
# Line 218: (blank line used for readability / logical separation)

# Line 219: discovered: set[tuple[str, str]] = set()
    discovered: set[tuple[str, str]] = set()
# Line 220: (blank line used for readability / logical separation)

# Line 221: for md_file in sorted(src_dir.rglob("*.md")):
    for md_file in sorted(src_dir.rglob("*.md")):
# Line 222: _, body = _parse_frontmatter(md_file.read_text(encoding="utf-8"))
        _, body = _parse_frontmatter(md_file.read_text(encoding="utf-8"))
# Line 223: source = _markdown_source_url(src_dir, md_file, site_url)
        source = _markdown_source_url(src_dir, md_file, site_url)
# Line 224: for link in _extract_links_from_markdown(body):
        for link in _extract_links_from_markdown(body):
# Line 225: if _is_http_external(link, site_host):
            if _is_http_external(link, site_host):
# Line 226: discovered.add((source, link))
                discovered.add((source, link))
# Line 227: (blank line used for readability / logical separation)

# Line 228: for html_file in sorted(out_dir.rglob("*.html")):
    for html_file in sorted(out_dir.rglob("*.html")):
# Line 229: source = _html_source_url(out_dir, html_file, site_url)
        source = _html_source_url(out_dir, html_file, site_url)
# Line 230: html_text = html_file.read_text(encoding="utf-8")
        html_text = html_file.read_text(encoding="utf-8")
# Line 231: for link in _extract_links_from_html(html_text):
        for link in _extract_links_from_html(html_text):
# Line 232: if _is_http_external(link, site_host):
            if _is_http_external(link, site_host):
# Line 233: discovered.add((source, link))
                discovered.add((source, link))
# Line 234: (blank line used for readability / logical separation)

# Line 235: state = _load_webmention_state()
    state = _load_webmention_state()
# Line 236: queue = state.get("queue", [])
    queue = state.get("queue", [])
# Line 237: published = state.get("published", [])
    published = state.get("published", [])
# Line 238: (blank line used for readability / logical separation)

# Line 239: existing = {
    existing = {
# Line 240: (item.get("source", ""), item.get("target", ""))
        (item.get("source", ""), item.get("target", ""))
# Line 241: for item in [*queue, *published]
        for item in [*queue, *published]
# Line 242: if isinstance(item, dict)
        if isinstance(item, dict)
# Line 243: }
    }
# Line 244: (blank line used for readability / logical separation)

# Line 245: now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
# Line 246: added = 0
    added = 0
# Line 247: for source, target in sorted(discovered):
    for source, target in sorted(discovered):
# Line 248: if (source, target) in existing:
        if (source, target) in existing:
# Line 249: continue
            continue
# Line 250: queue.append({"source": source, "target": target, "queued_at": now})
        queue.append({"source": source, "target": target, "queued_at": now})
# Line 251: existing.add((source, target))
        existing.add((source, target))
# Line 252: added += 1
        added += 1
# Line 253: (blank line used for readability / logical separation)

# Line 254: state["queue"] = queue
    state["queue"] = queue
# Line 255: WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
# Line 256: if added:
    if added:
# Line 257: print(f"Queued {added} webmention(s) in {WEBMENTION_STATE_PATH.name}")
        print(f"Queued {added} webmention(s) in {WEBMENTION_STATE_PATH.name}")
# Line 258: return added
    return added
# Line 259: (blank line used for readability / logical separation)

# Line 260: (blank line used for readability / logical separation)

# Line 261: def main(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
def main(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 262: notes_dir = src_dir / "notes"
    notes_dir = src_dir / "notes"
# Line 263: notes = sorted(notes_dir.rglob("*.md"), reverse=True) if notes_dir.exists() else []
    notes = sorted(notes_dir.rglob("*.md"), reverse=True) if notes_dir.exists() else []
# Line 264: rendered: list[str] = []
    rendered: list[str] = []
# Line 265: feed_entries: list[dict[str, str]] = []
    feed_entries: list[dict[str, str]] = []
# Line 266: for note_file in notes:
    for note_file in notes:
# Line 267: metadata, body = _parse_frontmatter(note_file.read_text(encoding="utf-8"))
        metadata, body = _parse_frontmatter(note_file.read_text(encoding="utf-8"))
# Line 268: relative = note_file.relative_to(src_dir).with_suffix("").as_posix()
        relative = note_file.relative_to(src_dir).with_suffix("").as_posix()
# Line 269: permalink = f"/{relative}/"
        permalink = f"/{relative}/"
# Line 270: note_type = html.escape(str(metadata.get("type", "note")))
        note_type = html.escape(str(metadata.get("type", "note")))
# Line 271: date_text = html.escape(str(metadata.get("date", "")))
        date_text = html.escape(str(metadata.get("date", "")))
# Line 272: title = html.escape(str(metadata.get("title", note_file.stem.replace("-", " ").title())))
        title = html.escape(str(metadata.get("title", note_file.stem.replace("-", " ").title())))
# Line 273: rendered.append(
        rendered.append(
# Line 274: "\n".join(
            "\n".join(
# Line 275: [
                [
# Line 276: '<article class="note-item panel h-entry">',
                    '<article class="note-item panel h-entry">',
# Line 277: f'  <a class="u-url note-permalink" href="{permalink}">{title}</a>',
                    f'  <a class="u-url note-permalink" href="{permalink}">{title}</a>',
# Line 278: f'  <div class="note-meta">{note_type} • {date_text}</div>',
                    f'  <div class="note-meta">{note_type} • {date_text}</div>',
# Line 279: f'  <div class="e-content">{_markdown(body)}</div>',
                    f'  <div class="e-content">{_markdown(body)}</div>',
# Line 280: "</article>",
                    "</article>",
# Line 281: ]
                ]
# Line 282: )
            )
# Line 283: )
        )
# Line 284: feed_entries.append(
        feed_entries.append(
# Line 285: {
            {
# Line 286: "title": str(metadata.get("title", note_file.stem.replace("-", " ").title())),
                "title": str(metadata.get("title", note_file.stem.replace("-", " ").title())),
# Line 287: "permalink": permalink,
                "permalink": permalink,
# Line 288: "pub_date": _to_rfc2822(str(metadata.get("date", ""))),
                "pub_date": _to_rfc2822(str(metadata.get("date", ""))),
# Line 289: "body": body.strip()[:1200],
                "body": body.strip()[:1200],
# Line 290: }
            }
# Line 291: )
        )
# Line 292: (blank line used for readability / logical separation)

# Line 293: notes_output = out_dir / "notes" / "index.html"
    notes_output = out_dir / "notes" / "index.html"
# Line 294: notes_output.parent.mkdir(parents=True, exist_ok=True)
    notes_output.parent.mkdir(parents=True, exist_ok=True)
# Line 295: notes_output.write_text(_notes_page(rendered), encoding="utf-8")
    notes_output.write_text(_notes_page(rendered), encoding="utf-8")
# Line 296: (blank line used for readability / logical separation)

# Line 297: site_url = str(config.get("site_url", "https://flench.me"))
    site_url = str(config.get("site_url", "https://flench.me"))
# Line 298: rss_output = out_dir / "notes" / "rss.xml"
    rss_output = out_dir / "notes" / "rss.xml"
# Line 299: rss_output.write_text(_notes_rss(site_url, feed_entries), encoding="utf-8")
    rss_output.write_text(_notes_rss(site_url, feed_entries), encoding="utf-8")
# Line 300: (blank line used for readability / logical separation)

# Line 301: _queue_discovered_links(src_dir, out_dir, site_url)
    _queue_discovered_links(src_dir, out_dir, site_url)
```

# gen.py — Annotated Source Snapshot

This file reproduces the Python source with heavy inline commentary for documentation and onboarding.

```python
# Line 1: #!/usr/bin/env python3
#!/usr/bin/env python3
# Line 2: from __future__ import annotations
from __future__ import annotations
# Line 3: (blank line used for readability / logical separation)

# Line 4: import argparse
import argparse
# Line 5: import html
import html
# Line 6: import importlib
import importlib
# Line 7: import json
import json
# Line 8: import re
import re
# Line 9: import xml.etree.ElementTree as ET
import xml.etree.ElementTree as ET
# Line 10: import urllib.error
import urllib.error
# Line 11: import urllib.parse
import urllib.parse
# Line 12: import urllib.request
import urllib.request
# Line 13: from dataclasses import dataclass
from dataclasses import dataclass
# Line 14: from datetime import datetime, timezone
from datetime import datetime, timezone
# Line 15: from email.utils import parsedate_to_datetime
from email.utils import parsedate_to_datetime
# Line 16: from pathlib import Path
from pathlib import Path
# Line 17: from typing import Any
from typing import Any
# Line 18: (blank line used for readability / logical separation)

# Line 19: try:
try:
# Line 20: import markdown as md_lib  # type: ignore
    import markdown as md_lib  # type: ignore
# Line 21: except Exception:
except Exception:
# Line 22: md_lib = None
    md_lib = None
# Line 23: (blank line used for readability / logical separation)

# Line 24: try:
try:
# Line 25: import yaml  # type: ignore
    import yaml  # type: ignore
# Line 26: except Exception:
except Exception:
# Line 27: yaml = None
    yaml = None
# Line 28: (blank line used for readability / logical separation)

# Line 29: DEFAULT_CONFIG: dict[str, Any] = {
DEFAULT_CONFIG: dict[str, Any] = {
# Line 30: "src_dir": "src",
    "src_dir": "src",
# Line 31: "out_dir": "dist",
    "out_dir": "dist",
# Line 32: "default_template": "src/page.html.temp",
    "default_template": "src/page.html.temp",
# Line 33: "plugins": [],
    "plugins": [],
# Line 34: "site_url": "https://flench.me",
    "site_url": "https://flench.me",
# Line 35: "rss": False,
    "rss": False,
# Line 36: }
}
# Line 37: (blank line used for readability / logical separation)

# Line 38: WEBMENTION_STATE_PATH = Path(".webmention-state.json")
WEBMENTION_STATE_PATH = Path(".webmention-state.json")
# Line 39: FED_BRIDGY_ENDPOINT = "https://fed.brid.gy/webmention"
FED_BRIDGY_ENDPOINT = "https://fed.brid.gy/webmention"
# Line 40: (blank line used for readability / logical separation)

# Line 41: (blank line used for readability / logical separation)

# Line 42: @dataclass
@dataclass
# Line 43: class ParsedMarkdown:
class ParsedMarkdown:
# Commentary: Class definition starts here; methods and state behavior appear below.
# Line 44: metadata: dict[str, Any]
    metadata: dict[str, Any]
# Line 45: body: str
    body: str
# Line 46: (blank line used for readability / logical separation)

# Line 47: (blank line used for readability / logical separation)

# Line 48: def parse_frontmatter(raw: str) -> ParsedMarkdown:
def parse_frontmatter(raw: str) -> ParsedMarkdown:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 49: if not raw.startswith("---\n"):
    if not raw.startswith("---\n"):
# Line 50: return ParsedMarkdown(metadata={}, body=raw)
        return ParsedMarkdown(metadata={}, body=raw)
# Line 51: (blank line used for readability / logical separation)

# Line 52: marker = "\n---\n"
    marker = "\n---\n"
# Line 53: end = raw.find(marker, 4)
    end = raw.find(marker, 4)
# Line 54: if end == -1:
    if end == -1:
# Line 55: return ParsedMarkdown(metadata={}, body=raw)
        return ParsedMarkdown(metadata={}, body=raw)
# Line 56: (blank line used for readability / logical separation)

# Line 57: header_text = raw[4:end]
    header_text = raw[4:end]
# Line 58: body = raw[end + len(marker) :]
    body = raw[end + len(marker) :]
# Line 59: (blank line used for readability / logical separation)

# Line 60: if yaml is not None:
    if yaml is not None:
# Line 61: data = yaml.safe_load(header_text) or {}
        data = yaml.safe_load(header_text) or {}
# Line 62: if isinstance(data, dict):
        if isinstance(data, dict):
# Line 63: return ParsedMarkdown(metadata={str(k): v for k, v in data.items()}, body=body)
            return ParsedMarkdown(metadata={str(k): v for k, v in data.items()}, body=body)
# Line 64: (blank line used for readability / logical separation)

# Line 65: metadata: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
# Line 66: for line in header_text.splitlines():
    for line in header_text.splitlines():
# Line 67: if ":" not in line:
        if ":" not in line:
# Line 68: continue
            continue
# Line 69: key, value = line.split(":", 1)
        key, value = line.split(":", 1)
# Line 70: metadata[key.strip()] = value.strip().strip('"').strip("'")
        metadata[key.strip()] = value.strip().strip('"').strip("'")
# Line 71: return ParsedMarkdown(metadata=metadata, body=body)
    return ParsedMarkdown(metadata=metadata, body=body)
# Line 72: (blank line used for readability / logical separation)

# Line 73: (blank line used for readability / logical separation)

# Line 74: def markdown_to_html(markdown_text: str) -> str:
def markdown_to_html(markdown_text: str) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 75: if md_lib is not None:
    if md_lib is not None:
# Line 76: return md_lib.markdown(markdown_text, extensions=["extra", "sane_lists"])
        return md_lib.markdown(markdown_text, extensions=["extra", "sane_lists"])
# Line 77: (blank line used for readability / logical separation)

# Line 78: chunks: list[str] = []
    chunks: list[str] = []
# Line 79: for line in markdown_text.splitlines():
    for line in markdown_text.splitlines():
# Line 80: stripped = line.strip()
        stripped = line.strip()
# Line 81: if not stripped:
        if not stripped:
# Line 82: continue
            continue
# Line 83: heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
# Line 84: if heading:
        if heading:
# Line 85: level = len(heading.group(1))
            level = len(heading.group(1))
# Line 86: chunks.append(f"<h{level}>{html.escape(heading.group(2))}</h{level}>")
            chunks.append(f"<h{level}>{html.escape(heading.group(2))}</h{level}>")
# Line 87: else:
        else:
# Line 88: chunks.append(f"<p>{html.escape(stripped)}</p>")
            chunks.append(f"<p>{html.escape(stripped)}</p>")
# Line 89: return "\n".join(chunks)
    return "\n".join(chunks)
# Line 90: (blank line used for readability / logical separation)

# Line 91: (blank line used for readability / logical separation)

# Line 92: def render_template(template_text: str, context: dict[str, Any]) -> str:
def render_template(template_text: str, context: dict[str, Any]) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 93: rendered = template_text
    rendered = template_text
# Line 94: for key, value in context.items():
    for key, value in context.items():
# Line 95: rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
# Line 96: return rendered
    return rendered
# Line 97: (blank line used for readability / logical separation)

# Line 98: (blank line used for readability / logical separation)

# Line 99: def clean_output_path(src_file: Path, src_dir: Path, out_dir: Path) -> Path:
def clean_output_path(src_file: Path, src_dir: Path, out_dir: Path) -> Path:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 100: relative = src_file.relative_to(src_dir)
    relative = src_file.relative_to(src_dir)
# Line 101: if relative.as_posix() == "index.md":
    if relative.as_posix() == "index.md":
# Line 102: return out_dir / "index.html"
        return out_dir / "index.html"
# Line 103: (blank line used for readability / logical separation)

# Line 104: page_dir = relative.with_suffix("")
    page_dir = relative.with_suffix("")
# Line 105: return out_dir / page_dir / "index.html"
    return out_dir / page_dir / "index.html"
# Line 106: (blank line used for readability / logical separation)

# Line 107: (blank line used for readability / logical separation)

# Line 108: def derive_title(src_file: Path, parsed: ParsedMarkdown) -> str:
def derive_title(src_file: Path, parsed: ParsedMarkdown) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 109: explicit = parsed.metadata.get("title")
    explicit = parsed.metadata.get("title")
# Line 110: if isinstance(explicit, str) and explicit.strip():
    if isinstance(explicit, str) and explicit.strip():
# Line 111: return explicit.strip()
        return explicit.strip()
# Line 112: if src_file.stem.lower() == "index":
    if src_file.stem.lower() == "index":
# Line 113: return "Home"
        return "Home"
# Line 114: return src_file.stem.replace("-", " ").replace("_", " ").title()
    return src_file.stem.replace("-", " ").replace("_", " ").title()
# Line 115: (blank line used for readability / logical separation)

# Line 116: (blank line used for readability / logical separation)

# Line 117: def build_site(src_dir: Path, out_dir: Path, default_template: Path, config: dict[str, Any]) -> int:
def build_site(src_dir: Path, out_dir: Path, default_template: Path, config: dict[str, Any]) -> int:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 118: if not src_dir.exists():
    if not src_dir.exists():
# Line 119: raise FileNotFoundError(f"Source directory not found: {src_dir}")
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
# Line 120: (blank line used for readability / logical separation)

# Line 121: if not default_template.exists():
    if not default_template.exists():
# Line 122: raise FileNotFoundError(f"Default template not found: {default_template}")
        raise FileNotFoundError(f"Default template not found: {default_template}")
# Line 123: (blank line used for readability / logical separation)

# Line 124: out_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
# Line 125: default_template_text = default_template.read_text(encoding="utf-8")
    default_template_text = default_template.read_text(encoding="utf-8")
# Line 126: (blank line used for readability / logical separation)

# Line 127: built = 0
    built = 0
# Line 128: for md_file in sorted(src_dir.rglob("*.md")):
    for md_file in sorted(src_dir.rglob("*.md")):
# Line 129: parsed = parse_frontmatter(md_file.read_text(encoding="utf-8"))
        parsed = parse_frontmatter(md_file.read_text(encoding="utf-8"))
# Line 130: (blank line used for readability / logical separation)

# Line 131: selected_template = parsed.metadata.get("template")
        selected_template = parsed.metadata.get("template")
# Line 132: if selected_template:
        if selected_template:
# Line 133: template_path = Path(str(selected_template))
            template_path = Path(str(selected_template))
# Line 134: elif md_file.is_relative_to(src_dir / "notes"):
        elif md_file.is_relative_to(src_dir / "notes"):
# Line 135: template_path = Path.cwd() / src_dir / "note.html.temp"
            template_path = Path.cwd() / src_dir / "note.html.temp"
# Line 136: else:
        else:
# Line 137: template_path = default_template
            template_path = default_template
# Line 138: if not template_path.is_absolute():
        if not template_path.is_absolute():
# Line 139: template_path = Path.cwd() / template_path
            template_path = Path.cwd() / template_path
# Line 140: template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else default_template_text
        template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else default_template_text
# Line 141: (blank line used for readability / logical separation)

# Line 142: body_html = markdown_to_html(parsed.body)
        body_html = markdown_to_html(parsed.body)
# Line 143: output_path = clean_output_path(md_file, src_dir, out_dir)
        output_path = clean_output_path(md_file, src_dir, out_dir)
# Line 144: output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)
# Line 145: (blank line used for readability / logical separation)

# Line 146: rel_url = "/" + output_path.relative_to(out_dir).as_posix()
        rel_url = "/" + output_path.relative_to(out_dir).as_posix()
# Line 147: if rel_url.endswith("/index.html"):
        if rel_url.endswith("/index.html"):
# Line 148: rel_url = rel_url[: -len("index.html")]
            rel_url = rel_url[: -len("index.html")]
# Line 149: (blank line used for readability / logical separation)

# Line 150: escaped_meta = {k: html.escape(str(v)) for k, v in parsed.metadata.items()}
        escaped_meta = {k: html.escape(str(v)) for k, v in parsed.metadata.items()}
# Line 151: context = {
        context = {
# Line 152: "title": html.escape(derive_title(md_file, parsed)),
            "title": html.escape(derive_title(md_file, parsed)),
# Line 153: "content": body_html,
            "content": body_html,
# Line 154: "date": html.escape(str(parsed.metadata.get("date", ""))),
            "date": html.escape(str(parsed.metadata.get("date", ""))),
# Line 155: "output": rel_url,
            "output": rel_url,
# Line 156: **escaped_meta,
            **escaped_meta,
# Line 157: }
        }
# Line 158: output_path.write_text(render_template(template_text, context), encoding="utf-8")
        output_path.write_text(render_template(template_text, context), encoding="utf-8")
# Line 159: built += 1
        built += 1
# Line 160: (blank line used for readability / logical separation)

# Line 161: for asset in src_dir.rglob("*"):
    for asset in src_dir.rglob("*"):
# Line 162: if not asset.is_file() or asset.suffix.lower() == ".md":
        if not asset.is_file() or asset.suffix.lower() == ".md":
# Line 163: continue
            continue
# Line 164: destination = out_dir / asset.relative_to(src_dir)
        destination = out_dir / asset.relative_to(src_dir)
# Line 165: destination.parent.mkdir(parents=True, exist_ok=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
# Line 166: destination.write_bytes(asset.read_bytes())
        destination.write_bytes(asset.read_bytes())
# Line 167: (blank line used for readability / logical separation)

# Line 168: run_plugins(src_dir, out_dir, config)
    run_plugins(src_dir, out_dir, config)
# Line 169: build_combined_rss_feed(out_dir, str(config.get("site_url", "https://flench.me")))
    build_combined_rss_feed(out_dir, str(config.get("site_url", "https://flench.me")))
# Line 170: return built
    return built
# Line 171: (blank line used for readability / logical separation)

# Line 172: (blank line used for readability / logical separation)

# Line 173: def run_plugins(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
def run_plugins(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 174: plugins = config.get("plugins", [])
    plugins = config.get("plugins", [])
# Line 175: if not isinstance(plugins, list):
    if not isinstance(plugins, list):
# Line 176: return
        return
# Line 177: (blank line used for readability / logical separation)

# Line 178: for plugin_name in plugins:
    for plugin_name in plugins:
# Line 179: if not isinstance(plugin_name, str) or not plugin_name.strip():
        if not isinstance(plugin_name, str) or not plugin_name.strip():
# Line 180: continue
            continue
# Line 181: module = importlib.import_module(plugin_name)
        module = importlib.import_module(plugin_name)
# Line 182: main = getattr(module, "main", None)
        main = getattr(module, "main", None)
# Line 183: if callable(main):
        if callable(main):
# Line 184: main(src_dir, out_dir, config)
            main(src_dir, out_dir, config)
# Line 185: (blank line used for readability / logical separation)

# Line 186: (blank line used for readability / logical separation)

# Line 187: def _is_enabled(value: Any) -> bool:
def _is_enabled(value: Any) -> bool:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 188: if isinstance(value, bool):
    if isinstance(value, bool):
# Line 189: return value
        return value
# Line 190: if isinstance(value, str):
    if isinstance(value, str):
# Line 191: return value.strip().lower() in {"1", "true", "yes", "on"}
        return value.strip().lower() in {"1", "true", "yes", "on"}
# Line 192: return False
    return False
# Line 193: (blank line used for readability / logical separation)

# Line 194: (blank line used for readability / logical separation)

# Line 195: def build_combined_rss_feed(out_dir: Path, site_url: str) -> bool:
def build_combined_rss_feed(out_dir: Path, site_url: str) -> bool:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 196: rss_files = sorted(path for path in out_dir.rglob("*.xml") if path.relative_to(out_dir).as_posix() != "rss.xml
    rss_files = sorted(path for path in out_dir.rglob("*.xml") if path.relative_to(out_dir).as_posix() != "rss.xml")
# Line 197: if not rss_files:
    if not rss_files:
# Line 198: return False
        return False
# Line 199: (blank line used for readability / logical separation)

# Line 200: items_by_key: dict[str, dict[str, Any]] = {}
    items_by_key: dict[str, dict[str, Any]] = {}
# Line 201: (blank line used for readability / logical separation)

# Line 202: for rss_file in rss_files:
    for rss_file in rss_files:
# Line 203: try:
        try:
# Line 204: root = ET.fromstring(rss_file.read_text(encoding="utf-8"))
            root = ET.fromstring(rss_file.read_text(encoding="utf-8"))
# Line 205: except Exception:
        except Exception:
# Line 206: continue
            continue
# Line 207: (blank line used for readability / logical separation)

# Line 208: channel = root.find("channel")
        channel = root.find("channel")
# Line 209: if channel is None:
        if channel is None:
# Line 210: continue
            continue
# Line 211: (blank line used for readability / logical separation)

# Line 212: for item in channel.findall("item"):
        for item in channel.findall("item"):
# Line 213: link = (item.findtext("link") or "").strip()
            link = (item.findtext("link") or "").strip()
# Line 214: guid = (item.findtext("guid") or "").strip()
            guid = (item.findtext("guid") or "").strip()
# Line 215: title = (item.findtext("title") or "").strip()
            title = (item.findtext("title") or "").strip()
# Line 216: key = guid or link or title
            key = guid or link or title
# Line 217: if not key:
            if not key:
# Line 218: continue
                continue
# Line 219: (blank line used for readability / logical separation)

# Line 220: pub_date = (item.findtext("pubDate") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
# Line 221: sort_key = datetime.min.replace(tzinfo=timezone.utc)
            sort_key = datetime.min.replace(tzinfo=timezone.utc)
# Line 222: if pub_date:
            if pub_date:
# Line 223: try:
                try:
# Line 224: parsed = parsedate_to_datetime(pub_date)
                    parsed = parsedate_to_datetime(pub_date)
# Line 225: sort_key = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                    sort_key = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
# Line 226: except Exception:
                except Exception:
# Line 227: pass
                    pass
# Line 228: (blank line used for readability / logical separation)

# Line 229: item_xml = ET.tostring(item, encoding="unicode")
            item_xml = ET.tostring(item, encoding="unicode")
# Line 230: existing = items_by_key.get(key)
            existing = items_by_key.get(key)
# Line 231: if existing is None or sort_key > existing["sort_key"]:
            if existing is None or sort_key > existing["sort_key"]:
# Line 232: items_by_key[key] = {"sort_key": sort_key, "xml": item_xml}
                items_by_key[key] = {"sort_key": sort_key, "xml": item_xml}
# Line 233: (blank line used for readability / logical separation)

# Line 234: if not items_by_key:
    if not items_by_key:
# Line 235: return False
        return False
# Line 236: (blank line used for readability / logical separation)

# Line 237: ordered_items = [entry["xml"] for entry in sorted(items_by_key.values(), key=lambda value: value["sort_key"], 
    ordered_items = [entry["xml"] for entry in sorted(items_by_key.values(), key=lambda value: value["sort_key"], reverse=True)]
# Line 238: site_root = site_url.rstrip("/")
    site_root = site_url.rstrip("/")
# Line 239: feed_xml = "\n".join(
    feed_xml = "\n".join(
# Line 240: [
        [
# Line 241: '<?xml version="1.0" encoding="UTF-8"?>',
            '<?xml version="1.0" encoding="UTF-8"?>',
# Line 242: '<rss version="2.0">',
            '<rss version="2.0">',
# Line 243: '  <channel>',
            '  <channel>',
# Line 244: '    <title>Site Feed</title>',
            '    <title>Site Feed</title>',
# Line 245: f'    <link>{html.escape(site_root + "/")}</link>',
            f'    <link>{html.escape(site_root + "/")}</link>',
# Line 246: '    <description>Latest updates from across the site</description>',
            '    <description>Latest updates from across the site</description>',
# Line 247: *[f"    {item_xml}" for item_xml in ordered_items],
            *[f"    {item_xml}" for item_xml in ordered_items],
# Line 248: '  </channel>',
            '  </channel>',
# Line 249: '</rss>',
            '</rss>',
# Line 250: ]
        ]
# Line 251: )
    )
# Line 252: (out_dir / "rss.xml").write_text(feed_xml + "\n", encoding="utf-8")
    (out_dir / "rss.xml").write_text(feed_xml + "\n", encoding="utf-8")
# Line 253: return True
    return True
# Line 254: (blank line used for readability / logical separation)

# Line 255: (blank line used for readability / logical separation)

# Line 256: def _simple_yaml_parse(raw: str) -> dict[str, Any]:
def _simple_yaml_parse(raw: str) -> dict[str, Any]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 257: data: dict[str, Any] = {}
    data: dict[str, Any] = {}
# Line 258: current_list_key: str | None = None
    current_list_key: str | None = None
# Line 259: for line in raw.splitlines():
    for line in raw.splitlines():
# Line 260: stripped = line.strip()
        stripped = line.strip()
# Line 261: if not stripped or stripped.startswith("#"):
        if not stripped or stripped.startswith("#"):
# Line 262: continue
            continue
# Line 263: if stripped.startswith("- ") and current_list_key:
        if stripped.startswith("- ") and current_list_key:
# Line 264: data.setdefault(current_list_key, []).append(stripped[2:].strip().strip('"').strip("'"))
            data.setdefault(current_list_key, []).append(stripped[2:].strip().strip('"').strip("'"))
# Line 265: continue
            continue
# Line 266: if ":" in line:
        if ":" in line:
# Line 267: key, value = line.split(":", 1)
            key, value = line.split(":", 1)
# Line 268: key = key.strip()
            key = key.strip()
# Line 269: value = value.strip()
            value = value.strip()
# Line 270: if value == "":
            if value == "":
# Line 271: data[key] = []
                data[key] = []
# Line 272: current_list_key = key
                current_list_key = key
# Line 273: else:
            else:
# Line 274: current_list_key = None
                current_list_key = None
# Line 275: data[key] = value.strip('"').strip("'")
                data[key] = value.strip('"').strip("'")
# Line 276: return data
    return data
# Line 277: (blank line used for readability / logical separation)

# Line 278: (blank line used for readability / logical separation)

# Line 279: def load_config(config_path: Path) -> dict[str, Any]:
def load_config(config_path: Path) -> dict[str, Any]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 280: data = dict(DEFAULT_CONFIG)
    data = dict(DEFAULT_CONFIG)
# Line 281: if not config_path.exists():
    if not config_path.exists():
# Line 282: return data
        return data
# Line 283: (blank line used for readability / logical separation)

# Line 284: raw = config_path.read_text(encoding="utf-8")
    raw = config_path.read_text(encoding="utf-8")
# Line 285: if yaml is not None:
    if yaml is not None:
# Line 286: loaded = yaml.safe_load(raw) or {}
        loaded = yaml.safe_load(raw) or {}
# Line 287: else:
    else:
# Line 288: loaded = _simple_yaml_parse(raw)
        loaded = _simple_yaml_parse(raw)
# Line 289: (blank line used for readability / logical separation)

# Line 290: if isinstance(loaded, dict):
    if isinstance(loaded, dict):
# Line 291: normalized = dict(loaded)
        normalized = dict(loaded)
# Line 292: if "site_url" not in normalized:
        if "site_url" not in normalized:
# Line 293: for alias in ("site-url", "--site-url"):
            for alias in ("site-url", "--site-url"):
# Line 294: if alias in normalized:
                if alias in normalized:
# Line 295: normalized["site_url"] = normalized[alias]
                    normalized["site_url"] = normalized[alias]
# Line 296: break
                    break
# Line 297: data.update(normalized)
        data.update(normalized)
# Line 298: return data
    return data
# Line 299: (blank line used for readability / logical separation)

# Line 300: (blank line used for readability / logical separation)

# Line 301: def _load_webmention_state() -> dict[str, Any]:
def _load_webmention_state() -> dict[str, Any]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 302: if not WEBMENTION_STATE_PATH.exists():
    if not WEBMENTION_STATE_PATH.exists():
# Line 303: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 304: try:
    try:
# Line 305: data = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
        data = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
# Line 306: except Exception:
    except Exception:
# Line 307: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 308: if not isinstance(data, dict):
    if not isinstance(data, dict):
# Line 309: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 310: data.setdefault("version", 1)
    data.setdefault("version", 1)
# Line 311: data.setdefault("queue", [])
    data.setdefault("queue", [])
# Line 312: data.setdefault("published", [])
    data.setdefault("published", [])
# Line 313: return data
    return data
# Line 314: (blank line used for readability / logical separation)

# Line 315: (blank line used for readability / logical separation)

# Line 316: def _save_webmention_state(state: dict[str, Any]) -> None:
def _save_webmention_state(state: dict[str, Any]) -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 317: WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
# Line 318: (blank line used for readability / logical separation)

# Line 319: (blank line used for readability / logical separation)

# Line 320: def queue_bridgy_webping_for_notes(src_dir: Path, out_dir: Path, site_url: str) -> int:
def queue_bridgy_webping_for_notes(src_dir: Path, out_dir: Path, site_url: str) -> int:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 321: site_url_clean = site_url.rstrip("/")
    site_url_clean = site_url.rstrip("/")
# Line 322: notes_dir = src_dir / "notes"
    notes_dir = src_dir / "notes"
# Line 323: if not notes_dir.exists() or not site_url_clean:
    if not notes_dir.exists() or not site_url_clean:
# Line 324: return 0
        return 0
# Line 325: (blank line used for readability / logical separation)

# Line 326: state = _load_webmention_state()
    state = _load_webmention_state()
# Line 327: queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
# Line 328: published = [item for item in state.get("published", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]
# Line 329: (blank line used for readability / logical separation)

# Line 330: existing = {
    existing = {
# Line 331: (str(item.get("source", "")).strip(), str(item.get("target", "")).strip())
        (str(item.get("source", "")).strip(), str(item.get("target", "")).strip())
# Line 332: for item in [*queue, *published]
        for item in [*queue, *published]
# Line 333: }
    }
# Line 334: (blank line used for readability / logical separation)

# Line 335: queued_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    queued_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
# Line 336: added = 0
    added = 0
# Line 337: (blank line used for readability / logical separation)

# Line 338: for md_file in sorted(notes_dir.rglob("*.md")):
    for md_file in sorted(notes_dir.rglob("*.md")):
# Line 339: output_path = clean_output_path(md_file, src_dir, out_dir)
        output_path = clean_output_path(md_file, src_dir, out_dir)
# Line 340: rel_url = "/" + output_path.relative_to(out_dir).as_posix()
        rel_url = "/" + output_path.relative_to(out_dir).as_posix()
# Line 341: if rel_url.endswith("/index.html"):
        if rel_url.endswith("/index.html"):
# Line 342: rel_url = rel_url[: -len("index.html")]
            rel_url = rel_url[: -len("index.html")]
# Line 343: source = f"{site_url_clean}{rel_url}"
        source = f"{site_url_clean}{rel_url}"
# Line 344: key = (source, FED_BRIDGY_ENDPOINT)
        key = (source, FED_BRIDGY_ENDPOINT)
# Line 345: if key in existing:
        if key in existing:
# Line 346: continue
            continue
# Line 347: queue.append({"source": source, "target": FED_BRIDGY_ENDPOINT, "queued_at": queued_at})
        queue.append({"source": source, "target": FED_BRIDGY_ENDPOINT, "queued_at": queued_at})
# Line 348: existing.add(key)
        existing.add(key)
# Line 349: added += 1
        added += 1
# Line 350: (blank line used for readability / logical separation)

# Line 351: state["queue"] = queue
    state["queue"] = queue
# Line 352: _save_webmention_state(state)
    _save_webmention_state(state)
# Line 353: return added
    return added
# Line 354: (blank line used for readability / logical separation)

# Line 355: (blank line used for readability / logical separation)

# Line 356: def publish_webmentions(dry_run: bool = False) -> tuple[int, int]:
def publish_webmentions(dry_run: bool = False) -> tuple[int, int]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 357: state = _load_webmention_state()
    state = _load_webmention_state()
# Line 358: queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
# Line 359: published = [item for item in state.get("published", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]
# Line 360: (blank line used for readability / logical separation)

# Line 361: sent = 0
    sent = 0
# Line 362: failed = 0
    failed = 0
# Line 363: remaining: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
# Line 364: (blank line used for readability / logical separation)

# Line 365: for item in queue:
    for item in queue:
# Line 366: source = str(item.get("source", "")).strip()
        source = str(item.get("source", "")).strip()
# Line 367: target = str(item.get("target", "")).strip()
        target = str(item.get("target", "")).strip()
# Line 368: if not source or not target:
        if not source or not target:
# Line 369: continue
            continue
# Line 370: (blank line used for readability / logical separation)

# Line 371: if dry_run:
        if dry_run:
# Line 372: print(f"DRY RUN publish {source} -> {target}")
            print(f"DRY RUN publish {source} -> {target}")
# Line 373: remaining.append(item)
            remaining.append(item)
# Line 374: continue
            continue
# Line 375: (blank line used for readability / logical separation)

# Line 376: payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
        payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
# Line 377: request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
        request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
# Line 378: request.add_header("Content-Type", "application/x-www-form-urlencoded")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
# Line 379: try:
        try:
# Line 380: with urllib.request.urlopen(request, timeout=15):
            with urllib.request.urlopen(request, timeout=15):
# Line 381: sent += 1
                sent += 1
# Line 382: published.append(
                published.append(
# Line 383: {
                    {
# Line 384: **item,
                        **item,
# Line 385: "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
# Line 386: }
                    }
# Line 387: )
                )
# Line 388: except urllib.error.URLError as exc:
        except urllib.error.URLError as exc:
# Line 389: failed += 1
            failed += 1
# Line 390: remaining.append(item)
            remaining.append(item)
# Line 391: print(f"Failed publishing {source} -> {target}: {exc}")
            print(f"Failed publishing {source} -> {target}: {exc}")
# Line 392: (blank line used for readability / logical separation)

# Line 393: state["queue"] = remaining
    state["queue"] = remaining
# Line 394: state["published"] = published
    state["published"] = published
# Line 395: _save_webmention_state(state)
    _save_webmention_state(state)
# Line 396: return sent, failed
    return sent, failed
# Line 397: (blank line used for readability / logical separation)

# Line 398: (blank line used for readability / logical separation)

# Line 399: def main() -> None:
def main() -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 400: parser = argparse.ArgumentParser(description="Build static site with clean URLs and plugins")
    parser = argparse.ArgumentParser(description="Build static site with clean URLs and plugins")
# Line 401: parser.add_argument("command", nargs="?", default="build", choices=["build", "publish"])
    parser.add_argument("command", nargs="?", default="build", choices=["build", "publish"])
# Line 402: parser.add_argument("--config", default="config.yml")
    parser.add_argument("--config", default="config.yml")
# Line 403: parser.add_argument("--dry-run", action="store_true", help="Print publish actions without sending webmentions"
    parser.add_argument("--dry-run", action="store_true", help="Print publish actions without sending webmentions")
# Line 404: args = parser.parse_args()
    args = parser.parse_args()
# Line 405: (blank line used for readability / logical separation)

# Line 406: if args.command == "publish":
    if args.command == "publish":
# Line 407: sent, failed = publish_webmentions(dry_run=args.dry_run)
        sent, failed = publish_webmentions(dry_run=args.dry_run)
# Line 408: print(f"Published {sent} webmention(s); {failed} failed")
        print(f"Published {sent} webmention(s); {failed} failed")
# Line 409: return
        return
# Line 410: (blank line used for readability / logical separation)

# Line 411: config = load_config(Path(args.config))
    config = load_config(Path(args.config))
# Line 412: src_dir = Path(str(config.get("src_dir", "src")))
    src_dir = Path(str(config.get("src_dir", "src")))
# Line 413: out_dir = Path(str(config.get("out_dir", "dist")))
    out_dir = Path(str(config.get("out_dir", "dist")))
# Line 414: template_path = Path(str(config.get("default_template", "src/page.html.temp")))
    template_path = Path(str(config.get("default_template", "src/page.html.temp")))
# Line 415: (blank line used for readability / logical separation)

# Line 416: built = build_site(src_dir, out_dir, template_path, config)
    built = build_site(src_dir, out_dir, template_path, config)
# Line 417: queued = queue_bridgy_webping_for_notes(src_dir, out_dir, str(config.get("site_url", "https://flench.me")))
    queued = queue_bridgy_webping_for_notes(src_dir, out_dir, str(config.get("site_url", "https://flench.me")))
# Line 418: print(f"Built {built} markdown page(s)")
    print(f"Built {built} markdown page(s)")
# Line 419: if queued:
    if queued:
# Line 420: print(f"Queued {queued} Bridgy Fed webping(s)")
        print(f"Queued {queued} Bridgy Fed webping(s)")
# Line 421: (blank line used for readability / logical separation)

# Line 422: (blank line used for readability / logical separation)

# Line 423: if __name__ == "__main__":
if __name__ == "__main__":
# Line 424: main()
    main()
```

#!/usr/bin/env python3
# pylint: disable=C0301,E0401,E1102,W0718,C0303,C0103
"""
Author: Flench04
Date: 3/7/2026
Description: A python3 based static site generator
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import importlib.util
import json
import logging
import re
import xml.etree.ElementTree as ET
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

try:
    import markdown as MD_LIB  # type: ignore
except Exception:
    MD_LIB = None
    print("No MD_LIB found")
try:
    import YAML  # type: ignore
except Exception:
    YAML = None

try:
    import INDIEWEB_UTILS  # type: ignore
except Exception:
    INDIEWEB_UTILS = None

DEFAULT_CONFIG: dict[str, Any] = {
    "src_dir": "src",
    "out_dir": "dist",
    "default_template": "src/page.html.temp",
    "plugins": [],
    "site_url": "https://flench.me",
    "rss": False,
}

WEBMENTION_STATE_PATH = Path(".webmention-state.json")
FED_BRIDGY_ENDPOINT = "https://fed.brid.gy/webmention"
LOGGER = logging.getLogger("gen")


@dataclass
class ParsedMarkdown:
    """
    Stores Parsed Markdown files allowing for easy access to the 2 chunks generated.
    """
    metadata: dict[str, Any]
    body: str


def parse_frontmatter(raw: str) -> ParsedMarkdown:
    """
    Parse the front matter of a markdown file for metadata on the page to generate
    """
    if not raw.startswith("---\n"):
        return ParsedMarkdown(metadata={}, body=raw)

    marker = "\n---\n"
    end = raw.find(marker, 4)
    if end == -1:
        return ParsedMarkdown(metadata={}, body=raw)

    header_text = raw[4:end]
    body = raw[end + len(marker) :]

    if YAML is not None:
        data = YAML.safe_load(header_text) or {}
        if isinstance(data, dict):
            return ParsedMarkdown(metadata={str(k): v for k, v in data.items()}, body=body)

    metadata: dict[str, Any] = {}
    for line in header_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return ParsedMarkdown(metadata=metadata, body=body)


def configure_logging(level_name: str, json_logs: bool = False) -> None:
    """
    Set up the logger for logging
    """
    level = getattr(logging, level_name.upper(), logging.INFO)
    if json_logs:
        class JsonFormatter(logging.Formatter):
            """
            Basic Frontmatter in json
            """
            def format(self, record: logging.LogRecord) -> str:
                payload = {
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "logger": record.name,
                }
                return json.dumps(payload, ensure_ascii=False)

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(level)
        return

    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def markdown_to_html(markdown_text: str) -> str:
    """
    Converts markdown provided into useable html
    """
    if MD_LIB is not None:
        return MD_LIB.markdown(markdown_text, extensions=["extra", "sane_lists"])

    chunks: list[str] = []
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            chunks.append(f"<h{level}>{html.escape(heading.group(2))}</h{level}>")
        else:
            chunks.append(f"<p>{html.escape(stripped)}</p>")
    return "\n".join(chunks)




def _resolve_element_file(raw_path: str, template_path: Path) -> Path | None:
    candidate = Path(raw_path)
    search_paths: list[Path] = []
    if candidate.is_absolute():
        search_paths.append(candidate)
    else:
        search_paths.append(Path.cwd() / candidate)
        search_paths.append(template_path.parent / candidate)

    for path in search_paths:
        if path.exists() and path.is_file():
            return path
    return None


def _run_dynamic_element(path: Path, render_context: dict[str, Any]) -> str:
    LOGGER.debug("Loading dynamic module: %s", path.name)
    module_name = f"_gen2_dynamic_{hash(path.resolve()) & 0xFFFFFFFF:x}_{path.stat().st_mtime_ns}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return "no module"

    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    try:
        loader.exec_module(module)
    except Exception as e:
        return e

    rendered: Any = ""
    renderer = getattr(module, "render", None)
    if not callable(renderer):
        renderer = getattr(module, "main", None)

    if callable(renderer):
        try:
            rendered = renderer(**render_context)
        except TypeError:
            try:
                LOGGER.debug("Dynamic module renderer rejected kwargs; retrying without context")
                rendered = renderer()
            except Exception as e:
                return e
        except Exception as e:
            return e
    else:
        html_value = getattr(module, "HTML", "")
        rendered = html_value

    if rendered is None:
        return "Error"
    return str(rendered)


def inject_elements(template_text: str, template_path: Path, render_context: dict[str, Any] | None = None) -> str:
    """
    Inject static and Dynamic elemnts into the provided html template text
    """
    LOGGER.debug("Injecting template elements from %s", template_path)
    static_pattern = re.compile(r"~\{([^{}]+)\}~")
    dynamic_pattern = re.compile(r":\{([^{}]+\.py)\}:")
    context = render_context or {}

    def replace_static(match: re.Match[str]) -> str:
        raw_path = match.group(1).strip()
        if not raw_path:
            return ""

        path = _resolve_element_file(raw_path, template_path)
        if path is not None:
            return path.read_text(encoding="utf-8")
        return ""

    def replace_dynamic(match: re.Match[str]) -> str:
        raw_path = match.group(1).strip()
        if not raw_path:
            return ""

        path = _resolve_element_file(raw_path, template_path)
        if path is None:
            return ""

        run_context = {
            "template_path": template_path,
            "project_root": Path.cwd(),
            "md": MD_LIB,
            **context,
        }
        return _run_dynamic_element(path, run_context)
    rendered = template_text
    for _ in range(10):
        updated = static_pattern.sub(replace_static, rendered)
        updated = dynamic_pattern.sub(replace_dynamic, updated)
        if updated == rendered:
            return rendered
        rendered = updated
    return rendered


def render_template(template_text: str, context: dict[str, Any]) -> str:
    """
    Fill in the {{ target }} blocks with target from the markdown file
    """
    rendered = template_text
    for key, value in context.items():
        #print(f"Replacing {key}") # RM
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
    #NEW
    rendered = re.sub(r'\{\{.*\}\}',"",rendered) 
    #END NEW
    return rendered

# R1 MUST REFACTOR TO USE DICT FOR VARS INSTEAD(up to build site)
## Will only include vars passed around
def clean_output_path(build_vars) -> Path:
    """
    Ensure pages are not .html but thier own folder
    """
    relative = build_vars["md_file"].relative_to(build_vars["src_dir"])
    if relative.as_posix() == "index.md":
        return build_vars["out_dir"] / "index.html"

    page_dir = relative.with_suffix("")
    return build_vars["out_dir"] / page_dir / "index.html"


def derive_title(build_vars) -> str:
    """
    Get the proper tile for a page from the markdown file
    """
    explicit = build_vars["parsed"].metadata.get("title")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if build_vars["md_file"].stem.lower() == "index":
        return "Home"
    return build_vars["md_file"].stem.replace("-", " ").replace("_", " ").title()
def _build_paths_exist(build_vars):
    if not build_vars["src_dir"].exists():
        raise FileNotFoundError(f"Source directory not found: {build_vars["src_dir"]}")

    if not build_vars["default_template"].exists():
        raise FileNotFoundError(f"Default template not found: {build_vars["default_template"]}")
def _prep_template(build_vars):
    parsed = parse_frontmatter(build_vars["md_file"].read_text(encoding="utf-8"))
    selected_template = parsed.metadata.get("template")
    if selected_template:
        template_path = Path(str(selected_template))
    elif build_vars["md_file"].is_relative_to(build_vars["src_dir"] / "notes"):
        template_path = Path.cwd() / build_vars["src_dir"] / "note.html.temp"
    else:
        template_path = build_vars["default_template"]
    if not template_path.is_absolute():
        template_path = Path.cwd() / template_path
    template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else build_vars["default_template_text"]
    build_vars["parsed"] = parsed
    build_vars["template_text"] = template_text
    build_vars["template_path"] = template_path
def parse_content(build_vars):
    """
    Parse the body content of a markdown file to enable setting of class and id values of divs we create
    """
    #pylint: disable=R0912
    # Need the changes here for dynamic locations
    # for headings place location as 2nd item seprated by a ---.
    groups = build_vars["parsed"].body.split("\n# ")
    #headings = []
    blocks = []
    for block in groups:
        lines = block.split("\n")
        if len(lines) > 1:
            blocks.append([lines[0],lines[1:]])
        else:
            blocks.append(["",lines[0]])
    locs = {}
    body = ""
    for block in blocks:
        parts = block[0].split("---")
        lef = ""
        rig = ""
        if len(parts)>3 and parts[2]!="{}":
            lef = f"<div class={parts[2]} id={parts[3]}>"
            rig = "</div>"
        elif len(parts)>3 and parts[2]=="{}":
            lef = f"<div  id={parts[3]}>"
            rig = "</div>"
        elif len(parts)>2 and parts[2]!="{}":
            lef = f"<div class={parts[2]}>"
            rig = "</div>"
        if len(parts) > 1 and parts[1] != "{}":
            #print(parts)#rm
            if ("{}") not in parts[0]:
                x = "# " + parts[0] +"\n" + "\n".join(block[1])
            else:
                x = "\n".join(block[1])
            #print(x) #RM
            if parts[1] not in locs:
                locs[parts[1]] = ""
            locs[parts[1]] += "\n" + lef + markdown_to_html(x) + rig
        else:
            if ("{}") not in parts[0]:
                x = "# " + parts[0] +"\n" + "\n".join(block[1])
            else:
                x = "\n".join(block[1])
            body = body + (lef + markdown_to_html(x)+rig)
    build_vars["body"] = body
    build_vars["locs"] = locs
def _derive_path(build_vars):
    output_path = clean_output_path(build_vars)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rel_url = "/" + output_path.relative_to(build_vars["out_dir"]).as_posix()
    if rel_url.endswith("/index.html"):
        rel_url = rel_url[: -len("index.html")]

    canonical = f"{str(build_vars["config"].get('site_url', 'https://flench.me')).rstrip('/')}{rel_url}"
    build_vars["output_path"] = output_path
    build_vars["rel_url"] = rel_url
    build_vars["canonical"] = canonical
def _write_page(build_vars):
    escaped_meta = {k: html.escape(str(v)) for k, v in build_vars["parsed"].metadata.items()}
    context = {
        "title": html.escape(derive_title(build_vars)),
        "content": build_vars["body"],
        "date": html.escape(str(build_vars["parsed"].metadata.get("date", ""))),
        "output": build_vars["rel_url"],
        "canonical": html.escape(build_vars["canonical"]),
        **build_vars["locs"],
        **escaped_meta,
    }
    #print(context) # RM
    build_vars["output_path"].write_text(render_template(build_vars["template_text"], context), encoding="utf-8")

def build_site(src_dir: Path, out_dir: Path, default_template: Path, config: dict[str, Any]) -> int:
    """
    Build the site from the provided input path to the provided output path.
    """
    build_vars = {"default_template_text": default_template.read_text(encoding="utf-8"),
                  "src_dir": src_dir,
                  "out_dir":out_dir,
                  "config":config,
                  "default_template":default_template}
    _build_paths_exist(build_vars)

    out_dir.mkdir(parents=True, exist_ok=True)
    

    built = 0
    for md_file in sorted(src_dir.rglob("*.md")):
        build_vars["md_file"] = md_file
        LOGGER.debug("Rendering markdown file: %s", md_file)
        _prep_template(build_vars)
        build_vars["template_text"] = inject_elements(
            build_vars["template_text"] ,
            build_vars["template_path"] ,
            render_context={
                "src_dir": src_dir,
                "out_dir": out_dir,
                "config": config,
                "current_markdown": md_file,
            },
        )
        parse_content(build_vars)
        # OG CODE
        # body_html = markdown_to_html(parsed.body)
        _derive_path(build_vars)

        _write_page(build_vars)
        built += 1

    for asset in src_dir.rglob("*"):
        skip = [".md",".element",".py",".temp",".bak"]
        if not asset.is_file() or asset.suffix.lower() in skip:
            continue
        destination = out_dir / asset.relative_to(src_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(asset.read_bytes())

    run_plugins(src_dir, out_dir, config)
    build_combined_rss_feed(out_dir, str(config.get("site_url", "https://flench.me")))
    return built


def run_plugins(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
    """
    Run any user provided plugins
    """
    plugins = config.get("plugins", [])
    if not isinstance(plugins, list):
        return

    for plugin_name in plugins:
        if not isinstance(plugin_name, str) or not plugin_name.strip():
            continue
        module = importlib.import_module(plugin_name)
        plugin_main = getattr(module, "main", None)
        if callable(plugin_main):
            plugin_main(src_dir, out_dir, config)


def _is_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False

#R2 REFACTOR TO USE LESS LOCAL VARS 
def build_combined_rss_feed(out_dir: Path, site_url: str) -> bool:
    """
    Combine all rss feeds on the site into one
    """
    rss_files = sorted(path for path in out_dir.rglob("*.xml") if path.relative_to(out_dir).as_posix() != "rss.xml")
    if not rss_files:
        return False

    items_by_key: dict[str, dict[str, Any]] = {}

    def infer_category(rss_file: Path) -> str | None:
        rel = rss_file.relative_to(out_dir)
        parts = rel.parts
        if len(parts) >= 2 and parts[-1] == "rss.xml":
            group = parts[-2].strip().lower()
            if group.endswith("s") and len(group) > 1:
                return group[:-1]
            return group or None
        if parts and parts[-1].lower().endswith(".xml"):
            name = Path(parts[-1]).stem.strip().lower()
            return name or None
        return None

    for rss_file in rss_files:
        category = infer_category(rss_file)
        try:
            root = ET.fromstring(rss_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        channel = root.find("channel")
        if channel is None:
            continue

        for item in channel.findall("item"):
            item_copy = ET.fromstring(ET.tostring(item, encoding="unicode"))
            if category:
                category_node = item_copy.find("category")
                if category_node is None:
                    category_node = ET.SubElement(item_copy, "category")
                category_node.text = category

            link = (item_copy.findtext("link") or "").strip()
            guid = (item_copy.findtext("guid") or "").strip()
            title = (item_copy.findtext("title") or "").strip()
            key = guid or link or title
            if not key:
                continue

            pub_date = (item_copy.findtext("pubDate") or "").strip()
            sort_key = datetime.min.replace(tzinfo=timezone.utc)
            if pub_date:
                try:
                    parsed = parsedate_to_datetime(pub_date)
                    sort_key = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                except Exception:
                    pass

            item_xml = ET.tostring(item_copy, encoding="unicode")
            existing = items_by_key.get(key)
            if existing is None or sort_key > existing["sort_key"]:
                items_by_key[key] = {"sort_key": sort_key, "xml": item_xml}

    if not items_by_key:
        return False

    ordered_items = [entry["xml"] for entry in sorted(items_by_key.values(), key=lambda value: value["sort_key"], reverse=True)]
    site_root = site_url.rstrip("/")
    feed_xml = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0">',
            '  <channel>',
            '    <title>Site Feed</title>',
            f'    <link>{html.escape(site_root + "/")}</link>',
            '    <description>Latest updates from across the site</description>',
            *[f"    {item_xml}" for item_xml in ordered_items],
            '  </channel>',
            '</rss>',
        ]
    )
    (out_dir / "rss.xml").write_text(feed_xml + "\n", encoding="utf-8")
    return True


def _simple_YAML_parse(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key:
            data.setdefault(current_list_key, []).append(stripped[2:].strip().strip('"').strip("'"))
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                data[key] = []
                current_list_key = key
            else:
                current_list_key = None
                data[key] = value.strip('"').strip("'")
    return data


def load_config(config_path: Path) -> dict[str, Any]:
    """
    Load the user config from config.yml
    """
    data = dict(DEFAULT_CONFIG)
    if not config_path.exists():
        return data

    raw = config_path.read_text(encoding="utf-8")
    if YAML is not None:
        loaded = YAML.safe_load(raw) or {}
    else:
        loaded = _simple_YAML_parse(raw)

    if isinstance(loaded, dict):
        normalized = dict(loaded)
        if "site_url" not in normalized:
            for alias in ("site-url", "--site-url"):
                if alias in normalized:
                    normalized["site_url"] = normalized[alias]
                    break
        data.update(normalized)
    return data


def _load_webmention_state() -> dict[str, Any]:
    if not WEBMENTION_STATE_PATH.exists():
        return {"version": 1, "queue": [], "published": [], "current_links": {}}
    try:
        data = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "queue": [], "published": [], "current_links": {}}
    if not isinstance(data, dict):
        return {"version": 1, "queue": [], "published": [], "current_links": {}}
    data.setdefault("version", 1)
    data.setdefault("queue", [])
    data.setdefault("published", [])
    data.setdefault("current_links", {})
    return data


def _save_webmention_state(state: dict[str, Any]) -> None:
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    links = set(re.findall(r"(?:href|src)=['\"]([^'\"]+)['\"]", html_text))
    return {link.strip() for link in links if link.strip()}


def _is_http_external(link: str, site_host: str) -> bool:
    parsed = urllib.parse.urlparse(link)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return parsed.netloc != site_host


def _normalize_for_hash(content: str) -> str:
    return " ".join(content.split())


def _source_fingerprint(content: str) -> str:
    normalized = _normalize_for_hash(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

#R1 Refactor to use many functions
def queue_discovered_webmentions(src_dir: Path, out_dir: Path, site_url: str) -> int:
    """
    Add found links to the webmention queue
    """
    site_host = urllib.parse.urlparse(site_url).netloc
    if not site_host:
        return 0

    discovered: dict[tuple[str, str], str] = {}
    current_links: dict[str, set[str]] = {}

    def record_discovery(source: str, target: str, source_hash: str) -> None:
        discovered.setdefault((source, target), source_hash)
        current_links.setdefault(source, set()).add(target)

    def removed_source_hash(source: str, targets: set[str]) -> str:
        return _source_fingerprint(f"{source}\nremoved\n" + "\n".join(sorted(targets)))
    for md_file in sorted(src_dir.rglob("*.md")):
        parsed = parse_frontmatter(md_file.read_text(encoding="utf-8"))
        source_hash = _source_fingerprint(parsed.body)
        output_path = clean_output_path({"md_file":md_file, "src_dir":src_dir, "out_dir":out_dir})
        rel_url = "/" + output_path.relative_to(out_dir).as_posix()
        if rel_url.endswith("/index.html"):
            rel_url = rel_url[: -len("index.html")]
        source = f"{site_url.rstrip('/')}{rel_url}"
        for link in _extract_links_from_markdown(parsed.body):
            if _is_http_external(link, site_host):
                record_discovery(source, link, source_hash)

    for html_file in sorted(out_dir.rglob("*.html")):
        source = _html_source_url(out_dir, html_file, site_url)
        html_text = html_file.read_text(encoding="utf-8")
        source_hash = _source_fingerprint(html_text)
        for link in _extract_links_from_html(html_text):
            if _is_http_external(link, site_host):
                record_discovery(source, link, source_hash)

    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]
    previous_current_links_raw = state.get("current_links", {})
    previous_current_links: dict[str, set[str]] = {}
    if isinstance(previous_current_links_raw, dict):
        for source, targets in previous_current_links_raw.items():
            if not isinstance(source, str):
                continue
            if isinstance(targets, list):
                previous_current_links[source] = {str(target).strip() for target in targets if str(target).strip()}

    existing = {
        (
            str(item.get("source", "")).strip(),
            str(item.get("target", "")).strip(),
            str(item.get("source_hash", "")).strip(),
            str(item.get("event", "added") or "added").strip(),
        )
        for item in [*queue, *published]
    }

    queued_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added = 0

    for (source, target), source_hash in sorted(discovered.items()):
        key = (source, target, source_hash, "added")
        if key in existing:
            continue
        queue.append(
            {
                "source": source,
                "target": target,
                "source_hash": source_hash,
                "event": "added",
                "queued_at": queued_at,
            }
        )
        existing.add(key)
        added += 1

    for source, previous_targets in previous_current_links.items():
        removed_targets = previous_targets - current_links.get(source, set())
        if not removed_targets:
            continue
        removal_hash = removed_source_hash(source, removed_targets)
        for target in sorted(removed_targets):
            key = (source, target, removal_hash, "removed")
            if key in existing:
                continue
            queue.append(
                {
                    "source": source,
                    "target": target,
                    "source_hash": removal_hash,
                    "event": "removed",
                    "queued_at": queued_at,
                }
            )
            existing.add(key)
            added += 1

    state["queue"] = queue
    state["current_links"] = {source: sorted(targets) for source, targets in sorted(current_links.items())}
    _save_webmention_state(state)
    return added


def _send_with_legacy_http(source: str, target: str) -> None:
    payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
    request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=15):
        return


def _send_webmention(source: str, target: str) -> None:
    if INDIEWEB_UTILS is not None:
        INDIEWEB_UTILS.send_webmention(source, target)
        return
    _send_with_legacy_http(source, target)


def publish_webmentions(dry_run: bool = False) -> tuple[int, int]:
    """
    Publish all webmentions
    """
    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]

    sent = 0
    failed = 0
    remaining: list[dict[str, Any]] = []

    for item in queue:
        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        event = str(item.get("event", "added") or "added").strip()
        if not source or not target:
            continue

        if dry_run:
            print(f"DRY RUN publish [{event}] {source} -> {target}")
            remaining.append(item)
            continue

        try:
            _send_webmention(source, target)
            sent += 1
            LOGGER.info("Published webmention [%s] %s -> %s", event, source, target)
            published.append(
                {
                    **item,
                    "event": event,
                    "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
            )
        except urllib.error.URLError as exc:
            failed += 1
            remaining.append(item)
            LOGGER.error("Failed publishing %s -> %s: %s", source, target, exc)
        except Exception as exc:
            failed += 1
            remaining.append(item)
            LOGGER.error("Failed publishing %s -> %s: %s", source, target, exc)

    state["queue"] = remaining
    state["published"] = published
    _save_webmention_state(state)
    return sent, failed


def main() -> None:
    """
    Main entry point for the static site generator
    """
    parser = argparse.ArgumentParser(description="Build static site with clean URLs and plugins")
    parser.add_argument("command", nargs="?", default="build", choices=["build", "publish"])
    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--dry-run", action="store_true", help="Print publish actions without sending webmentions")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--json-logs", action="store_true")
    args = parser.parse_args()
    configure_logging(args.log_level, json_logs=args.json_logs)

    if args.command == "publish":
        sent, failed = publish_webmentions(dry_run=args.dry_run)
        LOGGER.info("Published %s webmention(s); %s failed", sent, failed)
        return

    config = load_config(Path(args.config))
    src_dir = Path(str(config.get("src_dir", "src")))
    out_dir = Path(str(config.get("out_dir", "dist")))
    template_path = Path(str(config.get("default_template", "src/page.html.temp")))

    built = build_site(src_dir, out_dir, template_path, config)
    queued = queue_discovered_webmentions(src_dir, out_dir, str(config.get("site_url", "https://flench.me")))
    LOGGER.info("Built %s markdown page(s)", built)
    if queued:
        LOGGER.info("Queued %s webmention(s)", queued)


if __name__ == "__main__":
    main()

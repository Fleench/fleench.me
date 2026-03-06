#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import importlib
import importlib.util
import json
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
    import markdown as md_lib  # type: ignore
except Exception:
    md_lib = None
    print("No md_lib found")
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

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


@dataclass
class ParsedMarkdown:
    metadata: dict[str, Any]
    body: str


def parse_frontmatter(raw: str) -> ParsedMarkdown:
    if not raw.startswith("---\n"):
        return ParsedMarkdown(metadata={}, body=raw)

    marker = "\n---\n"
    end = raw.find(marker, 4)
    if end == -1:
        return ParsedMarkdown(metadata={}, body=raw)

    header_text = raw[4:end]
    body = raw[end + len(marker) :]

    if yaml is not None:
        data = yaml.safe_load(header_text) or {}
        if isinstance(data, dict):
            return ParsedMarkdown(metadata={str(k): v for k, v in data.items()}, body=body)

    metadata: dict[str, Any] = {}
    for line in header_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return ParsedMarkdown(metadata=metadata, body=body)


def markdown_to_html(markdown_text: str) -> str:
    if md_lib is not None:
        return md_lib.markdown(markdown_text, extensions=["extra", "sane_lists"])

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
    print(f"Loading Module at {path.name}")#rm
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
                print("EEEE")#RM
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
    print("Called")#rm
    static_pattern = re.compile(r"~\{([^{}]+)\}~")
    dynamic_pattern = re.compile(r":\{([^{}]+\.py)\}:")
    context = render_context or {}

    def replace_static(match: re.Match[str]) -> str:
        print("HEHE")#RM
        raw_path = match.group(1).strip()
        if not raw_path:
            return ""

        path = _resolve_element_file(raw_path, template_path)
        if path is not None:
            return path.read_text(encoding="utf-8")
        return ""

    def replace_dynamic(match: re.Match[str]) -> str:
        print("Here")#rm
        raw_path = match.group(1).strip()
        if not raw_path:
            return ""

        path = _resolve_element_file(raw_path, template_path)
        if path is None:
            return ""

        run_context = {
            "template_path": template_path,
            "project_root": Path.cwd(),
            "md": md_lib,
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
    rendered = template_text
    for key, value in context.items():
        #print(f"Replacing {key}") # RM
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
    #NEW
    rendered = re.sub(r'\{\{.*\}\}',"",rendered) 
    #END NEW
    return rendered


def clean_output_path(src_file: Path, src_dir: Path, out_dir: Path) -> Path:
    relative = src_file.relative_to(src_dir)
    if relative.as_posix() == "index.md":
        return out_dir / "index.html"

    page_dir = relative.with_suffix("")
    return out_dir / page_dir / "index.html"


def derive_title(src_file: Path, parsed: ParsedMarkdown) -> str:
    explicit = parsed.metadata.get("title")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if src_file.stem.lower() == "index":
        return "Home"
    return src_file.stem.replace("-", " ").replace("_", " ").title()


def build_site(src_dir: Path, out_dir: Path, default_template: Path, config: dict[str, Any]) -> int:
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    if not default_template.exists():
        raise FileNotFoundError(f"Default template not found: {default_template}")

    out_dir.mkdir(parents=True, exist_ok=True)
    default_template_text = default_template.read_text(encoding="utf-8")

    built = 0
    for md_file in sorted(src_dir.rglob("*.md")):
        print(md_file.name)#RM
        if "---" in md_file.name:
            continue
        parsed = parse_frontmatter(md_file.read_text(encoding="utf-8"))

        selected_template = parsed.metadata.get("template")
        if selected_template:
            template_path = Path(str(selected_template))
        elif md_file.is_relative_to(src_dir / "notes"):
            template_path = Path.cwd() / src_dir / "note.html.temp"
        else:
            template_path = default_template
        if not template_path.is_absolute():
            template_path = Path.cwd() / template_path
        template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else default_template_text
        template_text = inject_elements(
            template_text,
            template_path,
            render_context={
                "src_dir": src_dir,
                "out_dir": out_dir,
                "config": config,
                "current_markdown": md_file,
            },
        )
        # Need the changes here for dynamic locations
        # for headings place location as 2nd item seprated by a ---.
        groups = parsed.body.split("\n# ")
        headings = []
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
                if parts[1] not in locs.keys():
                    locs[parts[1]] = ""
                locs[parts[1]] += "\n" + lef + markdown_to_html(x) + rig
            else:
                if ("{}") not in parts[0]:
                    x = "# " + parts[0] +"\n" + "\n".join(block[1])
                else:
                    x = "\n".join(block[1])
                body = body + (lef + markdown_to_html(x)+rig)
        # OG CODE
        # body_html = markdown_to_html(parsed.body)
        output_path = clean_output_path(md_file, src_dir, out_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rel_url = "/" + output_path.relative_to(out_dir).as_posix()
        if rel_url.endswith("/index.html"):
            rel_url = rel_url[: -len("index.html")]

        escaped_meta = {k: html.escape(str(v)) for k, v in parsed.metadata.items()}
        context = {
            "title": html.escape(derive_title(md_file, parsed)),
            "content": body,
            "date": html.escape(str(parsed.metadata.get("date", ""))),
            "output": rel_url,
            **locs,
            **escaped_meta,
        }
        #print(context) # RM
        output_path.write_text(render_template(template_text, context), encoding="utf-8")
        built += 1

    for asset in src_dir.rglob("*"):
        if not asset.is_file() or asset.suffix.lower() == ".md":
            continue
        destination = out_dir / asset.relative_to(src_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(asset.read_bytes())

    run_plugins(src_dir, out_dir, config)
    build_combined_rss_feed(out_dir, str(config.get("site_url", "https://flench.me")))
    return built


def run_plugins(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
    plugins = config.get("plugins", [])
    if not isinstance(plugins, list):
        return

    for plugin_name in plugins:
        if not isinstance(plugin_name, str) or not plugin_name.strip():
            continue
        module = importlib.import_module(plugin_name)
        main = getattr(module, "main", None)
        if callable(main):
            main(src_dir, out_dir, config)


def _is_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def build_combined_rss_feed(out_dir: Path, site_url: str) -> bool:
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


def _simple_yaml_parse(raw: str) -> dict[str, Any]:
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
    data = dict(DEFAULT_CONFIG)
    if not config_path.exists():
        return data

    raw = config_path.read_text(encoding="utf-8")
    if yaml is not None:
        loaded = yaml.safe_load(raw) or {}
    else:
        loaded = _simple_yaml_parse(raw)

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


def _save_webmention_state(state: dict[str, Any]) -> None:
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def queue_bridgy_webping_for_notes(src_dir: Path, out_dir: Path, site_url: str) -> int:
    site_url_clean = site_url.rstrip("/")
    notes_dir = src_dir / "notes"
    if not notes_dir.exists() or not site_url_clean:
        return 0

    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]

    existing = {
        (str(item.get("source", "")).strip(), str(item.get("target", "")).strip())
        for item in [*queue, *published]
    }

    queued_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added = 0

    for md_file in sorted(notes_dir.rglob("*.md")):
        output_path = clean_output_path(md_file, src_dir, out_dir)
        rel_url = "/" + output_path.relative_to(out_dir).as_posix()
        if rel_url.endswith("/index.html"):
            rel_url = rel_url[: -len("index.html")]
        source = f"{site_url_clean}{rel_url}"
        key = (source, FED_BRIDGY_ENDPOINT)
        if key in existing:
            continue
        queue.append({"source": source, "target": FED_BRIDGY_ENDPOINT, "queued_at": queued_at})
        existing.add(key)
        added += 1

    state["queue"] = queue
    _save_webmention_state(state)
    return added


def publish_webmentions(dry_run: bool = False) -> tuple[int, int]:
    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]

    sent = 0
    failed = 0
    remaining: list[dict[str, Any]] = []

    for item in queue:
        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        if not source or not target:
            continue

        if dry_run:
            print(f"DRY RUN publish {source} -> {target}")
            remaining.append(item)
            continue

        payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
        request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(request, timeout=15):
                sent += 1
                published.append(
                    {
                        **item,
                        "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    }
                )
        except urllib.error.URLError as exc:
            failed += 1
            remaining.append(item)
            print(f"Failed publishing {source} -> {target}: {exc}")

    state["queue"] = remaining
    state["published"] = published
    _save_webmention_state(state)
    return sent, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static site with clean URLs and plugins")
    parser.add_argument("command", nargs="?", default="build", choices=["build", "publish"])
    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--dry-run", action="store_true", help="Print publish actions without sending webmentions")
    args = parser.parse_args()

    if args.command == "publish":
        sent, failed = publish_webmentions(dry_run=args.dry_run)
        print(f"Published {sent} webmention(s); {failed} failed")
        return

    config = load_config(Path(args.config))
    src_dir = Path(str(config.get("src_dir", "src")))
    out_dir = Path(str(config.get("out_dir", "dist")))
    template_path = Path(str(config.get("default_template", "src/page.html.temp")))

    built = build_site(src_dir, out_dir, template_path, config)
    queued = queue_bridgy_webping_for_notes(src_dir, out_dir, str(config.get("site_url", "https://flench.me")))
    print(f"Built {built} markdown page(s)")
    if queued:
        print(f"Queued {queued} Bridgy Fed webping(s)")


if __name__ == "__main__":
    main()

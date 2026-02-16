#!/usr/bin/env python3
"""Simple markdown-to-HTML builder.

Usage:
  python build.py
  python build.py --src src --out dist --template src/page.html.temp

The builder scans for Markdown files in the source directory and writes
matching .html files to the output directory using the provided template.

It supports YAML front matter at the top of each markdown file:

  ---
  template: src/page.html.temp
  title: My Page Title
  page_name: my-page
  output: custom-name.html
  ---

It also supports block directives inside markdown files:

  heading:::element_id---location

Any directive part can be empty via {}.
Blocks are rendered into matching template placeholders such as
{{ content }}, {{ sidebar }}, {{ nav bar }}.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import shutil
import sys
from dataclasses import dataclass
import html
from email.utils import format_datetime
from urllib import parse as urlparse
from urllib import request as urlrequest
import re
from pathlib import Path
import venv
import xml.etree.ElementTree as ET

try:
    import markdown as md_lib  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    md_lib = None

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _is_running_in_venv() -> bool:
    return bool(os.environ.get("VIRTUAL_ENV")) or sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _load_requirements(root_dir: Path) -> list[str]:
    requirement_files = [root_dir / "requirements.txt", root_dir / "requirements-dev.txt"]
    packages: list[str] = []
    for requirement_file in requirement_files:
        if not requirement_file.exists():
            continue
        for line in requirement_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            packages.append(stripped)
    if packages:
        return packages

    # Fallback to known optional dependencies used by this script.
    return ["markdown", "PyYAML"]


def ensure_local_venv(root_dir: Path) -> None:
    if _is_running_in_venv():
        return

    venv_dir = root_dir / ".venv"
    created_venv = False
    if not venv_dir.exists():
        print(f"Creating virtual environment at {venv_dir}")
        venv.create(venv_dir, with_pip=True)
        created_venv = True

    bin_dir = "Scripts" if os.name == "nt" else "bin"
    python_path = venv_dir / bin_dir / ("python.exe" if os.name == "nt" else "python")
    if not python_path.exists():
        raise FileNotFoundError(f"Unable to locate venv python: {python_path}")

    packages = _load_requirements(root_dir) if created_venv else []
    if packages:
        print("Installing dependencies into .venv")
        try:
            subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
            subprocess.run([str(python_path), "-m", "pip", "install", *packages], check=True)
        except subprocess.CalledProcessError as exc:
            print(f"Dependency install failed, continuing with available packages: {exc}")

    print("Re-running build with local virtual environment")
    subprocess.run([str(python_path), *sys.argv], check=True)
    raise SystemExit(0)


def _fallback_markdown_to_html(markdown_text: str) -> str:
    """Tiny markdown converter for environments without python-markdown."""
    lines = markdown_text.splitlines()
    out: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line:
            close_list()
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            close_list()
            level = len(heading_match.group(1))
            text = html.escape(heading_match.group(2).strip())
            out.append(f"<h{level}>{text}</h{level}>")
            continue

        list_match = re.match(r"^[-*]\s+(.*)$", line)
        if list_match:
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = html.escape(list_match.group(1).strip())
            out.append(f"  <li>{item}</li>")
            continue

        close_list()
        paragraph = html.escape(line)
        paragraph = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", paragraph)
        paragraph = re.sub(r"\*(.+?)\*", r"<em>\1</em>", paragraph)
        out.append(f"<p>{paragraph}</p>")

    close_list()
    return "\n".join(out)


def markdown_to_html(markdown_text: str) -> str:
    if md_lib is not None:
        return md_lib.markdown(markdown_text, extensions=["extra", "sane_lists"])
    return _fallback_markdown_to_html(markdown_text)


@dataclass
class ContentBlock:
    heading: str | None
    element_id: str | None
    location: str
    markdown_body: str


@dataclass
class ParsedPage:
    metadata: dict[str, str]
    markdown_body: str


_BLOCK_DIRECTIVE = re.compile(r"^(.*?):::(.*?)---(.*?)$")


def _normalize_piece(value: str) -> str | None:
    trimmed = value.strip()
    if trimmed == "{}" or trimmed == "":
        return None
    return trimmed


def _simple_front_matter_parse(raw: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def parse_front_matter(markdown_text: str) -> ParsedPage:
    """Parse optional YAML front matter and return metadata + markdown body."""
    if not markdown_text.startswith("---\n"):
        return ParsedPage(metadata={}, markdown_body=markdown_text)

    end_match = re.search(r"\n---\s*(\n|$)", markdown_text[4:])
    if not end_match:
        return ParsedPage(metadata={}, markdown_body=markdown_text)

    end_idx = 4 + end_match.start()
    front_matter_raw = markdown_text[4:end_idx]

    # Skip closing marker and one trailing newline if present.
    body_start = 4 + end_match.end()
    body = markdown_text[body_start:]

    if yaml is not None:
        loaded = yaml.safe_load(front_matter_raw) or {}
        if not isinstance(loaded, dict):
            loaded = {}
        metadata = {str(k): str(v) for k, v in loaded.items()}
    else:
        metadata = _simple_front_matter_parse(front_matter_raw)

    return ParsedPage(metadata=metadata, markdown_body=body)


def parse_markdown_blocks(markdown_text: str) -> list[ContentBlock]:
    blocks: list[ContentBlock] = []
    current_heading: str | None = None
    current_id: str | None = None
    current_location = "content"
    current_lines: list[str] = []

    def flush_current() -> None:
        if not current_lines and current_heading is None and current_id is None:
            return
        blocks.append(
            ContentBlock(
                heading=current_heading,
                element_id=current_id,
                location=current_location,
                markdown_body="\n".join(current_lines).strip(),
            )
        )

    for raw_line in markdown_text.splitlines():
        match = _BLOCK_DIRECTIVE.match(raw_line.strip())
        if match:
            flush_current()
            current_heading = _normalize_piece(match.group(1))
            current_id = _normalize_piece(match.group(2))
            current_location = _normalize_piece(match.group(3)) or "content"
            current_lines = []
            continue

        current_lines.append(raw_line)

    flush_current()

    if not blocks:
        blocks.append(
            ContentBlock(
                heading=None,
                element_id=None,
                location="content",
                markdown_body=markdown_text,
            )
        )

    return blocks


def _render_block_html(block: ContentBlock) -> str:
    parts: list[str] = []
    if block.heading:
        parts.append(f"<h2>{html.escape(block.heading)}</h2>")
    if block.markdown_body:
        parts.append(markdown_to_html(block.markdown_body))

    joined = "\n".join(part for part in parts if part.strip()).strip()
    if block.element_id:
        return f'<div id="{html.escape(block.element_id)}">{joined}</div>'
    return joined


def _combine_locations(blocks: list[ContentBlock]) -> dict[str, str]:
    rendered_by_location: dict[str, list[str]] = {}
    for block in blocks:
        rendered = _render_block_html(block)
        if not rendered:
            continue
        rendered_by_location.setdefault(block.location, []).append(rendered)
    return {k: "\n".join(v) for k, v in rendered_by_location.items()}


def render(template_text: str, context: dict[str, str]) -> str:
    def replace_placeholder(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return context.get(key, "")

    return re.sub(r"{{\s*([^{}]+?)\s*}}", replace_placeholder, template_text)


def derive_title(md_path: Path, metadata: dict[str, str], markdown_body: str) -> str:
    if metadata.get("title"):
        return metadata["title"]
    if metadata.get("page_name"):
        return metadata["page_name"]

    for line in markdown_body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return md_path.stem.replace("-", " ").title()


def resolve_template_path(template_value: str | None, md_file: Path, default_template: Path) -> Path:
    if not template_value:
        return default_template

    candidate = Path(template_value)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    relative_to_md = md_file.parent / candidate
    if relative_to_md.exists():
        return relative_to_md

    relative_to_cwd = Path.cwd() / candidate
    if relative_to_cwd.exists():
        return relative_to_cwd

    # Fallback to value as provided; caller will raise if not found.
    return candidate


def output_filename(md_file: Path, metadata: dict[str, str]) -> str:
    explicit_output = metadata.get("output")
    if explicit_output:
        return explicit_output

    page_name = metadata.get("page_name")
    if page_name:
        cleaned = page_name.strip().replace(" ", "-")
        if cleaned.endswith(".html"):
            return cleaned
        return f"{cleaned}.html"

    return f"{md_file.stem}.html"


def extract_target_urls(markdown_body: str) -> list[str]:
    found = re.findall(r"https?://[^\s)>'\"]+", markdown_body)
    # Preserve order and drop duplicates.
    unique: list[str] = []
    seen: set[str] = set()
    for url in found:
        if url in seen:
            continue
        seen.add(url)
        unique.append(url)
    return unique


DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ title }}</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <div class="page-wrap">
      <header class="marquee-frame">
        <marquee behavior="alternate" scrollamount="6">
          ★ Welcome to Retro Pixel Palace ★ Midnight Edition ★
        </marquee>
      </header>

      <nav class="top-nav panel">{{ nav bar }}</nav>

      <main class="layout">
        <section class="content panel">{{ content }}</section>
      </main>

      <footer class="panel footer">
        <p>© 2001 Retro Pixel Palace — E-mail: webmaster@pixelpalace.example</p>
      </footer>
    </div>
  </body>
</html>
"""
DEFAULT_TEMPLATE_PATH = Path("src/page.html.temp")
WEBPING_STATE_FILE = Path(__file__).with_name(".webping-state.json")


def _load_webping_state(state_path: Path) -> dict[str, list[str]]:
    if not state_path.exists():
        return {}
    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, value in loaded.items():
        if isinstance(key, str) and isinstance(value, list):
            result[key] = [str(item) for item in value]
    return result


def _save_webping_state(state_path: Path, state: dict[str, list[str]]) -> None:
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _discover_webmention_endpoint(target_url: str) -> str | None:
    req = urlrequest.Request(target_url, headers={"User-Agent": "fleench-builder/1.0"})
    with urlrequest.urlopen(req, timeout=8) as response:
        link_header = response.headers.get("Link", "")
        header_match = re.search(r'<([^>]+)>\s*;\s*rel="?webmention"?', link_header, flags=re.IGNORECASE)
        if header_match:
            return urlparse.urljoin(target_url, header_match.group(1))

        body = response.read(50_000).decode("utf-8", errors="ignore")

    body_match = re.search(
        r'<link[^>]+rel=["\'][^"\']*webmention[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
        body,
        flags=re.IGNORECASE,
    )
    if body_match:
        return urlparse.urljoin(target_url, body_match.group(1))

    alt_match = re.search(
        r'<a[^>]+rel=["\'][^"\']*webmention[^"\']*["\'][^>]+href=["\']([^"\']+)["\']',
        body,
        flags=re.IGNORECASE,
    )
    if alt_match:
        return urlparse.urljoin(target_url, alt_match.group(1))

    return None


def _send_webmention(source_url: str, target_url: str) -> bool:
    try:
        endpoint = _discover_webmention_endpoint(target_url)
    except Exception as exc:
        print(f"Webping discovery failed for {target_url}: {exc}")
        return False

    if not endpoint:
        print(f"Webping skipped (no endpoint): {target_url}")
        return False

    payload = urlparse.urlencode({"source": source_url, "target": target_url}).encode("utf-8")
    req = urlrequest.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "fleench-builder/1.0",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(req, timeout=8) as response:
            status_code = getattr(response, "status", response.getcode())
            if status_code == 200:
                print(f"Webping sent: {source_url} -> {target_url}")
                return True
            print(f"Webping skipped for {target_url}: HTTP {status_code}")
            return False
    except Exception as exc:
        print(f"Webping failed for {target_url}: {exc}")
        return False


def _copy_static_assets(src_dir: Path, out_dir: Path) -> int:
    copied = 0
    for source_path in src_dir.rglob("*"):
        if not source_path.is_file():
            continue
        name_lower = source_path.name.lower()
        if name_lower.endswith(".html.temp") or name_lower.endswith(".md"):
            continue

        relative_path = source_path.relative_to(src_dir)
        destination_path = out_dir / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        copied += 1
        print(f"Copied: {destination_path}")

    return copied


def _simple_yaml_parse(raw: str) -> dict[str, object]:
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root

        if value == "":
            nested: dict[str, object] = {}
            parent[key] = nested
            stack.append((indent, nested))
            continue

        normalized = value.strip('"').strip("'")
        if normalized.lower() in {"true", "false"}:
            parent[key] = normalized.lower() == "true"
        else:
            parent[key] = normalized

    return root


def load_config(root_dir: Path) -> dict[str, object]:
    config_path = root_dir / "config.yml"
    if not config_path.exists():
        return {}

    raw = config_path.read_text(encoding="utf-8")
    if yaml is not None:
        loaded = yaml.safe_load(raw) or {}
        if isinstance(loaded, dict):
            return loaded
        return {}

    print("PyYAML not installed; using limited config parser")
    return _simple_yaml_parse(raw)


def _extract_post_date(md_path: Path, metadata: dict[str, str]) -> dt.datetime:
    for key in ("date", "published", "pub_date"):
        value = metadata.get(key)
        if not value:
            continue
        cleaned = value.strip()
        try:
            parsed = dt.datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed
        except ValueError:
            pass

    filename_match = re.match(r"(\d{4}-\d{2}-\d{2})", md_path.stem)
    if filename_match:
        parsed = dt.datetime.fromisoformat(filename_match.group(1))
        return parsed.replace(tzinfo=dt.timezone.utc)

    modified = dt.datetime.fromtimestamp(md_path.stat().st_mtime, tz=dt.timezone.utc)
    return modified


def _extract_description(markdown_body: str) -> str:
    for line in markdown_body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        return stripped[:240]
    return ""


def _generate_rss_feed(src_dir: Path, out_dir: Path, site_url: str, config: dict[str, object]) -> Path | None:
    rss_config = config.get("rss")
    if not isinstance(rss_config, dict) or not _is_truthy(rss_config.get("enabled", False)):
        return None

    content_dir_name = str(rss_config.get("content_dir", "blog"))
    feed_path = str(rss_config.get("feed_path", "feed.xml"))
    content_dir = src_dir / content_dir_name
    if not content_dir.exists():
        print(f"RSS skipped: content directory not found ({content_dir})")
        return None

    entries: list[tuple[dt.datetime, Path, ParsedPage]] = []
    for md_path in sorted(content_dir.rglob("*.md")):
        raw_text = md_path.read_text(encoding="utf-8")
        parsed = parse_front_matter(raw_text)
        published = _extract_post_date(md_path, parsed.metadata)
        entries.append((published, md_path, parsed))

    if not entries:
        print(f"RSS skipped: no markdown files in {content_dir}")
        return None

    entries.sort(key=lambda item: item[0], reverse=True)
    now = dt.datetime.now(tz=dt.timezone.utc)

    rss_el = ET.Element("rss", attrib={"version": "2.0"})
    channel = ET.SubElement(rss_el, "channel")
    ET.SubElement(channel, "title").text = str(config.get("site_title") or site_url)
    ET.SubElement(channel, "link").text = site_url.rstrip("/") + "/"
    ET.SubElement(channel, "description").text = str(config.get("site_title") or "Site feed")
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(now)

    for published, md_path, parsed in entries:
        item = ET.SubElement(channel, "item")
        title = derive_title(md_path, parsed.metadata, parsed.markdown_body)
        rel_path = md_path.relative_to(src_dir).with_suffix(".html")
        link = urlparse.urljoin(site_url.rstrip("/") + "/", str(rel_path).replace("\\", "/"))
        description = parsed.metadata.get("description") or _extract_description(parsed.markdown_body)

        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = link
        ET.SubElement(item, "pubDate").text = format_datetime(
            published if published.tzinfo else published.replace(tzinfo=dt.timezone.utc)
        )
        ET.SubElement(item, "description").text = description

    output_path = out_dir / feed_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(rss_el)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Generated RSS: {output_path}")
    return output_path


def build(
    src_dir: Path,
    out_dir: Path,
    template_path: Path | None,
    site_url: str | None,
    config: dict[str, object] | None = None,
) -> int:
    config = config or {}
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    template_text_default = DEFAULT_TEMPLATE
    resolved_default_template = template_path
    if resolved_default_template is None and DEFAULT_TEMPLATE_PATH.exists():
        resolved_default_template = DEFAULT_TEMPLATE_PATH

    if resolved_default_template is not None:
        if not resolved_default_template.exists():
            raise FileNotFoundError(f"Template not found: {resolved_default_template}")
        template_text_default = resolved_default_template.read_text(encoding="utf-8")

    markdown_files = sorted(src_dir.glob("*.md"))

    out_dir.mkdir(parents=True, exist_ok=True)
    copied_assets = _copy_static_assets(src_dir, out_dir)
    webping_state_path = WEBPING_STATE_FILE
    webping_state = _load_webping_state(webping_state_path)

    built = 0
    for md_file in markdown_files:
        file_key = str(md_file.relative_to(src_dir))
        raw_text = md_file.read_text(encoding="utf-8")
        parsed = parse_front_matter(raw_text)

        template_text = template_text_default
        selected_template_value = parsed.metadata.get("template")
        if selected_template_value:
            selected_template = resolve_template_path(selected_template_value, md_file, Path.cwd())
            if not selected_template.exists():
                raise FileNotFoundError(f"Template not found: {selected_template}")
            template_text = selected_template.read_text(encoding="utf-8")

        blocks = parse_markdown_blocks(parsed.markdown_body)
        locations = _combine_locations(blocks)
        title = derive_title(md_file, parsed.metadata, parsed.markdown_body)

        escaped_meta = {k: html.escape(v) for k, v in parsed.metadata.items()}
        context = {"title": html.escape(title), **escaped_meta, **locations}
        full_html = render(template_text, context)

        output_name = output_filename(md_file, parsed.metadata)
        output_path = out_dir / output_name
        was_fresh_build = not output_path.exists()
        output_path.write_text(full_html, encoding="utf-8")
        built += 1
        print(f"Built: {output_path}")

        page_urls = extract_target_urls(parsed.markdown_body)
        previous_urls = webping_state.get(file_key, [])
        should_send_webpings = was_fresh_build or not previous_urls

        if should_send_webpings and page_urls:
            previous_set = set(previous_urls)
            successful_urls: list[str] = [url for url in page_urls if url in previous_set]
            if site_url:
                source_url = urlparse.urljoin(site_url.rstrip("/") + "/", output_name)
                for target_url in page_urls:
                    if target_url in previous_set:
                        continue
                    if _send_webmention(source_url, target_url):
                        successful_urls.append(target_url)
            else:
                print(f"Skipping webpings for {md_file.name}: --site-url is required")
            webping_state[file_key] = successful_urls
        else:
            webping_state[file_key] = [url for url in previous_urls if url in page_urls]

    if built == 0:
        print(f"No markdown files found in {src_dir}")
    if copied_assets == 0:
        print(f"No static assets copied from {src_dir}")

    if site_url:
        _generate_rss_feed(src_dir, out_dir, site_url, config)
    elif config.get("rss"):
        print("Skipping RSS generation: site_url is required")

    _save_webping_state(webping_state_path, webping_state)
    return built


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build HTML files from Markdown files")
    parser.add_argument("--src", default="src", help="Directory containing .md source files")
    parser.add_argument("--out", default="dist", help="Directory for generated .html files")
    parser.add_argument(
        "--template",
        default=None,
        help="Default template file (can be overridden in markdown front matter)",
    )
    parser.add_argument(
        "--site-url",
        default=None,
        help="Public base URL used as source URL when sending webpings",
    )
    return parser.parse_args()


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    ensure_local_venv(root_dir)

    args = parse_args()
    config = load_config(root_dir)
    config_site_url = config.get("site_url") if isinstance(config, dict) else None
    chosen_site_url = args.site_url or (str(config_site_url) if config_site_url else None)

    build(
        Path(args.src),
        Path(args.out),
        Path(args.template) if args.template else None,
        chosen_site_url,
        config,
    )


if __name__ == "__main__":
    main()

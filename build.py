#!/usr/bin/env python3
"""Simple markdown-to-HTML builder.

Usage:
  python build.py
  python build.py --src src --out dist --template src/page.html.temp

The builder scans for Markdown files in the source directory and writes
matching .html files to the output directory using the provided template.

It also supports block directives inside markdown files:

  heading:::element_id---location

Any part can be empty by using {}. Examples:
  Welcome:::intro---content
  {}:::news---sidebar
  Menu:::{}---nav bar

Each directive starts a new block. Following markdown lines belong to that
block until the next directive. Blocks are rendered into their target location
placeholder in the template, e.g. {{ content }}, {{ sidebar }}, {{ nav bar }}.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
import re
from pathlib import Path

try:
    import markdown as md_lib  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    md_lib = None


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


_BLOCK_DIRECTIVE = re.compile(r"^(.*?):::(.*?)---(.*?)$")


def _normalize_piece(value: str) -> str | None:
    trimmed = value.strip()
    if trimmed == "{}" or trimmed == "":
        return None
    return trimmed


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


def render(template_text: str, title: str, locations: dict[str, str]) -> str:
    context = {"title": html.escape(title), **locations}

    def replace_placeholder(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return context.get(key, "")

    return re.sub(r"{{\s*([^{}]+?)\s*}}", replace_placeholder, template_text)


def derive_title(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return md_path.stem.replace("-", " ").title()


def build(src_dir: Path, out_dir: Path, template_path: Path) -> int:
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    markdown_files = sorted(src_dir.glob("*.md"))

    out_dir.mkdir(parents=True, exist_ok=True)

    built = 0
    for md_file in markdown_files:
        markdown_text = md_file.read_text(encoding="utf-8")
        blocks = parse_markdown_blocks(markdown_text)
        locations = _combine_locations(blocks)
        title = derive_title(md_file)
        full_html = render(template_text, title, locations)

        output_name = f"{md_file.stem}.html"
        output_path = out_dir / output_name
        output_path.write_text(full_html, encoding="utf-8")
        built += 1
        print(f"Built: {output_path}")

    if built == 0:
        print(f"No markdown files found in {src_dir}")

    return built


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build HTML files from Markdown files")
    parser.add_argument("--src", default="src", help="Directory containing .md source files")
    parser.add_argument("--out", default="dist", help="Directory for generated .html files")
    parser.add_argument(
        "--template",
        default="src/page.html.temp",
        help="Template file with {{ title }} and {{ content }} placeholders",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build(Path(args.src), Path(args.out), Path(args.template))


if __name__ == "__main__":
    main()

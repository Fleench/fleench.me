from __future__ import annotations

import html
import re
import datetime as dt
from pathlib import Path
from typing import Any, Tuple

try:
    import markdown as md_lib  # type: ignore
except Exception:
    md_lib = None

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def _parse_frontmatter(raw: str) -> Tuple[dict[str, Any], str]:
    if not raw.startswith("---\n"):
        return {}, raw

    marker = "\n---\n"
    end = raw.find(marker, 4)

    if end == -1:
        return {}, raw

    header = raw[4:end]
    body = raw[end + len(marker):]

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

    return "\n".join(
        f"<p>{html.escape(line)}</p>"
        for line in text.splitlines()
        if line.strip()
    )


def _first_paragraph(text: str) -> str:
    paragraphs = re.split(r"\n\s*\n", text.strip())

    for p in paragraphs:
        stripped = p.strip()
        if stripped:
            return stripped

    return ""


def _date_from_slug(path: Path, src_dir: Path) -> str:
    rel = path.relative_to(src_dir)
    parts = rel.parts

    # Expecting: blogs/YYYY/MM/DD.md
    if len(parts) >= 4:
        try:
            year = int(parts[1])
            month = int(parts[2])
            day = int(Path(parts[3]).stem)

            d = dt.date(year, month, day)
            return d.strftime("%B %d, %Y")
        except Exception:
            pass

    return ""


def _permalink_from_path(path: Path, src_dir: Path) -> str:
    relative = path.relative_to(src_dir).with_suffix("")
    return f"/{relative.as_posix()}/"


def _blog_preview(metadata: dict[str, Any], body: str, permalink: str, date: str) -> str:
    title = html.escape(str(metadata.get("title", "Untitled")))

    img = metadata.get("img")
    img_alt = html.escape(str(metadata.get("img-alt", "")))

    excerpt = _first_paragraph(body)
    excerpt_html = _markdown(excerpt)

    parts: list[str] = ['<article class="blog-preview panel">']

    # Title
    parts.append(f'<h2 class="blog-title"><a href="{permalink}">{title}</a></h2>')

    # Date beneath title
    if date:
        parts.append(f'<div class="blog-date"><small>{html.escape(date)}</small></div>')

    # Image below title/date
    if img:
        parts.append(
            f'<a href="{permalink}" class="blog-cover">'
            f'<img src="{html.escape(str(img))}" alt="{img_alt}">'
            '</a>'
        )

    # Excerpt paragraph
    parts.append(f'<div class="blog-excerpt">{excerpt_html}</div>')

    parts.append("</article>")

    return "\n".join(parts)


def generate_blog_index(project_root: Path) -> str:
    src_dir = project_root / "src"
    blog_dir = src_dir / "blogs"

    posts = sorted(blog_dir.rglob("*.md"), reverse=True) if blog_dir.exists() else []

    rendered: list[str] = []

    for post_file in posts:
        raw = post_file.read_text(encoding="utf-8")
        metadata, body = _parse_frontmatter(raw)

        permalink = _permalink_from_path(post_file, src_dir)
        if pdate:=metadata.get("date","") != "":
            date = _date_from_slug(post_file, src_dir)
        else:
            date = pdate.split("-")
            d = dt.date(date[0], date[1], date[2])
            date = d.strftime("%B %d, %Y")

        preview = _blog_preview(metadata, body, permalink, date)
        rendered.append(preview)

    return "\n".join(rendered)


def main(**context) -> str:
    project_root = context.get("project_root", Path.cwd())
    return generate_blog_index(project_root)


if __name__ == "__main__":
    print(generate_blog_index(Path.cwd()))

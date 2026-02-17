from __future__ import annotations

import html
from pathlib import Path
from typing import Any

try:
    import markdown as md_lib  # type: ignore
except Exception:
    md_lib = None

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


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


def main(src_dir: Path, out_dir: Path, config: dict[str, Any]) -> None:
    notes_dir = src_dir / "notes"
    if not notes_dir.exists():
        return

    notes = sorted(notes_dir.rglob("*.md"), reverse=True)
    rendered: list[str] = []
    for note_file in notes:
        metadata, body = _parse_frontmatter(note_file.read_text(encoding="utf-8"))
        relative = note_file.relative_to(src_dir).with_suffix("").as_posix()
        permalink = f"/{relative}/"
        note_type = html.escape(str(metadata.get("type", "note")))
        date_text = html.escape(str(metadata.get("date", "")))
        rendered.append(
            "\n".join(
                [
                    '<article class="note-item h-entry">',
                    f'  <a class="u-url note-permalink" href="{permalink}">Permalink</a>',
                    f'  <div class="note-meta">{note_type} • {date_text}</div>',
                    f'  <div class="e-content">{_markdown(body)}</div>',
                    "</article>",
                ]
            )
        )

    output = out_dir / "notes" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(
            [
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="UTF-8">',
                '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                "  <title>Notes</title>",
                '  <link rel="stylesheet" href="/style.css">',
                "</head>",
                "<body>",
                "  <main>",
                "    <h1>Notes</h1>",
                *[f"    {item}" for item in rendered],
                "  </main>",
                "</body>",
                "</html>",
            ]
        ),
        encoding="utf-8",
    )

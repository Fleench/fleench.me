#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import importlib
import re
from dataclasses import dataclass
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

DEFAULT_CONFIG: dict[str, Any] = {
    "src_dir": "src",
    "out_dir": "dist",
    "default_template": "src/page.html.temp",
    "plugins": [],
}


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

    # fallback minimal markdown rendering
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


def render_template(template_text: str, context: dict[str, Any]) -> str:
    rendered = template_text
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
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
        parsed = parse_frontmatter(md_file.read_text(encoding="utf-8"))

        selected_template = parsed.metadata.get("template")
        template_path = Path(str(selected_template)) if selected_template else default_template
        if not template_path.is_absolute():
            template_path = Path.cwd() / template_path
        template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else default_template_text

        body_html = markdown_to_html(parsed.body)
        output_path = clean_output_path(md_file, src_dir, out_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rel_url = "/" + output_path.relative_to(out_dir).as_posix()
        if rel_url.endswith("/index.html"):
            rel_url = rel_url[: -len("index.html")]

        escaped_meta = {k: html.escape(str(v)) for k, v in parsed.metadata.items()}
        context = {
            "title": html.escape(derive_title(md_file, parsed)),
            "content": body_html,
            "date": html.escape(str(parsed.metadata.get("date", ""))),
            "output": rel_url,
            **escaped_meta,
        }
        output_path.write_text(render_template(template_text, context), encoding="utf-8")
        built += 1

    for asset in src_dir.rglob("*"):
        if not asset.is_file() or asset.suffix.lower() == ".md":
            continue
        destination = out_dir / asset.relative_to(src_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(asset.read_bytes())

    run_plugins(src_dir, out_dir, config)
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




def _simple_yaml_parse(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.startswith('- ') and current_list_key:
            data.setdefault(current_list_key, []).append(stripped[2:].strip().strip('"').strip("'"))
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if value == '':
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
        data.update(loaded)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static site with clean URLs and plugins")
    parser.add_argument("command", nargs="?", default="build", choices=["build"])
    parser.add_argument("--config", default="config.yml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    src_dir = Path(str(config.get("src_dir", "src")))
    out_dir = Path(str(config.get("out_dir", "dist")))
    template_path = Path(str(config.get("default_template", "src/page.html.temp")))

    built = build_site(src_dir, out_dir, template_path, config)
    print(f"Built {built} markdown page(s)")


if __name__ == "__main__":
    main()

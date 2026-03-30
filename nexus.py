#!/usr/bin/env python3
# pylint: disable=C0301,E0401,E1102,W0718,C0303,C0103
"""
Author: Flench04
Date: 3/7/2026
Description: A python3 based static site generator
"""
from __future__ import annotations

import argparse
import csv
import html
import importlib
import importlib.util
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

try:
    import markdown as MD_LIB  # type: ignore
except Exception:
    MD_LIB = None
    print("No MD_LIB found")
try:
    import YAML  # type: ignore
except Exception:
    YAML = None

DEFAULT_CONFIG: dict[str, Any] = {
    "src_dir": "src",
    "out_dir": "dist",
    "default_template": "src/page.html.temp",
    "plugins": [],
    "site_url": "https://flench.me",
    "rss": False,
    "cmds": {},
}
LOGGER = logging.getLogger("gen")
FEATURE_DOC_PATH = Path(__file__).with_name("nexus_features.md")


@dataclass
class ParsedMarkdown:
    metadata: dict[str, Any]
    body: str


@dataclass
class PluginDefinition:
    """Normalized plugin definition loaded from configuration."""

    name: str
    module_path: str
    api_exports: list[str]


def parse_frontmatter(raw: str) -> ParsedMarkdown:
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
    level = getattr(logging, level_name.upper(), logging.INFO)
    if json_logs:
        class JsonFormatter(logging.Formatter):
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


def _normalize_plugins(config: dict[str, Any]) -> list[PluginDefinition]:
    plugins = config.get("plugins", [])
    if not isinstance(plugins, list):
        return []

    normalized: list[PluginDefinition] = []
    for plugin in plugins:
        if isinstance(plugin, str):
            module_path = plugin.strip()
            if not module_path:
                continue
            normalized.append(
                PluginDefinition(
                    name=module_path.split(".")[-1],
                    module_path=module_path,
                    api_exports=[],
                )
            )
            continue

        if isinstance(plugin, dict):
            raw_name = str(plugin.get("name", "")).strip()
            raw_script = str(plugin.get("script", "")).strip()
            name = raw_name or raw_script.rsplit("/", 1)[-1].replace(".py", "")
            if not name:
                continue
            module_path = raw_script.replace("/", ".").replace(".py", "")
            if not module_path and raw_name:
                module_path = raw_name
            exports = plugin.get("api_exports", [])
            api_exports = [str(item).strip() for item in exports if str(item).strip()] if isinstance(exports, list) else []
            normalized.append(
                PluginDefinition(
                    name=name,
                    module_path=module_path,
                    api_exports=api_exports,
                )
            )
    return normalized


def _load_plugin_module(plugin: PluginDefinition) -> ModuleType:
    if not plugin.module_path:
        raise ImportError(f"Failed to load plugin '{plugin.name}': missing script/module path")
    try:
        return importlib.import_module(plugin.module_path)
    except Exception as exc:
        raise ImportError(f"Failed to load plugin '{plugin.name}': {exc}") from exc


def build_api(config: dict[str, Any]) -> tuple[dict[str, dict[str, Callable[..., Any]]], dict[str, ModuleType]]:
    """
    Build a filtered plugin API map before rendering pages.

    The API map is the single source of truth for plugin-to-plugin communication and
    dynamic element access. It is built once and then passed through render context.
    """

    plugin_defs = _normalize_plugins(config)
    module_registry: dict[str, ModuleType] = {}
    exported_lookup: dict[str, dict[str, Callable[..., Any]]] = {}

    for plugin in plugin_defs:
        module = _load_plugin_module(plugin)
        module_registry[plugin.name] = module
        available_exports = plugin.api_exports or list(getattr(module, "__api_exports__", []))
        if not isinstance(available_exports, list):
            available_exports = []
        exported_lookup[plugin.name] = {}
        for function_name in available_exports:
            attr = getattr(module, str(function_name), None)
            if attr is None:
                raise AttributeError(f"Function '{function_name}' not found in plugin '{plugin.name}'")
            if not callable(attr):
                raise TypeError(f"API function '{plugin.name}.{function_name}' is not callable")
            exported_lookup[plugin.name][str(function_name)] = attr

    available_functions = config.get("api_config", {}).get("available_functions", []) if isinstance(config.get("api_config"), dict) else []
    if not available_functions:
        return ({}, module_registry)
    if not isinstance(available_functions, list):
        raise TypeError("api_config.available_functions must be a list")

    # Basic acyclic validation: detect direct self references in configured identifiers.
    for identifier in available_functions:
        entry = str(identifier).strip()
        if not entry:
            continue
        plugin_name, _, function_name = entry.partition(".")
        if plugin_name == function_name:
            raise ValueError("Circular dependency detected in API configuration")

    api: dict[str, dict[str, Callable[..., Any]]] = {}
    for identifier in available_functions:
        entry = str(identifier).strip()
        if not entry:
            continue
        plugin_name, sep, function_name = entry.partition(".")
        if not sep or not function_name:
            raise ValueError(f"Invalid API function reference '{entry}', expected plugin.function")
        if plugin_name not in exported_lookup:
            raise ValueError(f"Plugin '{plugin_name}' not found in configuration")
        if function_name not in exported_lookup[plugin_name]:
            raise ValueError(f"API function '{plugin_name}.{function_name}' requested but not in api_config.available_functions")
        api.setdefault(plugin_name, {})[function_name] = exported_lookup[plugin_name][function_name]

    return api, module_registry


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
        return str(e)

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
                return str(e)
        except Exception as e:
            return str(e)
    else:
        rendered = getattr(module, "HTML", "")

    if rendered is None:
        return "Error"
    return str(rendered)


def _parse_dynamic_args(raw_args: str) -> list[Any]:
    stripped = raw_args.strip()
    if not stripped:
        return []
    try:
        tokens = next(csv.reader([stripped], skipinitialspace=True, escapechar="\\"))
    except Exception:
        tokens = [part.strip() for part in stripped.split(",")]
    parsed: list[Any] = []
    for token in tokens:
        value = token.strip()
        if not value:
            continue
        if YAML is not None:
            try:
                parsed.append(YAML.safe_load(value))
                continue
            except Exception:
                pass
        parsed.append(value)
    return parsed


def _find_dynamic_match(template_text: str, start_idx: int = 0) -> tuple[int, int, str, str] | None:
    marker_start = template_text.find(":{", start_idx)
    if marker_start == -1:
        return None

    path_start = marker_start + 2
    path_end = template_text.find("}:", path_start)
    if path_end == -1:
        return None

    raw_path = template_text[path_start:path_end].strip()
    if not raw_path.endswith(".py"):
        return _find_dynamic_match(template_text, marker_start + 2)

    args_start = path_end + 2
    if args_start >= len(template_text) or template_text[args_start] != "(":
        return (marker_start, args_start, raw_path, "")

    depth = 0
    quote_char: str | None = None
    escaped = False
    i = args_start

    while i < len(template_text):
        char = template_text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if char == "\\":
            escaped = True
            i += 1
            continue
        if quote_char:
            if char == quote_char:
                quote_char = None
            i += 1
            continue
        if char in ("'", '"'):
            quote_char = char
            i += 1
            continue
        if char == "(":
            depth += 1
            i += 1
            continue
        if char == ")":
            depth -= 1
            i += 1
            if depth == 0:
                return (marker_start, i, raw_path, template_text[args_start + 1 : i - 1])
            continue
        i += 1

    return None


def _replace_dynamic_elements(template_text: str, template_path: Path, context: dict[str, Any]) -> str:
    rendered_parts: list[str] = []
    cursor = 0
    search_from = 0
    replaced_any = False

    while True:
        found = _find_dynamic_match(template_text, search_from)
        if found is None:
            break
        start, end, raw_path, raw_args = found
        rendered_parts.append(template_text[cursor:start])
        element_args = _parse_dynamic_args(raw_args)
        path = _resolve_element_file(raw_path, template_path)
        if path is None:
            rendered_parts.append("")
        else:
            run_context = {
                "template_path": template_path,
                "project_root": Path.cwd(),
                "md": MD_LIB,
                **context,
                "args": element_args,
                "element_args": element_args,
            }
            rendered_parts.append(_run_dynamic_element(path, run_context))
        cursor = end
        search_from = end
        replaced_any = True

    if not replaced_any:
        return template_text
    rendered_parts.append(template_text[cursor:])
    return "".join(rendered_parts)


def inject_elements(template_text: str, template_path: Path, render_context: dict[str, Any] | None = None) -> str:
    static_pattern = re.compile(r"~\{([^{}]+)\}~")
    context = render_context or {}

    def replace_static(match: re.Match[str]) -> str:
        raw_path = match.group(1).strip()
        if not raw_path:
            return ""
        path = _resolve_element_file(raw_path, template_path)
        if path is not None:
            return path.read_text(encoding="utf-8")
        return ""
    rendered = template_text
    for _ in range(10):
        updated = static_pattern.sub(replace_static, rendered)
        updated = _replace_dynamic_elements(updated, template_path, context)
        if updated == rendered:
            return rendered
        rendered = updated
    return rendered


def render_template(template_text: str, context: dict[str, Any]) -> str:
    rendered = template_text
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
    rendered = re.sub(r"\{\{.*\}\}", "", rendered)
    return rendered


def clean_output_path(md_file: Path, src_dir: Path, out_dir: Path) -> Path:
    relative = md_file.relative_to(src_dir)
    if relative.as_posix() == "index.md":
        return out_dir / "index.html"
    page_dir = relative.with_suffix("")
    return out_dir / page_dir / "index.html"


class Page:
    """Worker object responsible for rendering one Markdown file."""

    def __init__(
        self,
        md_file: Path,
        src_dir: Path,
        out_dir: Path,
        config: dict[str, Any],
        default_template: Path,
        default_template_text: str,
        api: dict[str, dict[str, Callable[..., Any]]],
    ) -> None:
        self.md_file = md_file
        self.src_dir = src_dir
        self.out_dir = out_dir
        self.config = config
        self.default_template = default_template
        self.default_template_text = default_template_text
        self.api = api
        self.custom_template_set = False
        self.parsed = ParsedMarkdown({}, "")
        self.template_path = default_template
        self.template_text = default_template_text
        self.body = ""
        self.locs: dict[str, str] = {}
        self.output_path = Path()
        self.rel_url = ""
        self.canonical = ""
        self.rendered_html = ""
        self.opages = []

    def derive_title(self) -> str:
        explicit = self.parsed.metadata.get("title")
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip()
        if self.md_file.stem.lower() == "index":
            return "Home"
        return self.md_file.stem.replace("-", " ").replace("_", " ").title()

    def prep_template(self) -> None:
        self.parsed = parse_frontmatter(self.md_file.read_text(encoding="utf-8"))
        if self.custom_template_set:
            selected_template = self.template_path
        else:
            selected_template = self.parsed.metadata.get("template")
        if selected_template:
            template_path = Path(str(selected_template))
        elif self.md_file.is_relative_to(self.src_dir / "notes"):
            template_path = Path.cwd() / self.src_dir / "note.html.temp"
        else:
            template_path = self.default_template
        if not template_path.is_absolute():
            template_path = Path.cwd() / template_path
        self.template_path = template_path
        self.template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else self.default_template_text

    def parse_content(self) -> None:
        groups = self.parsed.body.split("\n# ")
        blocks = []
        for block in groups:
            lines = block.split("\n")
            if len(lines) > 1:
                blocks.append([lines[0], lines[1:]])
            else:
                blocks.append(["", lines[0]])
        locs: dict[str, str] = {}
        body = ""
        for block in blocks:
            parts = block[0].split("---")
            lef = ""
            rig = ""
            if len(parts) > 3 and parts[2] != "{}":
                lef = f"<div class={parts[2]} id={parts[3]}>"
                rig = "</div>"
            elif len(parts) > 3 and parts[2] == "{}":
                lef = f"<div  id={parts[3]}>"
                rig = "</div>"
            elif len(parts) > 2 and parts[2] != "{}":
                lef = f"<div class={parts[2]}>"
                rig = "</div>"
            if len(parts) > 1 and parts[1] != "{}":
                if "{}" not in parts[0]:
                    x = "# " + parts[0] + "\n" + "\n".join(block[1])
                else:
                    x = "\n".join(block[1])
                if parts[1] not in locs:
                    locs[parts[1]] = ""
                locs[parts[1]] += "\n" + lef + markdown_to_html(x) + rig
            else:
                if "{}" not in parts[0]:
                    x = "# " + parts[0] + "\n" + "\n".join(block[1])
                else:
                    x = "\n".join(block[1])
                body = body + (lef + markdown_to_html(x) + rig)
        self.body = body
        self.locs = locs

    def derive_path(self) -> None:
        self.output_path = clean_output_path(self.md_file, self.src_dir, self.out_dir)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.rel_url = "/" + self.output_path.relative_to(self.out_dir).as_posix()
        if self.rel_url.endswith("/index.html"):
            self.rel_url = self.rel_url[: -len("index.html")]
        site_url = str(self.config.get("site_url", "https://flench.me")).rstrip("/")
        self.canonical = f"{site_url}{self.rel_url}"

    def write(self) -> None:
        escaped_meta = {k: html.escape(str(v)) for k, v in self.parsed.metadata.items()}
        context = {
            "title": html.escape(self.derive_title()),
            "content": self.body,
            "date": html.escape(str(self.parsed.metadata.get("date", ""))),
            "output": self.rel_url,
            "canonical": html.escape(self.canonical),
            **self.locs,
            **escaped_meta,
        }
        self.template_text = inject_elements(
            self.template_text,
            self.template_path,
            render_context={
                "src_dir": self.src_dir,
                "out_dir": self.out_dir,
                "config": self.config,
                "api": self.api,
                "current_markdown": self.md_file,
                "opages": self.opages,
            },
        )
        self.rendered_html = render_template(self.template_text, context)
        self.output_path.write_text(self.rendered_html, encoding="utf-8")

    def render(self) -> "Page":
        self.prep_template()
        self.parse_content()
        self.derive_path()
        self.write()
        return self


def run_plugins(
    src_dir: Path,
    out_dir: Path,
    config: dict[str, Any],
    all_pages: list[Page],
    api: dict[str, dict[str, Callable[..., Any]]],
    module_registry: dict[str, ModuleType],
) -> None:
    for plugin_name, module in module_registry.items():
        plugin_main = getattr(module, "main", None)
        if callable(plugin_main):
            try:
                plugin_main(src_dir, out_dir, config, all_pages, api=api)
            except TypeError:
                try:
                    plugin_main(src_dir, out_dir, config, all_pages)
                except TypeError:
                    plugin_main(src_dir, out_dir, config)


def build_site(src_dir: Path, out_dir: Path, default_template: Path, config: dict[str, Any]) -> tuple[int, list[Page]]:
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    if not default_template.exists():
        raise FileNotFoundError(f"Default template not found: {default_template}")

    out_dir.mkdir(parents=True, exist_ok=True)
    default_template_text = default_template.read_text(encoding="utf-8")
    api, module_registry = build_api(config)
    config["API"] = api

    all_pages: list[Page] = []
    for md_file in sorted(src_dir.rglob("*.md")):
        LOGGER.debug("Rendering markdown file: %s", md_file)
        page = Page(md_file, src_dir, out_dir, config, default_template, default_template_text, api=api)
        all_pages.append(page)
    for page in all_pages:
        page.opages = all_pages
        page.render()

    for asset in src_dir.rglob("*"):
        skip = [".md", ".element", ".py", ".temp", ".bak"]
        if not asset.is_file() or asset.suffix.lower() in skip:
            continue
        destination = out_dir / asset.relative_to(src_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(asset.read_bytes())

    run_plugins(src_dir, out_dir, config, all_pages, api=api, module_registry=module_registry)
    return len(all_pages), all_pages


def _simple_YAML_parse(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_section: dict[str, Any] | None = None
    current_is_list = False

    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            current_section = None
            current_is_list = False
            if value == "":
                data[key] = {}
                current_section = data[key]
            else:
                data[key] = value.strip('"').strip("'")
            continue

        if indent > 0 and current_key:
            if stripped.startswith("- "):
                if not current_is_list:
                    data[current_key] = []
                    current_is_list = True
                    current_section = None
                data[current_key].append(stripped[2:].strip().strip('"').strip("'"))
                continue

            if ":" in stripped:
                if not isinstance(data.get(current_key), dict) or current_is_list:
                    data[current_key] = {}
                    current_is_list = False
                key, value = stripped.split(":", 1)
                data[current_key][key.strip()] = value.strip().strip('"').strip("'")

    return data


def load_config(config_path: Path) -> dict[str, Any]:
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
    data["API"] = {}
    return data


def run_config_command(command: str, config: dict[str, Any]) -> bool:
    cmds = config.get("cmds", {})
    if not isinstance(cmds, dict):
        return False
    module_path = cmds.get(command)
    if not isinstance(module_path, str) or not module_path.strip():
        return False

    module = importlib.import_module(module_path)
    command_main = getattr(module, "main", None)
    if not callable(command_main):
        raise AttributeError(f"Command module '{module_path}' does not expose a callable main()")
    command_main(config)
    return True


def get_feature_help_text() -> str:
    return """# Nexus Static Site Generator Features

Nexus is an API-first static site generator.

## Build Flow
- `python nexus.py` or `python nexus.py build`
- Reads `config.yml`
- Builds API once
- Renders markdown pages
- Runs plugins through the API contract

## API-First Plugin System
- Plugins are declared in `plugins`.
- Exposed plugin functions are declared with `api_exports`.
- User-visible API surface is controlled by `api_config.available_functions`.
- Dynamic elements and plugins receive the built `api` through `**context`.

## Config Example
```yaml
plugins:
  - name: seo
    script: plugins/seo.py
    api_exports:
      - generate_meta_tags

api_config:
  available_functions:
    - seo.generate_meta_tags
```

## Commands
- `build` (default): build site.
- Custom commands can be configured under `cmds` in `config.yml`.
"""


def ensure_feature_doc() -> Path:
    if not FEATURE_DOC_PATH.exists():
        FEATURE_DOC_PATH.write_text(get_feature_help_text(), encoding="utf-8")
    return FEATURE_DOC_PATH


def open_help_in_micro() -> None:
    doc_path = ensure_feature_doc()
    try:
        subprocess.run(["micro", str(doc_path)], check=False)
    except FileNotFoundError:
        raise SystemExit(
            f"Help document created at {doc_path}, but 'micro' is not installed or not on PATH."
        )


def main() -> None:
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        open_help_in_micro()
        return

    parser = argparse.ArgumentParser(
        description="Build static site with clean URLs and plugins",
        add_help=False,
    )
    parser.add_argument("command", nargs="?", default="build")
    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--json-logs", action="store_true")
    args = parser.parse_args()
    configure_logging(args.log_level, json_logs=args.json_logs)

    config = load_config(Path(args.config))

    if args.command != "build":
        if run_config_command(args.command, config):
            return
        raise SystemExit(f"Unknown command '{args.command}'. Add it under config.yml -> cmds.")

    src_dir = Path(str(config.get("src_dir", "src")))
    out_dir = Path(str(config.get("out_dir", "dist")))
    template_path = Path(str(config.get("default_template", "src/page.html.temp")))

    built, _all_pages = build_site(src_dir, out_dir, template_path, config)
    LOGGER.info("Built %s markdown page(s)", built)


if __name__ == "__main__":
    main()

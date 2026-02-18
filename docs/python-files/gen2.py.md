# gen2.py — Annotated Module Guide

`gen2.py` is an alternate static-site pipeline focused on:

- clean URL output generation from Markdown,
- static and dynamic template element injection,
- plugin execution,
- combined RSS feed generation,
- Bridgy Fed webmention queueing + publishing.

## CLI

```bash
python3 gen2.py build [--config config.yml]
python3 gen2.py publish [--dry-run] [--config config.yml]
```

- Default command is `build`.
- `publish` sends queued webmentions from `.webmention-state.json`.

## Key capabilities

### 1) Markdown + frontmatter rendering

- Parses YAML frontmatter into metadata (`parse_frontmatter`).
- Renders Markdown using `markdown` when available, with a regex-based fallback (`markdown_to_html`).

### 2) Template element injection

`inject_elements` supports two expansion forms:

- `~{path/to/file.html}~` for static file inclusion.
- `:{path/to/element.py}:` for dynamic Python execution.

Dynamic Python elements are loaded via `importlib.util.spec_from_file_location` and rendered through `render(...)`, `main(...)`, or `HTML` module variable fallback.

### 3) Site build behavior

`build_site(...)`:

- renders each Markdown file into clean URL structure (`.../index.html`),
- copies non-Markdown assets,
- runs configured plugins,
- writes a combined root RSS feed (`/rss.xml`) built from discovered XML feeds.

### 4) Combined feed assembly

`build_combined_rss_feed(...)`:

- scans `dist/**/*.xml` except root `rss.xml`,
- infers category from feed path,
- de-duplicates entries by guid/link/title,
- keeps the newest entry by parsed `pubDate`.

### 5) Webmention queue + publish

- `queue_bridgy_webping_for_notes(...)` queues a Bridgy Fed ping for each note page.
- `publish_webmentions(...)` publishes queued items to `https://fed.brid.gy/webmention`.
- Queue state persists in `.webmention-state.json` (`queue`, `published`).

## Config behavior

`load_config` merges `config.yml` over `DEFAULT_CONFIG` and accepts `site_url` aliases (`site-url`, `--site-url`) for compatibility.

## Related docs

- `docs/CODE.md`
- `docs/FEDERATION.md`
- `docs/USAGE.md`
- `docs/python-files/gen.py.md`

# Static Site Generator (ssg.md)

The site is powered by `gen.py`, a custom Python 3 static site generator built for modular, Markdown-first publishing.

## Core Logic and Workflow (`gen.py`)
- **Configuration**: `load_config` reads `config.yml` for paths (`src_dir`, `out_dir`), `default_template`, site metadata (`site_url`), plugin list, and custom commands (`cmds`).
- **Discovery**: The generator recursively discovers `*.md` files under `src/`.
- **Worker Objects (`Page`)**: Each markdown file is rendered by a `Page` instance through parsing, templating, and output writing.
- **Frontmatter Parsing**: `parse_frontmatter` extracts metadata like `title`, `date`, `template`, and `extends`.
- **Template Resolution**:
  - Uses `template:` for page-level template selection.
  - Supports inheritance with `extends:` and named blocks.
  - Enables reusable **subtemplates** by extending a shared parent and overriding only selected blocks.
- **Injections**: `inject_elements` performs multi-pass expansion for:
  - **Static includes**: `~{file}~`
  - **Dynamic elements**: `:{path.py}(args)`
- **Variable Rendering**: `render_template` replaces `{{ key }}` placeholders with computed context values.
- **Output Writing**: Markdown pages are emitted to `dist/` with clean URL structure (`.../index.html`).

## Extensibility and Plugins
`run_plugins` imports plugin modules declared in config and executes `main(...)` hooks after page rendering.

This keeps core generation focused while allowing extra behaviors such as:
- mobile-output generation
- RSS/feed generation
- webmention queue/publish workflows

## Subtemplate Feature Summary
The subtemplate system is implemented as template inheritance + block overrides:

1. Parent template defines blocks.
2. Child template declares `extends` and overrides one or more blocks.
3. Content pages select the child template via frontmatter.

Result: page families can share structure and behavior while customizing only needed sections.

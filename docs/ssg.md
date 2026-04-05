# Static Site Generator (ssg.md)

The site is powered by `gen.py`, a custom-built Python 3 static site generator designed for modular, Markdown-driven web development.

## Core Logic and Workflow (`gen.py`)
- **Configuration**: The process begins with `load_config`, which parses `config.yml`. This file defines crucial paths (`src_dir`, `out_dir`), the `default_template`, site metadata (`site_url`), and enables various plugins.
- **Rendering Lifecycle**: 
  - **Site Discovery**: The generator recursively traverses the source directory to discover all `.md` files.
  - **Worker Objects (`Page`)**: For every file, a `Page` object is instantiated. This worker maintains the state throughout the entire lifecycle: parsing, templating, and final output writing.
  - **Frontmatter**: Using `parse_frontmatter`, the generator extracts YAML-like metadata (title, date, template, etc.) at the top of each file, which informs subsequent rendering decisions.
  - **Dynamic Injections**: The engine performs multi-pass injections. `inject_elements` handles:
    - **Static Injections (`~{file}~`)**: Simple file content inclusion.
    - **Dynamic Elements (`:{path.py}(args):`)**: Advanced module execution. The generator imports specified Python modules and executes a `render` or `main` function, passing context variables, which returns HTML for seamless embedding.
  - **Templating**: Standard Jinja-like variable replacement occurs via `render_template`. It performs direct string replacement for keys enclosed in `{{ key }}`.
  - **Output Generation**: Files are written to the `dist/` directory, mirroring the source structure, with index pages getting clean directory-based URLs (e.g., `src/about.md` → `dist/about/index.html`).

## Extensibility and Plugins
- The plugin architecture allows for arbitrary logic injection after the main build process. `run_plugins` dynamically imports and executes modules listed in the configuration, enabling complex features like RSS feed generation, webmention handling, and mobile-specific page variations without modifying the core generator.

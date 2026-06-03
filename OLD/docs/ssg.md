# Static Site Generator (ssg.md)

The site is powered by `gen.py`, a custom Python 3 static site generator built for modular, Markdown-first publishing.

---

## 1. Core Logic and Workflow (`gen.py`)

1.  **Configuration**: `load_config` reads `config.yml` for paths, site metadata, plugin lists, and custom commands.
2.  **Discovery**: The generator recursively discovers `*.md` files under `src/`.
3.  **Worker Objects (`Page`)**: Each markdown file is rendered by a `Page` instance through a 3-step pipeline:
    -   **Step 1: Inheritance Resolution**: Resolves all `extends` and `block` replacements recursively.
    -   **Step 2: Element Injection**: Multi-pass expansion of static (`~{...}~`) and dynamic (`:{...}:(...)`) elements.
    -   **Step 3: Variable Rendering**: Replaces `{{ key }}` placeholders with context values.
4.  **Output Writing**: Markdown pages are emitted to `dist/` with clean URL structure (`.../index.html`).

---

## 2. Inheritance and Composition

-   **Frontmatter Parsing**: `parse_frontmatter` extracts metadata like `title`, `date`, `template`, and `extends`.
-   **Recursive Template Inheritance**: Supports `extends:` in both Markdown and templates, using named blocks `~{block NAME}~...~{endblock}~`.
-   **Sub-templates**: Common page patterns (like blogs or notes) are implemented as sub-templates that extend `page.html.temp`.
-   **Direct Inheritance**: A Markdown file can override template blocks directly by specifying `extends:` in its frontmatter.
-   **Element Composition**:
    -   **Static includes**: `~{file}~` (useful for headers, footers, etc.).
    -   **Dynamic elements**: `:{path.py}(args)` (executes a Python script to generate content).

---

## 3. Extensibility and Plugins

`run_plugins` imports plugin modules declared in `config.yml` and executes `main(...)` hooks after the primary page rendering is complete.

This enables extra behaviors such as:
- **Mobile output generation** (producing alternative mobile-friendly HTML).
- **RSS/feed generation** (scanning blog and note directories).
- **Webmention queue** (handling IndieWeb interactions).

---

## 4. Key Design Goals
-   **DRY (Don't Repeat Yourself)**: Using inheritance and elements ensures layout and component code is defined in only one place.
-   **Decoupled Logic**: Dynamic elements allow complex site features (like blog indexes) to be implemented in standalone Python scripts rather than being hardcoded into the generator.
-   **Clean URLs**: Every page is exported as an `index.html` file in its own directory.

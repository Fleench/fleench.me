# Static Site Generator (ssg.md)

The site is powered by `gen.py`, a custom-built Python 3 static site generator.

## Core Logic (`gen.py`)
- **Initialization**: `load_config` reads `config.yml` to set up source directories, output destinations, and active plugins.
- **Rendering Process**:
  - `build_site` iterates through all `.md` files in the source directory.
  - The `Page` object manages the lifecycle of each file:
    - **Frontmatter**: Extracts metadata using `parse_frontmatter`.
    - **Template Selection**: Determines which template to use (via metadata, specific directories, or defaults).
    - **Parsing**: `parse_content` splits Markdown into blocks, supports specific layout containers via `---` delimiters, and renders via `markdown_to_html` (using the `markdown` library if available, otherwise a custom fallback).
    - **Injection**: `inject_elements` processes dynamic content elements (`:{element.py}:`) and static injections (`~{file}~`).
    - **Replacement**: `render_template` handles standard `{{ key }}` variable substitution.
- **Dynamic Elements**: The `:{path.py}(args):` syntax allows embedding Python scripts that export a `render` or `main` function to inject dynamic content directly into templates.
- **Plugins**: A plugin system (`run_plugins`) triggers additional processing modules defined in `config.yml`.

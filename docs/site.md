# Site Architecture

The architecture is built on a strict separation between content (Markdown), structure (HTML templates), and presentation (CSS/JS), powered by a custom static site generator (`gen.py`).

## 1. Directory Structure

-   `src/`: Source content and templates.
    -   `*.md`: Markdown pages.
    -   `*.html.temp`: Site templates.
    -   `.elements/`: Modular building blocks (composition).
    -   `theme/`: Assets like images, icons, and small GIFs.
-   `dist/`: The generated static site (output).
-   `docs/`: Project documentation.
-   `scripts/`: Automation and build utilities.

---

## 2. Template System

The site uses a hybrid **Inheritance + Composition** model for its layouts.

-   **Base Shell (`page.html.temp`)**: The primary HTML structure.
-   **Sub-templates**: Specialized layouts like `blog.html.temp` or `note.html.temp` that extend the base shell.
-   **Template Blocks**: Named regions (`~{block NAME}~...~{endblock}~`) that can be overridden by sub-templates or even specific Markdown files.
-   **Template Elements (`src/.elements/`)**:
    -   **Static Elements (`.element`)**: HTML snippets like `nav.element` or `footer.element`.
    -   **Dynamic Elements (`.py`)**: Python scripts that generate HTML programmatically, such as `blogs.py` for listing posts or `spotify.py` for music integration.

---

## 3. Styling Framework

-   **Primary Styles (`style.css`)**: Global typography and defaults.
-   **Structural Grid (`style-grid.css`)**: Handles the site's responsive 3-column layout.
-   **Theming**: `dark.css` and `theme-mode.js` provide client-side theme persistence.
-   **Mobile Layer (`mobile.css`)**: Overrides styles for smaller viewports, working alongside specialized mobile templates in `src/mobile/`.

---

## 4. Content Logic

-   **Markdown-first**: Pages are written in Markdown with YAML frontmatter.
-   **Frontmatter Metadata**: Used to set titles, templates, and arbitrary page-specific data.
-   **Layout Containers**: `gen.py` supports layout structures via custom delimiters, enabling multi-column sidebars and callouts directly in authored content.

# Site Architecture (site.md)

The architecture is built on a strict separation between content (Markdown), structure (HTML templates), and presentation (CSS/JS).

## Template System
- **Template Locations**: Templates live in `src/` and use the `.html.temp` suffix.
- **Base Layout**: `page.html.temp` is the global container for shared site structure.
- **Subtemplates (new)**: Page-specific templates (for example `blog.html.temp` and `note.html.temp`) can be used as **subtemplates** to customize only selected sections while still inheriting the base layout behavior.
- **Mobile Variants**: `src/mobile/` contains mobile-focused templates like `mobile-blog.html.temp` and `mobile-note.html.temp`.

## Styling Framework
- **Primary Styles**: `style.css` for defaults and `style-grid.css` for structural grid behavior.
- **Theming**: `dark.css` and `theme-mode.js` provide client-side theme persistence.
- **Responsive Layer**: `mobile.css` adjusts layout behavior for smaller viewports.

## Content Components
Markdown supports layout containers via `---` delimiters. `gen.py` parses these into wrapper `div`s with classes/IDs, enabling callouts/sidebar-like structures directly in authored content.

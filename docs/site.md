# Site Architecture (site.md)

The architecture is built upon a philosophy of strict separation between content-authorship (Markdown), structure (HTML Templates), and presentation (CSS).

## Template System
- **Template Logic**: Templates are located in `src/` and follow a `.html.temp` naming convention. `page.html.temp` functions as the monolithic base for the site, though it is designed to be highly modular via the injection system.
- **Mobile Variants**: The `src/mobile/` directory contains templates specifically crafted for small-screen constraints, such as `mobile-blog.html.temp` and `mobile-note.html.temp`. These provide a distinct UI/UX flow from the desktop counterparts.

## Styling Framework
- **Primary Styles**: `style.css` handles the layout defaults, while `style-grid.css` provides the structural skeleton for the content layout.
- **Theming**: Dark mode capability is provided by `dark.css`. This is explicitly toggled via `theme-mode.js`, allowing client-side preference persistence without backend interference.
- **Responsive Design**: `mobile.css` serves as the corrective stylesheet to ensure that complex layouts collapse or reconfigure gracefully on mobile devices.

## Content Components
The system supports complex layout containers within Markdown via `---` delimiters. These blocks are parsed into CSS classes or IDs by `gen.py`, allowing authors to wrap content in specific `div` structures (e.g., sidebars, callouts, or grid items) directly from their Markdown documents, preventing the need for raw HTML in content files.

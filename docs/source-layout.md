# Source Layout

`src/` contains the authored site source.

- Markdown pages, blogs, and notes stay in place.
- `templates/` contains HTML templates.
- `templates/mobile/` contains mobile templates.
- `elements/` contains static `.element` includes and dynamic Python elements.
- `css/` contains stylesheets.
- `js/` contains browser scripts.
- CSS, JavaScript, images, and theme assets are copied to `dist/` during build.

Do not edit `dist/` directly; edit files here and rebuild.

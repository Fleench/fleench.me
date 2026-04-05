# Site Content (content.md)

The site functions as a personal digital garden, prioritizing chronological recording of thoughts, projects, and long-form writing.

## Authoring Categories
- **Index/Landing**: The root of the digital garden, located at `index.md`. It provides the primary navigation and context for visitors.
- **Blogs**: Located in `src/blogs/`, these are long-form, curated pieces. They utilize richer templates and are intended for more evergreen or polished content.
- **Notes**: Housed in `src/notes/`, these are the site's most granular content. They are heavily timestamped and organized into directory structures by date, facilitating rapid-fire publishing of thoughts as they occur (the "garden" aspect).
- **Static Documentation**: A collection of high-value information pages, including `about.md` (biographical), `ai.md` (AI interaction logging), `changelog.md` (site evolution), `todo.md` (project management), and `now.md` (the "now" page concept).

## Media and Metadata
- **Media**: Assets such as imagery and web-rating badges are found in `src/media/`. 
- **Versioning**: The file-based nature of the content—using Markdown—ensures the site is easily version-controllable, portable, and resistant to platform lock-in. It reflects an architectural choice to prefer simple text files over database-driven content management systems, facilitating long-term maintenance and accessibility.

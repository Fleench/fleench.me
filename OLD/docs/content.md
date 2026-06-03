# Site Content (content.md)

The site functions as a personal digital garden and professional portfolio, prioritizing chronological recording of thoughts, projects, and long-form technical writing.

## Authoring Categories
- **Index/Landing (`index.md`)**: The root of the digital garden. It serves as the primary navigation hub, establishing the site's identity and providing entry points to all other sections.
- **Blogs (`src/blogs/`)**: Curated, long-form articles. These entries focus on evergreen or polished content, utilizing richer, more specialized templates than standard notes.
- **Notes (`src/notes/`)**: The site's most granular and active content. Notes are timestamped, heavily organized into date-based directory structures (e.g., `src/notes/2026-04-01/`), and facilitate rapid-fire, informal publishing. This is the "garden" core, designed for stream-of-consciousness documentation.
- **Static Pages & Documentation**: 
    - `about.md`: A personal profile detailing the author's background (Computer Science student in Colorado), interests (game development, gaming, faith), and contact methodology.
    - `ai.md`: A declaration of site policies regarding AI usage. It outlines a philosophy of using AI only for code generation and maintenance (the "HoltBot" instance), while explicitly forbidding AI-generated content.
    - `changelog.md`: A record of the site's evolution and technical iterations.
    - `todo.md`: A tracker for project management and site-specific tasks.
    - `now.md`: A living document outlining current focuses.

## Media and Metadata
- **Media Assets**: Imagery, icons, and metadata badges (such as web-rating indicators) are housed in `src/media/`. 
- **Architectural Philosophy**: The site is file-based and Markdown-driven. This strategy ensures portability, avoids platform lock-in, and simplifies long-term maintenance by treating the site as source code rather than database-dependent content.

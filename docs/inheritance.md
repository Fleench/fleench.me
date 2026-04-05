# Template Inheritance and Block System

This document outlines the architecture of the new template inheritance system implemented in the static site generator.

## Overview
The system has moved from a "template-swap" model (where each page points to a discrete file) to an "inheritance-based" model. This allows for a single, consistent `page.html.temp` base layout while permitting granular customization of specific page components.

## Architecture
- **Base Template (`page.html.temp`)**: Serves as the master container for all site content. It defines the site skeleton, CSS/JS inclusions, and common structural components.
- **Child Templates**: Any template (e.g., `blog.html.temp`, `note.html.temp`) can now "extend" the base layout.
- **Blocks**: These are defined in the parent using `~{block NAME}~...~{endblock}~` and replaced by content in the child template using the same `~{block NAME}~...~{endblock}~` syntax.

## Implementation Details

### 1. Metadata Requirement
Each child template MUST declare the parent it extends in the frontmatter/meta-comment block:
```html
<!-- meta start -->
<!-- 
extends: src/page.html.temp
-->
<!-- meta end -->
```

### 2. Block Definition
In your base `page.html.temp`:
```html
<main>
  ~{block content}~
    {{ content }}
  ~{endblock}~
</main>
```

In your child template (e.g., `blog.html.temp`):
```html
~{block content}~
  <article class="blog-entry">
    <h1>{{ title }}</h1>
    {{ content }}
  </article>
~{endblock}~
```

## How It Works (`gen.py`)
- The `Page.prep_template()` function checks for the `extends` directive.
- If found, it reads the parent file into memory.
- It scans the child’s content for `block` tags.
- It uses regular expressions to find the corresponding `block` tags in the parent template and performs a surgical replacement of the placeholder content with the child’s defined content.
- This result is then processed through the standard `inject_elements` (for other includes) and `render_template` (for variables) pipelines.

## Benefits
- **DRY (Don't Repeat Yourself)**: Changes to the site layout (nav, headers, wrappers) now happen in one file (`page.html.temp`).
- **Granular Control**: Pages can easily modify specific regions (like a sidebar or content container) without duplicating the entire HTML structure.
- **Maintainability**: The separation of structure and content is now formal and enforced by the build system.

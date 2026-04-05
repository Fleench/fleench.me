# Template Inheritance, Blocks, and Subtemplates

This document outlines the template inheritance system in `gen.py`, including the **subtemplates** workflow for page-specific layout overrides.

## Overview
The generator supports an inheritance-based template model:

- A parent template (usually `src/page.html.temp`) provides the outer shell.
- Child templates override named `block`s from the parent.
- Markdown pages can then choose a child template with frontmatter (`template:`), creating a practical **subtemplate** layer on top of the base layout.

In practice:

- **Base template** = site-wide shell.
- **Template** = specialized page family (blog, note, etc.).
- **Subtemplate** = any template that extends another template and overrides only specific blocks.

## Syntax

### 1) Child template declares a parent
A child template must include an `extends` directive in a meta comment block:

```html
<!-- meta start -->
<!-- 
extends: src/page.html.temp
-->
<!-- meta end -->
```

### 2) Parent defines replaceable blocks

```html
<main>
  ~{block content}~
    {{ content }}
  ~{endblock}~
</main>
```

### 3) Child/subtemplate overrides a block

```html
~{block content}~
  <article class="blog-entry">
    <h1>{{ title }}</h1>
    {{ content }}
  </article>
~{endblock}~
```

## Page-Level Subtemplate Selection
Markdown pages choose templates with frontmatter:

```yaml
---
title: Example Post
template: src/blog.html.temp
---
```

A common pattern is:

1. `src/page.html.temp` defines the global shell.
2. `src/blog.html.temp` extends the base and overrides blocks.
3. A blog post sets `template: src/blog.html.temp`.

This gives reusable subtemplates without duplicating the full layout.

## How `gen.py` applies inheritance
`Page.prep_template()` performs inheritance resolution:

1. Reads markdown frontmatter.
2. Checks `extends` metadata.
3. Loads parent template text.
4. Finds each child `~{block NAME}~...~{endblock}~`.
5. Replaces matching parent blocks using regex.
6. Continues through normal include/dynamic injection and `{{ key }}` replacement.

## Benefits
- **DRY layouts**: One site shell, many focused subtemplates.
- **Safe customization**: Override only specific regions.
- **Clear author workflow**: Pick template in frontmatter; avoid full HTML duplication.

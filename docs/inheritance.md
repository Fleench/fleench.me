# Template Inheritance, Blocks, and Composition

The site generator uses a powerful, recursive template inheritance system combined with a modular composition (elements) model. This allows you to build complex layouts with minimal duplication while keeping components reusable.

## Overview
The architecture follows a hierarchical structure:

1.  **Base Template**: Provides the global HTML shell (e.g., `src/page.html.temp`).
2.  **Sub-template**: Extends the base template and overrides specific regions (e.g., `src/blog.html.temp`).
3.  **Composition (Elements)**: Reusable snippets or dynamic scripts (e.g., `src/.elements/`).
4.  **Markdown Page**: Selects a template via frontmatter OR extends a template directly.

---

## 1. Inheritance Syntax

### Template Meta Blocks
Templates declare their parent using a `meta` comment block:

```html
<!-- meta start -->
<!-- 
extends: src/page.html.temp
-->
<!-- meta end -->
```

### Named Blocks
Regions in a template can be made replaceable by wrapping them in `block` tags:

```html
~{block content_block}~
  <div class="default-content">
    {{ content }}
  </div>
~{endblock}~
```

### Direct Markdown Inheritance
A Markdown file can extend a template directly. When it does, it can override named blocks defined in the parent hierarchy.

```yaml
---
title: Custom Page
extends: src/page.html.temp
---
~{block content_block}~
  <section class="special-layout">
    <h1>{{ title }}</h1>
    {{ content }}
  </section>
~{endblock}~

This text will be injected into {{ content }} if referenced, 
or appended to the body.
```

---

## 2. Composition Syntax (Elements)

While inheritance builds the **vertical** structure of a page, elements handle **horizontal** composition—reusable bits that can be plugged in anywhere.

### Static Elements (`~{path/to/file}~`)
Inserts the content of a file directly into the template. This is useful for headers, footers, and meta-tags.

```html
<head>
  ~{src/.elements/head.element}~
</head>
```

### Dynamic Elements (`:{path/to/script.py}:(args)`)
Executes a Python script and inserts the returned string. The script should expose a `render` or `main` function.

```html
<section class="blog-list">
  :{src/.elements/blogs.py}:()
</section>
```
*Note: The generator passes a `context` dictionary to the script, which includes things like `project_root`, `src_dir`, and page-specific metadata.*

---

## 3. The Rendering Pipeline

The generator processes files in a strict order:

1.  **Inheritance Resolution**: First, `gen.py` resolves all `extends` and `block` replacements. This is recursive, so a sub-template can extend a base template, and a markdown file can extend a sub-template.
2.  **Element Injection**: Next, it searches for `~{...}~` and `:{...}:(...)` markers. This process is also recursive (up to 10 levels deep), allowing elements to include other elements.
3.  **Variable Substitution**: Finally, it replaces `{{ key }}` placeholders with values from the page's frontmatter or derived context (like `title`, `content`, `date`).

---

## 4. Best Practices: Inheritance vs. Composition

-   **Use Inheritance (Blocks)** when you want to change the **layout structure** for a category of pages (e.g., adding a sidebar to all blog posts).
-   **Use Composition (Elements)** when you want to **reuse a specific component** across different layouts (e.g., the site-wide marquee or a dynamic list of recent notes).

### Example: The Sub-template Pattern

1.  **Base (`src/page.html.temp`)**: Defines the outer shell with a `~{block content_block}~~{endblock}~`.
2.  **Sub-template (`src/blog.html.temp`)**: Extends the base, provides a blog-specific article wrapper, and maybe overrides the sidebar with `~{src/.elements/author.element}~`.
3.  **Page (`src/post.md`)**: Simply sets `template: src/blog.html.temp`.

Recursive resolution ensures that the final page includes the base shell, the blog layout, and the author element, all while the author writes simple Markdown.

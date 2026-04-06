# CODE.md — Detailed Code Architecture

This document explains the current Python codebase and module interactions.

## Top-level modules

- `gen.py`: primary static-site generator (build + command dispatch via `config.yml -> cmds`).
- `bot.py`: Discord orchestration for creating notes/replies and shipping updates.
- `scripts/build_notes.py`: helper for notes aggregation, feeds, and link discovery support.

## End-to-end flow

1. **Input creation**
   - A note/reply is authored (via Discord command or direct Markdown editing).
2. **Build phase**
   - `gen.py build` reads source Markdown + templates.
   - HTML is rendered into `dist/`.
   - Non-Markdown assets are copied.
   - Plugins run (where configured).
3. **Command phase**
   - `gen.py <custom-command>` runs mapped handlers from `config.yml -> cmds`.

## `gen.py` design detail

### Responsibilities

- Parse CLI args and configuration.
- Parse Markdown frontmatter.
- Render Markdown to HTML (library-backed or fallback renderer).
- Resolve template context and output URLs.
- **Recursive Template Inheritance**: Resolve `extends` across Markdown and templates.
- **Block Overrides**: Support named `~{block NAME}~...~{endblock}~` overrides.
- Support reusable subtemplates selected via page frontmatter (`template`).
- Expand static and dynamic template elements.
- Generate clean URL output structure (`.../index.html`).
- Copy static assets.
- Execute plugin hooks.

### Implementation: Recursive Inheritance (`Page.prep_template`)

The inheritance system is implemented in `Page.prep_template` and supported by `Page._resolve_template_text`:

1.  **Markdown check**: If the Markdown frontmatter contains `extends`, the whole file is processed as a child that can override parent blocks.
2.  **Template check**: If the Markdown file uses `template:`, that template is loaded.
3.  **Recursive Resolution**: `_resolve_template_text` is called on the template text.
    - It searches for an `extends` directive in the text (using either `extends: ...` or the `<!-- meta start -->` block).
    - If found, it recursively loads the parent and resolves its inheritance.
    - It then extracts any `~{block NAME}~...~{endblock}~` blocks from the current level and uses regex to replace the corresponding blocks in the parent's resolved text.
4.  **Final Result**: The process continues until no more `extends` directives are found, resulting in a single, fully composed template string.

## Template + Subtemplate contract

- **Base templates** define `~{block NAME}~...~{endblock}~` regions.
- **Child templates** (sub-templates) extend parent templates and override blocks.
- **Markdown pages** can:
    - Select a template via `template:`.
    - Directly extend a template via `extends:`.
    - Override blocks if using `extends:`.

## `bot.py` design detail

### Responsibilities

- Register Discord commands and restrict operations to allowed operator identity.
- Build frontmatter-backed note files with timestamped path naming.
- Trigger `gen.py build`.
- Stage relevant files, commit, and push.
- Summarize commit message text using Groq model output with fallback rules.

## `scripts/build_notes.py` design detail

### Responsibilities

- Aggregate note/reply content for a notes index page.
- Build RSS for notes.
- Parse and normalize links from Markdown + HTML.

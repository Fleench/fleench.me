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
   - `gen.py <custom-command>` runs mapped handlers from `config.yml -> cmds` (for example, publishing workflows).

## `gen.py` design detail

### Responsibilities

- Parse CLI args and configuration.
- Parse Markdown frontmatter.
- Render Markdown to HTML (library-backed or fallback renderer).
- Resolve template context and output URLs.
- Support template inheritance (`extends`) and block overrides.
- Support reusable subtemplates selected via page frontmatter (`template`).
- Expand static and dynamic template elements.
- Generate clean URL output structure (`.../index.html`).
- Copy static assets.
- Execute plugin hooks.

## Template + Subtemplate contract

- Parent templates define `~{block NAME}~...~{endblock}~` regions.
- Child templates override parent blocks and can serve as reusable subtemplates.
- Markdown pages select templates through frontmatter, allowing per-page layout selection without duplicating full HTML wrappers.

## `bot.py` design detail

### Responsibilities

- Register Discord commands and restrict operations to allowed operator identity.
- Build frontmatter-backed note files with timestamped path naming.
- Trigger `gen.py build`.
- Stage relevant files (`note`, `dist`, state file, etc.), commit, and push.
- Summarize commit message text using Groq model output with fallback rules.

## `scripts/build_notes.py` design detail

### Responsibilities

- Aggregate note/reply content for a notes index page.
- Build RSS for notes.
- Parse and normalize links from Markdown + HTML.

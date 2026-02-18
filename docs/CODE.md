# CODE.md — Detailed Code Architecture

This document explains how the Python codebase works and how modules interact.

## Top-level modules

- `gen.py`: static-site generator + webmention queue/publish CLI.
- `bot.py`: Discord orchestration layer for creating notes/replies and shipping updates.
- `scripts/build_notes.py`: build helper for notes index/feed and link discovery support.

## End-to-end flow

1. **Input creation**
   - A note/reply is authored (via Discord command or direct Markdown editing).
2. **Build phase**
   - `gen.py build` reads source Markdown + templates.
   - HTML is rendered into `dist/`.
   - non-Markdown assets are copied.
   - plugins run (including note/feed generation logic where configured).
   - outbound links are discovered and added to `.webmention-state.json` queue.
3. **Publish phase**
   - `gen.py publish` or bot `/publish` POSTs queued entries to fed.brid.gy webmention endpoint.
   - success entries move from `queue` to `published`.

## `gen.py` design detail

### Responsibilities

- Parse CLI args and configuration.
- Parse Markdown frontmatter.
- Render Markdown to HTML (library-backed or fallback renderer).
- Resolve template context and output URLs.
- Generate clean URL output structure (`.../index.html`).
- Copy static assets.
- Execute plugin hooks.
- Queue/publish webmentions.

### Notable implementation patterns

- **Graceful fallback parsing** when optional dependencies are missing.
- **Template fallback precedence** if per-page template is missing.
- **Idempotent queueing** by deduplicating `(source, target)` pairs across queue and published arrays.

## `bot.py` design detail

### Responsibilities

- Register Discord commands and gate operations to allowed operator identity.
- Build frontmatter-backed note files with timestamped path naming.
- Trigger `gen.py build`.
- Stage relevant files (`note`, `dist`, state file, etc.), commit, and push.
- Summarize commit message text using Groq model output with fallback rules.
- Publish queued webmentions and report counts/errors in command response.

### Reliability conventions

- Environment validation at startup (required secrets/IDs).
- Queue state read/write helpers with shape defaults.
- Network exception capture for publish attempts with failed items preserved.

## `scripts/build_notes.py` design detail

### Responsibilities

- Aggregate note/reply content for a notes index page.
- Build RSS for notes.
- Parse and normalize links from Markdown + HTML.
- Assist webmention queue discovery with canonical source URL handling.

### HTML/RSS safety

- Uses escaping helpers to avoid malformed XML/HTML serialization.
- Ensures predictable permalink generation for notes routes.

## Data contracts

## `.webmention-state.json`

Expected structure:

```json
{
  "version": 1,
  "queue": [
    {
      "source": "https://site.example/notes/.../",
      "target": "https://external.example/post",
      "queued_at": "2026-02-18T10:12:00+00:00"
    }
  ],
  "published": [
    {
      "source": "https://site.example/notes/.../",
      "target": "https://external.example/post",
      "published_at": "2026-02-18T10:14:00Z"
    }
  ]
}
```

## Operational notes for maintainers

- Keep build deterministic (same source => same output).
- Preserve queue idempotency and append-only publish history semantics.
- If changing command behavior, keep slash and prefix command parity.
- Validate state file writes in tests to avoid data shape regressions.

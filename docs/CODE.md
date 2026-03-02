# CODE.md — Detailed Code Architecture

This document explains how the Python codebase works and how modules interact.

## Top-level modules

- `gen.py`: primary static-site generator + webmention queue/publish CLI.
- `gen2.py`: alternative generator with dynamic template elements and combined feed assembly.
- `bot.py`: Discord orchestration layer for creating notes/replies and shipping updates.
- `scripts/build_notes.py`: build helper for notes index/feed and link discovery support.

## End-to-end flow

1. **Input creation**
   - A note/reply is authored (via Discord command or direct Markdown editing).
2. **Build phase**
   - `gen.py build` (or `gen2.py build`) reads source Markdown + templates.
   - HTML is rendered into `dist/`.
   - non-Markdown assets are copied.
   - plugins run (including note/feed generation logic where configured).
   - outbound links are discovered and added to `.webmention-state.json` queue using a content fingerprint (`source_hash`) for resend decisions.
3. **Publish phase**
   - `gen.py publish` / `gen2.py publish` or bot `/publish` POSTs queued entries to fed.brid.gy webmention endpoint.
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

## `gen2.py` design detail

### Responsibilities

- Includes all core `gen.py` build/publish responsibilities.
- Adds static + dynamic template element expansion (`~{...}~`, `:{...py}:`).
- Builds a combined root RSS feed from discovered sub-feeds.
- Queues Bridgy Fed pings for note pages after build.

### Notable implementation patterns

- Runtime-loaded dynamic template modules via `importlib.util`.
- Layered rendering with recursive element expansion limits.
- Feed de-duplication by `guid`/`link`/`title` and newest `pubDate` wins.

## `bot.py` design detail

### Responsibilities

- Register Discord commands and gate operations to allowed operator identity.
- Build frontmatter-backed note files with timestamped path naming.
- Trigger `gen.py build`.
- Stage relevant files (`note`, `dist`, state file, etc.), commit, and push.
- Summarize commit message text using Groq model output with fallback rules.
- Publish queued webmentions and report counts/errors in command response.

## `scripts/build_notes.py` design detail

### Responsibilities

- Aggregate note/reply content for a notes index page.
- Build RSS for notes.
- Parse and normalize links from Markdown + HTML.
- Assist webmention queue discovery with canonical source URL handling.

## Data contract: `.webmention-state.json`

Expected structure:

```json
{
  "version": 1,
  "queue": [
    {
      "source": "https://site.example/notes/.../",
      "target": "https://external.example/post",
      "source_hash": "sha256-hex-of-normalized-source",
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


## Resend behavior

Queue de-duplication key is `(source, target, source_hash)`, not only `(source, target)`.
That means edited source pages re-queue webmentions to the same target, while unchanged content does not generate duplicates.
Published history remains append-only for auditability.

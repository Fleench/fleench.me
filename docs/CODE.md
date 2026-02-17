# Codebase Architecture Guide

This guide is for future maintainers extending the IndieWeb publishing pipeline.

## Three-layer architecture

## 1) Content layer (Markdown notes)

Human-authored content is stored as Markdown under `src/notes/...` with frontmatter metadata (`date`, `type`, `template`, and optional `reply_to`).

## 2) Build layer (`gen.py`)

`gen.py` is the static site generator entrypoint. It renders templates, writes output under `dist/`, and coordinates build-time tasks.

## 3) Automation layer (`bot.py`)

`bot.py` is the operator interface and orchestration layer. It receives Discord commands and drives the publishing pipeline:

- write note/reply files
- run build
- stage + commit + push
- publish queued webmentions

## Key files

### `gen.py`

Primary static site generator command surface (for example, build/publish flows).

### `bot.py`

Discord automation interface and Git orchestrator. Handles command authorization, note creation, publishing, queue inspection, and manual publishing commands.

### `scripts/build_notes.py`

Build plugin responsible for note processing responsibilities, including feed generation and outbound link scanning used to queue webmentions.

# Link Reposts Plan

Goal: support a TikTok/Instagram-style "repost" flow, but only for sharing a link plus a small preview card and optional commentary.

This is not a content mirror. The repost should point to the original URL and render a compact preview with metadata.

## Intent

- Each repost is its own page, similar to notes.
- The page should show:
  - title
  - site name or domain
  - description
  - optional image
  - the original URL
  - my own note or caption
  - webmentions below the post
- The underlying content remains on the original site.

## Proposed File Layout

- `src/reposts.md` for the index page.
- `src/reposts/YYYY-MM-DD/HHMM.md` for each repost page.
- `src/templates/repost.html.temp` for the standalone repost page.
- `src/templates/mobile/mobile-repost.html.temp` later, if mobile parity is needed.

This keeps reposts as a separate content family while matching the existing note pattern.

## Markdown Shape

Keep the format simple since every entry is a link post.

```md
---
date: 2026-05-26T12:34
template: src/templates/repost.html.temp
url: https://example.com/article
title: Optional override title
description: Optional override description
site_name: Optional site name
image: Optional preview image URL
---

Optional note or commentary.
```

## Rendering Rules

- If frontmatter includes metadata, use it first.
- If metadata is missing, fall back to Open Graph tags.
- If OG data is weak, fall back to page title and domain.
- Show the repost preview as a card component.
- Keep the original URL clickable and obvious.
- Keep the author note separate from the link preview so the post still feels personal.

## Webmentions

- Add the webmention block to each repost page, not just the index.
- This keeps replies and backlinks attached to the individual repost.
- The index can remain a clean browsing view.

## Bot Workflow

1. User pastes a URL.
2. Bot fetches metadata.
3. Bot writes a markdown file to `src/reposts/...`.
4. Build generates a standalone page and index entry.
5. The page can later be crossposted or reused by other publishing flows.

## Repo Fit

- This should fit the current repo cleanly.
- `gen.py` already knows how to build Markdown pages.
- The current notes system shows that one-file-per-page content is already a working pattern.
- The CMS in `app.py` only manages `src/notes/` today, so repost editing would need a separate path if I want to create them from the admin UI.

## Later Work

- Add generator support so `src/reposts/` gets the right template automatically.
- Add a repost index page.
- Add a card component for previews.
- Add bot support for writing repost files.
- Add mobile template support if the repost flow becomes a regular publishing path.

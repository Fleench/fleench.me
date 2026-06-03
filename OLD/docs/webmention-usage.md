# Usage

## Webmention queue and publish flow

- `python3 gen.py build` now **queues** webmentions by scanning links in:
  - source markdown files (`src/**/*.md`)
  - generated html pages (`dist/**/*.html`)
- queued entries are stored in `.webmention-state.json`.
- the build step does **not** publish webmentions; it only queues them.

Queue entries are stored as source/target pairs:

- `source`: your site page URL
- `target`: external HTTP(S) link discovered on that page

## Bot commands

The bot now includes commands to inspect and publish the queue:

### Slash commands

- `/queue` — show queued + published counts and preview queued items.
- `/publish` — send queued webmentions using the configured sender flow (prefers `indieweb_utils`).

### Prefix commands

- `!queue`
- `!publish`

## Note/reply publishing behavior

- `/note` and `/reply` still:
  1. create/update note markdown
  2. run `python3 gen.py build`
  3. commit and push
- they now also stage `.webmention-state.json` so queued mentions are saved in git history.

## CLI publishing

You can now publish queued webmentions directly from `gen.py`:

- `python3 gen.py publish` — sends queued webmentions using `indieweb_utils` when available (with legacy fallback)
- `python3 gen.py publish --dry-run` — shows what would be sent without making network requests


## Logging

- `python3 gen.py build --log-level DEBUG` — verbose build diagnostics
- `python3 gen.py publish --json-logs` — structured JSON log output

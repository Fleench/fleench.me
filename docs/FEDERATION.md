# Federation and Webmention Delivery

This document explains how webmentions move from local queueing to federation delivery.

## Queue vs Bridge

### The Queue (local state)

Queued webmentions are stored in a local JSON state file (`.webmention-state.json`).

- `queue`: webmentions waiting to be sent.
- `published`: webmentions already sent.

This gives you durable local state across builds and bot runs.

### Sender behavior

Publishing prefers `indieweb_utils.send_webmention(source, target)` to discover and submit to target endpoints. If the library is unavailable, the legacy Bridgy fallback transport is used.

## Workflow

1. `gen.py build` (or `gen2.py build`) renders site output.
2. During build, link discovery queues webmention candidates into `.webmention-state.json`.
3. Publishing sends queued mentions via the sender abstraction (library-first, fallback transport).
   - You can do this manually with the publish command.
   - The bot also runs this automatically after Git push in its publish workflow.

Important distinction:

- **Build step** finds and queues links.
- **Publish step** actually sends network requests.

## Troubleshooting when a mention does not appear

1. Check queue status via Discord `/queue`.
   - If items are queued, they have not successfully sent yet.
2. Verify your site URL configuration in `config.yml` (`site_url` must be correct and publicly reachable).
3. Re-run publishing and inspect failures.
   - Errors usually include source/target and the transport issue.
4. Confirm your generated source page is live and accessible by URL.
   - Bridgy must be able to fetch the source URL.

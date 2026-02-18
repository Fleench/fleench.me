# USSAGE.md (Modulated Workflow Guide)

This file was moved from the repository root into `/docs` and expanded into a clearer operations guide.

## Quick start

1. Install dependencies.
2. Configure `.env` values for Discord + Groq.
3. Build the site with:

```bash
python3 gen.py build
```

4. Optionally publish queued webmentions:

```bash
python3 gen.py publish
```

## Runtime modulation (what changed conceptually)

The project works as a **modulated publishing pipeline** with three independently runnable layers:

- **Content modulation**: Markdown notes/replies are source-of-truth content.
- **Build modulation**: `gen.py` transforms content + templates into `dist/` output.
- **Automation modulation**: `bot.py` orchestrates note creation, build, git commit/push, and webmention publishing.

This modulation means each layer can be run independently for debugging and also chained for production publishing.

## Discord command usage

### Slash commands

- `/note <content>`: Create a note, build, stage, commit, push, then publish queued webmentions.
- `/reply <url> <content>`: Create reply note with `reply_to`, then run the same pipeline.
- `/queue`: Show queued and published webmention counts.
- `/publish`: Publish queued webmentions now.

### Prefix command aliases

- `!note <content>`
- `!reply <url> <content>`
- `!queue`
- `!publish`

## CLI usage

### Build static site

```bash
python3 gen.py build
```

### Publish queue

```bash
python3 gen.py publish
```

### Dry run publish

```bash
python3 gen.py publish --dry-run
```

## Queue + state file

Webmention queue state is persisted in:

- `.webmention-state.json`

The state tracks:

- `queue`: discovered but unsent webmentions.
- `published`: successfully sent webmentions.

## Recommended operator loop

1. Post content via Discord (`/note` or `/reply`) or write Markdown manually.
2. Run build (`gen.py build`) if working outside Discord.
3. Check queue (`/queue` or `!queue`).
4. Publish (`/publish` or `gen.py publish`).
5. Verify generated output in `dist/` and git history.

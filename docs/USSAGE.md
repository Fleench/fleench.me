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

5. Alternative generator path:

```bash
python3 gen2.py build
python3 gen2.py publish --dry-run
```

## Runtime modulation

The project works as a modulated publishing pipeline with three independently runnable layers:

- **Content modulation**: Markdown notes/replies are source-of-truth content.
- **Build modulation**: `gen.py` or `gen2.py` transforms content + templates into `dist/` output.
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

## Queue + state file

Webmention queue state is persisted in `.webmention-state.json`.

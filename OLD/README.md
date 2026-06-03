# flench.me

Personal static site source for `https://flench.me`.

The site is built with `gen.py`, a custom Markdown-first static site generator. Authored content lives in `src/`; generated output is written to `dist/`.

## Common Commands

```bash
.venv/bin/python gen.py build
.venv/bin/python gen.py build --remove
.venv/bin/python -m http.server 8000 --directory dist
.venv/bin/python -m unittest discover tests
node --test tests/theme-mode.test.mjs
```

## Repo Layout

- `gen.py` - current static site generator entrypoint.
- `config.yml` - build paths, plugin list, and command hooks.
- `src/` - authored site source.
- `src/templates/` - HTML templates only.
- `src/elements/` - reusable static and dynamic template elements.
- `src/css/` - stylesheet assets.
- `src/js/` - browser JavaScript assets.
- `scripts/` - build plugins and helper scripts.
- `tests/` - Python and JavaScript tests.
- `docs/` - project documentation, plans, and reference notes.
- `archive/` - historical generator copies and template backups.
- `dist/` - generated site output. Do not edit or commit this directory.

## Build Output

`dist/` is intentionally ignored by Git. Rebuild it locally when previewing or deploying.

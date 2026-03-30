# Nexus Static Site Generator Features

Nexus is an API-first static site generator focused on predictable plugin integration.

## What is new

- API is built first as a contract between plugins and dynamic elements.
- Plugins can export specific functions with `api_exports`.
- Users can limit callable API functions via `api_config.available_functions`.
- Dynamic elements receive API and site context through `**context`.
- Plugin `main(...)` functions can receive `api=...` for plugin-to-plugin collaboration.

## Build order

1. Parse config and normalize plugin definitions.
2. Load plugin modules.
3. Validate exports and build `api` map.
4. Render pages and dynamic elements with `api` in context.
5. Run plugins with access to rendered pages and `api`.

## Config examples

### Plugin declaration with API exports

```yaml
plugins:
  - name: markdown_processor
    script: plugins/markdown.py
    api_exports:
      - process_markdown
      - syntax_highlight

  - name: image_handler
    script: plugins/images.py
    api_exports:
      - optimize_image
      - responsive_srcset
```

### Limit API availability

```yaml
api_config:
  available_functions:
    - markdown_processor.process_markdown
    - image_handler.optimize_image
```

## Commands

- `python nexus.py` -> build (default)
- `python nexus.py build` -> build explicitly
- `python nexus.py <custom-command>` -> run command from `config.yml` -> `cmds`
- `python nexus.py -h` or `python nexus.py --help` -> open this document in `micro`

## Notes

- If `micro` is missing, Nexus exits with a clear message and leaves this file in place.
- This document is stored at `nexus_features.md` next to `nexus.py`.

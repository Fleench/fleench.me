# Custom Scripts (scripts.md)

Custom scripts are managed within the `scripts/` directory and utilized via the plugin system defined in `config.yml`.

## Plugins (Active)
- `scripts.mobile`: Likely handles mobile-specific layout generation and template logic.
- `scripts.rss_plugin`: Generates RSS feeds for the site content.
- `scripts.webmentions`: Processes webmentions for interactive social engagement.

## CLI Commands (`cmds`)
- `publish`: Maps to `scripts.webmentions`, allowing for manual execution of webmention publishing via the `gen.py` interface.

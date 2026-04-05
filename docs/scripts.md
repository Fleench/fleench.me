# Custom Scripts (scripts.md)

Custom functionality is modularized within the `scripts/` directory, operating as an extension to the core generator rather than core logic itself.

## Plugin Ecosystem
- **`scripts.mobile`**: This plugin intercepts the build process to generate mobile-optimized versions of site pages. It likely monitors content types and redirects or transforms templates into mobile-compatible HTML.
- **`scripts.rss_plugin`**: Responsible for the automatic generation of `rss.xml` files. It crawls blog and note entries, aggregates metadata, and formats the output into standard RSS feeds to ensure syndication compatibility.
- **`scripts.webmentions`**: A critical plugin for modern engagement. It monitors the site for references, aggregates incoming webmentions, and manages the publishing workflow to sync with social web services.

## Command-Line Interface (`cmds`)
The `gen.py` framework supports custom CLI commands mapped via `config.yml`.
- **`publish`**: This command is bound to `scripts.webmentions.main`. It provides a convenient entry point for manually triggering the webmention publication cycle, ensuring that the site communicates effectively with external platforms without needing a full rebuild. 
- **Extensibility**: The system is designed to allow new commands (e.g., deployment, cleanup, or data migration) to be added simply by referencing a Python module and an entry function in the configuration file, keeping the core generator footprint minimal.

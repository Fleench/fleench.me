# USSAGE.md

## Overview

This repository has two primary moving parts that work together but can also be operated independently:

1. **`gen.py`** — a static site generator that converts Markdown content into HTML pages, applies templates, copies static assets, and optionally runs plugins.
2. **`bot.py`** — a Discord slash-command bot that creates notes/replies as Markdown files, triggers site generation through `gen.py`, and then commits/pushes the generated result to Git.

A useful way to think about this codebase is as a **content pipeline**:

- You produce content (manually or through the bot).
- Content is written into `src/` as Markdown with frontmatter.
- `gen.py` transforms that content into a publishable `dist/` website.
- The bot automates the writing + building + committing + pushing cycle.

Although there are template and style files in `src/`, this guide intentionally spends more time on *how the machinery works* than on visual/frontend internals.

---

## High-level architecture

At runtime, three conceptual layers are involved:

- **Content layer**: Markdown files in `src/` (especially under `src/notes/...`) with optional YAML frontmatter.
- **Build layer**: `gen.py` reads config, parses Markdown, resolves templates, renders output to `dist/`, copies non-Markdown assets, and runs plugins.
- **Automation layer**: `bot.py` receives Discord commands, creates note files, calls `gen.py build`, stages relevant files, commits with an AI-generated summary, then pushes.

The key design principle is that content and build are decoupled from chat interaction. You can build manually without the bot, and the bot itself is basically a wrapper around local file writes and CLI/Git operations.

---

## Directory and file roles

While this guide does not focus on deep source styling details, it helps to know what each important file is for:

- `gen.py` — build engine.
- `bot.py` — Discord automation.
- `config.yml` — declarative build settings (`src_dir`, `out_dir`, template path, plugins).
- `src/page.html.temp` — default page template.
- `src/reply.html.temp` — template used for reply-type notes.
- `scripts/build_notes.py` — referenced in bot staging list (likely involved in notes workflows, depending on local usage).
- `dist/` — generated output folder produced by the build.

---

## Part 1: How to use `gen.py`

## 1) What `gen.py` does

`gen.py` is a lightweight static site generator. On `build`, it:

1. Loads configuration from `config.yml` (or another file if `--config` is provided).
2. Determines source folder, destination folder, default template, and plugin list.
3. Finds all `*.md` files recursively in the source directory.
4. For each Markdown file:
   - Parses frontmatter if present.
   - Renders Markdown body to HTML.
   - Chooses template (frontmatter override or default).
   - Interpolates values into template placeholders.
   - Writes HTML to a clean URL output path.
5. Copies all non-Markdown assets from source to output.
6. Runs configured plugins.
7. Prints how many Markdown pages were built.

The implementation is intentionally forgiving: if optional dependencies are unavailable, it uses fallback behavior rather than failing immediately.

## 2) Running `gen.py`

### Basic command

```bash
python3 gen.py build
```

`build` is the only accepted command right now. It is also the default if omitted, so this also works:

```bash
python3 gen.py
```

### Using a different config file

```bash
python3 gen.py build --config path/to/other-config.yml
```

If the config file is missing, the script uses built-in defaults.

## 3) Configuration behavior

`gen.py` starts from this default config:

- `src_dir: "src"`
- `out_dir: "dist"`
- `default_template: "src/page.html.temp"`
- `plugins: []`

Then it merges any values loaded from config.

If `PyYAML` is installed, YAML parsing is done with `yaml.safe_load`. If not, a simple line-based parser handles basic key-value and list patterns.

### Why this matters operationally

This means production usage can survive environments where dependencies are partly missing. You get graceful degradation rather than hard failure, but you should still prefer installing full dependencies for correctness and richer behavior.

## 4) Markdown frontmatter processing

A Markdown file may begin with a frontmatter block:

```yaml
---
title: "Example"
date: "2026-02-17"
template: "src/reply.html.temp"
---

# Body
```

`gen.py` recognizes frontmatter only when:

- File starts with `---\n`
- A closing delimiter exists as `\n---\n`

If that structure is not found, file is treated as pure Markdown body with empty metadata.

If YAML parser is available, metadata can include richer YAML. Without YAML parser, fallback parsing treats lines as simple `key: value` pairs and simple list item conventions.

## 5) Markdown rendering strategy

`gen.py` attempts to import `markdown` Python package (`markdown as md_lib`).

- If available: it renders using `extensions=["extra", "sane_lists"]`.
- If unavailable: it uses a minimal fallback renderer:
  - `#` headings become `<h1>`..`<h6>`
  - non-empty non-heading lines become `<p>` blocks
  - content is HTML-escaped

This fallback is intentionally minimal and not a full Markdown implementation.

## 6) Template rendering

The template system is simple placeholder replacement:

- It replaces exact tokens in the form `{{ key }}` with string values from context.
- There is no conditionals/loops/include language.

Context includes at least:

- `title` — derived from frontmatter or filename rules
- `content` — rendered HTML body
- `date` — frontmatter date (escaped)
- `output` — generated relative URL (e.g., `/notes/2026-02-17/1234/`)
- plus all frontmatter keys (escaped stringified values)

Important nuance: values from frontmatter are escaped before insertion, while `content` is already HTML from Markdown conversion.

## 7) URL and output path rules

For source file relative paths:

- `src/index.md` -> `dist/index.html`
- `src/about.md` -> `dist/about/index.html`
- `src/notes/2026-02-17/1234.md` -> `dist/notes/2026-02-17/1234/index.html`

This gives "clean URLs" where directories map to page routes ending with `/` when served.

`output` URL inserted in templates removes trailing `index.html` if present.

## 8) Template selection precedence

For each Markdown file:

1. If frontmatter has `template`, that path is attempted.
2. If chosen template path is relative, it is resolved from current working directory.
3. If that template exists, use it.
4. Otherwise, silently fall back to the default template loaded at startup.

This allows per-page templates while still being resilient to missing template files.

## 9) Title derivation rules

Title logic:

1. If frontmatter `title` is a non-empty string -> use it.
2. Else if filename stem is `index` -> title becomes `Home`.
3. Else derive from filename by replacing `_` and `-` with spaces and applying title-case.

This ensures every generated page has some title string even without explicit metadata.

## 10) Asset copying

After Markdown build, `gen.py` walks all files under `src/` and copies any file whose suffix is **not** `.md` to matching path in `dist/`.

Practical effect:

- CSS, JS, images, template-adjacent assets are mirrored into output.
- Templates themselves (`*.temp`) are also copied, because they are non-Markdown files.
- Markdown is transformed, not copied.

## 11) Plugin execution model

`plugins` in config is expected to be a list of module names.

For each plugin name:

- `importlib.import_module(plugin_name)` imports module.
- If module exposes callable `main`, it is called as `main(src_dir, out_dir, config)`.

No try/catch around plugin import/execute exists here, so plugin errors will propagate and fail build. This is generally desirable in CI-like pipelines because plugin failure should be visible.

## 12) Failure modes and diagnostics for `gen.py`

Main hard failures include:

- Source directory missing.
- Default template missing.
- Plugin import/runtime error.

Soft degradations include:

- Missing `markdown` package -> minimal Markdown renderer.
- Missing `yaml` package -> simple parser.
- Missing per-file template path -> fallback template used.

Console output currently just reports built page count; deeper diagnostics would require expanding script logging.

---

## Part 2: How to use `bot.py`

## 1) What the bot is for

`bot.py` is a Discord bot focused on content publishing operations. It exposes slash commands to create notes and replies. Internally it transforms a Discord interaction into a version-controlled site update.

The bot is opinionated:

- Only one authorized user can run commands.
- It expects local Git setup and push permissions.
- It expects build tools and templates to exist.
- It uses Groq API to synthesize commit message summaries.

## 2) Environment requirements

Bot startup loads `.env` via `python-dotenv`, then validates required variables:

- `DISCORD_TOKEN` (required)
- `GROQ_API_KEY` (required)
- `MY_DISCORD_ID` (required, numeric string)
- `GUILD_ID` (optional; if set, commands sync to that guild)

If any required variable is missing, startup raises `RuntimeError` and exits.

### Typical `.env` sketch

```env
DISCORD_TOKEN=...
GROQ_API_KEY=...
MY_DISCORD_ID=123456789012345678
GUILD_ID=987654321098765432
```

## 3) Running the bot

Start the bot with:

```bash
python3 bot.py
```

On successful login, it prints identity and command sync results.

If `GUILD_ID` is set, slash commands are registered to that guild (faster propagation). Otherwise commands are synced globally.

## 4) Authorization logic

The bot enforces access using a slash-command check:

- `interaction.user.id == ALLOWED_USER_ID`

Unauthorized callers receive an ephemeral denial message and no publishing pipeline is run.

This is a key safety design: regardless of who can see the bot, only configured user ID is permitted to issue mutating commands.

## 5) Commands provided

### `/note`

Input: `content` string.

Flow:

1. Defers interaction response (ephemeral + thinking).
2. Writes Markdown note file with frontmatter type `note`, template `src/note.html.temp`.
3. Runs publish pipeline (build + git add + commit + push).
4. Sends success/failure ephemeral response.

### `/reply`

Inputs:

- `url` (target being replied to)
- `content` (reply text)

Flow is similar, but file frontmatter includes:

- `type: reply`
- `template: src/reply.html.temp`
- `reply_to: "<url>"`

## 6) Note file path generation

Files are written under `src/notes/<YYYY-MM-DD>/`.

Filename pattern:

- primary: `<HHMM>.md`
- fallback if collision: `<HHMMSS>.md`

This provides chronological and mostly human-readable organization while minimizing filename collisions for closely timed entries.

## 7) Frontmatter emitted by bot

Each new note contains frontmatter similar to:

```yaml
---
date: 2026-02-17T14:31
type: note
template: src/note.html.temp
---

Your text here.
```

Replys additionally include `reply_to` URL.

This frontmatter is intentionally aligned with `gen.py` expectations so template selection and metadata interpolation work automatically at build time.

## 8) Commit summary generation via Groq

Before publishing, bot calls Groq chat completion endpoint with model `llama3-8b-8192` to produce a concise 3-5 word commit summary.

Prompt contract:

- Ask for 3-5 word summary.
- Return text without punctuation.

Post-processing:

- Use first response line.
- Split into words.
- If not between 3 and 5 words, fallback to `add <note_type> update`.

This ensures commit message constraints are enforced regardless of model variation.

## 9) Publish pipeline details

`_publish` performs sequential actions:

1. Generate commit summary.
2. Run `python3 gen.py build`.
3. Run `git add` on:
   - newly created note file path
   - `dist`
   - selected templates/config/scripts (`src/note.html.temp`, `src/reply.html.temp`, `config.yml`, `gen.py`, `scripts/build_notes.py`)
4. Commit with generated summary.
5. Push to remote.

### Why this staging list matters

The bot deliberately stages both dynamic output (`dist`) and key pipeline files. This can include unchanged files; Git simply ignores unchanged entries. It helps reduce risk of missing required build-related edits when commits are bot-generated.

## 10) Error handling behavior

Two error classes are surfaced to Discord users:

- `subprocess.CalledProcessError` => "Git/build error" + trailing stderr snippet.
- Generic exception => "Unexpected error" message.

All responses are ephemeral, reducing channel noise and preventing accidental public leakage of raw failures.

## 11) Async model and blocking calls

Although bot handlers are async, blocking operations (subprocess and commit summary generation) are wrapped with `asyncio.to_thread`. This keeps the event loop responsive while operations run in worker threads.

This design avoids freezing command processing during Git/build/network calls.

---

## Part 3: How `gen.py` and the bot work together

The integration is straightforward but powerful:

1. Bot writes a Markdown file that contains metadata recognized by generator.
2. Bot executes generator to refresh output site.
3. Bot commits both source update and generated output.
4. Bot pushes to remote, enabling deployment workflow outside this repository (if configured).

This pattern gives you a chat-driven CMS-like workflow without introducing a heavy CMS backend.

### End-to-end example mental model

When `/reply` is called:

- A file like `src/notes/2026-02-17/1431.md` appears.
- Frontmatter selects `src/reply.html.temp` and records reply target URL.
- `gen.py` builds this into `dist/notes/2026-02-17/1431/index.html`.
- Template receives `{{ reply_to }}` and other fields.
- Commit is created and pushed.

From a system design perspective, the bot is not rendering HTML itself; it only produces content + triggers a deterministic build step.

---

## Operational guidance and best practices

## 1) Keep dependencies explicit

Even with fallback logic, install full dependencies in production:

- `markdown`
- `PyYAML`
- `discord.py`
- `python-dotenv`
- `groq`

Fallback modes are good safety nets, not ideal long-term runtime standards.

## 2) Validate build locally

Before relying heavily on bot automation, manually run:

```bash
python3 gen.py build
```

Then inspect output directory and verify templates behave as expected.

## 3) Secure secrets

Never commit `.env` with real tokens. Keep:

- Discord token private.
- Groq API key private.
- Authorized Discord ID accurately configured.

A mistaken `MY_DISCORD_ID` can lock out legitimate use or unintentionally permit another account.

## 4) Git environment readiness

Because bot invokes `git add/commit/push`, ensure runtime environment has:

- Clean repo permissions.
- Correct branch checked out.
- Remote configured.
- Auth for pushing (SSH key/token).

Any Git misconfiguration bubbles up as command errors in bot responses.

## 5) Understand generated artifact strategy

This repo’s automation appears to commit generated `dist/` output. That is a valid static site strategy when host expects prebuilt files from Git. If you later move to CI-based build-on-deploy, you may adjust bot staging behavior.

## 6) Consider branch protection implications

If remote branch requires PRs or signed commits, bot `git push` may fail. In such environments, alter `_publish` strategy (e.g., push to automation branch, open PR separately).

## 7) Plugin hygiene

If you enable plugins in config, treat them as trusted code: they run with full process permissions during build. Keep plugin names clear and dependencies pinned.

---

## Extending behavior safely

## 1) Adding new content command types

To add a new slash command (e.g., `/bookmark`):

- Implement new command handler mirroring `note`/`reply` structure.
- Set distinct `type` and template in `_write_note` call.
- Ensure template file exists and supports expected metadata keys.

No generator changes are required if frontmatter-driven template logic is sufficient.

## 2) Improving template engine (optional)

Current placeholder replacement is intentionally minimal. If future needs require loops, conditionals, includes, or escaping control, introduce a templating library (e.g., Jinja2). Do so cautiously and document migration semantics.

## 3) Hardening publish pipeline

Potential improvements if needed:

- Add pre-commit validation command before commit.
- Log stdout/stderr from subprocess to persistent file.
- Add retry/backoff for transient push failures.
- Add configurable branch target.

These are architectural extensions; base workflow already remains coherent.

---

## Troubleshooting guide

## `gen.py` says source/template missing

Cause: invalid `config.yml` paths or wrong working directory.

Fix:

- Confirm you run command from repository root.
- Verify `src_dir` and `default_template` entries.

## Build output missing expected metadata values

Cause possibilities:

- Frontmatter not properly delimited with `---` lines.
- YAML parsing fallback misreading complex syntax.
- Placeholder token mismatch in template.

Fix:

- Validate frontmatter delimiter format exactly.
- Keep metadata values simple if running without PyYAML.
- Ensure template contains exact token names like `{{ title }}`.

## Bot starts then commands do nothing

Cause possibilities:

- Commands not synced yet.
- Wrong `GUILD_ID`.
- Unauthorized user ID.

Fix:

- Check startup logs for sync count.
- Verify `MY_DISCORD_ID` and invoking account match.
- If global sync, allow propagation time.

## Bot returns Git/build errors

Cause possibilities:

- Build broke due to template/config/plugin issue.
- Git working tree state conflicts.
- No push permission.

Fix:

- Run failing commands manually in repo shell.
- Inspect `git status`, remote URL, auth method.
- Resolve conflicts and rerun.

## Commit summary quality odd

Cause: model output outside word constraints.

Fix:

- Code already falls back to deterministic summary. If you want stricter behavior, replace AI summary with timestamped static format.

---

## Summary

`gen.py` and `bot.py` together provide a pragmatic, low-complexity publishing system:

- `gen.py` handles deterministic transformation from Markdown + metadata into clean-URL static HTML.
- `bot.py` handles controlled, permissioned content creation and Git publication from Discord.
- The contract between them is frontmatter metadata plus predictable file paths.

The result is a workflow where content can be authored quickly through chat commands while still producing version-controlled, inspectable static output.

If you keep environment variables secure, dependencies installed, and Git/push permissions healthy, the system is robust and easy to operate. The most important implementation idea to remember is this: **the bot is an orchestrator; `gen.py` is the builder.** Once that mental model is clear, troubleshooting and extending the system becomes straightforward.

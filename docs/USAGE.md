# Using the Discord Publishing Bot

This guide explains the everyday commands you can run from Discord and the equivalent CLI actions.

## Post a note

Use:

```text
/note <content>
```

Example:

```text
/note Shipping a small update to my site today.
```

What happens after you submit the command:

1. The bot creates a Markdown note file.
2. It runs the site build (`python3 gen.py build`).
3. It stages generated files and your new note in Git.
4. It creates a commit message summary.
5. It commits and pushes to your remote repository.
6. It automatically sends any queued webmention pings.

## Post a reply to an IndieWeb URL

Use:

```text
/reply <url> <content>
```

Example:

```text
/reply https://example.com/post/123 Really enjoyed this write-up. Thanks for sharing.
```

This creates a reply note that records the URL you are responding to, then follows the same automatic build/commit/push flow.

## Queue and publish commands

### Slash commands

- `/queue` — show queued + published webmention counts.
- `/publish` — publish queued mentions now.

### Prefix aliases

- `!queue`
- `!publish`

## CLI equivalents

```bash
python3 gen.py build
python3 gen.py publish
python3 gen.py publish --dry-run
```

Alternative pipeline:

```bash
python3 gen2.py build
python3 gen2.py publish --dry-run
```

## What is automated for you

When you run `/note` or `/reply`, you do **not** need to manually run build or Git commands. The bot handles:

- Site generation
- Git add/commit/push
- Webmention queue publishing

So your workflow stays focused on writing content in Discord.

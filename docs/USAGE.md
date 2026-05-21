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

## Advanced Templating (Subtemplates)

The generator supports **recursive inheritance**, allowing you to create specialized sub-templates or override layouts directly in your Markdown posts.

### 1. Using a Sub-template
Select a specialized template in your Markdown frontmatter:

```yaml
---
title: My Blog Post
template: src/templates/blog.html.temp
---
```

If `blog.html.temp` extends `page.html.temp`, your post will automatically inherit the site shell.

### 2. Direct Inheritance in Markdown
Override specific blocks directly in your post without creating a new template:

```yaml
---
title: One-off Special Page
extends: src/templates/page.html.temp
---
~{block content_block}~
  <div class="super-special">
    <h1>{{ title }}</h1>
    {{ content }}
  </div>
~{endblock}~

This content will be injected into {{ content }} in the block above.
```

### 3. Creating a Sub-template (`.html.temp`)
Use a meta block at the top of your template to extend another:

```html
<!-- meta start -->
<!-- extends: src/templates/page.html.temp -->
<!-- meta end -->

~{block sidebar}~
  <div class="custom-sidebar">...</div>
~{endblock}~
```

This makes your template a "child" that can be used by Markdown pages while inheriting the "parent" structure.

#!/usr/bin/env python3
"""Notes-only CMS for the Gen0/fleench.me repository.

This app intentionally stays simple:
- manages markdown files under src/notes/
- uses the existing frontmatter format expected by gen.py
- can trigger a local static-site build on demand
- authentication is disabled by default for testing

Run:
    python3 app.py
or:
    flask --app app run --debug

Optional environment variables:
    CMS_REQUIRE_AUTH=1            # enable lightweight shared-secret auth
    CMS_TOKEN=shared-secret       # required when CMS_REQUIRE_AUTH=1
    CMS_HOST=127.0.0.1
    CMS_PORT=5000
    CMS_DEBUG=1
"""
from __future__ import annotations

import os
import re
import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, redirect, render_template_string, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
NOTES_DIR = SRC_DIR / "notes"
GEN_SCRIPT = BASE_DIR / "gen.py"
DEFAULT_TEMPLATE = "src/note.html.temp"
DEFAULT_TYPE = "note"

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)


@dataclass
class NoteRecord:
    slug: str
    relative_path: str
    title: str
    date: str
    body: str
    file_path: Path


PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0f1115;
      --panel: #171a21;
      --muted: #98a2b3;
      --text: #e5e7eb;
      --accent: #7c9cff;
      --border: #2b3240;
      --danger: #ff7b72;
      --ok: #57d38c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
    .topbar {
      display: flex; gap: 12px; flex-wrap: wrap; align-items: center; justify-content: space-between;
      margin-bottom: 20px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 18px;
    }
    h1, h2, h3 { margin-top: 0; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .muted { color: var(--muted); }
    .grid { display: grid; grid-template-columns: 1fr; gap: 18px; }
    @media (min-width: 900px) {
      .grid.notes { grid-template-columns: 1.1fr 1.9fr; }
    }
    label { display: block; margin: 0 0 6px; font-weight: 600; }
    input, textarea {
      width: 100%; padding: 10px 12px; border-radius: 10px;
      border: 1px solid var(--border); background: #0d1016; color: var(--text);
      margin-bottom: 12px;
    }
    textarea { min-height: 320px; resize: vertical; font-family: ui-monospace, monospace; }
    .row { display: grid; grid-template-columns: 1fr; gap: 12px; }
    @media (min-width: 760px) { .row { grid-template-columns: 1fr 1fr; } }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; }
    button, .button {
      display: inline-block; cursor: pointer; border: 1px solid var(--border);
      background: var(--accent); color: #09111f; font-weight: 700;
      padding: 10px 14px; border-radius: 10px;
    }
    button.secondary, .button.secondary { background: transparent; color: var(--text); }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
    code, pre { background: #0d1016; border-radius: 8px; }
    pre { padding: 12px; overflow: auto; }
    .flash { padding: 12px 14px; border-radius: 10px; margin-bottom: 14px; border: 1px solid var(--border); }
    .flash.success { border-color: #1f6f46; color: #b5f3cb; }
    .flash.error { border-color: #7f1d1d; color: #fecaca; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <div>
        <h1 style="margin-bottom: 4px;">Gen0 Notes CMS</h1>
        <div class="muted">Notes only. Markdown files under <code>src/notes/</code>.</div>
      </div>
      <div class="actions">
        {% if authed %}
          <a class="button secondary" href="{{ url_for('index') }}">Notes</a>
          <a class="button secondary" href="{{ url_for('new_note') }}">New Note</a>
          <form method="post" action="{{ url_for('build_site') }}">
            <button type="submit">Run Build</button>
          </form>
          {% if auth_enabled %}
          <form method="post" action="{{ url_for('logout') }}">
            <button type="submit" class="secondary">Logout</button>
          </form>
          {% endif %}
        {% endif %}
      </div>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    {{ body|safe }}
  </div>
</body>
</html>
"""

LOGIN_BODY = """
<div class="panel" style="max-width: 420px; margin: 40px auto;">
  <h2>Authentication required</h2>
  <p class="muted">Authentication is disabled by default. To enable it, set <code>CMS_REQUIRE_AUTH=1</code> and <code>CMS_TOKEN</code>.</p>
  <form method="post">
    <label for="token">CMS token</label>
    <input id="token" name="token" type="password" autocomplete="current-password" required>
    <div class="actions">
      <button type="submit">Login</button>
    </div>
  </form>
</div>
"""


def auth_enabled() -> bool:
    return os.environ.get("CMS_REQUIRE_AUTH", "0") == "1"


def render_page(title: str, body: str) -> str:
    return render_template_string(PAGE_TEMPLATE, title=title, body=body, authed=is_authenticated(), auth_enabled=auth_enabled())


def is_authenticated() -> bool:
    if not auth_enabled():
        return True
    configured = os.environ.get("CMS_TOKEN")
    if not configured:
        return True
    return session.get("cms_authed") is True


def require_auth() -> None:
    if not is_authenticated():
        abort(401)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or datetime.now().strftime("%H%M")


def normalize_note_slug(value: str, date_str: str) -> str:
    candidate = value.strip()
    if candidate:
        return candidate
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M").strftime("%H%M")
    except ValueError:
        return datetime.now().strftime("%H%M")


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    marker = "\n---\n"
    end = raw.find(marker, 4)
    if end == -1:
        return {}, raw
    header = raw[4:end]
    body = raw[end + len(marker):]
    data: dict[str, str] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        data[key.strip()] = value
    return data, body.lstrip("\n")


def quote_yaml(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def make_note_path(date_str: str, slug: str) -> Path:
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
    return NOTES_DIR / dt.strftime("%Y-%m-%d") / f"{slug}.md"


def build_markdown(date_str: str, body: str) -> str:
    normalized_body = body.rstrip() + "\n"
    return (
        "---\n"
        f"date: {date_str}\n"
        f"type: {DEFAULT_TYPE}\n"
        f"template: {DEFAULT_TEMPLATE}\n"
        "---\n\n"
        f"{normalized_body}"
    )


def load_note(path: Path) -> NoteRecord:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    date = meta.get("date") or infer_date_from_path(path)
    title = path.stem
    return NoteRecord(
        slug=path.stem,
        relative_path=path.relative_to(BASE_DIR).as_posix(),
        title=title,
        date=date,
        body=body.rstrip("\n"),
        file_path=path,
    )


def infer_date_from_path(path: Path) -> str:
    parts = path.relative_to(NOTES_DIR).parts
    if len(parts) >= 2:
        day = parts[0]
        time = path.stem
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) and re.fullmatch(r"\d{4}", time):
            return f"{day}T{time[:2]}:{time[2:]}"
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def list_notes() -> list[NoteRecord]:
    notes = [load_note(path) for path in NOTES_DIR.rglob("*.md")]
    notes.sort(key=lambda note: (note.date, note.relative_path), reverse=True)
    return notes


def run_build_command() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["python3", str(GEN_SCRIPT), "build"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return True, output or "Build completed successfully."
    except subprocess.CalledProcessError as exc:
        output = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        return False, output or f"Build failed with exit code {exc.returncode}."


@app.errorhandler(401)
def unauthorized(_: Any):
    return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    if not auth_enabled() or not os.environ.get("CMS_TOKEN"):
        return redirect(url_for("index"))
    if request.method == "POST":
        submitted = request.form.get("token", "")
        if secrets.compare_digest(submitted, os.environ.get("CMS_TOKEN", "")):
            session["cms_authed"] = True
            flash("Authentication successful.", "success")
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid token.", "error")
    return render_page("Login", LOGIN_BODY)


@app.post("/logout")
def logout():
    session.pop("cms_authed", None)
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/")
def index():
    require_auth()
    rows = []
    for note in list_notes():
        rows.append(
            f"<tr>"
            f"<td><strong>{note.title}</strong><br><span class='muted'>{note.relative_path}</span></td>"
            f"<td>{note.date}</td>"
            f"<td>{note.slug}</td>"
            f"<td><a href='{url_for('edit_note', relative_path=note.relative_path)}'>Edit</a></td>"
            f"</tr>"
        )
    body = f"""
    <div class='panel'>
      <h2>Notes</h2>
      <p class='muted'>This CMS only manages notes in <code>src/notes/</code>.</p>
      <table>
        <thead><tr><th>Note</th><th>Date</th><th>Slug</th><th>Action</th></tr></thead>
        <tbody>{''.join(rows) or '<tr><td colspan="4">No notes found.</td></tr>'}</tbody>
      </table>
    </div>
    """
    return render_page("Notes", body)


@app.route("/notes/new", methods=["GET", "POST"])
def new_note():
    require_auth()
    now = datetime.now()
    defaults = {
        "date": now.strftime("%Y-%m-%dT%H:%M"),
        "slug": now.strftime("%H%M"),
        "body": "",
        "build_after": "1",
    }
    if request.method == "POST":
        date_str = request.form.get("date", "").strip()
        slug = normalize_note_slug(request.form.get("slug", ""), date_str)
        body = request.form.get("body", "").rstrip()
        build_after = request.form.get("build_after") == "1"

        if not body or not date_str:
            flash("Date and body are required.", "error")
            defaults.update({"date": date_str, "slug": slug, "body": body})
        else:
            try:
                path = make_note_path(date_str, slug)
            except ValueError:
                flash("Date must use YYYY-MM-DDTHH:MM.", "error")
                defaults.update({"date": date_str, "slug": slug, "body": body})
            else:
                if path.exists():
                    flash(f"Note already exists at {path.relative_to(BASE_DIR)}.", "error")
                    defaults.update({"date": date_str, "slug": slug, "body": body})
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(build_markdown(date_str, body), encoding="utf-8")
                    flash(f"Created {path.relative_to(BASE_DIR)}.", "success")
                    if build_after:
                        ok, output = run_build_command()
                        flash("Build completed." if ok else "Build failed. See log below.", "success" if ok else "error")
                        return render_page("Build Result", f"<div class='panel'><h2>Build output</h2><pre>{output}</pre><p><a href='{url_for('edit_note', relative_path=path.relative_to(BASE_DIR).as_posix())}'>Edit note</a></p></div>")
                    return redirect(url_for("edit_note", relative_path=path.relative_to(BASE_DIR).as_posix()))

    return render_page("New Note", render_note_form("Create note", url_for("new_note"), defaults, create_mode=True))


@app.route("/notes/edit")
def edit_note():
    require_auth()
    rel = request.args.get("relative_path", "")
    path = (BASE_DIR / rel).resolve()
    if not str(path).startswith(str(NOTES_DIR.resolve())) or not path.exists() or path.suffix != ".md":
        abort(404)
    note = load_note(path)
    values = {
        "date": note.date,
        "slug": note.slug,
        "body": note.body,
        "relative_path": note.relative_path,
    }
    body = render_note_form("Edit note", url_for("update_note"), values, create_mode=False)
    body += f"<div class='panel'><h3>Current file</h3><code>{note.relative_path}</code></div>"
    return render_page(note.title, body)


@app.post("/notes/update")
def update_note():
    require_auth()
    rel = request.form.get("relative_path", "")
    original_path = (BASE_DIR / rel).resolve()
    if not str(original_path).startswith(str(NOTES_DIR.resolve())) or not original_path.exists() or original_path.suffix != ".md":
        abort(404)

    date_str = request.form.get("date", "").strip()
    slug = normalize_note_slug(request.form.get("slug", ""), date_str) or original_path.stem
    body = request.form.get("body", "").rstrip()
    build_after = request.form.get("build_after") == "1"

    if not date_str or not body:
        flash("Date and body are required.", "error")
        return redirect(url_for("edit_note", relative_path=rel))

    try:
        target_path = make_note_path(date_str, slug)
    except ValueError:
        flash("Date must use YYYY-MM-DDTHH:MM.", "error")
        return redirect(url_for("edit_note", relative_path=rel))

    if target_path != original_path and target_path.exists():
        flash(f"Cannot move note. Destination already exists: {target_path.relative_to(BASE_DIR)}", "error")
        return redirect(url_for("edit_note", relative_path=rel))

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(build_markdown(date_str, body), encoding="utf-8")
    if target_path != original_path:
        original_path.unlink()
        flash(f"Updated and moved note to {target_path.relative_to(BASE_DIR)}.", "success")
    else:
        flash(f"Updated {target_path.relative_to(BASE_DIR)}.", "success")

    if build_after:
        ok, output = run_build_command()
        flash("Build completed." if ok else "Build failed. See log below.", "success" if ok else "error")
        return render_page("Build Result", f"<div class='panel'><h2>Build output</h2><pre>{output}</pre><p><a href='{url_for('edit_note', relative_path=target_path.relative_to(BASE_DIR).as_posix())}'>Return to editor</a></p></div>")

    return redirect(url_for("edit_note", relative_path=target_path.relative_to(BASE_DIR).as_posix()))


@app.post("/build")
def build_site():
    require_auth()
    ok, output = run_build_command()
    flash("Build completed." if ok else "Build failed.", "success" if ok else "error")
    return render_page("Build Result", f"<div class='panel'><h2>Build output</h2><pre>{output}</pre><p><a href='{url_for('index')}'>Back to notes</a></p></div>")


def render_note_form(title: str, action: str, values: dict[str, str], create_mode: bool) -> str:
    checked = "checked" if values.get("build_after", "1") == "1" else ""
    slug_help = "Leave blank to use the note time as HHMM, matching the existing bot-style notes." if create_mode else "Changing slug or date will move the file. Leave blank to use the note time as HHMM."
    return f"""
    <div class='panel'>
      <h2>{title}</h2>
      <form method='post' action='{action}'>
        {'<input type="hidden" name="relative_path" value="' + values.get('relative_path', '') + '">' if not create_mode else ''}
        <div class='row'>
          <div>
            <label>Date/time</label>
            <input name='date' type='datetime-local' value='{html_escape(values.get('date', ''))}' required>
          </div>
          <div>
            <label>Slug / filename</label>
            <input name='slug' value='{html_escape(values.get('slug', ''))}'>
            <div class='muted'>{slug_help}</div>
          </div>
        </div>
        <label>Markdown body</label>
        <textarea name='body' required>{html_escape(values.get('body', ''))}</textarea>
        <label><input type='checkbox' name='build_after' value='1' {checked}> Run <code>python3 gen.py build</code> after saving</label>
        <div class='actions' style='margin-top: 14px;'>
          <button type='submit'>{'Create note' if create_mode else 'Save changes'}</button>
          <a class='button secondary' href='{url_for('index')}'>Cancel</a>
        </div>
      </form>
    </div>
    """


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


if __name__ == "__main__":
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    app.run(
        host=os.environ.get("CMS_HOST", "127.0.0.1"),
        port=int(os.environ.get("CMS_PORT", "5000")),
        debug=os.environ.get("CMS_DEBUG", "0") == "1",
    )

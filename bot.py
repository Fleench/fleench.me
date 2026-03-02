import asyncio
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MY_DISCORD_ID = os.getenv("MY_DISCORD_ID")
GUILD_ID = os.getenv("GUILD_ID")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is required in .env")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is required in .env")
if not MY_DISCORD_ID:
    raise RuntimeError("MY_DISCORD_ID is required in .env")

ALLOWED_USER_ID = int(MY_DISCORD_ID)
TARGET_GUILD_ID = int(GUILD_ID) if GUILD_ID else None
NOTES_ROOT = Path("src/notes")
WEBMENTION_STATE_PATH = Path(".webmention-state.json")
FED_BRIDGY_ENDPOINT = "https://fed.brid.gy/webmention"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def _note_path(now: datetime) -> Path:
    day_dir = NOTES_ROOT / now.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)

    candidate = day_dir / f"{now.strftime('%H%M')}.md"
    if not candidate.exists():
        return candidate
    return day_dir / f"{now.strftime('%H%M%S')}.md"


def _write_note(content: str, note_type: str, template: str, reply_to: str | None = None) -> Path:
    now = datetime.now()
    path = _note_path(now)

    frontmatter_lines = [
        "---",
        f"date: {now.isoformat(timespec='minutes')}",
        f"type: {note_type}",
        f"template: {template}",
    ]
    if reply_to:
        frontmatter_lines.append(f"reply_to: \"{reply_to}\"")
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    path.write_text(f"{frontmatter}\n\n{content.strip()}\n", encoding="utf-8")
    return path


def _commit_summary(content: str, note_type: str) -> str:
    words = [
        "".join(ch for ch in token if ch.isalnum() or ch in "-_")
        for token in content.lower().split()
    ]
    words = [word for word in words if word]

    if not words:
        return f"add {note_type} update"

    summary_words = ["add", note_type, *words[:3]]
    return " ".join(summary_words[:5])


def _load_webmention_state() -> dict:
    if not WEBMENTION_STATE_PATH.exists():
        return {"version": 1, "queue": [], "published": [], "current_links": {}}

    try:
        raw = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "queue": [], "published": [], "current_links": {}}

    if not isinstance(raw, dict):
        return {"version": 1, "queue": [], "published": [], "current_links": {}}

    raw.setdefault("version", 1)
    raw.setdefault("queue", [])
    raw.setdefault("published", [])
    raw.setdefault("current_links", {})
    return raw


def _save_webmention_state(state: dict) -> None:
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _queue_status_message() -> str:
    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]

    lines = [
        f"Queued webmentions: {len(queue)}",
        f"Published webmentions: {len(published)}",
    ]

    if queue:
        lines.append("\nNext queued items:")
        for item in queue[:10]:
            source = str(item.get("source", ""))
            target = str(item.get("target", ""))
            lines.append(f"- {source} -> {target}")

    return "\n".join(lines)


def _publish_queued_webmentions() -> tuple[int, int, list[str]]:
    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]

    sent = 0
    failed = 0
    errors: list[str] = []
    remaining: list[dict] = []

    for item in queue:
        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        if not source or not target:
            continue

        event = str(item.get("event", "added") or "added").strip()

        payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
        request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(request, timeout=15):
                sent += 1
                item["event"] = event
                item["published_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                published.append(item)
        except urllib.error.URLError as exc:
            failed += 1
            remaining.append(item)
            errors.append(f"[{event}] {source} -> {target}: {exc}")

    state["queue"] = remaining
    state["published"] = published
    _save_webmention_state(state)
    return sent, failed, errors


async def _publish(path: Path, content: str, note_type: str) -> str:
    summary = await asyncio.to_thread(_commit_summary, content, note_type)
    await asyncio.to_thread(_run, ["python3", "gen.py", "build"])
    await asyncio.to_thread(
        _run,
        [
            "git",
            "add",
            str(path),
            "dist",
            "src/note.html.temp",
            "src/reply.html.temp",
            "config.yml",
            "gen.py",
            "scripts/build_notes.py",
            ".webmention-state.json",
        ],
    )
    await asyncio.to_thread(_run, ["git", "commit", "-m", summary])
    await asyncio.to_thread(_run, ["git", "push"])
    sent, failed, _errors = await asyncio.to_thread(_publish_queued_webmentions)
    return f"{summary} (Pings sent: {sent}, failed: {failed})"


def _is_allowed(interaction: discord.Interaction) -> bool:
    return interaction.user.id == ALLOWED_USER_ID


def _author_is_allowed(user_id: int) -> bool:
    return user_id == ALLOWED_USER_ID


async def _sync_commands() -> int:
    if TARGET_GUILD_ID:
        guild = discord.Object(id=TARGET_GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        return len(synced)

    synced = await bot.tree.sync()
    return len(synced)


@app_commands.check(_is_allowed)
@app_commands.command(name="note", description="Create and publish a short note")
@app_commands.describe(content="The note content")
async def note(interaction: discord.Interaction, content: str) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        path = await asyncio.to_thread(_write_note, content, "note", "src/note.html.temp", None)
        summary = await _publish(path, content, "note")
        await interaction.followup.send(f"✅ Published note: `{summary}`", ephemeral=True)
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or str(exc))[-1500:]
        await interaction.followup.send(f"❌ Git/build error: {message}", ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"❌ Unexpected error: {exc}", ephemeral=True)


@app_commands.check(_is_allowed)
@app_commands.command(name="reply", description="Create and publish a reply note")
@app_commands.describe(url="The URL you are replying to", content="Your reply content")
async def reply(interaction: discord.Interaction, url: str, content: str) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        path = await asyncio.to_thread(_write_note, content, "reply", "src/reply.html.temp", url)
        summary = await _publish(path, content, "reply")
        await interaction.followup.send(f"✅ Published reply: `{summary}`", ephemeral=True)
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or str(exc))[-1500:]
        await interaction.followup.send(f"❌ Git/build error: {message}", ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"❌ Unexpected error: {exc}", ephemeral=True)


@app_commands.check(_is_allowed)
@app_commands.command(name="queue", description="Show queued webmentions")
async def queue(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    message = await asyncio.to_thread(_queue_status_message)
    await interaction.followup.send(f"```\n{message[:1800]}\n```", ephemeral=True)


@app_commands.check(_is_allowed)
@app_commands.command(name="publish", description="Publish queued webmentions to fed.brid.gy")
async def publish(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    sent, failed, errors = await asyncio.to_thread(_publish_queued_webmentions)
    response = [f"Sent: {sent}", f"Failed: {failed}"]
    if errors:
        response.append("\nFailures:")
        response.extend([f"- {err}" for err in errors[:8]])
    body = '\n'.join(response)[:1800]
    await interaction.followup.send(f"```\n{body}\n```", ephemeral=True)


@app_commands.check(_is_allowed)
@app_commands.command(name="commands", description="Force reload slash commands")
async def reload_commands(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        synced_count = await _sync_commands()
        scope = f"guild {TARGET_GUILD_ID}" if TARGET_GUILD_ID else "globally"
        await interaction.followup.send(
            f"✅ Reloaded {synced_count} slash command(s) {scope}.",
            ephemeral=True,
        )
    except Exception as exc:
        await interaction.followup.send(f"❌ Command reload error: {exc}", ephemeral=True)


@bot.command(name="note")
async def note_prefix(ctx: commands.Context, *, content: str) -> None:
    if not _author_is_allowed(ctx.author.id):
        await ctx.send("⛔ You are not authorized to use this command.")
        return

    try:
        path = await asyncio.to_thread(_write_note, content, "note", "src/note.html.temp", None)
        summary = await _publish(path, content, "note")
        await ctx.send(f"✅ Published note: `{summary}`")
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or str(exc))[-1500:]
        await ctx.send(f"❌ Git/build error: {message}")
    except Exception as exc:
        await ctx.send(f"❌ Unexpected error: {exc}")


@bot.command(name="reply")
async def reply_prefix(ctx: commands.Context, url: str, *, content: str) -> None:
    if not _author_is_allowed(ctx.author.id):
        await ctx.send("⛔ You are not authorized to use this command.")
        return

    try:
        path = await asyncio.to_thread(_write_note, content, "reply", "src/reply.html.temp", url)
        summary = await _publish(path, content, "reply")
        await ctx.send(f"✅ Published reply: `{summary}`")
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or str(exc))[-1500:]
        await ctx.send(f"❌ Git/build error: {message}")
    except Exception as exc:
        await ctx.send(f"❌ Unexpected error: {exc}")


@bot.command(name="queue")
async def queue_prefix(ctx: commands.Context) -> None:
    if not _author_is_allowed(ctx.author.id):
        await ctx.send("⛔ You are not authorized to use this command.")
        return
    message = await asyncio.to_thread(_queue_status_message)
    await ctx.send(f"```\n{message[:1800]}\n```")


@bot.command(name="publish")
async def publish_prefix(ctx: commands.Context) -> None:
    if not _author_is_allowed(ctx.author.id):
        await ctx.send("⛔ You are not authorized to use this command.")
        return
    sent, failed, errors = await asyncio.to_thread(_publish_queued_webmentions)
    response = [f"Sent: {sent}", f"Failed: {failed}"]
    if errors:
        response.append("\nFailures:")
        response.extend([f"- {err}" for err in errors[:8]])
    body = '\n'.join(response)[:1800]
    await ctx.send(f"```\n{body}\n```")


@bot.command(name="commands")
async def commands_prefix(ctx: commands.Context) -> None:
    if not _author_is_allowed(ctx.author.id):
        await ctx.send("⛔ You are not authorized to use this command.")
        return

    try:
        synced_count = await _sync_commands()
        scope = f"guild {TARGET_GUILD_ID}" if TARGET_GUILD_ID else "globally"
        await ctx.send(f"✅ Reloaded {synced_count} slash command(s) {scope}.")
    except Exception as exc:
        await ctx.send(f"❌ Command reload error: {exc}")


@note.error
@reply.error
@queue.error
@publish.error
async def command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.CheckFailure):
        message = "⛔ You are not authorized to use this command."
    else:
        message = f"❌ Command error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@bot.event
async def setup_hook() -> None:
    if TARGET_GUILD_ID:
        guild = discord.Object(id=TARGET_GUILD_ID)
        bot.tree.add_command(note, guild=guild)
        bot.tree.add_command(reply, guild=guild)
        bot.tree.add_command(queue, guild=guild)
        bot.tree.add_command(publish, guild=guild)
        bot.tree.add_command(reload_commands, guild=guild)
        synced_count = await _sync_commands()
        print(f"Synced {synced_count} command(s) to guild {TARGET_GUILD_ID}")
    else:
        bot.tree.add_command(note)
        bot.tree.add_command(reply)
        bot.tree.add_command(queue)
        bot.tree.add_command(publish)
        bot.tree.add_command(reload_commands)
        synced_count = await _sync_commands()
        print(f"Synced {synced_count} global command(s)")


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} (id={bot.user.id if bot.user else 'unknown'})")


bot.run(DISCORD_TOKEN)

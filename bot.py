import asyncio
import os
import subprocess
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

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

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
groq_client = Groq(api_key=GROQ_API_KEY)


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
    completion = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": (
                    "Create a concise 3-5 word summary for a git commit message. "
                    "Return only the summary text without punctuation."
                ),
            },
            {"role": "user", "content": f"Type: {note_type}\nContent: {content}"},
        ],
        temperature=0.2,
    )
    summary = (completion.choices[0].message.content or "").strip().splitlines()[0]
    words = summary.split()
    if len(words) < 3 or len(words) > 5:
        return f"add {note_type} update"
    return " ".join(words)


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
        ],
    )
    await asyncio.to_thread(_run, ["git", "commit", "-m", summary])
    await asyncio.to_thread(_run, ["git", "push"])
    return summary


def _is_allowed(interaction: discord.Interaction) -> bool:
    return interaction.user.id == ALLOWED_USER_ID


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


@note.error
@reply.error
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
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {TARGET_GUILD_ID}")
    else:
        bot.tree.add_command(note)
        bot.tree.add_command(reply)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global command(s)")


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)

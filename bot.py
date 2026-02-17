import asyncio
import json
import os
import re
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
GUILD_ID = os.getenv("GUILD_ID")
MY_DISCORD_ID = os.getenv("MY_DISCORD_ID")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is required in .env")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is required in .env")
if not GUILD_ID:
    raise RuntimeError("GUILD_ID is required in .env")
if not MY_DISCORD_ID:
    raise RuntimeError("MY_DISCORD_ID is required in .env")


ALLOWED_USER_ID = int(MY_DISCORD_ID)
TARGET_GUILD_ID = int(GUILD_ID)
NOTES_DIR = Path("./src/notes")
SYSTEM_PROMPT = (
    "You are a helpful assistant that summarizes short notes into a clean, "
    "3-5 word URL-friendly slug and a concise Git commit message. "
    "Return only a JSON object with keys 'slug' and 'summary'."
)


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
groq_client = Groq(api_key=GROQ_API_KEY)


def _sanitize_slug(raw_slug: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9-]+", "-", raw_slug.strip().lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "note"


def _run_subprocess(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def _build_note_file(content: str, slug: str) -> tuple[Path, str]:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    date_part = now.strftime("%Y-%m-%d")
    filename = f"{date_part}-{slug}.md"
    file_path = NOTES_DIR / filename

    title = slug.replace("-", " ").title()
    frontmatter = (
        "---\n"
        f"date: {date_part}\n"
        f'title: "{title}"\n'
        "---\n\n"
    )

    file_path.write_text(frontmatter + content.strip() + "\n", encoding="utf-8")
    return file_path, title


def _generate_slug_and_summary(note_content: str) -> tuple[str, str]:
    completion = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": note_content},
        ],
        temperature=0.2,
    )

    raw_text = completion.choices[0].message.content.strip()

    parsed = json.loads(raw_text)
    slug = _sanitize_slug(parsed.get("slug", "note"))
    summary = parsed.get("summary", "Add note").strip() or "Add note"
    return slug, summary


@app_commands.check(lambda interaction: interaction.user.id == ALLOWED_USER_ID)
@bot.tree.command(
    name="note",
    description="Create a note, rebuild site, and push changes.",
    guild=discord.Object(id=TARGET_GUILD_ID),
)
@app_commands.describe(content="Note content to publish")
async def note(interaction: discord.Interaction, content: str) -> None:
    await interaction.response.defer(thinking=True)

    try:
        slug, summary = await asyncio.to_thread(_generate_slug_and_summary, content)
        await asyncio.to_thread(_build_note_file, content, slug)

        await asyncio.to_thread(_run_subprocess, ["python3", "gen.py"])
        await asyncio.to_thread(_run_subprocess, ["git", "add", "."])
        await asyncio.to_thread(_run_subprocess, ["git", "commit", "-m", summary])
        await asyncio.to_thread(_run_subprocess, ["git", "push"])

        await interaction.followup.send(
            f"✅ Note '{summary}' processed. Site rebuilt and pushed.",
            ephemeral=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        message = stderr[-1500:] if stderr else str(exc)
        await interaction.followup.send(
            f"❌ Build or git operation failed: {message}",
            ephemeral=True,
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        await interaction.followup.send(
            f"❌ Groq response parsing failed: {exc}",
            ephemeral=True,
        )
    except Exception as exc:
        await interaction.followup.send(
            f"❌ Unexpected error: {exc}",
            ephemeral=True,
        )


@note.error
async def note_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.CheckFailure):
        if interaction.response.is_done():
            await interaction.followup.send(
                "⛔ You are not authorized to use this command.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "⛔ You are not authorized to use this command.",
                ephemeral=True,
            )
    else:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Command error: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Command error: {error}", ephemeral=True)


@bot.event
async def on_ready() -> None:
    guild = discord.Object(id=TARGET_GUILD_ID)
    synced = await bot.tree.sync(guild=guild)
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Synced {len(synced)} command(s) to guild {TARGET_GUILD_ID}")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)

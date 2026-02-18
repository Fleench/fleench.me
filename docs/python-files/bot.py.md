# bot.py — Annotated Source Snapshot

This file reproduces the Python source with heavy inline commentary for documentation and onboarding.

```python
# Line 1: import asyncio
import asyncio
# Line 2: import json
import json
# Line 3: import os
import os
# Line 4: import subprocess
import subprocess
# Line 5: import urllib.error
import urllib.error
# Line 6: import urllib.parse
import urllib.parse
# Line 7: import urllib.request
import urllib.request
# Line 8: from datetime import datetime
from datetime import datetime
# Line 9: from pathlib import Path
from pathlib import Path
# Line 10: (blank line used for readability / logical separation)

# Line 11: import discord
import discord
# Line 12: from discord import app_commands
from discord import app_commands
# Line 13: from discord.ext import commands
from discord.ext import commands
# Line 14: from dotenv import load_dotenv
from dotenv import load_dotenv
# Line 15: from groq import Groq
from groq import Groq
# Line 16: (blank line used for readability / logical separation)

# Line 17: load_dotenv()
load_dotenv()
# Line 18: (blank line used for readability / logical separation)

# Line 19: DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# Line 20: GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Line 21: MY_DISCORD_ID = os.getenv("MY_DISCORD_ID")
MY_DISCORD_ID = os.getenv("MY_DISCORD_ID")
# Line 22: GUILD_ID = os.getenv("GUILD_ID")
GUILD_ID = os.getenv("GUILD_ID")
# Line 23: (blank line used for readability / logical separation)

# Line 24: if not DISCORD_TOKEN:
if not DISCORD_TOKEN:
# Line 25: raise RuntimeError("DISCORD_TOKEN is required in .env")
    raise RuntimeError("DISCORD_TOKEN is required in .env")
# Line 26: if not GROQ_API_KEY:
if not GROQ_API_KEY:
# Line 27: raise RuntimeError("GROQ_API_KEY is required in .env")
    raise RuntimeError("GROQ_API_KEY is required in .env")
# Line 28: if not MY_DISCORD_ID:
if not MY_DISCORD_ID:
# Line 29: raise RuntimeError("MY_DISCORD_ID is required in .env")
    raise RuntimeError("MY_DISCORD_ID is required in .env")
# Line 30: (blank line used for readability / logical separation)

# Line 31: ALLOWED_USER_ID = int(MY_DISCORD_ID)
ALLOWED_USER_ID = int(MY_DISCORD_ID)
# Line 32: TARGET_GUILD_ID = int(GUILD_ID) if GUILD_ID else None
TARGET_GUILD_ID = int(GUILD_ID) if GUILD_ID else None
# Line 33: NOTES_ROOT = Path("src/notes")
NOTES_ROOT = Path("src/notes")
# Line 34: WEBMENTION_STATE_PATH = Path(".webmention-state.json")
WEBMENTION_STATE_PATH = Path(".webmention-state.json")
# Line 35: FED_BRIDGY_ENDPOINT = "https://fed.brid.gy/webmention"
FED_BRIDGY_ENDPOINT = "https://fed.brid.gy/webmention"
# Line 36: (blank line used for readability / logical separation)

# Line 37: intents = discord.Intents.default()
intents = discord.Intents.default()
# Line 38: intents.message_content = True
intents.message_content = True
# Line 39: bot = commands.Bot(command_prefix="!", intents=intents)
bot = commands.Bot(command_prefix="!", intents=intents)
# Line 40: groq_client = Groq(api_key=GROQ_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)
# Line 41: (blank line used for readability / logical separation)

# Line 42: (blank line used for readability / logical separation)

# Line 43: def _run(cmd: list[str]) -> None:
def _run(cmd: list[str]) -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 44: subprocess.run(cmd, check=True, capture_output=True, text=True)
    subprocess.run(cmd, check=True, capture_output=True, text=True)
# Line 45: (blank line used for readability / logical separation)

# Line 46: (blank line used for readability / logical separation)

# Line 47: def _note_path(now: datetime) -> Path:
def _note_path(now: datetime) -> Path:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 48: day_dir = NOTES_ROOT / now.strftime("%Y-%m-%d")
    day_dir = NOTES_ROOT / now.strftime("%Y-%m-%d")
# Line 49: day_dir.mkdir(parents=True, exist_ok=True)
    day_dir.mkdir(parents=True, exist_ok=True)
# Line 50: (blank line used for readability / logical separation)

# Line 51: candidate = day_dir / f"{now.strftime('%H%M')}.md"
    candidate = day_dir / f"{now.strftime('%H%M')}.md"
# Line 52: if not candidate.exists():
    if not candidate.exists():
# Line 53: return candidate
        return candidate
# Line 54: return day_dir / f"{now.strftime('%H%M%S')}.md"
    return day_dir / f"{now.strftime('%H%M%S')}.md"
# Line 55: (blank line used for readability / logical separation)

# Line 56: (blank line used for readability / logical separation)

# Line 57: def _write_note(content: str, note_type: str, template: str, reply_to: str | None = None) -> Path:
def _write_note(content: str, note_type: str, template: str, reply_to: str | None = None) -> Path:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 58: now = datetime.now()
    now = datetime.now()
# Line 59: path = _note_path(now)
    path = _note_path(now)
# Line 60: (blank line used for readability / logical separation)

# Line 61: frontmatter_lines = [
    frontmatter_lines = [
# Line 62: "---",
        "---",
# Line 63: f"date: {now.isoformat(timespec='minutes')}",
        f"date: {now.isoformat(timespec='minutes')}",
# Line 64: f"type: {note_type}",
        f"type: {note_type}",
# Line 65: f"template: {template}",
        f"template: {template}",
# Line 66: ]
    ]
# Line 67: if reply_to:
    if reply_to:
# Line 68: frontmatter_lines.append(f"reply_to: \"{reply_to}\"")
        frontmatter_lines.append(f"reply_to: \"{reply_to}\"")
# Line 69: frontmatter_lines.append("---")
    frontmatter_lines.append("---")
# Line 70: frontmatter = "\n".join(frontmatter_lines)
    frontmatter = "\n".join(frontmatter_lines)
# Line 71: (blank line used for readability / logical separation)

# Line 72: path.write_text(f"{frontmatter}\n\n{content.strip()}\n", encoding="utf-8")
    path.write_text(f"{frontmatter}\n\n{content.strip()}\n", encoding="utf-8")
# Line 73: return path
    return path
# Line 74: (blank line used for readability / logical separation)

# Line 75: (blank line used for readability / logical separation)

# Line 76: def _commit_summary(content: str, note_type: str) -> str:
def _commit_summary(content: str, note_type: str) -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 77: completion = groq_client.chat.completions.create(
    completion = groq_client.chat.completions.create(
# Line 78: model="llama-3.1-8b-instant",
        model="llama-3.1-8b-instant",
# Line 79: messages=[
        messages=[
# Line 80: {
            {
# Line 81: "role": "system",
                "role": "system",
# Line 82: "content": (
                "content": (
# Line 83: "Create a concise 3-5 word summary for a git commit message. "
                    "Create a concise 3-5 word summary for a git commit message. "
# Line 84: "Return only the summary text without punctuation."
                    "Return only the summary text without punctuation."
# Line 85: ),
                ),
# Line 86: },
            },
# Line 87: {"role": "user", "content": f"Type: {note_type}\nContent: {content}"},
            {"role": "user", "content": f"Type: {note_type}\nContent: {content}"},
# Line 88: ],
        ],
# Line 89: temperature=0.2,
        temperature=0.2,
# Line 90: )
    )
# Line 91: summary = (completion.choices[0].message.content or "").strip().splitlines()[0]
    summary = (completion.choices[0].message.content or "").strip().splitlines()[0]
# Line 92: words = summary.split()
    words = summary.split()
# Line 93: if len(words) < 3 or len(words) > 5:
    if len(words) < 3 or len(words) > 5:
# Line 94: return f"add {note_type} update"
        return f"add {note_type} update"
# Line 95: return " ".join(words)
    return " ".join(words)
# Line 96: (blank line used for readability / logical separation)

# Line 97: (blank line used for readability / logical separation)

# Line 98: def _load_webmention_state() -> dict:
def _load_webmention_state() -> dict:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 99: if not WEBMENTION_STATE_PATH.exists():
    if not WEBMENTION_STATE_PATH.exists():
# Line 100: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 101: (blank line used for readability / logical separation)

# Line 102: try:
    try:
# Line 103: raw = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
        raw = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
# Line 104: except Exception:
    except Exception:
# Line 105: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 106: (blank line used for readability / logical separation)

# Line 107: if not isinstance(raw, dict):
    if not isinstance(raw, dict):
# Line 108: return {"version": 1, "queue": [], "published": []}
        return {"version": 1, "queue": [], "published": []}
# Line 109: (blank line used for readability / logical separation)

# Line 110: raw.setdefault("version", 1)
    raw.setdefault("version", 1)
# Line 111: raw.setdefault("queue", [])
    raw.setdefault("queue", [])
# Line 112: raw.setdefault("published", [])
    raw.setdefault("published", [])
# Line 113: return raw
    return raw
# Line 114: (blank line used for readability / logical separation)

# Line 115: (blank line used for readability / logical separation)

# Line 116: def _save_webmention_state(state: dict) -> None:
def _save_webmention_state(state: dict) -> None:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 117: WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
# Line 118: (blank line used for readability / logical separation)

# Line 119: (blank line used for readability / logical separation)

# Line 120: def _queue_status_message() -> str:
def _queue_status_message() -> str:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 121: state = _load_webmention_state()
    state = _load_webmention_state()
# Line 122: queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
# Line 123: published = [item for item in state.get("published", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]
# Line 124: (blank line used for readability / logical separation)

# Line 125: lines = [
    lines = [
# Line 126: f"Queued webmentions: {len(queue)}",
        f"Queued webmentions: {len(queue)}",
# Line 127: f"Published webmentions: {len(published)}",
        f"Published webmentions: {len(published)}",
# Line 128: ]
    ]
# Line 129: (blank line used for readability / logical separation)

# Line 130: if queue:
    if queue:
# Line 131: lines.append("\nNext queued items:")
        lines.append("\nNext queued items:")
# Line 132: for item in queue[:10]:
        for item in queue[:10]:
# Line 133: source = str(item.get("source", ""))
            source = str(item.get("source", ""))
# Line 134: target = str(item.get("target", ""))
            target = str(item.get("target", ""))
# Line 135: lines.append(f"- {source} -> {target}")
            lines.append(f"- {source} -> {target}")
# Line 136: (blank line used for readability / logical separation)

# Line 137: return "\n".join(lines)
    return "\n".join(lines)
# Line 138: (blank line used for readability / logical separation)

# Line 139: (blank line used for readability / logical separation)

# Line 140: def _publish_queued_webmentions() -> tuple[int, int, list[str]]:
def _publish_queued_webmentions() -> tuple[int, int, list[str]]:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 141: state = _load_webmention_state()
    state = _load_webmention_state()
# Line 142: queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
# Line 143: published = [item for item in state.get("published", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]
# Line 144: (blank line used for readability / logical separation)

# Line 145: sent = 0
    sent = 0
# Line 146: failed = 0
    failed = 0
# Line 147: errors: list[str] = []
    errors: list[str] = []
# Line 148: remaining: list[dict] = []
    remaining: list[dict] = []
# Line 149: (blank line used for readability / logical separation)

# Line 150: for item in queue:
    for item in queue:
# Line 151: source = str(item.get("source", "")).strip()
        source = str(item.get("source", "")).strip()
# Line 152: target = str(item.get("target", "")).strip()
        target = str(item.get("target", "")).strip()
# Line 153: if not source or not target:
        if not source or not target:
# Line 154: continue
            continue
# Line 155: (blank line used for readability / logical separation)

# Line 156: payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
        payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
# Line 157: request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
        request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
# Line 158: request.add_header("Content-Type", "application/x-www-form-urlencoded")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
# Line 159: (blank line used for readability / logical separation)

# Line 160: try:
        try:
# Line 161: with urllib.request.urlopen(request, timeout=15):
            with urllib.request.urlopen(request, timeout=15):
# Line 162: sent += 1
                sent += 1
# Line 163: item["published_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                item["published_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
# Line 164: published.append(item)
                published.append(item)
# Line 165: except urllib.error.URLError as exc:
        except urllib.error.URLError as exc:
# Line 166: failed += 1
            failed += 1
# Line 167: remaining.append(item)
            remaining.append(item)
# Line 168: errors.append(f"{source} -> {target}: {exc}")
            errors.append(f"{source} -> {target}: {exc}")
# Line 169: (blank line used for readability / logical separation)

# Line 170: state["queue"] = remaining
    state["queue"] = remaining
# Line 171: state["published"] = published
    state["published"] = published
# Line 172: _save_webmention_state(state)
    _save_webmention_state(state)
# Line 173: return sent, failed, errors
    return sent, failed, errors
# Line 174: (blank line used for readability / logical separation)

# Line 175: (blank line used for readability / logical separation)

# Line 176: async def _publish(path: Path, content: str, note_type: str) -> str:
async def _publish(path: Path, content: str, note_type: str) -> str:
# Line 177: summary = await asyncio.to_thread(_commit_summary, content, note_type)
    summary = await asyncio.to_thread(_commit_summary, content, note_type)
# Line 178: await asyncio.to_thread(_run, ["python3", "gen.py", "build"])
    await asyncio.to_thread(_run, ["python3", "gen.py", "build"])
# Line 179: await asyncio.to_thread(
    await asyncio.to_thread(
# Line 180: _run,
        _run,
# Line 181: [
        [
# Line 182: "git",
            "git",
# Line 183: "add",
            "add",
# Line 184: str(path),
            str(path),
# Line 185: "dist",
            "dist",
# Line 186: "src/note.html.temp",
            "src/note.html.temp",
# Line 187: "src/reply.html.temp",
            "src/reply.html.temp",
# Line 188: "config.yml",
            "config.yml",
# Line 189: "gen.py",
            "gen.py",
# Line 190: "scripts/build_notes.py",
            "scripts/build_notes.py",
# Line 191: ".webmention-state.json",
            ".webmention-state.json",
# Line 192: ],
        ],
# Line 193: )
    )
# Line 194: await asyncio.to_thread(_run, ["git", "commit", "-m", summary])
    await asyncio.to_thread(_run, ["git", "commit", "-m", summary])
# Line 195: await asyncio.to_thread(_run, ["git", "push"])
    await asyncio.to_thread(_run, ["git", "push"])
# Line 196: sent, failed, _errors = await asyncio.to_thread(_publish_queued_webmentions)
    sent, failed, _errors = await asyncio.to_thread(_publish_queued_webmentions)
# Line 197: return f"{summary} (Pings sent: {sent}, failed: {failed})"
    return f"{summary} (Pings sent: {sent}, failed: {failed})"
# Line 198: (blank line used for readability / logical separation)

# Line 199: (blank line used for readability / logical separation)

# Line 200: def _is_allowed(interaction: discord.Interaction) -> bool:
def _is_allowed(interaction: discord.Interaction) -> bool:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 201: return interaction.user.id == ALLOWED_USER_ID
    return interaction.user.id == ALLOWED_USER_ID
# Line 202: (blank line used for readability / logical separation)

# Line 203: (blank line used for readability / logical separation)

# Line 204: def _author_is_allowed(user_id: int) -> bool:
def _author_is_allowed(user_id: int) -> bool:
# Commentary: Function definition starts here; following indented block implements this unit.
# Line 205: return user_id == ALLOWED_USER_ID
    return user_id == ALLOWED_USER_ID
# Line 206: (blank line used for readability / logical separation)

# Line 207: (blank line used for readability / logical separation)

# Line 208: async def _sync_commands() -> int:
async def _sync_commands() -> int:
# Line 209: if TARGET_GUILD_ID:
    if TARGET_GUILD_ID:
# Line 210: guild = discord.Object(id=TARGET_GUILD_ID)
        guild = discord.Object(id=TARGET_GUILD_ID)
# Line 211: synced = await bot.tree.sync(guild=guild)
        synced = await bot.tree.sync(guild=guild)
# Line 212: return len(synced)
        return len(synced)
# Line 213: (blank line used for readability / logical separation)

# Line 214: synced = await bot.tree.sync()
    synced = await bot.tree.sync()
# Line 215: return len(synced)
    return len(synced)
# Line 216: (blank line used for readability / logical separation)

# Line 217: (blank line used for readability / logical separation)

# Line 218: @app_commands.check(_is_allowed)
@app_commands.check(_is_allowed)
# Line 219: @app_commands.command(name="note", description="Create and publish a short note")
@app_commands.command(name="note", description="Create and publish a short note")
# Line 220: @app_commands.describe(content="The note content")
@app_commands.describe(content="The note content")
# Line 221: async def note(interaction: discord.Interaction, content: str) -> None:
async def note(interaction: discord.Interaction, content: str) -> None:
# Line 222: await interaction.response.defer(ephemeral=True, thinking=True)
    await interaction.response.defer(ephemeral=True, thinking=True)
# Line 223: (blank line used for readability / logical separation)

# Line 224: try:
    try:
# Line 225: path = await asyncio.to_thread(_write_note, content, "note", "src/note.html.temp", None)
        path = await asyncio.to_thread(_write_note, content, "note", "src/note.html.temp", None)
# Line 226: summary = await _publish(path, content, "note")
        summary = await _publish(path, content, "note")
# Line 227: await interaction.followup.send(f"✅ Published note: `{summary}`", ephemeral=True)
        await interaction.followup.send(f"✅ Published note: `{summary}`", ephemeral=True)
# Line 228: except subprocess.CalledProcessError as exc:
    except subprocess.CalledProcessError as exc:
# Line 229: message = (exc.stderr or str(exc))[-1500:]
        message = (exc.stderr or str(exc))[-1500:]
# Line 230: await interaction.followup.send(f"❌ Git/build error: {message}", ephemeral=True)
        await interaction.followup.send(f"❌ Git/build error: {message}", ephemeral=True)
# Line 231: except Exception as exc:
    except Exception as exc:
# Line 232: await interaction.followup.send(f"❌ Unexpected error: {exc}", ephemeral=True)
        await interaction.followup.send(f"❌ Unexpected error: {exc}", ephemeral=True)
# Line 233: (blank line used for readability / logical separation)

# Line 234: (blank line used for readability / logical separation)

# Line 235: @app_commands.check(_is_allowed)
@app_commands.check(_is_allowed)
# Line 236: @app_commands.command(name="reply", description="Create and publish a reply note")
@app_commands.command(name="reply", description="Create and publish a reply note")
# Line 237: @app_commands.describe(url="The URL you are replying to", content="Your reply content")
@app_commands.describe(url="The URL you are replying to", content="Your reply content")
# Line 238: async def reply(interaction: discord.Interaction, url: str, content: str) -> None:
async def reply(interaction: discord.Interaction, url: str, content: str) -> None:
# Line 239: await interaction.response.defer(ephemeral=True, thinking=True)
    await interaction.response.defer(ephemeral=True, thinking=True)
# Line 240: (blank line used for readability / logical separation)

# Line 241: try:
    try:
# Line 242: path = await asyncio.to_thread(_write_note, content, "reply", "src/reply.html.temp", url)
        path = await asyncio.to_thread(_write_note, content, "reply", "src/reply.html.temp", url)
# Line 243: summary = await _publish(path, content, "reply")
        summary = await _publish(path, content, "reply")
# Line 244: await interaction.followup.send(f"✅ Published reply: `{summary}`", ephemeral=True)
        await interaction.followup.send(f"✅ Published reply: `{summary}`", ephemeral=True)
# Line 245: except subprocess.CalledProcessError as exc:
    except subprocess.CalledProcessError as exc:
# Line 246: message = (exc.stderr or str(exc))[-1500:]
        message = (exc.stderr or str(exc))[-1500:]
# Line 247: await interaction.followup.send(f"❌ Git/build error: {message}", ephemeral=True)
        await interaction.followup.send(f"❌ Git/build error: {message}", ephemeral=True)
# Line 248: except Exception as exc:
    except Exception as exc:
# Line 249: await interaction.followup.send(f"❌ Unexpected error: {exc}", ephemeral=True)
        await interaction.followup.send(f"❌ Unexpected error: {exc}", ephemeral=True)
# Line 250: (blank line used for readability / logical separation)

# Line 251: (blank line used for readability / logical separation)

# Line 252: @app_commands.check(_is_allowed)
@app_commands.check(_is_allowed)
# Line 253: @app_commands.command(name="queue", description="Show queued webmentions")
@app_commands.command(name="queue", description="Show queued webmentions")
# Line 254: async def queue(interaction: discord.Interaction) -> None:
async def queue(interaction: discord.Interaction) -> None:
# Line 255: await interaction.response.defer(ephemeral=True, thinking=True)
    await interaction.response.defer(ephemeral=True, thinking=True)
# Line 256: message = await asyncio.to_thread(_queue_status_message)
    message = await asyncio.to_thread(_queue_status_message)
# Line 257: await interaction.followup.send(f"```\n{message[:1800]}\n```", ephemeral=True)
    await interaction.followup.send(f"```\n{message[:1800]}\n```", ephemeral=True)
# Line 258: (blank line used for readability / logical separation)

# Line 259: (blank line used for readability / logical separation)

# Line 260: @app_commands.check(_is_allowed)
@app_commands.check(_is_allowed)
# Line 261: @app_commands.command(name="publish", description="Publish queued webmentions to fed.brid.gy")
@app_commands.command(name="publish", description="Publish queued webmentions to fed.brid.gy")
# Line 262: async def publish(interaction: discord.Interaction) -> None:
async def publish(interaction: discord.Interaction) -> None:
# Line 263: await interaction.response.defer(ephemeral=True, thinking=True)
    await interaction.response.defer(ephemeral=True, thinking=True)
# Line 264: sent, failed, errors = await asyncio.to_thread(_publish_queued_webmentions)
    sent, failed, errors = await asyncio.to_thread(_publish_queued_webmentions)
# Line 265: response = [f"Sent: {sent}", f"Failed: {failed}"]
    response = [f"Sent: {sent}", f"Failed: {failed}"]
# Line 266: if errors:
    if errors:
# Line 267: response.append("\nFailures:")
        response.append("\nFailures:")
# Line 268: response.extend([f"- {err}" for err in errors[:8]])
        response.extend([f"- {err}" for err in errors[:8]])
# Line 269: body = '\n'.join(response)[:1800]
    body = '\n'.join(response)[:1800]
# Line 270: await interaction.followup.send(f"```\n{body}\n```", ephemeral=True)
    await interaction.followup.send(f"```\n{body}\n```", ephemeral=True)
# Line 271: (blank line used for readability / logical separation)

# Line 272: (blank line used for readability / logical separation)

# Line 273: @app_commands.check(_is_allowed)
@app_commands.check(_is_allowed)
# Line 274: @app_commands.command(name="commands", description="Force reload slash commands")
@app_commands.command(name="commands", description="Force reload slash commands")
# Line 275: async def reload_commands(interaction: discord.Interaction) -> None:
async def reload_commands(interaction: discord.Interaction) -> None:
# Line 276: await interaction.response.defer(ephemeral=True, thinking=True)
    await interaction.response.defer(ephemeral=True, thinking=True)
# Line 277: (blank line used for readability / logical separation)

# Line 278: try:
    try:
# Line 279: synced_count = await _sync_commands()
        synced_count = await _sync_commands()
# Line 280: scope = f"guild {TARGET_GUILD_ID}" if TARGET_GUILD_ID else "globally"
        scope = f"guild {TARGET_GUILD_ID}" if TARGET_GUILD_ID else "globally"
# Line 281: await interaction.followup.send(
        await interaction.followup.send(
# Line 282: f"✅ Reloaded {synced_count} slash command(s) {scope}.",
            f"✅ Reloaded {synced_count} slash command(s) {scope}.",
# Line 283: ephemeral=True,
            ephemeral=True,
# Line 284: )
        )
# Line 285: except Exception as exc:
    except Exception as exc:
# Line 286: await interaction.followup.send(f"❌ Command reload error: {exc}", ephemeral=True)
        await interaction.followup.send(f"❌ Command reload error: {exc}", ephemeral=True)
# Line 287: (blank line used for readability / logical separation)

# Line 288: (blank line used for readability / logical separation)

# Line 289: @bot.command(name="note")
@bot.command(name="note")
# Line 290: async def note_prefix(ctx: commands.Context, *, content: str) -> None:
async def note_prefix(ctx: commands.Context, *, content: str) -> None:
# Line 291: if not _author_is_allowed(ctx.author.id):
    if not _author_is_allowed(ctx.author.id):
# Line 292: await ctx.send("⛔ You are not authorized to use this command.")
        await ctx.send("⛔ You are not authorized to use this command.")
# Line 293: return
        return
# Line 294: (blank line used for readability / logical separation)

# Line 295: try:
    try:
# Line 296: path = await asyncio.to_thread(_write_note, content, "note", "src/note.html.temp", None)
        path = await asyncio.to_thread(_write_note, content, "note", "src/note.html.temp", None)
# Line 297: summary = await _publish(path, content, "note")
        summary = await _publish(path, content, "note")
# Line 298: await ctx.send(f"✅ Published note: `{summary}`")
        await ctx.send(f"✅ Published note: `{summary}`")
# Line 299: except subprocess.CalledProcessError as exc:
    except subprocess.CalledProcessError as exc:
# Line 300: message = (exc.stderr or str(exc))[-1500:]
        message = (exc.stderr or str(exc))[-1500:]
# Line 301: await ctx.send(f"❌ Git/build error: {message}")
        await ctx.send(f"❌ Git/build error: {message}")
# Line 302: except Exception as exc:
    except Exception as exc:
# Line 303: await ctx.send(f"❌ Unexpected error: {exc}")
        await ctx.send(f"❌ Unexpected error: {exc}")
# Line 304: (blank line used for readability / logical separation)

# Line 305: (blank line used for readability / logical separation)

# Line 306: @bot.command(name="reply")
@bot.command(name="reply")
# Line 307: async def reply_prefix(ctx: commands.Context, url: str, *, content: str) -> None:
async def reply_prefix(ctx: commands.Context, url: str, *, content: str) -> None:
# Line 308: if not _author_is_allowed(ctx.author.id):
    if not _author_is_allowed(ctx.author.id):
# Line 309: await ctx.send("⛔ You are not authorized to use this command.")
        await ctx.send("⛔ You are not authorized to use this command.")
# Line 310: return
        return
# Line 311: (blank line used for readability / logical separation)

# Line 312: try:
    try:
# Line 313: path = await asyncio.to_thread(_write_note, content, "reply", "src/reply.html.temp", url)
        path = await asyncio.to_thread(_write_note, content, "reply", "src/reply.html.temp", url)
# Line 314: summary = await _publish(path, content, "reply")
        summary = await _publish(path, content, "reply")
# Line 315: await ctx.send(f"✅ Published reply: `{summary}`")
        await ctx.send(f"✅ Published reply: `{summary}`")
# Line 316: except subprocess.CalledProcessError as exc:
    except subprocess.CalledProcessError as exc:
# Line 317: message = (exc.stderr or str(exc))[-1500:]
        message = (exc.stderr or str(exc))[-1500:]
# Line 318: await ctx.send(f"❌ Git/build error: {message}")
        await ctx.send(f"❌ Git/build error: {message}")
# Line 319: except Exception as exc:
    except Exception as exc:
# Line 320: await ctx.send(f"❌ Unexpected error: {exc}")
        await ctx.send(f"❌ Unexpected error: {exc}")
# Line 321: (blank line used for readability / logical separation)

# Line 322: (blank line used for readability / logical separation)

# Line 323: @bot.command(name="queue")
@bot.command(name="queue")
# Line 324: async def queue_prefix(ctx: commands.Context) -> None:
async def queue_prefix(ctx: commands.Context) -> None:
# Line 325: if not _author_is_allowed(ctx.author.id):
    if not _author_is_allowed(ctx.author.id):
# Line 326: await ctx.send("⛔ You are not authorized to use this command.")
        await ctx.send("⛔ You are not authorized to use this command.")
# Line 327: return
        return
# Line 328: message = await asyncio.to_thread(_queue_status_message)
    message = await asyncio.to_thread(_queue_status_message)
# Line 329: await ctx.send(f"```\n{message[:1800]}\n```")
    await ctx.send(f"```\n{message[:1800]}\n```")
# Line 330: (blank line used for readability / logical separation)

# Line 331: (blank line used for readability / logical separation)

# Line 332: @bot.command(name="publish")
@bot.command(name="publish")
# Line 333: async def publish_prefix(ctx: commands.Context) -> None:
async def publish_prefix(ctx: commands.Context) -> None:
# Line 334: if not _author_is_allowed(ctx.author.id):
    if not _author_is_allowed(ctx.author.id):
# Line 335: await ctx.send("⛔ You are not authorized to use this command.")
        await ctx.send("⛔ You are not authorized to use this command.")
# Line 336: return
        return
# Line 337: sent, failed, errors = await asyncio.to_thread(_publish_queued_webmentions)
    sent, failed, errors = await asyncio.to_thread(_publish_queued_webmentions)
# Line 338: response = [f"Sent: {sent}", f"Failed: {failed}"]
    response = [f"Sent: {sent}", f"Failed: {failed}"]
# Line 339: if errors:
    if errors:
# Line 340: response.append("\nFailures:")
        response.append("\nFailures:")
# Line 341: response.extend([f"- {err}" for err in errors[:8]])
        response.extend([f"- {err}" for err in errors[:8]])
# Line 342: body = '\n'.join(response)[:1800]
    body = '\n'.join(response)[:1800]
# Line 343: await ctx.send(f"```\n{body}\n```")
    await ctx.send(f"```\n{body}\n```")
# Line 344: (blank line used for readability / logical separation)

# Line 345: (blank line used for readability / logical separation)

# Line 346: @bot.command(name="commands")
@bot.command(name="commands")
# Line 347: async def commands_prefix(ctx: commands.Context) -> None:
async def commands_prefix(ctx: commands.Context) -> None:
# Line 348: if not _author_is_allowed(ctx.author.id):
    if not _author_is_allowed(ctx.author.id):
# Line 349: await ctx.send("⛔ You are not authorized to use this command.")
        await ctx.send("⛔ You are not authorized to use this command.")
# Line 350: return
        return
# Line 351: (blank line used for readability / logical separation)

# Line 352: try:
    try:
# Line 353: synced_count = await _sync_commands()
        synced_count = await _sync_commands()
# Line 354: scope = f"guild {TARGET_GUILD_ID}" if TARGET_GUILD_ID else "globally"
        scope = f"guild {TARGET_GUILD_ID}" if TARGET_GUILD_ID else "globally"
# Line 355: await ctx.send(f"✅ Reloaded {synced_count} slash command(s) {scope}.")
        await ctx.send(f"✅ Reloaded {synced_count} slash command(s) {scope}.")
# Line 356: except Exception as exc:
    except Exception as exc:
# Line 357: await ctx.send(f"❌ Command reload error: {exc}")
        await ctx.send(f"❌ Command reload error: {exc}")
# Line 358: (blank line used for readability / logical separation)

# Line 359: (blank line used for readability / logical separation)

# Line 360: @note.error
@note.error
# Line 361: @reply.error
@reply.error
# Line 362: @queue.error
@queue.error
# Line 363: @publish.error
@publish.error
# Line 364: async def command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
async def command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
# Line 365: if isinstance(error, app_commands.CheckFailure):
    if isinstance(error, app_commands.CheckFailure):
# Line 366: message = "⛔ You are not authorized to use this command."
        message = "⛔ You are not authorized to use this command."
# Line 367: else:
    else:
# Line 368: message = f"❌ Command error: {error}"
        message = f"❌ Command error: {error}"
# Line 369: (blank line used for readability / logical separation)

# Line 370: if interaction.response.is_done():
    if interaction.response.is_done():
# Line 371: await interaction.followup.send(message, ephemeral=True)
        await interaction.followup.send(message, ephemeral=True)
# Line 372: else:
    else:
# Line 373: await interaction.response.send_message(message, ephemeral=True)
        await interaction.response.send_message(message, ephemeral=True)
# Line 374: (blank line used for readability / logical separation)

# Line 375: (blank line used for readability / logical separation)

# Line 376: @bot.event
@bot.event
# Line 377: async def setup_hook() -> None:
async def setup_hook() -> None:
# Line 378: if TARGET_GUILD_ID:
    if TARGET_GUILD_ID:
# Line 379: guild = discord.Object(id=TARGET_GUILD_ID)
        guild = discord.Object(id=TARGET_GUILD_ID)
# Line 380: bot.tree.add_command(note, guild=guild)
        bot.tree.add_command(note, guild=guild)
# Line 381: bot.tree.add_command(reply, guild=guild)
        bot.tree.add_command(reply, guild=guild)
# Line 382: bot.tree.add_command(queue, guild=guild)
        bot.tree.add_command(queue, guild=guild)
# Line 383: bot.tree.add_command(publish, guild=guild)
        bot.tree.add_command(publish, guild=guild)
# Line 384: bot.tree.add_command(reload_commands, guild=guild)
        bot.tree.add_command(reload_commands, guild=guild)
# Line 385: synced_count = await _sync_commands()
        synced_count = await _sync_commands()
# Line 386: print(f"Synced {synced_count} command(s) to guild {TARGET_GUILD_ID}")
        print(f"Synced {synced_count} command(s) to guild {TARGET_GUILD_ID}")
# Line 387: else:
    else:
# Line 388: bot.tree.add_command(note)
        bot.tree.add_command(note)
# Line 389: bot.tree.add_command(reply)
        bot.tree.add_command(reply)
# Line 390: bot.tree.add_command(queue)
        bot.tree.add_command(queue)
# Line 391: bot.tree.add_command(publish)
        bot.tree.add_command(publish)
# Line 392: bot.tree.add_command(reload_commands)
        bot.tree.add_command(reload_commands)
# Line 393: synced_count = await _sync_commands()
        synced_count = await _sync_commands()
# Line 394: print(f"Synced {synced_count} global command(s)")
        print(f"Synced {synced_count} global command(s)")
# Line 395: (blank line used for readability / logical separation)

# Line 396: (blank line used for readability / logical separation)

# Line 397: @bot.event
@bot.event
# Line 398: async def on_ready() -> None:
async def on_ready() -> None:
# Line 399: print(f"Logged in as {bot.user} (id={bot.user.id if bot.user else 'unknown'})")
    print(f"Logged in as {bot.user} (id={bot.user.id if bot.user else 'unknown'})")
# Line 400: (blank line used for readability / logical separation)

# Line 401: (blank line used for readability / logical separation)

# Line 402: bot.run(DISCORD_TOKEN)
bot.run(DISCORD_TOKEN)
```

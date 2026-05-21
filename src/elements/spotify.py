import os
from pathlib import Path
from urllib.parse import quote_plus

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


FALLBACK_IMAGE = "/profile.png"


def fallback_value(search_query, item_type, return_playback):
    if return_playback:
        return f"https://open.spotify.com/search/{quote_plus(str(search_query))}"
    return FALLBACK_IMAGE


def load_env():
    """Manually parses a .env file in the script's directory."""
    env_path = Path(__file__).parent / ".env"
    config = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def main(**context):
    # 1. Load Credentials
    env = load_env()
    client_id = env.get("SPOTIFY_CLIENT_ID")
    client_secret = env.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        args = context.get("args", [])
        search_query = str(args[0]) if args else ""
        item_type = str(args[1]) if len(args) > 1 else "artist"
        return_playback = str(args[2]) == "1" if len(args) > 2 else False
        return fallback_value(search_query, item_type, return_playback)

    # 2. Parse Args from List (from gen.py)
    args = context.get("args", [])
    if not args:
        return FALLBACK_IMAGE

    search_query = str(args[0])

    raw_item_type = str(args[1]) if len(args) > 1 else "artist"
    normalized_type = raw_item_type.lower()
    is_id_lookup = False

    if normalized_type.endswith("id"):
        item_type = normalized_type[:-2]
        is_id_lookup = True
    elif normalized_type.startswith("id"):
        item_type = normalized_type[2:]
        is_id_lookup = True
    else:
        item_type = normalized_type

    if item_type not in ["artist", "album", "track"]:
        return fallback_value(search_query, item_type, False)

    return_playback = str(args[2]) == "1" if len(args) > 2 else False

    # 3. Initialize Spotipy
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        return fallback_value(search_query, item_type, return_playback)

    # 4. Search Logic
    try:
        if is_id_lookup:
            if item_type == "artist":
                item_data = sp.artist(search_query)
            elif item_type == "album":
                item_data = sp.album(search_query)
            else:
                item_data = sp.track(search_query)
        else:
            # q format 'type:name' helps narrow results
            q = f"{item_type}:{search_query}"
            results = sp.search(q=q, type=item_type, limit=1)

            items = results.get(f"{item_type}s", {}).get("items", [])
            if not items:
                return fallback_value(search_query, item_type, return_playback)

            item_data = items[0]

        # 5. Return Output
        if return_playback:
            url = item_data.get("external_urls", {}).get("spotify")
            return url if url else fallback_value(search_query, item_type, return_playback)

        # Get Images (Tracks nest images inside the album object)
        images = []
        if item_type == "track":
            images = item_data.get("album", {}).get("images", [])
        else:
            images = item_data.get("images", [])

        if images:
            return images[0]["url"]

        return fallback_value(search_query, item_type, return_playback)

    except Exception as e:
        return fallback_value(search_query, item_type, return_playback)

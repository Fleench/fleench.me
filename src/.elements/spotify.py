import os
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


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
        return "STP_ERR: Missing .env credentials"

    # 2. Parse Args from List (from gen.py)
    args = context.get("args", [])
    if not args:
        return "STP_ERR: No arguments provided in tag"

    search_query = str(args[0])

    # FIX: Force lowercase to prevent Spotify 400 errors
    item_type = str(args[1]).lower() if len(args) > 1 else "artist"
    return_playback = str(args[2]) == "1" if len(args) > 2 else False

    # 3. Initialize Spotipy
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        return f"STP_ERR: Auth failure - {str(e)}"

    # 4. Search Logic
    try:
        # q format 'type:name' helps narrow results
        q = f"{item_type}:{search_query}" if item_type in ["artist", "album", "track"] else search_query
        results = sp.search(q=q, type=item_type, limit=1)

        items = results.get(f"{item_type}s", {}).get("items", [])
        if not items:
            return f"STP_ERR: '{search_query}' not found in {item_type}s"

        item_data = items[0]

        # 5. Return Output
        if return_playback:
            url = item_data.get("external_urls", {}).get("spotify")
            return url if url else "STP_ERR: No playback URL available"

        # Get Images (Tracks nest images inside the album object)
        images = []
        if item_type == "track":
            images = item_data.get("album", {}).get("images", [])
        else:
            images = item_data.get("images", [])

        if images:
            return images[0]["url"]

        return f"STP_ERR: No images found for {search_query}"

    except Exception as e:
        return f"STP_ERR: API Call Failed - {str(e)}"
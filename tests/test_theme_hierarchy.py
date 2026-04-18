from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from theme_hierarchy import ThemeLibrary


def test_song_propagates_to_all_ancestors() -> None:
    library = ThemeLibrary()
    library.add_parent_theme("Synthwave", "Electronic")
    library.add_parent_theme("Electronic", "Mood")

    library.add_song_to_theme("Synthwave", "Nightcall")

    assert library.songs_for_theme("Synthwave") == {"Nightcall"}
    assert library.songs_for_theme("Electronic") == {"Nightcall"}
    assert library.songs_for_theme("Mood") == {"Nightcall"}


def test_song_propagates_to_multiple_unrelated_parents() -> None:
    library = ThemeLibrary()
    library.add_parent_theme("Roadtrip", "Energetic")
    library.add_parent_theme("Roadtrip", "Nostalgic")

    library.add_song_to_theme("Roadtrip", "Running Up That Hill")

    assert library.songs_for_theme("Roadtrip") == {"Running Up That Hill"}
    assert library.songs_for_theme("Energetic") == {"Running Up That Hill"}
    assert library.songs_for_theme("Nostalgic") == {"Running Up That Hill"}


def test_parent_link_backfills_existing_child_songs() -> None:
    library = ThemeLibrary()
    library.add_theme("Chill")
    library.add_song_to_theme("Chill", "Weightless")

    library.add_parent_theme("Chill", "Ambient")

    assert library.songs_for_theme("Ambient") == {"Weightless"}


def test_deep_nesting_supported() -> None:
    library = ThemeLibrary()
    last = "L0"
    library.add_theme(last)

    depth = 100
    for i in range(1, depth + 1):
        current = f"L{i}"
        library.add_parent_theme(last, current)
        last = current

    library.add_song_to_theme("L0", "Infinite Ladder")

    assert "Infinite Ladder" in library.songs_for_theme(f"L{depth}")


def test_cycle_is_rejected() -> None:
    library = ThemeLibrary()
    library.add_parent_theme("A", "B")
    library.add_parent_theme("B", "C")

    with pytest.raises(ValueError, match="create a cycle"):
        library.add_parent_theme("C", "A")

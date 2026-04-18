from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Theme:
    name: str
    parents: set[str] = field(default_factory=set)
    songs: set[str] = field(default_factory=set)


class ThemeLibrary:
    """Manage themes with multi-parent inheritance and song propagation.

    Rules:
    - Themes can have multiple parents.
    - Parent chains can be arbitrarily deep.
    - Adding a song to a theme also adds it to all ancestor themes.
    - Cycles are blocked when linking parent relationships.
    """

    def __init__(self) -> None:
        self._themes: dict[str, Theme] = {}
        self._children: dict[str, set[str]] = defaultdict(set)

    def add_theme(self, name: str) -> None:
        key = name.strip()
        if not key:
            raise ValueError("Theme name cannot be empty")
        self._themes.setdefault(key, Theme(name=key))

    def add_parent_theme(self, child: str, parent: str) -> None:
        child_name = child.strip()
        parent_name = parent.strip()
        if not child_name or not parent_name:
            raise ValueError("Theme names cannot be empty")
        if child_name == parent_name:
            raise ValueError("A theme cannot be its own parent")

        self.add_theme(child_name)
        self.add_theme(parent_name)

        if self._path_exists(parent_name, child_name):
            raise ValueError(
                f"Adding parent '{parent_name}' to '{child_name}' would create a cycle"
            )

        if parent_name in self._themes[child_name].parents:
            return

        self._themes[child_name].parents.add(parent_name)
        self._children[parent_name].add(child_name)

        # Backfill: songs already in child should also exist in the new parent chain.
        child_songs = self._themes[child_name].songs
        for song in child_songs:
            for ancestor in self._ancestor_closure(parent_name):
                self._themes[ancestor].songs.add(song)

    def add_song_to_theme(self, theme: str, song: str) -> None:
        theme_name = theme.strip()
        song_name = song.strip()
        if not theme_name:
            raise ValueError("Theme name cannot be empty")
        if not song_name:
            raise ValueError("Song name cannot be empty")

        self.add_theme(theme_name)
        for ancestor in self._ancestor_closure(theme_name):
            self._themes[ancestor].songs.add(song_name)

    def songs_for_theme(self, theme: str) -> set[str]:
        theme_name = theme.strip()
        if theme_name not in self._themes:
            return set()
        return set(self._themes[theme_name].songs)

    def parents_for_theme(self, theme: str) -> set[str]:
        theme_name = theme.strip()
        if theme_name not in self._themes:
            return set()
        return set(self._themes[theme_name].parents)

    def _ancestor_closure(self, theme: str) -> set[str]:
        visited: set[str] = set()
        stack = [theme]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._themes[current].parents)

        return visited

    def _path_exists(self, start: str, target: str) -> bool:
        if start == target:
            return True

        visited: set[str] = set()
        stack = [start]

        while stack:
            current = stack.pop()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._themes[current].parents)

        return False

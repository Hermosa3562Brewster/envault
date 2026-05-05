"""Search across vault profiles for keys or values."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.profiles import load_index
from envault.vault import load_vault


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchMatch:
    profile: str
    key: str
    value: str


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return len(self.matches) > 0

    def by_profile(self) -> dict[str, List[SearchMatch]]:
        grouped: dict[str, List[SearchMatch]] = {}
        for m in self.matches:
            grouped.setdefault(m.profile, []).append(m)
        return grouped


def search_key(
    master_key: str,
    pattern: str,
    *,
    base_dir: Optional[Path] = None,
    profile: Optional[str] = None,
    case_sensitive: bool = False,
) -> SearchResult:
    """Search for *pattern* in env variable names across registered profiles."""
    index = load_index(base_dir=base_dir)
    if not index:
        return SearchResult()

    needle = pattern if case_sensitive else pattern.lower()
    result = SearchResult()

    profiles_to_search = {profile: index[profile]} if profile else index

    for prof_name, vault_path in profiles_to_search.items():
        vault_path = Path(vault_path)
        if not vault_path.exists():
            continue
        try:
            env = load_vault(vault_path, master_key)
        except Exception as exc:
            raise SearchError(f"Could not decrypt profile '{prof_name}': {exc}") from exc

        for k, v in env.items():
            haystack = k if case_sensitive else k.lower()
            if needle in haystack:
                result.matches.append(SearchMatch(profile=prof_name, key=k, value=v))

    return result


def search_value(
    master_key: str,
    pattern: str,
    *,
    base_dir: Optional[Path] = None,
    profile: Optional[str] = None,
    case_sensitive: bool = False,
) -> SearchResult:
    """Search for *pattern* in env variable values across registered profiles."""
    index = load_index(base_dir=base_dir)
    if not index:
        return SearchResult()

    needle = pattern if case_sensitive else pattern.lower()
    result = SearchResult()

    profiles_to_search = {profile: index[profile]} if profile else index

    for prof_name, vault_path in profiles_to_search.items():
        vault_path = Path(vault_path)
        if not vault_path.exists():
            continue
        try:
            env = load_vault(vault_path, master_key)
        except Exception as exc:
            raise SearchError(f"Could not decrypt profile '{prof_name}': {exc}") from exc

        for k, v in env.items():
            haystack = v if case_sensitive else v.lower()
            if needle in haystack:
                result.matches.append(SearchMatch(profile=prof_name, key=k, value=v))

    return result

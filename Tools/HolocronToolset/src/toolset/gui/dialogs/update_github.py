from __future__ import annotations

from typing import Any

import requests

from loggerplus import RobustLogger

from utility.updater.github import GithubRelease


def fetch_fork_releases(
    fork_full_name: str,
    *,
    include_all: bool = False,
    include_prerelease: bool = False
) -> list[GithubRelease]:
    """Fetch releases for a specific fork."""
    url = f"https://api.github.com/repos/{fork_full_name}/releases"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        releases_json = response.json()
        if include_all:
            return [GithubRelease.from_json(r) for r in releases_json]
        return [
            GithubRelease.from_json(r) for r in releases_json
            if not r["draft"] and (include_prerelease or not r["prerelease"])
        ]
    except requests.HTTPError as e:
        RobustLogger().exception(f"Failed to fetch releases for {fork_full_name}: {e}")
        return []

def fetch_and_cache_forks() -> dict[str, list[GithubRelease]]:
    """Fetch all forks and their releases."""
    forks_cache: dict[str, list[GithubRelease]] = {}
    forks_url = "https://api.github.com/repos/NickHugi/PyKotor/forks"
    try:
        forks_response: requests.Response = requests.get(forks_url, timeout=15)
        forks_response.raise_for_status()
        forks_json: list[dict[str, Any]] = forks_response.json()
        for fork in forks_json:
            fork_owner_login: str = fork["owner"]["login"]
            fork_full_name: str = f"{fork_owner_login}/{fork['name']}"
            forks_cache[fork_full_name] = fetch_fork_releases(fork_full_name, include_all=True)
    except requests.HTTPError as e:
        RobustLogger().exception(f"Failed to fetch forks: {e}")
    return forks_cache

def filter_releases(
    releases: list[GithubRelease],
    *,
    include_prerelease: bool = False
) -> list[GithubRelease]:
    """Filter releases based on criteria."""
    filtered: list[GithubRelease] = [
        release for release in releases
        if not release.draft
        and "toolset" in release.tag_name.lower()
        and (include_prerelease or not release.prerelease)
    ]
    return filtered

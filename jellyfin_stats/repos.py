"""Dynamic repo enumeration + display-name humanization.

Replaces the hand-curated repos.yaml — every public, non-archived,
non-fork repo in the configured orgs gets a banner. No list to maintain.
"""

from typing import Iterator

from github import Github

# Orgs we sweep for banner-eligible repos. The two cover everything:
# `jellyfin` for the server, web, official clients, and most labs;
# `jellyfin-labs` for the small number of incubating projects hosted
# off the main org.
DEFAULT_ORGS = ["jellyfin", "jellyfin-labs"]

# Repos that aren't really part of the user-facing surface — boilerplate
# org-profile repo, pure forks the API misses, etc. Keep this small.
_SKIP_NAMES = {".github"}


def discover_repos(gh: Github, orgs: list[str] | None = None) -> Iterator[tuple[str, str, str]]:
    """Yield ``(repo_name, display_name, org)`` for every active public repo.

    Skips archived repos, forks, and the org-profile (`.github`) repo.
    Display names are derived from the repo name via :func:`humanize`.
    """
    for org_name in (orgs or DEFAULT_ORGS):
        org = gh.get_organization(org_name)
        for repo in org.get_repos(type="public"):
            if repo.archived or repo.fork or repo.name in _SKIP_NAMES:
                continue
            yield repo.name, humanize(repo.name), org_name


def humanize(repo_name: str) -> str:
    """Generate a display name from a repo name.

    Rules:
      - ``jellyfin`` → ``Jellyfin``
      - ``jellyfin-<x>`` → ``Jellyfin <X>`` (each dash-segment title-cased,
        but internal capitals preserved so ``jellyfin-iOS`` becomes
        ``Jellyfin iOS`` rather than ``Jellyfin Ios``)
      - Anything else (e.g. ``Swiftfin``, ``jellycon``) is returned with
        only its first letter capitalized if it was all-lowercase, else
        unchanged.
    """
    if repo_name == "jellyfin":
        return "Jellyfin"
    if repo_name.startswith("jellyfin-"):
        suffix = repo_name[len("jellyfin-"):]
        words = [_titlecase_keep_caps(w) for w in suffix.split("-") if w]
        return "Jellyfin " + " ".join(words)
    return repo_name if any(ch.isupper() for ch in repo_name) else repo_name.capitalize()


def _titlecase_keep_caps(word: str) -> str:
    """Capitalize all-lowercase words; preserve any word with internal caps.

    ``android`` → ``Android``; ``iOS`` → ``iOS``; ``webOS`` → ``webOS``.
    Lossy for all-lowercase compound words like ``androidtv`` (becomes
    ``Androidtv``) and intentionally-lowercase brand-style words — rare
    enough trade-offs to live with.
    """
    if not word or any(ch.isupper() for ch in word):
        return word
    return word.capitalize()

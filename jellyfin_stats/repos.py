"""Dynamic repo enumeration + display-name humanization.

Replaces the hand-curated repos.yaml — every public, non-archived,
non-fork repo in the configured orgs gets a banner. No list to maintain.
"""

from typing import Iterator

from github import Github

# Orgs we sweep for banner-eligible repos.
DEFAULT_ORGS = ["jellyfin", "jellyfin-labs"]

_SKIP_NAMES = {".github"}

DISPLAY_NAMES = {
    "jellyfin-web":                  "Jellyfin for Web",

    "jellyfin-android":              "Jellyfin for Android",
    "jellyfin-androidtv":            "Jellyfin for Android TV",
    "jellyfin-desktop":              "Jellyfin for Desktop",
    "jellyfin-iOS":                  "Jellyfin for iOS",
    "jellyfin-kodi":                 "Jellyfin for Kodi",
    "jellyfin-roku":                 "Jellyfin for Roku",
    "jellyfin-tizen":                "Jellyfin for Tizen",
    "jellyfin-webOS":                "Jellyfin for WebOS",
    "jellyfin-xbox":                 "Jellyfin for Xbox",

    "jellycon":                      "Jellyfin for Kodi Addon",
    "jellyfin-titanos":              "Jellyfin for TitanOS",
    "jellyfin-vega":                 "Jellyfin for VegaOS",
    "jellyfin-vue":                  "Jellyfin Vue",
    "Swiftfin":                      "Swiftfin",

    "jellyfin.org":                  "Jellyfin.org",

    "jellyfin-sdk-csharp":           "Jellyfin SDK for C#",
    "jellyfin-sdk-swift":            "Jellyfin SDK for Swift",
    "jellyfin-sdk-kotlin":           "Jellyfin SDK for Kotlin",
    "jellyfin-sdk-typescript":       "Jellyfin SDK for TypeScript",
    "jellyfin-apiclient-javascript": "Jellyfin SDK for JavaScript",
    "jellyfin-apiclient-python":     "Jellyfin SDK for Python",
}

WORD_CASING = {
    "sdk":     "SDK",
    "api":     "API",
    "mpv":     "MPV",
    "vlc":     "VLC",
    "ui":      "UI",
    "ux":      "UX",
    "tv":      "TV",
    "ios":     "iOS",
    "tvos":    "tvOS",
    "macos":   "macOS",
    "watchos": "watchOS",
    "ipados":  "iPadOS",
    "webos":   "WebOS",
    "titanos": "TitanOS",
    "vegaos":  "VegaOS",
}

_DISPLAY_NAMES_LOWER = {k.lower(): v for k, v in DISPLAY_NAMES.items()}


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

    Resolution order:
      1. Explicit override in ``DISPLAY_NAMES`` (case-insensitive lookup).
      2. ``jellyfin`` → ``Jellyfin``.
      3. ``jellyfin-<x>`` → ``Jellyfin <X>`` with each dash-segment passed
         through ``_apply_casing`` — known acronyms (SDK, API, …) and
         brand-cased words (iOS, tvOS, …) get their canonical form;
         everything else is title-cased while preserving any internal
         capitals.
      4. Anything else (e.g. ``Swiftfin``, ``jellycon``) is returned with
         its first letter capitalized if it was all-lowercase, else
         unchanged.
    """
    if (override := _DISPLAY_NAMES_LOWER.get(repo_name.lower())) is not None:
        return override
    if repo_name == "jellyfin":
        return "Jellyfin"
    if repo_name.startswith("jellyfin-"):
        suffix = repo_name[len("jellyfin-"):]
        words = [_apply_casing(w) for w in suffix.split("-") if w]
        return "Jellyfin " + " ".join(words)
    return repo_name if any(ch.isupper() for ch in repo_name) else repo_name.capitalize()


def _apply_casing(word: str) -> str:
    """Canonical casing for a name segment.

    Looks the lowercase form up in ``WORD_CASING`` first; falls back to
    capitalize-or-preserve so ``android`` → ``Android`` and ``iOS`` →
    ``iOS``. Lossy for all-lowercase compound words like ``androidtv``
    (becomes ``Androidtv``) — those should go in ``DISPLAY_NAMES``.
    """
    canonical = WORD_CASING.get(word.lower())
    if canonical is not None:
        return canonical
    if not word or any(ch.isupper() for ch in word):
        return word
    return word.capitalize()

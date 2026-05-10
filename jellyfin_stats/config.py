import os

import yaml

from .models import ContributorsConfig

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT_DIR, "configuration")
REPOS_YAML = os.path.join(CONFIG_DIR, "repos.yaml")
CONTRIBUTORS_YAML = os.path.join(CONFIG_DIR, "contributors.yaml")
TEAM_YAML = os.path.join(CONFIG_DIR, "team.yaml")


def load_config(path: str = REPOS_YAML) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_team(path: str = TEAM_YAML) -> tuple[set[str], dict[str, str]]:
    if not os.path.isfile(path):
        return set(), {}
    with open(path) as f:
        data = yaml.safe_load(f) or []
    usernames: set[str] = set()
    urls: dict[str, str] = {}
    for m in data:
        username = m.get("username")
        if not username:
            continue
        key = username.lower()
        usernames.add(key)
        urls[key] = m.get("url") or f"https://github.com/{username}"
    return usernames, urls


def load_contributors(
    contributors_path: str = CONTRIBUTORS_YAML,
    team_path: str = TEAM_YAML,
) -> ContributorsConfig:
    team_usernames, team_urls = _load_team(team_path)
    if not os.path.isfile(contributors_path):
        return ContributorsConfig([], set(), set(), set(), {}, {}, team_usernames, team_urls)
    with open(contributors_path) as f:
        data = yaml.safe_load(f) or {}
    maintainers = data.get("maintainers", [])
    maintainer_usernames = {m["username"].lower() for m in maintainers}
    blacklist = {b.lower() for b in data.get("blacklist", [])}
    hidden = maintainer_usernames | blacklist
    repo_maintainers: dict[str, list[tuple[str, str]]] = {}
    repo_maintainer_usernames: dict[str, set[str]] = {}
    for m in maintainers:
        username = m["username"]
        name = m.get("name", username)
        url = m.get("url", f"https://github.com/{username}")
        for repo in m.get("repos", []):
            key = repo.lower()
            repo_maintainers.setdefault(key, []).append((name, url))
            repo_maintainer_usernames.setdefault(key, set()).add(username.lower())
    return ContributorsConfig(
        maintainers,
        maintainer_usernames,
        blacklist,
        hidden,
        repo_maintainers,
        repo_maintainer_usernames,
        team_usernames,
        team_urls,
    )


def expand_repos(config: dict) -> dict[str, dict[str, str]]:
    """Flatten the repos.yaml buckets into a single ``repo -> {display, org}`` map.

    Pulls from ``core``, ``clients``, ``labs``, and ``documentation``. Labs
    repos default to ``labs_org`` unless listed in ``labs_in_main_org``.
    """
    main_org = config.get("org", "jellyfin")
    labs_org = config.get("labs_org", "jellyfin-labs")
    labs_in_main = set(config.get("labs_in_main_org", []))

    out: dict[str, dict[str, str]] = {}
    for bucket in ("core", "clients", "documentation"):
        for key, display in (config.get(bucket) or {}).items():
            out[key] = {"display": display, "org": main_org}
    for key, display in (config.get("labs") or {}).items():
        out[key] = {
            "display": display,
            "org": main_org if key in labs_in_main else labs_org,
        }
    return out

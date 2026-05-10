"""High-level card builders.

Each function takes already-collected stats plus optional config and returns
an SVG string ready to drop into Markdown / MDX, or save to a file.

Kept deliberately thin: the layout and styling decisions live in
:mod:`jellyfin_stats.svg`. This module only assembles the inputs the SVG
primitives expect (e.g. building ``(name, url)`` pairs from contributor
usernames, picking a gradient id, sorting releases).
"""

from typing import Optional

from .models import ContributorsConfig, RangeData, RepoStats
from .svg import activity_chart, releases_table, repo_stats_card


# MARK: - Per-repo card

def build_repo_card(
    stats: RepoStats,
    *,
    title: Optional[str] = None,
    contributors: Optional[ContributorsConfig] = None,
    gradient_id: Optional[str] = None,
) -> str:
    """Render the per-repo stats card.

    `stats` carries the issue/PR/contributor counts and contributor lists for
    the period. `contributors` (optional) supplies the maintainer overrides
    and team profile URLs that decorate the card. `title` defaults to the
    stats' display name. `gradient_id` defaults to ``stats-<repo>-grad``;
    callers should pass a unique id when embedding multiple cards in the
    same SVG context to avoid id collisions.
    """
    title = title or stats.display_name
    gradient_id = gradient_id or f"stats-{stats.name.lower()}-grad"

    repo_maintainers: dict[str, list[tuple[str, str]]] = {}
    team_urls: dict[str, str] = {}
    if contributors is not None:
        repo_maintainers = contributors.repo_maintainers
        team_urls = contributors.team_urls

    maintainers = repo_maintainers.get(stats.name.lower()) or None

    team_pairs = [
        (username, team_urls.get(username.lower()) or f"https://github.com/{username}")
        for username, _count in stats.team_contributors
    ] or None
    top_pairs = [
        (username, f"https://github.com/{username}")
        for username, _count in stats.top_contributors[:5]
    ] or None
    new_pairs = [
        (username, f"https://github.com/{username}")
        for username in stats.new_contributors
    ] or None

    return repo_stats_card(
        title,
        stats.closed_issues,
        stats.merged_prs,
        stats.unique_contributors,
        gradient_id,
        maintainers=maintainers,
        team_contributors=team_pairs,
        top_contributors=top_pairs,
        new_contributors=new_pairs,
    )


# MARK: - Activity chart

def build_activity_chart(data: RangeData, *, gradient_id: str = "stats-activity-grad") -> str:
    """Render the trailing 12-month multi-line activity chart."""
    if not data.chart_monthly_stats:
        return ""
    return activity_chart(data.chart_monthly_stats, gradient_id)


# MARK: - Releases table

def _clean_release_name(name: str, tag: str) -> str:
    cleaned = name.strip()
    lower = cleaned.lower()
    if lower.startswith("release "):
        cleaned = cleaned[len("release "):].strip()
    elif lower.startswith("release:"):
        cleaned = cleaned[len("release:"):].strip()
    if len(cleaned) > 1 and cleaned[0] in ("v", "V") and cleaned[1].isdigit():
        cleaned = cleaned[1:]
    if not cleaned:
        cleaned = tag
    return cleaned


def build_releases_table(data: RangeData, *, gradient_id: str = "stats-releases-grad") -> str:
    """Render the latest-release-per-repo table."""
    if not data.latest_releases:
        return ""

    ordered = sorted(data.latest_releases, key=lambda r: r.published_at, reverse=True)
    rows = [
        (r.display_name, _clean_release_name(r.tag, r.tag), r.url, r.published_at)
        for r in ordered
    ]
    return releases_table(rows, gradient_id)

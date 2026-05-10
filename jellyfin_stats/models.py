from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ContributorsConfig:
    maintainers: list[dict[str, str]]
    maintainer_usernames: set[str]  # lowercase
    blacklist: set[str]  # lowercase
    hidden: set[str]  # lowercase, combined: maintainers + blacklist
    repo_maintainers: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # lowercase repo key -> list of (name, url)
    repo_maintainer_usernames: dict[str, set[str]] = field(default_factory=dict)  # lowercase repo key -> set of lowercase usernames
    team_usernames: set[str] = field(default_factory=set)  # lowercase
    team_urls: dict[str, str] = field(default_factory=dict)  # lowercase username -> profile url


@dataclass
class MonthlyStats:
    month_start: str
    month_end: str
    display_name: str
    closed_issues: int = 0
    merged_prs: int = 0
    contributors: int = 0


@dataclass
class Release:
    repo: str
    display_name: str
    tag: str
    name: str
    published_at: str
    url: str
    commits_count: int = 0


@dataclass
class RepoStats:
    name: str
    display_name: str
    closed_issues: int = 0
    merged_prs: int = 0
    unique_contributors: int = 0
    top_contributors: list[tuple[str, int]] = field(default_factory=list)
    team_contributors: list[tuple[str, int]] = field(default_factory=list)
    new_contributors: list[str] = field(default_factory=list)


@dataclass
class RangeData:
    start_date: datetime
    end_date: datetime
    monthly_stats: list[MonthlyStats]
    chart_monthly_stats: list[MonthlyStats]
    unique_contributors: set[str]
    yearly_contributors: set[str]
    releases: list[Release]
    repo_stats: dict[str, RepoStats]
    latest_releases: list[Release] = field(default_factory=list)

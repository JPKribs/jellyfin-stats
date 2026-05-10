import sys
import time
from datetime import datetime, timedelta
from typing import Optional

from github import Github, GithubException

from .models import ContributorsConfig, MonthlyStats, RangeData, Release, RepoStats

# GitHub Search API allows 30 req/min; use 24 to leave headroom
_SEARCH_RATE_INTERVAL = 60.0 / 24


# MARK: - Date Utilities

def get_month_ranges(start_date: datetime, end_date: datetime) -> list[tuple[datetime, datetime, str]]:
    ranges = []
    current = start_date.replace(day=1)
    end_month = end_date.replace(day=1)

    while current <= end_month:
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1)
        else:
            next_month = current.replace(month=current.month + 1)
        month_end = next_month - timedelta(days=1)

        actual_start = max(current, start_date)
        actual_end = min(month_end, end_date)

        display = current.strftime("%b %Y")
        ranges.append((actual_start, actual_end, display))

        current = next_month

    return ranges


def get_trailing_months(end_date: datetime, months: int = 12) -> list[tuple[datetime, datetime, str]]:
    """Return `months` complete calendar months ending at the last complete month before end_date."""
    ranges = []

    # Start from the last complete month (month before end_date's month)
    prev_day = end_date.replace(day=1) - timedelta(days=1)
    current = prev_day.replace(day=1)

    for _ in range(months):
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1, day=1)
        else:
            next_month = current.replace(month=current.month + 1, day=1)
        month_end = next_month - timedelta(days=1)
        display = current.strftime("%b")
        ranges.append((current, month_end, display))
        current = (current - timedelta(days=1)).replace(day=1)

    ranges.reverse()
    return ranges


# MARK: - DataCollector

class DataCollector:

    def __init__(self, gh: Github, org: str, contributors: Optional[ContributorsConfig] = None):
        self.gh = gh
        self.org = org
        self.contributors = contributors or ContributorsConfig([], set(), set(), set(), {}, set())
        self._last_search_time: float = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_search_time
        wait = _SEARCH_RATE_INTERVAL - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_search_time = time.time()

    def _search_count(self, query: str) -> int:
        """Rate-limited search returning total count, with exponential backoff fallback."""
        for attempt in range(3):
            self._throttle()
            try:
                return self.gh.search_issues(query).totalCount
            except GithubException as e:
                if attempt < 2 and e.status in (403, 429):
                    backoff = 60 * (2 ** attempt)
                    print(f"    Rate limited, waiting {backoff}s...", file=sys.stderr)
                    time.sleep(backoff)
                else:
                    raise
        return 0

    def _search_all(self, query: str) -> list:
        """Rate-limited search collecting all results, with exponential backoff fallback."""
        for attempt in range(3):
            self._throttle()
            try:
                return list(self.gh.search_issues(query))
            except GithubException as e:
                if attempt < 2 and e.status in (403, 429):
                    backoff = 60 * (2 ** attempt)
                    print(f"    Rate limited, waiting {backoff}s...", file=sys.stderr)
                    time.sleep(backoff)
                else:
                    raise
        return []

    def _build_scope(self, repo: Optional[str] = None, org: Optional[str] = None) -> str:
        if repo:
            scope_org = org or self.org
            return f"repo:{scope_org}/{repo}"
        return f"org:{org or self.org}"

    def count_closed_issues(self, start: str, end: str, repo: Optional[str] = None, org: Optional[str] = None) -> int:
        scope = self._build_scope(repo, org)
        query = f"{scope} is:issue is:closed closed:{start}..{end}"
        return self._search_count(query)

    def count_merged_prs(self, start: str, end: str, repo: Optional[str] = None, org: Optional[str] = None) -> int:
        scope = self._build_scope(repo, org)
        query = f"{scope} is:pr is:merged merged:{start}..{end}"
        return self._search_count(query)

    def fetch_merged_pr_authors(self, start: str, end: str, repo: Optional[str] = None, org: Optional[str] = None) -> list[str]:
        scope = self._build_scope(repo, org)
        query = f"{scope} is:pr is:merged merged:{start}..{end}"
        return [pr.user.login for pr in self._search_all(query) if pr.user]

    def _has_prior_repo_pr(self, repo: str, author: str, before: str, org: Optional[str] = None) -> bool:
        """True if `author` has any merged PR in `repo` strictly before `before` (YYYY-MM-DD)."""
        scope_org = org or self.org
        query = f"repo:{scope_org}/{repo} is:pr is:merged author:{author} merged:<{before}"
        return self._search_count(query) > 0

    def fetch_repo_releases(self, repo_name: str, display_name: str, since: datetime, until: datetime, org: Optional[str] = None) -> tuple[list[Release], Optional[Release]]:
        """Fetch releases for a repo.

        Returns ``(period_releases, latest_release)``: the period list contains
        every release published within ``[since, until]``; ``latest_release``
        is the single most recent release overall (regardless of date), or
        ``None`` if the repo has no releases.
        """
        repo_org = org or self.org
        try:
            repo = self.gh.get_repo(f"{repo_org}/{repo_name}")
        except GithubException:
            return [], None

        all_releases = []

        for release in repo.get_releases():
            if release.draft or not release.published_at:
                continue
            pub_naive = release.published_at.replace(tzinfo=None)
            all_releases.append({
                "tag": release.tag_name,
                "name": release.name or release.tag_name,
                "published_at": pub_naive,
                "url": release.html_url,
            })

        all_releases.sort(key=lambda x: x["published_at"])

        def _commits_count(idx: int) -> int:
            if idx == 0:
                return 0
            prev_tag = all_releases[idx - 1]["tag"]
            try:
                return repo.compare(prev_tag, all_releases[idx]["tag"]).total_commits
            except GithubException:
                return 0

        def _to_release(rel: dict, commits: int) -> Release:
            return Release(
                repo=repo_name,
                display_name=display_name,
                tag=rel["tag"],
                name=rel["name"],
                published_at=rel["published_at"].strftime("%Y-%m-%d"),
                url=rel["url"],
                commits_count=commits,
            )

        period_releases: list[Release] = []
        for i, rel in enumerate(all_releases):
            if not (since <= rel["published_at"] <= until):
                continue
            period_releases.append(_to_release(rel, _commits_count(i)))

        latest_release: Optional[Release] = None
        if all_releases:
            last_idx = len(all_releases) - 1
            if period_releases and period_releases[-1].tag == all_releases[last_idx]["tag"]:
                latest_release = period_releases[-1]
            else:
                latest_release = _to_release(all_releases[last_idx], _commits_count(last_idx))

        return period_releases, latest_release

    def _fetch_chart_contributors(
        self, chart_ranges: list[tuple[datetime, datetime, str]]
    ) -> tuple[dict[int, int], set[str]]:
        """Fetch unique contributor counts per chart month via batched searches.

        Processes chart months in bi-monthly chunks to stay under GitHub's
        1000-result search API limit while avoiding 12 separate full iterations.

        Returns (month_index -> unique_count, all_yearly_contributors).
        """
        if not chart_ranges:
            return {}, set()

        month_authors: dict[int, set[str]] = {i: set() for i in range(len(chart_ranges))}
        all_authors: set[str] = set()
        scope = self._build_scope()

        chunk_size = 2
        for chunk_start in range(0, len(chart_ranges), chunk_size):
            chunk = chart_ranges[chunk_start:chunk_start + chunk_size]
            chunk_indices = range(chunk_start, chunk_start + len(chunk))

            start = chunk[0][0].strftime("%Y-%m-%d")
            end = chunk[-1][1].strftime("%Y-%m-%d")

            query = f"{scope} is:pr is:merged merged:{start}..{end}"

            for pr in self._search_all(query):
                if not pr.user:
                    continue
                author = pr.user.login
                all_authors.add(author)

                if pr.closed_at:
                    closed_date = pr.closed_at.replace(tzinfo=None).date()
                    for i in chunk_indices:
                        ms, me, _ = chart_ranges[i]
                        if ms.date() <= closed_date <= me.date():
                            month_authors[i].add(author)
                            break

        counts = {i: len(authors) for i, authors in month_authors.items()}
        return counts, all_authors

    def _collect_repo_stats(self, repo: str, display_name: str, start_str: str, end_str: str, org: Optional[str] = None) -> RepoStats:
        closed = self.count_closed_issues(start_str, end_str, repo, org)
        merged = self.count_merged_prs(start_str, end_str, repo, org)

        top_contributors: list[tuple[str, int]] = []
        team_contributors: list[tuple[str, int]] = []
        new_contributors: list[str] = []
        unique_contributors = 0
        if merged > 0:
            authors = self.fetch_merged_pr_authors(start_str, end_str, repo, org)
            contributor_counts: dict[str, int] = {}
            for author in authors:
                contributor_counts[author] = contributor_counts.get(author, 0) + 1
            repo_maintainers = self.contributors.repo_maintainer_usernames.get(repo.lower(), set())
            team_only = self.contributors.team_usernames - repo_maintainers
            team_filtered = {
                k: v for k, v in contributor_counts.items()
                if k.lower() in team_only and k.lower() not in self.contributors.blacklist
            }
            team_contributors = sorted(team_filtered.items(), key=lambda x: x[1], reverse=True)
            community_hidden = repo_maintainers | self.contributors.blacklist
            community_filtered = {
                k: v for k, v in contributor_counts.items()
                if k.lower() not in community_hidden and k.lower() not in self.contributors.team_usernames
            }
            top_contributors = sorted(community_filtered.items(), key=lambda x: x[1], reverse=True)[:3]
            unique_contributors = len(contributor_counts)

            for author in contributor_counts:
                if author.lower() in self.contributors.blacklist:
                    continue
                if not self._has_prior_repo_pr(repo, author, start_str, org):
                    new_contributors.append(author)
            new_contributors.sort(key=str.lower)

        return RepoStats(
            name=repo,
            display_name=display_name,
            closed_issues=closed,
            merged_prs=merged,
            unique_contributors=unique_contributors,
            top_contributors=top_contributors,
            team_contributors=team_contributors,
            new_contributors=new_contributors,
        )

    def collect_range_data(
        self,
        start_date: datetime,
        end_date: datetime,
        all_repos: dict[str, dict[str, str]],
    ) -> RangeData:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        print(f"Collecting data from {start_str} to {end_str}...", file=sys.stderr)

        month_ranges = get_month_ranges(start_date, end_date)
        monthly_stats: list[MonthlyStats] = []
        all_contributors: set[str] = set()

        print("  Fetching period monthly stats and contributors...", file=sys.stderr)
        for i, (month_start, month_end, display) in enumerate(month_ranges, 1):
            ms_str = month_start.strftime("%Y-%m-%d")
            me_str = month_end.strftime("%Y-%m-%d")

            print(f"    [{i}/{len(month_ranges)}] {display}", file=sys.stderr)

            closed_issues = self.count_closed_issues(ms_str, me_str)
            merged_prs = self.count_merged_prs(ms_str, me_str)

            authors = self.fetch_merged_pr_authors(ms_str, me_str)
            all_contributors.update(authors)

            monthly_stats.append(MonthlyStats(
                month_start=ms_str,
                month_end=me_str,
                display_name=display,
                closed_issues=closed_issues,
                merged_prs=merged_prs,
            ))

        print("  Fetching 12-month chart data...", file=sys.stderr)
        chart_ranges = get_trailing_months(end_date, 12)
        chart_monthly_stats: list[MonthlyStats] = []

        print("    Fetching contributor counts (batched)...", file=sys.stderr)
        contributor_counts, yearly_contributors = self._fetch_chart_contributors(chart_ranges)

        for i, (month_start, month_end, display) in enumerate(chart_ranges):
            ms_str = month_start.strftime("%Y-%m-%d")
            me_str = month_end.strftime("%Y-%m-%d")

            print(f"    [{i + 1}/12] {display}", file=sys.stderr)

            closed_issues = self.count_closed_issues(ms_str, me_str)
            merged_prs = self.count_merged_prs(ms_str, me_str)

            chart_monthly_stats.append(MonthlyStats(
                month_start=ms_str,
                month_end=me_str,
                display_name=display,
                closed_issues=closed_issues,
                merged_prs=merged_prs,
                contributors=contributor_counts.get(i, 0),
            ))

        print("  Fetching releases...", file=sys.stderr)
        all_releases: list[Release] = []
        latest_releases: list[Release] = []
        for repo, meta in all_repos.items():
            display_name = meta["display"]
            org = meta.get("org") or self.org
            try:
                period, latest = self.fetch_repo_releases(repo, display_name, start_date, end_date, org)
                all_releases.extend(period)
                if latest:
                    latest_releases.append(latest)
            except GithubException as e:
                print(f"    Skipping releases for {org}/{repo}: not accessible ({e.status}).", file=sys.stderr)
        all_releases.sort(key=lambda x: x.published_at)
        latest_releases.sort(key=lambda x: x.display_name.lower())

        repo_stats: dict[str, RepoStats] = {}
        total = len(all_repos)
        for i, (repo, meta) in enumerate(all_repos.items(), 1):
            display_name = meta["display"]
            org = meta.get("org") or self.org
            print(f"  [{i}/{total}] Fetching stats for {org}/{repo}...", file=sys.stderr)
            try:
                stats = self._collect_repo_stats(repo, display_name, start_str, end_str, org)
            except GithubException as e:
                print(f"    Skipping stats for {org}/{repo}: not accessible ({e.status}).", file=sys.stderr)
                continue
            repo_stats[repo] = stats

        return RangeData(
            start_date=start_date,
            end_date=end_date,
            monthly_stats=monthly_stats,
            chart_monthly_stats=chart_monthly_stats,
            unique_contributors=all_contributors,
            yearly_contributors=yearly_contributors,
            releases=all_releases,
            repo_stats=repo_stats,
            latest_releases=latest_releases,
        )

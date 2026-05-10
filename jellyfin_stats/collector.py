"""GitHub Search API queries for the trailing 30-day banner stats.

Search API limits: 30 req/min authenticated, 10 req/min unauthenticated.
The collector throttles itself to 24 req/min so it stays clear of either
ceiling, and falls back to exponential backoff on 403/429.
"""

import sys
import time

from github import Github, GithubException

# 60s / 24 req → enforce a small interval between any two Search API calls.
_SEARCH_RATE_INTERVAL = 60.0 / 24


class DataCollector:
    """Per-repo issue / PR / contributor counts via GitHub Search."""

    def __init__(self, gh: Github, default_org: str = "jellyfin"):
        self.gh = gh
        self.default_org = default_org
        self._last_search_time: float = 0.0

    # MARK: - Rate limiting

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_search_time
        wait = _SEARCH_RATE_INTERVAL - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_search_time = time.time()

    def _search_count(self, query: str) -> int:
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

    # MARK: - Per-repo counts

    def _scope(self, repo: str, org: str | None = None) -> str:
        return f"repo:{org or self.default_org}/{repo}"

    def count_closed_issues(self, repo: str, org: str | None, start: str, end: str) -> int:
        return self._search_count(
            f"{self._scope(repo, org)} is:issue is:closed closed:{start}..{end}"
        )

    def count_merged_prs(self, repo: str, org: str | None, start: str, end: str) -> int:
        return self._search_count(
            f"{self._scope(repo, org)} is:pr is:merged merged:{start}..{end}"
        )

    def fetch_merged_pr_authors(self, repo: str, org: str | None, start: str, end: str) -> list[str]:
        return [
            pr.user.login
            for pr in self._search_all(
                f"{self._scope(repo, org)} is:pr is:merged merged:{start}..{end}"
            )
            if pr.user
        ]

    def has_prior_repo_pr(self, repo: str, org: str | None, author: str, before: str) -> bool:
        """True if `author` has any merged PR in `repo` strictly before `before`."""
        return self._search_count(
            f"{self._scope(repo, org)} is:pr is:merged author:{author} merged:<{before}"
        ) > 0

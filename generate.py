#!/usr/bin/env python3
"""Generate Jellyfin stats SVG cards.

Writes one ``<repo>.svg`` per configured repo plus ``activity.svg`` and
``releases.svg`` into the chosen output directory. Pass ``--repo`` to limit
to a single repo (the activity / releases cards are skipped in that mode).

Examples
--------

    # Every configured repo, default trailing month
    ./generate.py --output-dir out/

    # Explicit window
    ./generate.py --start 2026-04-01 --end 2026-05-01 --output-dir out/

    # Single repo card only
    ./generate.py --repo jellyfin-roku --start 2026-04-01 --end 2026-05-01 \\
        --output-dir out/

    # No GitHub calls (renders empty cards — useful for layout iteration)
    ./generate.py --simple --output-dir out/
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional

from github import Auth, Github

from jellyfin_stats.banners import build_banner
from jellyfin_stats.cards import (
    build_activity_chart,
    build_releases_table,
    build_repo_card,
)
from jellyfin_stats.collector import DataCollector
from jellyfin_stats.config import expand_repos, load_config, load_contributors
from jellyfin_stats.models import RangeData, RepoStats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SVG stats cards for Jellyfin repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--start", type=str, default=None,
                        help="Window start date (YYYY-MM-DD). Defaults to one month before --end.")
    parser.add_argument("--end", type=str, default=None,
                        help="Window end date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--repo", type=str, default=None,
                        help="Generate just this single repo's card. Skips activity/releases cards.")
    parser.add_argument("--output-dir", type=str, default="out",
                        help="Directory to write SVG files into (created if needed).")
    parser.add_argument("--simple", action="store_true",
                        help="Skip every GitHub API call. Cards render with zero stats; useful for layout iteration.")
    return parser.parse_args()


def _resolve_dates(start: Optional[str], end: Optional[str]) -> tuple[datetime, datetime]:
    end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.now()
    if start:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
    else:
        first_of_month = end_dt.replace(day=1)
        if first_of_month.month == 1:
            start_dt = first_of_month.replace(year=first_of_month.year - 1, month=12)
        else:
            start_dt = first_of_month.replace(month=first_of_month.month - 1)
    return start_dt, end_dt


def _resolve_token() -> Optional[str]:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            print("  Using token from gh CLI.", file=sys.stderr)
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _empty_range(start: datetime, end: datetime) -> RangeData:
    return RangeData(
        start_date=start,
        end_date=end,
        monthly_stats=[],
        chart_monthly_stats=[],
        unique_contributors=set(),
        yearly_contributors=set(),
        releases=[],
        repo_stats={},
        latest_releases=[],
    )


def _write(path: str, svg: str) -> None:
    if not svg:
        return
    with open(path, "w") as f:
        f.write(svg)
    print(f"  wrote {path}", file=sys.stderr)


def main() -> None:
    args = parse_args()
    start, end = _resolve_dates(args.start, args.end)
    print(f"Window: {start:%Y-%m-%d} → {end:%Y-%m-%d}", file=sys.stderr)

    config = load_config()
    contributors = load_contributors()
    repos = expand_repos(config)

    if args.repo:
        if args.repo not in repos:
            print(f"Error: '{args.repo}' is not in repos.yaml. "
                  f"Known: {', '.join(sorted(repos))}", file=sys.stderr)
            raise SystemExit(2)
        repos = {args.repo: repos[args.repo]}

    if args.simple:
        print("Simple mode: skipping GitHub API calls.", file=sys.stderr)
        range_data = _empty_range(start, end)
        for name, meta in repos.items():
            range_data.repo_stats[name] = RepoStats(name=name, display_name=meta["display"])
    else:
        token = _resolve_token()
        if not token:
            print("Warning: no GitHub token; API rate limits will be tight.", file=sys.stderr)
        gh = Github(auth=Auth.Token(token) if token else None, per_page=100)
        collector = DataCollector(gh, config.get("org", "jellyfin"), contributors)
        range_data = collector.collect_range_data(start, end, repos)

    os.makedirs(args.output_dir, exist_ok=True)

    for repo_key, meta in repos.items():
        stats = range_data.repo_stats.get(repo_key) or RepoStats(
            name=repo_key, display_name=meta["display"],
        )
        svg = build_repo_card(stats, title=meta["display"], contributors=contributors)
        if svg:
            _write(os.path.join(args.output_dir, f"{repo_key}.svg"), svg)

        # Banners are pure HTML (no API needed) — always emit one per repo,
        # even in --simple mode.
        _write(
            os.path.join(args.output_dir, f"{repo_key}-banner.md"),
            build_banner(repo_key, meta["display"]),
        )

    if not args.repo:
        _write(os.path.join(args.output_dir, "activity.svg"),
               build_activity_chart(range_data))
        _write(os.path.join(args.output_dir, "releases.svg"),
               build_releases_table(range_data))


if __name__ == "__main__":
    main()

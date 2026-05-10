#!/usr/bin/env python3
"""Generate one README banner SVG per Jellyfin repo.

Discovers repos dynamically from the configured GitHub orgs (default:
`jellyfin` and `jellyfin-labs`), fetches the trailing 30-day stats from
the Search API, and writes ``<repo>-banner.svg`` per repo into the output
dir. No `repos.yaml` required.

Examples
--------

    # All discovered repos, default last 30 days
    ./generate.py --output-dir out/

    # Single repo (skips discovery, fetch + render that one)
    ./generate.py --repo jellyfin-roku --output-dir out/

    # Explicit window
    ./generate.py --end 2026-05-10 --output-dir out/

    # Layout iteration — no API calls, zeroed stats, no welcome list
    ./generate.py --simple --output-dir out/
"""

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from github import Auth, Github

from jellyfin_stats.collector import DataCollector
from jellyfin_stats.repos import DEFAULT_ORGS, discover_repos, humanize
from jellyfin_stats.svg import build_banner_card, build_banner_plain

WINDOW_DAYS = 30


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate Jellyfin README banner SVGs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--end", type=str, default=None,
                   help=f"Window end date (YYYY-MM-DD). Defaults to today (window is {WINDOW_DAYS} days back).")
    p.add_argument("--repo", type=str, default=None,
                   help="Generate just this single repo (skips discovery).")
    p.add_argument("--org", type=str, default=None,
                   help="Org owning --repo. Defaults to `jellyfin`.")
    p.add_argument("--orgs", type=str, default=None,
                   help=f"Comma-separated orgs to discover. Default: {','.join(DEFAULT_ORGS)}.")
    p.add_argument("--output-dir", type=str, default="banners",
                   help="Directory to write SVG files into (created if needed).")
    p.add_argument("--simple", action="store_true",
                   help="No GitHub API calls. Renders zeroed stats — useful for layout iteration.")
    return p.parse_args()


def _resolve_window(end_arg: str | None) -> tuple[str, str]:
    end = datetime.strptime(end_arg, "%Y-%m-%d") if end_arg else datetime.now(UTC).replace(tzinfo=None)
    end = end.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=WINDOW_DAYS)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _resolve_token() -> str | None:
    if t := os.environ.get("GITHUB_TOKEN"):
        return t
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            print("  Using token from gh CLI.", file=sys.stderr)
            return r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _stats_for(collector: DataCollector, repo: str, org: str, start: str, end: str) -> tuple[int, int, int, int]:
    """Return (closed_issues, merged_prs, contributors, new_contributors)."""
    closed = collector.count_closed_issues(repo, org, start, end)
    merged = collector.count_merged_prs(repo, org, start, end)
    if merged == 0:
        return closed, 0, 0, 0
    authors = sorted({a for a in collector.fetch_merged_pr_authors(repo, org, start, end) if a})
    new_count = sum(1 for a in authors if not collector.has_prior_repo_pr(repo, org, a, start))
    return closed, merged, len(authors), new_count


def main() -> None:
    args = parse_args()
    start_str, end_str = _resolve_window(args.end)
    out_dir = Path(args.output_dir)
    plain_dir = out_dir / "plain"
    complete_dir = out_dir / "complete"
    plain_dir.mkdir(parents=True, exist_ok=True)
    complete_dir.mkdir(parents=True, exist_ok=True)

    print(f"Window: {start_str} → {end_str}", file=sys.stderr)

    # Resolve which repos to render
    if args.simple:
        if args.repo:
            repos = [(args.repo, humanize(args.repo), args.org or "jellyfin")]
        else:
            print("Error: --simple requires --repo (no API → no discovery).", file=sys.stderr)
            raise SystemExit(2)
    else:
        token = _resolve_token()
        if not token:
            print("Warning: no GitHub token; API rate limits will be tight.", file=sys.stderr)
        gh = Github(auth=Auth.Token(token) if token else None, per_page=100)
        if args.repo:
            repos = [(args.repo, humanize(args.repo), args.org or "jellyfin")]
        else:
            orgs = [s.strip() for s in args.orgs.split(",")] if args.orgs else None
            print(f"Discovering repos from {', '.join(orgs or DEFAULT_ORGS)}...", file=sys.stderr)
            repos = list(discover_repos(gh, orgs))
            print(f"Found {len(repos)} repos.", file=sys.stderr)

    collector = None if args.simple else DataCollector(gh)

    for repo, display, org in repos:
        slug = repo.lower()
        gradient_id = f"banner-{slug}-grad"

        # Plain banner — name + tagline + Jellyfin mark, no API needed
        plain_svg = build_banner_plain(repo, display, gradient_id)
        plain_path = plain_dir / f"{slug}.svg"
        plain_path.write_text(plain_svg)
        print(f"  [{repo}] wrote {plain_path}", file=sys.stderr)

        # Complete banner — adds the 30-day stats row
        if args.simple:
            closed = merged = contributors = new_count = 0
        else:
            print(f"  [{repo}] fetching stats...", file=sys.stderr)
            closed, merged, contributors, new_count = _stats_for(collector, repo, org, start_str, end_str)
            print(f"    issues={closed} prs={merged} contribs={contributors} new={new_count}", file=sys.stderr)

        complete_path = complete_dir / f"{slug}.svg"
        if not any((closed, merged, contributors, new_count)):
            # Nothing happened in the window — mirror the plain banner so the
            # complete URL still resolves but doesn't display an empty state.
            complete_path.write_text(plain_svg)
            print(f"    no activity → mirrored plain to {complete_path}", file=sys.stderr)
        else:
            svg = build_banner_card(
                repo=repo,
                display_name=display,
                closed=closed,
                merged=merged,
                contributors=contributors,
                new_contributors=new_count,
                gradient_id=gradient_id,
            )
            complete_path.write_text(svg)
            print(f"    wrote {complete_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

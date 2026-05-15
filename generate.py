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
"""

import argparse
import base64
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from github import Auth, Github

from jellyfin_stats.collector import DataCollector
from jellyfin_stats.repos import DEFAULT_ORGS, discover_repos, humanize
from jellyfin_stats.svg import (
    build_banner_contributor_icons,
    build_banner_contributor_names,
    build_banner_contributor_stats,
    build_banner_simple,
)

_AVATAR_CACHE: dict[tuple[str, int], str | None] = {}


def _fetch_avatar(login: str, size: int = 200) -> str | None:
    """Return login's GitHub avatar PNG as a base64 ``data:`` URI, or None on
    failure. Cached in-process so the same contributor isn't re-fetched across
    multiple repos in one run. Inlined (not externally referenced) so the
    avatar renders even when the SVG is loaded as an ``<img>`` in a README,
    where external image refs are sandboxed by most renderers.
    """
    key = (login, size)
    if key in _AVATAR_CACHE:
        return _AVATAR_CACHE[key]
    url = f"https://github.com/{login}.png?size={size}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "jellyfin-stats"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        uri = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"    avatar fetch failed for {login}: {e}", file=sys.stderr)
        uri = None
    _AVATAR_CACHE[key] = uri
    return uri

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


def _stats_for(collector: DataCollector, repo: str, org: str, start: str, end: str) -> tuple[int, int, int, int, list[str], list[str]]:
    """Return (closed_issues, merged_prs, contributors, new_contributors, authors, new_authors)."""
    closed = collector.count_closed_issues(repo, org, start, end)
    merged = collector.count_merged_prs(repo, org, start, end)
    if merged == 0:
        return closed, 0, 0, 0, [], []
    authors = sorted({a for a in collector.fetch_merged_pr_authors(repo, org, start, end) if a})
    new_authors = [a for a in authors if not collector.has_prior_repo_pr(repo, org, a, start)]
    return closed, merged, len(authors), len(new_authors), authors, new_authors


def main() -> None:
    args = parse_args()
    start_str, end_str = _resolve_window(args.end)
    out_dir = Path(args.output_dir)
    simple_dir = out_dir / "simple"
    stats_dir = out_dir / "contributor-stats"
    names_dir = out_dir / "contributor-names"
    icons_dir = out_dir / "contributor-icons"
    simple_dir.mkdir(parents=True, exist_ok=True)
    stats_dir.mkdir(parents=True, exist_ok=True)
    names_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)

    print(f"Window: {start_str} → {end_str}", file=sys.stderr)

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

    collector = DataCollector(gh)

    for repo, display, org in repos:
        slug = repo.lower()
        gradient_id = f"banner-{slug}-grad"

        # Simple banner — name + tagline + Jellyfin mark, no API needed
        simple_svg = build_banner_simple(repo, display, gradient_id)
        simple_path = simple_dir / f"{slug}.svg"
        simple_path.write_text(simple_svg)
        print(f"  [{repo}] wrote {simple_path}", file=sys.stderr)

        # contributor-stats banner — adds the 30-day stats row
        print(f"  [{repo}] fetching stats...", file=sys.stderr)
        closed, merged, contributors, new_count, rain_names, new_authors = _stats_for(collector, repo, org, start_str, end_str)
        print(f"    issues={closed} prs={merged} contribs={contributors} new={new_count}", file=sys.stderr)

        stats_path = stats_dir / f"{slug}.svg"
        if not any((closed, merged, contributors, new_count)):
            # Nothing happened in the window — mirror the simple banner so the
            # URL still resolves but doesn't display an empty state.
            stats_path.write_text(simple_svg)
            print(f"    no activity → mirrored simple to {stats_path}", file=sys.stderr)
        else:
            svg = build_banner_contributor_stats(
                repo=repo,
                display_name=display,
                closed=closed,
                merged=merged,
                contributors=contributors,
                new_contributors=new_count,
                gradient_id=gradient_id,
            )
            stats_path.write_text(svg)
            print(f"    wrote {stats_path}", file=sys.stderr)

        # contributor-names banner — Matrix-style falling contributor names behind
        # the mark + stats. Mirrors simple when there are no contributors to fall.
        names_path = names_dir / f"{slug}.svg"
        if not rain_names:
            names_path.write_text(simple_svg)
            print(f"    no contributors → mirrored simple to {names_path}", file=sys.stderr)
        else:
            svg = build_banner_contributor_names(
                repo=repo,
                display_name=display,
                closed=closed,
                merged=merged,
                contributors=contributors,
                new_contributors=new_count,
                contributors_list=rain_names,
                new_contributor_names=new_authors,
                gradient_id=gradient_id,
            )
            names_path.write_text(svg)
            print(f"    wrote {names_path}", file=sys.stderr)

        # contributor-icons banner — last-30-day contributor avatars in the rain.
        # Mirrors simple when there are no contributors.
        icons_path = icons_dir / f"{slug}.svg"
        if not rain_names:
            icons_path.write_text(simple_svg)
            print(f"    no contributors → mirrored simple to {icons_path}", file=sys.stderr)
        else:
            print(f"    fetching avatars for {len(rain_names)} contributors...", file=sys.stderr)
            avatar_uris: dict[str, str] = {}
            for login in rain_names:
                uri = _fetch_avatar(login)
                if uri:
                    avatar_uris[login] = uri
            svg = build_banner_contributor_icons(
                repo=repo,
                display_name=display,
                closed=closed,
                merged=merged,
                contributors=contributors,
                new_contributors=new_count,
                contributors_list=rain_names,
                avatar_uris=avatar_uris,
                new_contributor_names=new_authors,
                gradient_id=gradient_id,
            )
            icons_path.write_text(svg)
            print(f"    wrote {icons_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

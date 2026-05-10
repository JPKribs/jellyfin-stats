# jellyfin-stats

Standalone generator for the SVG stats cards used in *State of the Fin* posts.
Pulls activity data from the GitHub API and renders three card types as inline
SVG (JSX-compatible, theme-aware via `currentColor`):

- **Per-repo card** — issues closed, PRs merged, contributor count, team list,
  new contributors, and a donut breakdown of team / returning / new contributors.
- **Activity chart** — multi-line chart of merged PRs, closed issues, and
  unique contributors across the trailing 12 months.
- **Releases table** — latest release per configured repo.

This project contains only the card-generation logic. Markdown / blog-post
assembly lives in [`jellyfin-blog-stateofthefin`](../jellyfin-blog-stateofthefin).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

A GitHub token is read from `$GITHUB_TOKEN` or, if unset, `gh auth token`.
Without a token the GitHub Search API rate-limits to 10 req/min.

## Usage

```bash
# Generate every card (per-repo + activity + releases) for a date range.
python3 generate.py --start 2026-04-01 --end 2026-05-01 --output-dir out/

# Single repo:
python3 generate.py --start 2026-04-01 --end 2026-05-01 \
    --repo jellyfin-roku --output-dir out/

# No GitHub calls — useful for layout iteration on the SVG with mock data:
python3 generate.py --simple --output-dir out/
```

Output files:

- `out/<repo>.svg` — one per configured repo with activity in the period
- `out/activity.svg` — trailing 12-month chart
- `out/releases.svg` — latest releases table

## Configuration

Three YAML files in `configuration/` drive the run:

- `repos.yaml` — which repos to track, organised into `core`, `clients`,
  `labs`, and `documentation` buckets. Sets the `org` and `labs_org`
  defaults and a `labs_in_main_org` override list.
- `team.yaml` — list of team usernames (with profile URLs). Used to split
  contributors into "team" vs "community" in the donut chart.
- `contributors.yaml` — per-repo maintainers (who get bolded in the team
  list) and a blacklist of bot/noise accounts.

These are the same files used by the blog project; copy or symlink as needed.

## Layout

```
jellyfin_stats/
  models.py     dataclasses for stats / releases / contributors config
  config.py     YAML loaders
  collector.py  GitHub API queries (rate-limited)
  svg.py        pure SVG rendering primitives
  cards.py      glue: stats + config -> SVG card strings
generate.py     CLI entrypoint
```

`svg.py` and `models.py` have no GitHub or YAML dependencies — they can be
imported standalone if you already have data in hand and just want the SVG.

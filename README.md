# jellyfin-stats

Generates two SVG README banners per Jellyfin repo:

- **`banners/plain/<repo>.svg`** — gradient title strip with the repo name +
  tagline, plus the official Jellyfin "J" mark on a black banner. Static
  (no stats) — only changes if the repo gets renamed or moves orgs.
- **`banners/complete/<repo>.svg`** — same chrome, plus the trailing
  30-day activity summary (issues closed, PRs merged, contributors, new
  contributors). Updated daily by the workflow.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

A GitHub token is read from `$GITHUB_TOKEN` or, if unset, `gh auth token`.
Without a token the Search API rate-limits to 10 req/min — fine for one
repo, slow when sweeping the whole org.

## Usage

```bash
# Every active public repo across `jellyfin` and `jellyfin-labs` → banners/
python3 generate.py

# Single repo (skips the discovery sweep)
python3 generate.py --repo jellyfin-roku

# Different orgs
python3 generate.py --orgs jellyfin

# Layout iteration — no API calls, zeroed stats
python3 generate.py --simple --repo jellyfin-roku
```

Each repo gets a pair of files: `banners/plain/<repo>.svg` and
`banners/complete/<repo>.svg` (lowercase). The `jellyfin` server gets the
special tagline `The Free Software Media System`; everything else gets
`Part of the Jellyfin Project`.

## Automation

[`.github/workflows/banners.yml`](.github/workflows/banners.yml) regenerates
every banner daily at midnight UTC and commits the changes to `banners/`.
Trigger it manually from the Actions tab when needed. Once published,
embed in a repo's README via either:

```markdown
<!-- static — no stats, no daily churn -->
![Banner](https://raw.githubusercontent.com/<owner>/jellyfin-stats/main/banners/plain/<repo>.svg)

<!-- live 30-day activity summary -->
![Banner](https://raw.githubusercontent.com/<owner>/jellyfin-stats/main/banners/complete/<repo>.svg)
```

## How it works

- Repos are **discovered dynamically** from the GitHub API — every
  public, non-archived, non-fork repo in the configured orgs gets a
  banner. No `repos.yaml` to maintain.
- Display names are derived from repo names (`jellyfin-roku` → `Jellyfin
  Roku`, `Swiftfin` → `Swiftfin`). Internal capital letters are
  preserved (`jellyfin-iOS` → `Jellyfin iOS`).
- 30-day stats use the GitHub Search API. The "is this contributor new"
  lookup is one request per contributor — that dominates the runtime
  for active repos like `jellyfin` itself.

## Layout

```
jellyfin_stats/
  svg.py        build_banner_card + helpers (pure SVG, no I/O)
  collector.py  GitHub Search queries (rate-limited)
  repos.py      discover_repos + humanize
generate.py     CLI entrypoint
banners/        generated SVGs, written by the daily workflow
```

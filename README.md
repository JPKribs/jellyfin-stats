# jellyfin-stats

Daily-regenerated SVG README banners for every public repo across
`jellyfin` and `jellyfin-labs`. Each repo gets two flavors:

- **plain** (`banners/plain/<repo>.svg`) — name + Jellyfin mark, static
- **complete** (`banners/complete/<repo>.svg`) — adds the trailing
  30-day activity summary (issues closed, PRs merged, contributors, new
  contributors). Mirrors the plain banner when nothing happened in the
  window, so the URL always resolves.

The `jellyfin` server gets the tagline "The Free Software Media
System"; everything else gets "Part of the Jellyfin Project".

## Embed

### Jellyfin

![Jellyfin plain](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/plain/jellyfin.svg)

```markdown
![Jellyfin](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/plain/jellyfin.svg)
```

![Jellyfin complete](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/complete/jellyfin.svg)

```markdown
![Jellyfin](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/complete/jellyfin.svg)
```

### Jellyfin Web

![Jellyfin Web plain](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/plain/jellyfin-web.svg)

```markdown
![Jellyfin Web](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/plain/jellyfin-web.svg)
```

![Jellyfin Web complete](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/complete/jellyfin-web.svg)

```markdown
![Jellyfin Web](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/complete/jellyfin-web.svg)
```

Same pattern for any other repo — substitute the slug in the URL.

## Generation

Regenerated daily at 00:00 UTC by
[`banners.yml`](.github/workflows/banners.yml). Trigger manually from
the Actions tab. The workflow needs Settings → Actions → General →
Workflow permissions → "Read and write permissions" enabled to commit
back to `main`.

Local generation:

```bash
pip install -r requirements.txt
python generate.py                          # all repos in default orgs
python generate.py --repo jellyfin-roku     # one repo
python generate.py --simple --repo jellyfin # layout iteration, no API
```

`GITHUB_TOKEN` is read from env or `gh auth token`. Without it the
Search API is rate-limited to 10 req/min (vs 30 authenticated) and full
sweeps get slow.

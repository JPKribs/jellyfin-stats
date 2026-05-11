# jellyfin-stats

Daily-regenerated SVG README banners for every public repo across
`jellyfin` and `jellyfin-labs`. Each repo gets two flavors:

- **plain** (`banners/plain/<repo>.svg`)
- **complete** (`banners/complete/<repo>.svg`)

The `jellyfin` server gets the tagline "The Free Software Media
System". Everything else gets "Part of the Jellyfin Project".

## Example Embeds

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

## Generation

Regenerated daily at 00:00 UTC.

Local generation:

```bash
pip install -r requirements.txt
python generate.py                          # all repos in default orgs
python generate.py --repo jellyfin-roku     # one repo
python generate.py --simple --repo jellyfin # layout iteration, no API
```

# jellyfin-stats

Daily-regenerated SVG README banners for every public repo across
`jellyfin` and `jellyfin-labs`. Each repo gets four flavors:

- **simple** (`banners/simple/<repo>.svg`)
- **contributor-stats** (`banners/contributor-stats/<repo>.svg`)
- **contributor-names** (`banners/contributor-names/<repo>.svg`) — same as
  `contributor-stats` with the last 30 days of contributor names falling
  Matrix-style behind the mark in a 5-row brick pattern (new contributors
  bolded; 25% opacity; SMIL-animated SVG; renders in browsers and GitHub
  `<img>` embeds)
- **contributor-icons** (`banners/contributor-icons/<repo>.svg`) — same as
  `contributor-stats` with a row of last-30-day contributor avatars in place
  of the mark; new contributors get a gradient ring (avatars inlined as
  base64 so they render in GitHub `<img>` embeds)

The `jellyfin` server gets the tagline "The Free Software Media
System". Everything else gets "Part of the Jellyfin Project".

## Example Embeds

### Jellyfin

![Jellyfin simple](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/simple/jellyfin.svg)

```markdown
![Jellyfin](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/simple/jellyfin.svg)
```

![Jellyfin contributor-stats](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-stats/jellyfin.svg)

```markdown
![Jellyfin](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-stats/jellyfin.svg)
```

![Jellyfin contributor-names](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-names/jellyfin.svg)

```markdown
![Jellyfin](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-names/jellyfin.svg)
```

![Jellyfin contributor-icons](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-icons/jellyfin.svg)

```markdown
![Jellyfin](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-icons/jellyfin.svg)
```

### Jellyfin Web

![Jellyfin Web simple](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/simple/jellyfin-web.svg)

```markdown
![Jellyfin Web](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/simple/jellyfin-web.svg)
```

![Jellyfin Web contributor-stats](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-stats/jellyfin-web.svg)

```markdown
![Jellyfin Web](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-stats/jellyfin-web.svg)
```

![Jellyfin Web contributor-names](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-names/jellyfin-web.svg)

```markdown
![Jellyfin Web](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-names/jellyfin-web.svg)
```

![Jellyfin Web contributor-icons](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-icons/jellyfin-web.svg)

```markdown
![Jellyfin Web](https://raw.githubusercontent.com/JPKribs/jellyfin-stats/main/banners/contributor-icons/jellyfin-web.svg)
```

## Generation

Regenerated daily at 00:00 UTC.

Each run produces four SVGs per repo — one in each of `banners/simple/`,
`banners/contributor-stats/`, `banners/contributor-names/`, and
`banners/contributor-icons/`.

Local generation:

```bash
pip install -r requirements.txt
python generate.py                       # all repos in default orgs
python generate.py --repo jellyfin-roku  # one repo
```

"""GitHub README banner snippets.

Drop-in replacement for the hand-maintained banner block at the top of each
Jellyfin repo's README. The image is the official jellyfin-ux logo banner;
only the heading and tagline differ per repo. The output is HTML embedded
in markdown — works in both a `.md` README and a plain HTML page.

The shape mirrors the existing convention:

    <img alt="Logo Banner" src=".../banner-logo-solid.svg?sanitize=true"/>
    <br/>

    <h1 align="center">Jellyfin</h1>
    <h3 align="center">The Free Software Media System</h3>

`jellyfin` (the server) gets its established tagline; every other repo
gets `Part of the Jellyfin Project`.
"""

LOGO_BANNER_URL = (
    "https://raw.githubusercontent.com/jellyfin/jellyfin-ux/master"
    "/branding/SVG/banner-logo-solid.svg?sanitize=true"
)

JELLYFIN_TAGLINE = "The Free Software Media System"
PROJECT_TAGLINE = "Part of the Jellyfin Project"


def tagline_for(repo: str) -> str:
    """Return the tagline for a repo's banner."""
    return JELLYFIN_TAGLINE if repo == "jellyfin" else PROJECT_TAGLINE


def build_banner(repo: str, display_name: str) -> str:
    """Return the GitHub README banner block for a repo."""
    return (
        f'<img alt="Logo Banner" src="{LOGO_BANNER_URL}"/>\n'
        f'<br/>\n\n'
        f'<h1 align="center">{display_name}</h1>\n'
        f'<h3 align="center">{tagline_for(repo)}</h3>\n'
    )

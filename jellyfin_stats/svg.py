"""SVG banner card for Jellyfin repo READMEs.

Output is standard SVG with kebab-case attribute names (`stroke-width`,
`font-size`, `stop-color`, …) so the file renders correctly both as a
standalone `.svg` and embedded in JSX/MDX (modern React parsers accept
either case). Colors follow Jellyfin branding (purple → cyan gradient
accent) and the established chart palette: green for PRs merged, red
for issues closed, yellow for contributors, purple for new
contributors. Text is explicit `#ffffff` against the dark zone so the
banner reads consistently regardless of the host page's theme.

No GitHub or YAML dependencies — pass in the data and get back the SVG.
"""


# MARK: - Palette + fonts

GRADIENT_START = "#AA5CC3"  # Jellyfin purple
GRADIENT_END = "#00A4DC"    # Jellyfin cyan
COLOR_PRS = "#22c55e"
COLOR_ISSUES = "#ef4444"
COLOR_CONTRIBS = "#eab308"

TITLE_FONT_FAMILY = "Plus Jakarta Sans, system-ui, -apple-system, Segoe UI, sans-serif"

JELLYFIN_TAGLINE = "The Free Software Media System"
PROJECT_TAGLINE = "Part of the Jellyfin Project"


# MARK: - Helpers

def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _banner_path(width: float, banner_h: float, radius: float = 10.0, inset: float = 0.75) -> str:
    """SVG path data for a banner with rounded top corners only.

    Sized to sit inside the card's outer rounded border (which uses the same
    `inset` and `radius`). The bottom edge is square so subsequent content
    butts flush against it instead of leaving curved dead-space.
    """
    right = width - inset
    return (
        f"M{inset:.2f},{inset + radius:.2f} "
        f"A{radius},{radius} 0 0 1 {inset + radius:.2f},{inset:.2f} "
        f"L{right - radius:.2f},{inset:.2f} "
        f"A{radius},{radius} 0 0 1 {right:.2f},{inset + radius:.2f} "
        f"L{right:.2f},{banner_h:.2f} "
        f"L{inset:.2f},{banner_h:.2f} Z"
    )


def _jellyfin_logo(x: float, y: float, size: float, gradient_id: str) -> str:
    """Render the official Jellyfin "J" mark filled with the brand gradient.

    Path data taken from `jellyfin-ux/branding/SVG/icon-transparent.svg`
    (CC BY-SA 4.0). The mark is two paths — the outer "J" frame (with an
    internal cutout via the even-odd fill rule) and the smaller inner blob
    that sits inside the cutout.
    """
    s = size / 512
    return (
        f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.5f})">'
        f'<path fill="url(#{gradient_id})" fill-rule="evenodd" '
        'd="M256,23.3c-61.6,0-259.8,359.4-229.6,420.1s429.3,60,459.2,0S317.6,23.3,256,23.3z'
        'M406.5,390.8c-19.6,39.3-281.1,39.8-300.9,0s110.1-275.3,150.4-275.3S426.1,351.4,406.5,390.8z"/>'
        f'<path fill="url(#{gradient_id})" '
        'd="M256,201.6c-20.4,0-86.2,119.3-76.2,139.4s142.5,19.9,152.4,0S276.5,201.6,256,201.6z"/>'
        '</g>'
    )


# MARK: - Banner cards

def _emit_top_zone(
    parts: list[str],
    *,
    width: int,
    title_h: int,
    banner_h: int,
    height: int,
    gradient_id: str,
    display_name: str,
    tagline: str,
    font: str,
) -> None:
    """Append the shared chrome (title strip + dark zone + J mark) to ``parts``.

    The dark zone fills from the bottom of the title strip down to the card's
    bottom edge — so the same fragment works for the plain banner (height ==
    title_h + banner_h) and the complete banner (height includes a stats
    zone below the mark).
    """
    parts.append(
        f'<path d="{_banner_path(width, title_h)}" fill="url(#{gradient_id})"/>'
    )
    parts.append(
        f'<text x="{width / 2:.1f}" y="51" text-anchor="middle" '
        f'font-size="33" font-weight="700" font-family="{font}" '
        f'fill="#ffffff">{_xml_escape(display_name)}</text>'
    )
    parts.append(
        f'<text x="{width / 2:.1f}" y="84" text-anchor="middle" '
        f'font-size="20" font-family="{font}" '
        f'fill="#ffffff" opacity="0.85">{_xml_escape(tagline)}</text>'
    )
    parts.append(
        f'<rect x="0.75" y="{title_h}" width="{width - 1.5}" '
        f'height="{height - title_h - 0.75}" fill="#000b25"/>'
    )
    mark_size = 150
    mark_x = width / 2 - mark_size / 2
    mark_y = title_h + (banner_h - mark_size) / 2
    parts.append(_jellyfin_logo(mark_x, mark_y, mark_size, gradient_id))


def _open_svg(width: int, height: int, gradient_id: str, label: str) -> list[str]:
    """Emit the `<svg>` opener + `<defs>` (gradient + rounded-card clipPath).

    The clipPath matches the outer rounded border so the dark fill below
    the title strip doesn't leak past the curve at the bottom corners.
    Callers are expected to wrap their inner content in a
    ``<g clip-path="url(#{gradient_id}-clip)">…</g>`` and emit the border
    after the closing ``</g>`` so the stroke renders un-clipped on top.
    """
    return [
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{_xml_escape(label)}">',
        f'<defs>'
        f'<linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{GRADIENT_START}"/>'
        f'<stop offset="100%" stop-color="{GRADIENT_END}"/>'
        f'</linearGradient>'
        f'<clipPath id="{gradient_id}-clip">'
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" '
        f'rx="10" ry="10"/>'
        f'</clipPath>'
        f'</defs>',
    ]


def _outer_border(width: int, height: int, gradient_id: str) -> str:
    return (
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" '
        f'rx="10" ry="10" fill="none" stroke="url(#{gradient_id})" stroke-width="1.5"/>'
    )


def build_banner_plain(repo: str, display_name: str, gradient_id: str) -> str:
    """Plain README banner: gradient title strip + Jellyfin "J" mark, no stats.

    Static — only changes when the repo is renamed (display name updates) or
    moves between the server and the rest (tagline updates). Useful for
    repos where you don't want a daily commit churning the README.
    """
    width = 1080
    title_h = 105
    banner_h = 216
    height = title_h + banner_h
    tagline = JELLYFIN_TAGLINE if repo == "jellyfin" else PROJECT_TAGLINE
    font = TITLE_FONT_FAMILY

    parts = _open_svg(width, height, gradient_id, display_name)
    parts.append(f'<g clip-path="url(#{gradient_id}-clip)">')
    _emit_top_zone(
        parts,
        width=width, title_h=title_h, banner_h=banner_h, height=height,
        gradient_id=gradient_id, display_name=display_name,
        tagline=tagline, font=font,
    )
    parts.append('</g>')
    parts.append(_outer_border(width, height, gradient_id))
    parts.append('</svg>')
    return ''.join(parts)


def build_banner_card(
    repo: str,
    display_name: str,
    closed: int,
    merged: int,
    contributors: int,
    new_contributors: int,
    gradient_id: str,
) -> str:
    """README banner SVG: gradient title strip, Jellyfin banner mark, 30-day summary.

    Layout (top to bottom):

      1. Gradient strip with `display_name` and the appropriate tagline
         (`The Free Software Media System` for `jellyfin`, `Part of the
         Jellyfin Project` for everything else).
      2. Black banner strip with the centered Jellyfin "J" mark, mirroring
         `jellyfin-ux/branding/SVG/banner-logo-solid.svg`.
      3. Stats row with the trailing 30-day summary — Issues Closed, PRs
         Merged, Contributors, New Contributors. Zero-valued counts are
         dropped; if everything is zero the row reads "No activity in the
         last 30 days".
    """
    width = 1080
    pad_x = 36
    content_w = width - 2 * pad_x

    title_h = 105
    banner_h = 216  # 5:1 aspect to match banner-logo-solid.svg
    stats_h = 159   # subtitle baseline at +123 with 36px below to card edge
    height = title_h + banner_h + stats_h

    tagline = JELLYFIN_TAGLINE if repo == "jellyfin" else PROJECT_TAGLINE
    font = TITLE_FONT_FAMILY  # one font throughout the banner

    parts = _open_svg(width, height, gradient_id, display_name)
    parts.append(f'<g clip-path="url(#{gradient_id}-clip)">')
    _emit_top_zone(
        parts,
        width=width, title_h=title_h, banner_h=banner_h, height=height,
        gradient_id=gradient_id, display_name=display_name,
        tagline=tagline, font=font,
    )

    # Stats row — trailing 30-day summary, white text against the dark area
    stats_y = title_h + banner_h
    items: list[tuple[int, str, str]] = []
    if closed:
        items.append((closed, "Issues Closed" if closed != 1 else "Issue Closed", COLOR_ISSUES))
    if merged:
        items.append((merged, "PRs Merged" if merged != 1 else "PR Merged", COLOR_PRS))
    if contributors:
        items.append((contributors, "Contributors" if contributors != 1 else "Contributor", COLOR_CONTRIBS))
    if new_contributors:
        items.append((new_contributors, "New Contributors" if new_contributors != 1 else "New Contributor", GRADIENT_START))

    label_baseline = stats_y + 33
    value_baseline = stats_y + 78
    subtitle_baseline = stats_y + 123

    if items:
        n = len(items)
        for i, (value, label, color) in enumerate(items):
            cx = pad_x + content_w * (2 * i + 1) / (2 * n)
            parts.append(
                f'<text x="{cx:.1f}" y="{label_baseline:.1f}" text-anchor="middle" '
                f'font-size="18" font-family="{font}" '
                f'fill="#ffffff" opacity="0.85">{_xml_escape(label)}</text>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{value_baseline:.1f}" text-anchor="middle" '
                f'font-size="36" font-weight="700" font-family="{font}" '
                f'fill="{color}">{value:,}</text>'
            )
        parts.append(
            f'<text x="{width / 2:.1f}" y="{subtitle_baseline:.1f}" text-anchor="middle" '
            f'font-size="15" font-family="{font}" '
            f'fill="#ffffff" opacity="0.6">Last 30 Days</text>'
        )
    else:
        parts.append(
            f'<text x="{width / 2:.1f}" y="{stats_y + stats_h / 2 + 7:.1f}" text-anchor="middle" '
            f'font-size="20" font-family="{font}" '
            f'fill="#ffffff" opacity="0.7">No activity in the last 30 days</text>'
        )

    parts.append('</g>')
    parts.append(_outer_border(width, height, gradient_id))
    parts.append('</svg>')
    return ''.join(parts)

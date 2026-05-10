"""Inline SVG generation for the Jellyfin stats cards.

Output is JSX-compatible (camelCased attribute names, no `class`) so the
strings render correctly when embedded in Docusaurus `.mdx` files. Colors
follow Jellyfin branding (purple → cyan gradient accent) and the established
chart palette: green for PRs merged, red for issues closed, yellow for
contributors. Labels use `currentColor` so the SVG adapts to the active
Docusaurus theme (light or dark).

These functions have no GitHub or YAML dependencies; pass in the data and
get back an SVG string.
"""

import math
from datetime import datetime
from typing import Optional

from .models import MonthlyStats


# MARK: - Palette

GRADIENT_START = "#AA5CC3"  # Jellyfin purple
GRADIENT_END = "#00A4DC"    # Jellyfin cyan
COLOR_PRS = "#22c55e"
COLOR_ISSUES = "#ef4444"
COLOR_CONTRIBS = "#eab308"
COLOR_LINK = "#00A4DC"

FONT_FAMILY = "system-ui, -apple-system, Segoe UI, sans-serif"
TITLE_FONT_FAMILY = "Plus Jakarta Sans, system-ui, -apple-system, Segoe UI, sans-serif"

# Approximate per-character widths at 12px, used for soft-wrapping the
# contributor lines. These are eyeballed for the system sans-serif stack;
# they do not need to be exact, only conservative enough that the wrap point
# stays inside the card on common renderers.
CHAR_WIDTH = 6.6
CHAR_WIDTH_BOLD = 7.1


# MARK: - README banner card

JELLYFIN_TAGLINE = "The Free Software Media System"
PROJECT_TAGLINE = "Part of the Jellyfin Project"


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

    All text is in Plus Jakarta Sans for brand consistency.
    """
    width = 720
    title_h = 70
    banner_h = 144  # 5:1 aspect to match banner-logo-solid.svg
    stats_h = 60
    height = title_h + banner_h + stats_h

    tagline = JELLYFIN_TAGLINE if repo == "jellyfin" else PROJECT_TAGLINE
    font = TITLE_FONT_FAMILY  # one font throughout the banner

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{_xml_escape(display_name)}">'
    )
    parts.append(
        f'<defs><linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stopColor="{GRADIENT_START}"/>'
        f'<stop offset="100%" stopColor="{GRADIENT_END}"/>'
        '</linearGradient></defs>'
    )

    # 1. Title strip — gradient with display name + tagline
    parts.append(
        f'<path d="{_banner_path(width, title_h)}" fill="url(#{gradient_id})"/>'
    )
    parts.append(
        f'<text x="{width / 2:.1f}" y="34" textAnchor="middle" '
        f'fontSize="22" fontWeight="700" fontFamily="{font}" '
        f'fill="#ffffff">{_xml_escape(display_name)}</text>'
    )
    parts.append(
        f'<text x="{width / 2:.1f}" y="56" textAnchor="middle" '
        f'fontSize="13" fontFamily="{font}" '
        f'fill="#ffffff" opacity="0.85">{_xml_escape(tagline)}</text>'
    )

    # 2. Jellyfin banner strip — black background with the centered J mark
    banner_y = title_h
    parts.append(
        f'<rect x="0.75" y="{banner_y}" width="{width - 1.5}" height="{banner_h}" '
        'fill="#000b25"/>'
    )
    mark_size = 100
    mark_x = width / 2 - mark_size / 2
    mark_y = banner_y + (banner_h - mark_size) / 2
    parts.append(_jellyfin_logo(mark_x, mark_y, mark_size, gradient_id))

    # 3. Stats row — trailing 30-day summary
    stats_y = banner_y + banner_h
    items: list[tuple[int, str, str]] = []
    if closed:
        items.append((closed, "Issues Closed" if closed != 1 else "Issue Closed", COLOR_ISSUES))
    if merged:
        items.append((merged, "PRs Merged" if merged != 1 else "PR Merged", COLOR_PRS))
    if contributors:
        items.append((contributors, "Contributors" if contributors != 1 else "Contributor", COLOR_CONTRIBS))
    if new_contributors:
        items.append((new_contributors, "New Contributors" if new_contributors != 1 else "New Contributor", GRADIENT_START))

    pad_x = 24
    content_w = width - 2 * pad_x
    stats_baseline = stats_y + 30

    if items:
        n = len(items)
        for i, (value, label, color) in enumerate(items):
            cx = pad_x + content_w * (2 * i + 1) / (2 * n)
            parts.append(
                f'<text x="{cx:.1f}" y="{stats_baseline:.1f}" textAnchor="middle" '
                f'fontSize="13" fontFamily="{font}" fill="currentColor">'
                f'<tspan fontWeight="700" fontSize="15" fill="{color}">{value:,}</tspan>'
                f'<tspan> {_xml_escape(label)}</tspan></text>'
            )
        parts.append(
            f'<text x="{width / 2:.1f}" y="{stats_baseline + 18:.1f}" textAnchor="middle" '
            f'fontSize="10" fontFamily="{font}" '
            f'fill="currentColor" opacity="0.55">Last 30 Days</text>'
        )
    else:
        parts.append(
            f'<text x="{width / 2:.1f}" y="{stats_baseline + 6:.1f}" textAnchor="middle" '
            f'fontSize="13" fontFamily="{font}" '
            f'fill="currentColor" opacity="0.6">No activity in the last 30 days</text>'
        )

    # Outer rounded border last so it sits over the title/banner strip edges
    parts.append(
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" '
        f'rx="10" ry="10" fill="none" stroke="url(#{gradient_id})" strokeWidth="1.5"/>'
    )

    parts.append('</svg>')
    return ''.join(parts)


# MARK: - Repo stats card

NameList = list[tuple[str, str]]  # list of (name, url)


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _banner_path(width: float, banner_h: float, radius: float = 10.0, inset: float = 0.75) -> str:
    """Return SVG path data for a banner with rounded top corners only.

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


def _layout_contrib_line(
    label: str,
    names: NameList,
    max_width: float,
) -> tuple[list[list[tuple[str, object]]], float]:
    """Lay out a single ``Label: name1, name2, ...`` row across physical lines.

    Returns ``(lines, indent_width)`` where ``lines`` is a list of physical
    lines (each a list of ``(kind, value)`` items) and ``indent_width`` is the
    pixel offset that continuation lines should start at so they align under
    where the names began on the first line.

    Items per line use these ``kind`` values:
      - ``"label"`` → bold label text
      - ``"sep"``   → ", " separator (no link)
      - ``"name"``  → ``(name, url)`` tuple, rendered as a link if url is set
    """
    label_text = f"{label}:"
    label_w = len(label_text) * CHAR_WIDTH_BOLD + CHAR_WIDTH  # bold + trailing space

    lines: list[list[tuple[str, object]]] = [[("label", label_text)]]
    cursor = label_w

    for i, (name, url) in enumerate(names):
        sep = ", " if i > 0 else ""
        sep_w = len(sep) * CHAR_WIDTH
        name_w = len(name) * CHAR_WIDTH

        if cursor + sep_w + name_w > max_width and lines[-1] and i > 0:
            lines.append([])
            cursor = label_w
            sep = ""
            sep_w = 0

        if sep:
            lines[-1].append(("sep", sep))
        lines[-1].append(("name", (name, url)))
        cursor += sep_w + name_w

    return lines, label_w


def _render_contrib_line_svg(
    label: str,
    names: NameList,
    x: float,
    y: float,
    line_height: float,
    max_width: float,
) -> tuple[list[str], float]:
    """Render one labelled contributor row to SVG, wrapping as needed.

    Returns (svg_fragments, height_used_in_pixels).
    """
    physical_lines, indent_w = _layout_contrib_line(label, names, max_width)

    fragments: list[str] = []
    for line_idx, items in enumerate(physical_lines):
        line_x = x if line_idx == 0 else x + indent_w
        line_y = y + line_idx * line_height

        text_open = (
            f'<text x="{line_x:.1f}" y="{line_y:.1f}" fontSize="12" '
            f'fontFamily="{FONT_FAMILY}" fill="currentColor">'
        )
        chunks = [text_open]
        for kind, value in items:
            if kind == "label":
                chunks.append(
                    f'<tspan fontWeight="700">{_xml_escape(str(value))}</tspan>'
                    '<tspan> </tspan>'
                )
            elif kind == "sep":
                chunks.append(f'<tspan opacity="0.65">{_xml_escape(str(value))}</tspan>')
            elif kind == "name":
                name, url = value  # type: ignore[misc]
                escaped_name = _xml_escape(name)
                if url:
                    chunks.append(
                        f'<a href="{_xml_escape(url)}">'
                        f'<tspan fill="{COLOR_LINK}">{escaped_name}</tspan>'
                        '</a>'
                    )
                else:
                    chunks.append(f'<tspan>{escaped_name}</tspan>')
        chunks.append('</text>')
        fragments.append(''.join(chunks))

    height_used = len(physical_lines) * line_height
    return fragments, height_used


def _jellyfin_logo(x: float, y: float, size: float, gradient_id: str) -> str:
    """Render the official Jellyfin mark.

    Path data is taken verbatim from
    `jellyfin-ux/branding/SVG/icon-transparent.svg` (CC BY-SA 4.0). The mark
    uses two paths — the outer "J" frame (with an internal cutout via the
    even-odd fill rule) and the smaller inner blob that sits inside the
    cutout.
    """
    s = size / 512
    return (
        f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.5f})">'
        f'<path fill="url(#{gradient_id})" fillRule="evenodd" '
        'd="M256,23.3c-61.6,0-259.8,359.4-229.6,420.1s429.3,60,459.2,0S317.6,23.3,256,23.3z'
        'M406.5,390.8c-19.6,39.3-281.1,39.8-300.9,0s110.1-275.3,150.4-275.3S426.1,351.4,406.5,390.8z"/>'
        f'<path fill="url(#{gradient_id})" '
        'd="M256,201.6c-20.4,0-86.2,119.3-76.2,139.4s142.5,19.9,152.4,0S276.5,201.6,256,201.6z"/>'
        '</g>'
    )


def _award_icon(x: float, y: float, size: float) -> str:
    """Lucide-style award icon for the top community contributors column."""
    s = size / 24
    return (
        f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.4f})" '
        'fill="none" stroke="currentColor" strokeWidth="2" '
        'strokeLinecap="round" strokeLinejoin="round">'
        '<circle cx="12" cy="8" r="6"/>'
        '<path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>'
        '</g>'
    )


def _sparkles_icon(x: float, y: float, size: float) -> str:
    """Lucide-style sparkles icon for the new contributors column."""
    s = size / 24
    return (
        f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.4f})" '
        'fill="none" stroke="currentColor" strokeWidth="2" '
        'strokeLinecap="round" strokeLinejoin="round">'
        '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063L2.365 12.481a.5.5 0 0 1 0-.962'
        'L8.5 9.937A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0'
        'L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .963'
        'L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>'
        '<path d="M20 3v4"/><path d="M22 5h-4"/>'
        '</g>'
    )


def _donut_slice(
    cx: float,
    cy: float,
    r_outer: float,
    r_inner: float,
    a1: float,
    a2: float,
    color: str,
) -> str:
    """Render a single donut slice as an SVG path.

    Angles in radians (SVG convention: 0 = right, π/2 = down). The caller is
    responsible for keeping the sweep below 2π — full-circle slices should be
    split into two arcs by the caller to avoid the well-known degenerate case
    where start and end points coincide.
    """
    sweep = a2 - a1
    large_arc = 1 if sweep > math.pi else 0
    x1o = cx + r_outer * math.cos(a1)
    y1o = cy + r_outer * math.sin(a1)
    x2o = cx + r_outer * math.cos(a2)
    y2o = cy + r_outer * math.sin(a2)
    x1i = cx + r_inner * math.cos(a1)
    y1i = cy + r_inner * math.sin(a1)
    x2i = cx + r_inner * math.cos(a2)
    y2i = cy + r_inner * math.sin(a2)
    return (
        f'<path d="M{x1o:.2f},{y1o:.2f} '
        f'A{r_outer},{r_outer} 0 {large_arc} 1 {x2o:.2f},{y2o:.2f} '
        f'L{x2i:.2f},{y2i:.2f} '
        f'A{r_inner},{r_inner} 0 {large_arc} 0 {x1i:.2f},{y1i:.2f} Z" '
        f'fill="{color}"/>'
    )


def _render_pie(
    slices: list[tuple[str, int, str]],
    cx: float,
    cy: float,
    r_outer: float,
    r_inner: float,
) -> list[str]:
    """Render a donut chart centred at ``(cx, cy)``.

    `slices` items are ``(label, count, color)``. Slices with zero count are
    dropped. Returns SVG fragments for the donut wedges plus a centred total
    count label inside the donut hole.
    """
    fragments: list[str] = []
    non_zero = [s for s in slices if s[1] > 0]
    if not non_zero:
        return fragments

    total = sum(s[1] for s in non_zero)

    if len(non_zero) == 1:
        # Full ring — split at top/bottom to avoid the 2π degenerate path.
        color = non_zero[0][2]
        fragments.append(_donut_slice(cx, cy, r_outer, r_inner, -math.pi / 2, math.pi / 2, color))
        fragments.append(_donut_slice(cx, cy, r_outer, r_inner, math.pi / 2, 3 * math.pi / 2, color))
    else:
        angle = -math.pi / 2  # start at 12 o'clock, sweep clockwise
        for _label, count, color in non_zero:
            a2 = angle + (count / total) * 2 * math.pi
            fragments.append(_donut_slice(cx, cy, r_outer, r_inner, angle, a2, color))
            angle = a2

    fragments.append(
        f'<text x="{cx:.1f}" y="{cy + 8:.1f}" textAnchor="middle" '
        f'fontSize="22" fontWeight="700" fontFamily="{TITLE_FONT_FAMILY}" '
        f'fill="currentColor">{total:,}</text>'
    )

    return fragments


def _render_pie_legend(
    slices: list[tuple[str, int, str]],
    x: float,
    cy: float,
    row_height: float = 32,
) -> list[str]:
    """Render the pie legend column to the right of the donut, vertically
    centred on ``cy``. Each row shows a swatch, label, and ``count (xx%)``.
    """
    fragments: list[str] = []
    non_zero = [s for s in slices if s[1] > 0]
    if not non_zero:
        return fragments

    total = sum(s[1] for s in non_zero)
    legend_top = cy - (len(non_zero) - 1) * row_height / 2

    for i, (label, count, color) in enumerate(non_zero):
        baseline = legend_top + i * row_height
        pct = (count / total) * 100 if total else 0
        fragments.append(
            f'<circle cx="{x:.1f}" cy="{baseline - 4:.1f}" r="5" fill="{color}"/>'
        )
        fragments.append(
            f'<text x="{x + 12:.1f}" y="{baseline:.1f}" textAnchor="start" '
            f'fontSize="12" fontWeight="600" fontFamily="{FONT_FAMILY}" '
            f'fill="currentColor">{_xml_escape(label)}</text>'
        )
        fragments.append(
            f'<text x="{x + 12:.1f}" y="{baseline + 14:.1f}" textAnchor="start" '
            f'fontSize="11" fontFamily="{FONT_FAMILY}" '
            f'fill="currentColor" opacity="0.7">{count:,} ({pct:.0f}%)</text>'
        )

    return fragments


NEW_CONTRIB_SUB_COLS = 3
NEW_CONTRIB_MAX_ROWS = 3


def _render_new_contributors_column(
    items: list[tuple[str, str, bool]],
    col_x: float,
    col_w: float,
    label_y: float,
    names_y_start: float,
    name_height: float,
    icon_renderer,
    icon_size: float = 14.0,
    char_width: float = 6.6,
    sub_cols: int = NEW_CONTRIB_SUB_COLS,
    max_rows: int = NEW_CONTRIB_MAX_ROWS,
) -> list[str]:
    """Render the New Contributors column under a single header.

    Names fill a ``sub_cols × max_rows`` grid row-major (left-to-right,
    top-to-bottom). Names whose handle is wider than a sub-column are silently
    dropped, as are any that fall past the visible slot count. If no name
    fits, the section renders nothing — including no header — so an empty
    repo doesn't leave a stranded subheader.
    """
    parts: list[str] = []

    # Pad the names inside the section so they don't butt against the vertical
    # divider lines that flank the section.
    inner_pad = 14
    inner_x = col_x + inner_pad
    inner_w = col_w - 2 * inner_pad
    sub_col_w = inner_w / sub_cols

    fitting: list[tuple[str, str]] = []
    for name, url, _is_bold in items:
        if len(name) * char_width <= sub_col_w - 6:
            fitting.append((name, url))

    visible = fitting[: sub_cols * max_rows]
    if not visible:
        return parts

    label = "New Contributors"

    # Center the whole icon + label cluster on the section center so it lines
    # up with the middle sub-column's name center below.
    cluster_cx = col_x + col_w / 2
    label_w_approx = len(label) * 7.0
    icon_gap = 5.0
    cluster_w = icon_size + icon_gap + label_w_approx
    icon_x = cluster_cx - cluster_w / 2
    icon_y = label_y - icon_size + 1
    label_center_x = cluster_cx + (icon_size + icon_gap) / 2

    parts.append(icon_renderer(icon_x, icon_y))
    parts.append(
        f'<text x="{label_center_x:.1f}" y="{label_y:.1f}" textAnchor="middle" '
        f'fontSize="12" fontWeight="600" fontFamily="{FONT_FAMILY}" '
        f'fill="currentColor" opacity="0.9">{_xml_escape(label)}</text>'
    )

    # When only one or two names are visible, centring them on the section
    # (rather than parking them in left-most sub-columns) reads as a
    # deliberate small list instead of a half-empty grid.
    n_visible = len(visible)
    section_cx = col_x + col_w / 2

    # Row-major distribution so names fill left-to-right, top-to-bottom.
    # Reads alphabetically when input is sorted, and avoids leaving a
    # whole sub-column empty when there are fewer names than slots.
    # Each name is centered on its sub-column's center so the grid feels
    # visually balanced (rather than left-aligned) inside the section.
    for idx, (name, url) in enumerate(visible):
        if n_visible == 1:
            sub_col_cx = section_cx
            y = names_y_start
        elif n_visible == 2:
            # Place the two names at the 1/4 and 3/4 marks of the section
            # so they balance around the centre.
            sub_col_cx = col_x + col_w * (2 * idx + 1) / 4
            y = names_y_start
        else:
            col_idx = idx % sub_cols
            row_idx = idx // sub_cols
            sub_col_cx = inner_x + (col_idx + 0.5) * sub_col_w
            y = names_y_start + row_idx * name_height
        text_open = (
            f'<text x="{sub_col_cx:.1f}" y="{y:.1f}" textAnchor="middle" '
            f'fontSize="12" fontFamily="{FONT_FAMILY}"'
        )
        if url:
            parts.append(
                f'<a href="{_xml_escape(url)}">'
                f'{text_open} fill="{COLOR_LINK}">{_xml_escape(name)}</text>'
                '</a>'
            )
        else:
            parts.append(f'{text_open} fill="currentColor">{_xml_escape(name)}</text>')

    return parts


def _render_column(
    label: str,
    items: list[tuple[str, str, bool]],
    cx: float,
    label_y: float,
    name_y_start: float,
    name_height: float,
    icon_renderer,
    icon_size: float = 14.0,
) -> list[str]:
    """Render one of the three name columns.

    `items` are ``(name, url, is_bold)`` tuples; names render centered in the
    column with optional bolding (used to highlight maintainers in the team
    column). `icon_renderer(x, y)` draws the column's leading icon to the left
    of the label text.
    """
    parts: list[str] = []

    # Center the *whole icon + label cluster* on the column center so the
    # names below (also centered at cx) line up under the visual midpoint of
    # the header rather than under the label text alone.
    label_w = len(label) * 7.0
    icon_gap = 5.0
    cluster_w = icon_size + icon_gap + label_w
    icon_x = cx - cluster_w / 2
    icon_y = label_y - icon_size + 1
    label_center_x = cx + (icon_size + icon_gap) / 2

    parts.append(icon_renderer(icon_x, icon_y))
    parts.append(
        f'<text x="{label_center_x:.1f}" y="{label_y:.1f}" textAnchor="middle" '
        f'fontSize="12" fontWeight="600" fontFamily="{FONT_FAMILY}" '
        f'fill="currentColor" opacity="0.9">{_xml_escape(label)}</text>'
    )

    for j, (name, url, is_bold) in enumerate(items):
        ny = name_y_start + j * name_height
        weight = "700" if is_bold else "400"
        text_open = (
            f'<text x="{cx:.1f}" y="{ny:.1f}" textAnchor="middle" '
            f'fontSize="12" fontWeight="{weight}" fontFamily="{FONT_FAMILY}"'
        )
        if url:
            parts.append(
                f'<a href="{_xml_escape(url)}">'
                f'{text_open} fill="{COLOR_LINK}">{_xml_escape(name)}</text>'
                '</a>'
            )
        else:
            parts.append(f'{text_open} fill="currentColor">{_xml_escape(name)}</text>')

    return parts


def repo_stats_card(
    title: str,
    closed: int,
    merged: int,
    contributors: int,
    gradient_id: str,
    maintainers: Optional[NameList] = None,
    team_contributors: Optional[NameList] = None,
    top_contributors: Optional[NameList] = None,
    new_contributors: Optional[NameList] = None,
) -> str:
    """Render the repo stats card.

    Layout, top to bottom:

    1. **Banner** — gradient-filled strip with the repo title in white bold
       Plus Jakarta Sans.
    2. **Stats row** — ``<count> Issues Closed   <count> PRs Merged   <count> Contributors``,
       counts colored, labels in body weight; zero-valued stats are skipped.
    3. **Divider** — subtle horizontal rule.
    4. **Two columns**:
         * **Team** (Jellyfin logo): alphabetized union of maintainers and
           team contributors with maintainers in bold.
         * **Donut chart**: people-count breakdown across Team / Returning
           Community / New, with a legend showing the count and percentage of
           each slice. ``top_contributors`` is accepted for API compatibility
           but is not currently surfaced in the card.

    Every team name with a URL is wrapped in an ``<a>`` so it remains clickable.
    Returns an empty string when nothing renderable was supplied.
    """
    has_stats = bool(closed or merged or contributors)
    _ = top_contributors  # accepted for API compatibility; not used in the layout.

    # Combine maintainers + team contributors. Maintainers come first so the
    # dedup pass keeps them (in case a team contributor name also appears as a
    # maintainer). Then the union is sorted case-insensitively.
    seen: set[str] = set()
    team_combined: list[tuple[str, str, bool]] = []
    for name, url in (maintainers or []):
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        team_combined.append((name, url, True))
    for name, url in (team_contributors or []):
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        team_combined.append((name, url, False))
    team_combined.sort(key=lambda t: t[0].lower())

    new_list: list[tuple[str, str, bool]] = [
        (n, u, False) for n, u in (new_contributors or [])
    ]

    # Pie data — counts the number of people in each contributor category.
    # `contributors` (from RepoStats.unique_contributors) is the total unique
    # author count for the period; subtracting team and new gives "returning
    # community" contributors, clamped at zero in case of any double-counting.
    team_count = len(team_combined)
    new_count = len(new_list)
    community_count = max(0, contributors - team_count - new_count)

    # Pie only appears when there's something *interesting* to show — that is,
    # at least one non-team contributor. A single 100%-Team slice doesn't add
    # information, so we suppress the chart in that case.
    has_pie = (new_count > 0) or (community_count > 0)
    pie_total = (team_count + new_count + community_count) if has_pie else 0

    # Collapse mode: when only team members contributed (no new, no returning
    # community), the card shows just the names — no Team header, no New
    # section, no pie. The names ARE the story for the period.
    collapse_to_team = bool(team_combined) and not new_list and not has_pie

    has_bottom = bool(team_combined or new_list or has_pie)

    if not (title or has_stats or has_bottom):
        return ""

    width = 720
    pad_x = 24
    content_width = width - 2 * pad_x
    name_height = 18

    # Vertical layout. Stats row gains a touch more space above to breathe a
    # little under the gradient banner.
    banner_h = 40 if title else 0
    stats_h = 30 if has_stats else 0
    divider_pad = 14 if has_bottom and (banner_h or stats_h) else 0

    # Bottom block — three sections:
    #   1. Team list           (centered names, vertical)
    #   2. New Contributors    (single header, names split into 2 sub-columns)
    #   3. Donut + legend      (right-aligned, legend on the leading side)
    bottom_top = banner_h + stats_h + divider_pad
    label_h = 28  # vertical reserve from section top to first name baseline

    # ── Adaptive horizontal layout ────────────────────────────────────────
    # Team column width hugs the longest member name (or the "Team" header,
    # whichever is wider) plus a small inset, clamped to a sane range. This
    # keeps long names like "anultravioletaurora" or "Jean-Pierre Bachmann"
    # from spilling past the divider while still letting tiny lists render
    # in a narrow column.
    char_w_regular = 6.6
    char_w_bold = 7.0
    team_inner_pad = 12  # extra breathing room between names and the divider
    team_header_label = "Team"
    if team_combined:
        longest_team = max(len(n) for n, _u, _b in team_combined)
        team_name_w = longest_team * char_w_regular
        team_header_w = 14 + 5 + len(team_header_label) * char_w_bold  # icon + gap + bold "Team"
        team_col_w = max(team_name_w, team_header_w) + 2 * team_inner_pad
        team_col_w = max(team_col_w, content_width * 0.14)
        team_col_w = min(team_col_w, content_width * 0.40)
    else:
        longest_team = 0
        team_col_w = 0

    pie_col_w = content_width * 0.32 if has_pie else 0
    new_col_w = max(0, content_width - team_col_w - pie_col_w)

    # Pick the largest sub-column count (3 → 2 → 1) that still fits the
    # longest new-contributor handle inside a sub-column.
    #
    # When the team is both deep (≥5 members) and wide (longest name ≥15
    # chars), prefer starting from 2 sub-columns so the New grid doesn't end
    # up cramped opposite a tall team list — visually the card balances
    # better with bigger New cells in that case.
    new_inner_pad = 14
    if new_list:
        longest_new = max(len(n) for n, _u, _b in new_list)
        new_name_w = longest_new * char_w_regular
        new_inner_w = max(0, new_col_w - 2 * new_inner_pad)
        prefer_two = len(team_combined) >= 5 and longest_team >= 15
        new_sub_cols = 2 if prefer_two else NEW_CONTRIB_SUB_COLS
        while new_sub_cols > 1 and (new_inner_w / new_sub_cols) - 6 < new_name_w:
            new_sub_cols -= 1
    else:
        new_sub_cols = NEW_CONTRIB_SUB_COLS

    team_block_h = (label_h + len(team_combined) * name_height) if team_combined else 0
    pie_block_h = 98 if has_pie else 0

    # New Contributors row cap grows to match the tallest sibling section so
    # large repos (long team list or tall pie) don't artificially clip the
    # New list. The card's height is bounded by the tallest section anyway.
    available_h = max(team_block_h, pie_block_h, label_h + NEW_CONTRIB_MAX_ROWS * name_height)
    new_max_rows = max(NEW_CONTRIB_MAX_ROWS, (available_h - label_h) // name_height)
    new_visible = min(len(new_list), new_sub_cols * new_max_rows)
    new_rows_used = (
        (new_visible + new_sub_cols - 1) // new_sub_cols
        if new_visible else 0
    )
    new_block_h = (label_h + new_rows_used * name_height) if new_list else 0

    if collapse_to_team:
        # Just centered names, slightly larger row spacing so a small list
        # doesn't read as cramped. Cap at a sensible minimum so even a
        # single name has breathing room.
        collapse_row_h = 22
        bottom_h = max(48, len(team_combined) * collapse_row_h + 16)
    else:
        bottom_h = max(team_block_h, new_block_h, pie_block_h)
    bottom_pad = 12 if has_bottom else 8

    height = bottom_top + bottom_h + bottom_pad

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{_xml_escape(title) if title else "Repository stats"}">'
    )
    parts.append(
        f'<defs><linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stopColor="{GRADIENT_START}"/>'
        f'<stop offset="100%" stopColor="{GRADIENT_END}"/>'
        '</linearGradient></defs>'
    )

    if title:
        parts.append(
            f'<path d="{_banner_path(width, banner_h)}" fill="url(#{gradient_id})"/>'
        )
        parts.append(
            f'<text x="{width / 2:.1f}" y="{banner_h / 2 + 6:.1f}" textAnchor="middle" '
            f'fontSize="17" fontWeight="700" fontFamily="{TITLE_FONT_FAMILY}" '
            f'fill="#ffffff">{_xml_escape(title)}</text>'
        )

    parts.append(
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" '
        f'rx="10" ry="10" fill="none" stroke="url(#{gradient_id})" strokeWidth="1.5"/>'
    )

    if has_stats:
        stats_baseline = banner_h + 22
        stat_items: list[tuple[int, str, str]] = []
        if closed:
            stat_items.append((closed, "Issues Closed" if closed != 1 else "Issue Closed", COLOR_ISSUES))
        if merged:
            stat_items.append((merged, "PRs Merged" if merged != 1 else "PR Merged", COLOR_PRS))
        if contributors:
            stat_items.append((contributors, "Contributors" if contributors != 1 else "Contributor", COLOR_CONTRIBS))

        n = len(stat_items)
        for i, (value, label, color) in enumerate(stat_items):
            cx = pad_x + content_width * (2 * i + 1) / (2 * n)
            parts.append(
                f'<text x="{cx:.1f}" y="{stats_baseline:.1f}" textAnchor="middle" '
                f'fontSize="13" fontFamily="{FONT_FAMILY}" fill="currentColor">'
                f'<tspan fontWeight="700" fontSize="15" fill="{color}">{value:,}</tspan>'
                f'<tspan> {_xml_escape(label)}</tspan></text>'
            )

    if has_bottom and (banner_h or stats_h):
        divider_y = banner_h + stats_h + 8
        parts.append(
            f'<line x1="{pad_x}" y1="{divider_y:.1f}" x2="{width - pad_x}" y2="{divider_y:.1f}" '
            'stroke="currentColor" strokeWidth="0.5" opacity="0.2"/>'
        )

    if collapse_to_team:
        # Render just the team names — centered horizontally, vertically
        # spaced inside the bottom block. No Team header, no dividers, no pie.
        collapse_row_h = 22
        n = len(team_combined)
        block_h_used = n * collapse_row_h
        first_baseline = bottom_top + (bottom_h - block_h_used) / 2 + collapse_row_h - 4
        cx = pad_x + content_width / 2
        for i, (name, url, is_maint) in enumerate(team_combined):
            y = first_baseline + i * collapse_row_h
            weight = "700" if is_maint else "500"
            text_open = (
                f'<text x="{cx:.1f}" y="{y:.1f}" textAnchor="middle" '
                f'fontSize="14" fontWeight="{weight}" fontFamily="{FONT_FAMILY}"'
            )
            if url:
                parts.append(
                    f'<a href="{_xml_escape(url)}">'
                    f'{text_open} fill="{COLOR_LINK}">{_xml_escape(name)}</text>'
                    '</a>'
                )
            else:
                parts.append(f'{text_open} fill="currentColor">{_xml_escape(name)}</text>')
    elif has_bottom:
        # Section widths were computed adaptively above based on team-name
        # length and remaining space for New Contributors.
        team_col_cx = pad_x + team_col_w / 2
        new_col_x = pad_x + team_col_w
        pie_section_x = new_col_x + new_col_w

        label_y = bottom_top + 14
        names_y_start = label_y + 24  # extra padding between subheader and names

        # Partial vertical dividers between sections — subtle, inset from the
        # top/bottom so they don't reach the upper horizontal divider or the
        # card edge below.
        #
        # When there are no new contributors, the layout reduces to two
        # sections (Team + Pie) and we emit a single divider between them
        # rather than the two that would normally bracket the New section.
        divider_inset = 10
        v_top = bottom_top + divider_inset
        v_bot = bottom_top + bottom_h - divider_inset
        if new_list:
            divider_xs = (new_col_x, pie_section_x)
        elif team_combined and has_pie:
            # Place a single divider centred in the empty middle gap so the
            # team and pie clusters read as two distinct cells.
            divider_xs = ((new_col_x + pie_section_x) / 2,)
        else:
            divider_xs = ()
        for sep_x in divider_xs:
            parts.append(
                f'<line x1="{sep_x:.1f}" y1="{v_top:.1f}" '
                f'x2="{sep_x:.1f}" y2="{v_bot:.1f}" '
                'stroke="currentColor" strokeWidth="0.5" opacity="0.18"/>'
            )

        if team_combined:
            parts.extend(_render_column(
                "Team", team_combined, team_col_cx,
                label_y, names_y_start, name_height,
                lambda x, y: _jellyfin_logo(x, y, 14, gradient_id),
            ))

        if new_list:
            parts.extend(_render_new_contributors_column(
                new_list, new_col_x, new_col_w,
                label_y, names_y_start, name_height,
                lambda x, y: _sparkles_icon(x, y, 14),
                sub_cols=new_sub_cols,
                max_rows=new_max_rows,
            ))

        if has_pie:
            pie_slices = [
                ("Team", team_count, GRADIENT_START),
                ("Recurring", community_count, GRADIENT_END),
                ("New", new_count, COLOR_CONTRIBS),
            ]
            r_outer = 44.0
            r_inner = 30.0
            card_right = pad_x + content_width
            donut_cx = card_right - r_outer - 4  # right-aligned in the card
            donut_cy = bottom_top + bottom_h / 2
            # Pull the legend tight to the donut: its rightmost text ends a
            # few pixels left of the donut's edge. ~92px is enough for the
            # "Recurring" label, which is the widest of the three rows.
            legend_block_w = 92
            legend_gap = 8
            legend_x = donut_cx - r_outer - legend_gap - legend_block_w
            parts.extend(_render_pie_legend(pie_slices, legend_x, donut_cy))
            parts.extend(_render_pie(pie_slices, donut_cx, donut_cy, r_outer, r_inner))

    parts.append("</svg>")
    return "".join(parts)


# MARK: - Activity sparkline

def activity_chart(monthly_stats: list[MonthlyStats], gradient_id: str) -> str:
    """Render a multi-line activity chart as inline SVG.

    Plots merged PRs, closed issues, and unique contributors across the months
    in `monthly_stats`. Each data point is a small circle with a `<title>`
    element so browsers surface the underlying value as a hover tooltip.

    The chart sits inside the same gradient-bordered card chrome as the repo
    stats and releases tables — a banner with a white Plus Jakarta Sans title
    across the top, then the plot area below.
    """
    if not monthly_stats:
        return ""

    width = 720
    banner_h = 40
    plot_left = 56
    plot_right = 660
    plot_top = banner_h + 30
    plot_bottom = plot_top + 200
    height = plot_bottom + 60  # room for x-axis labels and legend
    plot_w = plot_right - plot_left
    plot_h = plot_bottom - plot_top

    n = len(monthly_stats)
    spacing = plot_w / max(n - 1, 1)

    max_value = max(
        max(m.merged_prs, m.closed_issues, m.contributors) for m in monthly_stats
    )
    y_max = max(((max_value + 99) // 100) * 100, 100)

    def x_for(i: int) -> float:
        return plot_left + i * spacing if n > 1 else (plot_left + plot_right) / 2

    def y_for(value: int) -> float:
        return plot_bottom - (value / y_max) * plot_h

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Activity by month">'
    )
    parts.append(
        f'<defs><linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stopColor="{GRADIENT_START}"/>'
        f'<stop offset="100%" stopColor="{GRADIENT_END}"/>'
        '</linearGradient></defs>'
    )

    parts.append(
        f'<path d="{_banner_path(width, banner_h)}" fill="url(#{gradient_id})"/>'
    )
    parts.append(
        f'<text x="{width / 2:.1f}" y="{banner_h / 2 + 6:.1f}" textAnchor="middle" '
        f'fontSize="17" fontWeight="700" fontFamily="{TITLE_FONT_FAMILY}" '
        'fill="#ffffff">Activity by Month</text>'
    )

    parts.append(
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" '
        f'rx="10" ry="10" fill="none" stroke="url(#{gradient_id})" strokeWidth="1.5"/>'
    )

    # Y-axis ticks (5 evenly spaced including 0 and y_max).
    for tick in range(5):
        value = round(y_max * tick / 4)
        y = y_for(value)
        parts.append(
            f'<line x1="{plot_left}" y1="{y:.1f}" x2="{plot_right}" y2="{y:.1f}" '
            'stroke="currentColor" strokeWidth="0.5" opacity="0.15"/>'
        )
        parts.append(
            f'<text x="{plot_left - 8}" y="{y + 4:.1f}" textAnchor="end" fontSize="10" '
            'fontFamily="system-ui, -apple-system, Segoe UI, sans-serif" '
            f'fill="currentColor" opacity="0.7">{value}</text>'
        )

    # X-axis labels.
    for i, m in enumerate(monthly_stats):
        x = x_for(i)
        parts.append(
            f'<text x="{x:.1f}" y="{plot_bottom + 18:.1f}" textAnchor="middle" '
            'fontSize="11" fontFamily="system-ui, -apple-system, Segoe UI, sans-serif" '
            f'fill="currentColor" opacity="0.7">{m.display_name}</text>'
        )

    series: list[tuple[str, str, list[int]]] = [
        ("PRs Merged", COLOR_PRS, [m.merged_prs for m in monthly_stats]),
        ("Issues Closed", COLOR_ISSUES, [m.closed_issues for m in monthly_stats]),
        ("Contributors", COLOR_CONTRIBS, [m.contributors for m in monthly_stats]),
    ]

    for label, color, values in series:
        points = " ".join(f"{x_for(i):.1f},{y_for(v):.1f}" for i, v in enumerate(values))
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            'strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"/>'
        )
        for i, v in enumerate(values):
            cx = x_for(i)
            cy = y_for(v)
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="{color}">'
                f'<title>{monthly_stats[i].display_name}: {v:,} {label.lower()}</title>'
                '</circle>'
            )

    # Legend.
    legend_y = height - 14
    legend_entries = [
        (COLOR_PRS, "PRs Merged"),
        (COLOR_ISSUES, "Issues Closed"),
        (COLOR_CONTRIBS, "Contributors"),
    ]
    legend_x = 200
    for color, label in legend_entries:
        parts.append(
            f'<circle cx="{legend_x}" cy="{legend_y}" r="4" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{legend_x + 10}" y="{legend_y + 4}" fontSize="11" '
            'fontFamily="system-ui, -apple-system, Segoe UI, sans-serif" '
            f'fill="currentColor" opacity="0.85">{label}</text>'
        )
        legend_x += 140

    parts.append("</svg>")
    return "".join(parts)


# MARK: - Releases table


def _format_release_date(published_at: str) -> str:
    """Render an ISO ``YYYY-MM-DD`` published-at into a short ``Mon DD, YYYY``.

    Returns the input unchanged if it doesn't match the expected ISO shape.
    """
    try:
        return datetime.strptime(published_at, "%Y-%m-%d").strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return published_at


def releases_table(rows: list[tuple[str, str, str, str]], gradient_id: str) -> str:
    """Render the latest-release-per-repo list as a styled SVG table.

    Each row is ``(repo_display_name, release_label, release_url, published_at)``.
    The SVG mirrors the repo stats card visuals: a gradient banner across the
    top with a white Noto Sans title, a header row beneath, then one data row
    per release. Release labels are wrapped in ``<a>`` so they remain
    clickable.
    """
    if not rows:
        return ""

    width = 720
    pad_x = 24
    pad_y = 12
    content_width = width - 2 * pad_x

    banner_h = 40
    header_h = 26
    row_h = 22

    # Column geometry (left-aligned cells, with the column boundary at the
    # listed x). 50 / 25 / 25 split feels balanced for the typical repo names
    # (longest is "Jellyfin for Android TV") and short version tags.
    repo_x = pad_x
    release_x = pad_x + content_width * 0.50
    date_x = pad_x + content_width * 0.78

    height = banner_h + header_h + len(rows) * row_h + pad_y

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Latest releases">'
    )
    parts.append(
        f'<defs><linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stopColor="{GRADIENT_START}"/>'
        f'<stop offset="100%" stopColor="{GRADIENT_END}"/>'
        '</linearGradient></defs>'
    )

    parts.append(
        f'<path d="{_banner_path(width, banner_h)}" fill="url(#{gradient_id})"/>'
    )
    parts.append(
        f'<text x="{width / 2:.1f}" y="{banner_h / 2 + 6:.1f}" textAnchor="middle" '
        f'fontSize="17" fontWeight="700" fontFamily="{TITLE_FONT_FAMILY}" '
        f'fill="#ffffff">Latest Releases</text>'
    )

    parts.append(
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" '
        f'rx="10" ry="10" fill="none" stroke="url(#{gradient_id})" strokeWidth="1.5"/>'
    )

    header_y = banner_h + 18
    for label, x in (("Repository", repo_x), ("Release", release_x), ("Date", date_x)):
        parts.append(
            f'<text x="{x:.1f}" y="{header_y:.1f}" textAnchor="start" '
            f'fontSize="11" fontWeight="600" fontFamily="{FONT_FAMILY}" '
            f'fill="currentColor" opacity="0.7">{_xml_escape(label)}</text>'
        )

    parts.append(
        f'<line x1="{pad_x}" y1="{banner_h + header_h:.1f}" '
        f'x2="{width - pad_x}" y2="{banner_h + header_h:.1f}" '
        'stroke="currentColor" strokeWidth="0.5" opacity="0.2"/>'
    )

    for i, (repo_name, release_label, release_url, published_at) in enumerate(rows):
        ry = banner_h + header_h + (i + 1) * row_h - 6
        parts.append(
            f'<text x="{repo_x:.1f}" y="{ry:.1f}" textAnchor="start" '
            f'fontSize="12" fontFamily="{FONT_FAMILY}" '
            f'fill="currentColor">{_xml_escape(repo_name)}</text>'
        )
        if release_url:
            parts.append(
                f'<a href="{_xml_escape(release_url)}">'
                f'<text x="{release_x:.1f}" y="{ry:.1f}" textAnchor="start" '
                f'fontSize="12" fontFamily="{FONT_FAMILY}" fontWeight="600" '
                f'fill="{COLOR_LINK}">{_xml_escape(release_label)}</text>'
                '</a>'
            )
        else:
            parts.append(
                f'<text x="{release_x:.1f}" y="{ry:.1f}" textAnchor="start" '
                f'fontSize="12" fontFamily="{FONT_FAMILY}" fontWeight="600" '
                f'fill="currentColor">{_xml_escape(release_label)}</text>'
            )
        parts.append(
            f'<text x="{date_x:.1f}" y="{ry:.1f}" textAnchor="start" '
            f'fontSize="12" fontFamily="{FONT_FAMILY}" '
            f'fill="currentColor" opacity="0.75">{_xml_escape(_format_release_date(published_at))}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)

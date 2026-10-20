"""Draw the twelve RSDGGS faces one per page, for building a large paper dodecahedron.

    python images/rsdggs_faces.py              # writes images/faces/rsdggs_face_00.svg ... _11.svg
    python images/rsdggs_faces.py --png DIR    # also writes PNG previews into DIR

Uses the drawing code of rsdggs_net_page1.py (Figure 1), so each face shows the same map,
triangles, cities, exceptions and north arrow, enlarged to fill a US Letter page with
0.5 in margins. North is up at the face centre.

Every edge of a face is the base of one of its five top-level triangles and is labelled
inside the face with that face and triangle, for example "F1·T3". Each of the thirty
edges has one glue tab, on one of its two faces; the tab names the edge it is glued
under on the other face. Cut out each face with its tabs, fold the tabs back, and glue
each tab beneath the edge whose label it names.
"""

import math
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Polygon as MplPolygon

import rsdggs_net_page1 as fig1
from rsdggs_net_page1 import INK, MARGIN, PAGE_H, PAGE_W, halo, unit

OUT = fig1.HERE / "faces"
TITLE_BAND = 16.0
LEGEND_BAND = 14.0
TAB_DEPTH = 12.0
TAB_ANGLE = math.radians(50)
K = 2.0                                  # text and symbol scale relative to Figure 1

NAMES = [
    "Antarctica / New Zealand", "Europe", "North America", "Asia", "South Atlantic",
    "Africa / Middle East", "South America", "Eastern Australia", "Southern Indian Ocean",
    "West Africa", "Central Pacific", "North Pacific",
]

# Cities that the small net has no room for.
EXTRA_CITIES = [
    ("Berlin", 52.52, 13.40, None),
    ("Rome", 41.90, 12.50, None),
    ("Casablanca", 33.57, -7.59, None),
    ("Sendai", 38.27, 140.87, None),
]


def edges(net):
    """For every face f and triangle t: the face g and triangle u across that edge."""
    out = {}
    for f in range(12):
        for t in range(5):
            a, b = net.v[f][t], net.v[f][(t + 1) % 5]
            for g in range(12):
                if g == f:
                    continue
                for u in range(5):
                    p, q = net.v[g][u], net.v[g][(u + 1) % 5]
                    if np.allclose(p, b) and np.allclose(q, a):
                        out[f, t] = (g, u)
    assert len(out) == 60
    return out


def tab_owners(across):
    """For each edge, the face that carries its glue tab, two or three tabs per face.

    Start from the lower face number, then move tabs from a face that has two more than a
    neighbour to that neighbour until no such pair is left. Deterministic.
    """
    owner = {frozenset((f, g)): min(f, g) for (f, _), (g, _) in across.items()}
    count = lambda f: sum(o == f for o in owner.values())      # noqa: E731
    moved = True
    while moved:
        moved = False
        for e in sorted(owner, key=sorted):
            f = owner[e]
            g = next(iter(e - {f}))
            if count(f) - count(g) >= 2:
                owner[e] = g
                moved = True
    assert all(2 <= count(f) <= 3 for f in range(12)), [count(f) for f in range(12)]
    return owner


def place(net, f, r=None):
    """Put face f alone on the page, north up at its centre.

    Without r, return the largest circumradius that fits with tabs; with r, use it.
    """
    lat = math.degrees(math.asin(net.c[f][2]))
    lon = math.degrees(math.atan2(net.c[f][1], net.c[f][0]))
    north = net.local(f, unit(lat + 0.5, lon))
    th = math.pi / 2 - math.atan2(north[1], north[0])
    corners = net.local(f, net.v[f]) @ fig1.Net.rot(th).T / net.radius
    lo, hi = corners.min(0), corners.max(0)
    box_w = PAGE_W - 2 * MARGIN - 2 * TAB_DEPTH
    box_h = PAGE_H - 2 * MARGIN - TITLE_BAND - LEGEND_BAND - 2 * TAB_DEPTH
    if r is None:
        return min(box_w / (hi - lo)[0], box_h / (hi - lo)[1])
    net.scale = r / net.radius
    centre = np.array([PAGE_W / 2, MARGIN + LEGEND_BAND + TAB_DEPTH + box_h / 2])
    net.place = {f: (th, centre - r * (lo + hi) / 2)}
    return r


def text_angle(a, b):
    ang = math.degrees(math.atan2(*(b - a)[::-1]))
    return ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang


def draw_edges(ax, net, f, across, owner):
    """Cut lines and glue tabs (drawn before the map)."""
    ctr = net.to_page(f, net.c[f])
    corners = net.to_page(f, net.v[f])
    for t in range(5):
        a, b = corners[t], corners[(t + 1) % 5]
        g, u = across[f, t]
        ax.plot(*np.column_stack([a, b]), color=INK, lw=1.2, zorder=5, solid_capstyle="round")
        if owner[frozenset((f, g))] == f:
            mid = (a + b) / 2
            inward = (ctr - mid) / np.linalg.norm(ctr - mid)
            ax.add_patch(MplPolygon(tab(a, b, ctr), closed=True, facecolor="#E0E0D0",
                                    edgecolor=INK, lw=0.8, zorder=1))
            ax.plot(*np.column_stack([a, b]), color="#333333", lw=0.8, ls=(0, (4, 3)),
                    zorder=5.5)
            ax.text(*(mid - TAB_DEPTH * 0.5 * inward), f"glue under F{g}·T{u}", fontsize=8.5,
                    color="#55553F", ha="center", va="center", rotation=text_angle(a, b),
                    zorder=2)


def label_edges(ax, net, f):
    """Each edge's own face·triangle label, inside the face at the middle of the edge."""
    ctr = net.to_page(f, net.c[f])
    corners = net.to_page(f, net.v[f])
    for t in range(5):
        a, b = corners[t], corners[(t + 1) % 5]
        mid = (a + b) / 2
        inward = (ctr - mid) / np.linalg.norm(ctr - mid)
        ax.text(*(mid + 4.5 * inward), f"F{f}·T{t}", fontsize=9, weight="bold", color=INK,
                ha="center", va="center", rotation=text_angle(a, b),
                path_effects=halo("white", 2.2), zorder=8)


def tab(a, b, ctr):
    u = (b - a) / np.linalg.norm(b - a)
    n = np.array([u[1], -u[0]])
    if n @ (a - ctr) < 0:
        n = -n
    inset = TAB_DEPTH / math.tan(TAB_ANGLE)
    return np.array([a, a + inset * u + TAB_DEPTH * n, b - inset * u + TAB_DEPTH * n, b])


def footer(ax, net, f, r):
    top = PAGE_H - MARGIN
    region = {0: "no ITU Region"}.get(f % 4, f"ITU Region {f % 4}")
    ax.text(PAGE_W / 2, top - 4, f"RSDGGS face {f} — {NAMES[f]}", fontsize=14, weight="bold",
            color=INK, ha="center", va="center")
    edge = 2 * r * math.sin(math.radians(36))
    ax.text(PAGE_W / 2, top - 10.5,
            f"{region} (face mod 4) · print at 100% on US Letter · edge {edge:.1f} mm · "
            "cut along the solid outline and around the tabs · glue each tab under the named "
            "edge", fontsize=6.5, style="italic", color="#555555", ha="center", va="center")
    fig1.legend(ax, MARGIN + 8)
    y = MARGIN + 2.5
    ax.text(MARGIN, y, "F·T = face and triangle of an edge   ·   ✕ = boundary exception   ·   "
            "N = true north", fontsize=6.5, color=INK, va="center")
    span = 40.0
    x1 = PAGE_W - MARGIN
    ax.plot([x1 - span, x1], [y, y], color=INK, lw=1.4, solid_capstyle="butt")
    for x in (x1 - span, x1):
        ax.plot([x, x], [y - 1, y + 1], color=INK, lw=0.8)
    deg = math.degrees(math.atan(span / net.scale))        # exact for a span from the centre
    ax.text(x1 - span - 2, y, f"{span:.0f} mm from the centre = {deg:.2f}°", fontsize=6.5,
            color=INK, ha="right", va="center")


def check(fig, ax, f):
    """Fail if any text or tab leaves the printable area."""
    px = fig.dpi / 25.4
    renderer = fig.canvas.get_renderer()
    lo, right, top = MARGIN * px, (PAGE_W - MARGIN) * px, (PAGE_H - MARGIN) * px
    for t in ax.texts:
        bb = t.get_window_extent(renderer)
        assert bb.x0 >= lo - 1 and bb.x1 <= right + 1 and bb.y0 >= lo - 1 and bb.y1 <= top + 1, \
            f"face {f}: text outside the margins: {t.get_text()!r}"
    for patch in ax.patches:
        if isinstance(patch, MplPolygon):
            xy = patch.get_xy()
            assert xy.min() >= MARGIN - 1e-6 and (xy[:, 0] <= PAGE_W - MARGIN).all() and \
                (xy[:, 1] <= PAGE_H - MARGIN).all(), f"face {f}: tab outside the margins"


def main():
    png = Path(sys.argv[sys.argv.index("--png") + 1]) if "--png" in sys.argv else None
    fig1.plt.rcParams["svg.hashsalt"] = "rsdggs"
    fig1.plt.rcParams["hatch.linewidth"] = 0.8
    features = fig1.countries()
    raster, step = fig1.class_raster(features)
    across = edges(fig1.Net())
    owner = tab_owners(across)
    tabs = [sum(o == f for o in owner.values()) for f in range(12)]
    OUT.mkdir(exist_ok=True)
    # One size for every face, so the pieces fit together: the largest that fits all pages.
    r = math.floor(min(place(fig1.Net(), f) for f in range(12)))
    for f in range(12):
        net = fig1.Net()
        place(net, f, r)
        fig, ax = fig1.new_page()
        draw_edges(ax, net, f, across, owner)
        label_edges(ax, net, f)
        fig1.draw_map(fig, ax, net, [f], features, raster, step, k=K,
                      cities=fig1.CITIES + EXTRA_CITIES, triangles_last=True)
        footer(ax, net, f, r)
        out = OUT / f"rsdggs_face_{f:02d}.svg"
        fig.savefig(out, facecolor="white", metadata={"Date": None})
        if png:
            fig.savefig(png / out.with_suffix(".png").name, dpi=110, facecolor="white")
        check(fig, ax, f)
        fig1.plt.close(fig)
        print(out, f"R = {r:.1f} mm, tabs {tabs[f]}")


if __name__ == "__main__":
    main()

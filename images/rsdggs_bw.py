"""Black-and-white versions of Figures 1 and 2 and of the twelve face pages, for RFCs.

    python images/rsdggs_bw.py              # writes images/bw/*.svg and images/bw/faces/*.svg
    python images/rsdggs_bw.py --png DIR    # also writes PNG previews into DIR (needs cairosvg)

It also copies the black-and-white net into the draft, between the two
"rsdggs_bw.py: begin/end rsdggs_net_page1_bw.svg" comments, as the figure's SVG artwork.

The SVG profile for RFCs (RFC 7996) allows black and white only, and no patterns,
gradients, clipping or images. So these files are written element by element rather than
by matplotlib: ISM bands are drawn as explicit hatch lines clipped to the land, and every
label has a white outline drawn under it instead of a coloured background.

Band hatching (the same in every file):
    /   433 MHz                    \\  868 MHz (only together with 433 MHz)
    --  902-928 MHz                dots: 2.4 GHz only
    unmarked land: no standard allocation (Antarctica); unmarked water: ocean

The geometry, the glue tabs and the label positions come from the colour figures
(rsdggs_net_page1.py, rsdggs_faces.py), so the two sets match. To stay readable without
colour, countries with the same bands are merged (only band boundaries and coasts are
drawn), small islands are dropped, and the net carries no city names.
"""

import math
import sys
import textwrap
from pathlib import Path

import numpy as np
import shapely
from matplotlib.text import Annotation
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

import rsdggs_faces as faces
import rsdggs_net_page1 as fig1
import rsdggs_net_page2 as fig2
from rsdggs_net_page1 import MARGIN, PAGE_H, PAGE_W

OUT = fig1.HERE / "bw"
DRAFT = fig1.HERE.parent / "draft" / "draft-hanley-rsdggs-01.xml"
PT = 25.4 / 72                    # millimetres per point

# Hatching per band class (rsdggs_net_page1.band_class): (angle in degrees, ...); "dots".
HATCH = {1: (45,), 2: (45, -45), 3: (0,), 4: "dots", 5: ()}
LEGEND = [(1, "433 MHz"), (2, "433 + 868 MHz"), (3, "902–928 MHz"), (4, "2.4 GHz only"),
          (5, "No allocation (Antarctica)")]


def num(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    """An SVG document in the RFC 7996 profile. Coordinates are in millimetres with y up
    (as in the matplotlib figures) unless `flip` is False."""

    def __init__(self, w, h, title, flip=True, unit="mm"):
        self.w, self.h, self.title, self.flip, self.unit = w, h, title, flip, unit
        self.out = []

    def y(self, y):
        return self.h - y if self.flip else y

    def pts(self, xy):
        return " ".join(f"{num(x)} {num(self.y(y))}" for x, y in xy)

    def path(self, d, width, stroke="black", fill="none", dash=None, cap=None, join=None):
        if not d:
            return
        a = f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{num(width)}"'
        if dash:
            a += f' stroke-dasharray="{" ".join(num(v) for v in dash)}"'
        if cap:
            a += f' stroke-linecap="{cap}"'
        if join:
            a += f' stroke-linejoin="{join}"'
        self.out.append(a + "/>")

    def line(self, pts, width, closed=False, **kw):
        self.path("M" + self.pts(pts) + ("Z" if closed else ""), width, **kw)

    def segments(self, segs, width, **kw):
        self.path("".join(f"M{self.pts(s)}" for s in segs), width, **kw)

    def fill(self, pts, stroke="black", width=0.1, fill="black"):
        self.path("M" + self.pts(pts) + "Z", width, stroke=stroke, fill=fill, join="round")

    def rings(self, geom, width, **kw):
        d = "".join("M" + self.pts(np.asarray(r.coords)[:-1]) + "Z"
                    for p in fig1.flat_polygons(geom) for r in [p.exterior, *p.interiors])
        self.path(d, width, join="round", **kw)

    def circle(self, x, y, r, width, fill="white"):
        self.out.append(f'<circle cx="{num(x)}" cy="{num(self.y(y))}" r="{num(r)}" '
                        f'fill="{fill}" stroke="black" stroke-width="{num(width)}"/>')

    def rect(self, x, y, w, h, width, fill="none"):
        y0 = self.y(y + h) if self.flip else y
        self.out.append(f'<rect x="{num(x)}" y="{num(y0)}" width="{num(w)}" height="{num(h)}" '
                        f'fill="{fill}" stroke="black" stroke-width="{num(width)}"/>')

    def text(self, x, y, s, size, anchor="start", bold=False, italic=False, angle=0.0,
             halo=0.0, dy=0.0):
        """Text with its baseline at (x, y), or `dy` below it in the text's own frame.
        `size` is in drawing units; `halo` is the width of a white outline drawn under it."""
        a = f'font-size="{num(size)}"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if bold:
            a += ' font-weight="bold"'
        if italic:
            a += ' font-style="italic"'
        if angle:
            pos = (f'x="0" y="{num(dy)}" transform="translate({num(x)} {num(self.y(y))}) '
                   f'rotate({num(-angle if self.flip else angle)})"')
        else:
            pos = f'x="{num(x)}" y="{num(self.y(y) + dy)}"'
        if halo:
            self.out.append(f'<text {pos} {a} fill="white" stroke="white" '
                            f'stroke-width="{num(halo)}" stroke-linejoin="round">{esc(s)}</text>')
        self.out.append(f'<text {pos} {a} fill="black">{esc(s)}</text>')

    def save(self, path):
        size = (f'width="{num(self.w)}{self.unit}" height="{num(self.h)}{self.unit}" '
                if self.unit else "")
        body = "\n".join(self.out)
        path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny" '
            f'{size}viewBox="0 0 {num(self.w)} {num(self.h)}" font-family="sans-serif">\n'
            f"<title>{esc(self.title)}</title>\n"
            f'<rect x="0" y="0" width="{num(self.w)}" height="{num(self.h)}" fill="white"/>\n'
            f"{body}\n</svg>\n")


# Map -------------------------------------------------------------------------------------

def hatch_lines(geom, angle, spacing):
    """Parallel lines at `angle` degrees, `spacing` apart, clipped to geom."""
    th = math.radians(angle)
    d, n = np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])
    x0, y0, x1, y1 = geom.bounds
    corners = np.array([[x0, y0], [x0, y1], [x1, y0], [x1, y1]])
    lo, hi = (corners @ n).min(), (corners @ n).max()
    a0, a1 = (corners @ d).min() - 1, (corners @ d).max() + 1
    lines = [LineString([n * s + d * a0, n * s + d * a1])
             for s in np.arange(math.ceil(lo / spacing), math.floor(hi / spacing) + 1) * spacing]
    out = []
    for g in shapely.intersection(lines, geom):
        for part in getattr(g, "geoms", [g]):
            if part.geom_type == "LineString" and part.length > 0.05:
                out.append(np.asarray(part.coords))
    return out


def dots(geom, spacing):
    """A staggered grid of points inside geom."""
    x0, y0, x1, y1 = geom.bounds
    pts = [(x, y) for j, y in enumerate(np.arange(math.floor(y0 / spacing), y1 / spacing + 1)
                                       * spacing)
           for x in np.arange(math.floor(x0 / spacing) - 0.5 * (j % 2), x1 / spacing + 1)
           * spacing]
    if not pts:
        return []
    pts = np.array(pts)
    return pts[shapely.contains_xy(geom, pts[:, 0], pts[:, 1])]


def draw_land(svg, net, face_ids, features, s):
    """Band classes on each face, merged, simplified and hatched. `s` scales the drawing."""
    for f in face_ids:
        by_class = {}
        for cls, parts in fig1.face_countries(net, f, features):
            by_class.setdefault(cls, []).extend(parts)
        for cls in sorted(by_class):
            geom = unary_union(by_class[cls]).simplify(0.05 * s)
            geom = unary_union([p for p in fig1.flat_polygons(geom) if p.area > 0.12 * s * s])
            if geom.is_empty:
                continue
            style = HATCH[cls]
            if style == "dots":
                pts = dots(geom, 1.0 * s)
                svg.path("".join(f"M{svg.pts([p])}h0.01" for p in pts), 0.3 * s, cap="round")
            else:
                for angle in style:
                    svg.segments(hatch_lines(geom, angle, 0.9 * s), 0.13 * s)
            svg.rings(geom, 0.16 * s)


def triangles(svg, net, face_ids, k):
    """Dashed lines from each face centre to its corners (the five top-level triangles)."""
    for f in face_ids:
        ctr = net.to_page(f, net.c[f])
        corners = net.to_page(f, net.v[f])
        segs = []
        for t in range(5):
            d = corners[t] - ctr
            segs.append([ctr + d / np.linalg.norm(d) * 3.2 * k, corners[t]])
        svg.segments(segs, 0.15 * k, dash=(0.9 * k, 0.7 * k))


# Labels ----------------------------------------------------------------------------------

def layout(fig, ax, net, face_ids, raster, step, k, cities, triangles_last):
    """Place the labels with the colour figures' Labeller, and return what it placed.

    The colour map itself is not drawn; only the labels, markers and arrows matter here.
    """
    saved = fig1.draw_land, fig1.draw_borders, fig1.EXCEPTIONS
    fig1.draw_land = fig1.draw_borders = lambda *a, **kw: None
    # The generic sans-serif fonts that RFC SVG allows may have no arrow glyph.
    fig1.EXCEPTIONS = [(label.replace("→", "->"), lat, lon) for label, lat, lon in saved[2]]
    try:
        fig1.draw_map(fig, ax, net, face_ids, [], raster, step, k=k, cities=cities,
                      triangles_last=triangles_last)
    finally:
        fig1.draw_land, fig1.draw_borders, fig1.EXCEPTIONS = saved
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    texts, arrows = [], []
    for t in ax.texts:
        if t.get_rotation() != 0:
            continue
        s = t.get_text()
        if isinstance(t, Annotation) and not s:
            arrows.append((np.asarray(t.xyann), np.asarray(t.xy)))
            continue
        bb = t.get_window_extent(renderer)
        (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
        descent = renderer.get_text_width_height_descent(s, t.get_fontproperties(), False)[2]
        x = {"left": x0, "center": (x0 + x1) / 2, "right": x1}[t.get_ha()]
        texts.append(dict(s=s, x=x, y=y0 + descent / fig.dpi * 25.4, size=t.get_fontsize(),
                          anchor={"left": "start", "center": "middle", "right": "end"}[t.get_ha()],
                          bold=t.get_fontweight() == "bold", italic=t.get_fontstyle() == "italic"))
    marks = {"o": [], "x": []}
    for line in ax.lines:
        if line.get_marker() in marks:
            marks[line.get_marker()].append(line.get_xydata()[0])
    return texts, arrows, marks


def draw_labels(svg, net, face_ids, texts, arrows, marks, k):
    for f in face_ids:
        if f in (6, 9):
            ctr = net.to_page(f, net.c[f])
            bar = [ctr + [-1.1 * k, -2.2 * k], ctr + [1.1 * k, -2.2 * k]]
            svg.line(bar, 1.1 * k * PT + 0.9 * k, stroke="white")
            svg.line(bar, 1.1 * k * PT)
    for x, y in marks["o"]:
        svg.circle(x, y, 0.6 * k, 0.18 * k)
    for x, y in marks["x"]:
        r = 0.9 * k
        for stroke, w in (("white", 1.0 * k), ("black", 0.4 * k)):
            svg.segments([[(x - r, y - r), (x + r, y + r)], [(x - r, y + r), (x + r, y - r)]],
                         w, stroke=stroke, cap="round")
    for base, tip in arrows:
        d = (tip - base) / np.linalg.norm(tip - base)
        nrm = np.array([-d[1], d[0]])
        head = [tip, tip - 1.6 * k * d + 0.7 * k * nrm, tip - 1.6 * k * d - 0.7 * k * nrm]
        svg.line([base, tip - 1.2 * k * d], 1.0 * k, stroke="white", cap="round")
        svg.fill(head, stroke="white", width=0.8 * k, fill="white")
        svg.line([base, tip - 1.2 * k * d], 0.3 * k, cap="round")
        svg.fill(head)
    for t in texts:
        size = t["size"] * PT
        if t["s"].isdigit():
            size *= 1.15
        svg.text(t["x"], t["y"], t["s"], size, t["anchor"], t["bold"] or t["s"].isdigit(),
                 t["italic"], halo=size * 0.35)


# Legends ---------------------------------------------------------------------------------

def swatch(svg, x, y, w, h, cls, s=1.0):
    """A legend box showing a band class's hatching; (x, y) is its lower left corner."""
    box = Polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    style = HATCH[cls]
    if style == "dots":
        svg.path("".join(f"M{svg.pts([p])}h0.01" for p in dots(box.buffer(-0.4), s)),
                 0.3 * s, cap="round")
    else:
        for angle in style:
            svg.segments(hatch_lines(box, angle if svg.flip else -angle, 0.9 * s), 0.13 * s)
    svg.rect(x, y, w, h, 0.2 * min(s, 2))


def band_legend(svg, x, y, s=1.0, size=6.5):
    """One row of band swatches with its baseline at y, hatched as the map at scale s."""
    for cls, label in LEGEND:
        swatch(svg, x, y - 1.3, 6, 3.4, cls, s)
        svg.text(x + 7.5, y - 0.6, label, size * PT)
        x += 13 + 1.25 * len(label)


def line_legend(svg, x, y, size=6.5):
    """Cut, fold, glue tab and exception marker, one row at height y."""
    t = size * PT
    svg.line([(x, y), (x + 8, y)], 0.28, dash=(1.4, 1.05))
    svg.text(x + 10, y - 0.8, "Fold line", t)
    svg.line([(x + 26, y), (x + 34, y)], 0.35)
    svg.text(x + 36, y - 0.8, "Cut line", t)
    svg.rect(x + 51, y - 1.4, 7, 2.8, 0.18)
    svg.text(x + 60, y - 0.8, "Glue tab (left unprinted)", t)
    r = 0.9
    cx = x + 98
    svg.segments([[(cx - r, y - r), (cx + r, y + r)], [(cx - r, y + r), (cx + r, y - r)]],
                 0.4, cap="round")
    svg.text(cx + 2.5, y - 0.8, "Boundary exception", t)
    svg.text(cx + 32, y - 0.8, "T0–T4 = triangle index", t, italic=True)


# Figure 1 --------------------------------------------------------------------------------

def tab_text(svg, a, b, mid, s, size):
    ang = math.degrees(math.atan2(*(b - a)[::-1]))
    ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
    svg.text(mid[0], mid[1], s, size, "middle", angle=ang, dy=0.35 * size)


def net_page(features, raster, step):
    net = fig1.Net()
    tabs, cuts, folds = fig1.layout(net)
    fig, ax = fig1.new_page()
    texts, arrows, marks = layout(fig, ax, net, range(12), raster, step, 1.0, [], False)
    fig1.plt.close(fig)

    svg = Svg(PAGE_W, PAGE_H, "RSDGGS dodecahedron net: ISM band coverage (black and white)")
    for poly, a, b in tabs:
        svg.line(poly, 0.18)
        tab_text(svg, a, b, (poly[1] + poly[2]) / 2 * 0.55 + (a + b) / 2 * 0.45, "GLUE",
                 4.5 * PT)
    draw_land(svg, net, range(12), features, 1.0)
    triangles(svg, net, range(12), 1.0)
    edge = lambda f, i: [net.outline(f)[0][i], net.outline(f)[0][(i + 1) % 5]]  # noqa: E731
    svg.segments([edge(f, i) for f, i in folds], 0.28, dash=(1.4, 1.05))
    svg.segments([edge(f, i) for f, i in cuts], 0.35, cap="round")
    draw_labels(svg, net, range(12), texts, arrows, marks, 1.0)

    x1, y = PAGE_W - MARGIN, MARGIN + fig1.LEGEND_BAND - 3
    svg.segments([[(x1 - fig1.R_MM, y), (x1, y)]], 0.5)
    svg.segments([[(x, y - 1), (x, y + 1)] for x in (x1 - fig1.R_MM, x1)], 0.28)
    svg.text(x1 - fig1.R_MM / 2, y + 1.8, f"25 mm = {net.arc_deg:.2f}°", 6.5 * PT, "middle")
    top = PAGE_H - MARGIN
    svg.text(PAGE_W / 2, top - 5.5, "RSDGGS Dodecahedron Net — ISM Band Regulatory Coverage",
             12 * PT, "middle", bold=True)
    svg.text(PAGE_W / 2, top - 11, "Gnomonic projection · Geography continuous across all fold "
             "edges · Numbers = RSDGGS face index · Black-and-white edition", 7 * PT, "middle",
             italic=True)
    band_legend(svg, MARGIN, MARGIN + 9)
    line_legend(svg, MARGIN, MARGIN + 3)
    return svg


# Face pages ------------------------------------------------------------------------------

def face_page(f, r, across, owner, features, raster, step):
    k = faces.K
    net = fig1.Net()
    faces.place(net, f, r)
    fig, ax = fig1.new_page()
    faces.draw_edges(ax, net, f, across, owner)
    faces.label_edges(ax, net, f)
    texts, arrows, marks = layout(fig, ax, net, [f], raster, step, k,
                                  fig1.CITIES + faces.EXTRA_CITIES, True)
    fig1.plt.close(fig)

    svg = Svg(PAGE_W, PAGE_H, f"RSDGGS face {f}: {faces.NAMES[f]} (black and white)")
    ctr = net.to_page(f, net.c[f])
    corners = net.to_page(f, net.v[f])
    draw_land(svg, net, [f], features, 2.0)
    triangles(svg, net, [f], k)
    cut, fold = [], []
    for t in range(5):
        a, b = corners[t], corners[(t + 1) % 5]
        g, u = across[f, t]
        mid = (a + b) / 2
        inward = (ctr - mid) / np.linalg.norm(ctr - mid)
        if owner[frozenset((f, g))] == f:
            fold.append([a, b])
            svg.line(faces.tab(a, b, ctr), 0.28)
            tab_text(svg, a, b, mid - faces.TAB_DEPTH * 0.5 * inward, f"glue under F{g}·T{u}",
                     8.5 * PT)
        else:
            cut.append([a, b])
    svg.segments(fold, 0.28, dash=(1.4, 1.05))
    svg.segments(cut, 0.42, cap="round")
    draw_labels(svg, net, [f], texts, arrows, marks, k)
    for t in range(5):
        a, b = corners[t], corners[(t + 1) % 5]
        mid = (a + b) / 2
        inward = (ctr - mid) / np.linalg.norm(ctr - mid)
        ang = math.degrees(math.atan2(*(b - a)[::-1]))
        ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
        p = mid + 4.5 * inward
        svg.text(p[0], p[1], f"F{f}·T{t}", 9 * PT, "middle", bold=True, angle=ang,
                 halo=1.2, dy=0.35 * 9 * PT)

    top = PAGE_H - MARGIN
    region = {0: "no ITU Region"}.get(f % 4, f"ITU Region {f % 4}")
    svg.text(PAGE_W / 2, top - 5.5, f"RSDGGS face {f} — {faces.NAMES[f]}", 14 * PT, "middle",
             bold=True)
    edge = 2 * r * math.sin(math.radians(36))
    svg.text(PAGE_W / 2, top - 11.5,
             f"{region} (face mod 4) · print at 100% on US Letter · edge {edge:.1f} mm · cut "
             "along the solid outline and around the tabs · glue each tab under the named edge",
             6.5 * PT, "middle", italic=True)
    band_legend(svg, MARGIN, MARGIN + 9, 2.0)
    y = MARGIN + 2.5
    svg.text(MARGIN, y - 0.8, "F·T = face and triangle of an edge   ·   × = boundary exception"
             "   ·   N = true north", 6.5 * PT)
    span, x1 = 40.0, PAGE_W - MARGIN
    svg.segments([[(x1 - span, y), (x1, y)]], 0.5)
    svg.segments([[(x, y - 1), (x, y + 1)] for x in (x1 - span, x1)], 0.28)
    deg = math.degrees(math.atan(span / net.scale))
    svg.text(x1 - span - 2, y - 0.8, f"{span:.0f} mm from the centre = {deg:.2f}°", 6.5 * PT,
             "end")
    return svg


# Figure 2 --------------------------------------------------------------------------------

BANDS = [
    # class for the swatch, title, line, detail
    (1, "A  433.050–434.790 MHz", "ITU Region 1 only", fig2.BANDS[0][6]),
    (None, "B  863–870 MHz (ETSI SRD)", "EU / CEPT / EEA region", fig2.BANDS[1][6]),
    (3, "C  902–928 MHz", "Region 2 + selected Region 3", fig2.BANDS[2][6]),
    (5, "D  2400–2500 MHz", "Global — all countries: no hatching", fig2.BANDS[3][6]),
    (4, "Dots: 2.4 GHz only (no sub-GHz ISM)", "Most of Asia/Pacific region",
     "No 433/868/915 MHz allocation"),
    (2, "Crossed hatching: 433 + 868 MHz", "Each band adds its own hatching",
     "/ = 433 MHz   \\ = 868 MHz   — = 902–928 MHz"),
]
QUICK_CLASS = [1, None, 3, 3, 5]


class Key(Svg):
    """Figure 2's 2000 x 1555 grid, y down; sizes in points as in rsdggs_net_page2.py."""

    def __init__(self):
        super().__init__(fig2.W, fig2.H, "RSDGGS dodecahedron net: reference key (black and "
                         "white)", flip=False, unit=None)

    def t(self, x, y, s, size=9.5, va="top", **kw):
        u = size / 0.72                       # one grid unit is 0.72 pt
        lines = s.split("\n")
        step = 1.32 * u
        y0 = {"top": y + 0.8 * u, "center": y + 0.35 * u - (len(lines) - 1) * step / 2,
              "baseline": y}[va]
        for i, line in enumerate(lines):
            self.text(x, y0 + i * step, line, u, **kw)

    def rule(self, x0, x1, y):
        self.line([(x0, y), (x1, y)], 0.8)

    def heading(self, x0, x1, y, s):
        self.t(x0, y, s, 13, va="baseline", bold=True)
        self.rule(x0, x1, y + 22)

    def swatch(self, x, y, w, h, cls):
        if cls is None:                       # 868 MHz alone: back-slash hatching
            box = Polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
            self.segments(hatch_lines(box, 45, 12), 1.6)       # y is down here
            self.rect(x, y, w, h, 1.6)
        else:
            swatch(self, x, y, w, h, cls, s=12)


def key_page():
    k = Key()
    W = fig2.W
    k.t(W / 2, 65, "RSDGGS Dodecahedron Net — Reference Key", 20, "center", anchor="middle",
        bold=True)
    k.t(W / 2, 115, "Regulatory Spectrum Discrete Global Grid System · ISM Band Coverage · ITU "
        "Radio Region Face Assignment · Black-and-white edition", 11, "center", anchor="middle",
        italic=True)
    k.rule(50, 1950, 135)

    x0, x1 = 50, 680
    k.heading(x0, x1, 195, "ISM Band Regulatory Coverage")
    for i, (cls, title, line, detail) in enumerate(BANDS):
        y = 240 + 102 * i
        k.swatch(x0 - 5, y, 120, 76, cls)
        k.t(x0 + 130, y + 2, title, 11, bold=True)
        k.t(x0 + 130, y + 26, line, 9.5)
        k.t(x0 + 130, y + 46, detail, 8.5, italic=True)
    k.heading(x0, x1, 905, "Construction Edge Guide")
    items = [("Dashed line = Fold edge", "Score firmly with a stylus or dull knife, then fold"),
             ("Solid outer edge = Cut line", "Cut cleanly with scissors or craft knife"),
             ("Outlined tab = Glue surface", "Apply PVA or stick glue; press to adjacent face")]
    for i, (title, line) in enumerate(items):
        y = 960 + 76 * i
        if i == 0:
            k.line([(x0 + 10, y + 12), (x0 + 110, y + 12)], 3.5, dash=(12, 8))
        elif i == 1:
            k.line([(x0 + 8, y + 12), (x0 + 110, y + 12)], 4.2)
        else:
            k.rect(x0 + 5, y - 6, 110, 40, 1.1)
            k.t(x0 + 60, y + 14, "GLUE", 7, "center", anchor="middle")
        k.t(x0 + 130, y - 2, title, 11, bold=True)
        k.t(x0 + 130, y + 20, line, 9.5)
    k.heading(x0, x1, 1230, "Cartographic Projection")
    k.t(x0, 1268, textwrap.fill(fig2.CARTOGRAPHY, 70), 9.5)

    x0, x1 = 750, 1310
    k.heading(x0, x1, 195, "RSDGGS Face Reference")
    cols = (x0, x0 + 60, x0 + 365)
    for x, s in zip(cols, ("F#", "Name / Regulatory Bodies", "ISM Bands Available")):
        k.t(x, 252, s, 9.5, bold=True)
    k.rule(x0, x1, 274)
    for i, (name, bodies, bands) in enumerate(fig2.FACES):
        y = 278 + 70 * i
        k.rule(x0, x1, y + 69)
        k.circle(x0 + 23, y + 22, 15, 1.6)
        k.t(x0 + 23, y + 22, str(i), 11 if i < 10 else 9.5, "center", anchor="middle",
            bold=True)
        k.t(cols[1], y + 8, name, 10.5, bold=True)
        k.t(cols[1], y + 32, bodies, 8, italic=True)
        k.t(cols[2], y + 9, textwrap.fill(bands, 30), 8.5)

    x0, x1 = 1350, 1950
    k.heading(x0, x1, 195, "Construction Instructions")
    for i, (title, body) in enumerate(fig2.STEPS):
        y = 232 + 64 * i
        k.circle(x0 + 14, y + 12, 13, 1.4)
        k.t(x0 + 14, y + 12, str(i + 1), 10, "center", anchor="middle", bold=True)
        k.t(x0 + 55, y, title, 11, bold=True)
        k.t(x0 + 55, y + 21, textwrap.fill(body, 92), 8.5)
    k.rule(x0, x1, 685)
    k.heading(x0, x1, 735, "ISM Band Quick Reference")
    cx = (x0 + 5, x0 + 80, x0 + 205, x0 + 335, x0 + 445)
    k.rect(x0 - 10, 772, 565, 40, 1.6)
    for x, s in zip(cx, ("Band", "Frequency", "Max EIRP", "Duty cycle", "LBT req.")):
        k.t(x, 792, s, 9, "center", bold=True)
    for i, ((_, freq, eirp, duty, lbt), cls) in enumerate(zip(fig2.QUICK, QUICK_CLASS)):
        y = 814 + 50 * i
        k.rect(x0 - 10, y, 565, 48, 0.8)
        k.swatch(x0, y + 6, 70, 36, cls)
        for x, s in zip(cx[1:], (freq, eirp, duty, lbt)):
            k.t(x, y + 24, s, 8.5, "center")
    k.heading(x0, x1, 1110, "About RSDGGS")
    k.t(x0, 1148, textwrap.fill(fig2.ABOUT, 72), 9.5)
    k.t(x0, 1290, "draft-hanley-rsdggs-00 · Independent Submission\n"
                  "IEEE 802.15.4 MAC layer · CBOR encoded · Rust reference impl", 9.5)
    k.rule(50, 1950, 1500)
    k.t(W / 2, 1520, fig2.FOOTER, 8, "center", anchor="middle")
    return k


def embed(svg_file):
    """Put svg_file into the draft between its begin and end comments."""
    name = svg_file.name
    begin, end = f"<!-- rsdggs_bw.py: begin {name} -->\n", f"<!-- rsdggs_bw.py: end {name} -->"
    xml = DRAFT.read_text(encoding="utf-8")
    i, j = xml.index(begin) + len(begin), xml.index(end)
    svg = svg_file.read_text(encoding="utf-8").split("\n", 1)[1]     # drop the XML declaration
    DRAFT.write_text(xml[:i] + '<artwork type="svg">' + svg.rstrip("\n") + "</artwork>\n"
                     + xml[j:], encoding="utf-8")
    print(DRAFT, f"<- {name}")


def main():
    png = Path(sys.argv[sys.argv.index("--png") + 1]) if "--png" in sys.argv else None
    features = fig1.countries()
    raster, step = fig1.class_raster(features)
    (OUT / "faces").mkdir(parents=True, exist_ok=True)
    jobs = [(OUT / "rsdggs_net_page1_bw.svg", lambda: net_page(features, raster, step)),
            (OUT / "rsdggs_net_page2_bw.svg", key_page)]
    across = faces.edges(fig1.Net())
    owner = faces.tab_owners(across)
    r = math.floor(min(faces.place(fig1.Net(), f) for f in range(12)))
    for f in range(12):
        jobs.append((OUT / "faces" / f"rsdggs_face_{f:02d}_bw.svg",
                     lambda f=f: face_page(f, r, across, owner, features, raster, step)))
    for out, make in jobs:
        make().save(out)
        print(out, f"{out.stat().st_size // 1024} KiB")
        if png:
            import cairosvg
            cairosvg.svg2png(url=str(out), write_to=str(png / out.with_suffix(".png").name),
                             output_width=1400)
    embed(OUT / "rsdggs_net_page1_bw.svg")


if __name__ == "__main__":
    main()

"""Draw Figure 1 of draft-hanley-rsdggs-00: the dodecahedron net, ISM band coverage.

    python images/rsdggs_net_page1.py    # writes images/rsdggs_net_page1.png

Requires matplotlib (built with 3.10.8), numpy and shapely. The face geometry is read
from src/constants.rs, so the figure always matches the reference implementation.
Country outlines come from Natural Earth 5.1.2 (1:50m admin 0, public domain), which is
downloaded once into images/.cache and checked against a pinned SHA-256.

Output: US Letter portrait at 300 dpi with 0.5 in margins. Each pentagon has a
circumradius of 25 mm when printed at 100%. Every face is a gnomonic projection centered
on that face, so great-circle fold edges are straight and coastlines continue across them.
"""

import hashlib
import json
import math
import re
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path as MplPath
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Rectangle
from shapely.geometry import LineString, Polygon

HERE = Path(__file__).resolve().parent
CONSTANTS = HERE.parent / "src" / "constants.rs"
NE_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/"
          "geojson/ne_50m_admin_0_countries.geojson")
NE_SHA256 = "3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb"

# Page, in millimetres with the origin at the bottom left.
PAGE_W, PAGE_H = 215.9, 279.4
MARGIN = 12.7
DPI = 300
R_MM = 25.0                       # pentagon circumradius at 100% print size
TITLE_BAND = 16.0                 # reserved below the top margin
LEGEND_BAND = 16.0                # reserved above the bottom margin
TAB_DEPTH = 5.0
TAB_ANGLE = math.radians(30)      # tab sides stay inside the 36 degree notches of the net

# The net: F0 with its five neighbours, F1 with its five, joined across the F8-F2 edge.
NET_TREE = {0: [7, 8, 9, 10, 11], 8: [2], 2: [1], 1: [3, 4, 5, 6]}

INK = "#1A1A2E"
OCEAN = "#A9D6E5"
BORDER = "#3A3A3A"
CLASS_COLORS = {
    1: "#CC2222",   # 433 MHz
    2: "#CC2222",   # 433 + 868 MHz: red with teal hatch
    3: "#D4780A",   # 902-928 MHz
    4: "#B0C8DC",   # 2.4 GHz only
    5: "#E4E8EC",   # Antarctica: no standard allocation
}
HATCH = "#1A7A5E"

# Band classes follow draft section 4.6.1 and the Figure 2 legend.
ETSI = set(
    "AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE "
    "IS LI NO CH GB UA AL BA ME MK RS XK MD AD MC SM VA FO GG JE IM GI AX "
    "NC PF WF".split()
)
BAND_C_EXTRA = {"AU", "NZ", "TW", "JP", "GU", "MP", "AS", "UM"}
R1_ASIA = {"Western Asia", "Central Asia", "Southern Asia"}

CITIES = [
    # name, lat, lon, label offset in points (face 2 is drawn with north to the upper left)
    ("Seattle", 47.61, -122.33, (3, -5)),
    ("Vancouver", 49.28, -123.12, (-3, 4)),
    ("Los Angeles", 34.05, -118.24, (4, -1)),
    ("Denver", 39.74, -104.99, (0, 5)),
    ("Dallas", 32.78, -96.80, (4, 0)),
    ("Minneapolis", 44.98, -93.27, (-4, -2)),
    ("Chicago", 41.88, -87.63, (-4, 3)),
    ("Toronto", 43.65, -79.38, (-4, 0)),
    ("New York", 40.71, -74.01, (4, 1)),
    ("Miami", 25.76, -80.19, (4, 0)),
    ("Havana", 23.11, -82.37, (4, -3)),
    ("Mexico City", 19.43, -99.13, (4, 0)),
]
EXCEPTIONS = [
    ("AK→F6", 61.2, -149.9),
    ("HI→F9", 21.3, -157.8),
    ("PR→F4", 18.5, -66.1),
]


# Geometry -------------------------------------------------------------------------------

def read_constants():
    src = re.sub(r"//[^\n]*", "", CONSTANTS.read_text())

    def array(name, count):
        body = src[src.index(f"pub const {name}"):]
        body = body[body.index("= [") + 2:]
        nums = re.findall(r"-?\d+\.\d+(?:e-?\d+)?", body)[:count]
        return np.array([float(x) for x in nums])

    centers = array("FACE_CENTERS", 36).reshape(12, 3)
    verts = array("FACE_PENTAGON_VERTS", 180).reshape(12, 5, 3)
    return centers, verts


def unit(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


class Net:
    def __init__(self):
        self.c, self.v = read_constants()
        self.basis = []
        for f in range(12):
            c = self.c[f]
            t = self.v[f, 0] - self.v[f, 0].dot(c) * c
            e1 = t / np.linalg.norm(t)
            self.basis.append((c, e1, np.cross(c, e1)))
        self.radius = np.linalg.norm(self.local(0, self.v[0]), axis=1)[0]
        self.arc_deg = math.degrees(math.atan(self.radius))
        self.scale = R_MM / self.radius
        self.place = {0: (0.0, np.zeros(2))}
        order = [0]
        for f in order:
            for g in NET_TREE.get(f, []):
                a, b = self.shared(f, g)
                pa, pb = self.to_page(f, a), self.to_page(f, b)
                la, lb = self.local(g, a), self.local(g, b)
                th = math.atan2(*(pb - pa)[::-1]) - math.atan2(*(lb - la)[::-1])
                self.place[g] = (th, pa - self.scale * self.rot(th) @ la)
                order.append(g)
        self.folds = {frozenset((f, g)) for f, gs in NET_TREE.items() for g in gs}

    @staticmethod
    def rot(th):
        return np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])

    def local(self, f, p):
        c, e1, e2 = self.basis[f]
        q = p / (p @ c)[..., None] if p.ndim > 1 else p / (p @ c)
        return np.stack([q @ e1, q @ e2], -1)

    def to_page(self, f, p):
        th, t = self.place[f]
        return self.scale * self.local(f, p) @ self.rot(th).T + t

    def from_page(self, f, xy):
        th, t = self.place[f]
        loc = (xy - t) @ self.rot(th) / self.scale
        c, e1, e2 = self.basis[f]
        p = c + loc[..., :1] * e1 + loc[..., 1:] * e2
        return p / np.linalg.norm(p, axis=-1, keepdims=True)

    def shared(self, f, g):
        out = [vf for vf in self.v[f] if np.min(np.linalg.norm(self.v[g] - vf, axis=1)) < 1e-9]
        assert len(out) == 2, (f, g)
        return out

    def neighbour(self, f, a, b):
        for g in range(12):
            if g != f and all(np.min(np.linalg.norm(self.v[g] - x, axis=1)) < 1e-9 for x in (a, b)):
                return g
        raise ValueError(f)

    def outline(self, f):
        """Pentagon vertices on the page, counter-clockwise, with their 3D points."""
        # Sort in the face's own frame so edge indices survive moving the net.
        loc = self.local(f, self.v[f])
        order = np.argsort(np.arctan2(loc[:, 1], loc[:, 0]))
        return self.to_page(f, self.v[f])[order], self.v[f][order]

    def face_of(self, lat, lon):
        return int(np.argmax(self.c @ unit(lat, lon)))

    def transform(self, angle, shift):
        """Rotate the whole net by `angle` about the origin, then translate by `shift`."""
        rm = self.rot(angle)
        self.place = {f: (th + angle, rm @ t + shift) for f, (th, t) in self.place.items()}


def tab_polygon(a, b, ctr, depth):
    u = (b - a) / np.linalg.norm(b - a)
    n = np.array([u[1], -u[0]])
    if n @ (a - ctr) < 0:
        n = -n
    inset = depth / math.tan(TAB_ANGLE)
    return np.array([a, a + inset * u + depth * n, b - inset * u + depth * n, b])


def layout(net):
    """Choose tab sides, then rotate and centre the net in the printable area."""
    faces = {f: Polygon(net.outline(f)[0]) for f in range(12)}
    tabs, cuts, folds = [], [], []
    done = set()
    for f in range(12):
        pts, vs = net.outline(f)
        for i in range(5):
            g = net.neighbour(f, vs[i], vs[(i + 1) % 5])
            edge = frozenset((f, g))
            if edge in net.folds:
                if f < g:
                    folds.append((f, i))
                continue
            cuts.append((f, i))
            if edge in done:
                continue
            done.add(edge)
            tabs.append((f, i, g))
    # A tab goes on whichever side of its edge does not collide with faces or other tabs.
    placed = []
    for f, i, g in tabs:
        for side in (f, g):
            pts, vs = net.outline(side)
            if side == f:
                k = i
            else:
                k = next(j for j in range(5) if net.neighbour(side, vs[j], vs[(j + 1) % 5]) == f)
            poly = Polygon(tab_polygon(pts[k], pts[(k + 1) % 5], pts.mean(0), TAB_DEPTH))
            if all(poly.intersection(q).area < 1e-6 for q in faces.values()) and \
                    all(poly.intersection(q).area < 1e-6 for _, _, q in placed):
                placed.append((side, k, poly))
                break
        else:
            raise SystemExit(f"no room for the glue tab between faces {f} and {g}")

    def extent(angle):
        rm = net.rot(angle)
        pts = np.vstack([np.asarray(p.exterior.coords) for p in faces.values()] +
                        [np.asarray(q.exterior.coords) for _, _, q in placed]) @ rm.T
        return pts.min(0), pts.max(0)

    box_w = PAGE_W - 2 * MARGIN
    box_h = PAGE_H - 2 * MARGIN - TITLE_BAND - LEGEND_BAND
    best = None
    for deg in np.arange(0, 360, 0.5):
        lo, hi = extent(math.radians(deg))
        w, h = hi - lo
        fit = max(w / box_w, h / box_h)
        if best is None or fit < best[0]:
            best = (fit, deg, lo, hi)
    fit, deg, lo, hi = best
    if fit > 1:
        raise SystemExit(f"net does not fit at R = {R_MM} mm (needs {fit:.0%} of the space)")
    box_lo = np.array([MARGIN, MARGIN + LEGEND_BAND])
    shift = box_lo + (np.array([box_w, box_h]) - (hi - lo)) / 2 - lo
    net.transform(math.radians(deg), shift)
    tab_shapes = []
    for side, k, _ in placed:
        pts, _ = net.outline(side)
        tab_shapes.append((tab_polygon(pts[k], pts[(k + 1) % 5], pts.mean(0), TAB_DEPTH),
                           pts[k], pts[(k + 1) % 5]))
    return tab_shapes, cuts, folds


# Map data -------------------------------------------------------------------------------

def countries():
    cache = HERE / ".cache" / "ne_50m_admin_0_countries.geojson"
    if not cache.exists():
        cache.parent.mkdir(exist_ok=True)
        urllib.request.urlretrieve(NE_URL, cache)
    data = cache.read_bytes()
    if hashlib.sha256(data).hexdigest() != NE_SHA256:
        raise SystemExit(f"{cache}: unexpected SHA-256; delete it and re-run")
    return json.loads(data)["features"]


def band_class(props):
    iso = props["ISO_A2_EH"]
    cont = props["CONTINENT"]
    if cont == "Antarctica":
        return 5
    if iso in ETSI:
        return 2
    if cont in ("North America", "South America") or iso in BAND_C_EXTRA:
        return 3
    if cont in ("Europe", "Africa") or props["SUBREGION"] in R1_ASIA or iso == "RU":
        return 1
    return 4


def rings(feature):
    geom = feature["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        yield from poly


def class_raster(features, step=0.04):
    """Equirectangular raster of band classes (0 = ocean)."""
    from PIL import Image, ImageDraw

    w, h = int(360 / step), int(180 / step)
    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)
    for feat in features:
        cls = band_class(feat["properties"])
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = np.asarray(poly[0])
            xy = np.column_stack([(ring[:, 0] + 180) / step, (90 - ring[:, 1]) / step])
            draw.polygon([tuple(p) for p in xy], fill=cls)
    return np.asarray(img), step


# Drawing --------------------------------------------------------------------------------

def page_raster(net, raster, step):
    """RGBA image of all faces at the output resolution."""
    px = DPI / 25.4
    w, h = round(PAGE_W * px), round(PAGE_H * px)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    palette = np.zeros((6, 3), dtype=np.uint8)
    palette[0] = [int(OCEAN[i:i + 2], 16) for i in (1, 3, 5)]
    for k, col in CLASS_COLORS.items():
        palette[k] = [int(col[i:i + 2], 16) for i in (1, 3, 5)]
    hatch = np.array([int(HATCH[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)
    for f in range(12):
        pts, _ = net.outline(f)
        x0, y0 = np.floor(pts.min(0) * px).astype(int)
        x1, y1 = np.ceil(pts.max(0) * px).astype(int)
        gx, gy = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        xy = np.column_stack([(gx.ravel() + 0.5) / px, (gy.ravel() + 0.5) / px])
        inside = MplPath(pts).contains_points(xy)
        xy, gx, gy = xy[inside], gx.ravel()[inside], gy.ravel()[inside]
        p = net.from_page(f, xy)
        lat = np.degrees(np.arcsin(np.clip(p[:, 2], -1, 1)))
        lon = np.degrees(np.arctan2(p[:, 1], p[:, 0]))
        rr = np.clip(((90 - lat) / step).astype(int), 0, raster.shape[0] - 1)
        cc = np.clip(((lon + 180) / step).astype(int), 0, raster.shape[1] - 1)
        cls = raster[rr, cc]
        col = palette[cls]
        stripe = (cls == 2) & (((gx + gy) % 14) < 4)
        col[stripe] = hatch
        rgba[gy, gx, :3] = col
        rgba[gy, gx, 3] = 255
    return rgba


def draw_borders(ax, net, features):
    for f in range(12):
        face = Polygon(net.outline(f)[0])
        c = net.c[f]
        for feat in features:
            for ring in rings(feat):
                ll = np.asarray(ring)
                p = unit(ll[:, 1], ll[:, 0])
                near = p @ c > 0.55
                # Drop the artificial edges along the antimeridian and the South Pole.
                art = (np.abs(ll[:, 0]) > 179.99) | (ll[:, 1] < -89.99)
                keep = near & ~art
                runs = np.split(np.arange(len(ll)), np.where(~keep)[0])
                for run in runs:
                    run = run[keep[run]]
                    if len(run) < 2:
                        continue
                    line = LineString(net.to_page(f, p[run])).intersection(face)
                    for part in getattr(line, "geoms", [line]):
                        if part.length > 0:
                            xs, ys = part.xy
                            ax.plot(xs, ys, color=BORDER, lw=0.18, alpha=0.75,
                                    solid_capstyle="round", zorder=3)


def halo(color="black", width=1.6):
    return [pe.withStroke(linewidth=width, foreground=color)]


def main():
    net = Net()
    tabs, cuts, folds = layout(net)
    features = countries()
    raster, step = class_raster(features)

    fig = plt.figure(figsize=(PAGE_W / 25.4, PAGE_H / 25.4), dpi=DPI)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(0, PAGE_H)
    ax.set_aspect("equal")
    ax.axis("off")

    for poly, a, b in tabs:
        ax.add_patch(MplPolygon(poly, closed=True, facecolor="#E0E0D0", edgecolor="#9A9A88",
                                lw=0.5, zorder=1))
        mid = (poly[1] + poly[2]) / 2 * 0.55 + (a + b) / 2 * 0.45
        ang = math.degrees(math.atan2(*(b - a)[::-1]))
        if ang > 90:
            ang -= 180
        elif ang < -90:
            ang += 180
        ax.text(*mid, "GLUE", fontsize=4.5, color="#8A8A78", ha="center", va="center",
                rotation=ang, zorder=2)

    ax.imshow(page_raster(net, raster, step), extent=(0, PAGE_W, 0, PAGE_H), origin="lower",
              interpolation="nearest", zorder=2)
    draw_borders(ax, net, features)

    for f, i in cuts:
        pts, _ = net.outline(f)
        a, b = pts[i], pts[(i + 1) % 5]
        ax.plot(*np.column_stack([a, b]), color=INK, lw=1.0, zorder=5, solid_capstyle="round")
    for f, i in folds:
        pts, _ = net.outline(f)
        a, b = pts[i], pts[(i + 1) % 5]
        ax.plot(*np.column_stack([a, b]), color="#333333", lw=0.8, ls=(0, (4, 3)), zorder=5)

    # Ghost lines for the five top-level triangles. Triangle k is (centre, vertex k,
    # vertex k+1) in the order of FACE_PENTAGON_VERTS, which is the order the encoder
    # uses for Cell[1] bits 7-4; the winding differs between faces, so do not re-sort.
    ghost = dict(color=INK, alpha=0.45, lw=0.45, ls=(0, (2.5, 2)), zorder=6)
    for f in range(12):
        ctr = net.to_page(f, net.c[f])
        corners = net.to_page(f, net.v[f])
        for k in range(5):
            d = corners[k] - ctr
            start = ctr + d / np.linalg.norm(d) * 3.2      # keep the face index clear
            ax.plot(*np.column_stack([start, corners[k]]), **ghost)
            mid = (corners[k] + corners[(k + 1) % 5]) / 2
            label = ctr + 0.82 * (mid - ctr)              # clear of face 2's cities
            ax.text(*label, f"T{k}", fontsize=5.5, color=INK, style="italic", ha="center",
                    va="center", alpha=0.8, path_effects=halo("white", 1.4), zorder=7)

    for f in range(12):
        ctr = net.to_page(f, net.c[f])
        ax.text(*ctr, str(f), fontsize=9, color="white", weight="bold", ha="center",
                va="center", path_effects=halo(), zorder=8)

    for name, lat, lon, off in CITIES:
        f = net.face_of(lat, lon)
        xy = net.to_page(f, unit(lat, lon))
        ax.plot(*xy, "o", ms=4, mfc="white", mec=INK, mew=0.5, zorder=9)
        ha = "center" if off[0] == 0 else "left" if off[0] > 0 else "right"
        ax.annotate(name, xy, xytext=off, textcoords="offset points", fontsize=6,
                    color="white", ha=ha, va="center",
                    path_effects=halo(width=1.2), zorder=9)
    for label, lat, lon in EXCEPTIONS:
        f = net.face_of(lat, lon)
        assert label.endswith(f"F{f}"), (label, f)
        xy = net.to_page(f, unit(lat, lon))
        ax.plot(*xy, "x", ms=5, mec="#D00000", mew=1.4, zorder=9, path_effects=halo("white", 2.6))
        ax.annotate(label, xy, xytext=(4, 4), textcoords="offset points", fontsize=6,
                    color="#D00000", weight="bold", path_effects=halo("white", 1.6), zorder=9)

    # North arrow on face 2, over the open Pacific south-west of California.
    assert net.face_of(18.0, -132.0) == 2
    base = net.to_page(2, unit(18.0, -132.0))
    tip = net.to_page(2, unit(18.5, -132.0))
    d = (tip - base) / np.linalg.norm(tip - base)
    ax.annotate("", base + 6 * d, base, zorder=9,
                arrowprops=dict(arrowstyle="-|>", color="white", lw=1.0, mutation_scale=7,
                                path_effects=halo(width=2.2)))
    ax.text(*(base + 7.8 * d), "N", fontsize=6.5, color="white", weight="bold", ha="center",
            va="center", path_effects=halo(width=1.4), zorder=9)

    # Scale bar, bottom right.
    x1, y = PAGE_W - MARGIN, MARGIN + LEGEND_BAND - 3
    ax.plot([x1 - R_MM, x1], [y, y], color=INK, lw=1.4, solid_capstyle="butt")
    for x in (x1 - R_MM, x1):
        ax.plot([x, x], [y - 1, y + 1], color=INK, lw=0.8)
    ax.text(x1 - R_MM / 2, y + 1.8, f"25 mm = {net.arc_deg:.2f}°", fontsize=6.5, color=INK,
            ha="center", va="bottom")

    top = PAGE_H - MARGIN
    ax.text(PAGE_W / 2, top - 4, "RSDGGS Dodecahedron Net — ISM Band Regulatory Coverage",
            fontsize=12, weight="bold", color=INK, ha="center", va="center")
    ax.text(PAGE_W / 2, top - 10, "Gnomonic projection · Geography continuous across all fold "
            "edges · Numbers = RSDGGS face index · See reverse for key", fontsize=7,
            style="italic", color="#555555", ha="center", va="center")

    # Legend.
    legend = [
        (CLASS_COLORS[1], None, "433 MHz"),
        (CLASS_COLORS[2], HATCH, "433 + 868 MHz"),
        (CLASS_COLORS[3], None, "902–928 MHz"),
        (CLASS_COLORS[4], None, "2.4 GHz only"),
        (CLASS_COLORS[5], None, "No standard allocation"),
        (OCEAN, None, "Ocean"),
    ]
    y = MARGIN + 9
    x = MARGIN
    for fill, hatch, label in legend:
        ax.add_patch(Rectangle((x, y - 1.5), 6, 3.2, facecolor=fill, edgecolor="#555555",
                               lw=0.3, hatch="/////" if hatch else None))
        if hatch:
            ax.add_patch(Rectangle((x, y - 1.5), 6, 3.2, fill=False, hatch="/////",
                                   edgecolor=hatch, lw=0))
        ax.text(x + 7.5, y, label, fontsize=6.5, color=INK, va="center")
        x += 13 + 1.25 * len(label)
    y = MARGIN + 3
    ax.plot([MARGIN, MARGIN + 8], [y, y], color="#333333", lw=0.8, ls=(0, (4, 3)))
    ax.text(MARGIN + 10, y, "Fold line (score & fold)", fontsize=6.5, color=INK, va="center")
    ax.plot([MARGIN + 44, MARGIN + 52], [y, y], color=INK, lw=1.0)
    ax.text(MARGIN + 54, y, "Cut line (outer edge)", fontsize=6.5, color=INK, va="center")
    ax.add_patch(Rectangle((MARGIN + 84, y - 1.4), 7, 2.8, facecolor="#E0E0D0",
                           edgecolor="#9A9A88", lw=0.5))
    ax.text(MARGIN + 93, y, "GLUE tab", fontsize=6.5, color=INK, va="center")
    ax.plot(MARGIN + 109, y, "x", ms=4, mec="#D00000", mew=1.2)
    ax.text(MARGIN + 112, y, "Boundary exception", fontsize=6.5, color=INK, va="center")
    ax.text(MARGIN + 140, y, "T0–T4 = triangle index", fontsize=6.5, color=INK,
            style="italic", va="center")

    out = HERE / "rsdggs_net_page1.png"
    fig.savefig(out, dpi=DPI, facecolor="white")
    check(fig, ax, net, tabs)
    print(out)


def check(fig, ax, net, tabs):
    """Fail if any artwork leaves the printable area."""
    px = DPI / 25.4
    print(f"pentagon circumradius: {R_MM * px:.1f} px ({R_MM} mm, {net.arc_deg:.2f}° of arc)")
    pts = np.vstack([net.outline(f)[0] for f in range(12)] + [t[0] for t in tabs])
    assert pts.min() >= MARGIN - 1e-6 and (pts[:, 0] <= PAGE_W - MARGIN).all() \
        and (pts[:, 1] <= PAGE_H - MARGIN).all(), "line art outside the margins"
    renderer = fig.canvas.get_renderer()
    lo, hi = MARGIN * px, (PAGE_W - MARGIN) * px
    for t in ax.texts:
        bb = t.get_window_extent(renderer)
        assert bb.x0 >= lo - 1 and bb.x1 <= hi + 1 and bb.y0 >= lo - 1 and \
            bb.y1 <= (PAGE_H - MARGIN) * px + 1, f"text outside the margins: {t.get_text()!r}"


if __name__ == "__main__":
    main()

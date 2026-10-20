"""Draw Figure 1 of draft-hanley-rsdggs-00: the dodecahedron net, ISM band coverage.

    python images/rsdggs_net_page1.py    # writes images/rsdggs_net_page1.png and .svg

Requires matplotlib (built with 3.10.8), numpy and shapely. The face geometry is read
from src/constants.rs, so the figure always matches the reference implementation.
Country outlines come from Natural Earth 5.1.2 (1:50m admin 0, public domain), which is
downloaded once into images/.cache and checked against a pinned SHA-256.

Output: US Letter portrait, as a 300 dpi PNG and an all-vector SVG, with 0.5 in margins. Each pentagon has a
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
from matplotlib.patches import PathPatch
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox
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

# The net: F0 with its five neighbours, F1 with its five, joined across the F6-F2 edge.
NET_TREE = {0: [4, 6, 7, 8, 10], 6: [2], 2: [1], 1: [3, 5, 9, 11]}

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

# The most populous cities on each face (Natural Earth 5.1.2 populated places, at least
# 4.5 degrees apart). Face 2 keeps hand-set label offsets in points (it is drawn with north
# up, tilted left); the other labels are placed automatically where they collide with nothing.
CITIES = [
    ("Seattle", 47.61, -122.33, (3, -5)),
    ("Vancouver", 49.28, -123.12, (-3, 4)),
    ("Los Angeles", 34.05, -118.24, (4, -1)),
    ("Denver", 39.74, -104.99, (0, 5)),
    ("Dallas", 32.78, -96.80, (4, 0)),
    ("Minneapolis", 44.98, -93.27, (-4, -2)),
    ("Chicago", 41.88, -87.63, (3, -5)),
    ("Toronto", 43.65, -79.38, (-4, 4)),
    ("New York", 40.71, -74.01, (4, 1)),
    ("Miami", 25.76, -80.19, (4, 0)),
    ("Havana", 23.11, -82.37, (4, -3)),
    ("Mexico City", 19.43, -99.13, (4, 0)),
    # face 0
    ("Auckland", -36.85, 174.76, None),
    ("Christchurch", -43.53, 172.64, None),
    ("McMurdo", -77.85, 166.67, None),
    # face 1
    ("London", 51.51, -0.13, None),
    ("Paris", 48.86, 2.35, None),
    ("Madrid", 40.42, -3.70, None),
    ("Moscow", 55.76, 37.62, None),
    ("Istanbul", 41.01, 28.98, None),
    ("Cairo", 30.04, 31.24, None),
    ("Tehran", 35.69, 51.39, None),
    # face 3
    ("Tokyo", 35.68, 139.69, None),
    ("Seoul", 37.57, 126.98, None),
    ("Beijing", 39.90, 116.40, (4, 0)),
    ("Shanghai", 31.23, 121.47, None),
    ("Delhi", 28.61, 77.21, None),
    ("Mumbai", 19.08, 72.88, None),
    ("Kolkata", 22.57, 88.36, None),
    ("Bangkok", 13.76, 100.50, None),
    ("Jakarta", -6.21, 106.85, None),
    # face 4
    ("Cape Town", -33.92, 18.42, None),
    ("Gqeberha", -33.96, 25.60, None),
    # face 5
    ("Kinshasa", -4.33, 15.31, None),
    ("Luanda", -8.84, 13.23, None),
    ("Khartoum", 15.59, 32.53, None),
    ("Riyadh", 24.71, 46.68, None),
    ("Johannesburg", -26.20, 28.05, None),
    ("Addis Ababa", 9.03, 38.74, None),
    ("Nairobi", -1.29, 36.82, None),
    ("Dubai", 25.20, 55.27, None),
    # face 6
    ("São Paulo", -23.55, -46.63, None),
    ("Buenos Aires", -34.60, -58.38, None),
    ("Lima", -12.05, -77.04, None),
    ("Bogotá", 4.71, -74.07, None),
    ("Santiago", -33.45, -70.67, None),
    ("Brasília", -15.79, -47.88, None),
    # face 7
    ("Sydney", -33.87, 151.21, None),
    ("Brisbane", -27.47, 153.03, None),
    ("Port Moresby", -9.44, 147.18, None),
    ("Suva", -18.14, 178.44, None),
    # face 8
    ("Melbourne", -37.81, 144.96, None),
    ("Adelaide", -34.93, 138.60, None),
    ("Perth", -31.95, 115.86, None),
    ("Denpasar", -8.65, 115.22, None),
    ("Hobart", -42.88, 147.33, None),
    # face 9
    ("Lagos", 6.52, 3.38, None),
    ("Abidjan", 5.36, -4.01, None),
    ("Dakar", 14.69, -17.44, None),
    ("Recife", -8.05, -34.88, None),
    ("Fortaleza", -3.73, -38.53, None),
    ("Salvador", -12.97, -38.50, None),
    # face 10
    ("Honolulu", 21.31, -157.86, None),
    ("Papeete", -17.54, -149.57, None),
    # face 11
    ("Sapporo", 43.06, 141.35, None),
    ("Khabarovsk", 48.48, 135.07, None),
    ("Petropavlovsk", 53.04, 158.65, None),
    ("Anchorage", 61.22, -149.90, None),
]
# Places whose rules differ from their face's region code (draft sections 4.2 and 8.3).
EXCEPTIONS = [
    ("NZ→F0", -45.5, 169.5),
    ("IR→F1", 32.5, 54.5),
    ("BVI→F2", 18.43, -64.62),
    ("HK/MO→F3", 22.3, 114.0),
    ("SG→F3", 1.35, 103.82),
    ("ZA→F4", -29.5, 19.5),
    ("GU→F7", 13.44, 144.79),
    ("NC→F7", -21.3, 165.5),
    ("AU→F8", -28.0, 123.0),
    ("Canaries→F9", 28.3, -15.6),
    ("Azores→F9", 38.6, -28.0),
    ("GF→F9", 4.0, -53.0),
    ("HI→F10", 21.3, -157.8),
    ("AK→F11", 64.0, -152.0),
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

def polygons(feature):
    """Each polygon of a feature as a list of rings, exterior first."""
    geom = feature["geometry"]
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]


def clip_ring(p, c, eps=0.2):
    """Clip a closed ring of sphere points to the half-space p.c >= eps (Sutherland-Hodgman).

    Straight chords between kept points project to great-circle arcs, so the gnomonic
    projection of the clipped ring is exact along every edge.
    """
    d = p @ c - eps
    if (d >= 0).all():
        return p
    out = []
    for i in range(len(p)):
        j = (i + 1) % len(p)
        if d[i] >= 0:
            out.append(p[i])
        if (d[i] >= 0) != (d[j] >= 0):
            out.append(p[i] + d[i] / (d[i] - d[j]) * (p[j] - p[i]))
    return np.array(out)


def flat_polygons(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return [q for g in getattr(geom, "geoms", []) for q in flat_polygons(g)]


def shapely_patch(geom, **kw):
    """A PathPatch for a shapely geometry's polygons, holes included, or None."""
    verts, codes = [], []
    for poly in flat_polygons(geom):
        for ring in [poly.exterior, *poly.interiors]:
            xy = np.asarray(ring.coords)
            verts += xy.tolist()
            codes += [MplPath.MOVETO] + [MplPath.LINETO] * (len(xy) - 2) + [MplPath.CLOSEPOLY]
    return PathPatch(MplPath(verts, codes), **kw) if verts else None


def draw_land(ax, net, faces, features):
    """Ocean, then each country clipped to each face, coloured by band class (all vector)."""
    for f in faces:
        face = Polygon(net.outline(f)[0])
        ax.add_patch(shapely_patch(face, facecolor=OCEAN, edgecolor=OCEAN, lw=0.2, zorder=2))
        c = net.c[f]
        for feat in features:
            cls = band_class(feat["properties"])
            parts = []
            for poly in polygons(feat):
                ring3 = [unit(np.asarray(r)[:, 1], np.asarray(r)[:, 0]) for r in poly]
                if (ring3[0] @ c).max() < 0.2:
                    continue
                clipped = [clip_ring(r, c) for r in ring3]
                if len(clipped[0]) < 3:
                    continue
                holes = [net.to_page(f, r) for r in clipped[1:] if len(r) >= 3]
                shape = Polygon(net.to_page(f, clipped[0]), holes).buffer(0).intersection(face)
                if not shape.is_empty:
                    parts.append(shape)
            if not parts:
                continue
            col = CLASS_COLORS[cls]
            for shape in parts:
                # The edge in the fill colour closes hairline seams between neighbours.
                ax.add_patch(shapely_patch(shape, facecolor=col, edgecolor=col, lw=0.2,
                                           zorder=2.1))
                if cls == 2:
                    ax.add_patch(shapely_patch(shape, fill=False, hatch="//////",
                                               edgecolor=HATCH, lw=0, zorder=2.2))


def draw_borders(ax, net, features, faces=range(12), lw=0.18):
    for f in faces:
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
                            ax.plot(xs, ys, color=BORDER, lw=lw, alpha=0.75,
                                    solid_capstyle="round", zorder=3)


def halo(color="black", width=1.6):
    return [pe.withStroke(linewidth=width, foreground=color)]


class Labeller:
    """Places labels and north arrows on the drawn faces, clear of everything drawn so far.

    A label may cross a fold line, where the map continues onto the next face, but every
    corner must be on some drawn face, so nothing hangs over a cut edge. `k` scales the
    offsets and sizes for enlarged faces.
    """

    STEPS = ((4, 0), (-4, 0), (0, 5), (0, -5), (4, 4), (-4, 4), (4, -4), (-4, -4))

    def __init__(self, fig, ax, net, faces, k=1.0):
        self.fig, self.ax, self.net, self.k = fig, ax, net, k
        self.renderer = fig.canvas.get_renderer()
        self.boxes = [t.get_window_extent(self.renderer).padded(1) for t in ax.texts]
        self.paths = {f: MplPath(ax.transData.transform(net.outline(f)[0])) for f in faces}
        self.offsets = [(dx * r * k, dy * r * k) for r in (1, 1.3) for dx, dy in self.STEPS]

    def _free(self, bb):
        corners = [(bb.x0, bb.y0), (bb.x0, bb.y1), (bb.x1, bb.y0), (bb.x1, bb.y1)]
        on = np.any([path.contains_points(corners) for path in self.paths.values()], axis=0)
        return on.all() and not any(bb.overlaps(b) for b in self.boxes)

    def block_point(self, xy):
        x, y = self.ax.transData.transform(xy)
        r = 6 * self.k
        self.boxes.append(Bbox([[x - r, y - r], [x + r, y + r]]))

    def place(self, f, xy, text, off, **kw):
        """Label a point. A hand-set offset is used as is on the net (k = 1), where it was
        tuned by eye; on enlarged faces it is only the first position tried."""
        fixed = off is not None and self.k == 1
        tries = ([(off[0] * self.k, off[1] * self.k)] if off else []) + \
            ([] if fixed else self.offsets)
        for i, (dx, dy) in enumerate(tries):
            ha = "center" if dx == 0 else "left" if dx > 0 else "right"
            va = "center" if (off and i == 0) or dy == 0 else "bottom" if dy > 0 else "top"
            t = self.ax.annotate(text, xy, xytext=(dx, dy), textcoords="offset points", ha=ha,
                                 va=va, zorder=9, **kw)
            bb = t.get_window_extent(self.renderer).padded(1)
            if fixed or self._free(bb):
                self.boxes.append(bb)
                return
            t.remove()
        raise SystemExit(f"no room for the label {text!r} on face {f}; drop or move it")

    def north_arrow(self, f, raster, step):
        """A north arrow on face f, over open water where there is room."""
        net, ax, k = self.net, self.ax, self.k
        c, e1, e2 = net.basis[f]
        cands = []
        for frac in (0.55, 0.42, 0.68):
            for deg in range(0, 360, 15):
                a = math.radians(deg)
                p = c + net.radius * frac * (math.cos(a) * e1 + math.sin(a) * e2)
                p /= np.linalg.norm(p)
                lat, lon = math.degrees(math.asin(p[2])), math.degrees(math.atan2(p[1], p[0]))
                if lat < -88 or lat > 88:
                    continue
                cell = raster[min(int((90 - lat) / step), raster.shape[0] - 1),
                              min(int((lon + 180) / step), raster.shape[1] - 1)]
                cands.append((cell != 0, lat, lon))
        cands.sort(key=lambda x: x[0])                   # open water first; stable otherwise
        for _, lat, lon in cands:
            base = net.to_page(f, unit(lat, lon))
            tip = net.to_page(f, unit(lat + 0.5, lon))
            d = (tip - base) / np.linalg.norm(tip - base)
            ends = ax.transData.transform([base, base + 6 * k * d])
            arrow = Bbox([ends.min(0) - 3 * k, ends.max(0) + 3 * k])
            t = ax.text(*(base + 7.8 * k * d), "N", fontsize=6.5 * k, color="white",
                        weight="bold", ha="center", va="center",
                        path_effects=halo(width=1.4 * k), zorder=9)
            bb = t.get_window_extent(self.renderer).padded(1)
            if self.paths[f].contains_points(ends).all() and self._free(arrow) and self._free(bb):
                ax.annotate("", base + 6 * k * d, base, zorder=9,
                            arrowprops=dict(arrowstyle="-|>", color="white", lw=1.0 * k,
                                            mutation_scale=7 * k,
                                            path_effects=halo(width=2.2 * k)))
                self.boxes += [arrow, bb]
                return
            t.remove()
        raise SystemExit(f"no room for a north arrow on face {f}")


def draw_map(fig, ax, net, faces, features, raster, step, k=1.0, cities=CITIES,
             triangles_last=False):
    """Everything on the faces themselves: map, triangles, numbers, cities, exceptions, arrows.

    `k` scales text, symbols and line weights for enlarged faces. With `triangles_last` the
    T0-T4 labels are placed after the cities, sliding toward the centre to stay clear.
    """
    draw_land(ax, net, faces, features)
    draw_borders(ax, net, features, faces, lw=0.18 * k)

    # Ghost lines for the five top-level triangles. Triangle k is (centre, vertex k,
    # vertex k+1) in the order of FACE_PENTAGON_VERTS, which is the order the encoder
    # uses for Cell[1] bits 7-4.
    ghost = dict(color=INK, alpha=0.45, lw=0.45 * k, ls=(0, (2.5, 2)), zorder=6)
    for f in faces:
        ctr = net.to_page(f, net.c[f])
        corners = net.to_page(f, net.v[f])
        for t in range(5):
            d = corners[t] - ctr
            start = ctr + d / np.linalg.norm(d) * 3.2 * k     # keep the face index clear
            ax.plot(*np.column_stack([start, corners[t]]), **ghost)
            if not triangles_last:
                mid = (corners[t] + corners[(t + 1) % 5]) / 2
                tri_label(ax, ctr + 0.82 * (mid - ctr), t, k)   # clear of face 2's cities

    for f in faces:
        ctr = net.to_page(f, net.c[f])
        ax.text(*ctr, str(f), fontsize=9 * k, color="white", weight="bold", ha="center",
                va="center", path_effects=halo(width=1.6 * k), zorder=8)
        if f in (6, 9):
            # A bar under 6 and 9 tells them apart when the folded globe is turned over.
            ax.plot([ctr[0] - 1.1 * k, ctr[0] + 1.1 * k], [ctr[1] - 2.2 * k] * 2,
                    color="white", lw=1.1 * k, solid_capstyle="butt",
                    path_effects=halo(width=2.4 * k), zorder=8)

    labels = Labeller(fig, ax, net, faces, k)
    here = [(name, lat, lon, off, net.face_of(lat, lon)) for name, lat, lon, off in cities]
    here = [c for c in here if c[4] in faces]
    exc = [(label, lat, lon, net.face_of(lat, lon)) for label, lat, lon in EXCEPTIONS]
    for label, _, _, f in exc:
        assert label.endswith(f"F{f}"), (label, f)
    exc = [e for e in exc if e[3] in faces]
    for _, lat, lon, _, f in here:
        xy = net.to_page(f, unit(lat, lon))
        ax.plot(*xy, "o", ms=4 * k, mfc="white", mec=INK, mew=0.5 * k, zorder=9)
        labels.block_point(xy)
    for _, lat, lon, f in exc:
        xy = net.to_page(f, unit(lat, lon))
        ax.plot(*xy, "x", ms=5 * k, mec="#D00000", mew=1.4 * k, zorder=9,
                path_effects=halo("white", 2.6 * k))
        labels.block_point(xy)
    for name, lat, lon, off, f in here:
        labels.place(f, net.to_page(f, unit(lat, lon)), name, off, fontsize=6 * k,
                     color="white", path_effects=halo(width=1.2 * k))
    for label, lat, lon, f in exc:
        labels.place(f, net.to_page(f, unit(lat, lon)), label, None, fontsize=6 * k,
                     color="#D00000", weight="bold", path_effects=halo("white", 1.6 * k))
    if triangles_last:
        for f in faces:
            ctr = net.to_page(f, net.c[f])
            corners = net.to_page(f, net.v[f])
            for t in range(5):
                mid = (corners[t] + corners[(t + 1) % 5]) / 2
                along = (mid - ctr) / np.linalg.norm(mid - ctr)
                side = np.array([-along[1], along[0]]) * 4 * k
                spots = [ctr + frac * (mid - ctr) + sh for frac in (0.82, 0.72, 0.62, 0.52, 0.42)
                         for sh in (0, side, -side)]
                for spot in spots:
                    txt = tri_label(ax, spot, t, k)
                    bb = txt.get_window_extent(labels.renderer).padded(1)
                    if labels._free(bb):
                        labels.boxes.append(bb)
                        break
                    txt.remove()
                else:
                    raise SystemExit(f"no room for the label T{t} on face {f}")
    for f in faces:
        labels.north_arrow(f, raster, step)
    return labels


def tri_label(ax, xy, t, k):
    return ax.text(*xy, f"T{t}", fontsize=5.5 * k, color=INK, style="italic", ha="center",
                   va="center", alpha=0.8, path_effects=halo("white", 1.4 * k), zorder=7)


def new_page():
    fig = plt.figure(figsize=(PAGE_W / 25.4, PAGE_H / 25.4), dpi=DPI)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(0, PAGE_H)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def legend(ax, y):
    """The band colour key, one row at height y."""
    entries = [
        (CLASS_COLORS[1], None, "433 MHz"),
        (CLASS_COLORS[2], HATCH, "433 + 868 MHz"),
        (CLASS_COLORS[3], None, "902–928 MHz"),
        (CLASS_COLORS[4], None, "2.4 GHz only"),
        (CLASS_COLORS[5], None, "No standard allocation"),
        (OCEAN, None, "Ocean"),
    ]
    x = MARGIN
    for fill, hatch, label in entries:
        ax.add_patch(Rectangle((x, y - 1.5), 6, 3.2, facecolor=fill, edgecolor="#555555",
                               lw=0.3))
        if hatch:
            ax.add_patch(Rectangle((x, y - 1.5), 6, 3.2, fill=False, hatch="/////",
                                   edgecolor=hatch, lw=0))
        ax.text(x + 7.5, y, label, fontsize=6.5, color=INK, va="center")
        x += 13 + 1.25 * len(label)


def save(fig, stem):
    """Write stem.png (300 dpi) and stem.svg (all vector) next to this script or below it."""
    for ext in ("png", "svg"):
        fig.savefig(stem.with_suffix("." + ext), dpi=DPI, facecolor="white",
                    metadata={"Date": None} if ext == "svg" else None)


def main():
    plt.rcParams["svg.hashsalt"] = "rsdggs"          # stable ids, so re-runs diff cleanly
    plt.rcParams["hatch.linewidth"] = 0.6
    net = Net()
    tabs, cuts, folds = layout(net)
    features = countries()
    raster, step = class_raster(features)
    fig, ax = new_page()

    for poly, a, b in tabs:
        # Outline and text only, in pure black so a colour printer uses black toner alone:
        # toner on a tab keeps the glue from holding.
        ax.add_patch(MplPolygon(poly, closed=False, facecolor="none", edgecolor="black",
                                lw=0.5, zorder=1))
        mid = (poly[1] + poly[2]) / 2 * 0.55 + (a + b) / 2 * 0.45
        ang = math.degrees(math.atan2(*(b - a)[::-1]))
        if ang > 90:
            ang -= 180
        elif ang < -90:
            ang += 180
        ax.text(*mid, "GLUE", fontsize=4.5, color="black", ha="center", va="center",
                rotation=ang, zorder=2)

    for f, i in cuts:
        pts, _ = net.outline(f)
        a, b = pts[i], pts[(i + 1) % 5]
        ax.plot(*np.column_stack([a, b]), color=INK, lw=1.0, zorder=5, solid_capstyle="round")
    for f, i in folds:
        pts, _ = net.outline(f)
        a, b = pts[i], pts[(i + 1) % 5]
        ax.plot(*np.column_stack([a, b]), color="#333333", lw=0.8, ls=(0, (4, 3)), zorder=5)

    draw_map(fig, ax, net, range(12), features, raster, step)

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

    legend(ax, MARGIN + 9)
    y = MARGIN + 3
    ax.plot([MARGIN, MARGIN + 8], [y, y], color="#333333", lw=0.8, ls=(0, (4, 3)))
    ax.text(MARGIN + 10, y, "Fold line (score & fold)", fontsize=6.5, color=INK, va="center")
    ax.plot([MARGIN + 44, MARGIN + 52], [y, y], color=INK, lw=1.0)
    ax.text(MARGIN + 54, y, "Cut line (outer edge)", fontsize=6.5, color=INK, va="center")
    ax.add_patch(Rectangle((MARGIN + 84, y - 1.4), 7, 2.8, facecolor="none",
                           edgecolor="black", lw=0.5))
    ax.text(MARGIN + 93, y, "GLUE tab", fontsize=6.5, color=INK, va="center")
    ax.plot(MARGIN + 109, y, "x", ms=4, mec="#D00000", mew=1.2)
    ax.text(MARGIN + 112, y, "Boundary exception", fontsize=6.5, color=INK, va="center")
    ax.text(MARGIN + 140, y, "T0–T4 = triangle index", fontsize=6.5, color=INK,
            style="italic", va="center")

    out = HERE / "rsdggs_net_page1"
    save(fig, out)
    check(fig, ax, net, tabs)
    print(out.with_suffix(".png"), out.with_suffix(".svg"))


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
    # Inside each tab (kept clear of its outline): grey levels only, and mostly paper.
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(int)
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    pix = np.column_stack([xs.ravel() + 0.5, h - ys.ravel() - 0.5])
    for poly, _, _ in tabs:
        inner = poly.mean(0) + 0.85 * (poly - poly.mean(0))
        p = img[MplPath(ax.transData.transform(inner)).contains_points(pix).reshape(h, w)]
        assert (p.max(1) - p.min(1) <= 2).all(), "colour on a glue tab"
        assert (p.max(1) < 250).mean() < 0.25, "shading on a glue tab"


if __name__ == "__main__":
    main()

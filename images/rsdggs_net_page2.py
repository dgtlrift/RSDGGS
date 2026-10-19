"""Draw Figure 2 of draft-rsdggs-informational-00: the dodecahedron net reference key.

    python images/rsdggs_net_page2.py    # writes images/rsdggs_net_page2.png

Requires matplotlib (built with 3.10.8). Layout coordinates are in a 2000 x 1555
grid with the origin at the top left.
"""

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

W, H = 2000, 1555
INK = "#1A1A2E"
GREY = "#555555"
RULE = "#CCCCCC"
SHADE = "#F3F3EF"
NAVY = "#1A3580"

BANDS = [
    # letter, fill, hatch, title, title color, line, detail
    ("A", "#CC2222", None, "433.050–434.790 MHz", "#CC2222", "ITU Region 1 only",
     "Europe, Africa, Middle East, Russia,\nCentral Asia, Indian Subcontinent"),
    ("B", "#1A7A5E", None, "863–870 MHz  (ETSI SRD)", "#1A7A5E", "EU / CEPT / EEA region",
     "EU member states, EEA, and select\nETSI-aligned partner nations"),
    ("C", "#D4780A", None, "902–928 MHz", "#D4780A", "Region 2 + selected Region 3",
     "Americas · Australia · New Zealand\nTaiwan · Japan (920–928 MHz only)"),
    ("D", NAVY, None, "2400–2500 MHz", NAVY, "Global — all countries",
     "Wi-Fi (802.11 b/g/n/ax)\nBluetooth · Zigbee · Thread"),
    ("", "#B0C8DC", None, "2.4 GHz only (no sub-GHz ISM)", GREY, "Most of Asia/Pacific region",
     "No 433/868/915 MHz allocation"),
    ("", "#CC2222", "#1A7A5E", "Diagonal hatching = multiple bands", INK,
     "Background color = primary band", "Hatch color = secondary band"),
]

FACES = [
    ("Polar / Antarctic", "Special coordination zone",
     "Antarctic Treaty area; no standard ISM band allocations"),
    ("ITU R1 — Europe", "ETSI · Ofcom · ARCEP · BNetzA · IDA", "433 MHz + 868 MHz + 2.4 GHz"),
    ("ITU R2 — N. America", "FCC (US) · ISED (CA) · IFT (MX)",
     "902–928 MHz + 2.4 GHz · 1-byte RSL covers all of R2"),
    ("ITU R3 — E. Asia", "MIC (JP) · MIIT (CN) · KCC (KR) · NCC (TW)",
     "2.4 GHz universal; 920–928 MHz JP; 915 MHz TW"),
    ("R1-A Africa West", "ATU West cluster · NCC (NG) · OFCOM (GH)", "433 MHz + 2.4 GHz"),
    ("R1-B Africa East", "ATU East · CCK (KE) · TCRA (TZ) · CA (ET)", "433 MHz + 2.4 GHz"),
    ("R1-C Russia / CAS", "Roskomnadzor (RU) · RRT (KZ) · MCI (UZ)", "433 MHz + 2.4 GHz"),
    ("R1-D Middle East", "ASMG · TRA (AE) · MCIT (SA) · NTRA (EG)", "433 MHz + 2.4 GHz"),
    ("R2-A S. America", "Anatel (BR) · ENACOM (AR) · SUBTEL (CL)",
     "902–928 MHz + 2.4 GHz · BR: split 902–907.5 + 915–928 MHz"),
    ("R2-B Caribbean", "NTRC cluster · FCC (PR/USVI) · BIPT (AW)", "902–928 MHz + 2.4 GHz"),
    ("R3-A S/SE Asia", "WPC/DoT (IN) · MCMC (MY) · IMDA (SG) · NTC (PH)",
     "2.4 GHz; some: 920–925 MHz (IN, SG, MY, ID)"),
    ("R3-B Oceania", "ACMA (AU) · RSM (NZ) · MCIT (PG)", "915–928 MHz (AU/NZ) + 2.4 GHz"),
]

STEPS = [
    ("Print", 'Print page 1 on US Letter (8.5×11", portrait). Select "Actual size" — '
              "do not scale to fit."),
    ("Cut", "Cut along all solid outer edges. A sharp craft knife and steel rule gives the "
            "cleanest result."),
    ("Score", "Score every dashed fold line firmly with a dull stylus or spent ballpoint, "
              "running against a ruler."),
    ("Fold", "Fold each face upward (mountain fold) along the scored dashed lines. "
             "Crease firmly."),
    ("Glue", "Apply PVA or strong stick glue to the grey GLUE tabs. Work one tab at a time."),
    ("Join", "Press each glued tab firmly against the inner face of its matching neighbour. "
             "Hold 30 seconds."),
    ("Close", "The final seam joins the last free edge. Clamp or tape on the outside while "
              "the glue sets."),
]

QUICK = [
    ("#CC2222", "433 MHz", "10 mW (EU)\n—(others)", "10% EU", "No (EU)"),
    ("#1A7A5E", "868 MHz", "25 mW EU\n500 mW 869.4", "1% / 10%", "Yes (EU)"),
    ("#D4780A", "915 MHz", "1 W FCC\n4 W EIRP CA", "None FCC", "No (FCC)"),
    ("#D4780A", "920 MHz", "10 mW JP\n25 mW AU", "1% JP", "Yes JP"),
    (NAVY, "2.4 GHz", "100 mW EU\n1 W FCC", "None", "No"),
]

CARTOGRAPHY = (
    "Each face uses a gnomonic projection centered on its dodecahedron face center. "
    "On a gnomonic projection, all great-circle arcs appear as straight lines, so country "
    "borders that cross a fold edge continue as straight lines into the adjacent face. "
    "Geographic continuity across all 11 fold edges is verified to within 0.006° of arc "
    "(numerical precision only)."
)

# Resolution per index length follows draft §5.2.
ABOUT = (
    "RSDGGS (Regulatory Spectrum Discrete Global Grid System) encodes device geographic "
    "location as a 1–8 byte index rooted in a spherical dodecahedron. Face indices align "
    "to ITU Radio Region numbers. Index length implies resolution: 1 byte = ITU Region · "
    "2 bytes = sub-regional bloc · 3 bytes = country-level · 4+ bytes = sub-national. "
    "Devices derive regulatory ISM band rules directly from their cell index with no "
    "server dependency."
)

FOOTER = (
    "RSDGGS — Regulatory Spectrum Discrete Global Grid System · draft-rsdggs-informational-00"
    " · Dodecahedron faces aligned to ITU Radio Regions · Gnomonic projection per face"
)


def text(ax, x, y, s, size=9.5, color=INK, weight="normal", style="normal", **kw):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, fontstyle=style,
            va=kw.pop("va", "top"), ha=kw.pop("ha", "left"),
            linespacing=kw.pop("linespacing", 1.4), **kw)


def rule(ax, x0, x1, y):
    ax.plot([x0, x1], [y, y], color=RULE, lw=0.8)


def heading(ax, x0, x1, y, s):
    text(ax, x0, y, s, size=13, weight="bold", va="baseline")
    rule(ax, x0, x1, y + 22)


def legend(ax, x0, x1):
    heading(ax, x0, x1, 195, "ISM Band Regulatory Coverage")
    for k, (letter, fill, hatch, title, tcolor, line, detail) in enumerate(BANDS):
        y = 240 + 102 * k
        box = FancyBboxPatch((x0 - 5, y), 120, 76, boxstyle="round,pad=0,rounding_size=4",
                             facecolor=fill, edgecolor="#333333", lw=0.8)
        ax.add_patch(box)
        if hatch:
            ax.add_patch(Rectangle((x0 - 5, y), 120, 76, fill=False, hatch="////",
                                   edgecolor=hatch, lw=0))
        if letter:
            text(ax, x0 + 55, y + 38, letter, size=15, color="white", weight="bold",
                 ha="center", va="center")
        text(ax, x0 + 130, y + 2, title, size=11, color=tcolor, weight="bold")
        text(ax, x0 + 130, y + 26, line, size=9.5)
        text(ax, x0 + 130, y + 46, detail, size=8.5, color=GREY, style="italic")

    heading(ax, x0, x1, 905, "Construction Edge Guide")
    items = [
        ("dash", "Dashed line = Fold edge", "Score firmly with a stylus or dull knife, then fold"),
        ("solid", "Solid outer edge = Cut line", "Cut cleanly with scissors or craft knife"),
        ("glue", "Grey tab = Glue surface", "Apply PVA or stick glue; press to adjacent face"),
    ]
    for k, (kind, title, line) in enumerate(items):
        y = 960 + 76 * k
        if kind == "dash":
            ax.plot([x0 + 10, x0 + 110], [y + 12, y + 12], color="#445566", lw=2.5,
                    dashes=(6, 4))
        elif kind == "solid":
            ax.plot([x0 + 8, x0 + 110], [y + 12, y + 12], color=INK, lw=3)
        else:
            ax.add_patch(FancyBboxPatch((x0 + 5, y - 6), 110, 40,
                                        boxstyle="round,pad=0,rounding_size=4",
                                        facecolor="#DDDDCC", edgecolor="#999999", lw=0.8))
            text(ax, x0 + 60, y + 14, "GLUE", size=7, color="#777777", ha="center",
                 va="center")
        text(ax, x0 + 130, y - 2, title, size=11, weight="bold")
        text(ax, x0 + 130, y + 20, line, size=9.5)

    heading(ax, x0, x1, 1230, "Cartographic Projection")
    text(ax, x0, 1268, textwrap.fill(CARTOGRAPHY, 70), size=9.5)


def faces(ax, x0, x1):
    heading(ax, x0, x1, 195, "RSDGGS Face Reference")
    cols = (x0, x0 + 60, x0 + 365)
    for x, s in zip(cols, ("F#", "Name / Regulatory Bodies", "ISM Bands Available")):
        text(ax, x, 252, s, size=9.5, weight="bold")
    rule(ax, x0, x1, 274)
    for k, (name, bodies, bands) in enumerate(FACES):
        y = 278 + 70 * k
        if k % 2 == 0:
            ax.add_patch(Rectangle((x0 - 5, y), x1 - x0 + 5, 68, facecolor=SHADE, lw=0))
        rule(ax, x0, x1, y + 69)
        ax.add_patch(Circle((x0 + 23, y + 22), 13, facecolor=NAVY, lw=0))
        text(ax, x0 + 23, y + 22, str(k), size=11 if k < 10 else 9.5, color="white",
             weight="bold", ha="center", va="center")
        text(ax, cols[1], y + 8, name, size=10.5, weight="bold")
        text(ax, cols[1], y + 32, bodies, size=8, color="#333333", style="italic")
        text(ax, cols[2], y + 9, textwrap.fill(bands, 30), size=8.5)


def right(ax, x0, x1):
    heading(ax, x0, x1, 195, "Construction Instructions")
    for k, (title, body) in enumerate(STEPS):
        y = 232 + 64 * k
        text(ax, x0 + 5, y, chr(0x2460 + k), size=13)
        text(ax, x0 + 55, y, title, size=11, weight="bold")
        text(ax, x0 + 55, y + 21, textwrap.fill(body, 92), size=8.5, color="#333333")
    rule(ax, x0, x1, 685)

    heading(ax, x0, x1, 735, "ISM Band Quick Reference")
    cx = (x0 + 5, x0 + 80, x0 + 205, x0 + 335, x0 + 445)
    ax.add_patch(FancyBboxPatch((x0 - 10, 772), 565, 40, boxstyle="round,pad=0,rounding_size=4",
                                facecolor=INK, lw=0))
    for x, s in zip(cx, ("Band", "Frequency", "Max EIRP", "Duty cycle", "LBT req.")):
        text(ax, x, 792, s, size=9, color="white", weight="bold", va="center")
    for k, (fill, freq, eirp, duty, lbt) in enumerate(QUICK):
        y = 814 + 50 * k
        ax.add_patch(Rectangle((x0 - 10, y), 565, 48, facecolor="#F7F7F5" if k % 2 == 0
                               else "white", edgecolor="#E0E0E0", lw=0.6))
        ax.add_patch(Rectangle((x0, y + 6), 70, 36, facecolor=fill, lw=0))
        for x, s in zip(cx[1:], (freq, eirp, duty, lbt)):
            text(ax, x, y + 24, s, size=8.5, va="center", linespacing=1.2)

    heading(ax, x0, x1, 1110, "About RSDGGS")
    text(ax, x0, 1148, textwrap.fill(ABOUT, 72), size=9.5)
    text(ax, x0, 1290, "draft-rsdggs-informational-00 · Independent Submission\n"
                       "IEEE 802.15.4 MAC layer · CBOR encoded · Rust reference impl",
         size=9.5)


def main():
    fig = plt.figure(figsize=(W / 100, H / 100))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    text(ax, W / 2, 65, "RSDGGS Dodecahedron Net — Reference Key", size=20, weight="bold",
         ha="center", va="center")
    text(ax, W / 2, 115, "Regulatory Spectrum Discrete Global Grid System · ISM Band Coverage"
                         " · ITU Radio Region Face Assignment", size=11, color=GREY,
         style="italic", ha="center", va="center")
    rule(ax, 50, 1950, 135)
    legend(ax, 50, 680)
    faces(ax, 750, 1310)
    right(ax, 1350, 1950)
    rule(ax, 50, 1950, 1500)
    text(ax, W / 2, 1520, FOOTER, size=8, color="#777777", ha="center", va="center")
    out = Path(__file__).with_suffix(".png")
    fig.savefig(out, dpi=250, facecolor="white")
    print(out)


if __name__ == "__main__":
    main()

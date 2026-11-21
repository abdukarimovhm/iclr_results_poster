import base64
import json
import math
import pathlib
import re
import subprocess

import segno
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
STATS = json.loads((HERE / "stats.json").read_text())
COUNTRIES = json.loads((HERE / "countries.json").read_text())
NAME = "iclr2027-rebuttal"
URL = "https://github.com/clareLab/posters"
HIDDEN = {"HK", "MO", "TW"}

W, H = 7200, 9600
BANDS = 4
L, R = 260, 6940
TOP, BOTTOM = 300, 9340
SPLIT, COLUMN = 4500, 4680
CAP = 0.698
GAP = 150
PANEL = 110
INK = "#111111"
GREY = "#5b616b"
QUIET = "#8a919c"
SOFT = "#41464e"
RULE = "#c9ced6"
GRID = "#e7eaee"
LINK = "#1a4f8b"
FRAME = "#a9afb8"
NOBODY = "#b9bec6"
GONE = "#2f343b"
NODE = "#a3aab4"
FILES = {
    ("sans", 400): "IBMPlexSans-Regular.otf",
    ("sans", 500): "IBMPlexSans-Medium.otf",
    ("sans", 600): "IBMPlexSans-SemiBold.otf",
    ("sans", 700): "IBMPlexSans-Bold.otf",
    ("cond", 400): "IBMPlexSansCondensed-Regular.otf",
    ("cond", 500): "IBMPlexSansCondensed-Medium.otf",
    ("cond", 600): "IBMPlexSansCondensed-SemiBold.otf",
}
FAMILY = {"sans": "IBM Plex Sans", "cond": "IBM Plex Sans Condensed"}
FALLBACK = {"sans": "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif", "cond": "'IBM Plex Sans Condensed', 'Arial Narrow', sans-serif"}
LOADED = {}

OVERALL = STATS["overall"]
MATCHED = STATS["matched"]
BASE = OVERALL["base"]
USED = OVERALL["used"]
OPEN = OVERALL["status"]["open"]
RANKED = 16
BOUNDS = [-0.45, -0.3, -0.15, 0.0, 0.15, 0.3, 0.45]
ALL = {
    "weight": BASE,
    "papers": BASE,
    "withdrawn": OVERALL["status"]["withdrawn"] / BASE,
    "rebuttal": OVERALL["papers_rebuttal"],
    "kept_initial": OVERALL["mean_kept_initial"],
    "final": OVERALL["mean_final"],
    "gain": OVERALL["mean_final"] - OVERALL["mean_kept_initial"],
}
SIZE = 22
HEAD = 26
TICK = 21
BODY = 48
FLAG = SIZE * 0.72 * 4 / 3
BLOCK = 60 * CAP + 80 + 44 + 16 + 4
DOT = 3.0
LAB = (12, 2.0, 22)
REACH = ((0, 14, 28, 42, 54), (0, 6, 12, 18, 24, 30, 36, 42, 48, 54))
RISE = 100
OFFSETS = (44, 104, 84, 125, 180, 22, 100)
LENS = (14.78, 160.5, 2.314, 2.672)
LIFT = 60
SHEET = 48
JOINS = {"of", "and", "for", "at", "de", "in", "für", "di", "del", "zu"}
KINDLY = {"University", "Universität", "Université", "Universidad", "Institute", "College", "School", "Academy", "Laboratory", "Center", "Centre", "Technology", "Technologies", "Research"}
NAMES = {v["name"]: k for k, v in COUNTRIES.items()}
SHAPES = {}


def font(family: str, weight: int) -> ImageFont.FreeTypeFont:
    if (family, weight) not in LOADED:
        LOADED[family, weight] = ImageFont.truetype(str(HERE / "fonts" / FILES[family, weight]), 1000)
    return LOADED[family, weight]


def measure(text: str, size: float, family: str = "sans", weight: int = 400) -> float:
    return font(family, weight).getlength(text) * size / 1000


def ink(text: str, size: float, family: str = "sans", weight: int = 400) -> tuple:
    face = font(family, weight)
    canvas = Image.new("L", (int(face.getlength(text)) + 2000, 2000), 0)
    ImageDraw.Draw(canvas).text((500, 1400), text, font=face, fill=255, anchor="ls")
    x0, y0, x1, y1 = canvas.getbbox()
    return tuple(v * size / 1000 for v in (x0 - 500, y0 - 1400, x1 - 500, y1 - 1400))


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def gamma(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def oklch(l: float, c: float, h: float) -> str:
    a, b = c * math.cos(math.radians(h)), c * math.sin(math.radians(h))
    l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (l - 0.0894841775 * a - 1.291485548 * b) ** 3
    rgb = [4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_, -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_, -0.0041960863 * l_ - 0.7034186147 * m_ + 1.707614701 * s_]
    return "#" + "".join(f"{round(255 * min(1, max(0, gamma(v)))):02x}" for v in rgb)


def mix(colour: str, t: float) -> str:
    rgb = [int(colour[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(v + (255 - v) * t):02x}" for v in rgb)


def shade(colour: str, t: float) -> str:
    return "#" + "".join(f"{round(int(colour[i:i + 2], 16) * (1 - t)):02x}" for i in (1, 3, 5))


def luminance(colour: str) -> float:
    def linear(v: float) -> float:
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(int(colour[i:i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def edge(colour: str) -> str:
    t = 0.3
    while luminance(shade(colour, t)) > 0.12 and t < 0.9:
        t += 0.05
    return shade(colour, t)


STEPS = [(0.965, 0.016), (0.875, 0.06), (0.8, 0.095), (0.72, 0.13)]
CLASSES = [oklch(l, c, 32) for l, c in reversed(STEPS)] + [oklch(l, c, 252) for l, c in STEPS]
RAISED = oklch(0.72, 0.125, 252)
LOWERED = oklch(0.64, 0.17, 30)
FAMILIES = {
    "Asia": ((8, 78), (0.46, 0.86), 0.17),
    "Europe": ((128, 192), (0.42, 0.86), 0.12),
    "North America": ((234, 272), (0.44, 0.84), 0.15),
    "Oceania": ((288, 330), (0.5, 0.82), 0.14),
    "South America": ((98, 122), (0.6, 0.88), 0.15),
    "Africa": ((40, 70), (0.4, 0.74), 0.06),
}
ORDER = ["North America", "Europe", "Asia", "Oceania", "South America", "Africa"]
SPREAD = [(0.1, 0.42), (0.62, 0.5), (0.95, 0.78), (0.38, 0.12), (0.0, 0.84), (0.8, 0.2), (0.5, 0.95), (0.22, 0.65), (0.72, 0.68), (1.0, 0.3), (0.3, 0.88), (0.88, 0.04), (0.05, 0.08), (0.55, 0.3), (0.15, 0.98), (0.45, 0.58)]
KINDS = ["#163d6e", "#3f6fae", "#84a3cf", "#c4d3e8", "#9aa1ab", "#c9ced6", "#dfe3e8"]


def continent(code: str) -> str:
    return COUNTRIES.get(code, {}).get("continent", "")


def country(code: str) -> str:
    return COUNTRIES.get(code, {}).get("name", code)


def painter(order: list) -> dict:
    seen, colours = {}, {}
    for code in order:
        family = FAMILIES.get(continent(code))
        if not family:
            colours[code] = NOBODY
            continue
        k = seen.get(continent(code), 0)
        seen[continent(code)] = k + 1
        (h0, h1), (l0, l1), chroma = family
        hf, lf = SPREAD[k % len(SPREAD)]
        light = l0 + lf * (l1 - l0)
        colours[code] = oklch(light, chroma * (1 - 0.45 * max(0, light - 0.7) / 0.3), h0 + hf * (h1 - h0))
    return colours


def tone(name: str) -> str:
    (h0, h1), (l0, l1), chroma = FAMILIES[name]
    return oklch((l0 + l1) / 2, chroma, (h0 + h1) / 2)


def klass(change: float):
    v = round(change, 2)
    if v == 0:
        return None
    k = sum(abs(v) >= b - 1e-9 for b in BOUNDS[4:])
    return CLASSES[4 + k] if v > 0 else CLASSES[3 - k]


def way(change: float) -> str:
    return RAISED if change > 1e-9 else LOWERED if change < -1e-9 else None


def fixed(value: float) -> str:
    return f"{value:,.2f}"


def score(value: float) -> str:
    return f"{value:.2f}"


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def signed(value: float) -> str:
    v = round(value, 2)
    return "0.00" if v == 0 else f"+{v:.2f}" if v > 0 else f"−{-v:.2f}"


class Canvas:
    def __init__(self, hidden: set) -> None:
        self.items = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']
        self.texts = []
        self.hidden = hidden
        self.flags = {}

    def add(self, item: str) -> None:
        self.items.append(item)

    def rect(self, x: float, y: float, w: float, h: float, fill: str, stroke: str = "", width: float = 0) -> None:
        line = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(w, 0):.2f}" height="{max(h, 0):.2f}" fill="{fill}"{line}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = INK, width: float = 2, dash: str = "") -> None:
        pattern = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{width}"{pattern}/>')

    def shape(self, d: str, fill: str, stroke: str = "", width: float = 0) -> None:
        line = f' stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"' if stroke else ""
        self.add(f'<path d="{d}" fill="{fill}"{line}/>')

    def circle(self, x: float, y: float, r: float, fill: str, stroke: str = "", width: float = 0) -> None:
        line = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        self.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}"{line}/>')

    def text(self, x: float, y: float, s: str, size: float, weight: int = 400, family: str = "sans", anchor: str = "start", fill: str = INK, spacing: float = 0, halo: float = 0, length: float = 0) -> None:
        track = f' letter-spacing="{spacing:.1f}"' if spacing else ""
        mask = f' stroke="#ffffff" stroke-width="{halo:.1f}" stroke-linejoin="round" paint-order="stroke"' if halo else ""
        fit = f' textLength="{length:.2f}" lengthAdjust="spacing"' if length else ""
        self.texts.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FALLBACK[family]}" font-size="{size:.1f}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{track}{mask}{fit}>{escape(s)}</text>')

    def flag(self, code: str, x: float, baseline: float, size: float) -> float:
        h = size * 0.72
        w = h * 4 / 3
        if code in self.hidden:
            return w
        if code not in self.flags:
            self.flags[code] = base64.b64encode((HERE / "flags" / f"{code.lower()}.svg").read_bytes()).decode()
        top = baseline - size * CAP / 2 - h / 2
        self.add(f'<use href="#flag-{code}" x="{x:.2f}" y="{top:.2f}" width="{w:.2f}" height="{h:.2f}"/>')
        self.rect(x, top, w, h, "none", FRAME, 1)
        return w

    def save(self, path: pathlib.Path) -> None:
        faces = "".join(
            f"@font-face{{font-family:'{FAMILY[family]}';font-weight:{weight};font-style:normal;src:url(data:font/otf;base64,{base64.b64encode((HERE / 'fonts' / file).read_bytes()).decode()}) format('opentype');}}"
            for (family, weight), file in FILES.items()
        )
        marks = "".join(f'<symbol id="flag-{code}" viewBox="0 0 4 3" preserveAspectRatio="none"><image width="4" height="3" preserveAspectRatio="none" href="data:image/svg+xml;base64,{data}"/></symbol>' for code, data in self.flags.items())
        head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs><style>{faces}</style>{marks}</defs>'
        path.write_text(head + "".join(self.items) + "".join(self.texts) + "</svg>")


class Grid:
    def __init__(self, cell: float = 120) -> None:
        self.cell = cell
        self.boxes: dict = {}

    def cells(self, box: tuple) -> list:
        return [(i, j) for i in range(int(box[0] // self.cell), int(box[2] // self.cell) + 1) for j in range(int(box[1] // self.cell), int(box[3] // self.cell) + 1)]

    def hit(self, box: tuple, skip: object = None) -> bool:
        for cell in self.cells(box):
            for other, owner in self.boxes.get(cell, []):
                if (skip is None or owner != skip) and box[0] < other[2] and box[2] > other[0] and box[1] < other[3] and box[3] > other[1]:
                    return True
        return False

    def add(self, box: tuple, owner: object = None) -> None:
        for cell in self.cells(box):
            self.boxes.setdefault(cell, []).append((box, owner))

    def drop(self, test) -> None:
        for cell, items in self.boxes.items():
            self.boxes[cell] = [item for item in items if not test(item[1])]


def meets(box: tuple, a: float, b: float, p: float, q: float) -> bool:
    t0, t1 = 0.0, 1.0
    for d, lo, hi, s in ((p - a, box[0], box[2], a), (q - b, box[1], box[3], b)):
        if abs(d) < 1e-9:
            if s <= lo or s >= hi:
                return False
            continue
        u0, u1 = sorted(((lo - s) / d, (hi - s) / d))
        t0, t1 = max(t0, u0), min(t1, u1)
        if t0 >= t1:
            return False
    return True


def wedge(c: Canvas, x: float, y: float, r: float, colour: str, gone: float) -> None:
    edge = 1.2 if r > 4 else 0.6
    c.circle(x, y, r, GONE if gone >= 1 - 1e-9 else colour)
    if 1e-9 < gone < 1 - 1e-9:
        a = 2 * math.pi * gone
        c.shape(f"M{x:.2f},{y:.2f} L{x:.2f},{y - r:.2f} A{r:.2f},{r:.2f} 0 {1 if gone > 0.5 else 0} 1 {x + r * math.sin(a):.2f},{y - r * math.cos(a):.2f} Z", GONE, GONE, 0.8)
    c.circle(x, y, r, "none", "#ffffff", edge)


def heading(c: Canvas, x0: float, x1: float, y: float, title: str, note: str = "") -> float:
    top = ink(title, 60, "sans", 600)[1]
    base = y - top - 1
    c.text(x0, base, title, 60, 600, spacing=8)
    if note:
        c.text(x1, base, note, 36, 400, anchor="end", fill=GREY)
    return base


def lines(y: float) -> tuple:
    l1 = y + 60 * CAP + 80
    l2 = l1 + 44
    return l1, l2, l2 + 16


def span(c: Canvas, a: float, b: float, y: float, text: str) -> None:
    c.text((a + b) / 2, y, text, HEAD, 400, anchor="middle", fill=GREY)
    c.line(a, y + 13, b, y + 13, RULE, 2)


def radius(weight: float) -> float:
    return DOT * math.sqrt(weight)


def duplicates() -> set:
    seen, twice = set(), set()
    for u in STATS["institutions"]:
        (twice if u["name"] in seen else seen).add(u["name"])
    return twice


TWICE = duplicates()
RAW = {u["name"] for u in STATS["institutions"]}


def display(u: dict) -> tuple:
    named = re.fullmatch(r"(.*) \(([^()]*)\)", u["name"])
    if named and named.group(2) in NAMES:
        return u["country"], named.group(1) if NAMES[named.group(2)] == u["country"] and named.group(1) not in RAW else u["name"]
    return (u["country"] if u["name"] in TWICE else None), u["name"]


def shape(text: str, size: float, family: str, weight: int) -> tuple:
    if (text, family, weight) not in SHAPES:
        SHAPES[text, family, weight] = ink(text, 1000, family, weight)
    return tuple(v * size / 1000 for v in SHAPES[text, family, weight])


def metrics(parts: list) -> tuple:
    x, y, wide, box = 0.0, 0.0, 0.0, None
    for part in parts:
        if part[0] == "break":
            x, y = part[1], y + part[2]
            continue
        if part[0] == "flag":
            z = part[2]
            h = z * 0.72
            top = -z * CAP / 2 - h / 2
            b = (x, y + top, x + h * 4 / 3, y + top + h)
            x += h * 4 / 3 + z * 0.28
        else:
            _, t, z, wt, f, _ = part
            g = shape(t, z, f, wt)
            b = (x + g[0], y + g[1], x + g[2], y + g[3])
            x += measure(t, z, f, wt)
        wide = max(wide, x)
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return wide, box


def halves(text: str) -> tuple:
    words = text.split(" ")
    best = None
    for i in range(1, len(words)):
        if words[i] in JOINS or words[i] in KINDLY or words[i - 1].endswith(",") or words[i].startswith("("):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            w = max(measure(a, 10, "cond", 500), measure(b, 10, "cond", 500))
            if best is None or w < best[0]:
                best = (w, a, b)
    return best[1:] if best else None


def apart(a: tuple, b: tuple) -> float:
    def point(px_: float, py_: float, s: tuple) -> float:
        dx, dy = s[2] - s[0], s[3] - s[1]
        t = max(0, min(1, ((px_ - s[0]) * dx + (py_ - s[1]) * dy) / max(dx * dx + dy * dy, 1e-9)))
        return math.hypot(s[0] + t * dx - px_, s[1] + t * dy - py_)

    def turn(p: tuple, q: tuple, r: tuple) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    p1, p2, p3, p4 = a[:2], a[2:4], b[:2], b[2:4]
    if turn(p1, p2, p3) * turn(p1, p2, p4) < 0 and turn(p3, p4, p1) * turn(p3, p4, p2) < 0:
        return 0.0
    return min(point(*p1, b), point(*p2, b), point(*p3, a), point(*p4, a))


def area(a: dict) -> str:
    return a["area"][0].upper() + a["area"][1:]


def reach() -> float:
    longest = max(measure(display(u)[1], SIZE, "cond", 500) for u in STATS["institutions"] if u["weight"] >= RANKED)
    widest = max(measure(f"{u['weight']:,.2f}", SIZE) for u in STATS["institutions"] if u["weight"] >= RANKED)
    return math.floor(R - COLUMN - (74 + FLAG + 12 + longest + 30 + widest + sum(OFFSETS)))


GLYPH = reach()


def stem(c: Canvas, x: float, y: float, key: float, colour: str, dot: float) -> None:
    a, b = sorted((x, key))
    c.rect(a, y - 2.5, b - a, 5, colour, shade(colour, 0.3), 1)
    if dot:
        c.circle(x, y, dot, colour, shade(colour, 0.3), 1.2)


def arrow(c: Canvas, x: float, y: float, side: int, colour: str) -> None:
    c.shape(f"M{x + side * 10:.2f},{y:.2f} L{x - side * 2:.2f},{y - 7:.2f} L{x - side * 2:.2f},{y + 7:.2f} Z", colour, edge(colour), 1.5)


def code(c: Canvas, x: float, y: float, cell: int) -> int:
    qr = segno.make(URL, error="m")
    runs = []
    for i, row in enumerate(qr.matrix):
        j = 0
        while j < len(row):
            if not row[j]:
                j += 1
                continue
            k = j
            while k < len(row) and row[k]:
                k += 1
            runs.append(f"M{x + cell * j},{y + cell * i}h{cell * (k - j)}v{cell}h{-cell * (k - j)}z")
            j = k
    c.shape("".join(runs), INK)
    return len(qr.matrix) * cell


def pie(c: Canvas, x: float, y: float, r: float, parts: list) -> None:
    edge = 1.2 if r > 4 else 0.6
    step = 2 * math.pi / len(parts)

    def sector(a: float, b: float) -> str:
        return f"M{x:.2f},{y:.2f} L{x + r * math.sin(a):.2f},{y - r * math.cos(a):.2f} A{r:.2f},{r:.2f} 0 {1 if b - a > math.pi else 0} 1 {x + r * math.sin(b):.2f},{y - r * math.cos(b):.2f} Z"

    for i, (colour, gone) in enumerate(parts):
        c.shape(sector(i * step, (i + 1) * step), GONE if gone >= 1 - 1e-9 else colour)
    for i in range(len(parts)):
        c.line(x, y, x + r * math.sin(i * step), y - r * math.cos(i * step), "#ffffff", 0.6)
    for i, (colour, gone) in enumerate(parts):
        if 1e-9 < gone < 1 - 1e-9:
            c.shape(sector(i * step, (i + gone) * step), GONE, GONE, 0.8)
    c.circle(x, y, r, "none", "#ffffff", edge)


def masthead(c: Canvas) -> float:
    title = "ICLR 2027 Rebuttal"
    sub = "by Country and Institution"
    meta = [("Author", "clareLab", INK), ("Contact", "https://clarelab.moe", LINK), ("Date", "Nov 19, 2026", INK), ("Reviews", "OpenReview, Nov 6 and Nov 19, 2026", INK), ("Affiliations", "OpenAlex, Nov 14, 2026", INK)]
    defs = [("Submissions", "fractional count over affiliated authors and their institutions"), ("Initial", "mean rating at review release, Nov 6"), ("Final", "mean rating on Nov 19 of the open submissions"), ("Change", "final minus initial over the same open submissions"), ("Withdrawn", "share withdrawn by Nov 19"), ("Rebuttal", "share with at least one author comment"), ("Replied", "share of reviews whose reviewer posted at least one comment"), ("Raised", "rated higher on Nov 19 than on Nov 6")]
    scope = [
        f"{USED:,} of {BASE:,} rated submissions ({100 * USED / BASE:.1f}%) on arXiv before the reviews:",
        f"{OVERALL['institutions']:,} institutions in {OVERALL['countries']} countries, initial score {OVERALL['used_mean_initial']:.2f} against {OVERALL['rest_mean_initial']:.2f} for the rest",
    ]
    keys = ["Dot area", "Line", "Dark part", "Flag", "Dashed", "Colour", "Frame", "Fill"]
    notes = [
        "1, 4, 16 and 64 submissions at release; a sector each where institutions coincide",
        "initial to final score of the submissions still open on Nov 19; an arrow runs off the axis",
        "withdrawn share; a dark dot when all withdrew, at its initial score",
        "country; on hero labels only where the name ends in a country or occurs twice",
        "share or score of all the submissions a table or chart covers",
        "raised, unchanged or lowered review or submission from Nov 6 to Nov 19",
        "area shown enlarged at lower right",
        "change, centred on zero in steps of 0.15; 0.00 unfilled",
    ]
    unit = ink(title, 1000, "sans", 700)
    size = (SPLIT - L) * 1000 / (unit[2] - unit[0])
    base = TOP - unit[1] * size / 1000
    c.text(L - unit[0] * size / 1000, base, title, size, 700, length=measure(title, size, "sans", 700))
    cell = 10
    side = len(segno.make(URL, error="m").matrix) * cell
    top = round(base + 96)
    bottom = top + side
    pitch = 64
    big = 74 / CAP
    lead = ink(sub, big)
    c.text(L - lead[0] + 1, top + big * CAP, sub, big, 400, fill=GREY)
    link = ink(URL, 58)
    upper = top + big * CAP
    lower = bottom - pitch - BODY * CAP
    c.text(L - link[0] + 1, (upper + lower + 58 * CAP) / 2, URL, 58, 400, fill=LINK)
    for i, v in enumerate(scope):
        c.text(L, bottom - pitch * (1 - i), v, BODY, 400)
    stack = max(lead[2] - lead[0], link[2] - link[0], *(measure(v, BODY) for v in scope))
    key = 6.25 * BODY
    widest = max(measure(v, BODY) for _, v in defs)
    vx = SPLIT - widest
    kx = vx - key
    code(c, round(L + stack + (kx - L - stack - side) / 2), top, cell)
    for i, (k, v, colour) in enumerate(meta):
        c.text(kx, bottom - pitch * (4 - i), k, BODY, 400, fill=GREY)
        c.text(vx, bottom - pitch * (4 - i), v, BODY, 400, fill=colour)
    first = bottom + 112
    for i, (k, v) in enumerate(defs):
        c.text(kx, first + i * pitch, k, BODY, 400, fill=GREY)
        c.text(vx, first + i * pitch, v, BODY, 400, length=widest if measure(v, BODY) == widest else 0)
    s = BODY / 40
    gx = L + key
    mid = BODY * CAP / 2
    tx = kx - GAP - max(measure(n, BODY) for n in notes)
    for i, (k, n) in enumerate(zip(keys, notes)):
        c.text(L, first + i * pitch, k, BODY, 400, fill=GREY)
        c.text(tx, first + i * pitch, n, BODY, 400)
    y = first
    x = gx
    for value in (1, 4, 16, 64):
        r = radius(value)
        c.circle(x + r, y - mid, r, NOBODY)
        x += 2 * r + 14 * s
    pie(c, x + 10 * s + radius(64), y - mid, radius(64), [(NOBODY, 1), (NOBODY, 0.5), (NOBODY, 0), (NOBODY, 0), (NOBODY, 0)])
    y += pitch
    c.rect(gx + 20 * s - 2, y - mid - 6, 4, mid + 12, mix(QUIET, 0.45))
    c.circle(gx + 20 * s, y - mid - 6, 10 * s, QUIET, "#ffffff", 1.2)
    stem(c, gx + 118 * s, y - mid, gx + 58 * s, QUIET, 9 * s)
    y += pitch
    wedge(c, gx + 20 * s, y - mid, 20 * s, NOBODY, 0.25)
    c.rect(gx + 58 * s, y - mid - 9 * s, 72 * s, 18 * s, GRID)
    c.rect(gx + 58 * s, y - mid - 9 * s, 18 * s, 18 * s, GONE)
    c.circle(gx + 150 * s, y - mid, 12 * s, GONE, "#ffffff", 1.2)
    y += pitch
    c.flag("US", gx, y, BODY)
    y += pitch
    c.line(gx, y - mid, gx + 130 * s, y - mid, QUIET, 3, "14 10")
    y += pitch
    x = gx
    for colour in (RAISED, None, LOWERED):
        if colour:
            c.rect(x, y - mid - 15 * s, 44 * s, 30 * s, colour)
        else:
            c.rect(x + 1, y - mid - 15 * s + 1, 44 * s - 2, 30 * s - 2, "none", QUIET, 2)
        x += 44 * s + 12 * s
    y += pitch
    c.rect(gx + 1, y - mid - 15 * s, 130 * s, 30 * s, "none", QUIET, 2)
    y += pitch
    sw = (tx - 40 - gx) / len(CLASSES)
    for k, colour in enumerate(CLASSES):
        c.rect(gx + k * sw, y - mid - 15 * s, sw, 30 * s, colour)
    return y + ink("gy", BODY)[3]


COARSE = [0, 180] + [a for step in range(15, 91, 15) for a in (360 - step, step, 180 + step, 180 - step)]
FINE = [0, 180] + [a for step in range(5, 91, 5) for a in (360 - step, step, 180 + step, 180 - step)]


class Placer:
    def __init__(self, spots: dict, bounds: tuple, tails: dict, bare: set) -> None:
        self.spots = spots
        self.bounds = bounds
        self.tails = tails
        self.bare = bare
        self.dots = Grid()
        for k, (x, y, r) in spots.items():
            self.dots.add((x - r - 2, y - r - 2, x + r + 2, y + r + 2), k)
        self.labels = Grid()
        self.paths = Grid()
        self.placed = {}
        self.fixed = Grid()
        self.memo = {}
        self.owns = {}

    def block(self, box: tuple) -> None:
        self.fixed.add(box)

    def gap(self, k: str, box: tuple) -> float:
        x, y, r = self.spots[k]
        return math.hypot(min(max(x, box[0]), box[2]) - x, min(max(y, box[1]), box[3]) - y) - r

    def rivals(self, k: str, box: tuple, within: float, among: set = None) -> bool:
        seen = set()
        for cell in self.dots.cells((box[0] - within, box[1] - within, box[2] + within, box[3] + within)):
            for _, owner in self.dots.boxes.get(cell, []):
                if owner != k and owner not in seen and (among is None or owner in among):
                    seen.add(owner)
                    if self.gap(owner, box) < within:
                        return True
        return False

    def fit(self, k: str, boxed: tuple):
        key = (k, boxed)
        if key not in self.owns:
            x0, y0, x1, y1 = self.bounds
            tail = self.tails.get(k)
            own = None
            if not (boxed[0] < x0 or boxed[2] > x1 or boxed[1] < y0 or boxed[3] > y1) and not (tail and boxed[0] < tail[2] and boxed[2] > tail[0] and boxed[1] < tail[3] and boxed[3] > tail[1]):
                gap = self.gap(k, boxed)
                if gap >= 3 and not self.fixed.hit(boxed):
                    own = gap
            self.owns[key] = own
        return self.owns[key]

    def crowd(self, box: tuple, glyph: tuple, z: float, room: float, allowed: set) -> set:
        soft = set()
        g0, g1, g2, g3 = glyph
        boxes = self.labels.boxes
        size = self.labels.cell
        cells = [(i, j) for i in range(int((box[0] - 40) // size), int((box[2] + 40) // size) + 1) for j in range(int((box[1] - 40) // size), int((box[3] + 40) // size) + 1)]
        for cell in cells:
            for _, owner in boxes.get(cell, ()):
                oz, ob, oroom, ok = owner
                if ok in soft:
                    continue
                em = z if z > oz else oz
                h = ob[0] - g2 if ob[0] - g2 > g0 - ob[2] else g0 - ob[2]
                v = ob[1] - g3 if ob[1] - g3 > g1 - ob[3] else g1 - ob[3]
                if (v < 0.35 * em and h < (1 if v < 0 else (room if room > oroom else oroom)) * em) or (h < 0 and v < em and min(abs(ob[0] - g0), abs(ob[2] - g2), abs(ob[0] + ob[2] - g0 - g2) / 2) < em):
                    if ok not in allowed:
                        return {ok}
                    soft.add(ok)
        return soft

    def cuts(self, box: tuple) -> set:
        out = set()
        for cell in self.paths.cells(box):
            for _, (seg, owner) in self.paths.boxes.get(cell, []):
                if meets(box, *seg):
                    out.add(owner)
        return out

    def crossing(self, k: str, seg: tuple):
        a, b, p, q = seg
        box = (min(a, p), min(b, q), max(a, p), max(b, q))
        for cell in self.dots.cells(box):
            for _, owner in self.dots.boxes.get(cell, []):
                if owner != k:
                    x, y, r = self.spots[owner]
                    if apart(seg, (x, y, x, y)) < r + 2:
                        return None
        soft = set()
        for cell in self.fixed.cells(box):
            for other, _ in self.fixed.boxes.get(cell, []):
                if meets(other, a, b, p, q):
                    return None
        for cell in self.labels.cells(box):
            for other, owner in self.labels.boxes.get(cell, []):
                if meets(other, a, b, p, q):
                    soft.add(owner[3])
        for cell in self.paths.cells((box[0] - 3, box[1] - 3, box[2] + 3, box[3] + 3)):
            for _, (other, owner) in self.paths.boxes.get(cell, []):
                if apart(seg, other) < 3:
                    soft.add(owner)
        return soft

    def options(self, k: str, parts: list, z: float, reach: tuple, fine: bool) -> list:
        key = (k, repr(parts), z, reach, fine)
        if key not in self.memo:
            self.memo[key] = [o for o in self.search(k, parts, z, reach, fine) if self.fit(k, o[7]) is not None]
        return self.memo[key]

    def search(self, k: str, parts: list, z: float, reach: tuple, fine: bool) -> list:
        cx, cy, r = self.spots[k]
        width, ib = metrics(parts)
        halo = 0.1 * z + 1
        pad = z * 0.18
        out = []
        for distance in reach:
            for angle in FINE if fine else COARSE:
                a = math.radians(angle)
                ax, ay = cx + (r + 6 + distance) * math.cos(a), cy + (r + 6 + distance) * math.sin(a)
                if abs(math.sin(a)) < 0.5:
                    ly = ay - (ib[1] + ib[3]) / 2
                elif math.sin(a) < 0:
                    ly = ay - pad - halo - ib[3]
                else:
                    ly = ay + pad + halo - ib[1]
                xs = [ax + pad if math.cos(a) > 0 else ax - width - pad] if abs(math.cos(a)) > 0.5 else [ax - width / 2, ax + pad - width * 0.1, ax - width * 0.9 - pad, ax - width * 0.25, ax - width * 0.75, ax - pad, ax + pad - width]
                for lx in xs:
                    glyph = (lx + ib[0], ly + ib[1], lx + ib[2], ly + ib[3])
                    boxed = (glyph[0] - halo, glyph[1] - halo, glyph[2] + halo, glyph[3] + halo)
                    rise = abs((boxed[1] + boxed[3]) / 2 - cy)
                    side = max(0, boxed[0] - cx - r, cx - r - boxed[2])
                    if rise <= RISE + r:
                        out.append((rise + 0.35 * side + distance * 0.2, distance, ax, ay, lx, ly, glyph, boxed))
        out.sort(key=lambda o: (o[1] > 10, o[0]))
        return out

    def test(self, k: str, option: tuple, z: float, room: float, margin: float, allowed: set):
        _, distance, ax, ay, lx, ly, glyph, boxed = option
        own = self.fit(k, boxed)
        if own is None:
            return None
        soft = self.crowd(boxed, glyph, z, room, allowed)
        if soft - allowed:
            return None
        soft |= self.cuts(boxed)
        if soft - allowed:
            return None
        seg = None
        if distance > 10:
            if self.rivals(k, boxed, z / 4) or self.rivals(k, boxed, max(7, 0.35 * z), self.bare):
                return None
            cx, cy, r = self.spots[k]
            norm = max(math.hypot(ax - cx, ay - cy), 1)
            seg = (cx + r * (ax - cx) / norm, cy + r * (ay - cy) / norm, ax, ay)
            hit = self.crossing(k, seg)
            if hit is None or hit - allowed:
                return None
            soft |= hit
        elif self.rivals(k, boxed, own + margin):
            return None
        return soft, (lx, ly, glyph, boxed, seg)

    def drop(self, k: str) -> None:
        self.labels.drop(lambda o: o is not None and o[3] == k)
        self.paths.drop(lambda o: o[1] == k)
        del self.placed[k]

    def save(self) -> tuple:
        return {c: list(v) for c, v in self.labels.boxes.items()}, {c: list(v) for c, v in self.paths.boxes.items()}, dict(self.placed)

    def load(self, state: tuple) -> None:
        self.labels.boxes = {c: list(v) for c, v in state[0].items()}
        self.paths.boxes = {c: list(v) for c, v in state[1].items()}
        self.placed = dict(state[2])

    def put(self, k: str, parts: list, z: float, room: float, spot: tuple, ink_: tuple) -> None:
        lx, ly, glyph, boxed, seg = spot
        self.labels.add(boxed, (z, glyph, room, k))
        if seg:
            self.paths.add((min(seg[0], seg[2]), min(seg[1], seg[3]), max(seg[0], seg[2]), max(seg[1], seg[3])), (seg, k))
        self.placed[k] = (lx, ly, parts, seg, ink_)

    def attempt(self, k: str, parts: list, z: float, reach: tuple, fine: bool, ink_: tuple, room: float = 0.35, margin: float = 3, allowed: set = frozenset(), far: bool = True):
        for option in self.options(k, parts, z, reach, fine):
            if not far and option[1] > 10:
                break
            found = self.test(k, option, z, room, margin, allowed)
            if found:
                soft, spot = found
                for o in soft:
                    self.drop(o)
                self.put(k, parts, z, room, spot, ink_)
                return soft
        return None


def layering(glyphs: dict) -> list:
    keys = list(glyphs)
    points = {}
    for k in keys:
        x, y, r, dark = glyphs[k]
        disc, part = [], []
        for i in range(160):
            rr = r * math.sqrt((i + 0.5) / 160)
            qx, qy = x + rr * math.cos(i * 2.399963), y + rr * math.sin(i * 2.399963)
            disc.append((qx, qy))
            a = math.degrees(math.atan2(qx - x, y - qy)) % 360
            if any(lo <= a <= hi for lo, hi in dark):
                part.append((qx, qy))
        points[k] = (disc, part)
    grid = Grid(80)
    for k in keys:
        x, y, r, _ = glyphs[k]
        grid.add((x - r, y - r, x + r, y + r), k)
    near = {}
    for k in keys:
        x, y, r, _ = glyphs[k]
        near[k] = sorted({o for cell in grid.cells((x - r, y - r, x + r, y + r)) for _, o in grid.boxes.get(cell, []) if o != k and math.hypot(glyphs[o][0] - x, glyphs[o][1] - y) < r + glyphs[o][2] + 1})
    order = sorted(keys, key=lambda k: (-glyphs[k][2], sum(hi - lo for lo, hi in glyphs[k][3]), k))

    def seen(k: str, pos: dict, ps: list) -> float:
        if not ps:
            return 1.0
        over = [glyphs[o] for o in near[k] if pos[o] > pos[k]]
        return sum(1 for qx, qy in ps if all(math.hypot(qx - a, qy - b) >= c + 0.6 for a, b, c, _ in over)) / len(ps)

    def worth(k: str, pos: dict) -> float:
        return min(min(seen(k, pos, points[k][1]), 0.5) / 0.5, min(seen(k, pos, points[k][0]), 0.35) / 0.35)

    for _ in range(400):
        pos = {k: i for i, k in enumerate(order)}
        bad = sorted((seen(k, pos, points[k][1]), k) for k in keys if glyphs[k][3])
        moved = False
        for v, k in bad:
            if v >= 0.5:
                break
            over = [o for o in near[k] if pos[o] > pos[k]]
            if not over:
                continue
            target = max(pos[o] for o in over)
            trial = order[:pos[k]] + order[pos[k] + 1:target + 1] + [k] + order[target + 1:]
            tpos = {o: i for i, o in enumerate(trial)}
            if min(worth(o, tpos) for o in [k] + over) > min(worth(o, pos) for o in [k] + over) + 1e-9:
                order = trial
                moved = True
                break
        if not moved:
            break
    return order


LAYOUT = {}


def hero(c: Canvas, colours: dict, ranks: dict, box: tuple, y: float, upper: list, key: tuple) -> None:
    x0, y0, x1, y1 = box
    heading(c, L, SPLIT, y, "INSTITUTIONS", f"every institution from 1 submission, {USED:,} matched submissions")
    units = sorted([u for u in STATS["institutions"] if u["weight"] >= 1], key=lambda u: -u["weight"])
    hi = 2 ** math.ceil(math.log2(max(u["weight"] for u in units)))
    bottom, top = 1.0, 3.4

    def px(w: float) -> float:
        return x0 + math.log2(w) / math.log2(hi) * (x1 - x0)

    def py(m: float) -> float:
        return y1 - (m - bottom) / (top - bottom) * (y1 - y0)

    def level(u: dict) -> float:
        return u["final"] if u["final"] is not None else u["initial"]

    def tip(u: dict) -> float:
        return u["kept_initial"] if u["final"] is not None else level(u)

    spots = {u["institution"]: (px(u["weight"]), py(level(u)), radius(u["weight"])) for u in units}
    groups = {}
    for u in units:
        groups.setdefault(tuple(round(v, 2) for v in spots[u["institution"]]), []).append(u)
    pile = {u["institution"]: g for g in (sorted(g, key=lambda u: (-u["withdrawn"], u["country"], u["institution"])) for g in groups.values() if len(g) > 1) for u in g}
    marks = {k: (x, yy, radius(sum(u["weight"] for u in pile[k]))) if k in pile else (x, yy, r) for k, (x, yy, r) in spots.items()}
    glyphs = {}
    for u in units:
        k = u["institution"]
        if k in pile and pile[k][0] is not u:
            continue
        members = pile.get(k, [u])
        glyphs[k] = (*marks[k], [(360 * i / len(members), 360 * (i + min(1, v["withdrawn"])) / len(members)) for i, v in enumerate(members) if v["withdrawn"] > 1e-9])
    for k in range(int(round((top - bottom) * 5)) + 1):
        v = bottom + k / 5
        c.line(x0, py(v), x1, py(v), GRID, 2)
        c.text(x0 - 32, py(v) + 34 * CAP / 2, score(v), 34, 400, anchor="end", fill=GREY)
    w = 1
    while w <= hi:
        c.line(px(w), y0, px(w), y1, GRID, 2)
        c.text(px(w), y1 + 56, str(w), 34, 400, anchor="middle", fill=GREY)
        w *= 2
    c.text(SPLIT, y1 + 118, "Submissions at release", 40, 500, anchor="end")
    c.text(L, y0 - 56, "Score", 40, 500)
    keys = ((MATCHED["final"], f"Mean final {MATCHED['final']:.2f}"), (MATCHED["kept_initial"], f"Mean initial of the open submissions {MATCHED['kept_initial']:.2f}"))
    for v, _ in keys:
        c.line(x0, py(v), x1, py(v), QUIET, 3, "14 10")

    def covers(m: tuple) -> bool:
        for u in units:
            x, yy, r = marks[u["institution"]]
            ky = py(tip(u))
            if x + r > m[0] and x - r < m[2] and max(yy, ky) + r > m[1] and min(yy, ky) - r < m[3]:
                return True
        return False

    places, masks = [], []
    cursor = y0 + 4
    for iw, ih, draw in upper:
        places.append(((SPLIT - iw, cursor, SPLIT, cursor + ih), draw))
        cursor += ih + GAP
    masks.append((SPLIT - max(iw for iw, _, _ in upper) - 60, y0 - 46, SPLIT, cursor - GAP + 50))
    kw, kh, draw = key
    right = masks[0][0] - PANEL
    places.append(((right - kw, y0 + 4, right, y0 + 4 + kh), draw))
    masks.append((right - kw - 40, y0 - 30, masks[0][0] + 1, y0 + 4 + kh + 40))
    wa, wb, sa, sb = LENS
    lens = (px(wa), py(sb), px(wb), py(sa))
    for x, yy, r in marks.values():
        inner = lens[0] <= x <= lens[2] and lens[1] <= yy <= lens[3]
        reach = min(x - lens[0], lens[2] - x, yy - lens[1], lens[3] - yy) if inner else math.hypot(max(lens[0] - x, 0, x - lens[2]), max(lens[1] - yy, 0, yy - lens[3]))
        if reach < r + 1:
            raise RuntimeError("lens frame cuts a dot")
    fx1, fy1 = x1, y1 - LIFT
    zoom = 3.0
    while True:
        fx0, fy0 = fx1 - (lens[2] - lens[0]) * zoom, fy1 - (lens[3] - lens[1]) * zoom
        sheet = (fx0 - 22 - measure("2.60", 30) - SHEET, fy0 - 18 - 30 * CAP - SHEET, x1 - 1, fy1 + 24)
        if not covers(sheet) and not any(sheet[0] < m[2] and sheet[2] > m[0] and sheet[1] < m[3] and sheet[3] > m[1] for m in masks):
            break
        zoom = round(zoom - 0.01, 2)
    masks.append(sheet)
    for m in masks[:2]:
        if covers(m):
            raise RuntimeError("inset covers an institution")
    for m in masks:
        c.rect(m[0], m[1], m[2] - m[0], m[3] - m[1], "#ffffff")
    for (a, b, _, _), draw in places:
        draw(a, b)

    def lx_(x: float) -> float:
        return fx0 + (x - lens[0]) * zoom

    def ly_(yy: float) -> float:
        return fy0 + (yy - lens[1]) * zoom

    inside = [u for u in units if wa <= u["weight"] <= wb and sa <= level(u) <= sb]
    seats = {k: (lx_(x), ly_(yy), r) for k, (x, yy, r, _) in glyphs.items() if lx_(x) + r > fx0 and lx_(x) - r < fx1 and ly_(yy) + r > fy0 and ly_(yy) - r < fy1}
    if any(min(x - fx0, fx1 - x, yy - fy0, fy1 - yy) < r + 2 for x, yy, r in seats.values()) or {u["institution"] for u in inside} != set(seats):
        raise RuntimeError("inset frame cuts a dot")
    dots = Grid()
    for k, (x, yy, r) in marks.items():
        dots.add((x - r - 2, yy - r - 2, x + r + 2, yy + r + 2), k)
    notes = []
    for k, (v, text) in enumerate(keys):
        tw = measure(text, 30, "sans", 500)
        ly = py(v) - 14 if k == 0 else py(v) + 14 + 30 * CAP
        for right in range(int(x1), int(x0 + tw), -20):
            boxed = (right - tw - 8, ly - 30 * CAP - 6, right + 4, ly + 8)
            if any(boxed[0] < m[2] and boxed[2] > m[0] and boxed[1] < m[3] and boxed[3] > m[1] for m in masks + [lens]):
                continue
            if not dots.hit(boxed):
                notes.append((right, ly, text, boxed))
                break

    def size(u: dict) -> float:
        return min(LAB[2], LAB[0] + LAB[1] * math.floor(math.log2(u["weight"])))

    def name(u: dict, split: bool = False) -> list:
        code, text = display(u)
        out = [("flag", code, size(u))] if code else []
        pair = halves(text) if split else None
        if not pair:
            return out + [("text", text, size(u), 500, "cond", INK)]
        indent = metrics(out)[0] if out else 0
        return out + [("text", pair[0], size(u), 500, "cond", INK), ("break", indent, round(1.08 * size(u))), ("text", pair[1], size(u), 500, "cond", INK)]

    def band(u: dict) -> int:
        return min(4, int(math.log2(u["weight"])))

    def pen(u: dict) -> tuple:
        return colours.get(u["country"], NOBODY), 2 if u["weight"] >= 2 else 1.2

    def settle(placer: Placer, u: dict) -> bool:
        k = u["institution"]
        for far in (False, True):
            for split in (False, True):
                if split and not halves(display(u)[1]):
                    break
                if far and placer.attempt(k, name(u, split), size(u), REACH[0], False, pen(u)) is not None:
                    return True
                if placer.attempt(k, name(u, split), size(u), REACH[1], True, pen(u), margin=2, far=far) is not None:
                    return True
        return False

    def label(placer: Placer, group: list, tries: int = 1) -> None:
        by = {u["institution"]: u for u in group}
        top = [u for u in group if u["institution"] in ranks]
        room = {u["institution"]: sum(1 for o in placer.options(u["institution"], name(u), size(u), REACH[0], False) if placer.test(u["institution"], o, size(u), 0.35, 2, frozenset())) for u in top}
        orders = [
            lambda u: (room[u["institution"]] > 12, room[u["institution"]], -u["weight"]),
            lambda u: -u["weight"],
            lambda u: (room[u["institution"]], -u["weight"]),
            lambda u: placer.spots[u["institution"]][0],
            lambda u: -placer.spots[u["institution"]][0],
        ]
        start, best = placer.save(), None
        for key in orders[:tries]:
            placer.load(start)
            top.sort(key=key)
            for u in top:
                settle(placer, u)
            repair(placer, top * 2, by)
            if best is None or len(placer.placed) > len(best[2]):
                best = placer.save()
            if len(placer.placed) == len(top):
                break
        placer.load(best)
        late = {}
        for _ in range(16):
            missing = [u["institution"] for u in top if u["institution"] not in placer.placed]
            if not missing:
                break
            for k in missing:
                late[k] = late.get(k, 0) + 1
            placer.load(start)
            top.sort(key=lambda u: -late.get(u["institution"], 0))
            for u in top:
                settle(placer, u)
            repair(placer, top * 2, by)
            if len(placer.placed) > len(best[2]):
                best = placer.save()
        placer.load(best)
        for u in top:
            if u["institution"] not in placer.placed:
                rescue(placer, u, by, 2, frozenset())
        repair(placer, [u for u in group if u["institution"] not in ranks and band(u) == 3], by)
        share = 1.0
        for b in (3, 2, 1, 0):
            members = [u for u in group if u["institution"] not in ranks and band(u) == b]
            for u in members:
                if sum(1 for v in members if v["institution"] in placer.placed) >= math.floor(share * len(members) + 1e-9):
                    break
                settle(placer, u)
            if b == 3 and members:
                share = sum(1 for v in members if v["institution"] in placer.placed) / len(members)

    def rescue(placer: Placer, u: dict, by: dict, depth: int, banned: frozenset) -> bool:
        k = u["institution"]
        for split in (False, True):
            if split and not halves(display(u)[1]):
                break
            every = set(placer.placed) - banned
            tried = [found for found in (placer.test(k, option, size(u), 0.35, 2, every) for option in placer.options(k, name(u, split), size(u), REACH[1], True)) if found and len(found[0]) <= 2 + depth]
            for found in sorted(tried, key=lambda f: len(f[0]))[:20 * depth]:
                state = placer.save()
                for o in found[0]:
                    placer.drop(o)
                placer.put(k, name(u, split), size(u), 0.35, found[1], pen(u))
                if all(settle(placer, by[o]) or (depth > 1 and rescue(placer, by[o], by, depth - 1, banned | {k})) for o in sorted(found[0], key=lambda o: -by[o]["weight"])):
                    return True
                placer.load(state)
        return False

    def repair(placer: Placer, queue: list, by: dict) -> None:
        for u in queue:
            k = u["institution"]
            if k in placer.placed:
                continue
            if u["institution"] not in ranks and settle(placer, u):
                continue
            done = False
            for split in (False, True):
                if done or (split and not halves(display(u)[1])):
                    break
                every = set(placer.placed)
                tried = [found for found in (placer.test(k, option, size(u), 0.35, 2, every) for option in placer.options(k, name(u, split), size(u), REACH[1], True)) if found and len(found[0]) <= 5]
                for found in sorted(tried, key=lambda f: len(f[0]))[:40]:
                    state = placer.save()
                    for o in found[0]:
                        placer.drop(o)
                    placer.put(k, name(u, split), size(u), 0.35, found[1], pen(u))
                    if all(settle(placer, by[o]) for o in sorted(found[0], key=lambda o: -by[o]["weight"])):
                        done = True
                        break
                    placer.load(state)

    if box not in LAYOUT:
        tails = {u["institution"]: (spots[u["institution"]][0] - 3, min(spots[u["institution"]][1], py(tip(u))), spots[u["institution"]][0] + 3, max(spots[u["institution"]][1], py(tip(u)))) for u in units}
        main = Placer(marks, (x0, y0, x1, y1), tails, set(marks))
        for m in masks + [(lens[0] - 2, lens[1] - 2, lens[2] + 2, lens[3] + 2)]:
            main.block(m)
        for *_, boxed in notes:
            main.block(boxed)
        label(main, [u for u in units if u not in inside and u["institution"] not in pile])
        lows = {k: max(fy0, min(fy1, ly_(py(tip(u))))) for u in units for k in [u["institution"]] if k in seats}
        lens_tails = {k: (seats[k][0] - 3, min(seats[k][1], ky), seats[k][0] + 3, max(seats[k][1], ky)) for k, ky in lows.items()}
        zoomed = Placer(seats, (fx0 + 2, fy0 + 2, fx1 - 2, fy1 - 2), lens_tails, set())
        label(zoomed, inside, 5)
        LAYOUT[box] = (main, zoomed, layering(glyphs))
    main, zoomed, order = LAYOUT[box]
    by = {u["institution"]: u for u in units}

    def disc(k: str, x: float, yy: float, r: float) -> None:
        if k in pile:
            pie(c, x, yy, r, [(colours.get(u["country"], NOBODY), u["withdrawn"]) for u in pile[k]])
        else:
            wedge(c, x, yy, r, colours.get(by[k]["country"], NOBODY), by[k]["withdrawn"])

    for k in order:
        for u in pile.get(k, [by[k]]):
            if u["final"] is None or abs(u["gain"]) < 1e-9:
                continue
            x, yy, r = spots[u["institution"]]
            ky = py(u["kept_initial"])
            c.rect(x - max(1.4, 0.1 * r) / 2, min(yy, ky), max(1.4, 0.1 * r), abs(ky - yy), mix(colours.get(u["country"], NOBODY), 0.45))
    c.rect(lens[0], lens[1], lens[2] - lens[0], lens[3] - lens[1], "none", QUIET, 2)
    for placer in (main, zoomed):
        for lx, ly, parts, seg, (colour, width) in placer.placed.values():
            if seg:
                c.line(*seg, colour, width)
    for k in order:
        disc(k, *marks[k])
    v = math.ceil(sa * 10 - 1e-9) / 10
    while v <= sb + 1e-9:
        c.line(fx0, ly_(py(v)), fx1, ly_(py(v)), GRID, 2)
        c.text(fx0 - 22, ly_(py(v)) + 30 * CAP / 2, score(v), 30, 400, anchor="end", fill=GREY)
        v += 0.1
    w = 2 ** math.ceil(math.log2(wa))
    while w <= wb:
        c.line(lx_(px(w)), fy0, lx_(px(w)), fy1, GRID, 2)
        c.text(lx_(px(w)), fy0 - 18, str(w), 30, 400, anchor="middle", fill=GREY)
        w *= 2
    for v, _ in keys:
        if sa <= v <= sb:
            c.line(fx0, ly_(py(v)), fx1, ly_(py(v)), QUIET, 3, "14 10")
    c.add(f'<clipPath id="lens"><rect x="{fx0:.2f}" y="{fy0:.2f}" width="{fx1 - fx0:.2f}" height="{fy1 - fy0:.2f}"/></clipPath><g clip-path="url(#lens)">')
    for k in order:
        for u in pile.get(k, [by[k]]):
            x, yy, r = spots[u["institution"]]
            if u["final"] is None or abs(u["gain"]) < 1e-9 or not fx0 - r < lx_(x) < fx1 + r:
                continue
            a, b = sorted((ly_(yy), ly_(py(u["kept_initial"]))))
            if b > fy0 and a < fy1:
                c.rect(lx_(x) - max(1.4, 0.1 * r) / 2, a, max(1.4, 0.1 * r), b - a, mix(colours.get(u["country"], NOBODY), 0.45))
    for k in order:
        if k in seats:
            disc(k, *seats[k])
    c.add("</g>")
    c.rect(fx0, fy0, fx1 - fx0, fy1 - fy0, "none", QUIET, 2)
    for placer in (main, zoomed):
        for k, (lx, ly, parts, seg, _) in placer.placed.items():
            left = lx + metrics(parts)[0] <= placer.spots[k][0]
            x, yy = lx, ly
            for part in parts:
                if part[0] == "break":
                    x, yy = lx + part[1], yy + part[2]
                    continue
                if part[0] == "flag":
                    x += c.flag(part[1], x, yy, part[2]) + part[2] * 0.28
                    continue
                _, t, z, wt, f, colour = part
                step = measure(t, z, f, wt)
                c.text(x + step if left else x, yy, t, z, wt, f, anchor="end" if left else "start", fill=colour, halo=round(0.2 * z))
                x += step
    for right, ly, text, _ in notes:
        c.text(right, ly, text, 30, 500, anchor="end", fill=GREY, halo=6)


def palette(c: Canvas, colours: dict, at: tuple, per: int = 17, pitch: float = 32) -> tuple:
    items = []
    for name in ORDER:
        members = [n["country"] for n in STATS["countries"] if continent(n["country"]) == name]
        if members:
            items.append(("head", name))
            items += [("item", code) for code in members]
    groups, column = [], []
    for i, (kind, value) in enumerate(items):
        follow = next((j for j in range(i + 1, len(items)) if items[j][0] == "head"), len(items)) - i - 1
        if len(column) == per or (kind == "head" and per - len(column) - 1 < min(2, follow)):
            groups.append(column)
            column = []
        column.append((kind, value))
    groups.append(column)
    wide = max(max(measure(country(v), SIZE, "cond", 500) + 30 + FLAG + 10 if k == "item" else measure(v, SIZE, "cond", 600) for k, v in g) for g in groups)
    gutter = 44
    size = (len(groups) * (wide + gutter) - gutter, (per - 1) * pitch + SIZE)
    if at is None:
        return size
    x0, y0 = at
    for i, g in enumerate(groups):
        x = x0 + i * (wide + gutter)
        for j, (kind, value) in enumerate(g):
            base = y0 + j * pitch + SIZE * CAP
            if kind == "head":
                c.text(x, base, value, SIZE, 600, "cond")
                continue
            c.circle(x + 10, base - SIZE * CAP / 2, 10, colours.get(value, NOBODY))
            c.flag(value, x + 30, base, SIZE)
            c.text(x + 30 + FLAG + 10, base, country(value), SIZE, 500, "cond")
    return size


def ribbon(a0: float, a1: float, ya: float, b0: float, b1: float, yb: float) -> str:
    m = (ya + yb) / 2
    return f"M{a0:.2f},{ya:.2f} C{a0:.2f},{m:.2f} {b0:.2f},{m:.2f} {b0:.2f},{yb:.2f} L{b1:.2f},{yb:.2f} C{b1:.2f},{m:.2f} {a1:.2f},{m:.2f} {a1:.2f},{ya:.2f} Z"


def scale(nodes: dict, gx) -> float:
    keys = sorted(nodes)
    return min((gx(b) - gx(a) - 3) * 2 / (nodes[a] + nodes[b]) for a, b in zip(keys, keys[1:]))


def papers(c: Canvas, box: tuple) -> None:
    x0, y0, x1, y1 = box
    base = heading(c, x0, x1, y0, "SUBMISSIONS", f"all {BASE:,} submissions")
    flows = STATS["flows"]
    exits = ["missing", "desk", "withdrawn"]
    starts, ends, gone = {}, {}, {}
    moves = {"raised": 0, "unchanged": 0, "lowered": 0}
    for f in flows:
        v = float(f["initial"])
        starts[v] = starts.get(v, 0) + f["papers"]
        key = f["outcome"] if f["outcome"] in exits else float(f["outcome"])
        ends[key] = ends.get(key, 0) + f["papers"]
        if f["outcome"] == "withdrawn":
            gone[v] = f["papers"]
        if f["outcome"] not in exits:
            d = float(f["outcome"]) - v
            moves["raised" if d > 1e-9 else "lowered" if d < -1e-9 else "unchanged"] += f["papers"]
    ax0, ax1 = x0 + 650, x1 - measure("4.00", 30) / 2
    lo, hi = 1.0, 4.0

    def gx(v: float) -> float:
        return ax0 + (v - lo) / (hi - lo) * (ax1 - ax0)

    s = min(scale(starts, gx), scale({k: v for k, v in ends.items() if k not in exits}, gx))
    strip0, strip1 = base + 83, base + 483
    yt = strip1 + 130
    yb = y1 - 120
    thick = 16

    def sy(share: float) -> float:
        return strip1 - share * (strip1 - strip0)

    for k in range(5):
        v = k / 4
        c.line(ax0, sy(v), ax1, sy(v), GRID, 2)
        c.text(ax0 - 22, sy(v) + 30 * CAP / 2, f"{round(100 * v)}%", 30, 400, anchor="end", fill=GREY)
    mean = ALL["withdrawn"]
    c.line(ax0, sy(mean), ax1, sy(mean), QUIET, 3, "14 10")
    marks, bodies = Grid(60), Grid(60)
    tag = f"All {percent(mean)}"
    tw = measure(tag, 30, "sans", 500)
    marks.add((ax0, sy(mean) - 9, ax1, sy(mean) + 9))

    def block(box: tuple, owner: object = None) -> None:
        marks.add(box, owner)
        bodies.add(box, owner)

    spots = {}
    for v in starts:
        share = gone.get(v, 0) / starts[v]
        spots[v] = (gx(v), sy(share), 0.3 * math.sqrt(starts[v]), share)
        x, y, r, _ = spots[v]
        block((x - max(r, 2) - 3, y - max(r, 2) - 3, x + max(r, 2) + 3, y + max(r, 2) + 3), v)
    for v in starts:
        x, y, r, _ = spots[v]
        block((x - 3, y, x + 3, sy(0) + 14), v)
    for k in range(5):
        t = f"{round(25 * k)}%"
        block((ax0 - 22 - measure(t, 30), sy(k / 4) - 24, ax0 - 16, sy(k / 4) + 6))
    ya = sy(1) + 30 * CAP / 2
    c.text(L, ya, "Withdrawn", 34, 600)
    c.text(L, ya + 52, "share by initial score", 30, 400, fill=GREY)
    c.text(L, ya + 112, "Dot area, submissions", 30, 500, fill=GREY)
    x = L
    for n in (100, 1000, 10000):
        r = 0.3 * math.sqrt(n)
        c.circle(x + r, ya + 182 - 30 * CAP / 2, r, GONE, "#ffffff", 1)
        c.text(x + 2 * r + 10, ya + 182, f"{n:,}", 30, 400, fill=GREY)
        x += 2 * r + 10 + measure(f"{n:,}", 30) + 24
    block((L, ya - 40, max(x, L + measure("Dot area, submissions", 30, "sans", 500)) + 20, ya + 210))
    ty = sy(mean) - 14
    block((ax1 - tw - 12, ty - 30 * CAP - 8, ax1 + 4, ty + 8))
    tags, links = [], []
    fs = 24
    floor = yt - 30 - 30 * CAP - 16
    for v in sorted(starts, key=lambda v: -starts[v]):
        x, y, r, share = spots[v]
        rr = max(r, 2)
        t = percent(share)
        w = measure(t, fs)
        best = None
        sides = ("up", "right", "left", "down") if share == 0 else ("right", "up", "left", "down")
        for d in (0, 14, 30, 50, 74):
            for side in sides:
                if side == "up":
                    lx, ly = x - w / 2, y - rr - 8 - d
                    a, b, end = x, y - rr, (x, y - rr - 8 - d + 2)
                elif side == "down":
                    lx, ly = x - w / 2, y + rr + 8 + d + fs * CAP
                    a, b, end = x, y + rr, (x, y + rr + 8 + d - 2)
                elif side == "right":
                    lx, ly = x + rr + 8 + d, y + fs * CAP / 2
                    a, b, end = x + rr, y, (x + rr + 8 + d - 4, y)
                else:
                    lx, ly = x - rr - 8 - d - w, y + fs * CAP / 2
                    a, b, end = x - rr, y, (x - rr - 8 - d + 4, y)
                boxed = (lx - 6, ly - fs * CAP - 6, lx + w + 6, ly + 6)
                if boxed[0] < L or boxed[2] > ax1 + 4 or boxed[1] < strip0 - 40 or boxed[3] > floor:
                    continue
                if marks.hit(boxed, v):
                    continue
                seg = (min(a, end[0]) - 1, min(b, end[1]) - 1, max(a, end[0]) + 1, max(b, end[1]) + 1)
                if d > 0 and bodies.hit(seg, v):
                    continue
                best = (lx, ly, boxed, d, (a, b, *end))
                break
            if best:
                break
        if not best:
            raise RuntimeError(f"no room for the withdrawn share at {v}")
        lx, ly, boxed, d, link = best
        block(boxed)
        if d > 0:
            links.append(link)
            block((min(link[0], link[2]) - 1, min(link[1], link[3]) - 1, max(link[0], link[2]) + 1, max(link[1], link[3]) + 1))
        tags.append((lx, ly, t))
    for v in starts:
        x, y, r, _ = spots[v]
        c.line(x, sy(0) + 12, x, y, NODE, 2)
    for a, b, p, q in links:
        c.line(a, b, p, q, QUIET, 1.5)
    for v in sorted(starts, key=lambda v: -starts[v]):
        x, y, r, _ = spots[v]
        c.circle(x, y, r, GONE, "#ffffff", 1 if r > 4 else 0.4)
    for lx, ly, t in tags:
        c.text(lx, ly, t, fs, 400, fill=SOFT, halo=5)
    c.text(ax1, ty, tag, 30, 500, anchor="end", fill=GREY, halo=6)
    ticks = [1 + k / 3 for k in range(10)]
    for v in ticks:
        c.text(gx(v), yt - 30, score(v), 30, 400, anchor="middle", fill=GREY)
        c.text(gx(v), yb + thick + 46, score(v), 30, 400, anchor="middle", fill=GREY)
    top = {v: gx(v) - s * n / 2 for v, n in starts.items()}
    widths = {k: measure(name, 30, "sans", 500) for k, name in (("missing", "Missing"), ("desk", "Desk rejected"), ("withdrawn", "Withdrawn"))}
    spare = (ax0 - 170 + widths["withdrawn"] / 2 - L - sum(widths.values())) / 2
    slots = {"missing": L + widths["missing"] / 2, "desk": L + widths["missing"] + spare + widths["desk"] / 2, "withdrawn": ax0 - 170}

    def place(k) -> float:
        return slots[k] if k in exits else gx(k)

    bot = {k: place(k) - s * n / 2 for k, n in ends.items()}
    shapes = []
    cursor = dict(top)
    for f in sorted(flows, key=lambda f: (float(f["initial"]), place(f["outcome"] if f["outcome"] in exits else float(f["outcome"])))):
        v = float(f["initial"])
        k = f["outcome"] if f["outcome"] in exits else float(f["outcome"])
        shapes.append([f["papers"], v, k, cursor[v], cursor[v] + s * f["papers"]])
        cursor[v] += s * f["papers"]
    cursor = dict(bot)
    for item in sorted(shapes, key=lambda it: (place(it[2]), it[1])):
        item += [cursor[item[2]], cursor[item[2]] + s * item[0]]
        cursor[item[2]] += s * item[0]
    for n, v, k, a0, a1, b0, b1 in sorted(shapes, key=lambda it: (it[2] in exits, it[2] not in exits and abs(it[2] - it[1]) > 1e-6, -it[0])):
        colour = GONE if k == "withdrawn" else NODE if k in exits else way(k - v)
        if colour:
            c.shape(ribbon(a0, a1, yt + thick, b0, b1, yb), colour)
        else:
            c.shape(ribbon(a0, a1, yt + thick, b0, b1, yb), "none", QUIET, 1.5)
    for v, n in starts.items():
        before = s * sum(f["papers"] for f in flows if float(f["initial"]) == v and f["outcome"] in ("missing", "desk"))
        c.rect(top[v], yt, s * n, thick, NODE)
        c.rect(top[v] + before, yt, s * gone.get(v, 0), thick, GONE)
    for k, n in ends.items():
        c.rect(bot[k], yb, s * n, thick, GONE if k == "withdrawn" else NODE)
    for k, name in (("withdrawn", "Withdrawn"), ("desk", "Desk rejected"), ("missing", "Missing")):
        c.text(slots[k], yb + thick + 46, name, 30, 500, anchor="middle")
        c.text(slots[k], yb + thick + 88, f"{ends[k]:,}", 30, 400, anchor="middle", fill=GREY)
    c.text(L, yt - 30, "Nov 6", 34, 600)
    c.text(L, yt + 22, "initial score", 30, 400, fill=GREY)
    c.text(L, yt + 62, f"median {OVERALL['median_initial']:.2f}, mean {OVERALL['mean_initial']:.2f}", 30, 400, fill=GREY)
    late = [f"final score of the {OPEN:,} open", f"{moves['raised']:,} raised", f"{moves['unchanged']:,} unchanged", f"{moves['lowered']:,} lowered", f"median {OVERALL['median_final']:.2f}, mean {OVERALL['mean_final']:.2f}"]
    for k, t in enumerate(reversed(late)):
        c.text(L, yb - 30 - 40 * k, t, 30, 400, fill=GREY, halo=6)
    c.text(L, yb - 30 - 40 * (len(late) - 1) - 52, "Nov 19", 34, 600, halo=6)


def matrix(c: Canvas, box: tuple) -> None:
    x0, y0, x1, y1 = box
    heading(c, x0, x1, y0, "REVIEWS", f"all {OVERALL['reviews_compared']:,} reviews on both dates: {OVERALL['reviews_raised']:,} raised, {OVERALL['reviews_lowered']:,} lowered")
    l1, l2, rule = lines(y0)
    end = y1 - 3
    trans = {(t["before"], t["after"]): t["reviews"] for t in STATS["transitions"]}
    added = {int(k): v for k, v in STATS["added"].items()}
    gone = {int(k): v for k, v in STATS["removed"].items()}
    replied = STATS["replied"]
    raised = STATS["raised"]
    fs = 28
    first = x0 + max(measure(t, fs, "sans", 600) for t in ("Added", "Total")) + 40
    counts = [1, 2, 3, 4, "removed", "total"]
    shares = ["replied", "yes", "no"]
    names = ["1", "2", "3", "4", "Removed", "Total", "Replied", "If replied", "If silent"]
    sw = max(max(measure(n, HEAD) for n in names[6:]), measure("47.4%", fs)) + 44
    rows = [1, 2, 3, 4, "added", "total"]
    rh = (end - rule - 4) / len(rows)

    def value(r, k):
        if k in ("yes", "no"):
            key = f"{'all' if r == 'total' else r}:{1 if k == 'yes' else 0}"
            return raised.get(key) if r != "added" else None
        if k == "replied":
            return OVERALL["reviews_replied"] if r == "total" else replied.get(str(r))
        if r == "total" and k == "total":
            return None
        if r == "total":
            return sum(trans.get((b, k), 0) for b in range(1, 5)) + added.get(k, 0) if k != "removed" else sum(gone.values())
        if k == "total":
            return sum(trans.get((r, a), 0) for a in range(1, 5)) + gone.get(r, 0) if r != "added" else sum(added.values())
        if r == "added":
            return None if k == "removed" else added.get(k, 0)
        if k == "removed":
            return gone.get(r, 0)
        return trans.get((r, k), 0)

    wide = {k: max(measure(f"{value(r, k):,}", fs, "sans", 600) for r in rows if value(r, k) is not None) for k in counts}
    tight = {k: max(wide[k] + 28, measure(name, HEAD)) + 30 for k, name in (("removed", "Removed"), ("total", "Total"))}
    cw = (x1 - first - len(shares) * sw - sum(tight.values())) / 4
    edges = [first]
    for w in [cw] * 4 + [tight["removed"], tight["total"]] + [sw] * len(shares):
        edges.append(edges[-1] + w)
    span(c, edges[0] + 8, edges[4] - 8, l1, "Rating on Nov 19, square area by share of the row")
    span(c, edges[7] + 8, edges[9] - 4, l1, "Raised")
    c.text(x0, l2, "Nov 6", HEAD, 400, fill=GREY)
    for j, name in enumerate(names):
        c.text(edges[j + 1] - 14, l2, name, HEAD, 400, anchor="end", fill=GREY)
    c.line(x0, rule, x1, rule, INK, 3)
    room = min(rh - 28, min(cw - wide[k] - 54 for k in counts[:4]))
    for i, r in enumerate(rows):
        top = rule + 4 + i * rh
        cy = top + rh / 2
        base = cy + fs * CAP / 2
        if i:
            c.line(x0, top, x1, top, RULE, 2)
        c.text(x0, base, {"added": "Added", "total": "Total"}.get(r, str(r)), fs, 600)
        whole = sum(value(r, k) or 0 for k in counts if k != "total")
        for j, k in enumerate(counts + shares):
            n = value(r, k)
            if n is None:
                continue
            edge = edges[j + 1] - 14
            if k in (1, 2, 3, 4) and n:
                side = room * math.sqrt(n / whole)
                sx = edge - wide[k] - 20
                tint = way(k - r) if isinstance(r, int) and isinstance(k, int) else NODE
                if tint:
                    c.rect(sx - side, cy - side / 2, side, side, tint)
                else:
                    c.rect(sx - side + 1, cy - side / 2 + 1, side - 2, side - 2, "none", QUIET, 2)
            c.text(edge, base, percent(n) if k in shares else f"{n:,}", fs, 600 if r == "total" or k == "total" else 400, anchor="end")
    c.line(x0, end + 1.5, x1, end + 1.5, INK, 3)


def daily(c: Canvas, box: tuple) -> None:
    x0, y0, x1, y1 = box
    days = STATS["daily"]
    heading(c, x0, x1, y0, "COMMENTS", f"per AoE day, all {BASE:,} submissions")
    l1, l2, rule = lines(y0)
    end = y1 - 3
    rh = (end - rule - 4) / (len(days) + 1)
    roles = [("authors", "Authors", SOFT), ("reviewer", "Reviewers", QUIET), ("chair", "Area chairs", RULE)]
    totals = {k: sum(d[k] for d in days) for k, _, _ in roles}
    hi = 10000 * math.ceil(max(sum(d[k] for k, _, _ in roles) for d in days) / 10000)
    day = max(measure("Nov 18, deadline", SIZE, "cond", 500), measure("Day", HEAD))
    widths = {k: max(measure(f"{totals[k]:,}", SIZE, "sans", 600), measure(name, HEAD) + 20) for k, name, _ in roles}
    gap = 40
    g0 = x0 + day + sum(widths.values()) + 3 * gap + 60
    step = 10000 if (x1 - g0) * 10000 / hi >= 90 else 20000
    ticks = list(range(0, hi + 1, step))
    while ticks and g0 + (x1 - g0) * ticks[-1] / hi + measure(f"{ticks[-1]:,}", TICK) / 2 > x1:
        ticks.pop()
    g1 = x1
    nums = {}
    x = x0 + day
    for k, _, _ in roles:
        x += gap + widths[k]
        nums[k] = x
    c.text(x0, l2, "Day", HEAD, 400, fill=GREY)
    for k, name, colour in roles:
        c.text(nums[k], l2, name, HEAD, 400, anchor="end", fill=GREY)
        c.rect(nums[k] - measure(name, HEAD) - 22, l2 - HEAD * CAP / 2 - 8, 16, 16, colour)
    for v in ticks:
        c.text(g0 + (g1 - g0) * v / hi, l2, f"{v:,}", TICK, 400, anchor="start" if v == 0 else "middle", fill=GREY)
    c.line(x0, rule, x1, rule, INK, 3)
    for v in ticks[1:]:
        c.line(g0 + (g1 - g0) * v / hi, rule + 4, g0 + (g1 - g0) * v / hi, rule + 4 + len(days) * rh, GRID, 2)
    for i, d in enumerate(days):
        cy = rule + 4 + (i + 0.5) * rh
        base = cy + SIZE * CAP / 2
        c.text(x0, base, f"Nov {int(d['day'][-2:])}" + (", deadline" if d["day"] == "2026-11-18" else ""), SIZE, 500, "cond")
        x = g0
        for k, _, colour in roles:
            c.text(nums[k], base, f"{d[k]:,}", SIZE, 400, anchor="end")
            w = (g1 - g0) * d[k] / hi
            c.rect(x, cy - 13, w, 26, colour)
            x += w
    total = rule + 4 + len(days) * rh
    c.line(x0, total, x1, total, RULE, 2)
    base = total + rh / 2 + SIZE * CAP / 2
    c.text(x0, base, "Total", SIZE, 600, "cond")
    for k, _, _ in roles:
        c.text(nums[k], base, f"{totals[k]:,}", SIZE, 600, anchor="end")
    c.line(x0, end + 1.5, x1, end + 1.5, INK, 3)


def columns(x0: float, x1: float, flags: bool) -> dict:
    cols = {"rank": x0 + 60, "flag": x0 + 74}
    cols["name"] = x0 + 74 + (FLAG + 12 if flags else 0)
    cols["glyph"] = (x1 - GLYPH, x1)
    cols["change"] = x1 - GLYPH - OFFSETS[0]
    cols["final"] = cols["change"] - OFFSETS[1]
    cols["reb"] = cols["final"] - OFFSETS[2]
    cols["bar"] = (cols["reb"] - OFFSETS[3] - OFFSETS[4], cols["reb"] - OFFSETS[3])
    cols["share"] = cols["bar"][0] - OFFSETS[5]
    cols["subs"] = cols["share"] - OFFSETS[6]
    return cols


def width(names: list, amounts: list, flags: bool, head: str) -> float:
    need = max(max(measure(n, SIZE, "cond", 500) for n in names) + 30 + max(measure(a, SIZE, "sans", 600) for a in amounts), measure(head, HEAD) + 40 + measure("Submissions", HEAD))
    return math.ceil(74 + (FLAG + 12 if flags else 0) + need + sum(OFFSETS) + GLYPH)


def ledger(c: Canvas, title: str, note: str, head_label: str, rows: list, y: float, rh: float, flags: bool, colour, name, amount, base: dict, cols: dict, axis: tuple, total: dict = None) -> float:
    x0, x1 = cols["rank"] - 60, cols["glyph"][1]
    heading(c, x0, x1, y, title, note)
    l1, l2, rule = lines(y)
    b0, b1 = cols["bar"]
    g0, g1 = cols["glyph"]
    lo, hi = axis
    g1 -= measure(score(hi), TICK) / 2
    span(c, cols["share"] - 70, b1, l1, "Withdrawn")
    span(c, cols["final"] - 56, x1, l1, "Score")
    c.text(cols["rank"], l2, "Rank", HEAD, 400, anchor="end", fill=GREY)
    c.text(cols["name"], l2, head_label, HEAD, 400, fill=GREY)
    c.text(cols["subs"], l2, "Submissions", HEAD, 400, anchor="end", fill=GREY)
    c.text(cols["share"], l2, "Share", HEAD, 400, anchor="end", fill=GREY)
    for v in (0, 0.5, 1):
        c.text(b0 + v * (b1 - b0), l2, f"{round(100 * v)}%", TICK, 400, anchor="start" if v == 0 else "end" if v == 1 else "middle", fill=GREY)
    c.text(cols["reb"], l2, "Rebuttal", HEAD, 400, anchor="end", fill=GREY)
    c.text(cols["final"], l2, "Final", HEAD, 400, anchor="end", fill=GREY)
    c.text(cols["change"], l2, "Change", HEAD, 400, anchor="end", fill=GREY)

    def gx(m: float) -> float:
        return g0 + (m - lo) / (hi - lo) * (g1 - g0)

    step = 0.2 if (g1 - g0) * 0.2 / (hi - lo) >= 56 else 0.4
    v = math.ceil(lo / step - 1e-9) * step
    while v <= hi + 1e-9:
        c.text(gx(v), l2, score(v), TICK, 400, anchor="middle", fill=GREY)
        v += step
    c.line(x0, rule, x1, rule, INK, 3)
    every = rows + ([total] if total else [])
    for k, n in enumerate(every):
        cy = rule + 4 + (k + 0.5) * rh
        base_y = cy + SIZE * CAP / 2
        number = k + 1
        last = n is total
        if last:
            c.line(x0, rule + 4 + k * rh, x1, rule + 4 + k * rh, RULE, 2)
        elif number & (number - 1) == 0 and number < len(rows):
            c.line(x0, rule + 4 + (k + 1) * rh, x1, rule + 4 + (k + 1) * rh, RULE, 2)
        tint = SOFT if last else colour(n)
        weight = 600 if last else 400
        if not last:
            c.text(cols["rank"], base_y, str(number), SIZE, 400, anchor="end", fill=QUIET)
            if flags:
                c.flag(n["country"], cols["flag"], base_y, SIZE)
        c.text(cols["name"], base_y, "All" if last else name(n), SIZE, 600 if last else 500, "cond")
        c.text(cols["subs"], base_y, amount(n), SIZE, weight, anchor="end")
        c.text(cols["share"], base_y, percent(n["withdrawn"]), SIZE, weight, anchor="end")
        c.rect(b0, cy - SIZE * 0.36, b1 - b0, SIZE * 0.72, GRID)
        c.rect(b0, cy - SIZE * 0.36, (b1 - b0) * n["withdrawn"], SIZE * 0.72, GONE)
        c.text(cols["reb"], base_y, percent(n["rebuttal"]), SIZE, weight, anchor="end", fill=INK if last else SOFT)
        if n["final"] is not None:
            c.text(cols["final"], base_y, score(n["final"]), SIZE, 600, anchor="end")
            cw = cols["change"] - cols["final"] - 14
            if klass(n["gain"]):
                c.rect(cols["change"] - cw + 7, cy - min(rh, 40) / 2 + 3, cw, min(rh, 40) - 6, klass(n["gain"]))
            c.text(cols["change"], base_y, signed(n["gain"]), SIZE, weight, anchor="end")
            a, b = n["kept_initial"], n["final"]
            stem(c, gx(min(max(b, lo), hi)), cy, gx(min(max(a, lo), hi)), tint, SIZE * 0.3 if lo <= b <= hi else 0)
            for side in {(v > hi) - (v < lo) for v in (a, b)} - {0}:
                arrow(c, gx(hi if side > 0 else lo), cy, side, tint)
        else:
            c.text(cols["final"], base_y, "–", SIZE, 400, anchor="end", fill=QUIET)
            c.text(cols["change"], base_y, "–", SIZE, 400, anchor="end", fill=QUIET)
            v = n["initial"]
            if lo <= v <= hi:
                c.circle(gx(v), cy, SIZE * 0.3, GONE, "#ffffff", 1.2)
            else:
                arrow(c, gx(hi if v > hi else lo), cy, 1 if v > hi else -1, GONE)
    end = rule + 4 + len(every) * rh
    c.line(b0 + (b1 - b0) * base["withdrawn"], rule, b0 + (b1 - b0) * base["withdrawn"], end, QUIET, 2, "6 6")
    c.line(gx(base["final"]), rule, gx(base["final"]), end, QUIET, 2, "6 6")
    c.line(x0, end + 1.5, x1, end + 1.5, INK, 3)
    return end + 3


def build(hidden: set) -> Canvas:
    c = Canvas(hidden)
    colours = painter([n["country"] for n in STATS["countries"]])
    end = masthead(c)
    nations = list(STATS["countries"])
    continents = list(STATS["continents"])
    kinds = list(STATS["kinds"])
    areas = STATS["areas"]
    rows = sorted([u for u in STATS["institutions"] if u["weight"] >= RANKED], key=lambda u: -u["final"])
    every = rows + nations + continents + kinds + areas
    lo = math.floor(min(min(n["kept_initial"], n["final"]) for n in every if n["final"] is not None and n["weight"] >= 1) * 10 + 1e-9) / 10
    hi = math.ceil(max(max(n["kept_initial"], n["final"]) for n in every if n["final"] is not None and n["weight"] >= 1) * 10 - 1e-9) / 10
    axis = (lo, hi)
    rh = (BOTTOM - TOP - 3 * (BLOCK + 3) - 2 * GAP) / (len(rows) + len(nations) + len(areas) + 1)
    cols = columns(COLUMN, R, True)
    paint = {k["kind"]: KINDS[i % len(KINDS)] for i, k in enumerate(kinds)}
    y = TOP
    for title, note, head_label, items, colour, name in (
        ("INSTITUTIONS BY FINAL SCORE", f"{RANKED} or more submissions, {USED:,} matched submissions", "Institution", rows, lambda n: colours.get(n["country"], NOBODY), lambda n: display(n)[1]),
        ("COUNTRIES BY SUBMISSIONS", f"{USED:,} matched submissions", "Country", nations, lambda n: colours.get(n["country"], NOBODY), lambda n: country(n["country"])),
    ):
        y = ledger(c, title, note, head_label, items, y, rh, True, colour, name, lambda n: fixed(n["weight"]), MATCHED, cols, axis) + GAP
    low = BOTTOM - (BLOCK + 3 + (len(areas) + 1) * rh)
    matrix(c, (COLUMN, low, R, BOTTOM))
    aw = width([area(a) for a in areas], [f"{BASE:,}"], False, "Area")
    ax0 = SPLIT - aw
    ledger(c, "PRIMARY AREAS", f"all {BASE:,} submissions", "Area", areas, low, rh, False, lambda n: SOFT, area, lambda n: f"{n['papers']:,}", ALL, columns(ax0, SPLIT, False), axis, ALL)
    daily(c, (L, low, ax0 - PANEL, BOTTOM))
    flow_top = low - GAP - 1163
    papers(c, (L, flow_top, SPLIT, low - GAP + 11))
    iw = width([n["continent"] for n in continents] + [k["kind"].capitalize() for k in kinds], [fixed(USED)], False, "Continent")
    ch = BLOCK + 3 + (len(continents) + 1) * rh
    th = BLOCK + 3 + len(kinds) * rh
    upper = [
        (iw, ch, lambda a, b: ledger(c, "CONTINENTS", f"{USED:,} matched submissions", "Continent", continents, b, rh, False, lambda n: tone(n["continent"]), lambda n: n["continent"], lambda n: fixed(n["weight"]), MATCHED, columns(a, SPLIT, False), axis, MATCHED)),
        (iw, th, lambda a, b: ledger(c, "INSTITUTION TYPES", f"{USED:,} matched submissions", "Type", kinds, b, rh, False, lambda n: paint[n["kind"]], lambda n: n["kind"].capitalize(), lambda n: fixed(n["weight"]), MATCHED, columns(a, SPLIT, False), axis)),
    ]
    gx0 = L + 32 + measure("3.40", 34)
    kw, kh = palette(c, colours, None)
    hero(c, colours, {u["institution"]: k + 1 for k, u in enumerate(rows)}, (gx0, end + GAP + 192, SPLIT - measure("512", 34) / 2, flow_top - GAP - 118), end + GAP, upper, (kw, kh, lambda a, b: palette(c, colours, (a, b))))
    return c


def shoot(svg: pathlib.Path, folder: pathlib.Path, bands: list) -> list:
    step = H // BANDS
    jobs = []
    for k in bands:
        page = folder / f"{svg.stem}-{k}.html"
        page.write_text(f'<!doctype html><html><head><style>html,body{{margin:0;overflow:hidden;background:#fff}}img{{position:absolute;left:0;top:{-k * step}px;width:{W}px;height:{H}px}}</style></head><body><img src="{svg.resolve().as_uri()}"></body></html>')
        shot = folder / f"{svg.stem}-{k}.png"
        jobs.append((k, shot, subprocess.Popen(["chromium", "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", f"--window-size={W},{step}", "--run-all-compositor-stages-before-draw", "--virtual-time-budget=600000", f"--screenshot={shot}", page.resolve().as_uri()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    for _, _, job in jobs:
        job.wait()
    return [(k, shot) for k, shot, _ in jobs]


def missing(image: Image.Image) -> set:
    step = H // BANDS
    gray = image.convert("L")
    out = set()
    for y in range(TOP, BOTTOM, 256):
        for a, b in ((L, SPLIT), (COLUMN, R)):
            if gray.crop((a, y, b, min(y + 256, BOTTOM))).getextrema()[0] >= 250:
                out.add(y // step)
    if max(gray.getpixel((x, BOTTOM - 2)) for x in (L + 10, SPLIT - 10, COLUMN + 10, R - 10)) >= 80:
        out.add((BOTTOM - 2) // step)
    return out


def render(pairs: list) -> None:
    step = H // BANDS
    folder = HERE / ".render"
    folder.mkdir(exist_ok=True)
    images = {svg: Image.new("RGB", (W, H), "white") for svg, _ in pairs}
    todo = {svg: set(range(BANDS)) for svg, _ in pairs}
    for _ in range(8):
        for svg, shots in [(svg, shoot(svg, folder, sorted(todo[svg]))) for svg, _ in pairs if todo[svg]]:
            for k, shot in shots:
                images[svg].paste(Image.open(shot).convert("RGB").crop((0, 0, W, step)), (0, k * step))
        for svg, _ in pairs:
            todo[svg] = missing(images[svg]) if todo[svg] else set()
        if not any(todo.values()):
            break
    for path in folder.iterdir():
        path.unlink()
    folder.rmdir()
    for svg, png in pairs:
        if todo[svg]:
            raise RuntimeError(f"incomplete render of {svg.name}")
        temp = png.with_name(png.stem + "-temp.png")
        images[svg].save(temp)
        temp.replace(png)


def main() -> None:
    variant = HERE / f"{NAME}-nohmt"
    build(set()).save(HERE / f"{NAME}.svg")
    build(HIDDEN).save(variant.with_suffix(".svg"))
    full = variant.with_name(variant.name + "-full.png")
    render([(HERE / f"{NAME}.svg", HERE / f"{NAME}.png"), (variant.with_suffix(".svg"), full)])
    small = variant.with_name(variant.name + "-4mb.png")
    for colours in (256, 192, 128):
        Image.open(full).convert("RGB").quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(small, optimize=True)
        if small.stat().st_size < 4_000_000:
            break
    full.unlink()


if __name__ == "__main__":
    main()

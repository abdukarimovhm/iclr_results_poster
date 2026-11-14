import base64
import json
import math
import pathlib
import subprocess

from PIL import Image, ImageFont

HERE = pathlib.Path(__file__).parent
STATS = json.loads((HERE / "stats.json").read_text())
COUNTRIES = json.loads((HERE / "countries.json").read_text())
NAME = "iclr2027-institutions"
URL = "https://github.com/clareLab/posters"
HIDDEN = {"HK", "MO", "TW"}

W, H = 7200, 9600
L, R = 260, 6940
SPLIT, COLUMN = 4800, 5000
TOP, BOTTOM = 300, H - 260
CAP = 0.7
GAP = 150
INK = "#111111"
GREY = "#5b616b"
QUIET = "#8a919c"
SOFT = "#41464e"
RULE = "#c9ced6"
GRID = "#e7eaee"
LINK = "#1a4f8b"
FRAME = "#a9afb8"
TILE = "#e9ecf0"
NOBODY = "#b9bec6"
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
MEAN = OVERALL["mean_used"]
SD = OVERALL["sd_used"]
USED = OVERALL["used"]
MEDIAN = OVERALL["median"]
RANKED = 16
BOUNDS = [-0.16, -0.08, -0.04, 0.0, 0.04, 0.08, 0.16]


def measure(text: str, size: float, family: str = "sans", weight: int = 400) -> float:
    if (family, weight) not in LOADED:
        LOADED[family, weight] = ImageFont.truetype(str(HERE / "fonts" / FILES[family, weight]), 1000)
    return LOADED[family, weight].getlength(text) * size / 1000


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


STEPS = [(0.935, 0.03), (0.875, 0.06), (0.8, 0.095), (0.72, 0.13)]
CLASSES = [oklch(l, c, 32) for l, c in reversed(STEPS)] + [oklch(l, c, 252) for l, c in STEPS]
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


def klass(mean: float) -> str:
    return CLASSES[sum(mean - MEAN > b for b in BOUNDS)]


def fixed(value: float) -> str:
    return f"{value:,.2f}"


def share(value: float) -> str:
    return f"{100 * value:.2f}%"


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


class Canvas:
    def __init__(self) -> None:
        self.items = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']
        self.flags = {}
        self.hidden = set()

    def add(self, item: str) -> None:
        self.items.append(item)

    def rect(self, x: float, y: float, w: float, h: float, fill: str, stroke: str = "", width: float = 0) -> None:
        line = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" fill="{fill}"{line}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = INK, width: float = 2, dash: str = "") -> None:
        pattern = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{pattern}/>')

    def path(self, points: list, stroke: str, width: float, dash: str = "") -> None:
        pattern = f' stroke-dasharray="{dash}"' if dash else ""
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)
        self.add(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}"{pattern}/>')

    def circle(self, x: float, y: float, r: float, fill: str, stroke: str = "", width: float = 0, opacity: float = 1) -> None:
        line = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        alpha = f' fill-opacity="{opacity}"' if opacity < 1 else ""
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"{alpha}{line}/>')

    def text(self, x: float, y: float, s: str, size: float, weight: int = 400, family: str = "sans", anchor: str = "start", fill: str = INK, spacing: float = 0) -> None:
        track = f' letter-spacing="{spacing:.1f}"' if spacing else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FALLBACK[family]}" font-size="{size:.1f}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{track}>{escape(s)}</text>')

    def runs(self, x: float, y: float, parts: list, anchor: str = "start") -> None:
        spans = "".join(f'<tspan font-family="{FALLBACK[f]}" font-size="{s:.1f}" font-weight="{w}" fill="{c}">{escape(t)}</tspan>' for t, s, w, f, c in parts)
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{spans}</text>')

    def flag(self, code: str, x: float, baseline: float, size: float) -> float:
        if code in self.hidden:
            return 0
        h = size * 0.72
        w = h * 4 / 3
        source = HERE / "flags" / f"{code.lower()}.svg"
        if source.exists():
            if code not in self.flags:
                self.flags[code] = base64.b64encode(source.read_bytes()).decode()
            top = baseline - size * CAP / 2 - h / 2
            self.add(f'<image x="{x:.1f}" y="{top:.1f}" width="{w:.1f}" height="{h:.1f}" preserveAspectRatio="none" href="data:image/svg+xml;base64,{self.flags[code]}"/>')
            self.rect(x, top, w, h, "none", FRAME, 1)
        return w

    def save(self, path: pathlib.Path) -> None:
        faces = "".join(
            f"@font-face{{font-family:'{FAMILY[family]}';font-weight:{weight};font-style:normal;src:url(data:font/otf;base64,{base64.b64encode((HERE / 'fonts' / file).read_bytes()).decode()}) format('opentype');}}"
            for (family, weight), file in FILES.items()
        )
        head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs><style>{faces}</style></defs>'
        path.write_text(head + "".join(self.items) + "</svg>")


def squarify(values: list, x: float, y: float, w: float, h: float) -> list:
    out: list = [None] * len(values)
    total = sum(values)
    if total <= 0 or w <= 0 or h <= 0:
        return [(x, y, 0, 0)] * len(values)
    scale = w * h / total
    items = [(i, values[i] * scale) for i in sorted(range(len(values)), key=lambda i: -values[i]) if values[i] > 0]

    def worst(row: list, side: float) -> float:
        s = sum(a for _, a in row)
        return max(max(side * side * a / (s * s), s * s / (side * side * a)) for _, a in row)

    while items:
        side = min(w, h)
        row = [items.pop(0)]
        while items and worst(row + [items[0]], side) <= worst(row, side):
            row.append(items.pop(0))
        s = sum(a for _, a in row)
        if w >= h:
            col, cy = s / h, y
            for i, a in row:
                out[i] = (x, cy, col, a / col)
                cy += a / col
            x, w = x + col, w - col
        else:
            band, cx = s / w, x
            for i, a in row:
                out[i] = (cx, y, a / band, band)
                cx += a / band
            y, h = y + band, h - band
    return [o if o else (x, y, 0, 0) for o in out]


def wrap(text: str, size: float, width: float, family: str, weight: int, lines: int) -> list:
    words, out = text.split(), []
    while words and len(out) < lines:
        line = words.pop(0)
        while words and measure(line + " " + words[0], size, family, weight) <= width:
            line += " " + words.pop(0)
        out.append(line)
    if words or any(measure(t, size, family, weight) > width for t in out):
        return []
    return out


def radius(weight: float) -> float:
    return 5.2 * math.sqrt(weight)


def masthead(c: Canvas) -> float:
    title = "ICLR 2027 Review Scores"
    size = min(330, (SPLIT - L) * 1000 / measure(title, 1000, "sans", 700))
    base = TOP + size * CAP
    c.text(L - size * 0.035, base, title, size, 700)
    base += 175
    c.text(L, base, "by Country and Institution", 120, 400, fill=GREY)
    base += 125
    c.text(L, base, URL, 58, 400, fill=LINK)
    base += 115
    used, under = OVERALL["used"], OVERALL["under_review"]
    c.text(L, base, f"Initial ratings of {used:,} of {under:,} submissions ({100 * used / under:.1f}%) posted on arXiv before the reviews", 46, 400)
    base += 64
    c.text(L, base, f"{OVERALL['institutions']:,} institutions in {OVERALL['countries']} countries, mean score {MEAN:.2f} against {OVERALL['mean_rest']:.2f} for the other submissions", 46, 400)
    base += 100
    meta = [("Author", "clareLab", INK), ("Contact", "https://clarelab.moe", LINK), ("Date", "Nov 14, 2026", INK), ("Reviews", "OpenReview, Nov 6, 2026", INK), ("Affiliations", "OpenAlex, Nov 14, 2026", INK)]
    for i, (k, v, colour) in enumerate(meta):
        c.text(L, base + i * 54, k, 40, 400, fill=GREY)
        c.text(L + 250, base + i * 54, v, 40, 400, fill=colour)
    base += len(meta) * 54 + 70
    x = L
    c.text(x, base, "Dot area = Submissions", 42, 500)
    x += measure("Dot area = Submissions", 42, "sans", 500) + 48
    for value in (8, 32, 128):
        r = radius(value)
        c.circle(x + r, base - 42 * CAP / 2, r, NOBODY)
        c.text(x + 2 * r + 14, base, str(value), 42, 400)
        x += 2 * r + 14 + measure(str(value), 42) + 44
    base += 84
    x = L
    c.text(x, base, "Dot colour = country, by continent", 42, 500)
    x += measure("Dot colour = country, by continent", 42, "sans", 500) + 48
    for name in ORDER:
        c.circle(x + 15, base - 42 * CAP / 2, 15, tone(name))
        c.text(x + 42, base, name, 42, 400)
        x += 42 + measure(name, 42) + 44
    base += 76
    c.text(L, base, "Submissions = fractional count over affiliated authors and their institutions", 40, 400, fill=SOFT)
    base += 60
    x = L
    for item in ("Score = mean initial rating", f"Above median = share rated above {MEDIAN:.2f}, the median of all submissions", "Funnel = 95% range for a unit of that size"):
        c.text(x, base, item, 40, 400, fill=SOFT)
        x += measure(item, 40) + 80
    return base


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


def octave(w: float) -> str:
    return f"{w:g}" if w >= 1 else f"1/{round(1 / w)}"


def funnel(c: Canvas, colours: dict, ranks: dict, box: tuple) -> None:
    x0, y0, x1, y1 = box
    units = sorted([u for u in STATS["institutions"] if u["weight"] >= 1], key=lambda u: -u["weight"])
    lo = 1
    hi = 2 ** math.ceil(math.log2(max(u["weight"] for u in units)))
    bottom = math.floor(min(u["mean"] for u in units) * 5) / 5
    top = math.ceil(max(u["mean"] for u in units) * 5) / 5

    def px(w: float) -> float:
        return x0 + (math.log2(w) - math.log2(lo)) / (math.log2(hi) - math.log2(lo)) * (x1 - x0)

    def py(m: float) -> float:
        return y1 - (m - bottom) / (top - bottom) * (y1 - y0)

    for k in range(int(round((top - bottom) * 5)) + 1):
        value = bottom + k / 5
        c.line(x0, py(value), x1, py(value), GRID, 2)
        c.text(x0 - 20, py(value) + 34 * CAP / 2, f"{value:.1f}", 34, 400, anchor="end", fill=GREY)
    w = lo
    while w <= hi:
        c.line(px(w), y0, px(w), y1, GRID, 2)
        c.text(px(w), y1 + 52, octave(w), 34, 400, anchor="middle", fill=GREY)
        w *= 2
    c.text(x1, y1 + 112, "Submissions", 40, 500, anchor="end")
    c.text(L, y0 - 44, "Score", 40, 500)
    steps = [lo * (hi / lo) ** (k / 400) for k in range(401)]
    for sign in (1, -1):
        c.path([(px(n), py(MEAN + sign * 1.96 * SD / math.sqrt(n))) for n in steps if bottom <= MEAN + sign * 1.96 * SD / math.sqrt(n) <= top], QUIET, 3, "14 10")
    c.line(x0, py(MEAN), x1, py(MEAN), QUIET, 3)
    c.text(x1 - 12, py(MEAN) + 46, f"Mean {MEAN:.2f}", 34, 500, anchor="end", fill=GREY)
    dots = Grid()
    for u in units:
        r = max(3, radius(u["weight"]))
        c.circle(px(u["weight"]), py(u["mean"]), r, colours.get(u["country"], NOBODY), "#ffffff", 1.2 if r > 4 else 0.6, 0.9)
        if r >= 6:
            dots.add((px(u["weight"]) - r, py(u["mean"]) - r, px(u["weight"]) + r, py(u["mean"]) + r), u["institution"])
    angles = [0, 180]
    for step in range(15, 91, 15):
        angles += [360 - step, step, 180 + step, 180 - step]
    labels = Grid()
    for u in units:
        cx, cy, r = px(u["weight"]), py(u["mean"]), max(3, radius(u["weight"]))
        size = max(12, min(52, 16 + 6.5 * math.log2(u["weight"])))
        rank = ranks.get(u["institution"])
        parts = ([(f"{rank} ", size * 0.86, 400, "cond", QUIET)] if rank else []) + [(u["name"], size, 500, "cond", INK)]
        width = sum(measure(t, z, f, wt) for t, z, wt, f, _ in parts)
        reach = (0, 30, 60, 100, 150, 210, 280, 360, 450, 560, 680) if u["weight"] >= RANKED else (0, 16, 36, 64, 100, 150, 220, 300) if u["weight"] >= 2 else (0, 10, 24, 44, 70)
        best = None
        for distance in reach:
            for angle in angles:
                a = math.radians(angle)
                ax, ay = cx + (r + 8 + distance) * math.cos(a), cy + (r + 8 + distance) * math.sin(a)
                lx = ax if math.cos(a) >= -0.2 else ax - width
                ly = ay + size * CAP / 2
                boxed = (lx - 4, ly - size * 0.92, lx + width + 4, ly + size * 0.25)
                if boxed[0] < x0 or boxed[2] > x1 or boxed[1] < y0 or boxed[3] > y1:
                    continue
                if labels.hit(boxed) or dots.hit(boxed, u["institution"]):
                    continue
                best = (lx, ly, boxed, distance, ax, ay)
                break
            if best:
                break
        if not best:
            continue
        lx, ly, boxed, distance, ax, ay = best
        labels.add(boxed)
        if distance > 12:
            norm = max(math.hypot(ax - cx, ay - cy), 1)
            c.line(cx + r * (ax - cx) / norm, cy + r * (ay - cy) / norm, ax, ay, colours.get(u["country"], NOBODY), 2 if u["weight"] >= 2 else 1)
        c.runs(lx, ly, parts)


def heading(c: Canvas, x0: float, x1: float, y: float, title: str, note: str = "") -> float:
    base = y + 60 * CAP
    c.text(x0, base, title, 60, 600, spacing=8)
    if note:
        c.text(x1, base, note, 36, 400, anchor="end", fill=GREY)
    return base


def axis(c: Canvas, lo: float, hi: float, g0: float, g1: float, base: float, size: float) -> None:
    step = 0.2 if (g1 - g0) * 0.2 / (hi - lo) >= 64 else 0.4
    value = math.ceil(lo / step - 1e-9) * step
    while value <= hi + 1e-9:
        c.text(g0 + (value - lo) / (hi - lo) * (g1 - g0), base, f"{value:.1f}", size, 400, anchor="middle", fill=GREY)
        value += step


def whisker(c: Canvas, mean: float, se: float, lo: float, hi: float, g0: float, g1: float, cy: float, colour: str, dot: float, width: float) -> None:
    def gx(m: float) -> float:
        return g0 + (min(max(m, lo), hi) - lo) / (hi - lo) * (g1 - g0)

    if se:
        c.line(gx(mean - 1.96 * se), cy, gx(mean + 1.96 * se), cy, colour, width)
    c.circle(gx(mean), cy, dot, colour, "#ffffff", 1.2)


def table(c: Canvas, colours: dict, x0: float, x1: float, y: float, rows: list, rh: float) -> float:
    sizes = {u["institution"]: k + 1 for k, u in enumerate(sorted(STATS["institutions"], key=lambda u: -u["weight"]))}
    heading(c, x0, x1, y, "INSTITUTIONS BY SCORE", f"at least {RANKED} submissions")
    head = y + 60 * CAP + 100
    cols = {"rank": x0 + 60, "flag": x0 + 80, "name": x0 + 128, "subs": x0 + 880, "share": x0 + 1010, "above": x0 + 1190, "score": x0 + 1290, "glyph": (x0 + 1340, x0 + 1730), "size": x1}
    for key, label, anchor in (("rank", "Rank", "end"), ("name", "Institution", "start"), ("subs", "Submissions", "end"), ("share", "Share", "end"), ("above", "Above median", "end"), ("score", "Score", "end"), ("size", "Size rank", "end")):
        c.text(cols[key], head, label, 26, 400, anchor=anchor, fill=GREY)
    lo = math.floor(min(u["mean"] - 1.96 * u["se"] for u in rows) * 5) / 5
    hi = math.ceil(max(u["mean"] + 1.96 * u["se"] for u in rows) * 5) / 5
    g0, g1 = cols["glyph"]
    axis(c, lo, hi, g0, g1, head, 24)
    rule = head + 16
    c.line(x0, rule, x1, rule, INK, 3)
    font = min(25, rh * 0.64)
    for k, u in enumerate(rows):
        cy = rule + 4 + (k + 0.5) * rh
        base = cy + font * CAP / 2
        rank = k + 1
        if rank > 1 and rank & (rank - 1) == 0:
            c.line(x0, rule + 4 + k * rh, x1, rule + 4 + k * rh, RULE, 2)
        c.text(cols["rank"], base, str(rank), font, 400, anchor="end", fill=QUIET)
        c.flag(u["country"], cols["flag"], base, font)
        name = u["name"]
        while measure(name, font, "cond", 500) > cols["subs"] - cols["name"] - 170 and len(name) > 4:
            name = name[:-2].rstrip() + "…"
        c.text(cols["name"], base, name, font, 500, "cond")
        c.text(cols["subs"], base, fixed(u["weight"]), font, 400, anchor="end")
        c.text(cols["share"], base, share(u["weight"] / USED), font, 400, anchor="end", fill=SOFT)
        c.text(cols["above"], base, percent(u["above"]), font, 400, anchor="end", fill=SOFT)
        c.text(cols["score"], base, f"{u['mean']:.2f}", font, 600, anchor="end")
        whisker(c, u["mean"], u["se"], lo, hi, g0, g1, cy, colours.get(u["country"], NOBODY), font * 0.28, 3)
        c.text(cols["size"], base, str(sizes[u["institution"]]), font, 400, anchor="end", fill=GREY)
    end = rule + 4 + len(rows) * rh
    c.line(g0 + (MEAN - lo) / (hi - lo) * (g1 - g0), rule, g0 + (MEAN - lo) / (hi - lo) * (g1 - g0), end, QUIET, 2, "6 6")
    c.line(x0, end, x1, end, INK, 3)
    return end


def ledger(c: Canvas, title: str, label: str, rows: list, x0: float, x1: float, y: float, rh: float, flags: bool, colour, name) -> float:
    heading(c, x0, x1, y, title)
    head = y + 60 * CAP + 100
    start = x0 + (128 if flags else 80)
    cols = {"rank": x0 + 60, "flag": x0 + 80, "subs": x0 + 760, "share": (x0 + 800, x0 + 1150), "above": (x0 + 1200, x0 + 1530), "score": x0 + 1640, "glyph": (x0 + 1670, x1)}
    c.text(cols["rank"], head, "Rank", 26, 400, anchor="end", fill=GREY)
    c.text(start, head, label, 26, 400, fill=GREY)
    c.text(cols["subs"], head, "Submissions", 26, 400, anchor="end", fill=GREY)
    c.text(cols["share"][0], head, "Share", 26, 400, fill=GREY)
    c.text(cols["above"][0], head, "Above median", 26, 400, fill=GREY)
    c.text(cols["score"], head, "Score", 26, 400, anchor="end", fill=GREY)
    g0, g1 = cols["glyph"]
    lo = max(math.floor(min(n["mean"] - 1.96 * n["se"] for n in rows) * 5) / 5, math.floor((MEAN - 0.4) * 5) / 5)
    hi = min(math.ceil(max(n["mean"] + 1.96 * n["se"] for n in rows) * 5) / 5, math.ceil((MEAN + 0.4) * 5) / 5)
    axis(c, lo, hi, g0 + 20, g1 - 20, head, 24)
    rule = head + 16
    c.line(x0, rule, x1, rule, INK, 3)
    widest = max(n["weight"] for n in rows) / USED
    font = min(26, rh * 0.6)
    for k, n in enumerate(rows):
        cy = rule + 4 + (k + 0.5) * rh
        base = cy + font * CAP / 2
        rank = k + 1
        if rank > 1 and rank & (rank - 1) == 0:
            c.line(x0, rule + 4 + k * rh, x1, rule + 4 + k * rh, RULE, 2)
        tint = colour(n)
        c.text(cols["rank"], base, str(rank), font, 400, anchor="end", fill=QUIET)
        if flags:
            c.flag(n["country"], cols["flag"], base, font)
        c.text(start, base, name(n), font, 500, "cond")
        c.text(cols["subs"], base, fixed(n["weight"]), font, 400, anchor="end")
        bar = font * 0.8
        a, b = cols["share"]
        length = (b - a - 120) * (n["weight"] / USED) / widest
        c.rect(a, cy - bar / 2, length, bar, tint)
        c.text(a + length + 10, base, share(n["weight"] / USED), font * 0.92, 400, fill=SOFT)
        a, b = cols["above"]
        length = (b - a - 110) * n["above"]
        c.rect(a, cy - bar / 2, length, bar, tint)
        c.text(a + max(length, (b - a - 110) * OVERALL["above"]) + 10, base, percent(n["above"]), font * 0.92, 400, fill=SOFT)
        c.text(cols["score"], base, f"{n['mean']:.2f}", font, 600, anchor="end")
        whisker(c, n["mean"], n["se"], lo, hi, g0 + 20, g1 - 20, cy, tint, font * 0.3, 4)
    end = rule + 4 + len(rows) * rh
    a, b = cols["above"]
    c.line(a + (b - a - 110) * OVERALL["above"], rule, a + (b - a - 110) * OVERALL["above"], end, QUIET, 2, "6 6")
    gm = g0 + 20 + (MEAN - lo) / (hi - lo) * (g1 - g0 - 40)
    c.line(gm, rule, gm, end, QUIET, 2, "6 6")
    c.line(x0, end, x1, end, INK, 3)
    return end


def mosaic(c: Canvas, colours: dict, box: tuple) -> None:
    x0, y0, x1, y1 = box
    base = heading(c, x0 + 4, x1 - 4, y0, "INSTITUTIONS BY COUNTRY")
    swatch = 140
    lx = x1 - 4 - 8 * swatch
    for k, colour in enumerate(CLASSES):
        c.rect(lx + k * swatch, base - 46, swatch, 46, colour)
    for k, b in enumerate(BOUNDS):
        c.text(lx + (k + 1) * swatch, base + 44, f"{MEAN + b:.2f}", 30, 400, anchor="middle")
    c.text(lx - 24, base - 46 / 2 + 40 * CAP / 2, "Score", 40, 500, anchor="end")
    top = base + 90
    nations = [n for n in STATS["countries"] if n["country"]]
    blocks = squarify([n["weight"] for n in nations], x0, top, x1 - x0, y1 - top)
    for n, (bx, by, bw, bh) in zip(nations, blocks):
        code = n["country"]
        pad = 3
        bx, by, bw, bh = bx + pad, by + pad, bw - 2 * pad, bh - 2 * pad
        header = 0
        if bw > 150 and bh > 110:
            size = max(20, min(70, math.sqrt(bw * bh) / 14))
            header = size * 1.55
            yb = by + header * 0.5 + size * CAP / 2
            x = bx + 10
            square = size * 0.56
            c.rect(x, yb - size * CAP / 2 - square / 2, square, square, colours.get(code, NOBODY))
            x += square + size * 0.28
            flag = c.flag(code, x, yb, size)
            x += flag + (size * 0.3 if flag else 0)
            parts = [(country(code), size, 600, "sans", INK), (f"  {fixed(n['weight'])}", size * 0.8, 400, "sans", GREY), (f"  {share(n['weight'] / USED)}", size * 0.8, 400, "sans", GREY)]
            while len(parts) > 1 and sum(measure(t, s, f, w) for t, s, w, f, _ in parts) > bx + bw - x - 10:
                parts.pop()
            while parts[0][1] > 14 and measure(parts[0][0], parts[0][1], "sans", 600) > bx + bw - x - 10:
                parts[0] = (parts[0][0], parts[0][1] - 2, 600, "sans", INK)
            c.runs(x, yb, parts)
        members = [i for i in STATS["institutions"] if i["country"] == code]
        tiles = squarify([i["weight"] for i in members], bx, by + header, bw, bh - header)
        for u, (tx, ty, tw, th) in zip(members, tiles):
            c.rect(tx + 1, ty + 1, tw - 2, th - 2, klass(u["mean"]))
            if tw < 46 or th < 30:
                continue
            corner = 0
            fit = None
            for s in (64, 56, 48, 42, 36, 32, 28, 24, 21, 18, 16, 14, 12):
                lines = wrap(u["name"], s, tw - 14, "cond", 500, 3)
                if not lines:
                    continue
                block = len(lines) * s * 1.12
                corner = max(12, min(26, s * 0.55)) if th - 10 >= block + 2 * max(12, min(26, s * 0.55)) * 1.4 and tw > 100 else 0
                if block + corner * 2.8 <= th - 10:
                    fit = (s, lines, block)
                    break
            if not fit:
                continue
            s, lines, block = fit
            if corner:
                c.text(tx + 8, ty + 6 + corner * CAP + 4, f"{u['mean']:.2f}", corner, 600, "cond", fill=SOFT)
                c.text(tx + tw - 8, ty + 6 + corner * CAP + 4, fixed(u["weight"]), corner, 400, "cond", anchor="end", fill=GREY)
            first = ty + (th - block) / 2 + s * 0.84
            for i, t in enumerate(lines):
                c.text(tx + tw / 2, first + i * s * 1.12, t, s, 500, "cond", anchor="middle")


def build(hidden: set) -> Canvas:
    c = Canvas()
    c.hidden = hidden
    colours = painter([n["country"] for n in STATS["countries"]])
    end = masthead(c)
    nations = [n for n in STATS["countries"] if n["country"]]
    continents = [k for k in STATS["continents"] if k["continent"]]
    kinds = [k for k in STATS["kinds"] if k["kind"]]
    rows = sorted([u for u in STATS["institutions"] if u["weight"] >= RANKED], key=lambda u: -u["mean"])
    block = 60 * CAP + 100 + 16 + 4
    rh = (BOTTOM - TOP - 4 * block - 3 * GAP) / (len(rows) + len(nations) + len(continents) + len(kinds))
    y = table(c, colours, COLUMN, R, TOP, rows, rh) + GAP
    y = ledger(c, "COUNTRIES", "Country", nations, COLUMN, R, y, rh, True, lambda n: colours.get(n["country"], NOBODY), lambda n: country(n["country"])) + GAP
    y = ledger(c, "CONTINENTS", "Continent", continents, COLUMN, R, y, rh, False, lambda n: tone(n["continent"]) if n["continent"] in FAMILIES else NOBODY, lambda n: n["continent"]) + GAP
    paint = {k["kind"]: KINDS[i % len(KINDS)] for i, k in enumerate(kinds)}
    ledger(c, "INSTITUTION TYPES", "Type", kinds, COLUMN, R, y, rh, False, lambda n: paint[n["kind"]], lambda n: n["kind"].capitalize())
    funnel(c, colours, {u["institution"]: k + 1 for k, u in enumerate(rows)}, (L + 20 + measure("2.7", 34), end + 150, SPLIT, end + 150 + 2900))
    mosaic(c, colours, (L - 4, end + 150 + 2900 + 230, SPLIT + 4, BOTTOM + 5))
    return c


def render(svg: pathlib.Path, png: pathlib.Path) -> None:
    for budget in (600000, 1200000, 2400000, 4800000):
        subprocess.run(
            ["chromium", "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", f"--window-size={W},{H}", "--run-all-compositor-stages-before-draw", f"--virtual-time-budget={budget}", f"--screenshot={png}", svg.as_uri()],
            check=True,
            capture_output=True,
        )
        image = Image.open(png).convert("RGB")
        if min(image.getpixel((R - 10, BOTTOM + k))[0] for k in range(-2, 3)) < 80 and image.getpixel((L + 10, BOTTOM - 20)) != (255, 255, 255):
            return
    raise RuntimeError(f"incomplete render of {svg.name}")


def main() -> None:
    build(set()).save(HERE / f"{NAME}.svg")
    render(HERE / f"{NAME}.svg", HERE / f"{NAME}.png")
    variant = HERE / f"{NAME}-nohmt"
    build(HIDDEN).save(variant.with_suffix(".svg"))
    full = variant.with_name(variant.name + "-full.png")
    render(variant.with_suffix(".svg"), full)
    small = variant.with_name(variant.name + "-4mb.png")
    for colours in (256, 192, 128):
        Image.open(full).convert("RGB").quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(small, optimize=True)
        if small.stat().st_size < 4_000_000:
            break
    full.unlink()


main()

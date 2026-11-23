import json
import pathlib
import shutil
import subprocess

from PIL import ImageFont

HERE = pathlib.Path(__file__).parent
BROWSER = shutil.which("chromium") or shutil.which("google-chrome") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
STATS = json.loads((HERE / "stats.json").read_text())
NAME = "iclr2027-scores-poster"

W, H = 6000, 8000
L, R = 130, 5870
INK = "#111111"
SOFT = "#4b5260"
MUTED = "#8a919c"
HAIR = "#d9dde3"
BAND = "#f4f6f9"
SECTION = "#e9eef5"
BLUE = "#1f5fbf"
NAVY = "#14305f"
STOPS = [(0.0, "#f2f6fb"), (0.05, "#d8e5f5"), (0.10, "#b1cbec"), (0.20, "#6d9fdb"), (0.30, "#2f6bbf"), (0.40, "#163e85")]
FAMILY = {"sans": "Arial, 'Liberation Sans', Helvetica, sans-serif", "narrow": "'Arial Narrow', 'TeX Gyre Heros Cn', 'Liberation Sans Narrow', sans-serif"}
PATTERNS = {("sans", "normal"): "Arial", ("sans", "bold"): "Arial:bold", ("narrow", "normal"): "Arial Narrow", ("narrow", "bold"): "Arial Narrow:bold"}
LOADED = {}


def measure(text: str, size: float, family: str = "sans", weight: str = "normal") -> float:
    key = (family, weight)
    if key not in LOADED:
        if shutil.which("fc-match"):
            file = subprocess.run(["fc-match", "-f", "%{file}", PATTERNS[key]], check=True, capture_output=True, text=True).stdout
        else:
            file = f"/System/Library/Fonts/Supplemental/{PATTERNS[key].replace(':bold', ' Bold')}.ttf"
        LOADED[key] = ImageFont.truetype(file, 1000)
    return LOADED[key].getlength(text) * size / 1000


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def shade(value: float) -> str:
    value = min(max(value, 0.0), STOPS[-1][0])
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if value <= b:
            t = (value - a) / (b - a)
            pa = [int(ca[i : i + 2], 16) for i in (1, 3, 5)]
            pb = [int(cb[i : i + 2], 16) for i in (1, 3, 5)]
            return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))
    return STOPS[-1][1]


def count(n: int) -> str:
    return f"{n:,}"


def score(v: float) -> str:
    return f"{v:.2f}"


def percent(p: float) -> str:
    p *= 100
    if p == 0:
        return "0"
    if p < 0.1:
        return f"{p:.3f}"
    if p < 1:
        return f"{p:.2f}"
    return f"{p:.1f}"


class Canvas:
    def __init__(self) -> None:
        self.defs = []
        self.items = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']

    def rect(self, x: float, y: float, w: float, h: float, fill: str) -> None:
        self.items.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(w, 0):.2f}" height="{h:.2f}" fill="{fill}"/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = INK, width: float = 3) -> None:
        self.items.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{width}"/>')

    def circle(self, x: float, y: float, r: float, fill: str) -> None:
        self.items.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}"/>')

    def text(self, x: float, y: float, s: str, size: float, weight: str = "normal", anchor: str = "start", fill: str = INK, family: str = "sans", baseline: str = "central") -> None:
        self.items.append(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FAMILY[family]}" font-size="{size:.2f}" font-weight="{weight}" '
            f'text-anchor="{anchor}" dominant-baseline="{baseline}" fill="{fill}">{escape(s)}</text>'
        )

    def gradient(self, x: float, y: float, w: float, h: float) -> None:
        stops = "".join(f'<stop offset="{a / STOPS[-1][0]:.3f}" stop-color="{c}"/>' for a, c in STOPS)
        self.defs.append(f'<linearGradient id="ramp" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient>')
        self.items.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="url(#ramp)"/>')

    def save(self, path: pathlib.Path) -> None:
        head = f'<svg xmlns="http://www.w3.org/2000/svg" width="7200" height="9600" viewBox="0 0 {W} {H}">'
        path.write_text(head + "<defs>" + "".join(self.defs) + "</defs>" + "".join(self.items) + "</svg>")


def header(c: Canvas) -> None:
    c.text(L, 120, "ICLR 2027 Review Scores", 250, "bold", baseline="text-before-edge")
    c.text(L, 440, "Initial ratings at review release, overall and by primary area", 80, "bold", baseline="text-before-edge")
    block = [("Author:", "abdukarimovhm", INK), ("Contact:", "https://github.com/abdukarimovhm", BLUE), ("Date:", "Nov 24, 2026", INK), ("Data:", "OpenReview, Nov 6, 2026", INK)]
    x = R - max(measure(v, 46) for _, v, _ in block)
    for i, (k, v, colour) in enumerate(block):
        y = 160 + i * 62
        c.text(x - 16, y, k, 46, "bold", anchor="end")
        c.text(x, y, v, 46, fill=colour)
    left, width = R - 1150, 1150
    c.text(left, 455, "Share of an area's submissions in each band", 32, "bold")
    c.gradient(left, 490, width, 40)
    for tick in range(5):
        c.text(left + width * tick / 4, 565, f"{tick * 10}%", 28, fill=SOFT, anchor=["start", "middle", "middle", "middle", "end"][tick])
    c.line(L, 630, R, 630, INK, 4)


def hero(c: Canvas) -> None:
    overall = STATS["overall"]
    span = (R - L) / 5
    groups = [("COUNTS", 0, 2), ("AVERAGE RATING PER SUBMISSION", 2, 5)]
    for title, a, b in groups:
        c.text(L + a * span, 700, title, 34, "bold", fill=MUTED)
        c.line(L + a * span, 730, L + b * span - 80, 730, HAIR, 3)
    items = [
        (count(overall["submissions"]), "submissions under review"),
        (count(overall["reviews"]), "reviews"),
        (score(overall["mean"]), "mean"),
        (score(overall["median"]), "median"),
        (f"{score(overall['q1'])}–{score(overall['q3'])}", "first to third quartile"),
    ]
    for i, (number, label) in enumerate(items):
        x = L + i * span
        c.text(x, 760, number, 200, "bold", fill=NAVY, baseline="text-before-edge")
        c.text(x, 990, label, 50, fill=SOFT, baseline="text-before-edge")


def titled(c: Canvas, x0: float, x1: float, y: float, title: str) -> None:
    c.text(x0, y, title, 46, "bold")
    c.line(x0, y + 42, x1, y + 42, INK, 3)


def bars(c: Canvas, x0: float, x1: float, y: float, title: str, labels: tuple, rows: list, total: int, rh: float = 100) -> float:
    titled(c, x0, x1, y, title)
    c.text(x0, y + 88, labels[0], 30, "bold", fill=MUTED)
    c.text(x0 + 260, y + 88, labels[1], 30, "bold", fill=MUTED)
    c.text(x1, y + 88, labels[2], 30, "bold", anchor="end", fill=MUTED)
    top = y + 125
    longest = max(n for _, n in rows)
    span = x1 - x0 - 260 - 420
    for i, (label, n) in enumerate(rows):
        cy = top + i * rh + rh / 2
        if i % 2 == 0:
            c.rect(x0, top + i * rh, x1 - x0, rh, BAND)
        c.text(x0 + 16, cy, label, 42, "bold")
        length = span * n / longest
        c.rect(x0 + 260, cy - 24, length, 48, BLUE)
        c.text(x0 + 260 + length + 16, cy, count(n), 38, "bold")
        c.text(x1, cy, f"{percent(n / total)}%", 38, fill=SOFT, anchor="end")
    return top + len(rows) * rh


def ladder(c: Canvas, x0: float, x1: float, y: float, rh: float = 100) -> float:
    titled(c, x0, x1, y, "PERCENTILES OF THE AVERAGE")
    c.text(x0, y + 88, "PERCENTILE", 30, "bold", fill=MUTED)
    c.text(x1, y + 88, "AVERAGE", 30, "bold", anchor="end", fill=MUTED)
    top = y + 125
    rows = sorted(STATS["percentiles"].items(), key=lambda item: -int(item[0]))
    a, b = x0 + 300, x1 - 260

    def place(v: float) -> float:
        return a + (b - a) * (v - 1) / 3

    bottom = top + len(rows) * rh
    for i in range(len(rows)):
        if i % 2 == 0:
            c.rect(x0, top + i * rh, x1 - x0, rh, BAND)
    for tick in (1, 2, 3, 4):
        c.line(place(tick), top, place(tick), bottom, HAIR, 3)
        c.text(place(tick), bottom + 40, str(tick), 34, fill=SOFT, anchor="middle")
    for i, (q, v) in enumerate(rows):
        cy = top + i * rh + rh / 2
        suffix = {"1": "st"}.get(q, "th")
        c.text(x0 + 16, cy, f"{q}{suffix}", 42, "bold")
        c.circle(place(v), cy, 20, NAVY)
        c.text(x1, cy, score(v), 38, "bold", anchor="end")
    return bottom + 70


def exact(c: Canvas, x0: float, x1: float, y: float, rh: float) -> float:
    titled(c, x0, x1, y, "AVERAGE RATING PER SUBMISSION, EVERY VALUE")
    cols = {"value": x0 + 150, "bar": x0 + 190, "share": x0 + 1750, "rank": x0 + 2260, "top": x1}
    c.text(cols["value"], y + 88, "AVERAGE", 30, "bold", anchor="end", fill=MUTED)
    c.text(cols["bar"], y + 88, "SUBMISSIONS", 30, "bold", fill=MUTED)
    c.text(cols["share"], y + 88, "SHARE", 30, "bold", anchor="end", fill=MUTED)
    c.text(cols["rank"], y + 88, "RANK", 30, "bold", anchor="end", fill=MUTED)
    c.text(cols["top"], y + 88, "TOP", 30, "bold", anchor="end", fill=MUTED)
    top = y + 125
    rows = STATS["exact"]
    longest = max(r["count"] for r in rows)
    span = 1050
    overall = STATS["overall"]
    tags = {round(overall["q1"], 4): "Q1", round(overall["median"], 4): "Median", round(overall["q3"], 4): "Q3"}
    for i, r in enumerate(rows):
        cy = top + i * rh + rh / 2
        if i % 2 == 0:
            c.rect(x0, top + i * rh, x1 - x0, rh, BAND)
        c.text(cols["value"], cy, score(r["value"]), 38, "bold", anchor="end")
        length = span * r["count"] / longest
        c.rect(cols["bar"], cy - 20, length, 40, BLUE)
        label = count(r["count"])
        c.text(cols["bar"] + length + 14, cy, label, 36, "bold")
        tag = tags.get(round(r["value"], 4))
        if tag:
            c.text(cols["bar"] + length + 14 + measure(label, 36, weight="bold") + 26, cy, tag, 34, "bold", fill=NAVY)
        c.text(cols["share"], cy, f"{percent(r['share'])}%", 36, fill=SOFT, anchor="end")
        rank = count(r["first"]) if r["first"] == r["last"] else f"{count(r['first'])}–{count(r['last'])}"
        c.text(cols["rank"], cy, rank, 36, fill=SOFT, anchor="end")
        c.text(cols["top"], cy, f"{percent(r['top_from'])}–{percent(r['top_to'])}%", 36, anchor="end")
    return top + len(rows) * rh


def wrap(text: str, size: float, width: float, family: str, weight: str) -> list:
    if measure(text, size, family, weight) <= width:
        return [text]
    words, first = text.split(" "), []
    while words and measure(" ".join(first + [words[0]]), size, family, weight) <= width:
        first.append(words.pop(0))
    return [" ".join(first), " ".join(words)]


def areas(c: Canvas, y: float, rh: float) -> float:
    c.rect(L, y, R - L, 110, SECTION)
    c.text(L + 24, y + 55, "BY PRIMARY AREA", 54, "bold")
    c.text(R - 24, y + 55, "sorted by mean average rating", 34, fill=SOFT, anchor="end")
    heat0, cell = 3060, 212
    heat1 = heat0 + 10 * cell
    cols = {"area": L + 16, "subs": 1640, "reviews": 2350, "mean": 2545, "q1": 2660, "median": 2810, "q3": 2960, "above": [5410, 5640, R]}
    g = y + 180
    note = "from the value shown up to the next"
    first = measure("AVERAGE RATING BAND", 32, weight="bold")
    start = heat0 + 10 * cell / 2 - (first + 18 + measure(note, 30)) / 2
    c.text(start, g, "AVERAGE RATING BAND", 32, "bold")
    c.text(start + first + 18, g, note, 30, fill=MUTED)
    c.line(heat0 + 6, g + 34, heat1 - 6, g + 34, HAIR, 3)
    c.text((heat1 + R) / 2 + 20, g, "SHARE AT OR ABOVE", 32, "bold", anchor="middle")
    c.line(heat1 + 60, g + 34, R, g + 34, HAIR, 3)
    c.text(cols["q1"] - 40 + 150, g, "AVERAGE", 32, "bold", anchor="middle")
    c.line(cols["mean"] - 150, g + 34, cols["q3"] + 60, g + 34, HAIR, 3)
    h = g + 85
    c.text(cols["area"], h, "PRIMARY AREA", 32, "bold")
    c.text(cols["subs"], h, "SUBMISSIONS", 32, "bold")
    c.text(cols["reviews"], h, "REVIEWS", 32, "bold", anchor="end")
    c.text(cols["mean"], h, "MEAN", 32, "bold", anchor="end")
    for key, label in (("q1", "Q1"), ("median", "MEDIAN"), ("q3", "Q3")):
        c.text(cols[key], h, label, 32, "bold", anchor="middle")
    for i in range(10):
        c.text(heat0 + i * cell + cell / 2, h, score(1 + i / 3), 32, "bold", anchor="middle")
    for x, label in zip(cols["above"], ("≥2.33", "≥2.67", "≥3.00")):
        c.text(x, h, label, 32, "bold", anchor="end")
    c.line(L, h + 42, R, h + 42, INK, 4)
    top = h + 56
    rows = [("All submissions", STATS["overall"])] + sorted(STATS["areas"].items(), key=lambda item: -item[1]["mean"])
    longest = max(s["submissions"] for _, s in rows[1:])
    for i, (name, s) in enumerate(rows):
        y0 = top + i * rh
        cy = y0 + rh / 2
        strong = "bold" if i == 0 else "normal"
        if i % 2 == 1:
            c.rect(L, y0, R - L, rh, BAND)
        label = name[0].upper() + name[1:]
        lines = wrap(label, 42, cols["subs"] - cols["area"] - 60, "narrow", strong)
        for j, part in enumerate(lines):
            c.text(cols["area"], cy + (j - (len(lines) - 1) / 2) * 50, part, 42, strong, family="narrow")
        length = 380 * min(s["submissions"] / longest, 1)
        if i:
            c.rect(cols["subs"], cy - 22, length, 44, BLUE)
            c.text(cols["subs"] + length + 14, cy, count(s["submissions"]), 38, "bold")
        else:
            c.text(cols["subs"], cy, count(s["submissions"]), 38, "bold")
        c.text(cols["reviews"], cy, count(s["reviews"]), 38, strong, fill=SOFT, anchor="end")
        c.text(cols["mean"], cy, f"{s['mean']:.3f}", 40, "bold", anchor="end")
        for key in ("q1", "median", "q3"):
            c.text(cols[key], cy, score(s[key]), 40, strong, anchor="middle")
        for k, n in enumerate(s["bands"]):
            share = n / s["submissions"]
            x = heat0 + k * cell
            c.rect(x + 5, y0 + 8, cell - 10, rh - 16, shade(share))
            ink = "#ffffff" if share >= 0.25 else (INK if n else MUTED)
            c.text(x + cell / 2, cy - 17, count(n), 40, "bold", fill=ink, anchor="middle")
            c.text(x + cell / 2, cy + 28, f"{percent(share)}%", 28, fill=ink if share >= 0.25 else (INK if share >= 0.10 else SOFT), anchor="middle")
        for x, key in zip(cols["above"], ("2.33", "2.67", "3.00")):
            c.text(x, cy, f"{percent(s['above'][key])}%", 40, strong, anchor="end")
        if i == 0:
            c.line(L, y0 + rh, R, y0 + rh, INK, 3)
    bottom = top + len(rows) * rh
    c.line(L, bottom, R, bottom, INK, 4)
    return bottom


def main() -> None:
    c = Canvas()
    header(c)
    hero(c)
    y = 1160
    mid = 2830
    overall = STATS["overall"]
    ratings = [(str(k), STATS["ratings"][str(k)]) for k in (4, 3, 2, 1)]
    left = bars(c, L, mid, y, "RATINGS", ("RATING", "REVIEWS", "SHARE"), ratings, overall["reviews"])
    per = [(k, v) for k, v in STATS["per_submission"].items()]
    left = bars(c, L, mid, left + 110, "REVIEWS PER SUBMISSION", ("REVIEWS", "SUBMISSIONS", "SHARE"), per, overall["submissions"])
    left = ladder(c, L, mid, left + 110)
    rh = (left - y - 125) / len(STATS["exact"])
    right = exact(c, 3010, R, y, rh)
    areas(c, max(left, right) + 130, 158)
    svg = HERE / f"{NAME}.svg"
    c.save(svg)
    subprocess.run(
        [BROWSER, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=7200,9600", "--run-all-compositor-stages-before-draw", "--virtual-time-budget=30000", f"--screenshot={HERE / (NAME + '.png')}", svg.as_uri()],
        check=True,
        capture_output=True,
    )


main()

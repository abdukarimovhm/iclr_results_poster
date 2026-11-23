"""Shared "soft academic" look for my posters: pastel rounded cards, one friendly sans.

Posters are written as HTML + inline SVG and rendered with headless Chrome to PNG and PDF.
"""

import html
import pathlib
import shutil
import subprocess
import tempfile

import segno

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "out"
AUTHOR = "abdukarimovhm"
REPO = "https://github.com/abdukarimovhm/iclr_results_poster"

# Page: A-series ratio, rendered at 3x for print.
W = 1600
SCALE = 3

INK = "#1e1b3a"
SOFT = "#4a4766"
MUTED = "#7d7a96"
LINE = "#e6e4f2"
PAGE = "#fafaff"
CARD = "#ffffff"

PURPLE, PURPLE_BG, PURPLE_DARK = "#5b4fd6", "#eeedfe", "#3c3489"
TEAL, TEAL_BG, TEAL_DARK = "#1d9e75", "#e1f5ee", "#085041"
CORAL, CORAL_BG, CORAL_DARK = "#d85a30", "#faece7", "#712b13"
LILAC = "#b9b3f0"


STOPS = ["#f3f2fe", "#dedbfa", "#c4bff3", "#a59eea", "#857cde", "#6a5fd2", "#5348b5", "#40378f", "#2f286d", "#211b4f"]


def ramp(n: int, stops: list = STOPS) -> list:
    """n-step single-hue sequential ramp (purple), light to dark, interpolated through hand-picked stops."""
    rgb = [[int(s[i : i + 2], 16) for i in (1, 3, 5)] for s in stops]
    out = []
    for k in range(n):
        pos = k / (n - 1) * (len(rgb) - 1)
        i = min(int(pos), len(rgb) - 2)
        f = pos - i
        out.append("#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(rgb[i], rgb[i + 1])))
    return out


def esc(text) -> str:
    return html.escape(str(text))


def qr(url: str = REPO, size: int = 150, colour: str = INK) -> str:
    code = segno.make(url, error="m")
    return code.svg_inline(scale=size / code.symbol_size(border=0)[0], border=0, dark=colour)


FONT_LINK = '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=block" rel="stylesheet">'

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;background:{PAGE};color:{INK};font-family:'Plus Jakarta Sans',system-ui,sans-serif;
  font-variant-numeric:tabular-nums;-webkit-font-smoothing:antialiased}}
.page{{padding:56px;display:flex;flex-direction:column;gap:28px}}
.row{{display:grid;gap:28px}}
.card{{background:{CARD};border-radius:28px;padding:34px 38px;border:1.5px solid {LINE}}}
.card.purple{{background:{PURPLE_BG};border-color:transparent}}
.card.teal{{background:{TEAL_BG};border-color:transparent}}
.card.coral{{background:{CORAL_BG};border-color:transparent}}
h2{{font-size:30px;font-weight:800;letter-spacing:-.01em;margin-bottom:6px}}
.sub{{font-size:18px;color:{SOFT};line-height:1.45;margin-bottom:22px}}
.note{{font-size:17px;color:{SOFT};line-height:1.45;margin-top:18px}}
.note b{{color:{INK}}}
.kpi .v{{font-size:64px;font-weight:800;letter-spacing:-.03em;line-height:1}}
.kpi .l{{font-size:19px;color:{SOFT};margin-top:12px;line-height:1.35}}
svg text{{font-family:'Plus Jakarta Sans',system-ui,sans-serif}}
.hero{{background:{PURPLE};color:#fff;border-radius:36px;padding:52px 56px;display:flex;justify-content:space-between;gap:40px}}
.hero .kick{{font-size:22px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#d9d5ff}}
.hero h1{{font-size:78px;font-weight:800;letter-spacing:-.03em;line-height:1.02;margin:14px 0 18px}}
.hero .lede{{font-size:24px;line-height:1.45;color:#ecebff;max-width:980px}}
.hero .meta{{display:flex;flex-direction:column;align-items:center;gap:12px;flex-shrink:0}}
.hero .qr{{background:#fff;border-radius:22px;padding:16px;line-height:0}}
.hero .who{{font-size:18px;color:#ecebff;text-align:center;line-height:1.4}}
.foot{{font-size:16px;color:{MUTED};line-height:1.55;display:flex;justify-content:space-between;gap:40px;padding:0 8px}}
.foot b{{color:{SOFT}}}
.legend{{display:flex;gap:22px;flex-wrap:wrap;font-size:16px;color:{SOFT};align-items:center}}
.legend i{{display:inline-block;width:16px;height:16px;border-radius:5px;margin-right:8px;vertical-align:-2px}}
"""


def hero(kicker: str, title: str, lede: str, date: str) -> str:
    return f"""<header class="hero">
  <div><div class="kick">{esc(kicker)}</div><h1>{title}</h1><p class="lede">{lede}</p></div>
  <div class="meta"><div class="qr">{qr(size=150)}</div>
  <div class="who"><b>{AUTHOR}</b><br>{esc(date)}</div></div>
</header>"""


def footer(left: str) -> str:
    return f"""<footer class="foot"><div>{left}</div>
<div style="text-align:right;flex-shrink:0">Made by <b>{AUTHOR}</b> · {REPO.removeprefix('https://')}<br>
Some data-processing code adapted from clareLab/posters (MIT)</div></footer>"""


def document(title: str, body: str, extra_css: str = "") -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{esc(title)}</title>{FONT_LINK}
<style>{CSS}{extra_css}</style></head><body><div class="page" id="page">{body}</div></body></html>"""


BROWSER = shutil.which("chromium") or shutil.which("google-chrome") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _chrome(*args: str) -> str:
    return subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--run-all-compositor-stages-before-draw",
                           "--virtual-time-budget=60000", *args], check=True, capture_output=True, text=True).stdout


MEASURE = "<script>addEventListener('load',()=>document.fonts.ready.then(()=>{document.body.dataset.h=Math.ceil(document.getElementById('page').getBoundingClientRect().height)}))</script>"


def render(doc: str, name: str) -> pathlib.Path:
    """Write <name>.html, measure its height, then render <name>.png (3x) and <name>.pdf."""
    OUT.mkdir(exist_ok=True)
    page = OUT / f"{name}.html"
    page.write_text(doc.replace("</body>", MEASURE + "</body>"))
    dom = _chrome(f"--window-size={W},2000", "--dump-dom", page.as_uri())
    height = int(dom.split('data-h="', 1)[1].split('"', 1)[0])
    page.write_text(doc.replace("</style>", f"html,body{{height:{height}px;overflow:hidden}}@page{{size:{W}px {height}px;margin:0}}</style>", 1))
    _chrome(f"--force-device-scale-factor={SCALE}", f"--window-size={W},{height}", f"--screenshot={OUT / (name + '.png')}", page.as_uri())
    with tempfile.TemporaryDirectory() as tmp:
        _chrome(f"--user-data-dir={tmp}", "--no-pdf-header-footer", f"--print-to-pdf={OUT / (name + '.pdf')}", page.as_uri())
    print(f"{name}: {W}x{height} CSS px -> {OUT / (name + '.png')}")
    return OUT / f"{name}.png"


# ---------- shared pieces used by several posters ----------

def pct(x: float, d: int = 1) -> str:
    if 0 < x < 5 * 10 ** -(d + 3):
        return f"<{10 ** -d:g}%"
    return f"{x * 100:.{d}f}%"


def pos(v: float, lo: float, hi: float) -> float:
    return max(0.0, min(100.0, (v - lo) / (hi - lo) * 100))


def axis(lo: float, hi: float, ticks: list, fmt: str = "{:.2f}") -> str:
    """Tick labels for a track column; put it in the header row above dot/arrow tracks."""
    labels = "".join(f'<span style="left:{pos(t, lo, hi):.2f}%">{fmt.format(t)}</span>' for t in ticks)
    return f'<div class="axis">{labels}</div>'


def dot_track(mean: float, se: float, lo: float, hi: float, colour: str = PURPLE, ref: float = None) -> str:
    """A dot at the mean with a soft bar for the 95% interval."""
    a, b = pos(mean - 1.96 * se, lo, hi), pos(mean + 1.96 * se, lo, hi)
    line = f'<u style="left:{pos(ref, lo, hi):.2f}%"></u>' if ref is not None else ""
    return (f'<div class="track">{line}<s style="left:{a:.2f}%;width:{b - a:.2f}%;background:{colour}33"></s>'
            f'<b style="left:{pos(mean, lo, hi):.2f}%;background:{colour}"></b></div>')


def arrow_track(start: float, end: float, lo: float, hi: float, colour: str = PURPLE, ref: float = None) -> str:
    """Hollow dot at start, filled dot at end, joined by a bar."""
    a, b = pos(start, lo, hi), pos(end, lo, hi)
    left, width = min(a, b), abs(b - a)
    line = f'<u style="left:{pos(ref, lo, hi):.2f}%"></u>' if ref is not None else ""
    return (f'<div class="track">{line}<s style="left:{left:.2f}%;width:{width:.2f}%;background:{colour}55;height:8px;top:calc(50% - 4px)"></s>'
            f'<b style="left:{a:.2f}%;background:#fff;border:3px solid {colour}"></b><b style="left:{b:.2f}%;background:{colour}"></b></div>')


def name_cell(name: str, code: str = "", weight: int = 600) -> str:
    """Institution or country name that truncates with an ellipsis but always keeps its country badge."""
    return (f'<span style="display:flex;align-items:center;min-width:0;font-weight:{weight}"><span style="white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis">{esc(name)}</span>{badge(code)}</span>')


def badge(code: str) -> str:
    return f'<span class="badge">{esc(code)}</span>' if code else ""


def share_bar(share: float, top: float, colour: str = PURPLE) -> str:
    return f'<div class="sbar"><i style="width:{share / top * 100:.2f}%;background:{colour}"></i></div>'


TRACK_CSS = f"""
.track{{position:relative;height:30px}}
.track s{{position:absolute;top:calc(50% - 7px);height:14px;border-radius:7px;text-decoration:none}}
.track b{{position:absolute;top:50%;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;box-sizing:border-box}}
.track u{{position:absolute;top:0;bottom:0;border-left:2px dashed {LILAC};text-decoration:none}}
.axis{{position:relative;height:20px;font-size:14px;color:{MUTED};font-weight:600;letter-spacing:0;text-transform:none}}
.axis span{{position:absolute;transform:translateX(-50%);white-space:nowrap}}
.badge{{display:inline-block;font-size:13px;font-weight:800;color:{PURPLE_DARK};background:{PURPLE_BG};border-radius:7px;padding:2px 7px;margin-left:8px;vertical-align:2px;letter-spacing:.03em}}
.sbar{{flex:1;height:18px;border-radius:9px;background:#f1f0f8;overflow:hidden}}
.sbar i{{display:block;height:100%;border-radius:9px}}
.trow{{display:grid;gap:18px;align-items:center;font-size:18px;padding:8px 0;border-top:1.5px solid {LINE}}}
.trow.head{{font-size:14px;font-weight:700;color:{MUTED};text-transform:uppercase;letter-spacing:.06em;border-top:0;padding-bottom:4px}}
.r{{text-align:right}}
.card.purple .trow,.card.teal .trow,.card.coral .trow{{border-top-color:#ffffff99}}
.card.purple .sbar,.card.teal .sbar,.card.coral .sbar{{background:#ffffffcc}}
"""
CSS += TRACK_CSS

"""16:9 cover image for the first X post: title, three key numbers and thumbnails of the three posters.

    .venv/bin/python promo/cover.py   ->  promo/x-0-cover.png (2400x1350)
"""

import json
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "posters"))
import style  # noqa: E402
from style import AUTHOR, CORAL_BG, CORAL_DARK, PURPLE, PURPLE_BG, PURPLE_DARK, TEAL_BG, TEAL_DARK, document, render  # noqa: E402

SCORES = json.loads((ROOT / "iclr2027-scores" / "stats.json").read_text())
REBUTTAL = json.loads((ROOT / "iclr2027-rebuttal" / "stats.json").read_text())
O, R = SCORES["overall"], REBUTTAL["overall"]
GAIN = R["mean_final"] - R["mean_kept_initial"]
SELECTION = R["mean_kept_initial"] - R["mean_initial"]
RAISED = REBUTTAL["raised"]

W, H = 1600, 900
THUMBS = [ROOT / "posters" / "out" / f"iclr2027-{n}.png" for n in ("scores", "institutions", "rebuttal")]


def stat(bg: str, fg: str, value: str, label: str) -> str:
    return f'<div class="stat" style="background:{bg}"><b style="color:{fg}">{value}</b><span>{label}</span></div>'


def main() -> None:
    stats = "".join([
        stat(PURPLE_BG, PURPLE_DARK, f"{SCORES['ratings']['2'] / O['reviews'] * 100:.0f}%", "of all 125,304 ratings were a 2"),
        stat(CORAL_BG, CORAL_DARK, f"{SELECTION / (SELECTION + GAIN) * 100:.0f}%", "of the post-rebuttal jump is just withdrawals"),
        stat(TEAL_BG, TEAL_DARK, f"{RAISED['all:1'] / RAISED['all:0']:.0f}×", "more raises when reviewers join the discussion"),
    ])
    thumbs = "".join(f'<div class="thumb" style="transform:rotate({r}deg) translateY({y}px)"><img src="{p.as_uri()}"></div>'
                     for p, r, y in zip(THUMBS, (-4, 0, 4), (30, 0, 30)))
    body = f"""<div class="cover">
  <div class="left">
    <div class="kick">ICLR 2027 · Peer review in numbers</div>
    <h1>{O['submissions']:,} papers,<br>three posters</h1>
    <div class="stats">{stats}</div>
    <div class="by">by <b>{AUTHOR}</b> · {style.REPO.removeprefix('https://')}</div>
  </div>
  <div class="right">{thumbs}</div>
</div>"""
    css = f"""
html,body{{width:{W}px}}
.page{{padding:0}}
.cover{{width:{W}px;height:{H}px;display:grid;grid-template-columns:760px 1fr;overflow:hidden;background:#fafaff}}
.left{{padding:70px 0 60px 72px;display:flex;flex-direction:column}}
.kick{{font-size:22px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:{PURPLE}}}
h1{{font-size:76px;font-weight:800;letter-spacing:-.03em;line-height:1.02;margin:16px 0 34px}}
.stats{{display:flex;flex-direction:column;gap:14px}}
.stat{{display:flex;align-items:center;gap:22px;border-radius:22px;padding:16px 26px}}
.stat b{{font-size:46px;font-weight:800;letter-spacing:-.02em;min-width:120px}}
.stat span{{font-size:21px;line-height:1.3;color:#4a4766}}
.by{{margin-top:auto;font-size:19px;color:#7d7a96}}
.by b{{color:#1e1b3a}}
.right{{position:relative;display:flex;gap:18px;align-items:flex-start;padding:70px 40px 0 10px}}
.thumb{{flex:1;height:820px;border-radius:22px;overflow:hidden;border:2px solid #e6e4f2;background:#fff;box-shadow:0 18px 40px rgba(60,52,137,.18)}}
.thumb img{{width:100%;display:block}}
"""
    png = render(document("ICLR 2027 cover", body, css), "x-0-cover")
    out = ROOT / "promo" / "x-0-cover.png"
    Image.open(png).convert("RGB").resize((2400, 1350), Image.LANCZOS).save(out, optimize=True)
    for suffix in (".png", ".pdf", ".html"):
        (png.with_suffix(suffix)).unlink(missing_ok=True)
    print(out, round(out.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()

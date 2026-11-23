"""Minimal results poster built with style.py. Copy both files, replace DATA with your stats, run:

    python example_poster.py            # writes out/example.{html,png,pdf}

Shows every common building block once: hero, KPI row, bar card, dot-track table, arrow table, stacked band bars, footer.
"""

from style import (CORAL, PURPLE, TEAL, arrow_track, axis, document, dot_track, esc, footer, hbars, hero, kpis, name_cell, pct, ramp,
                   render, share_bar)

# Replace with numbers computed upstream (stats.json). Never type numbers into the poster by hand.
DATA = {
    "total": 12480,
    "responses": 38211,
    "ratings": {"5": 1210, "4": 9650, "3": 17402, "2": 7801, "1": 2148},
    "groups": [  # name, code, share of items, mean, standard error, mean before, mean after, band counts (low -> high)
        {"name": "Northfield University", "code": "GB", "weight": 812, "mean": 3.21, "se": 0.03, "before": 3.05, "after": 3.27, "bands": [40, 120, 300, 260, 92]},
        {"name": "Lakeside Institute of Technology", "code": "US", "weight": 655, "mean": 3.08, "se": 0.04, "before": 2.98, "after": 3.12, "bands": [55, 140, 250, 170, 40]},
        {"name": "Harbor Research Lab", "code": "SG", "weight": 410, "mean": 3.34, "se": 0.05, "before": 3.20, "after": 3.41, "bands": [10, 50, 150, 140, 60]},
        {"name": "Eastgate College", "code": "DE", "weight": 233, "mean": 2.91, "se": 0.07, "before": 2.85, "after": 2.95, "bands": [30, 60, 90, 43, 10]},
    ],
}


def ratings_card() -> str:
    rows = [(k, v) for k, v in DATA["ratings"].items()]
    top = max(DATA["ratings"], key=DATA["ratings"].get)
    return f"""<div class="card purple"><h2>What people gave</h2><p class="sub">All {DATA['responses']:,} ratings on a 1–5 scale</p>
{hbars(rows, 654, DATA['responses'], PURPLE)}
<p class="note"><b>{pct(DATA['ratings'][top] / DATA['responses'], 0)} of ratings were a {top}.</b> One sentence of takeaway under every chart.</p></div>"""


def groups_card() -> str:
    lo, hi = 2.7, 3.5
    cols = "grid-template-columns:1fr 130px 56px 190px"
    top = max(g["weight"] for g in DATA["groups"]) / DATA["total"]
    head = f'<div class="trow head" style="{cols}"><span>Group</span><span>Share</span><span class="r">Mean</span>{axis(lo, hi, [2.8, 3.1, 3.4])}</div>'
    body = "".join(
        f"""<div class="trow" style="{cols}">{name_cell(g['name'], g['code'])}
<div style="display:flex;align-items:center;gap:10px">{share_bar(g['weight'] / DATA['total'], top, TEAL)}<b style="min-width:52px">{pct(g['weight'] / DATA['total'])}</b></div>
<b class="r">{g['mean']:.2f}</b>{dot_track(g['mean'], g['se'], lo, hi, TEAL, ref=3.1)}</div>""" for g in DATA["groups"])
    return f'<div class="card teal"><h2>Groups</h2><p class="sub">Share of items and mean with its 95% range. Dashed line: overall mean.</p>{head}{body}</div>'


def change_card() -> str:
    lo, hi = 2.7, 3.5
    cols = "grid-template-columns:1fr 260px 80px"
    head = f'<div class="trow head" style="{cols}"><span>Group</span>{axis(lo, hi, [2.8, 3.0, 3.2, 3.4])}<span class="r">Change</span></div>'
    body = "".join(
        f"""<div class="trow" style="{cols}">{name_cell(g['name'], g['code'])}{arrow_track(g['before'], g['after'], lo, hi, CORAL)}
<b class="r">{g['after'] - g['before']:+.2f}</b></div>""" for g in DATA["groups"])
    return f'<div class="card coral"><h2>Before and after</h2><p class="sub">Hollow dot: before. Filled dot: after.</p>{head}{body}</div>'


def bands_card() -> str:
    shades = ramp(5)
    rows = []
    for g in DATA["groups"]:
        n = sum(g["bands"])
        segs = "".join(f'<i style="width:{b / n * 100:.2f}%;background:{shades[k]}"></i>' for k, b in enumerate(g["bands"]) if b)
        rows.append(f'<div class="trow" style="grid-template-columns:360px 1fr">{name_cell(g["name"], g["code"])}<span class="stack">{segs}</span></div>')
    legend = "".join(f'<span><i style="background:{shades[k]}"></i>{k + 1}</span>' for k in range(5))
    return (f'<section class="card"><h2>How each group rated</h2><p class="sub">Each bar splits a group\'s ratings from 1 (light) to 5 (dark)</p>'
            f'<div class="legend" style="margin-bottom:16px">{legend}</div>{"".join(rows)}</section>')


EXTRA = """
.stack{display:flex;height:26px;border-radius:13px;overflow:hidden;gap:2px;background:#fff}
.stack i{display:block;height:100%}
"""


def main() -> None:
    body = "".join([
        hero("Example · Survey results", "How 12,480 people<br>rated the course", "One sentence on what the data is, where it came from and when.", "Jan 1, 2027"),
        kpis([("purple", f"{DATA['total']:,}", "people answered"), ("teal", f"{DATA['responses']:,}", "ratings in total"),
              ("coral", "3.12", "average rating"), ("purple", pct(0.087), "gave the top rating")]),
        f'<section class="row" style="grid-template-columns:1fr 1fr">{ratings_card()}{groups_card()}</section>',
        f'<section class="row" style="grid-template-columns:1fr 1fr">{change_card()}<div class="card"><h2>Method</h2><p class="sub">'
        f'{esc("Explain sampling, weighting and caveats here: who is missing, what the ranges mean, what not to over-read.")}</p></div></section>',
        bands_card(),
        footer("<b>Data:</b> where it comes from, snapshot date, and any filters applied."),
    ])
    render(document("Example poster", body, EXTRA), "example")


if __name__ == "__main__":
    main()

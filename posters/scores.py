"""ICLR 2027 review scores poster, soft academic style.

    .venv/bin/python posters/scores.py   ->  posters/out/iclr2027-scores.{png,pdf,html}
"""

import json
import pathlib

from style import (CORAL, CORAL_DARK, INK, LILAC, LINE, MUTED, PURPLE, PURPLE_DARK, SOFT, TEAL, TEAL_DARK, document, esc, footer,
                   hero, pct, ramp, render)

DATA = pathlib.Path(__file__).resolve().parent.parent / "iclr2027-scores" / "stats.json"
S = json.loads(DATA.read_text())
O = S["overall"]
BANDS = [1 + k / 3 for k in range(10)]  # band k covers averages from this value up to the next
SHADES = ramp(10)

SHORT = {
    "foundation or frontier models, including LLMs": "Foundation and frontier models, LLMs",
    "applications to computer vision, audio, language, and other modalities": "Applications: vision, audio, language",
    "alignment, fairness, safety, privacy, and societal considerations": "Alignment, fairness, safety, privacy",
    "datasets and benchmarks": "Datasets and benchmarks",
    "generative models": "Generative models",
    "reinforcement learning": "Reinforcement learning",
    "applications to robotics, autonomy, planning": "Applications: robotics and planning",
    "unsupervised, self-supervised, semi-supervised, and supervised representation learning": "Representation learning",
    "applications to physical sciences (physics, chemistry, biology, etc.)": "Applications: physical sciences",
    "interpretability and explainable AI": "Interpretability and explainable AI",
    "optimization": "Optimization",
    "learning theory": "Learning theory",
    "transfer learning, meta learning, and lifelong learning": "Transfer, meta and lifelong learning",
    "learning on time series and dynamical systems": "Time series and dynamical systems",
    "other topics in machine learning (i.e., none of the above)": "Other topics in machine learning",
    "learning on graphs and other geometries & topologies": "Graphs, geometry and topology",
    "probabilistic methods (Bayesian methods, variational inference, sampling, UQ, etc.)": "Probabilistic methods",
    "applications to neuroscience & cognitive science": "Applications: neuroscience and cognition",
    "infrastructure, software libraries, hardware, systems, etc.": "Infrastructure, software, hardware",
    "neurosymbolic & hybrid AI systems (physics-informed, logic & formal reasoning, etc.)": "Neurosymbolic and hybrid AI",
    "causal reasoning": "Causal reasoning",
}


def kpis() -> str:
    tiles = [
        ("purple", f"{O['submissions']:,}", "papers under review when scores came out"),
        ("teal", f"{O['reviews']:,}", f"reviews, about {O['reviews'] / O['submissions']:.1f} per paper"),
        ("coral", f"{O['median']:.2f}", f"median paper average<br>(middle half: {O['q1']:.2f}–{O['q3']:.2f})"),
        ("purple", pct(O["above"]["2.67"]), "of papers average 2.67 or more"),
    ]
    cells = "".join(f'<div class="card kpi {c}"><div class="v">{v}</div><div class="l">{l}</div></div>' for c, v, l in tiles)
    return f'<section class="row" style="grid-template-columns:repeat(4,1fr)">{cells}</section>'


def hbars(rows: list, width: int, total: float, colour: str, label_w: int = 70, row_h: int = 54) -> str:
    """Horizontal rounded bars. rows = [(label, count)]."""
    top = max(v for _, v in rows)
    room = width - label_w - 190
    out = [f'<svg width="{width}" height="{len(rows) * row_h}" viewBox="0 0 {width} {len(rows) * row_h}">']
    for i, (label, v) in enumerate(rows):
        y = i * row_h
        w = max(6, room * v / top)
        out.append(f'<text x="0" y="{y + 30}" font-size="22" font-weight="700" fill="{INK}">{esc(label)}</text>')
        out.append(f'<rect x="{label_w}" y="{y + 8}" width="{room}" height="32" rx="16" fill="#ffffff" opacity=".7"/>')
        out.append(f'<rect x="{label_w}" y="{y + 8}" width="{w:.1f}" height="32" rx="16" fill="{colour}"/>')
        out.append(f'<text x="{label_w + w + 14:.1f}" y="{y + 31}" font-size="20" font-weight="700" fill="{INK}">{pct(v / total)}</text>')
        out.append(f'<text x="{width}" y="{y + 31}" font-size="18" fill="{SOFT}" text-anchor="end">{v:,}</text>')
    out.append("</svg>")
    return "".join(out)


def ratings_card() -> str:
    rows = [(str(k), S["ratings"][str(k)]) for k in (4, 3, 2, 1)]
    two = S["ratings"]["2"] / O["reviews"]
    return f"""<div class="card purple"><h2>What reviewers gave</h2>
<p class="sub">All {O['reviews']:,} ratings on the 1–4 scale</p>{hbars(rows, 654, O['reviews'], PURPLE)}
<p class="note"><b>{pct(two, 0)} of all ratings were a 2.</b> Only {pct(S['ratings']['4'] / O['reviews'])} were a 4.</p></div>"""


def per_paper_card() -> str:
    rows = [(k, v) for k, v in S["per_submission"].items()]
    three = S["per_submission"]["3"] / O["submissions"]
    return f"""<div class="card teal"><h2>Reviews per paper</h2>
<p class="sub">How many ratings each paper had at release</p>{hbars(rows, 654, O['submissions'], TEAL, row_h=40)}
<p class="note"><b>{pct(three, 0)} of papers got exactly three reviews,</b> so most averages are multiples of ⅓.</p></div>"""


def histogram_card() -> str:
    width, height, left, bottom = 1412, 470, 70, 70
    plot_w, plot_h = width - left - 20, height - bottom - 30
    x = lambda v: left + (v - 1) / 3 * plot_w
    top = max(e["count"] for e in S["exact"])
    y = lambda c: 30 + plot_h * (1 - c / 13000)
    out = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for c in range(0, 13001, 2000):
        out.append(f'<line x1="{left}" x2="{width - 20}" y1="{y(c):.1f}" y2="{y(c):.1f}" stroke="{LINE}" stroke-width="1.5"/>')
        out.append(f'<text x="{left - 14}" y="{y(c) + 6:.1f}" font-size="17" fill="{MUTED}" text-anchor="end">{c // 1000}k</text>' if c else
                   f'<text x="{left - 14}" y="{y(c) + 6:.1f}" font-size="17" fill="{MUTED}" text-anchor="end">0</text>')
    cut = x(8 / 3) - 12
    out.append(f'<rect x="{cut:.1f}" y="30" width="{width - 20 - cut:.1f}" height="{plot_h}" rx="18" fill="{CORAL}" opacity=".08"/>')
    out.append(f'<text x="{cut + 22:.1f}" y="70" font-size="22" font-weight="800" fill="{CORAL_DARK}">Top {pct(O["above"]["2.67"], 0)}: 2.67 and up</text>')
    out.append(f'<text x="{cut + 22:.1f}" y="98" font-size="18" fill="{CORAL_DARK}">Top {pct(O["above"]["3.00"], 0)} reach 3.00</text>')
    for e in S["exact"]:
        v, n = e["value"], e["count"]
        colour = CORAL if v >= 8 / 3 - 1e-6 else (PURPLE if n >= 500 else LILAC)
        h = plot_h * n / 13000
        out.append(f'<rect x="{x(v) - 9:.1f}" y="{30 + plot_h - h:.1f}" width="18" height="{max(h, 2):.1f}" rx="6" fill="{colour}"/>')
        if n >= 3000:
            out.append(f'<text x="{x(v):.1f}" y="{30 + plot_h - h - 12:.1f}" font-size="18" font-weight="700" fill="{INK}" text-anchor="middle">{n:,}</text>')
    for v in (1, 4 / 3, 5 / 3, 2, 7 / 3, 8 / 3, 3, 10 / 3, 11 / 3, 4):
        out.append(f'<text x="{x(v):.1f}" y="{height - bottom + 32}" font-size="19" font-weight="600" fill="{SOFT}" text-anchor="middle">{v:.2f}</text>')
    for v, name in ((O["q1"], "Q1"), (O["median"], "median"), (O["q3"], "Q3")):
        out.append(f'<text x="{x(v):.1f}" y="{height - bottom + 60}" font-size="16" font-weight="700" fill="{PURPLE_DARK}" text-anchor="middle">{name}</text>')
    out.append("</svg>")
    return f"""<section class="card"><h2>Where paper averages land</h2>
<p class="sub">Number of papers at each exact average rating. Averages bunch up on thirds because most papers have three reviews.</p>
{''.join(out)}</section>"""


def rank_card() -> str:
    rows = [e for e in S["exact"] if e["count"] >= 200]
    out = []
    for e in rows:
        share = e["top_to"]
        out.append(f"""<div style="display:grid;grid-template-columns:84px 1fr 96px;align-items:center;gap:16px;height:44px">
<b style="font-size:24px">{e['value']:.2f}</b>
<div style="height:24px;border-radius:12px;background:#fff;opacity:.95;position:relative">
<div style="position:absolute;inset:0 auto 0 0;width:{share * 100:.1f}%;border-radius:12px;background:{CORAL}"></div></div>
<span style="font-size:20px;font-weight:700;text-align:right">top {pct(share, 0) if share >= .1 else pct(share)}</span></div>""")
    return f"""<div class="card coral"><h2>Find your rank</h2>
<p class="sub">If your paper's average is at least this, this share of all papers is at or above you</p>{''.join(out)}</div>"""


def cutoffs_card() -> str:
    p = S["percentiles"]
    items = [("Top 1%", "99"), ("Top 5%", "95"), ("Top 10%", "90"), ("Top 25%", "75"), ("Middle", "50"), ("Bottom 25%", "25"), ("Bottom 10%", "10")]
    out = "".join(f"""<div style="display:flex;justify-content:space-between;align-items:center;background:#fff;border-radius:18px;padding:14px 22px">
<span style="font-size:21px;color:{TEAL_DARK};font-weight:700">{label}</span><b style="font-size:28px">{p[k]:.2f}</b></div>""" for label, k in items)
    return f"""<div class="card teal"><h2>Score cutoffs</h2>
<p class="sub">Paper average at each percentile</p><div style="display:flex;flex-direction:column;gap:12px">{out}</div>
<p class="note">The 90th and 95th percentile are the same value: <b>a 2.67 already puts you in the top {pct(O['above']['2.67'], 0)}.</b></p></div>"""


def areas_card() -> str:
    areas = sorted(S["areas"].items(), key=lambda kv: -kv[1]["mean"])
    rows = [("All papers", O, True)] + [(SHORT.get(k, k), v, False) for k, v in areas]
    head = f"""<div class="arow head"><span>Primary area</span><span style="text-align:right">Papers</span><span>Share of papers in each average-rating band</span>
<span style="text-align:right">Mean</span><span style="text-align:right">2.67+</span></div>"""
    body = []
    for name, a, total in rows:
        n = sum(a["bands"])
        segs = "".join(f'<i style="width:{b / n * 100:.3f}%;background:{SHADES[k]}"></i>' for k, b in enumerate(a["bands"]) if b)
        body.append(f"""<div class="arow{' total' if total else ''}"><span>{esc(name)}</span><span style="text-align:right">{a['submissions']:,}</span>
<span class="stack">{segs}</span><b style="text-align:right">{a['mean']:.2f}</b><b style="text-align:right;color:{CORAL_DARK}">{pct(a['above']['2.67'])}</b></div>""")
    legend = "".join(f'<span><i style="background:{SHADES[k]}"></i>{BANDS[k]:.2f}{"+" if k == 9 else ""}</span>' for k in range(10))
    return f"""<section class="card"><h2>Areas, ranked by average score</h2>
<p class="sub">Each bar splits an area's papers by their average rating, from the lowest band (light) to the highest (dark)</p>
<div class="legend" style="margin-bottom:20px">{legend}</div>{head}{''.join(body)}</section>"""


EXTRA = f"""
.arow{{display:grid;grid-template-columns:430px 90px 1fr 80px 90px;gap:22px;align-items:center;font-size:19px;padding:9px 0;border-top:1.5px solid {LINE}}}
.arow.head{{font-size:15px;font-weight:700;color:{MUTED};text-transform:uppercase;letter-spacing:.06em;border-top:0}}
.arow.total{{font-weight:800;background:#f4f3fd;border-radius:14px;padding:12px 14px;margin:0 -14px 6px;border-top:0}}
.stack{{display:flex;height:26px;border-radius:13px;overflow:hidden;gap:2px;background:#fff}}
.stack i{{display:block;height:100%}}
"""


def main() -> None:
    lede = (f"Every review rating on OpenReview the day scores were released (Nov 6, 2026). "
            f"A paper's average is the mean of its ratings on ICLR's 1–4 scale.")
    body = "".join([
        hero("ICLR 2027 · Review scores", f"How reviewers scored<br>{O['submissions']:,} papers", lede, "Nov 24, 2026"),
        kpis(),
        f'<section class="row" style="grid-template-columns:1fr 1fr">{ratings_card()}{per_paper_card()}</section>',
        histogram_card(),
        f'<section class="row" style="grid-template-columns:1.35fr 1fr">{rank_card()}{cutoffs_card()}</section>',
        areas_card(),
        footer("<b>Data:</b> OpenReview, snapshot Nov 6, 2026, open submissions only. Bands are 1.00, 1.33, 1.67 … 4.00, each running up to the next."),
    ])
    render(document("ICLR 2027 review scores", body, EXTRA), "iclr2027-scores")


if __name__ == "__main__":
    main()

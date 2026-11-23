"""ICLR 2027 rebuttal poster, soft academic style.

    .venv/bin/python posters/rebuttal.py   ->  posters/out/iclr2027-rebuttal.{png,pdf,html}
"""

import collections
import json
import pathlib

from scores import SHORT
from style import (CORAL, CORAL_BG, CORAL_DARK, INK, LILAC, LINE, MUTED, PURPLE, PURPLE_DARK, SOFT, TEAL, TEAL_BG, TEAL_DARK, arrow_track,
                   axis, document, esc, footer, hero, name_cell, pct, render)

HERE = pathlib.Path(__file__).resolve().parent.parent / "iclr2027-rebuttal"
S = json.loads((HERE / "stats.json").read_text())
NAMES = {k: v["name"] for k, v in json.loads((HERE / "countries.json").read_text()).items()}
O = S["overall"]
OPEN = O["status"]["open"]
GAIN = O["mean_final"] - O["mean_kept_initial"]
SELECTION = O["mean_kept_initial"] - O["mean_initial"]


def kpis() -> str:
    tiles = [
        ("purple", f"+{GAIN:.2f}", f"average rating gain on the {OPEN:,} papers that stayed in"),
        ("teal", f"{O['reviews_raised']:,}", f"reviews raised, against only {O['reviews_lowered']:,} lowered"),
        ("coral", f"{O['status']['withdrawn']:,}", f"papers withdrawn ({pct(O['status']['withdrawn'] / O['base'])} of all)"),
        ("purple", pct(O["papers_rebuttal_open"], 0), "of papers still open had an author response"),
    ]
    cells = "".join(f'<div class="card kpi {c}"><div class="v">{v}</div><div class="l">{l}</div></div>' for c, v, l in tiles)
    return f'<section class="row" style="grid-template-columns:repeat(4,1fr)">{cells}</section>'


def jump_card() -> str:
    lo, hi = 1.95, 2.40
    p = lambda v: (v - lo) / (hi - lo) * 100
    steps = [
        ("Nov 6 average, all papers", O["mean_initial"], None, LILAC, f"{O['mean_initial']:.3f}"),
        ("Withdrawn papers leave", O["mean_kept_initial"], O["mean_initial"], CORAL, f"+{SELECTION:.3f}"),
        ("Reviewers change ratings", O["mean_final"], O["mean_kept_initial"], PURPLE, f"+{GAIN:.3f}"),
        ("Nov 19 average, open papers", O["mean_final"], None, LILAC, f"{O['mean_final']:.3f}"),
    ]
    rows = []
    for label, end, start, colour, text in steps:
        a = p(start) if start is not None else 0
        rows.append(f"""<div style="display:grid;grid-template-columns:250px 1fr;gap:18px;align-items:center;height:62px">
<span style="font-size:19px;font-weight:700">{label}</span><div style="position:relative;height:38px">
<i style="position:absolute;left:{a:.2f}%;width:{p(end) - a:.2f}%;top:0;bottom:0;border-radius:19px;background:{colour}"></i>
<b style="position:absolute;left:calc({p(end):.2f}% + 12px);top:7px;font-size:20px">{text}</b></div></div>""")
    share = SELECTION / (SELECTION + GAIN)
    return f"""<div class="card purple"><h2>Where the score jump came from</h2>
<p class="sub">The average rose from {O['mean_initial']:.2f} to {O['mean_final']:.2f}. Bars start at {lo:.2f}, not zero.</p>{''.join(rows)}
<p class="note"><b>About {pct(share, 0)} of the rise is just weak papers leaving:</b> withdrawn papers averaged {O['mean_withdrawn_initial']:.2f}
against {O['mean_kept_initial']:.2f} for those that stayed.</p></div>"""


def moves_card() -> str:
    grid = collections.defaultdict(int)
    for t in S["transitions"]:
        grid[t["before"], t["after"]] = t["reviews"]
    cells = [f'<span></span>' + "".join(f'<span class="mh">→ {a}</span>' for a in (1, 2, 3, 4))]
    for b in (1, 2, 3, 4):
        total = sum(grid[b, a] for a in (1, 2, 3, 4))
        row = [f'<span class="mh" style="text-align:left">{b} →</span>']
        for a in (1, 2, 3, 4):
            s = grid[b, a] / total
            if a == b:
                bg, fg = "#ffffff", SOFT
            elif a > b:
                bg, fg = f"rgba(29,158,117,{0.15 + 0.85 * min(1, s / 0.2):.2f})", "#fff" if s > 0.1 else TEAL_DARK
            else:
                bg, fg = f"rgba(216,90,48,{0.15 + 0.85 * min(1, s / 0.2):.2f})", "#fff" if s > 0.1 else CORAL_DARK
            row.append(f'<span class="mc" style="background:{bg};color:{fg}"><b>{pct(s)}</b><small>{grid[b, a]:,}</small></span>')
        cells.append("".join(row))
    return f"""<div class="card teal"><h2>How each review moved</h2>
<p class="sub">Rows: rating on Nov 6. Columns: rating on Nov 19. Each row adds up to 100%.</p>
<div class="moves">{''.join(cells)}</div>
<p class="note"><b>Reviews starting at 2 moved most:</b> {pct(grid[2, 3] / sum(grid[2, a] for a in (1, 2, 3, 4)), 0)} went up to a 3.
Downgrades were rare everywhere.</p></div>"""


def talk_card() -> str:
    r = S["raised"]
    rows = []
    for k in ("1", "2", "3"):
        on, off = r[f"{k}:1"], r[f"{k}:0"]
        rows.append(f"""<div style="display:grid;grid-template-columns:120px 1fr;gap:16px;align-items:center;margin-bottom:16px">
<span style="font-size:19px;font-weight:700">Started at {k}</span><div>
<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px"><div class="sbar" style="height:24px"><i style="width:{on / .4 * 100:.1f}%;background:{CORAL}"></i></div><b style="min-width:54px">{pct(on, 0)}</b></div>
<div style="display:flex;align-items:center;gap:12px"><div class="sbar" style="height:24px"><i style="width:{off / .4 * 100:.1f}%;background:#c9c6d9"></i></div><b style="min-width:54px;color:{SOFT}">{pct(off, 0)}</b></div></div></div>""")
    legend = f'<div class="legend" style="margin-bottom:18px"><span><i style="background:{CORAL}"></i>Reviewer joined the discussion</span><span><i style="background:#c9c6d9"></i>Reviewer stayed silent</span></div>'
    rep = S["replied"]
    return f"""<div class="card coral"><h2>Talking helps</h2>
<p class="sub">Share of reviews raised, by whether the reviewer posted in the discussion</p>{legend}{''.join(rows)}
<p class="note"><b>Engaged reviewers raised {r['all:1'] / r['all:0']:.0f}× as often</b> ({pct(r['all:1'], 0)} vs {pct(r['all:0'], 0)}).
But the harshest joined least: {pct(rep['1'], 0)} of reviewers who gave a 1, against {pct(rep['3'], 0)} who gave a 3.</p></div>"""


def withdraw_card() -> str:
    total, gone = collections.Counter(), collections.Counter()
    for f in S["flows"]:
        total[f["initial"]] += f["papers"]
        if f["outcome"] == "withdrawn":
            gone[f["initial"]] += f["papers"]
    keys = sorted((k for k in total if total[k] >= 300), key=float)
    rows = "".join(f"""<div style="display:grid;grid-template-columns:64px 1fr 70px;gap:14px;align-items:center;height:40px">
<b style="font-size:20px">{float(k):.2f}</b><div class="sbar" style="height:24px"><i style="width:{gone[k] / total[k] / .45 * 100:.1f}%;background:{PURPLE}"></i></div>
<b class="r" style="font-size:19px">{pct(gone[k] / total[k], 0)}</b></div>""" for k in keys)
    low = gone["1.0000"] / total["1.0000"]
    return f"""<div class="card purple"><h2>Who withdrew</h2>
<p class="sub">Share of papers withdrawn by Nov 19, by their Nov 6 average (averages with 300+ papers)</p>{rows}
<p class="note"><b>{pct(low, 0)} of papers averaging 1.00 were withdrawn,</b> against {pct(O['status']['withdrawn'] / O['base'], 0)} overall.</p></div>"""


def histogram_card() -> str:
    width, height, left, bottom, top_pad = 1412, 440, 70, 50, 24
    pw, ph = width - left - 20, height - bottom - top_pad
    x = lambda v: left + (v - 1) / 3 * pw
    ymax = 13000
    y = lambda c: top_pad + ph * (1 - c / ymax)
    out = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for c in range(0, ymax + 1, 2000):
        out.append(f'<line x1="{left}" x2="{width - 20}" y1="{y(c):.1f}" y2="{y(c):.1f}" stroke="{LINE}" stroke-width="1.5"/>'
                   f'<text x="{left - 12}" y="{y(c) + 6:.1f}" font-size="17" fill="{MUTED}" text-anchor="end">{f"{c // 1000}k" if c else 0}</text>')
    for values, dx, colour in ((S["initial_values"], -10, LILAC), (S["final_values"], 10, PURPLE)):
        for k, n in values.items():
            v = float(k)
            h = ph * n / ymax
            out.append(f'<rect x="{x(v) + dx - 9:.1f}" y="{y(n):.1f}" width="18" height="{max(h, 2):.1f}" rx="6" fill="{colour}"/>')
    for v in (1, 4 / 3, 5 / 3, 2, 7 / 3, 8 / 3, 3, 10 / 3, 11 / 3, 4):
        out.append(f'<text x="{x(v):.1f}" y="{height - bottom + 32}" font-size="19" font-weight="600" fill="{SOFT}" text-anchor="middle">{v:.2f}</text>')
    out.append("</svg>")
    legend = (f'<div class="legend" style="margin-bottom:14px"><span><i style="background:{LILAC}"></i>Nov 6, all {O["base"]:,} papers</span>'
              f'<span><i style="background:{PURPLE}"></i>Nov 19, {OPEN:,} papers still open</span></div>')
    return f"""<section class="card"><h2>Paper averages, before and after</h2>
<p class="sub">Number of papers at each average rating. The median moved from {O['median_initial']:.2f} to {O['median_final']:.2f};
{O['papers_changed']:,} open papers changed their average.</p>{legend}{''.join(out)}</section>"""


def daily_card() -> str:
    days = [d for d in S["daily"] if d["day"] < O["after"]]
    width, height, left, bottom = 1412, 360, 70, 50
    pw, ph = width - left - 20, height - bottom - 20
    top = max(d["authors"] + d["reviewer"] + d["chair"] for d in days)
    ymax = 70000
    slot = pw / len(days)
    y = lambda c: 20 + ph * (1 - c / ymax)
    out = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for c in range(0, ymax + 1, 10000):
        out.append(f'<line x1="{left}" x2="{width - 20}" y1="{y(c):.1f}" y2="{y(c):.1f}" stroke="{LINE}" stroke-width="1.5"/>'
                   f'<text x="{left - 12}" y="{y(c) + 6:.1f}" font-size="17" fill="{MUTED}" text-anchor="end">{f"{c // 1000}k" if c else 0}</text>')
    for i, d in enumerate(days):
        cx = left + slot * (i + 0.5)
        base = 0
        for key, colour in (("authors", PURPLE), ("reviewer", TEAL), ("chair", CORAL)):
            n = d[key]
            if n:
                out.append(f'<rect x="{cx - 26:.1f}" y="{y(base + n):.1f}" width="52" height="{max(ph * n / ymax - 2, 1):.1f}" rx="7" fill="{colour}"/>')
            base += n
        out.append(f'<text x="{cx:.1f}" y="{height - bottom + 30}" font-size="17" font-weight="600" fill="{SOFT}" text-anchor="middle">Nov {int(d["day"][-2:])}</text>')
        if base == top:
            out.append(f'<text x="{cx:.1f}" y="{y(base) - 12:.1f}" font-size="18" font-weight="800" fill="{INK}" text-anchor="middle">{base:,}</text>')
    out.append("</svg>")
    c = O["comments"]
    legend = (f'<div class="legend" style="margin-bottom:14px"><span><i style="background:{PURPLE}"></i>Authors ({c["authors"]:,})</span>'
              f'<span><i style="background:{TEAL}"></i>Reviewers ({c["reviewer"]:,})</span><span><i style="background:{CORAL}"></i>Area chairs ({c["chair"]:,})</span></div>')
    return f"""<section class="card"><h2>The discussion, day by day</h2>
<p class="sub">Comments posted per day (AoE). Authors wrote {c['authors'] / c['reviewer']:.1f} comments for every reviewer comment, and both peaked on the last day.</p>
{legend}{''.join(out)}</section>"""


def areas_card() -> str:
    lo, hi, ticks = 1.95, 2.55, [2.0, 2.1, 2.2, 2.3, 2.4, 2.5]
    rows = sorted(S["areas"], key=lambda a: -a["gain"])
    cols = "grid-template-columns:400px 80px 96px 96px 1fr 84px"
    head = (f'<div class="trow head" style="{cols}"><span>Primary area</span><span class="r">Papers</span><span class="r">Withdrawn</span>'
            f'<span class="r">Rebuttal</span>{axis(lo, hi, ticks)}<span class="r">Change</span></div>')
    body = "".join(
        f"""<div class="trow" style="{cols}"><span style="font-weight:600">{esc(SHORT.get(a['area'], a['area']))}</span><span class="r">{a['papers']:,}</span>
<span class="r">{pct(a['withdrawn'], 0)}</span><span class="r">{pct(a['rebuttal'], 0)}</span>{arrow_track(a['kept_initial'], a['final'], lo, hi, PURPLE)}
<b class="r" style="color:{TEAL_DARK}">+{a['gain']:.2f}</b></div>""" for a in rows)
    legend = (f'<div class="legend" style="margin-bottom:16px"><span><i style="background:#fff;border:3px solid {PURPLE};border-radius:50%"></i>Nov 6 average</span>'
              f'<span><i style="background:{PURPLE};border-radius:50%"></i>Nov 19 average</span><span>Both for papers still open on Nov 19</span></div>')
    return f"""<section class="card"><h2>Research areas, before and after</h2>
<p class="sub">Sorted by how much the average moved. Areas really do differ: generative models gained about 1.5× as much as neurosymbolic AI.</p>
{legend}{head}{body}</section>"""


def group_card(title: str, sub: str, rows: list, name, code, tone: str, colour: str) -> str:
    lo, hi, ticks = 2.05, 2.65, [2.1, 2.3, 2.5]
    cols = "grid-template-columns:1fr 74px 220px 64px"
    head = f'<div class="trow head" style="{cols}"><span>{sub}</span><span class="r">Withdr.</span>{axis(lo, hi, ticks)}<span class="r">Change</span></div>'
    body = "".join(
        f"""<div class="trow" style="{cols}">{name_cell(name(r), code(r))}<span class="r">{pct(r['withdrawn'], 0)}</span>
{arrow_track(r['kept_initial'], r['final'], lo, hi, colour)}<b class="r">+{r['gain']:.2f}</b></div>""" for r in rows)
    return f'<div class="card {tone}"><h2>{title}</h2><p class="sub">Nov 6 → Nov 19 average of papers still open, and share withdrawn</p>{head}{body}</div>'


EXTRA = f"""
.moves{{display:grid;grid-template-columns:70px repeat(4,1fr);gap:8px}}
.moves span{{border-radius:14px}}
.mh{{font-size:17px;font-weight:800;color:{TEAL_DARK};text-align:center;align-self:center}}
.mc{{display:flex;flex-direction:column;align-items:center;justify-content:center;height:86px;font-size:21px}}
.mc small{{font-size:14px;opacity:.8;margin-top:2px}}
"""


def main() -> None:
    lede = (f"Every paper and review on OpenReview when scores came out (Nov 6, 2026) compared with the same papers after the discussion "
            f"period closed (Nov 19). Ratings are on ICLR's 1–4 scale.")
    institutions = [r for r in S["institutions"] if r["weight"] >= 100][:14]
    body = "".join([
        hero("ICLR 2027 · Rebuttal", "What the rebuttal<br>changed", lede, "Nov 24, 2026"),
        kpis(),
        f'<section class="row" style="grid-template-columns:1fr 1fr">{jump_card()}{moves_card()}</section>',
        f'<section class="row" style="grid-template-columns:1fr 1fr">{talk_card()}{withdraw_card()}</section>',
        histogram_card(),
        daily_card(),
        areas_card(),
        f'<section class="row" style="grid-template-columns:1fr 1fr">'
        f'{group_card("Countries", "Country", S["countries"][:14], lambda r: NAMES.get(r["country"], r["country"]), lambda r: r["country"], "purple", PURPLE)}'
        f'{group_card("Biggest institutions", "Institution", institutions, lambda r: r["name"], lambda r: r["country"], "teal", TEAL)}</section>',
        footer(f"<b>Data:</b> OpenReview snapshots of Nov 6 and Nov 19, 2026. Countries and institutions cover the {O['used']:,} papers matched to an earlier "
               f"preprint in OpenAlex, split fractionally across authors. Change = Nov 19 minus Nov 6 average for papers still open."),
    ])
    render(document("ICLR 2027 rebuttal", body, EXTRA), "iclr2027-rebuttal")


if __name__ == "__main__":
    main()

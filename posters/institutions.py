"""ICLR 2027 institutions poster, soft academic style.

    .venv/bin/python posters/institutions.py   ->  posters/out/iclr2027-institutions.{png,pdf,html}
"""

import json
import math
import pathlib

from style import (CORAL, CORAL_DARK, INK, LINE, MUTED, PURPLE, SOFT, TEAL, TEAL_DARK, axis, badge, document, dot_track, esc, footer,
                   hero, name_cell, pct, render, share_bar)

HERE = pathlib.Path(__file__).resolve().parent.parent / "iclr2027-institutions"
S = json.loads((HERE / "stats.json").read_text())
NAMES = {k: v["name"] for k, v in json.loads((HERE / "countries.json").read_text()).items()}
O = S["overall"]
USED = O["used"]
LO, HI = 1.95, 2.55
TICKS = [2.0, 2.1, 2.2, 2.3, 2.4, 2.5]
CONTINENT_COLOUR = {"Asia": PURPLE, "North America": TEAL, "Europe": CORAL}
KIND = {"education": "University", "company": "Company", "facility": "Research lab", "government": "Government", "nonprofit": "Nonprofit",
        "healthcare": "Healthcare", "archive": "Archive", "other": "Other"}


def short(name: str) -> str:
    return name.replace("University", "Univ.") if len(name) > 34 else name


def kpis() -> str:
    tiles = [
        ("purple", f"{USED:,}", f"papers traced to their authors' institutions ({pct(USED / O['under_review'], 0)} of all {O['under_review']:,})"),
        ("teal", f"{O['countries']}", "countries"),
        ("coral", f"{O['institutions']:,}", "institutions with at least one author"),
        ("purple", f"{O['mean_used']:.2f}", f"average score of traced papers, vs {O['mean_rest']:.2f} for the rest"),
    ]
    cells = "".join(f'<div class="card kpi {c}"><div class="v">{v}</div><div class="l">{l}</div></div>' for c, v, l in tiles)
    return f'<section class="row" style="grid-template-columns:repeat(4,1fr)">{cells}</section>'


def group_card(title: str, sub: str, rows: list, label, colour: str, tone: str) -> str:
    top = max(r["weight"] for r in rows) / USED
    head = f'<div class="trow head" style="grid-template-columns:150px 1fr 56px 190px"><span>{sub}</span><span>Share of papers</span><span class="r">Score</span>{axis(LO, HI, [2.0, 2.2, 2.4])}</div>'
    body = "".join(
        f"""<div class="trow" style="grid-template-columns:150px 1fr 56px 190px"><span style="font-weight:700">{esc(label(r))}</span>
<div style="display:flex;align-items:center;gap:12px">{share_bar(r['weight'] / USED, top, colour)}<span style="font-weight:700;min-width:62px">{pct(r['weight'] / USED)}</span></div>
<b class="r">{r['mean']:.2f}</b>{dot_track(r['mean'], r['se'], LO, HI, colour, O['mean_used'])}</div>"""
        for r in rows if r["weight"] >= 5)
    return f'<div class="card {tone}"><h2>{title}</h2><p class="sub">Fractional share of the {USED:,} traced papers, and average initial score with its 95% range</p>{head}{body}</div>'


def countries_card() -> str:
    rows = S["countries"][:18]
    top = rows[0]["weight"] / USED
    cols = "grid-template-columns:44px 300px 1fr 92px 82px 360px"
    head = (f'<div class="trow head" style="{cols}"><span>#</span><span>Country</span><span>Share of traced papers</span><span class="r">Papers</span>'
            f'<span class="r">Score</span>{axis(LO, HI, TICKS)}</div>')
    body = "".join(
        f"""<div class="trow" style="{cols}"><span style="color:{MUTED};font-weight:700">{k}</span>{name_cell(NAMES.get(r['country'], r['country']), r['country'], 700)}
<div style="display:flex;align-items:center;gap:12px">{share_bar(r['weight'] / USED, top, PURPLE)}<span style="font-weight:700;min-width:62px">{pct(r['weight'] / USED)}</span></div>
<span class="r">{r['papers']:,}</span><b class="r">{r['mean']:.2f}</b>{dot_track(r['mean'], r['se'], LO, HI, PURPLE, O['mean_used'])}</div>"""
        for k, r in enumerate(rows, 1))
    cn, us = rows[0], rows[1]
    note = (f"<b>China ({pct(cn['weight'] / USED, 0)}) and the United States ({pct(us['weight'] / USED, 0)}) supply two thirds of the traced papers</b> "
            f"and score almost the same ({cn['mean']:.2f} vs {us['mean']:.2f}). Dashed line: average of all traced papers ({O['mean_used']:.2f}).")
    return f'<section class="card"><h2>Countries</h2><p class="sub">The 18 countries with the most traced papers. Papers = papers with at least one author there.</p>{head}{body}<p class="note">{note}</p></section>'


def biggest_card() -> str:
    rows = S["institutions"][:20]
    top = rows[0]["weight"] / USED
    cols = "grid-template-columns:36px 1fr 190px 70px"
    head = f'<div class="trow head" style="{cols}"><span>#</span><span>Institution</span><span>Share</span><span class="r">Score</span></div>'
    body = "".join(
        f"""<div class="trow" style="{cols}"><span style="color:{MUTED};font-weight:700">{k}</span>{name_cell(short(r['name']), r['country'])}
<div style="display:flex;align-items:center;gap:10px">{share_bar(r['weight'] / USED, top, TEAL)}<span style="font-weight:700;min-width:52px;font-size:16px">{pct(r['weight'] / USED)}</span></div><b class="r">{r['mean']:.2f}</b></div>"""
        for k, r in enumerate(rows, 1))
    return f'<div class="card teal"><h2>Biggest institutions</h2><p class="sub">By fractional share of traced papers</p>{head}{body}</div>'


def best_card(minimum: float = 20) -> str:
    rows = sorted([r for r in S["institutions"] if r["weight"] >= minimum], key=lambda r: -r["mean"])[:20]
    cols = "grid-template-columns:36px 1fr 64px 230px"
    head = f'<div class="trow head" style="{cols}"><span>#</span><span>Institution</span><span class="r">Score</span>{axis(2.0, 2.7, [2.1, 2.3, 2.5])}</div>'
    body = "".join(
        f"""<div class="trow" style="{cols}"><span style="color:{MUTED};font-weight:700">{k}</span>{name_cell(short(r['name']), r['country'])}
<b class="r">{r['mean']:.2f}</b>{dot_track(r['mean'], r['se'], 2.0, 2.7, CORAL, O['mean_used'])}</div>"""
        for k, r in enumerate(rows, 1))
    return (f'<div class="card coral"><h2>Highest average scores</h2><p class="sub">Institutions with at least {minimum:.0f} fractional papers. '
            f'Wide ranges mean few papers: treat the order loosely.</p>{head}{body}</div>')


def scatter_card() -> str:
    width, height, left, bottom, top_pad = 1412, 640, 70, 60, 20
    pw, ph = width - left - 30, height - bottom - top_pad
    rows = [r for r in S["institutions"] if r["weight"] >= 3]
    xlo, xhi = math.log10(3), math.log10(400)
    ylo, yhi = 1.7, 2.8
    x = lambda w: left + (math.log10(w) - xlo) / (xhi - xlo) * pw
    y = lambda m: top_pad + (1 - (m - ylo) / (yhi - ylo)) * ph
    cont = {c: v.get("continent", "") for c, v in json.loads((HERE / "countries.json").read_text()).items()}
    out = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for t in (1.8, 2.0, 2.2, 2.4, 2.6, 2.8):
        out.append(f'<line x1="{left}" x2="{width - 30}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{LINE}" stroke-width="1.5"/>'
                   f'<text x="{left - 12}" y="{y(t) + 6:.1f}" font-size="17" fill="{MUTED}" text-anchor="end">{t:.1f}</text>')
    for t in (3, 5, 10, 20, 50, 100, 200, 400):
        out.append(f'<text x="{x(t):.1f}" y="{height - bottom + 30}" font-size="17" fill="{MUTED}" text-anchor="middle">{t}</text>')
    out.append(f'<line x1="{left}" x2="{width - 30}" y1="{y(O["mean_used"]):.1f}" y2="{y(O["mean_used"]):.1f}" stroke="{SOFT}" stroke-width="2" stroke-dasharray="8 7"/>')
    for r in sorted(rows, key=lambda r: -r["weight"]):
        colour = CONTINENT_COLOUR.get(cont.get(r["country"]), "#b4b2a9")
        rad = 3 + 2.2 * math.sqrt(r["weight"])
        out.append(f'<circle cx="{x(r["weight"]):.1f}" cy="{y(r["mean"]):.1f}" r="{rad:.1f}" fill="{colour}" fill-opacity=".55" stroke="#fff" stroke-width="2"/>')
    for k, r in enumerate(S["institutions"][:4], 1):
        out.append(f'<text x="{x(r["weight"]):.1f}" y="{y(r["mean"]) + 6:.1f}" font-size="16" font-weight="800" fill="#fff" text-anchor="middle">{k}</text>')
    out.append(f'<text x="{left + pw / 2}" y="{height - 4}" font-size="17" font-weight="600" fill="{SOFT}" text-anchor="middle">Fractional papers (log scale)</text>')
    out.append("</svg>")
    legend = "".join(f'<span><i style="background:{c}"></i>{k}</span>' for k, c in CONTINENT_COLOUR.items()) + '<span><i style="background:#b4b2a9"></i>Elsewhere</span>'
    return (f'<section class="card"><h2>Bigger is not better</h2><p class="sub">Every institution with at least 3 fractional papers: size against average initial score. '
            f'Small institutions scatter widely by chance; the biggest sit right on the overall average (dashed). Numbers 1–4 match the Biggest institutions list.</p>'
            f'<div class="legend" style="margin-bottom:14px">{legend}</div>{"".join(out)}</section>')


def main() -> None:
    lede = (f"Who wrote the {USED:,} ICLR 2027 submissions that also appeared as an earlier preprint, and how reviewers scored them. "
            f"Each paper is split equally across its authors, then across each author's institutions.")
    body = "".join([
        hero("ICLR 2027 · Countries and institutions", "Where ICLR 2027<br>papers come from", lede, "Nov 24, 2026"),
        kpis(),
        f'<section class="row" style="grid-template-columns:1fr 1fr">'
        f'{group_card("Continents", "Continent", S["continents"], lambda r: r["continent"], PURPLE, "purple")}'
        f'{group_card("Institution types", "Type", S["kinds"], lambda r: KIND.get(r["kind"], r["kind"]), TEAL, "teal")}</section>',
        countries_card(),
        f'<section class="row" style="grid-template-columns:1fr 1fr">{biggest_card()}{best_card()}</section>',
        scatter_card(),
        footer(f"<b>Data:</b> reviews from OpenReview (Nov 6, 2026); affiliations from OpenAlex (Nov 14, 2026), matched by title and abstract to preprints "
               f"posted before reviews came out. Traced papers score higher than the rest, so they are not a random sample. Score = average initial rating (1–4)."),
    ])
    render(document("ICLR 2027 institutions", body), "iclr2027-institutions")


if __name__ == "__main__":
    main()

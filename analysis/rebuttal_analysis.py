# %% [markdown]
# # ICLR 2027 rebuttal: my own analysis
#
# Works only from the aggregate tables committed in `iclr2027-rebuttal/`
# (no raw OpenReview data needed). Run as a script, or open in VS Code /
# Jupyter: each `# %%` block is a cell.
#
#     .venv/bin/python analysis/rebuttal_analysis.py
#
# Column notes (from iclr2027-rebuttal/stats.py):
# - `submissions` is fractional: each paper is split equally across its
#   authors, then across each author's affiliations.
# - `initial_score` = mean review rating on 2026-11-06 (scale 1-4), all papers.
# - `open_initial_score` = same, but only papers still open on 2026-11-19.
# - `score_change` = final - initial, open papers only. `*_standard_error` are
#   weighted standard errors.
# - `reviews_raised` / `reviews_lowered` = share of reviews whose rating changed.
# - `rebuttal` = share of papers where the authors posted at least one comment.
# - Country / institution / type tables cover only the 10,520 papers matched to
#   an OpenAlex preprint posted before reviews came out. Areas cover all 40,544.

# %%
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as st

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "iclr2027-rebuttal"
FIGS = HERE / "figures"
FIGS.mkdir(exist_ok=True)

S = json.loads((DATA / "stats.json").read_text())
O = S["overall"]
read = lambda name: pd.read_csv(DATA / f"{name}.csv", encoding="utf-8-sig")
areas, countries, institutions, types, continents = (read(n) for n in ("areas", "countries", "institutions", "types", "continents"))

# Chart style: reference palette, thin marks, recessive axes.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e4e3de", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
})
FINDINGS = []


def note(text: str) -> None:
    FINDINGS.append(text)
    print("•", text)


# %% [markdown]
# ## 1. How much of the score jump is real?
# The mean score rose from initial to final, but withdrawn papers (mostly
# low-scoring) drop out of the "final" mean. Split the jump into a selection
# part and a genuine rating-change part.

# %%
selection = O["mean_kept_initial"] - O["mean_initial"]
genuine = O["mean_final"] - O["mean_kept_initial"]
total = selection + genuine
note(f"Mean score {O['mean_initial']:.3f} → {O['mean_final']:.3f} (+{total:.3f}). "
     f"{selection / total:.0%} of that is withdrawals removing weak papers (+{selection:.3f}); "
     f"{genuine / total:.0%} is reviewers actually changing ratings (+{genuine:.3f}).")
note(f"{O['status']['withdrawn']:,} of {O['base']:,} papers ({O['status']['withdrawn'] / O['base']:.1%}) were withdrawn; "
     f"their mean initial score was {O['mean_withdrawn_initial']:.2f} vs {O['mean_kept_initial']:.2f} for papers that stayed.")

fig, ax = plt.subplots(figsize=(7, 2.6))
steps = [("Initial mean\n(all papers)", O["mean_initial"], 0, MUTED),
         ("Withdrawals\nleave", selection, O["mean_initial"], ORANGE),
         ("Ratings\nchange", genuine, O["mean_kept_initial"], BLUE),
         ("Final mean\n(open papers)", O["mean_final"], 0, MUTED)]
for i, (label, width, left, color) in enumerate(steps):
    ax.barh(i, width, left=left, color=color, height=0.6)
    end = left + width
    ax.text(end + 0.004, i, f"{width:+.3f}" if left else f"{width:.3f}", va="center", color=INK2, fontsize=9)
ax.set_yticks(range(4), [s[0] for s in steps])
ax.invert_yaxis()
ax.set_xlim(1.95, 2.32)
ax.set_xlabel("Mean review rating (1–4)")
ax.grid(axis="y", visible=False)
ax.set_title("Where the post-rebuttal score jump comes from")
fig.savefig(FIGS / "1_score_jump_decomposition.png")
plt.close(fig)

# %% [markdown]
# ## 2. Does reviewer engagement matter?
# `replied` = the reviewer posted at least one comment in the discussion.

# %%
raised = S["raised"]
replied = S["replied"]
note(f"Reviewers who joined the discussion raised their rating {raised['all:1']:.0%} of the time, "
     f"vs {raised['all:0']:.0%} for reviewers who stayed silent (×{raised['all:1'] / raised['all:0']:.1f}).")
note("Harsher reviewers engaged less: discussion participation was "
     + ", ".join(f"{replied[k]:.0%} for rating {k}" for k in sorted(replied)) + ".")

tr = pd.DataFrame(S["transitions"]).pivot(index="before", columns="after", values="reviews").fillna(0)
moved_up = {b: tr.loc[b, tr.columns > b].sum() / tr.loc[b].sum() for b in tr.index}
note("Share of reviews raised, by starting rating: " + ", ".join(f"{int(b)} → {v:.1%}" for b, v in moved_up.items())
     + f". Only {O['reviews_lowered'] / O['reviews_compared']:.1%} of reviews went down.")

fig, ax = plt.subplots(figsize=(7, 3.2))
ratings = ["1", "2", "3"]
x = np.arange(len(ratings))
w = 0.36
for off, flag, color, label in ((-w / 2 - 0.01, "1", BLUE, "Reviewer joined discussion"), (w / 2 + 0.01, "0", MUTED, "Reviewer stayed silent")):
    vals = [raised[f"{r}:{flag}"] for r in ratings]
    ax.bar(x + off, vals, w, color=color, label=label)
    for xi, v in zip(x + off, vals):
        ax.text(xi, v + 0.008, f"{v:.0%}", ha="center", color=INK2, fontsize=9)
ax.set_xticks(x, [f"Initial rating {r}" for r in ratings])
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_ylabel("Reviews raised")
ax.grid(axis="x", visible=False)
ax.legend(frameon=False, loc="upper right")
ax.set_title("Engaged reviewers raise ratings far more often")
fig.savefig(FIGS / "2_raise_rate_by_engagement.png")
plt.close(fig)

# %% [markdown]
# ## 3. Research areas: withdrawals, rebuttal effort and score change
# Areas cover every paper, so this is the least biased breakdown.

# %%
a = areas.copy()
a["short"] = a["area"].str.split(",| \\(| including").str[0].str.strip().map(lambda s: s if len(s) <= 42 else s[:42].rsplit(" ", 1)[0] + "…")
r_w, p_w = st.pearsonr(a["initial_score"], a["withdrawn"])
r_g, p_g = st.pearsonr(a["rebuttal"], a["score_change"])
note(f"Across {len(a)} areas, an area's mean initial score does not predict its withdrawal rate (r = {r_w:.2f}, p = {p_w:.2f}), "
     "even though withdrawn papers individually scored low. The highest-withdrawal areas (vision, robotics, generative models) "
     "score above average; one guess worth checking is resubmission to a vision conference with a November deadline.")
note(f"Areas where more authors wrote rebuttals did {'' if p_g < 0.05 else 'not clearly '}see bigger score gains "
     f"(r = {r_g:.2f}, p = {p_g:.3f}).")
top = a.nlargest(1, "withdrawn").iloc[0]
low = a.nsmallest(1, "withdrawn").iloc[0]
note(f"Withdrawal rate ranges from {low['withdrawn']:.0%} ({low['short']}) to {top['withdrawn']:.0%} ({top['short']}).")
best, worst = a.nlargest(1, "score_change").iloc[0], a.nsmallest(1, "score_change").iloc[0]
aw = 1 / a["score_change_standard_error"] ** 2
a_pool = (aw * a["score_change"]).sum() / aw.sum()
a_Q = (aw * (a["score_change"] - a_pool) ** 2).sum()
a_p = st.chi2.sf(a_Q, len(a) - 1)
note(f"Unlike countries, areas do differ in how much scores moved: Q = {a_Q:.1f} on {len(a) - 1} df, p = {a_p:.1g} "
     "(areas don't share papers, so this test is clean).")
note(f"Score change by area ranges from +{worst['score_change']:.3f} ({worst['short']}) to +{best['score_change']:.3f} ({best['short']}).")

s = a.sort_values("score_change")
fig, ax = plt.subplots(figsize=(7.5, 6.4))
y = np.arange(len(s))
ax.errorbar(s["score_change"], y, xerr=1.96 * s["score_change_standard_error"], fmt="o", color=BLUE,
            ecolor=BLUE, elinewidth=1.2, capsize=0, markersize=5)
ax.axvline(genuine, color=MUTED, linewidth=1, linestyle="--")
ax.text(genuine, len(s) - 0.2, f" all papers +{genuine:.3f}", color=INK2, fontsize=8, va="bottom")
ax.set_yticks(y, s["short"], fontsize=8.5)
ax.set_xlabel("Mean score change after rebuttal (open papers, 95% CI)")
ax.grid(axis="y", visible=False)
ax.set_title("Score change by primary area")
fig.savefig(FIGS / "3_score_change_by_area.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4.4))
ax.scatter(a["initial_score"], a["withdrawn"], s=np.sqrt(a["submissions"]) * 2.2, color=BLUE, alpha=0.75,
           edgecolor=SURFACE, linewidth=1.5)
for _, row in a.nlargest(3, "withdrawn").iterrows():
    ax.annotate(row["short"], (row["initial_score"], row["withdrawn"]), xytext=(6, 2), textcoords="offset points", fontsize=8, color=INK2)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))
ax.set_xlabel("Mean initial score")
ax.set_ylabel("Papers withdrawn")
ax.set_title(f"Area withdrawal rate is not explained by score (r = {r_w:.2f}); dot size = submissions")
fig.savefig(FIGS / "4_area_withdrawal_vs_score.png")
plt.close(fig)

# %% [markdown]
# ## 4. Countries: is the rebuttal bump the same everywhere?
# Cochran's Q tests whether score changes differ more than the standard
# errors would allow. (Approximate: co-authored papers count in several
# countries, so the groups are not independent.)

# %%
c = countries[countries["open_submissions"] >= 50].copy()
wts = 1 / c["score_change_standard_error"] ** 2
pooled = (wts * c["score_change"]).sum() / wts.sum()
Q = (wts * (c["score_change"] - pooled) ** 2).sum()
p_q = st.chi2.sf(Q, len(c) - 1)
note(f"Among {len(c)} countries with ≥50 open papers, score change spans "
     f"+{c['score_change'].min():.3f} to +{c['score_change'].max():.3f}; heterogeneity test Q = {Q:.1f}, p = {p_q:.3f} "
     f"→ {'differences are larger than noise' if p_q < 0.05 else 'consistent with the same bump everywhere'}.")
note("Rebuttal participation by country (top 6 by papers): "
     + ", ".join(f"{r.country_name} {r.rebuttal:.0%}" for r in c.head(6).itertuples()) + ".")
note("Withdrawal rate by country (top 6): " + ", ".join(f"{r.country_name} {r.withdrawn:.0%}" for r in c.head(6).itertuples()) + ".")

# %% [markdown]
# ## 5. Institutions: real outliers or noise?
# A funnel plot: small institutions scatter widely by chance. Only points
# outside the funnel are worth a second look. Bonferroni-corrected z for
# the number of institutions tested.

# %%
inst = institutions[institutions["open_submissions"] >= 10].copy()
inst = inst[inst["score_change_standard_error"] > 0]
inst["z"] = (inst["score_change"] - pooled) / inst["score_change_standard_error"]
cut = st.norm.isf(0.025 / len(inst))
flag = inst[inst["z"].abs() > cut]
note(f"{len(inst)} institutions have ≥10 open papers; with a Bonferroni cut of |z| > {cut:.2f}, "
     f"{len(flag)} stand out from the overall bump"
     + (": " + ", ".join(f"{r.name} ({r.score_change:+.2f})" for r in flag.itertuples()) if len(flag) else "") + ".")

spread = np.median(inst["score_change_standard_error"] * np.sqrt(inst["open_submissions"]))
n = np.linspace(inst["open_submissions"].min(), inst["open_submissions"].max(), 300)
fig, ax = plt.subplots(figsize=(7.5, 4.4))
ax.scatter(inst["open_submissions"], inst["score_change"], s=14, color=BLUE, alpha=0.55, linewidth=0)
for k, ls in ((1.96, "--"), (cut, ":")):
    ax.plot(n, pooled + k * spread / np.sqrt(n), color=MUTED, linewidth=1, linestyle=ls)
    ax.plot(n, pooled - k * spread / np.sqrt(n), color=MUTED, linewidth=1, linestyle=ls)
ax.axhline(pooled, color=INK2, linewidth=1)
for r, dy in zip(inst.nlargest(3, "open_submissions").itertuples(), (-40, 34, -28)):
    ax.annotate(r.name.replace("University", "U."), (r.open_submissions, r.score_change), xytext=(-10, dy), textcoords="offset points",
                ha="right", fontsize=8, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.7))
ax.set_xscale("log")
ax.set_xlabel("Open submissions (fractional, log scale)")
ax.set_ylabel("Mean score change")
ax.set_title("Institution score change vs size: almost all inside the noise funnel")
ax.text(0.99, 0.02, "dashed = 95% band, dotted = Bonferroni band", transform=ax.transAxes, ha="right", fontsize=8, color=MUTED)
fig.savefig(FIGS / "5_institution_funnel.png")
plt.close(fig)

# %% [markdown]
# ## 6. Organization type and coverage caveat

# %%
note("By organization type: " + ", ".join(f"{r.type} initial {r.initial_score:.2f} → change {r.score_change:+.3f}" for r in types.head(3).itertuples()) + ".")
note(f"Caveat: country/institution tables cover {O['used']:,} of {O['base']:,} papers (those with an earlier preprint). "
     f"Those papers started higher ({O['used_mean_initial']:.2f} vs {O['rest_mean_initial']:.2f}), so they are not a random sample.")

# %% [markdown]
# ## 7. Discussion timeline

# %%
d = pd.DataFrame(S["daily"]).set_index("day").iloc[:-1]  # last day is a partial snapshot day
peak = d["authors"].idxmax()
note(f"Author comments peaked on {peak} ({d.loc[peak, 'authors']:,}); there were {O['comments']['authors']:,} author comments "
     f"vs {O['comments']['reviewer']:,} reviewer comments overall ({O['comments']['authors'] / O['comments']['reviewer']:.1f} per reviewer comment).")

fig, ax = plt.subplots(figsize=(7.5, 3.2))
days = pd.to_datetime(d.index).strftime("%b %d")
ax.plot(days, d["authors"], color=BLUE, linewidth=2, marker="o", markersize=4, label="Authors")
ax.plot(days, d["reviewer"], color=ORANGE, linewidth=2, marker="o", markersize=4, label="Reviewers")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:.0f}k" if v else "0"))
ax.tick_params(axis="x", labelsize=8, rotation=45)
ax.grid(axis="x", visible=False)
ax.legend(frameon=False, loc="upper left")
ax.set_ylabel("Comments per day (AoE)")
ax.set_title("Discussion activity during the rebuttal window")
fig.savefig(FIGS / "6_daily_comments.png")
plt.close(fig)

# %%
(HERE / "findings.md").write_text("# Findings (auto-generated)\n\n" + "\n".join(f"- {f}" for f in FINDINGS) + "\n")
print(f"\nWrote {len(list(FIGS.glob('*.png')))} figures to {FIGS} and findings.md")

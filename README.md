# ICLR 2027 results posters + my analysis

Three posters on ICLR 2027 reviews (scores, institutions, rebuttal), plus my own analysis of the rebuttal phase in
[`analysis/`](analysis/). The posters are my own design and code ([`posters/`](posters/)). The data pipelines that produced
the summary tables (`stats.json`, CSVs) are adapted from [clareLab/posters](https://github.com/clareLab/posters) under the
MIT license; both copyright notices are in [LICENSE](LICENSE).

Each poster comes as a print-size PNG (4800 px wide) and a PDF in [`posters/out/`](posters/out/).

- [ICLR 2027 posters](#iclr-2027-posters)
- [My analysis of the rebuttal phase](#my-analysis-of-the-rebuttal-phase)
- [Repo layout](#repo-layout)
- [Running things](#running-things)

## ICLR 2027 posters

All three use OpenReview (reviews) and OpenAlex (author affiliations). ICLR 2027 reviews use a 1–4 rating scale.

### Review scores ([`posters/scores.py`](posters/scores.py))

- **40,544** submissions under review with **125,304** reviews.
- Mean of per-paper average ratings: **2.06**; median **2.0**.
- Ratings given: 1 → 23,782 · 2 → 72,006 · 3 → 27,624 · 4 → 1,892. Almost 3 in 5 reviews were a 2.
- Only **37.9%** of papers average 2.33 or more, **15.1%** 2.67 or more and **4.1%** 3.00 or more.
- By primary area, average scores range from **1.92** (interpretability) to **2.16** (generative models).

![ICLR 2027 scores poster](posters/out/iclr2027-scores.png)

### Institutions ([`posters/institutions.py`](posters/institutions.py))

Covers the 10,520 papers that could be matched to a preprint posted before reviews were released. Each paper is split fractionally across
its authors and their affiliations: **74 countries** and **1,884 institutions**. These papers score higher than the rest
(2.19 vs 2.02), so they are not a random sample.

- **China (33.4%)** and the **United States (32.0%)** account for two thirds of the matched submissions, then
  South Korea, Hong Kong, the UK, Germany and Singapore (3–4% each).
- Largest institutions: Tsinghua (3.0%), Peking (2.1%), Shanghai Jiao Tong (2.0%), Zhejiang (1.7%), Stanford (1.4%), NUS (1.4%).
- Among the top countries, South Korea (2.26) and Germany (2.23) have the highest average initial score; China and the US are both about 2.18.
- Universities supply 83% of the matched submissions; companies 10%, and company papers score a little higher (2.23 vs 2.18).

![ICLR 2027 institutions poster](posters/out/iclr2027-institutions.png)

### Rebuttal ([`posters/rebuttal.py`](posters/rebuttal.py))

Compares a snapshot taken when reviews came out (2026-11-06) with one taken after the discussion period (2026-11-19).

- **6,127** papers (15.1%) were withdrawn and **16** were desk rejected; **34,400** stayed open.
- **17,373** reviews were raised and only **792** lowered; **13,791** open papers changed their average score.
- **75.5%** of open papers had an author response; authors posted **265,321** comments, reviewers **54,690**.
- Median score went from **2.0** to **2.33**.

![ICLR 2027 rebuttal poster](posters/out/iclr2027-rebuttal.png)

## My analysis of the rebuttal phase

[`analysis/rebuttal_analysis.py`](analysis/rebuttal_analysis.py) works only from the summary tables in `iclr2027-rebuttal/`,
so it runs without the raw OpenReview data. All findings are in [`analysis/findings.md`](analysis/findings.md). The main ones:

1. **About 28% of the post-rebuttal score jump comes from withdrawals.** The mean went from 2.060 to 2.284 (+0.225). Withdrawn papers averaged 1.70,
   so dropping them accounts for +0.064; reviewers actually changing ratings accounts for +0.161.

   ![Score jump decomposition](analysis/figures/1_score_jump_decomposition.png)

2. **Reviewers who joined the discussion raised their rating about 6× as often** (29% vs 5%), at every starting rating.
   Harsher reviewers took part less: 24% of reviewers who gave a 1 joined the discussion, against 46% of those who gave a 3. This is a correlation, not proof of cause.

   ![Raise rate by reviewer engagement](analysis/figures/2_raise_rate_by_engagement.png)

3. **The rebuttal effect really differs by area**: from +0.13 (neurosymbolic & hybrid AI) to +0.20 (generative models), far beyond
   what chance would produce (p ≈ 2e-13).

   ![Score change by area](analysis/figures/3_score_change_by_area.png)

4. **An area's withdrawal rate doesn't follow its scores.** Computer vision (25%), robotics (22%) and generative models (19%) withdrew the most,
   yet score above average. One untested guess: papers leaving to resubmit to another conference.

   ![Area withdrawal vs score](analysis/figures/4_area_withdrawal_vs_score.png)

5. **Every country got about the same boost** (+0.17 to +0.22 among the 15 largest; p = 0.73), but withdrawal rates differ:
   China 15% vs 8–10% for the US, UK and Germany.
6. **No institution stands out once you allow for size.** All 178 institutions with at least 10 open papers sit inside the range that
   random variation would produce, so a ranking of institutions by rebuttal gain would mostly reflect noise.

   ![Institution funnel plot](analysis/figures/5_institution_funnel.png)

7. Authors wrote about **5 comments for every reviewer comment**, peaking at 48k author comments on Nov 18.

   ![Daily comments](analysis/figures/6_daily_comments.png)

## Repo layout

| Folder | What it is |
|---|---|
| `posters/` | My poster code: `style.py` (shared look), `scores.py`, `institutions.py`, `rebuttal.py`; output in `posters/out/` |
| `iclr2027-scores/`, `iclr2027-institutions/`, `iclr2027-rebuttal/` | Data pipelines (fetch and stats scripts) and the summary CSV/JSON tables the posters read |
| `analysis/` | My analysis script, its charts and findings |

## Running things

Set up once:

```bash
python3 -m venv .venv && .venv/bin/pip install pandas numpy matplotlib scipy pillow segno pyarrow rapidfuzz
```

Render the posters from the committed `stats.json` files (needs Google Chrome or Chromium, and internet for the
Plus Jakarta Sans font; no API keys). Each takes under a minute:

```bash
.venv/bin/python posters/scores.py
.venv/bin/python posters/institutions.py
.venv/bin/python posters/rebuttal.py
```

Run my analysis:

```bash
.venv/bin/python analysis/rebuttal_analysis.py
```

Rebuilding the `stats.json` files themselves (the `stats.py`, `fetch.py` and `openalex.py` scripts, or the `justfile` recipes) needs
the raw OpenReview/OpenAlex snapshots under `~/Documents/data/posters/iclr2027/`, which are not in the repo. Fetching them needs
an OpenReview API key and an OpenAlex API key.

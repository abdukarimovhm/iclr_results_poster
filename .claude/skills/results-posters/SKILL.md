---
name: results-posters
description: Make data and research results posters (tall infographic-style posters full of charts, tables and headline numbers) from summary statistics, and render them to print-size PNG and PDF. Covers two proven approaches, an HTML-cards + inline-SVG kit rendered with headless Chrome (fast, default) and a fixed-size hand-placed SVG canvas (exact print layout, offline), plus the data pipeline that turns raw data such as OpenReview or OpenAlex into stats.json. Use this whenever someone wants a poster, infographic, one-page visual report or shareable image of results, such as conference review statistics, rankings, survey or benchmark results, country or institution breakdowns, or before/after comparisons, or wants to restyle, redesign or re-render such a poster, even if they don't say "poster".
---

# Results posters

A results poster is a single tall page that tells a data story: a header, a row of headline numbers, then cards that
each answer one question with one chart and one sentence of takeaway. This skill comes from building the ICLR 2027
review posters (scores, institutions, rebuttal), first in clareLab's original SVG-canvas code, then rebuilt as HTML cards.

## Workflow

1. **Get the numbers first.** Compute every number into a `stats.json` (or CSVs) with a separate script before any design
   work. The poster script only reads it. This keeps posters re-renderable and stops hand-typed numbers from drifting.
   For pulling and aggregating raw data (API paging, snapshots, fractional author weights, standard errors), read
   `references/data-pipeline.md`.
2. **Pick the story.** List 5–8 questions the data answers ("what did reviewers give?", "did the rebuttal help?").
   Each becomes one card. Order: the headline first, the detail (long tables) last.
3. **Choose the approach** (next section) and build the poster.
4. **Render, then look at it.** Crop the PNG into top, middle and bottom pieces and view each one. Most bugs are only visible
   this way: invisible bars, collided labels, half-rendered regions, wrong rounding. Use `references/review-checklist.md`.
5. **Ship.** Commit the PNG and PDF next to the code. For social media, crop 4:5 images of the top of each poster,
   because tall images get cropped badly in feeds.

## Choosing an approach

| | HTML cards (default) | SVG canvas |
|---|---|---|
| Layout | CSS grid/flex, auto height | every x/y computed by hand on a fixed canvas (e.g. 7200×9600) |
| Iteration speed | fast: change CSS, re-run | slow: moving one block shifts everything below |
| Text fitting | browser wraps and truncates | measure glyphs with PIL to place and fit text |
| Output | 3× PNG + PDF, height fits content | exact fixed-size print PNG/SVG |
| Fonts | web font (needs network) or local | embedded as base64 in the SVG, fully offline |
| Code size | ~250–350 lines per poster | ~300–1,700 lines per poster |
| Best for | most posters, restyles, social images | strict print specs, dense custom charts (flows, treemaps), offline builds |

- **HTML cards:** read `references/html-cards.md` and start from `assets/style.py` + `assets/example_poster.py`.
  Copy both next to the new poster script and edit the settings block (author, repo link for the QR code, credit line).
- **SVG canvas:** read `references/svg-canvas.md`.

## Content rules that made these posters work

- **Each card has one question as its title, one chart, and a one-sentence takeaway in bold**, e.g. "57% of all ratings were a 2."
  Readers skim titles and bold text, so put the finding there and not just the chart.
- **Headline numbers row:** 4 tiles, a big number plus a short plain label. Pick the four things someone should remember.
- **Be honest in small print:**
  - Say when a subset isn't random ("traced papers score higher than the rest").
  - Explain fractional counting.
  - Show 95% ranges for means.
  - Add "treat the order loosely" on rankings of small groups.
  - Separate selection effects from real change (withdrawn papers raising a mean).
- **Rankings of many small groups mostly rank noise.** Show a size-vs-value scatter or a funnel plot next to any "top N" list.
- **Formatting:**
  - Round shares sensibly and show `<0.1%` rather than `0.0%`.
  - Use thousands separators and tabular numbers.
  - Use the same decimals within a column.
- **Colour:**
  - One hue per meaning, across the whole poster.
  - Use a single-hue light→dark ramp for ordered bands.
  - Use at most ~3 categorical colours plus grey for "other" on scatters.
  - Text stays ink-coloured, not series-coloured.
- **Credit and license:** an author, date, data source and snapshot date in the footer, and a QR code to the code or repo.
  If any code or data processing is adapted from someone else, keep their license notice and credit them.

## Files in this skill

- `assets/style.py`: the HTML-cards kit. It holds the design tokens and these building blocks:
  - `hero`, `kpis`, `hbars`
  - `dot_track`, `arrow_track`, `axis`
  - `share_bar`, `name_cell`, `badge`, `ramp`
  - `footer`, `render`
- `assets/example_poster.py`: a runnable minimal poster using every block once, with dummy data.
- `references/html-cards.md`: how the kit works, the components, rendering details and gotchas.
- `references/svg-canvas.md`: clareLab's original fixed-canvas technique: Canvas class, text measurement, embedded fonts, banded rendering.
- `references/data-pipeline.md`: from raw API data to `stats.json` (OpenReview and OpenAlex example, weights, standard errors).
- `references/review-checklist.md`: what to check before calling a poster done.

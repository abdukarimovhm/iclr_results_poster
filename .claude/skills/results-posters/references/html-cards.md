# HTML cards approach

Write the poster as an HTML page: CSS grid for layout, inline SVG for the few charts that need real geometry, then
let headless Chrome turn it into a 3× PNG and a PDF. This is how the "soft academic" ICLR 2027 posters were built
(`posters/style.py`, `scores.py`, `institutions.py`, `rebuttal.py` in the iclr_results_poster repo).

## Setup

- Python packages: `segno` (QR code), `pillow` (only for checking and cropping output).
- Google Chrome or Chromium. `style.py` finds `chromium`, then `google-chrome`, then the macOS Chrome app path.
- Internet access at render time if you use the Google Fonts link (Plus Jakarta Sans). For offline builds, download the font
  files and use a local `@font-face` instead.

## Page structure

```
<div class="page" id="page">          # 1600px wide, 56px padding, 28px gaps
  hero(...)                            # coloured header: kicker, big title, lede, QR + author + date
  kpis([...])                          # row of 4 headline numbers
  <section class="row" style="grid-template-columns:1fr 1fr"> card card </section>
  <section class="card"> full-width chart or table </section>
  ...
  footer(...)                          # data source on the left, author/repo/credit on the right
```

Cards: `.card` (white with hairline), `.card.purple` / `.teal` / `.coral` (pastel fills). Inside a card: `<h2>` title,
`<p class="sub">` one-line description, the chart, `<p class="note"><b>takeaway.</b> detail</p>`.

## Components in `assets/style.py`

- **`hero(kicker, title_html, lede, date)`:** header card with a QR code to `REPO`.
- **`kpis([(tone, value, label), ...])`:** headline number row.
- **`hbars(rows, width, total, colour)`:** inline-SVG horizontal rounded bars with a percent and a count. Good for
  distributions with fewer than 10 categories.
- **Tables:** `.trow` grid rows with `grid-template-columns` set per table. A `.trow.head` row gives uppercase column labels.
  Put `axis(lo, hi, ticks)` in the header cell above a track column so the ticks line up with the rows below.
- **`dot_track(mean, se, lo, hi, colour, ref)`:** a dot at the mean, a soft bar for ±1.96·se, and an optional dashed reference line.
- **`arrow_track(start, end, lo, hi, colour)`:** a hollow dot (before), a filled dot (after) and a bar between them.
  Good for before/after per group.
- **`share_bar(share, top, colour)`:** a thin bar scaled to the largest row. Put it in a flex container next to its label.
- **`name_cell(name, code)`:** a long name truncated with an ellipsis that always keeps its country `badge(code)`.
  Country-code badges replace flag images, so there are no image assets or licensing to worry about.
- **`ramp(n)`:** an n-step purple sequential ramp interpolated through hand-picked stops. Use it for ordered bands such as
  stacked "share of papers in each rating band" bars (`.stack` with `<i>` segments, see `example_poster.py`).
- **`pct(x, d)`:** a percent with `<0.1%` for tiny non-zero values.
- **`render(doc, name)`:** see below.

### Charts written as inline SVG in the posters

- **Histogram of exact values:** x is positioned by value (not equal spacing) so gaps are honest. Colour the bars past a
  cutoff differently and shade that region, label only the big bars, and put Q1/median/Q3 under the axis.
- **Scatter (size vs value):**
  - Log x, bubble radius ∝ √size.
  - ≤3 continent colours plus grey.
  - A dashed overall-mean line.
  - Number the biggest few bubbles (1–4) to match a table instead of placing long text labels, which collide.
- **Stacked daily columns** (authors / reviewers / chairs) with the total labelled on the peak day only.
- **Transition grid** (rating before → after) as a CSS grid of rounded cells: green intensity for up, coral for down,
  white diagonal.

## Rendering (`render`)

1. Write `<name>.html` with a small script that, after `document.fonts.ready`, stores the page height in `body[data-h]`.
2. Run Chrome `--dump-dom` and read the height back from the DOM.
3. Rewrite the HTML with that exact height, then run Chrome twice:
   - `--screenshot` at `--force-device-scale-factor=3`, giving a 4800 px wide PNG.
   - `--print-to-pdf` with `@page{size:W H;margin:0}` and `--no-pdf-header-footer`, giving a one-page PDF.

All Chrome calls use `--headless=new --hide-scrollbars --run-all-compositor-stages-before-draw --virtual-time-budget=60000`.

## Gotchas found the hard way

- **Invisible bars in flex rows:** a `div` bar inside `display:flex` collapses to zero width. Give it `flex:1`
  (`.sbar` does this).
- **Half-blank render:** a large SVG (hundreds of circles) at 3× rendered only partly with a 20 s virtual time budget.
  60 s fixed it. Always view the bottom of the PNG.
- **Rounding:** `0.45%` printed as `<0.1%` because of a wrong threshold. The cut-off for `d` decimals is `x < 5·10^-(d+3)`.
- **Axis labels crowd** when a track column is narrow. Use 3 ticks, not 5.
- **Long names push badges out.** Use `name_cell`, which truncates the name, not the badge.
- **Uneven card heights in a 2-column row:** fine, but put the taller content on the right, or balance by moving a note.
- **Web font not loaded:** the measure step waits for `document.fonts.ready`. If the PNG shows a fallback font, check the network.

## Social images

Crop the top `width × 1.25·width` of the 3× PNG and resize to 1440×1800 (4:5) for X. For Telegram, send the full poster
scaled to 1600 px wide as an album (well under the 10 MB limit).

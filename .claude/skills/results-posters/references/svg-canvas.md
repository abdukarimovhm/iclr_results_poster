# SVG canvas approach (clareLab's original)

The original ICLR 2027 posters by clareLab (github.com/clareLab/posters, MIT license) were built as one big hand-placed
SVG. In the iclr_results_poster repo the original scripts live in git history (`git show c65c674:iclr2027-rebuttal/poster.py`,
and `iclr2027-scores/poster.py`, `iclr2027-institutions/poster.py`). If you reuse their code, keep their copyright notice.

Use this approach when you need an exact fixed print size, fully offline rendering with embedded fonts, or dense custom
graphics (flow ribbons, treemaps, label placement around hundreds of dots) that CSS can't express.

## Core pieces

**Fixed canvas and layout constants.** A fixed canvas (`W, H = 7200, 9600` in the larger posters; the scores poster used a
6000×8000 viewBox rendered at 7200×9600). Margins, column split and gaps are named constants (`L, R, TOP, BOTTOM, SPLIT,
COLUMN, GAP`). Every section function takes a y position and returns the y where it ended, so sections stack:

```python
y = header(c)
y = ratings(c, L, mid, y + 110)
y = ladder(c, L, mid, y + 110)
```

**Canvas class.** It collects SVG strings:

```python
class Canvas:
    def __init__(self): self.items = [f'<rect width="{W}" height="{H}" fill="#fff"/>']; self.texts = []
    def rect(self, x, y, w, h, fill, stroke="", width=0): ...
    def line(self, x1, y1, x2, y2, stroke=INK, width=2, dash=""): ...
    def circle(self, x, y, r, fill, stroke="", width=0): ...
    def shape(self, d, fill, stroke="", width=0): ...        # arbitrary path
    def text(self, x, y, s, size, weight=400, family="sans", anchor="start", fill=INK,
             spacing=0, halo=0, length=0): ...               # halo = white stroke behind text, paint-order=stroke
    def save(self, path): ...                                # writes <svg> + <defs><style>@font-face…</style></defs>
```

Texts are kept in a separate list and written after all shapes, so labels always sit on top.

**Text measurement with PIL.** You can't ask an SVG how wide a string is before rendering, so load the same font files
with Pillow at size 1000 and scale:

```python
def measure(text, size, family="sans", weight=400):
    return ImageFont.truetype(FONT_FILES[family, weight], 1000).getlength(text) * size / 1000
```

The rebuttal poster also measured the real ink box (`ink()`) by drawing the glyphs on a scratch image and calling
`getbbox()`, for tight vertical alignment. Column widths, right-aligned numbers and truncation all come from `measure`.

**Embedded fonts.** IBM Plex Sans and Plex Sans Condensed (OFL) `.otf` files are base64-encoded into `@font-face` rules inside
the SVG's `<defs><style>`, so the SVG renders identically anywhere, offline.

**Colour helpers:**
- `oklch(l, c, h)` → hex, for perceptually even ramps.
- `mix` / `shade` toward white or black.
- `luminance` to choose dark or light text on a fill.
- A gradient `<linearGradient>` for continuous legends.
- Categorical colours assigned by a fixed order (`painter`).

**Flags.** Country flag SVGs are base64-embedded once as `<symbol>` and placed with `<use>`. A variant build could hide a set
of flags (the `-nohmt` variant). The rebuilt posters dropped flags in favour of text badges.

**QR code.** `segno.make(URL).matrix` was drawn cell by cell as rects.

**Label placement.** For scatter labels the rebuttal poster had a `Grid` spatial hash (cells of 120 px) and a `Placer` that
tries candidate positions around each dot, rejects any that hit dots, other labels or fixed boxes, and adds leader lines.
That is about 200 lines; consider whether numbering a few bubbles is enough before writing one.

**Chart types used:**
- Ledger tables with flags, bars and a score axis.
- Exact-value tables with a "top x%" column.
- Percentile ladders.
- Heat-shaded band tables per area.
- Funnel plots with 95% curves.
- Mosaic or treemap of institutions by country.
- Flow ribbons of paper averages from Nov 6 to Nov 19.
- A review transition matrix.
- Daily comment columns.

## Rendering

Chrome headless screenshots of the SVG. For the 7200×9600 posters a single screenshot sometimes came back partly blank, so
the rebuttal poster:

1. Splits the page into `BANDS = 4` horizontal bands. Each band is an HTML page that offsets the SVG `<img>` by `-k·step`.
2. Screenshots all bands in parallel (`subprocess.Popen`).
3. Checks each band for blank regions (`missing()`: a 256 px strip whose darkest pixel is ≥ 250) and re-shoots only those, up to 8 times.
4. Stitches the bands with Pillow.

The institutions poster instead retried a full render with growing `--virtual-time-budget` (600 s up to 4,800 s of
virtual time) until a known corner pixel was painted. Both then wrote a `-4mb.png` variant by quantizing to 256/192/128 colours
until it fit under 4 MB (for upload limits).

## Trade-offs

- **Pros:**
  - Pixel-exact.
  - Self-contained SVG with fonts embedded.
  - Any graphic is possible.
  - Deterministic output.
- **Cons:**
  - Every layout change means recomputing coordinates.
  - The code grows large: the rebuttal poster was ~1,700 lines.
  - Text fitting is manual.
  - Rendering very large canvases needs the banding workaround.

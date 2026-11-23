# Review checklist before a poster is done

Render, then actually look. Crop the 3× PNG into 3–4 horizontal pieces and view each one at a readable size:

```python
from PIL import Image
im = Image.open("out/poster.png"); w, h = im.size
for k in range(4):
    im.crop((0, h * k // 4, w, h * (k + 1) // 4)).resize((w // 3, h // 12)).save(f"/tmp/part{k}.png")
```

**Rendering:**
- [ ] The whole page is painted: no white or blank band near the bottom, and the big SVG charts are complete.
- [ ] The web font loaded (no fallback serif or system font).
- [ ] The PDF is one page with the same content.

**Layout:**
- [ ] Every bar is visible: no zero-width flex bars, and tiny values still show a sliver.
- [ ] No text is clipped at a card edge (labels drawn after a bar's end need room up to the right edge).
- [ ] Labels don't collide (scatters, crowded axes). Label fewer items or number them.
- [ ] Long names truncate, and their badges or counts stay visible.
- [ ] Axis ticks line up with the tracks below them.

**Numbers:**
- [ ] Every number comes from `stats.json`. Spot-check 3–5 against the file.
- [ ] Shares in a stacked bar or a transition row add to ~100%.
- [ ] Tiny values print as `<0.1%`, not `0.0%`, and values like 0.4% aren't wrongly shown as `<0.1%`.
- [ ] Wording matches the definition: "2.67 or more" vs "above 2.67"; "papers with an author there" vs fractional share.

**Honesty:**
- [ ] Sample caveats are on the poster (subset not random, snapshot dates, fractional counting).
- [ ] Rankings of small groups show uncertainty, or carry a "treat the order loosely" note.
- [ ] Selection effects are called out where a mean changes because items left.

**Credit:**
- [ ] The footer has the data source and dates, the author and the repo link.
- [ ] The QR code points to the right URL. Decode it, or check the `REPO` setting.
- [ ] Any adapted code or data pipeline is credited, and its license notice is kept in the repo.

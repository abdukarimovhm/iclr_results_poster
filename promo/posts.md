# Posts

Images in this folder:
- `telegram-1-scores.png`, `telegram-2-institutions.png`, `telegram-3-rebuttal.png`: full posters, 1600 px wide. Send them as one album with the Telegram post.
- `x-0-cover.png`: 16:9 cover for the main X post (title, three key numbers, thumbnails of all three posters). Rebuild it with `.venv/bin/python promo/cover.py`.
- `x-1-scores.png`, `x-2-institutions.png`, `x-3-rebuttal.png`: 4:5 crops of each poster's top part for the replies in the X thread.

---

## Telegram

**I rebuilt three data posters on ICLR 2027 peer review** 📊

40,544 papers and 125,304 reviews from OpenReview, plus author affiliations from OpenAlex. A few things that stood out:

• **Reviewers are tough.** 57.5% of all ratings were a 2 on the 1–4 scale. The median paper averaged 2.00, and only 15% reached 2.67.

• **The rebuttal works, but less than it looks.** The average rose from 2.06 to 2.28, but about 28% of that is just weak papers being withdrawn (6,127 of them).

• **Talking helps.** Reviewers who joined the discussion raised their score about 6× as often as silent ones (29% vs 5%). 17,373 reviews went up and only 792 went down.

• **Research areas differ, countries don't.** Generative models gained +0.20 after the rebuttal, neurosymbolic AI +0.13. Every big country got about the same +0.2.

• **Bigger is not better.** China (33%) and the US (32%) supply two thirds of the traced papers and score the same. The biggest institutions sit right on the average.

Posters (PNG + PDF), code and my analysis are all open:
https://github.com/abdukarimovhm/iclr_results_poster

Data pipeline adapted from clareLab/posters (MIT).

---

## X thread

Images: post 1 (the main post) gets `x-0-cover.png`; post 2 gets `x-1-scores.png`, post 3 `x-2-institutions.png`, post 4 `x-3-rebuttal.png`; post 5 has no image.
Lengths (URL counted as 23): 238, 185, 221, 228, 210 characters.

**Post 1** (main post, attach `x-0-cover.png`)

I rebuilt three data posters on ICLR 2027 peer review: scores, who submits, and what the rebuttal changed.

40,544 papers, 125,304 reviews, all from OpenReview. Code and full-size posters are open 👇
https://github.com/abdukarimovhm/iclr_results_poster

🧵 Key findings

**Post 2** (attach `x-1-scores.png`)

1/ Scores

Reviewers are tough: 57.5% of all ratings were a 2 (on a 1–4 scale). The median paper averaged 2.00.

Only 15% of papers reached an average of 2.67, and just 4% reached 3.00.

**Post 3** (attach `x-2-institutions.png`)

2/ Who submits

Of the 10,520 papers I could trace to institutions, China (33%) and the US (32%) supply two thirds, and they score the same (2.18).

The biggest institutions sit right on the average. Bigger is not better.

**Post 4** (attach `x-3-rebuttal.png`)

3/ The rebuttal

The average rose from 2.06 to 2.28. About 28% of that is just weak papers being withdrawn.

17,373 reviews went up, 792 went down. Reviewers who joined the discussion raised their score ~6× as often (29% vs 5%).

**Post 5**

4/ How it's made

Python → HTML + inline SVG → headless Chrome → print-size PNG + PDF. Data pipeline adapted from clareLab/posters (MIT).

Everything, including my own analysis, is here:
https://github.com/abdukarimovhm/iclr_results_poster

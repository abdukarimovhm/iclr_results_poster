# Data pipeline: raw data → stats.json

Posters should only read precomputed numbers. Keep three stages, each a separate script with a date `--stamp`:

```
fetch  (API → raw parquet pages, one folder per snapshot date)     fetch.py / openalex.py
stats  (raw → stats.json + CSV tables, all numbers the poster uses) stats.py
poster (stats.json → PNG/PDF)                                       poster script
```

Raw data and API keys live outside the repo (e.g. `~/Documents/data/<project>/` and `~/Documents/data/<service>-api-key`).
Commit only `stats.json` and CSVs, so anyone can re-render the posters without keys.

## Example: OpenReview reviews (ICLR 2027)

- **Fetch.**
  - Page through `https://api2.openreview.net/notes?invitation=<Venue>/-/Submission&details=replies&sort=number:asc&limit=500&offset=…`
    with a Bearer token.
  - Save each page as `page-NNNN.parquet` with columns `id`, `number` and `note` (raw JSON).
  - Resume from the number of existing pages.
  - Back off on errors (10, 30, 90, 300 s).
  - Wait about 2 s between pages.
  - Use a neutral User-Agent naming your project.
- **Snapshots.** Fetch again on later dates (e.g. at review release and after the discussion) into separate stamped folders.
  Compare by review `id` to get rating transitions, and by paper `venue` for status (open, withdrawn, desk rejected).
- **Per-paper stats:**
  - Average of `Official_Review` ratings.
  - Number of reviews.
  - Primary area.
  - Author comments (did they rebut?).
  - Reviewer comments (did the reviewer engage?).
- **Summaries:**
  - Counts per rating.
  - Reviews per paper.
  - Percentiles using `method="inverted_cdf"` so cutoffs are real values.
  - Exact-value table with cumulative "top x%" shares.
  - Bands on thirds (1.00, 1.33, …, 4.00).
  - Share at or above key cutoffs.
  - The same summaries per area.

## Example: OpenAlex affiliations

- **Match** submissions to OpenAlex works by title (fuzzy, e.g. `rapidfuzz`), then confirm by abstract word overlap
  (Jaccard ≥ 0.25). Keep only works posted before the review release, so you don't pick up camera-ready versions.
- **Fractional weights.** Each paper has weight 1, split equally across its authors, then each author's share equally across
  their institutions. A paper with 4 authors, one of whom has 2 affiliations, gives each of those institutions 1/8.
- **Weighted summaries per group** (country, continent, institution, type):
  - `weight = Σw`
  - `mean = Σw·x / Σw`
  - `se = sqrt(Σ w²·(x − mean)²) / Σw`
  - `papers` = number of distinct papers touching the group
  - Shares of open, withdrawn and rebutted papers
- **Say what's missing.** Report how many papers were matched, matched only after the release, or had no affiliation, and
  compare the matched papers' mean to the rest. That number goes in the poster's small print.

## stats.json shape (what the posters read)

```json
{
  "overall": {"submissions": 40544, "reviews": 125304, "mean": 2.06, "median": 2.0, "q1": 1.67, "q3": 2.33,
              "bands": [953, 3476, "..."], "above": {"2.33": 0.379, "2.67": 0.151, "3.00": 0.041}},
  "ratings": {"1": 23782, "2": 72006, "3": 27624, "4": 1892},
  "percentiles": {"99": 3.0, "95": 2.67, "...": "..."},
  "exact": [{"value": 2.0, "count": 12066, "top_from": 0.39, "top_to": 0.69}],
  "areas": {"generative models": {"submissions": 2756, "mean": 2.16, "bands": ["..."], "above": {"...": "..."}}},
  "countries": [{"country": "CN", "papers": 4338, "weight": 3512.75, "mean": 2.18, "se": 0.0065}]
}
```

Also write flat CSVs (`countries.csv`, `institutions.csv`, `areas.csv`) for anyone who wants to analyse the data without
reading JSON.

import argparse
import json
import pathlib

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = pathlib.Path(__file__).parent
DATA = pathlib.Path.home() / "Documents/data/posters/iclr2027/openreview"
QUANTILES = [1, 5, 10, 25, 50, 75, 90, 95, 99]


def load(store: pathlib.Path) -> pd.DataFrame:
    rows = []
    for path in sorted(store.glob("page-*.parquet")):
        table = pq.read_table(path, columns=["number", "note"]).to_pydict()
        for number, raw in zip(table["number"], table["note"]):
            note = json.loads(raw)
            content = note.get("content", {})
            for reply in note.get("details", {}).get("replies", []):
                if reply["invitations"][0].endswith("/-/Official_Review"):
                    rows.append({"number": number, "venue": content.get("venue", {}).get("value", ""), "area": content.get("primary_area", {}).get("value"), "rating": int(reply["content"]["rating"]["value"])})
    reviews = pd.DataFrame(rows)
    return reviews[reviews["venue"] == "ICLR 2027 Conference Submission"].copy()


def summary(part: pd.DataFrame, rows: pd.DataFrame) -> dict:
    values = part["average"].to_numpy()
    q1, median, q3 = np.percentile(values, [25, 50, 75], method="inverted_cdf")
    bands = part["band"].value_counts().reindex(range(10), fill_value=0)
    return {
        "submissions": len(part),
        "reviews": int(len(rows)),
        "mean": float(values.mean()),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "bands": [int(b) for b in bands],
        "above": {f"{c:.2f}": float((values >= c - 1e-9).mean()) for c in (7 / 3, 8 / 3, 3.0)},
    }


def build(stamp: str) -> dict:
    reviews = load(DATA / stamp)
    papers = reviews.groupby("number").agg(average=("rating", "mean"), reviews=("rating", "size"), area=("area", "first")).reset_index()
    papers["band"] = np.floor((papers["average"] - 1) * 3 + 1e-9).astype(int)
    total = len(papers)
    exact = papers["average"].round(4).value_counts().sort_index(ascending=False)
    ladder, above = [], 0
    for value, n in exact.items():
        ladder.append({"value": float(value), "count": int(n), "share": n / total, "first": above + 1, "last": above + int(n), "top_from": above / total, "top_to": (above + n) / total})
        above += int(n)
    return {
        "overall": summary(papers, reviews),
        "ratings": {int(k): int(v) for k, v in reviews["rating"].value_counts().sort_index().items()},
        "per_submission": {int(k): int(v) for k, v in papers["reviews"].value_counts().sort_index().items()},
        "percentiles": {str(q): float(np.percentile(papers["average"], q, method="inverted_cdf")) for q in QUANTILES},
        "exact": ladder,
        "areas": {area: summary(part, reviews[reviews["area"] == area]) for area, part in papers.groupby("area")},
    }


parser = argparse.ArgumentParser()
parser.add_argument("--stamp", default="2026-11-06")
arguments = parser.parse_args()
(HERE / "stats.json").write_text(json.dumps(build(arguments.stamp), indent=1))

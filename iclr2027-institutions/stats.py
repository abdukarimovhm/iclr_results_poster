import argparse
import json
import pathlib
import re

import numpy as np
import pandas as pd

from common import OPENALEX, submissions

HERE = pathlib.Path(__file__).parent
COUNTRIES = json.loads((HERE / "countries.json").read_text())
RELEASE = "2026-11-05"
SIMILAR = 0.25


def words(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def catalogue() -> dict:
    found = {}
    for path in sorted(OPENALEX.glob("works-*.parquet")):
        for work, record in pd.read_parquet(path).itertuples(index=False):
            data = json.loads(record)
            slots = []
            for authorship in data.get("authorships") or []:
                places = [(i["id"].rsplit("/", 1)[-1], i.get("display_name") or "", i.get("country_code") or "", i.get("type") or "") for i in authorship.get("institutions") or [] if i.get("id")]
                if places:
                    slots.append(places)
            found[work] = {"date": data.get("publication_date") or "", "vocabulary": words(" ".join(data.get("abstract_inverted_index") or {})), "slots": slots}
    return found


def match(papers: pd.DataFrame, found: dict, stamp: str) -> pd.DataFrame:
    pairs = pd.read_parquet(OPENALEX / f"candidates-{stamp}.parquet").groupby("number")
    rows = []
    for paper in papers.itertuples(index=False):
        if paper.number not in pairs.groups:
            continue
        mine = words(paper.abstract)
        accepted = []
        for work, title in pairs.get_group(paper.number)[["work", "similarity"]].itertuples(index=False):
            record = found.get(work)
            if not record:
                continue
            union = mine | record["vocabulary"]
            if not record["vocabulary"] or len(mine & record["vocabulary"]) / len(union) >= SIMILAR:
                accepted.append(dict(record, title=title))
        if accepted:
            best = sorted(accepted, key=lambda r: (-len(r["slots"]), -r["title"], r["date"]))[0]
            rows.append({"number": paper.number, "posted": min(r["date"] for r in accepted), "slots": best["slots"]})
    return pd.DataFrame(rows)


def weights(matched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for paper in matched.itertuples(index=False):
        for places in paper.slots:
            for institution, name, country, kind in places:
                rows.append((paper.number, institution, name, country, kind, 1 / len(paper.slots) / len(places)))
    return pd.DataFrame(rows, columns=["number", "institution", "name", "country", "kind", "weight"])


def summarise(table: pd.DataFrame, unit: str, scores: pd.Series, extra: list, median: float) -> list:
    table = table.groupby(["number", unit] + extra, as_index=False)["weight"].sum()
    table["average"] = table["number"].map(scores)
    out = []
    for keys, part in table.groupby([unit] + extra):
        w, x = part["weight"].to_numpy(), part["average"].to_numpy()
        total = w.sum()
        mean = float((w * x).sum() / total)
        record = dict(zip([unit] + extra, keys if isinstance(keys, tuple) else (keys,)))
        record.update({
            "papers": int(part["number"].nunique()),
            "weight": float(total),
            "above": float(w[x > median + 1e-9].sum() / total),
            "mean": mean,
            "se": float(np.sqrt((w**2 * (x - mean) ** 2).sum()) / total),
        })
        out.append(record)
    return sorted(out, key=lambda r: -r["weight"])


def build(stamp: str) -> dict:
    papers = submissions(stamp)
    matched = match(papers, catalogue(), stamp)
    before = matched[(matched["posted"] < RELEASE) & (matched["slots"].map(len) > 0)]
    table = weights(before)
    scores = papers.set_index("number")["average"]
    median = float(np.percentile(scores, 50, method="inverted_cdf"))
    used = scores.loc[before["number"]]
    rest = scores.drop(before["number"])
    table["continent"] = table["country"].map(lambda c: COUNTRIES.get(c, {}).get("continent", ""))
    countries = summarise(table, "country", scores, [], median)
    institutions = summarise(table, "institution", scores, ["name", "country", "kind"], median)
    overall = {
        "stamp": stamp,
        "release": RELEASE,
        "median": median,
        "under_review": int(len(papers)),
        "matched": int(len(matched)),
        "after_release": int((matched["posted"] >= RELEASE).sum()),
        "without_affiliation": int(((matched["posted"] < RELEASE) & (matched["slots"].map(len) == 0)).sum()),
        "used": int(len(before)),
        "above": float((used > median + 1e-9).mean()),
        "mean_used": float(used.mean()),
        "sd_used": float(used.std()),
        "mean_rest": float(rest.mean()),
        "mean_all": float(scores.mean()),
        "countries": len([c for c in countries if c["country"]]),
        "institutions": len(institutions),
    }
    return {
        "overall": overall,
        "countries": countries,
        "institutions": institutions,
        "kinds": summarise(table, "kind", scores, [], median),
        "continents": summarise(table, "continent", scores, [], median),
    }


def tables(stats: dict) -> None:
    used = stats["overall"]["used"]
    columns = {"weight": "submissions", "papers": "papers", "above": "above_median", "mean": "score", "se": "standard_error"}
    for name, rows, keys in (
        ("institutions", stats["institutions"], ["institution", "name", "country", "kind"]),
        ("countries", stats["countries"], ["country"]),
        ("continents", stats["continents"], ["continent"]),
        ("types", stats["kinds"], ["kind"]),
    ):
        frame = pd.DataFrame(rows)
        frame["share"] = frame["weight"] / used
        if "country" in keys:
            frame["country_name"] = frame["country"].map(lambda c: COUNTRIES.get(c, {}).get("name", ""))
            keys = keys[: keys.index("country") + 1] + ["country_name"] + keys[keys.index("country") + 1 :]
        frame = frame[keys + ["weight", "papers", "share", "above", "mean", "se"]].rename(columns=columns | {"kind": "type"})
        frame.round({"submissions": 4, "share": 6, "above_median": 6, "score": 4, "standard_error": 4}).to_csv(HERE / f"{name}.csv", index=False, encoding="utf-8-sig")


parser = argparse.ArgumentParser()
parser.add_argument("--stamp", default="2026-11-06")
arguments = parser.parse_args()
stats = build(arguments.stamp)
(HERE / "stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False))
tables(stats)

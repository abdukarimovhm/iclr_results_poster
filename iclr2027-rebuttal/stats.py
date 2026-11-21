import argparse
import collections
import datetime
import json
import pathlib
import re

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = pathlib.Path(__file__).parent
ROOT = pathlib.Path.home() / "Documents/data/posters/iclr2027"
OPENREVIEW = ROOT / "openreview"
OPENALEX = ROOT / "openalex"
COUNTRIES = json.loads((HERE / "countries.json").read_text())
STORE = ROOT / "rebuttal"
RELEASE = "2026-11-05"
SIMILAR = 0.25
OPEN = "ICLR 2027 Conference Submission"
STATUS = {OPEN: "open", "ICLR 2027 Conference Withdrawn Submission": "withdrawn", "ICLR 2027 Conference Desk Rejected Submission": "desk"}
AOE = datetime.timezone(datetime.timedelta(hours=-12))


def value(content: dict, key: str):
    v = content.get(key, {})
    return v.get("value") if isinstance(v, dict) else None


def snapshot(stamp: str) -> tuple:
    papers, reviews, comments = {}, [], []
    for path in sorted((OPENREVIEW / stamp).glob("page-*.parquet")):
        table = pq.read_table(path, columns=["number", "note"]).to_pydict()
        for number, raw in zip(table["number"], table["note"]):
            note = json.loads(raw)
            content = note.get("content", {})
            papers[number] = {"venue": value(content, "venue"), "title": value(content, "title") or "", "abstract": value(content, "abstract") or "", "area": value(content, "primary_area") or ""}
            for reply in note.get("details", {}).get("replies", []):
                kind = reply["invitations"][0].rsplit("/-/", 1)[-1]
                who = reply["signatures"][0].rsplit("/", 1)[-1]
                if kind == "Official_Review":
                    reviews.append((number, reply["id"], who, int(reply["content"]["rating"]["value"])))
                elif kind == "Official_Comment":
                    comments.append((number, who, reply["cdate"]))
    return papers, pd.DataFrame(reviews, columns=["number", "id", "reviewer", "rating"]), pd.DataFrame(comments, columns=["number", "who", "cdate"])


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
    frame = pd.DataFrame(rows, columns=["number", "institution", "name", "country", "kind", "weight"])
    frame["continent"] = frame["country"].map(lambda c: COUNTRIES.get(c, {}).get("continent", ""))
    return frame


def papers(before: str, after: str) -> tuple:
    old, old_reviews, _ = snapshot(before)
    new, new_reviews, comments = snapshot(after)
    initial = old_reviews.groupby("number")["rating"].agg(["mean", "size"])
    base = pd.DataFrame([{"number": n, **p} for n, p in old.items() if p["venue"] == OPEN and n in initial.index])
    base["status"] = base["number"].map(lambda n: STATUS.get(new.get(n, {}).get("venue"), "missing"))
    base["initial"] = base["number"].map(initial["mean"])
    final = new_reviews.groupby("number")["rating"].mean()
    base["final"] = base["number"].map(final).where(base["status"] == "open")
    reviews = old_reviews[old_reviews["number"].isin(base["number"])].merge(new_reviews[["id", "rating"]], on="id", how="outer", suffixes=("_before", "_after"))
    reviews["number"] = reviews["number"].fillna(reviews["id"].map(new_reviews.set_index("id")["number"]))
    reviews = reviews[reviews["number"].isin(base["number"])].copy()
    reviews["number"] = reviews["number"].astype(int)
    reviews["reviewer"] = reviews["id"].map(pd.concat([old_reviews, new_reviews]).drop_duplicates("id").set_index("id")["reviewer"])
    replied = set(zip(comments["number"], comments["who"]))
    reviews["replied"] = [(n, r) in replied for n, r in zip(reviews["number"], reviews["reviewer"])]
    compared = reviews.dropna(subset=["rating_before", "rating_after"])
    tally = compared.assign(up=compared["rating_after"] > compared["rating_before"], down=compared["rating_after"] < compared["rating_before"]).groupby("number")[["up", "down"]].agg(["sum", "size"])
    base["compared"] = base["number"].map(tally[("up", "size")]).fillna(0).astype(int)
    base["raised"] = base["number"].map(tally[("up", "sum")]).fillna(0).astype(int)
    base["lowered"] = base["number"].map(tally[("down", "sum")]).fillna(0).astype(int)
    base["added"] = base["number"].map(reviews[reviews["rating_before"].isna()].groupby("number").size()).fillna(0).astype(int)
    roles = comments.assign(role=comments["who"].map(lambda w: "authors" if w == "Authors" else "reviewer" if w.startswith("Reviewer") else "chair" if w.startswith("Area_Chair") else "other"))
    for role in ("authors", "reviewer", "chair"):
        base[f"{role}_comments"] = base["number"].map(roles[roles["role"] == role].groupby("number").size()).fillna(0).astype(int)
    roles = roles[roles["number"].isin(base["number"])].copy()
    roles["day"] = pd.to_datetime(roles["cdate"], unit="ms", utc=True).dt.tz_convert(AOE).dt.strftime("%Y-%m-%d")
    return base, reviews, roles


def mean(w: np.ndarray, x: np.ndarray) -> tuple:
    total = w.sum()
    if total <= 0:
        return None, None
    m = float((w * x).sum() / total)
    return m, float(np.sqrt((w**2 * (x - m) ** 2).sum()) / total)


def summarise(frame: pd.DataFrame, base: pd.DataFrame, keys: list, medians: tuple) -> list:
    table = frame.groupby(["number"] + keys, as_index=False)["weight"].sum().merge(base, on="number")
    out = []
    for group, part in table.groupby(keys):
        w = part["weight"].to_numpy()
        kept = part[part["status"] == "open"]
        wk = kept["weight"].to_numpy()
        record = dict(zip(keys, group if isinstance(group, tuple) else (group,)))
        initial, initial_se = mean(w, part["initial"].to_numpy())
        final, final_se = mean(wk, kept["final"].to_numpy())
        gain, gain_se = mean(wk, (kept["final"] - kept["initial"]).to_numpy())
        kept_initial, _ = mean(wk, kept["initial"].to_numpy())
        rated = part[part["compared"] > 0]
        record.update({
            "papers": int(part["number"].nunique()),
            "weight": float(w.sum()),
            "open": float(wk.sum()),
            "withdrawn": float(part.loc[part["status"] == "withdrawn", "weight"].sum() / w.sum()),
            "desk": float(part.loc[part["status"] == "desk", "weight"].sum() / w.sum()),
            "initial": initial,
            "initial_se": initial_se,
            "kept_initial": kept_initial,
            "final": final,
            "final_se": final_se,
            "gain": gain,
            "gain_se": gain_se,
            "raised": float((rated["weight"] * rated["raised"] / rated["compared"]).sum() / rated["weight"].sum()) if len(rated) else None,
            "lowered": float((rated["weight"] * rated["lowered"] / rated["compared"]).sum() / rated["weight"].sum()) if len(rated) else None,
            "rebuttal": float((part["weight"] * (part["authors_comments"] > 0)).sum() / w.sum()),
            "above_initial": float((part["weight"] * (part["initial"] > medians[0] + 1e-9)).sum() / w.sum()),
            "above_final": float((kept["weight"] * (kept["final"] > medians[1] + 1e-9)).sum() / wk.sum()) if wk.sum() > 0 else None,
        })
        out.append(record)
    return sorted(out, key=lambda r: -r["weight"])


def counts(series: pd.Series) -> dict:
    return {f"{k:.4f}": int(v) for k, v in series.round(4).value_counts().sort_index().items()}


def build(before: str, after: str) -> dict:
    base, reviews, roles = papers(before, after)
    found = catalogue()
    matched = match(base[["number", "abstract"]], found, before)
    used = matched[(matched["posted"] < RELEASE) & (matched["slots"].map(len) > 0)]
    long = weights(used)
    columns = base.drop(columns=["title", "abstract", "venue", "area"])
    kept = base[base["status"] == "open"]
    medians = (float(np.percentile(base["initial"], 50, method="inverted_cdf")), float(np.percentile(kept["final"], 50, method="inverted_cdf")))
    compared = reviews.dropna(subset=["rating_before", "rating_after"])
    flows = collections.Counter()
    for paper in base.itertuples(index=False):
        flows[(f"{paper.initial:.4f}", f"{paper.final:.4f}" if paper.status == "open" else paper.status)] += 1
    daily = roles.groupby(["day", "role"]).size().unstack(fill_value=0)
    flat = base[["number", "area"]].assign(weight=1.0)
    overall = {
        "before": before,
        "after": after,
        "release": RELEASE,
        "base": int(len(base)),
        "status": {k: int(v) for k, v in base["status"].value_counts().items()},
        "median_initial": medians[0],
        "median_final": medians[1],
        "mean_initial": float(base["initial"].mean()),
        "mean_kept_initial": float(kept["initial"].mean()),
        "mean_final": float(kept["final"].mean()),
        "mean_withdrawn_initial": float(base.loc[base["status"] == "withdrawn", "initial"].mean()),
        "reviews_before": int(reviews["rating_before"].notna().sum()),
        "reviews_after": int(reviews["rating_after"].notna().sum()),
        "reviews_compared": int(len(compared)),
        "reviews_raised": int((compared["rating_after"] > compared["rating_before"]).sum()),
        "reviews_lowered": int((compared["rating_after"] < compared["rating_before"]).sum()),
        "reviews_added": int(reviews["rating_before"].isna().sum()),
        "reviews_removed": int(reviews["rating_after"].isna().sum()),
        "reviews_replied": float(reviews.loc[reviews["rating_before"].notna(), "replied"].mean()),
        "papers_rebuttal": float((base["authors_comments"] > 0).mean()),
        "papers_rebuttal_open": float((kept["authors_comments"] > 0).mean()),
        "papers_changed": int((kept["final"] - kept["initial"]).abs().gt(1e-9).sum()),
        "comments": {role: int(roles.loc[roles["role"] == role].shape[0]) for role in ("authors", "reviewer", "chair", "other")},
        "matched": int(len(matched)),
        "after_release": int((matched["posted"] >= RELEASE).sum()),
        "without_affiliation": int(((matched["posted"] < RELEASE) & (matched["slots"].map(len) == 0)).sum()),
        "used": int(len(used)),
        "used_status": {k: int(v) for k, v in base[base["number"].isin(used["number"])]["status"].value_counts().items()},
        "used_mean_initial": float(base[base["number"].isin(used["number"])]["initial"].mean()),
        "rest_mean_initial": float(base[~base["number"].isin(used["number"])]["initial"].mean()),
        "countries": int(long["country"].replace("", np.nan).dropna().nunique()),
        "institutions": int(long["institution"].nunique()),
    }
    transitions = compared.groupby(["rating_before", "rating_after"]).size()
    rated = reviews[reviews["rating_before"].notna()]
    raised = compared.assign(up=compared["rating_after"] > compared["rating_before"])
    STORE.mkdir(parents=True, exist_ok=True)
    base.drop(columns=["abstract"]).to_parquet(STORE / "papers.parquet")
    reviews.to_parquet(STORE / "reviews.parquet")
    long.merge(columns, on="number").to_parquet(STORE / "weights.parquet")
    return {
        "overall": overall,
        "transitions": [{"before": int(b), "after": int(a), "reviews": int(n)} for (b, a), n in transitions.items()],
        "added": {str(int(k)): int(v) for k, v in reviews.loc[reviews["rating_before"].isna(), "rating_after"].value_counts().sort_index().items()},
        "removed": {str(int(k)): int(v) for k, v in reviews.loc[reviews["rating_after"].isna(), "rating_before"].value_counts().sort_index().items()},
        "replied": {str(int(k)): float(v) for k, v in rated.groupby("rating_before")["replied"].mean().sort_index().items()},
        "raised": {f"{int(k)}:{int(r)}": float(v) for (k, r), v in raised.groupby(["rating_before", "replied"])["up"].mean().items()} | {f"all:{int(r)}": float(v) for r, v in raised.groupby("replied")["up"].mean().items()},
        "flows": [{"initial": i, "outcome": o, "papers": n} for (i, o), n in sorted(flows.items())],
        "initial_values": counts(base["initial"]),
        "final_values": counts(kept["final"]),
        "daily": [{"day": day, **{role: int(row.get(role, 0)) for role in ("authors", "reviewer", "chair")}} for day, row in daily.iterrows()],
        "matched": summarise(long.assign(scope="matched"), columns, ["scope"], medians)[0],
        "areas": summarise(flat, columns, ["area"], medians),
        "countries": summarise(long, columns, ["country"], medians),
        "continents": summarise(long, columns, ["continent"], medians),
        "kinds": summarise(long, columns, ["kind"], medians),
        "institutions": summarise(long, columns, ["institution", "name", "country", "kind"], medians),
    }


def tables(stats: dict) -> None:
    used = stats["overall"]["used"]
    columns = ["weight", "papers", "share", "withdrawn", "desk", "open", "initial", "initial_se", "kept_initial", "final", "final_se", "gain", "gain_se", "raised", "lowered", "rebuttal", "above_initial", "above_final"]
    names = {"weight": "submissions", "open": "open_submissions", "initial": "initial_score", "initial_se": "initial_standard_error", "kept_initial": "open_initial_score", "final": "final_score", "final_se": "final_standard_error", "gain": "score_change", "gain_se": "score_change_standard_error", "raised": "reviews_raised", "lowered": "reviews_lowered", "above_initial": "initial_above_median", "above_final": "final_above_median", "kind": "type"}
    for name, rows, keys, total in (
        ("institutions", stats["institutions"], ["institution", "name", "country", "kind"], used),
        ("countries", stats["countries"], ["country"], used),
        ("continents", stats["continents"], ["continent"], used),
        ("types", stats["kinds"], ["kind"], used),
        ("areas", stats["areas"], ["area"], stats["overall"]["base"]),
    ):
        frame = pd.DataFrame(rows)
        frame["share"] = frame["weight"] / total
        if "country" in keys:
            frame["country_name"] = frame["country"].map(lambda c: COUNTRIES.get(c, {}).get("name", ""))
            keys = keys[: keys.index("country") + 1] + ["country_name"] + keys[keys.index("country") + 1 :]
        frame[keys + columns].rename(columns=names).round(6).to_csv(HERE / f"{name}.csv", index=False, encoding="utf-8-sig")


parser = argparse.ArgumentParser()
parser.add_argument("--before", default="2026-11-06")
parser.add_argument("--after", default="2026-11-19")
arguments = parser.parse_args()
stats = build(arguments.before, arguments.after)
(HERE / "stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False))
tables(stats)

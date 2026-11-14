import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein

from common import AGENT, KEY, OPENALEX, key, submissions

ARXIV = "S4306400194"
SINCE = "2025-06-01"
SIMILAR = 0.9


def get(params: dict) -> dict:
    params = dict(params, api_key=KEY.read_text().strip())
    request = urllib.request.Request(f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}", headers={"User-Agent": AGENT})
    for wait in (5, 15, 60, 180, 0):
        try:
            with urllib.request.urlopen(request, timeout=120) as reply:
                return json.load(reply)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print("retry", type(error).__name__, error, flush=True)
            if not wait:
                raise
            time.sleep(wait)


def titles() -> None:
    OPENALEX.mkdir(parents=True, exist_ok=True)
    state_file = OPENALEX / "cursor.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"cursor": "*", "chunk": 0}
    rows = []
    while state["cursor"]:
        data = get({"filter": f"locations.source.id:{ARXIV},from_publication_date:{SINCE}", "select": "id,display_name,publication_date", "per_page": 200, "cursor": state["cursor"]})
        rows += [(w["id"].rsplit("/", 1)[-1], w.get("display_name") or "", w.get("publication_date") or "") for w in data["results"]]
        state["cursor"] = data["meta"].get("next_cursor")
        if len(rows) >= 10000 or not state["cursor"]:
            pd.DataFrame(rows, columns=["work", "title", "date"]).to_parquet(OPENALEX / f"titles-{state['chunk']:04d}.parquet")
            state["chunk"] += 1
            rows = []
            state_file.write_text(json.dumps(state))
            print("chunk", state["chunk"], flush=True)
        time.sleep(0.2)


def candidates(stamp: str) -> pd.DataFrame:
    catalogue = pd.concat(pd.read_parquet(f) for f in sorted(OPENALEX.glob("titles-*.parquet"))).drop_duplicates("work")
    catalogue["key"] = catalogue["title"].map(key)
    catalogue = catalogue[catalogue["key"] != ""]
    papers = submissions(stamp)
    papers = papers[papers["key"] != ""]
    keys, ids = catalogue["key"].tolist(), catalogue["work"].to_numpy()
    queries, numbers = papers["key"].tolist(), papers["number"].to_numpy()
    rows = []
    for start in range(0, len(queries), 256):
        scores = process.cdist(queries[start : start + 256], keys, scorer=Levenshtein.normalized_similarity, score_cutoff=SIMILAR, dtype=np.float32, workers=8)
        for r, c in zip(*np.nonzero(scores >= SIMILAR)):
            rows.append((int(numbers[start + r]), str(ids[c]), float(scores[r, c])))
    table = pd.DataFrame(rows, columns=["number", "work", "similarity"])
    table.to_parquet(OPENALEX / f"candidates-{stamp}.parquet")
    print("candidates", table["number"].nunique(), "submissions,", len(table), "pairs", flush=True)
    return table


def works(stamp: str) -> None:
    wanted = sorted(set(candidates(stamp)["work"]))
    have = set()
    for path in OPENALEX.glob("works-*.parquet"):
        have |= set(pd.read_parquet(path, columns=["work"])["work"])
    todo = [w for w in wanted if w not in have]
    part = len(list(OPENALEX.glob("works-*.parquet")))
    for start in range(0, len(todo), 2000):
        rows = []
        for batch in range(start, min(start + 2000, len(todo)), 50):
            ids = todo[batch : batch + 50]
            data = get({"filter": "ids.openalex:" + "|".join(ids), "select": "id,display_name,publication_date,authorships,abstract_inverted_index", "per_page": 50})
            rows += [(w["id"].rsplit("/", 1)[-1], json.dumps(w)) for w in data["results"]]
            time.sleep(0.2)
        pd.DataFrame(rows, columns=["work", "record"]).to_parquet(OPENALEX / f"works-{part:04d}.parquet")
        part += 1
        print("works", start + len(rows), "of", len(todo), flush=True)


parser = argparse.ArgumentParser()
parser.add_argument("step", choices=["titles", "works"])
parser.add_argument("--stamp", default="2026-11-06")
arguments = parser.parse_args()
titles() if arguments.step == "titles" else works(arguments.stamp)

import json
import pathlib
import re
import unicodedata

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = pathlib.Path.home() / "Documents/data/posters/iclr2027"
OPENREVIEW = ROOT / "openreview"
OPENALEX = ROOT / "openalex"
KEY = pathlib.Path.home() / "Documents/data/openalex-api-key"
AGENT = "clareLab posters"


def key(title: str) -> str:
    text = re.sub(r"\.pdf$", "", (title or "").strip(), flags=re.I)
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = text.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def submissions(stamp: str) -> pd.DataFrame:
    rows = []
    for path in sorted((OPENREVIEW / stamp).glob("page-*.parquet")):
        table = pq.read_table(path, columns=["number", "note"]).to_pydict()
        for number, raw in zip(table["number"], table["note"]):
            note = json.loads(raw)
            content = note.get("content", {})
            if content.get("venue", {}).get("value") != "ICLR 2027 Conference Submission":
                continue
            ratings = [int(r["content"]["rating"]["value"]) for r in note.get("details", {}).get("replies", []) if r["invitations"][0].endswith("/-/Official_Review")]
            if ratings:
                rows.append({"number": number, "title": content.get("title", {}).get("value", ""), "abstract": content.get("abstract", {}).get("value", ""), "area": content.get("primary_area", {}).get("value", ""), "average": float(np.mean(ratings))})
    frame = pd.DataFrame(rows)
    frame["key"] = frame["title"].map(key)
    return frame

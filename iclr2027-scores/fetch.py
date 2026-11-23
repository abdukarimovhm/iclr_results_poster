import argparse
import datetime
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

DATA = pathlib.Path.home() / "Documents/data/posters/iclr2027/openreview"
TOKEN = pathlib.Path.home() / "Documents/data/openreview-api-key"


def crawl(stamp: str, pace: float, size: int = 500) -> None:
    headers = {"Authorization": f"Bearer {TOKEN.read_text().strip()}", "User-Agent": "iclr_results_poster"}
    store = DATA / stamp
    store.mkdir(parents=True, exist_ok=True)
    page = len(list(store.glob("page-*.parquet")))
    while True:
        query = urllib.parse.urlencode({"invitation": "ICLR.cc/2027/Conference/-/Submission", "details": "replies", "sort": "number:asc", "limit": size, "offset": page * size})
        request = urllib.request.Request(f"https://api2.openreview.net/notes?{query}", headers=headers)
        for wait in (10, 30, 90, 300, 0):
            try:
                with urllib.request.urlopen(request, timeout=900) as reply:
                    notes = json.load(reply)["notes"]
                break
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                print(f"page {page}: {type(error).__name__} {error}", flush=True)
                if not wait:
                    raise
                time.sleep(wait)
        if not notes:
            break
        pd.DataFrame({"id": [n["id"] for n in notes], "number": [n.get("number") for n in notes], "note": [json.dumps(n) for n in notes]}).to_parquet(store / f"page-{page:04d}.parquet")
        replies = sum(len(n.get("details", {}).get("replies", [])) for n in notes)
        print(f"page {page}: {len(notes)} submissions, {replies} replies", flush=True)
        page += 1
        if len(notes) < size:
            break
        time.sleep(pace)


parser = argparse.ArgumentParser()
parser.add_argument("--stamp", default=datetime.date.today().isoformat())
parser.add_argument("--pace", type=float, default=2.0)
arguments = parser.parse_args()
crawl(arguments.stamp, arguments.pace)

iclr2027-scores-fetch stamp:
    uv run python iclr2027-scores/fetch.py --stamp {{stamp}}

iclr2027-scores stamp="2026-11-06":
    uv run python iclr2027-scores/stats.py --stamp {{stamp}}
    uv run python iclr2027-scores/poster.py

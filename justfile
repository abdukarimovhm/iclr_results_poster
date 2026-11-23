iclr2027-scores-fetch stamp:
    uv run python iclr2027-scores/fetch.py --stamp {{stamp}}

iclr2027-scores stamp="2026-11-06":
    uv run python iclr2027-scores/stats.py --stamp {{stamp}}
    uv run python posters/scores.py

iclr2027-institutions-fetch stamp="2026-11-06":
    uv run python iclr2027-institutions/openalex.py titles
    uv run python iclr2027-institutions/openalex.py works --stamp {{stamp}}

iclr2027-institutions stamp="2026-11-06":
    uv run python iclr2027-institutions/stats.py --stamp {{stamp}}
    uv run python posters/institutions.py

iclr2027-rebuttal before="2026-11-06" after="2026-11-19":
    uv run python iclr2027-rebuttal/stats.py --before {{before}} --after {{after}}
    uv run python posters/rebuttal.py

posters:
    uv run python posters/scores.py
    uv run python posters/institutions.py
    uv run python posters/rebuttal.py

analysis:
    uv run python analysis/rebuttal_analysis.py

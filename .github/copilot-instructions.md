# Project instructions

- Python 3.10+. Keep the two-step scope explicit: (1) preprocessing into sessions, (2) habit discovery with DBSCAN per resident × room.
- Never use `activity_label` as a feature; it exists only to score results.
- Raw data is immutable and not committed; `data/processed/` is regenerated; `reports/results/` is committed because the report cites it.
- Every behaviour change needs a test (`python -m pytest`). Keep experiments reproducible (fixed seed) and re-run `smart-home run` / `smart-home experiments` after changing the method.

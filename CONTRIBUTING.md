# Contributing

Run the local path before opening a change:

```text
python scripts/01_generate_sample_data.py
python scripts/02_validate_sample_data.py
pytest
ruff check .
ruff format --check .
```

Keep detection free of ground-truth labels. Keep recommendation actions behind human approval. Do not add secrets, real tenant ids, or production project names. If a CDF API is unavailable, add a documented fallback instead of a function that only passes.

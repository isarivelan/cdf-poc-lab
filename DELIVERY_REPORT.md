# Delivery report

Local proof of concept for the CDF Intelligent Maintenance Investigator. Nothing was deployed to Cognite Data Fusion.

## Validation that completed

| Command | Result |
| --- | --- |
| `python scripts/01_generate_sample_data.py` | 198,314 sensor rows and 3 expected incidents |
| `python scripts/02_validate_sample_data.py` | Missing 1.63%, 0 duplicates, 0 out of range |
| `pytest` | 33 passed, 1 skipped (CDF credentials absent), coverage 91.75% |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed |
| `python -m compileall -q app src scripts functions` | Passed |
| `cdf build --env dev` | Built 47 resources. One warning: group placeholder `replace-with-dataset-id` |
| Streamlit at `http://localhost:8501` | Home, equipment, anomaly, and investigation pages rendered the Pump P-101 story |

The CDF contract test was skipped because `CDF_PROJECT`, `CDF_CLIENT_ID`, and `CDF_CLIENT_SECRET` were not set. No Toolkit deploy, dry-run against a tenant, or second CDF ingest was run.

## Detection result

- `INC-P101-20261108-1000` warning, health 75, `PUMP-P101`
- `INC-P101-20261110-1409` warning, health 75, `PUMP-P101`
- `INC-P101-20261111-2000` critical, health 38, `PUMP-P101`

The investigation selected in the UI is the critical incident. Confidence is 0.78 from the mock investigator. WO-2025-001 ranks first. Manual sections include `SEC-VIBRATION-001` and `SEC-BEARING-001`. Recommended actions require human approval.

## Mock and tenant boundaries

Mock: local repository, mock investigator, notification file, disabled work-order gateway, Markdown section parser.

Needs a development CDF tenant: data-model deploy, time series and datapoints, RAW and the transformation, functions, and the workflow.

Needs an external AI provider: `AI_PROVIDER=openai_compatible` with `AI_ENDPOINT` and `AI_API_KEY`. Local and hybrid modes fall back to the mock investigator when those are empty.

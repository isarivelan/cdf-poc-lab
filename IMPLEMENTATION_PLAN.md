# Implementation plan

CDF Intelligent Maintenance Investigator. The repository root is this workspace.
The project virtual environment resolved `cognite-sdk` 8.24.0 and `cognite-toolkit` 0.9.79.
The project declares `requires-python >= 3.11`. `cdf.toml` records module version 0.9.79, the CLI that built the module.

## Decisions

- Local mode is the default and does not read CDF or AI credentials.
- Toolkit groups live under `modules/maintenance_investigator/auth/` because Toolkit 0.9 loads groups from `auth`, not `groups`.
- Data-model resources live under `data_modeling/` (`Space`, `Container`, `View`, `DataModel`, `Node`, `Edge`). A `data_models/` folder would not be loaded as its own kind.
- Incidents and investigations are data-model nodes. A classic-event payload is built for optional use and is not written unless `CDF_WRITE_CLASSIC_EVENTS=true`.
- Document contextualization uses a replaceable section parser over the synthetic manual. Native CDF document extraction is not required.
- Mock AI is deterministic. An OpenAI-compatible adapter is optional and unused when credentials are absent.
- Same-severity anomaly runs separated by less than 15 minutes become one incident. A severity increase opens a new incident so the warning period and the critical period both remain visible.
- Detection never reads `ground_truth`. Labels are for validation only.
- Cleanup of CDF resources requires `CDF_CONFIRM_CLEANUP=yes` and refuses any project name containing `prod`.
- No secrets, tenant IDs, or project names are committed. `.env.example` values are empty.

## Health score

Start at 100. In the incident window, deduct at most one band per signal:

| Signal | Condition | Deduction |
| --- | --- | --- |
| Drive-end vibration | max >= 7.1 mm/s, else >= 4.5 | 18, else 10 |
| Drive-end bearing temperature | max >= 82 °C, else >= 75 | 16, else 8 |
| Flow | min <= 82 m³/h, else <= 88 | 12, else 6 |
| Motor current | max >= 46 A, else >= 44 | 8, else 5 |
| Breadth | 3 or more of those signals in a warning-or-worse band | 8 |

Then cap a critical window at 45 and a warning window at 75, and clamp to 0–100.
The full critical pattern scores 38. The score is a transparent penalty model, not a probability of failure.

## Checklist

### Phase 1 — Structure, configuration, models

- [x] Repository metadata, tooling, and environment example
- [x] Pydantic domain models and settings validation
- [x] Logging, exceptions, identifiers

### Phase 2 — Sample data

- [x] Deterministic 14-day generator
- [x] Source master data and synthetic manual
- [x] Validation script and expected-incident file

### Phase 3 — Local repository

- [x] Local JSON/CSV repository
- [x] Idempotent ingestion helpers

### Phase 4 — Detection and health

- [x] Externalized rules
- [x] Duration, shutdown exclusion, spike suppression
- [x] Features, statistical signals, health score

### Phase 5 — Incidents

- [x] Merge policy and idempotent incident ids

### Phase 6 — Context

- [x] Work-order ranking
- [x] Manual section linking

### Phase 7 — Evidence

- [x] Context package and evidence registry
- [x] Citation checks

### Phase 8 — Investigation

- [x] Mock investigator and schema
- [x] Recommendation templates and human approval
- [x] Safe fallback when model output is invalid

### Phase 9 — Streamlit

- [x] Six workflow pages plus home
- [x] Local, CDF, and hybrid modes
- [x] Decision-support notice

### Phase 10 — CDF

- [x] SDK client compatible with cognite-sdk 8.24
- [x] Ingestion, detection, investigation, verify, and cleanup scripts

### Phase 11 — Toolkit

- [x] Module validated against Toolkit 0.9.79 classes and `cdf build`
- [x] Functions and workflow definition

### Phase 12 — Proof

- [x] Unit, integration, and contract tests
- [x] Ruff, pytest, sample-data validation
- [x] README, security, demo guide, CI, Docker
- [x] Delivery report with commands actually run

## Blockers

CDF deployment was not executed. No development credentials were supplied, and production deployment is out of scope.

`cdf build` completed locally with one warning: the example group references the placeholder data-set id `replace-with-dataset-id`. Replace it before deploying the group. Operating detection uses motor speed of at least 1400 rpm so start-up flow does not become a critical incident.

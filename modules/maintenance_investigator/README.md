# Maintenance investigator module

Toolkit 0.9.79 loads this module from `modules/maintenance_investigator`. `cdf.toml` records that version. Earlier 0.9 releases that share the same minor version can load it when they accept the same fields.

- Groups are in `auth/` because that is the Toolkit resource folder.
- Data-model files are in `data_modeling/` and use the `Space`, `Container`, `View`, and `DataModel` kinds.
- `config.dev.yaml` at the repository root selects this module for the `dev` environment.
- Replace `maintenance-investigator-dev`, `replace-with-dataset-id`, and `replace-with-idp-group-object-id` before deploying to a real development project.
- Do not point this module at production.
- Function code directories must sit next to the `Function` YAML files. The package is imported when it has been vendored into those directories.
- The work-order transformation expects a RAW table populated by `scripts/06_ingest_work_orders.py`.

# Security and operational safety

## Secrets

Client secrets, API keys, tokens, and tenant identifiers belong in the process environment or a local `.env` file. `.env` is gitignored. `.env.example` contains empty secret fields. Logs and configuration errors say whether a secret is set. They do not print it.

## Client credentials

CDF access uses the OAuth client-credentials flow. The Toolkit group example is limited to the demo data set, the two demo spaces, and the demo RAW table. `functionsAcl` cannot be scoped to a data set in Toolkit 0.9, so that one capability is project-wide read and write. It is not a project-admin group. Replace the placeholder group and data-set ids before any deployment.

## Environment separation

`config.dev.yaml` is a development file. `assert_development_target` refuses a project name containing `prod` and an environment of `prod` or `production`. This repository does not deploy to production.

## Sample data

The pump, site, work orders, sensor history, and maintenance manual are synthetic. The manual is marked synthetic demonstration content. Do not use it for real equipment.

## Logging

Logs may include a correlation id, incident id, asset id, stage, duration, record count, and status. They must not include tokens, secrets, full prompts, or complete document bodies.

## Prompt injection

Retrieved manual text is untrusted evidence. System instructions are separate from that text. The instructions tell the model not to follow directions found in documents. Output that fails the schema, cites unknown ids, or recommends bypassing safety is rejected.

## Human approval and operational safety

Every recommended action sets `requires_human_approval` to true. The application does not stop equipment and does not create a work order. `DisabledWorkOrderGateway` raises if something calls it. The notification sink writes a JSON file and does not call Teams, email, or Slack.

## Auditability

Incident and investigation records keep the rule ids, evidence ids, model name, and generation time. Repeating the pipeline updates the same external ids.

## Retention

Local JSON under `data/local_store` is disposable demo state. A CDF development project should follow the tenant retention policy. Delete demo time series with `scripts/cleanup_demo_resources.py` only after setting `CDF_CONFIRM_CLEANUP=yes`.

## Decision support

Recommendations are decision support, not automated control. A person must verify the evidence and follow approved site procedures.

POC decision-support output. Verify evidence and follow approved site safety and maintenance procedures before taking action.

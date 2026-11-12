# Ten-minute demonstration

Use local mode when CDF or an AI service is unavailable. That is the fallback path and the expected path for this repository.

```text
python scripts/01_generate_sample_data.py
streamlit run app/Home.py
```

Optional replay of the critical window, printing one minute every twentieth of a second:

```text
python scripts/replay_demo.py --speed 1200 --max-steps 8
```

## Minute 1 — the problem

On the home page, explain that a cooling-water pump can show rising vibration without telling the engineer which bearing, which past repair, or which manual section matters. The application keeps hypotheses separate from facts.

## Minute 2 — the asset

Open Equipment overview. Show Chennai Manufacturing Demo Site, Utilities Area, Cooling Water System, and PUMP-P101, plus motor M-101, valve V-101, and the two bearings. The current health score is 38 because the extract ends inside the critical window.

## Minutes 3 and 4 — normal operation, then degradation

Open Anomaly detection. The early days stay inside the normal vibration band, about 2 to 3.5 mm/s. A planned shutdown on 4 November does not create an incident. A one-minute spike does not create a critical incident. From 10 November the drive-end vibration and bearing temperature climb together.

## Minute 5 — the critical incident

The shaded window from 11 November 20:00 is critical. Drive-end vibration stays above 7.1 mm/s, bearing temperature above 82 °C, flow below 82 m³/h, and motor current above 46 A. The incident id is `INC-P101-20261111-2000`.

## Minute 6 — the investigation

Open Incident investigation and select that incident. Read the summary, the health score of 38, and the hypothesis. The wording says it is a hypothesis, not a diagnosis.

## Minute 7 — history

Open Maintenance history. WO-2025-001, drive-end bearing replacement after lubrication degradation, ranks first. WO-2025-002, coupling alignment, is also near the top. Ranking uses the asset, component, failure mode, cause, recency, and completeness.

## Minute 8 — the manual

Open Technical documents. Search for `SEC-VIBRATION-001` and `SEC-BEARING-001`. The manual is marked synthetic.

## Minute 9 — actions

Return to the investigation. Each action names its template or section and says human approval is required. The banner states that the output is decision support.

## Minute 10 — what production would add

Show `modules/maintenance_investigator` and [ARCHITECTURE.md](ARCHITECTURE.md). Production would deploy the Toolkit module to a development project, replace placeholder group ids, vendor the package into Cognite Functions, and keep a person in the approval path. It would not let the model stop the pump.

## If CDF is available

Set `APP_MODE=cdf` in `.env` for the development project only. The sidebar reports authentication. Ingest with `make cdf-ingest` after `cdf build` and a reviewed `cdf deploy`. Do not deploy to production.

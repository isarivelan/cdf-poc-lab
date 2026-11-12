"""Print local verification results. CDF checks run only when credentials are configured."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.clients.cdf_client import probe_connection
from maintenance_investigator.pipeline import run_local_pipeline
from maintenance_investigator.settings import load_settings


def main() -> int:
    settings = load_settings(repo_root=ROOT)
    result = run_local_pipeline(ROOT)
    critical = [item for item in result.incidents if item.severity == "critical"]
    print(f"Mode: {settings.app_mode.value}")
    print(f"Incidents: {len(result.incidents)}. Critical: {len(critical)}.")
    print(f"Health score: {result.health_score}")
    print(f"Data-quality score: {result.quality['data_quality_score']}")
    print(f"Missing percent: {result.quality['missing_percent']}")
    if not critical or critical[-1].equipment != "PUMP-P101":
        print("Verification failed: the critical incident is not linked to PUMP-P101.")
        return 1
    if settings.cdf_required():
        status, detail = probe_connection(settings)
        print(detail)
        return 0 if status == "ok" else 1
    print("CDF credentials were not required. Local verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

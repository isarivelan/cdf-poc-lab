"""Delete demo time series. Requires CDF_CONFIRM_CLEANUP=yes and a non-production project."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.clients.cdf_client import CdfRepository
from maintenance_investigator.constants import ALL_SENSORS
from maintenance_investigator.exceptions import ConfigurationError, MaintenanceInvestigatorError
from maintenance_investigator.settings import assert_development_target, load_settings


def main() -> int:
    settings = load_settings(repo_root=ROOT)
    if not settings.confirm_cleanup:
        print("Cleanup was not run.")
        print(
            "Set CDF_CONFIRM_CLEANUP=yes to delete the demo time series "
            "from the configured project."
        )
        return 2
    try:
        assert_development_target(settings)
        if not settings.cdf_required():
            raise ConfigurationError(
                "Cleanup needs APP_MODE=cdf or APP_MODE=hybrid.",
                likely_cause="The current mode does not select a CDF project.",
                action="Set APP_MODE and the development credentials, then retry.",
            )
        CdfRepository(settings).delete_time_series(list(ALL_SENSORS))
    except (ConfigurationError, MaintenanceInvestigatorError) as exc:
        print(exc)
        return 1
    print("Deleted the demo time series external ids.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

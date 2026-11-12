"""Explain Toolkit deployment. This script does not deploy."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.exceptions import ConfigurationError
from maintenance_investigator.settings import assert_development_target, load_settings


def main() -> int:
    settings = load_settings(repo_root=ROOT)
    print("Toolkit module: modules/maintenance_investigator")
    print("Build command: cdf build")
    print("Dry run: cdf deploy --dry-run")
    if not settings.cdf_required():
        print("APP_MODE is not cdf or hybrid. No deployment was started.")
        return 0
    try:
        assert_development_target(settings)
    except ConfigurationError as exc:
        print(exc)
        return 2
    print("Credentials are configured for a development target.")
    print("This POC script does not deploy. Review the build, then run cdf deploy yourself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
from pathlib import Path

from segym.validation import validate_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SettlementEthicsGym scenarios.")
    parser.add_argument("paths", nargs="+", help="Scenario YAML files")
    args = parser.parse_args()

    reports = [validate_path(path) for path in args.paths]
    errors = sum(len(report.errors) for report in reports)
    warnings = sum(len(report.warnings) for report in reports)
    for report in reports:
        for err in report.errors:
            print(f"ERROR {Path(report.path)}: {err}")
        for warn in report.warnings:
            print(f"WARNING {Path(report.path)}: {warn}")
    print(f"Validated {len(reports)} scenarios.")
    print(f"{errors} errors.")
    print(f"{warnings} warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())


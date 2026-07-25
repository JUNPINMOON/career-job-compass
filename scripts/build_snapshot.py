"""Build the GitHub Pages fallback from the live job_search public projection."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-search-root", required=True, type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "app-data.json",
    )
    args = parser.parse_args()
    root = args.job_search_root.resolve(strict=True)
    sys.path.insert(0, str(root))
    from jobsearch_v4.public_snapshot import build_public_snapshot

    payload = build_public_snapshot(
        actions_path=root / "work" / "recommendation-v4" / "g006-cross-sector-actions.json",
        posting_facts_path=root / "work" / "recommendation-v4" / "g003-posting-facts.json",
        dashboard_path=root / "dashboard" / "data.js",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {args.output}: {len(payload['jobs'])} V4 candidates, "
        f"{len(payload['programs'])} programs, {len(payload['funding'])} funding opportunities"
    )


if __name__ == "__main__":
    main()

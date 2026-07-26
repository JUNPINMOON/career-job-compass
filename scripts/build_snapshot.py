"""Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IHE_DELFT = "IHE Delft Institute for Water Education"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _key(record: dict[str, Any]) -> tuple[str, str]:
    return (
        str(record.get("university", "")).strip().casefold(),
        str(record.get("program", "")).strip().casefold(),
    )


def _apply_latest_programs(payload: dict[str, Any], shortlist_path: Path) -> str:
    """Refresh compact programme records from the lightweight current shortlist."""
    shortlist = _read_json(shortlist_path)
    latest = shortlist.get("programs")
    current = payload.get("programs")
    if not isinstance(latest, list) or not isinstance(current, list):
        raise ValueError("graduate shortlist or public snapshot has no programme list")
    by_key = {_key(record): record for record in latest if isinstance(record, dict)}
    refreshed: list[dict[str, Any]] = []
    for item in current:
        if not isinstance(item, dict):
            continue
        source = by_key.get(_key(item))
        if source is None:
            refreshed.append(item)
            continue
        item.update(
            {
                "rank": source.get("rank"),
                "decision": source.get("decision", item.get("decision", "")),
                "score": source.get("score", item.get("score")),
                "deadline": source.get("application_deadline", item.get("deadline", "")),
                "intake": source.get("intake", item.get("intake", "")),
                "tuition": source.get("tuition_annual", item.get("tuition", "")),
                "funding": source.get("funding_model", item.get("funding", "")),
                "verification": source.get("official_verification_status", item.get("verification", "")),
                "verifiedAt": source.get("last_verified", item.get("verifiedAt", "")),
                "officialUrl": source.get("url", item.get("officialUrl", "")),
                "sources": source.get("source_urls", item.get("sources", [])),
            }
        )
        if source.get("university") == IHE_DELFT:
            item.update(
                {
                    "englishStatus": "공식 기준 확인",
                    "english": "정규·공동 MSc: IELTS Academic 전체 6.0 및 Writing 6.0, 또는 TOEFL iBT 총점 80 및 Writing 17.",
                    "englishCriteria": source.get("english_requirements", []),
                    "englishGapPlan": source.get("english_gap_plan", []),
                }
            )
        refreshed.append(item)
    payload["programs"] = sorted(
        refreshed,
        key=lambda item: (item.get("rank") is None, item.get("rank") or 10_000, str(item.get("university", ""))),
    )
    return str(shortlist.get("generated_at", ""))


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
    from jobsearch_v4.public_snapshot import build_public_job_slice

    if not args.output.exists():
        raise FileNotFoundError(f"base public snapshot required: {args.output}")
    payload = _read_json(args.output)
    job_slice = build_public_job_slice(
        actions_path=root / "work" / "recommendation-v4" / "g006-cross-sector-actions.json",
        posting_facts_path=root / "work" / "recommendation-v4" / "g003-posting-facts.json",
    )
    graduate_generated_at = _apply_latest_programs(
        payload,
        root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json",
    )
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
    stats.update(job_slice["stats"])
    stats.update(
        {
            "programs": len(payload["programs"]),
            "funding": len(payload.get("funding", [])),
            "graduateGeneratedAt": graduate_generated_at,
        }
    )
    payload.update(
        {
            "schemaVersion": 3,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "dataAsOf": max(job_slice["jobDataAsOf"], graduate_generated_at[:10]),
            "stats": stats,
            "sectors": job_slice["sectors"],
            "jobs": job_slice["jobs"],
            "reviewQueue": job_slice["reviewQueue"],
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {args.output}: {len(payload['jobs'])} job candidates, "
        f"{len(payload['programs'])} programs, {len(payload['funding'])} funding opportunities"
    )


if __name__ == "__main__":
    main()

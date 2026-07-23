"""Build a compact public PWA snapshot from the local job_search artifacts.

The script intentionally excludes job descriptions, user-profile matching text,
credentials, CRM fields, tokens, and external-write paths. A published snapshot
is a reading aid, not a live job board or application system.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_JOBS = 72
MAX_STUDY_ROUTES = 12


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def compact_job(row: dict[str, Any]) -> dict[str, Any]:
    score = number(row.get("final_rank_score") or row.get("ranking_score"))
    eligibility = text(row.get("eligibility_status")) or "verify_first"
    status = "확인 필요" if eligibility != "eligible" else "조건 확인됨"
    return {
        "id": text(row.get("v3_canonical_id") or row.get("v3_id") or row.get("id")),
        "title": text(row.get("title")) or "제목 미확인 공고",
        "company": text(row.get("company")) or "기관 미확인",
        "location": text(row.get("location")) or "근무지 원문 확인",
        "sector": text(row.get("sector_label")) or "분야 미분류",
        "source": text(row.get("source")) or "출처 미확인",
        "url": text(row.get("url")),
        "deadline": text(row.get("deadline")),
        "score": round(score, 1),
        "status": status,
        "action": "원문 확인",
        "eligibilitySummary": text(row.get("eligibility_reason")) or "지원 조건을 원문에서 확인하세요.",
        "evidenceCompleteness": round(number(row.get("evidence_completeness")), 1),
    }


def compact_program(row: dict[str, Any]) -> dict[str, Any]:
    urls = row.get("source_urls") if isinstance(row.get("source_urls"), list) else []
    official_url = text(row.get("url")) or next((text(url) for url in urls if text(url)), "")
    stable_id = hashlib.sha256((official_url or text(row.get("program"))).encode("utf-8")).hexdigest()[:16]
    return {
        "id": "study-" + stable_id,
        "university": text(row.get("university")) or "대학 원문 확인",
        "program": text(row.get("program")) or "과정 원문 확인",
        "country": text(row.get("country")) or "국가 원문 확인",
        "degree": text(row.get("degree")),
        "deadline": text(row.get("application_deadline")) or "마감 원문 확인",
        "funding": text(row.get("funding_model")) or "재정 조건 원문 확인",
        "verification": text(row.get("official_verification_status")) or "원문 재확인 필요",
        "url": official_url,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-search-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "app-data.json")
    args = parser.parse_args()

    root = args.job_search_root.resolve(strict=True)
    scored_path = root / "scored_jobs.json"
    source_health_path = root / "source_health.json"
    programs_path = root / "config" / "grad_school_programs.researched.json"
    raw_path = root / "jobs.json"

    scored = load_json(scored_path)
    source_health = load_json(source_health_path)
    programs = load_json(programs_path)
    raw_jobs = load_json(raw_path)
    if not all(isinstance(value, list) for value in (scored, source_health, programs, raw_jobs)):
        raise ValueError("expected list-shaped job_search artifacts")

    ordered = sorted(
        (row for row in scored if isinstance(row, dict) and text(row.get("url"))),
        key=lambda row: number(row.get("final_rank_score") or row.get("ranking_score")),
        reverse=True,
    )
    seen_urls: set[str] = set()
    jobs: list[dict[str, Any]] = []
    for row in ordered:
        url = text(row.get("url"))
        if url in seen_urls:
            continue
        seen_urls.add(url)
        jobs.append(compact_job(row))
        if len(jobs) == MAX_JOBS:
            break

    study = [compact_program(row) for row in sorted(
        (row for row in programs if isinstance(row, dict) and (text(row.get("url")) or row.get("source_urls"))),
        key=lambda row: (number(row.get("practicality_score")), number(row.get("fit_score"))),
        reverse=True,
    )[:MAX_STUDY_ROUTES]]
    health_states = Counter(text(row.get("status")) or "unknown" for row in source_health if isinstance(row, dict))
    visible_sectors = Counter(job["sector"] for job in jobs)
    newest_source_check = max(
        (text(row.get("last_checked")) for row in source_health if isinstance(row, dict) and text(row.get("last_checked"))),
        default="",
    )

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "snapshotBoundary": "정적 공개 스냅샷입니다. 원문 확인 전에는 마감·자격·지원 가능 여부를 확정하지 않습니다.",
        "stats": {
            "rawJobs": len(raw_jobs),
            "scoredJobs": len(scored),
            "publishedJobs": len(jobs),
            "sourceRecords": len(source_health),
            "sourceStatusCounts": dict(sorted(health_states.items())),
            "newestSourceCheck": newest_source_check,
        },
        "sectors": [
            {"name": name, "publishedJobs": count}
            for name, count in visible_sectors.most_common()
        ],
        "jobs": jobs,
        "study": study,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} with {len(jobs)} jobs and {len(study)} study routes")


if __name__ == "__main__":
    main()

"""Build the public Career Compass snapshot from the current job_search outputs.

The old public build read an obsolete compatibility feed and then imposed
presentation-only caps.  This builder intentionally uses the V4 cross-sector
action artifact and the same graduate/funding projection consumed by the local
dashboard.  It still strips private profile, application, CRM and credential
fields before writing a GitHub Pages-safe static file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QUEUE_ORDER = ("verify", "hold", "apply", "stretch", "submitted", "reject")
PUBLIC_JOB_QUEUES = {"verify", "hold", "apply", "stretch"}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def compact_list(value: Any, limit: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text(item) for item in value if text(item)][:limit]


def stable_id(prefix: str, *values: Any) -> str:
    source = "|".join(text(value) for value in values)
    return f"{prefix}-{hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]}"


def queue_label(queue: str) -> str:
    return {
        "verify": "원문 확인",
        "hold": "추가 검토",
        "apply": "지원 검토",
        "stretch": "도전 후보",
    }.get(queue, "검토 후보")


def compact_job(row: dict[str, Any], queue: str) -> dict[str, Any]:
    sector = row.get("primarySector") if isinstance(row.get("primarySector"), dict) else {}
    confidence = row.get("evidenceConfidence") if isinstance(row.get("evidenceConfidence"), dict) else {}
    burden = row.get("evidenceResolutionBurden") if isinstance(row.get("evidenceResolutionBurden"), dict) else {}
    return {
        "id": text(row.get("jobId")) or stable_id("job", row.get("url"), row.get("title")),
        "title": text(row.get("title")) or "제목 원문 확인",
        "company": text(row.get("employer")) or "기관 원문 확인",
        "location": ", ".join(compact_list(row.get("locations"), 3)) or "근무지 원문 확인",
        "sector": text(sector.get("label")) or "분야 검토 중",
        "source": text(row.get("source")) or "출처 원문 확인",
        "url": text(row.get("url")),
        "queue": queue,
        "queueLabel": queue_label(queue),
        "deadline": text((row.get("prioritySignals") or {}).get("deadlineUrgency", {}).get("value")),
        "nextAction": text(row.get("nextActionKo")) or "공식 원문에서 마감·자격·근무 조건을 확인하세요.",
        "requirements": compact_list(row.get("requirementsKo")),
        "checks": compact_list(row.get("checksKo")),
        "risks": compact_list(row.get("risksKo")),
        "evidenceGapCount": confidence.get("feasibilityUnknownCount") if isinstance(confidence.get("feasibilityUnknownCount"), int) else None,
        "evidenceBurden": text(burden.get("level")),
    }


def compact_program(row: dict[str, Any]) -> dict[str, Any]:
    urls = row.get("sourceUrls") if isinstance(row.get("sourceUrls"), list) else []
    official_url = text(row.get("officialUrl")) or next((text(url) for url in urls if text(url)), "")
    track = row.get("programTrack") if isinstance(row.get("programTrack"), dict) else {}
    english = row.get("englishProfile") if isinstance(row.get("englishProfile"), dict) else {}
    return {
        "id": stable_id("program", official_url, row.get("university"), row.get("program")),
        "rank": row.get("rank") if isinstance(row.get("rank"), int) else None,
        "university": text(row.get("university")) or "대학 원문 확인",
        "program": text(row.get("program")) or "과정 원문 확인",
        "country": text(row.get("country")) or "국가 원문 확인",
        "degree": text(track.get("label")) or text(row.get("degree")),
        "decision": text(row.get("decision")),
        "score": row.get("score") if isinstance(row.get("score"), (int, float)) else None,
        "deadline": text(row.get("applicationDeadline")) or text(row.get("application_deadline")),
        "intake": text(row.get("intake")),
        "tuition": text(row.get("tuitionAnnual")) or text(row.get("tuition_annual")),
        "funding": text(row.get("fundingModel")) or text(row.get("funding_model")),
        "verification": text(row.get("officialVerificationStatus")) or text(row.get("official_verification_status")),
        "verifiedAt": text(row.get("lastVerified")) or text(row.get("last_verified")),
        "english": text(english.get("summary")),
        "officialUrl": official_url,
        "sources": compact_list(urls, 4),
    }


def compact_funding(row: dict[str, Any]) -> dict[str, Any]:
    url = text(row.get("officialUrl")) or text(row.get("official_url"))
    return {
        "id": text(row.get("id")) or stable_id("funding", url, row.get("name")),
        "name": text(row.get("name")) or "장학금 원문 확인",
        "type": text(row.get("fundingType")) or text(row.get("funding_type")),
        "coverage": text(row.get("coverageLevel")) or text(row.get("coverage_level")),
        "decision": text(row.get("decision")),
        "score": row.get("score") if isinstance(row.get("score"), (int, float)) else None,
        "likelihood": text(row.get("selectionLikelihood")) or text(row.get("selection_likelihood")),
        "deadline": text(row.get("deadlineHint")) or text(row.get("deadline_hint")),
        "gates": compact_list(row.get("hardGates") or row.get("hard_gates")),
        "risks": compact_list(row.get("riskFlags") or row.get("risk_flags")),
        "verification": text(row.get("verificationStatus")) or text(row.get("verification_status")),
        "officialUrl": url,
        "countries": compact_list(row.get("countries"), 4),
    }


def load_dashboard_projection(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig").strip()
    try:
        return json.loads(raw[raw.index("{"):].rstrip(";").strip())
    except (ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot parse dashboard projection: {path}") from error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-search-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "app-data.json")
    args = parser.parse_args()

    root = args.job_search_root.resolve(strict=True)
    actions_path = root / "work" / "recommendation-v4" / "g006-cross-sector-actions.json"
    dashboard_path = root / "dashboard" / "data.js"
    actions = load_json(actions_path)
    dashboard = load_dashboard_projection(dashboard_path)
    if not isinstance(actions, dict) or not isinstance(dashboard, dict):
        raise ValueError("expected structured V4 action and dashboard artifacts")

    action_jobs: list[dict[str, Any]] = []
    for queue in QUEUE_ORDER:
        if queue not in PUBLIC_JOB_QUEUES:
            continue
        rows = (actions.get("queues") or {}).get(queue, [])
        if not isinstance(rows, list):
            continue
        action_jobs.extend(compact_job(row, queue) for row in rows if isinstance(row, dict))
    if not action_jobs:
        raise ValueError("V4 action artifact did not yield public action candidates")

    grad = dashboard.get("gradSchool") if isinstance(dashboard.get("gradSchool"), dict) else {}
    programs = [compact_program(row) for row in grad.get("programs", []) if isinstance(row, dict)]
    funding = [compact_funding(row) for row in grad.get("fundingOpportunities", []) if isinstance(row, dict)]
    if len(programs) < 1 or len(funding) < 1:
        raise ValueError("dashboard projection did not yield graduate and funding research")

    sector_counts: dict[str, int] = {}
    for job in action_jobs:
        sector_counts[job["sector"]] = sector_counts.get(job["sector"], 0) + 1
    queue_counts = {queue: sum(job["queue"] == queue for job in action_jobs) for queue in PUBLIC_JOB_QUEUES}

    action_updated_at = datetime.fromtimestamp(actions_path.stat().st_mtime, timezone.utc)
    graduate_generated_at = text(grad.get("generatedAt"))
    graduate_day = graduate_generated_at[:10]
    action_day = action_updated_at.date().isoformat()
    data_as_of = max(day for day in (graduate_day, action_day) if day)
    payload = {
        "schemaVersion": 3,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "dataAsOf": data_as_of,
        "snapshotBoundary": "공개 읽기용 스냅샷입니다. 공고·과정·장학금의 마감과 자격은 반드시 공식 원문에서 다시 확인하세요.",
        "stats": {
            "actionCandidates": len(action_jobs),
            "programs": len(programs),
            "funding": len(funding),
            "queueCounts": queue_counts,
            "v4RunId": text(actions.get("runId")),
            "v4ArtifactUpdatedAt": action_updated_at.isoformat(),
            "graduateGeneratedAt": graduate_generated_at,
        },
        "sectors": [{"name": name, "publishedJobs": count} for name, count in sorted(sector_counts.items(), key=lambda item: (-item[1], item[0]))],
        "jobs": action_jobs,
        "reviewQueue": action_jobs[:3],
        "programs": programs,
        "funding": funding,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}: {len(action_jobs)} V4 candidates, {len(programs)} programs, {len(funding)} funding opportunities")


if __name__ == "__main__":
    main()

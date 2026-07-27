"""Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


IHE_DELFT = "IHE Delft Institute for Water Education"
MINIMUM_EXPERIENCE_EXCLUSION_YEARS = 2


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError(f"expected JSON array: {path}")
    return [item for item in value if isinstance(item, dict)]


def _key(record: dict[str, Any]) -> tuple[str, str]:
    return (
        str(record.get("university", "")).strip().casefold(),
        str(record.get("program", "")).strip().casefold(),
    )


def _application_readiness(source: dict[str, Any]) -> tuple[str, str, str]:
    """Keep an actionable preparation lane distinct from a verified open call.

    The shortlist is a research inventory.  A recurrent schedule, an estimate,
    or an old verification must never be presented as an application that is
    open today.  ``Use now`` means the school is worth preparing for, not that
    the application portal is open.
    """
    if str(source.get("decision", "")).strip() == "Use now":
        return (
            "prepare",
            "지금 준비",
            "현재 열린 접수로 확인된 것은 아닙니다. 성적·서류·교수/과정 조사를 지금 시작할 후보입니다.",
        )
    return (
        "research",
        "추가 조사",
        "현재 접수 여부를 공식 원문에서 다시 확인한 뒤 준비 대상으로 올리세요.",
    )


def _public_url(value: Any) -> str:
    url = str(value or "").strip()
    return url if url.startswith(("https://", "http://")) else ""


def _recent_five_years(value: Any) -> bool:
    years = [int(year) for year in re.findall(r"\b20\d{2}\b", str(value or ""))]
    cutoff = datetime.now().year - 4
    return not years or max(years) >= cutoff


def _verified_date(source: Mapping[str, Any]) -> str:
    """Publish only explicit ISO dates, never internal review markers."""
    for key in ("faculty_last_verified", "last_verified"):
        value = str(source.get(key) or "").strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
    return ""


def experienced_only_title(job: Mapping[str, Any]) -> bool:
    """DATA-214: fail closed when the title itself explicitly says 경력직."""
    title = str(job.get("title", "")).replace(" ", "")
    return "경력직" in title and "신입" not in title and "경력무관" not in title


def support_only_title(job: Mapping[str, Any]) -> bool:
    """DATA-215: keep employer context from turning Finance Intern into a technical role."""
    title = str(job.get("title", "")).strip()
    support_role = re.search(
        r"\b(finance intern|finance and budget officer|recruit(?:ment|er)|"
        r"human resources?|payroll|reception(?:ist)?|account executive)\b",
        title,
        flags=re.IGNORECASE,
    )
    if not support_role:
        return False
    title_grounded_target = re.search(
        r"\b(water|hydro|flood|climate|adaptation|resilien(?:ce|t)|coastal|"
        r"environment|gis|geospatial|remote sensing|data|machine learning|ai|"
        r"artificial intelligence|project)\b",
        title,
        flags=re.IGNORECASE,
    )
    return title_grounded_target is None


def verified_research_project(project: Mapping[str, Any]) -> bool:
    """DATA-216: count only records evidenced as research contracts or funded projects."""
    evidence_text = " ".join(
        str(project.get(field, "")).strip().lower()
        for field in ("title", "funder", "period")
    )
    non_contract_markers = (
        "not a funded grant",
        "editorial",
        "guest editor",
        "special issue",
        "publication dates",
        "specific grant id not disclosed",
    )
    return not any(marker in evidence_text for marker in non_contract_markers)


def _public_research(source: dict[str, Any]) -> dict[str, Any]:
    """DATA-213: publish source-backed research facts, never personal fit notes."""
    faculty: list[dict[str, Any]] = []
    for person in source.get("faculty", []):
        if not isinstance(person, dict):
            continue
        papers = [
            {
                "year": str(paper.get("year", "")).strip(),
                "title": str(paper.get("title", "")).strip(),
                "venue": str(paper.get("venue", "")).strip(),
                "url": _public_url(paper.get("url")),
            }
            for paper in person.get("recent_papers", [])
            if isinstance(paper, dict) and paper.get("title") and _recent_five_years(paper.get("year"))
        ]
        projects = [
            {
                "title": str(project.get("title", "")).strip(),
                "funder": str(project.get("funder", "")).strip(),
                "period": str(project.get("period", "")).strip(),
                "amount": str(project.get("amount", "")).strip(),
                "url": _public_url(project.get("url")),
            }
            for project in person.get("recent_projects", [])
            if (
                isinstance(project, dict)
                and project.get("title")
                and _recent_five_years(project.get("period"))
                and verified_research_project(project)
            )
        ]
        faculty.append(
            {
                "name": str(person.get("name", "")).strip(),
                "title": str(person.get("title", "")).strip(),
                "labOrGroup": str(person.get("lab_or_group", "")).strip(),
                "profileUrls": [
                    url
                    for url in (_public_url(item) for item in person.get("profile_urls", []))
                    if url
                ],
                "recentPapers": papers,
                "recentProjects": projects,
            }
        )
    destinations = [
        {
            "period": str(item.get("year_range", "")).strip(),
            "destination": str(item.get("destination", "")).strip(),
            "role": str(item.get("role", "")).strip(),
            "url": _public_url(item.get("url")),
        }
        for item in source.get("graduate_destinations", [])
        if isinstance(item, dict) and item.get("destination")
    ]
    return {
        "keywords": [str(item).strip() for item in source.get("keywords", []) if str(item).strip()],
        "faculty": faculty,
        "recentProjects": [project for person in faculty for project in person["recentProjects"]],
        "graduateDestinations": destinations,
        "lastVerified": _verified_date(source),
        "evidenceStatus": "공식·연구실 원문 확인" if faculty else "공개 연구자료 추가 확인 필요",
    }


def _apply_latest_programs(payload: dict[str, Any], shortlist_path: Path, research_path: Path) -> str:
    """Refresh compact programme records from the lightweight current shortlist."""
    shortlist = _read_json(shortlist_path)
    latest = shortlist.get("programs")
    current = payload.get("programs")
    if not isinstance(latest, list) or not isinstance(current, list):
        raise ValueError("graduate shortlist or public snapshot has no programme list")
    by_key = {_key(record): record for record in latest if isinstance(record, dict)}
    research_by_key = {_key(record): record for record in _read_json_list(research_path)}
    refreshed: list[dict[str, Any]] = []
    for item in current:
        if not isinstance(item, dict):
            continue
        source = by_key.get(_key(item))
        research = research_by_key.get(_key(item))
        if source is None:
            readiness, label, reason = _application_readiness(item)
            item.update(
                {
                    "applicationStatus": readiness,
                    "applicationStatusLabel": label,
                    "applicationStatusReason": reason,
                }
            )
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
        readiness, label, reason = _application_readiness(source)
        item.update(
            {
                "applicationStatus": readiness,
                "applicationStatusLabel": label,
                "applicationStatusReason": reason,
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
        item["publicResearch"] = _public_research(research) if research else {
            "keywords": [],
            "faculty": [],
            "recentProjects": [],
            "graduateDestinations": [],
            "lastVerified": "",
            "evidenceStatus": "공개 연구자료 추가 확인 필요",
        }
        refreshed.append(item)
    payload["programs"] = sorted(
        refreshed,
        key=lambda item: (item.get("rank") is None, item.get("rank") or 10_000, str(item.get("university", ""))),
    )
    return str(shortlist.get("generated_at", ""))


def _apply_public_eligibility(
    job_slice: dict[str, Any],
    overrides: dict[str, Any],
    canonical_job_key: Callable[[Mapping[str, Any]], tuple[str, str]],
    explicit_experience_exclusion: Callable[[Mapping[str, Any]], bool],
) -> dict[str, Any]:
    """DATA-210: recheck eligibility and canonical duplicates after expansion."""
    excluded = 0
    duplicate_count = 0
    jobs: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_title_companies: set[str] = set()
    for source in job_slice.get("jobs", []):
        if not isinstance(source, dict):
            continue
        job = dict(source)
        override = overrides.get(str(job.get("id", "")))
        if isinstance(override, dict):
            job.update(override)
        minimum_years = job.get("minimumExperienceYears", 0)
        try:
            minimum_years = float(minimum_years)
        except (TypeError, ValueError):
            minimum_years = 0
        if (
            minimum_years >= MINIMUM_EXPERIENCE_EXCLUSION_YEARS
            or job.get("publicEligibility") == "excluded"
            or experienced_only_title(job)
            or support_only_title(job)
            or explicit_experience_exclusion(job)
        ):
            excluded += 1
            continue
        url_key, title_company_key = canonical_job_key(job)
        if (url_key and url_key in seen_urls) or (title_company_key and title_company_key in seen_title_companies):
            duplicate_count += 1
            continue
        if url_key:
            seen_urls.add(url_key)
        if title_company_key:
            seen_title_companies.add(title_company_key)
        jobs.append(job)

    eligible_ids = {str(job.get("id", "")) for job in jobs}
    review_queue = [
        item
        for item in job_slice.get("reviewQueue", [])
        if isinstance(item, dict) and str(item.get("id", "")) in eligible_ids
    ]
    sectors = [dict(item) for item in job_slice.get("sectors", []) if isinstance(item, dict)]
    for sector in sectors:
        sector["publishedJobs"] = sum(
            1 for job in jobs if sector.get("name") in job.get("sectors", [])
        )

    stats = dict(job_slice.get("stats", {}))
    stats["marketCounts"] = {
        market: sum(1 for job in jobs if job.get("market") == market)
        for market in ("domestic", "overseas", "unknown")
    }
    stats["queueCounts"] = {
        queue: sum(1 for job in jobs if job.get("queue") == queue)
        for queue in ("verify", "hold", "apply", "stretch")
    }
    stats["actionCandidates"] = sum(1 for job in jobs if job.get("discoveryTier") == "action")
    stats["actionableCandidates"] = len(review_queue)
    stats["explorationCandidates"] = sum(1 for job in jobs if job.get("discoveryTier") == "explore")
    stats["excludedExperienceCandidates"] = excluded
    stats["excludedDuplicateCandidates"] = duplicate_count

    return {
        **job_slice,
        "jobs": jobs,
        "reviewQueue": review_queue,
        "sectors": sectors,
        "stats": stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-search-root", required=True, type=Path)
    parser.add_argument(
        "--catalog-source",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "catalog-source.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "app-data.json",
    )
    parser.add_argument(
        "--programs-only",
        action="store_true",
        help="Enrich the existing public snapshot without rebuilding the job slice.",
    )
    args = parser.parse_args()
    root = args.job_search_root.resolve(strict=True)
    sys.path.insert(0, str(root))
    from jobsearch_v4.public_snapshot import (
        build_public_job_slice,
        canonical_job_key,
        explicit_experience_exclusion,
    )

    if args.catalog_source.resolve() == args.output.resolve():
        raise ValueError("catalog source and generated output must be different files")
    if not args.catalog_source.exists():
        raise FileNotFoundError(f"catalog source required: {args.catalog_source}")
    payload = _read_json(args.catalog_source)
    if args.programs_only:
        graduate_generated_at = _apply_latest_programs(
            payload,
            root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json",
            root / "config" / "grad_school_programs.researched.json",
        )
        stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
        stats.update({"programs": len(payload["programs"]), "graduateGeneratedAt": graduate_generated_at})
        payload["stats"] = stats
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.output}: enriched {len(payload['programs'])} programs")
        return
    raw_job_slice = build_public_job_slice(
        actions_path=root / "work" / "recommendation-v4" / "g006-cross-sector-actions.json",
        posting_facts_path=root / "work" / "recommendation-v4" / "g003-posting-facts.json",
    )
    overrides = payload.get("jobEligibilityOverrides", {})
    job_slice = _apply_public_eligibility(
        raw_job_slice,
        overrides if isinstance(overrides, dict) else {},
        canonical_job_key,
        explicit_experience_exclusion,
    )
    graduate_generated_at = _apply_latest_programs(
        payload,
        root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json",
        root / "config" / "grad_school_programs.researched.json",
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

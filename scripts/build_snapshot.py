"""Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


IHE_DELFT = "IHE Delft Institute for Water Education"
MINIMUM_EXPERIENCE_EXCLUSION_YEARS = 2
LIFESTYLE_METHOD_VERSION = "lifestyle-evidence-v1"
LIFESTYLE_STATUSES = frozenset({"confirmed", "claimed", "unknown", "negative"})
REMOTE_LOCATION_PATTERN = re.compile(
    r"(?i)(^|[,(/])\s*remote(?:\s*[,)/]|$)|hybrid|\uc7ac\ud0dd\uadfc\ubb34|\uc7ac\ud0dd\ub300\uba74\ud63c\ud569\uadfc\ubb34"
)
SEOUL_LOCATION_PATTERN = re.compile(r"(?i)\uc11c\uc6b8|seoul")
BUSAN_LOCATION_PATTERN = re.compile(r"(?i)\ubd80\uc0b0|busan")
WLB_NEGATIVE_PATTERN = re.compile(
    r"(?i)\uc57c\uac04|\uad50\ub300|\uc8fc\ub9d0\s*(?:\uadfc\ubb34|\ub2f9\uc9c1)|\ub2f9\uc9c1|\uc628\ucf5c|on[- ]?call|night shift|"
    r"rotating shift|weekend shift|frequent travel|\uc78a\uc740 \ucd9c\uc7a5|\ud604\uc7a5 \uc0c1\uc8fc|\ud604\uc7a5 \ud30c\uacac"
)
WLB_POSITIVE_PATTERN = re.compile(
    r"(?i)\uc6cc\ub77c\ubc38|\uc720\uc5f0\uadfc\ubb34|\ud0c4\ub825\uadfc\ubb34|\uc120\ud0dd\uadfc\ubb34|\uc2dc\ucc28\ucd9c\ud1f4\uadfc|"
    r"\uc8fc\s*4\.5\uc77c|\uc815\uc2dc\ud1f4\uadfc|flexible hours|flexitime|compressed workweek|no overtime"
)


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


def _typed_sources(
    items: Any,
    *,
    fallback_url: Any = "",
    default_type: str,
    default_label: str,
) -> list[dict[str, str]]:
    """DATA-217: retain source provenance instead of flattening links."""
    sources: list[dict[str, str]] = []
    raw_items = items if isinstance(items, list) else []
    if not raw_items and fallback_url:
        fallback_items = fallback_url if isinstance(fallback_url, list) else [fallback_url]
        raw_items = [{"url": url} for url in fallback_items]
    for item in raw_items:
        source = item if isinstance(item, dict) else {"url": item}
        url = _public_url(source.get("url"))
        if not url:
            continue
        entry = {
            "sourceType": str(source.get("source_type") or default_type).strip(),
            "label": str(source.get("label") or default_label).strip(),
            "url": url,
        }
        if entry not in sources:
            sources.append(entry)
    return sources


def _public_research(source: dict[str, Any]) -> dict[str, Any]:
    """DATA-213: publish source-backed research facts, never personal fit notes."""
    faculty: list[dict[str, Any]] = []
    for person in source.get("faculty", []):
        if not isinstance(person, dict) or not str(person.get("name", "")).strip():
            continue
        profile_sources = _typed_sources(
            person.get("profile_sources"),
            fallback_url=person.get("profile_urls"),
            default_type="untyped_faculty_source",
            default_label="교수·연구자 원문",
        )
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
                "profileSources": profile_sources,
                "recentPapers": papers,
                "recentProjects": projects,
            }
        )
    destinations: list[dict[str, Any]] = []
    for item in source.get("graduate_destinations", []):
        if not isinstance(item, dict) or not item.get("destination"):
            continue
        outcome_sources = _typed_sources(
            item.get("sources"),
            fallback_url=item.get("url"),
            default_type=str(item.get("source_type") or "untyped_public_source"),
            default_label=str(item.get("source_label") or "진로 근거 원문"),
        )
        destinations.append({
            "period": str(item.get("year_range", "")).strip(),
            "destination": str(item.get("destination", "")).strip(),
            "role": str(item.get("role", "")).strip(),
            "url": _public_url(item.get("url")),
            "sources": outcome_sources,
        })
    # DATA-218: reviews remain supporting evidence, never employment proof.
    testimonials: list[dict[str, Any]] = []
    for item in source.get("graduate_testimonials", []):
        if not isinstance(item, dict) or not item.get("summary"):
            continue
        testimonial_sources = _typed_sources(
            item.get("sources"),
            fallback_url=item.get("url"),
            default_type=str(item.get("source_type") or "public_alumni_review"),
            default_label=str(item.get("source_label") or "동문 후기"),
        )
        testimonials.append({
            "person": str(item.get("person", "")).strip(),
            "summary": str(item.get("summary", "")).strip(),
            "context": str(item.get("context", "")).strip(),
            "sources": testimonial_sources,
        })
    return {
        "keywords": [str(item).strip() for item in source.get("keywords", []) if str(item).strip()],
        "faculty": faculty,
        "recentProjects": [project for person in faculty for project in person["recentProjects"]],
        "graduateDestinations": destinations,
        "graduateOutcomeSources": [
            evidence
            for destination in destinations
            for evidence in destination["sources"]
        ],
        "graduateTestimonials": testimonials,
        "lastVerified": _verified_date(source),
        "evidenceStatus": "공식·연구실 원문 확인" if faculty else "공개 연구자료 추가 확인 필요",
    }


def _public_program_from_research(source: dict[str, Any]) -> dict[str, Any]:
    """DATA-222: turn a canonical research discovery into an app programme."""
    university = str(source.get("university", "")).strip()
    program = str(source.get("program", "")).strip()
    digest = hashlib.sha256(f"{university}\0{program}".encode("utf-8")).hexdigest()[:12]
    readiness, label, reason = _application_readiness(source)
    country = str(source.get("country", "")).strip()
    return {
        "id": f"program-{digest}",
        "rank": source.get("rank"),
        "university": university,
        "program": program,
        "country": country,
        "market": "domestic" if country == "South Korea" else "overseas",
        "degree": str(source.get("degree", "")).strip(),
        "decision": str(source.get("decision", "Research")).strip(),
        "score": source.get("score"),
        "deadline": str(source.get("application_deadline", "")).strip(),
        "intake": str(source.get("intake", "")).strip(),
        "tuition": str(source.get("tuition_annual", "")).strip(),
        "funding": str(source.get("funding_model", "")).strip(),
        "verification": str(source.get("official_verification_status", "")).strip(),
        "verifiedAt": _verified_date(source),
        "officialUrl": _public_url(source.get("url")),
        "sources": [
            url
            for url in (_public_url(item) for item in source.get("source_urls", []))
            if url
        ],
        "applicationStatus": readiness,
        "applicationStatusLabel": label,
        "applicationStatusReason": reason,
        "publicResearch": _public_research(source),
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
            # DATA-229: the ranked shortlist is intentionally small. A catalog
            # programme must still receive its matching canonical research
            # evidence when it is not one of those ranked shortlist records.
            research_source = research if research is not None else item
            readiness, label, reason = _application_readiness(research_source)
            item.update(
                {
                    "applicationStatus": readiness,
                    "applicationStatusLabel": label,
                    "applicationStatusReason": reason,
                    "publicResearch": _public_research(research) if research else {
                        "keywords": [],
                        "faculty": [],
                        "recentProjects": [],
                        "graduateDestinations": [],
                        "graduateOutcomeSources": [],
                        "graduateTestimonials": [],
                        "lastVerified": "",
                        "evidenceStatus": "공개 연구자료 추가 확인 필요",
                    },
                }
            )
            if research is not None:
                item.update(
                    {
                        "verification": research.get(
                            "official_verification_status", item.get("verification", "")
                        ),
                        "verifiedAt": _verified_date(research) or item.get("verifiedAt", ""),
                        "officialUrl": _public_url(research.get("url")) or item.get("officialUrl", ""),
                        "sources": [
                            url
                            for url in (
                                _public_url(value)
                                for value in research.get("source_urls", item.get("sources", []))
                            )
                            if url
                        ],
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
            "graduateOutcomeSources": [],
            "graduateTestimonials": [],
            "lastVerified": "",
            "evidenceStatus": "공개 연구자료 추가 확인 필요",
        }
        refreshed.append(item)
    existing_keys = {_key(item) for item in refreshed}
    new_research_keys = sorted(set(research_by_key) - existing_keys)
    for key in new_research_keys:
        refreshed.append(_public_program_from_research(research_by_key[key]))
    payload["programs"] = sorted(
        refreshed,
        key=lambda item: (item.get("rank") is None, item.get("rank") or 10_000, str(item.get("university", ""))),
    )
    return str(shortlist.get("generated_at", ""))


def _graduate_evidence_coverage(programs: Any) -> dict[str, int]:
    """Expose programme-level evidence coverage against the complete public list."""
    records = [item for item in programs if isinstance(item, dict)] if isinstance(programs, list) else []
    research = [
        item.get("publicResearch") if isinstance(item.get("publicResearch"), dict) else {}
        for item in records
    ]
    has_faculty = [bool(item.get("faculty")) for item in research]
    has_papers = [
        any(person.get("recentPapers") for person in item.get("faculty", []) if isinstance(person, dict))
        for item in research
    ]
    has_projects = [bool(item.get("recentProjects")) for item in research]
    has_outcomes = [bool(item.get("graduateDestinations")) for item in research]
    has_testimonials = [bool(item.get("graduateTestimonials")) for item in research]
    has_any = [
        any(values)
        for values in zip(has_faculty, has_papers, has_projects, has_outcomes, has_testimonials)
    ]
    return {
        "totalPrograms": len(records),
        "programsWithAnyEvidence": sum(has_any),
        "programsWithFaculty": sum(has_faculty),
        "programsWithRecentPapers": sum(has_papers),
        "programsWithFundedProjects": sum(has_projects),
        "programsWithGraduateDestinations": sum(has_outcomes),
        "programsWithTestimonials": sum(has_testimonials),
        "unresearchedPrograms": len(records) - sum(has_any),
    }


def _graduate_data_lineage(payload: Mapping[str, Any]) -> dict[str, Any]:
    """DATA-227: bind every graduate consumer to the canonical public payload."""
    programs = payload.get("programs")
    funding = payload.get("funding")
    if not isinstance(programs, list) or not isinstance(funding, list):
        raise ValueError("canonical graduate payload requires programme and funding lists")
    canonical = json.dumps(
        {"programs": programs, "funding": funding},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "producer": "career-job-compass/scripts/build_snapshot.py",
        "artifact": "data/app-data.json",
        "payloadSha256": hashlib.sha256(canonical).hexdigest(),
        "programCount": len(programs),
        "fundingCount": len(funding),
    }


def _fact(label: str, value: Any, evidence: str = "공개 원문") -> dict[str, str] | None:
    text = str(value or "").strip()
    if not text:
        return None
    return {"label": label, "value": text, "evidence": evidence}


def _job_decision_support(job: Mapping[str, Any], verified_at: str) -> dict[str, Any]:
    """DATA-233: confirmed facts and unresolved questions."""
    known = [
        _fact("기관", job.get("company")),
        _fact("근무지", job.get("location")),
        _fact("마감", job.get("deadline")),
        _fact("분류", job.get("queueLabel") or job.get("discoveryLabel"), "분류 엔진"),
    ]
    missing: list[dict[str, str]] = []
    deadline = job.get("deadline")
    if not deadline:
        missing.append({"label": "마감", "why": "정보 없음"})
    missing.append({"label": "급여·복지", "why": "공개 정보 없음"})
    missing.append({"label": "고용형태·근무방식", "why": "공개 정보 없음"})
    overseas = job.get("market") == "international"
    if overseas:
        missing.append({"label": "\ube44\uc790\u00b7\ucde8\uc5c5 \ud5c8\uac00", "why": "\uace0\uc6a9\uc8fc \uc9c0\uc6d0 \uc5ec\ubd80 \ubbf8\ud655\uc778"})
    for check in job.get("checks") or []:
        missing.append({"label": "\ucd94\uac00 \uac80\uc99d", "why": str(check)})
    dimensions = []
    dimensions.append({"label": "\uc9c0\uc6d0 \uac00\ub2a5\uc131", "status": "\ud655\uc778 \ud544\uc694", "value": "\uacbd\ub825\u00b7\ud559\ub825 \uc870\uac74 \ub300\uc870"})
    dimensions.append({"label": "\uc5c5\ubb34 \uc801\ud569", "status": "\ubd80\ubd84 \ud655\uc778", "value": str(job.get("sectorEvidence") or "\ubd84\uc57c \uadfc\uac70")})
    dimensions.append({"label": "\uc870\uac74\u00b7\uc548\uc815\uc131", "status": "\uc815\ubcf4 \ubd80\uc871", "value": "\uae09\uc5ec\u00b7\uace0\uc6a9\ud615\ud0dc \ud655\uc778"})
    dimensions.append({"label": "\uc131\uc7a5\u00b7\uc9c4\ub85c", "status": "\ucd94\ub860 \uae08\uc9c0", "value": "\ud300\u00b7\ud504\ub85c\uc81d\ud2b8\u00b7\uc2b9\uc9c4 \uacbd\ub85c \ud655\uc778"})
    dimensions.append({"label": "\ub9c8\uac10\u00b7\ud589\ub3d9", "status": "\ud655\uc778" if deadline else "\ud655\uc778 \ud544\uc694", "value": str(deadline or job.get("nextAction") or "\uc6d0\ubb38 \ud655\uc778")})
    return {
        "recordType": "job",
        "evidenceLevel": "공개 원문과 분류 근거",
        "lastVerified": verified_at,
        "knownInformation": [item for item in known if item],
        "missingInformation": missing,
        "nextActions": [str(job.get("nextAction") or "공식 공고 확인")],
        "dimensions": dimensions,
    }


def _program_decision_support(program: Mapping[str, Any]) -> dict[str, Any]:
    research = program.get("publicResearch") if isinstance(program.get("publicResearch"), dict) else {}
    faculty = research.get("faculty") if isinstance(research.get("faculty"), list) else []
    projects = research.get("recentProjects") if isinstance(research.get("recentProjects"), list) else []
    outcomes = research.get("graduateDestinations") if isinstance(research.get("graduateDestinations"), list) else []
    papers = sum(len(item.get("recentPapers") or []) for item in faculty if isinstance(item, dict))
    known = [
        _fact("\uc900\ube44 \uc0c1\ud0dc", program.get("applicationStatusLabel"), "\ubd84\ub958 \uc5d4\uc9c4"),
        _fact("\ud559\uc704\u00b7\uad6d\uac00", " \u00b7 ".join(filter(None, [program.get("degree"), program.get("country")]))),
        _fact("\ub9c8\uac10", program.get("deadline")),
        _fact("\uc7ac\uc815 \uc9c0\uc6d0", program.get("funding")),
        _fact("\uc601\uc5b4 \uc694\uac74", program.get("english")),
        _fact("\uad50\uc218\u00b7\ub17c\ubb38", f"\uad50\uc218 {len(faculty)}\uba85 \u00b7 \ucd5c\uadfc \ub17c\ubb38 {papers}\uac74", research.get("evidenceStatus") or "\uacf5\uac1c \uc5f0\uad6c\uc790\ub8cc"),
        _fact("\uc5f0\uad6c\uc6a9\uc5ed", f"{len(projects)}\uac74", research.get("evidenceStatus") or "\uacf5\uac1c \uc5f0\uad6c\uc790\ub8cc"),
        _fact("\uc878\uc5c5 \ud6c4 \uacbd\ub85c", f"{len(outcomes)}\uac74", research.get("evidenceStatus") or "\uacf5\uac1c \uc5f0\uad6c\uc790\ub8cc"),
    ]
    missing = []
    if not program.get("deadline"):
        missing.append({"label": "\ub9c8\uac10\uc77c", "why": "\ucd5c\uc2e0 \uc785\ud559 \uacf5\uace0 \uc7ac\ud655\uc778 \ud544\uc694"})
    if not faculty:
        missing.append({"label": "\uad50\uc218\u00b7\ub17c\ubb38", "why": "\uacf5\uac1c \uc5f0\uad6c \uadfc\uac70 \ubbf8\uc5f0\uacb0"})
    if not projects:
        missing.append({"label": "\ucd5c\uadfc 5\ub144 \uc5f0\uad6c\uc6a9\uc5ed", "why": "\uacf5\uc2dc\u00b7\uc0b0\ud559\ud611\ub825 \uadfc\uac70 \ubbf8\uc5f0\uacb0"})
    if not outcomes:
        missing.append({"label": "\uc878\uc5c5\uc0dd \uc9c4\ub85c", "why": "\uacf5\uc2dd \ucde8\uc5c5 \ud604\ud669\u00b7\ub3d9\ubb38 \uadfc\uac70 \ubbf8\uc5f0\uacb0"})
    missing.append({"label": "\ud3c9\uade0 \uc878\uc5c5 \uae30\uac04\u00b7\uc911\ub3c4\ud0c8\ub77d", "why": "\uacfc\uc815 \uc644\uc8fc \uc704\ud5d8 \uadfc\uac70 \ubbf8\ud655\uc778"})
    missing.append({"label": "\uc5f0\uad6c\uc2e4 \ubb38\ud654\u00b7\uc9c0\ub3c4 \ubc29\uc2dd", "why": "\uc7ac\ud559\uc0dd\u00b7\uc878\uc5c5\uc0dd \ud6c4\uae30 \ucd94\uac00 \ud655\uc778 \ud544\uc694"})
    dimensions = [
        {"label": "\uc9c0\uc6d0 \uac00\ub2a5\uc131", "status": "\ubd80\ubd84 \ud655\uc778", "value": str(program.get("applicationStatusLabel") or "\uc6d0\ubb38 \ud655\uc778")},
        {"label": "\uc5f0\uad6c \uc801\ud569", "status": "\uadfc\uac70 \uc788\uc74c" if faculty else "\uc815\ubcf4 \ubd80\uc871", "value": f"\uad50\uc218 {len(faculty)}\uba85\u00b7\ub17c\ubb38 {papers}\uac74"},
        {"label": "\ube44\uc6a9\u00b7\uc7ac\uc815", "status": "\ud655\uc778" if program.get("funding") else "\uc815\ubcf4 \ubd80\uc871", "value": str(program.get("funding") or program.get("tuition") or "\ucd94\uac00 \ud655\uc778")},
        {"label": "\uc878\uc5c5 \ud6c4 \uc9c4\ub85c", "status": "\uadfc\uac70 \uc788\uc74c" if outcomes else "\uc815\ubcf4 \ubd80\uc871", "value": f"\uc9c4\ub85c \uadfc\uac70 {len(outcomes)}\uac74"},
        {"label": "\ub9c8\uac10\u00b7\ud589\ub3d9", "status": "\ud655\uc778" if program.get("deadline") else "\uc7ac\ud655\uc778", "value": str(program.get("deadline") or program.get("applicationStatusReason") or "\uacf5\uc2dd \uacf5\uace0 \ud655\uc778")},
    ]
    return {
        "recordType": "program",
        "evidenceLevel": str(research.get("evidenceStatus") or program.get("verification") or "\uacf5\uac1c \uadfc\uac70"),
        "lastVerified": str(research.get("lastVerified") or program.get("verifiedAt") or ""),
        "knownInformation": [item for item in known if item],
        "missingInformation": missing,
        "nextActions": [str(program.get("applicationStatusReason") or "\uacf5\uc2dd \uc785\ud559 \uacf5\uace0\uc640 \uad50\uc218 \uc5f0\uad6c\uc2e4\uc744 \ud655\uc778\ud558\uc138\uc694.")],
        "dimensions": dimensions,
    }


def _apply_decision_support(payload: dict[str, Any]) -> None:
    verified_at = str(payload.get("dataAsOf") or payload.get("generatedAt") or "")
    for job in payload.get("jobs") or []:
        job["decisionSupport"] = _job_decision_support(job, verified_at)
    for program in payload.get("programs") or []:
        program["decisionSupport"] = _program_decision_support(program)
    payload["releaseVersion"] = "decision-support-v2"


def _lifestyle_axis(
    status: str,
    summary: str,
    evidence: list[str],
    missing: list[str],
) -> dict[str, Any]:
    if status not in LIFESTYLE_STATUSES:
        raise ValueError(f"unsupported lifestyle status: {status}")
    return {
        "status": status,
        "summary": summary,
        "evidence": evidence,
        "missing": missing,
    }


def _wlb_axis(job: Mapping[str, Any]) -> dict[str, Any]:
    condition_fields = {
        key: job.get(key)
        for key in ("requirements", "checks", "risks", "nextAction", "decisionSupport")
        if job.get(key)
    }
    condition_text = json.dumps(condition_fields, ensure_ascii=False, sort_keys=True)
    negative_match = WLB_NEGATIVE_PATTERN.search(condition_text)
    if negative_match:
        return _lifestyle_axis(
            "negative",
            "\uc57c\uac04\u00b7\uad50\ub300\u00b7\uc8fc\ub9d0\u00b7\ub2f9\uc9c1\u00b7\ucd9c\uc7a5 \uc911 \ubd80\uc815 \uadfc\ubb34 \uc2e0\ud638\uac00 \uba85\uc2dc\ub410\uc2b5\ub2c8\ub2e4.",
            [f"\uba85\uc2dc \uc2e0\ud638: {negative_match.group(0)}"],
            ["\uc2e4\uc81c \uadfc\ubb34\ud45c\uc640 \ud300 \ub2e8\uc704 \ucd08\uacfc\uadfc\ubb34 \ud604\ud669"],
        )
    positive_match = WLB_POSITIVE_PATTERN.search(condition_text)
    if positive_match:
        return _lifestyle_axis(
            "claimed",
            "\uacf5\uace0\uc5d0 \uc720\uc5f0\uadfc\ubb34\u00b7\uc815\uc2dc\ud1f4\uadfc \ub4f1 \uc0dd\ud65c \uc870\uac74 \uc2e0\ud638\uac00 \uba85\uc2dc\ub410\uc2b5\ub2c8\ub2e4.",
            [f"\uba85\uc2dc \uc2e0\ud638: {positive_match.group(0)}"],
            ["\ud300\ubcc4 \uc2e4\uc81c \uc801\uc6a9 \uc5ec\ubd80", "\ud3c9\uade0 \ucd08\uacfc\uadfc\ubb34\u00b7\ud734\uac00 \uc0ac\uc6a9 \ud604\ud669"],
        )
    return _lifestyle_axis(
        "unknown",
        "\uacf5\uac1c \uacf5\uace0\ub9cc\uc73c\ub85c\ub294 \uc6cc\ub77c\ubc38\uc744 \ud310\ub2e8\ud560 \uadfc\uac70\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.",
        [],
        ["\uc8fc\ub2f9 \uadfc\ubb34\uc2dc\uac04", "\ucd08\uacfc\uadfc\ubb34\u00b7\uc57c\uac04\u00b7\uc8fc\ub9d0 \uadfc\ubb34", "\uc720\uc5f0\uadfc\ubb34\u00b7\ud734\uac00 \uc2e4\uc81c \uc6b4\uc601"],
    )


def _combined_lifestyle_status(commute_status: str, wlb_status: str) -> str:
    if "negative" in {commute_status, wlb_status}:
        return "negative"
    if commute_status == "confirmed" and wlb_status == "confirmed":
        return "confirmed"
    if commute_status in {"confirmed", "claimed"} and wlb_status in {"confirmed", "claimed"}:
        return "claimed"
    return "unknown"


def _lifestyle_counts(rows: list[tuple[str, str]]) -> dict[str, int]:
    return {status: sum(1 for _, value in rows if value == status) for status in sorted(LIFESTYLE_STATUSES)}


def _apply_lifestyle_discovery(payload: dict[str, Any]) -> None:
    """Build a separate evidence layer without changing jobs or recommendation scores."""
    jobs = payload.get("jobs") or []
    jobs_before = json.dumps(jobs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    items: list[dict[str, Any]] = []
    jayang_rows: list[tuple[str, str]] = []
    busan_rows: list[tuple[str, str]] = []

    for job in jobs:
        job_id = str(job.get("id") or "").strip()
        location = str(job.get("location") or "").strip()
        market = str(job.get("market") or "unknown")
        is_domestic = market == "domestic"
        is_seoul = bool(SEOUL_LOCATION_PATTERN.search(location))
        is_remote_location = bool(REMOTE_LOCATION_PATTERN.search(location))
        is_busan = bool(BUSAN_LOCATION_PATTERN.search(location))
        is_jayang_candidate = is_domestic and (is_seoul or is_remote_location)
        is_busan_candidate = is_domestic and is_busan
        if not job_id or not (is_jayang_candidate or is_busan_candidate):
            continue

        if is_jayang_candidate:
            commute_axis = _lifestyle_axis(
                "claimed",
                "\uacf5\uac1c \uadfc\ubb34\uc9c0\ub85c \uc790\uc591\ub3d9 \ud1b5\uadfc \ud6c4\ubcf4\uc5d0 \ud3ec\ud568\ud588\uc9c0\ub9cc \uc2e4\uc81c \uc18c\uc694 \uc2dc\uac04\uc740 \ubbf8\ud655\uc778\uc785\ub2c8\ub2e4.",
                [f"\uacf5\uac1c \uadfc\ubb34\uc9c0: {location or 'location not stated'}"],
                ["\uc815\ud655\ud55c \uc0ac\ubb34\uc2e4 \uc8fc\uc18c", "\uc8fc\uac04 \ucd9c\uadfc \ud69f\uc218", "\ucd9c\ud1f4\uadfc \ub300\uc911\uad50\ud1b5 \uc18c\uc694 \uc2dc\uac04"],
            )
        else:
            commute_axis = _lifestyle_axis(
                "unknown",
                "\uc790\uc591\ub3d9 \ud1b5\uadfc \ud6c4\ubcf4\ub85c \ubd84\ub958\ud560 \uadfc\uac70\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.",
                [],
                ["\uc815\ud655\ud55c \uadfc\ubb34\uc9c0", "\ucd9c\ud1f4\uadfc \uc18c\uc694 \uc2dc\uac04"],
            )

        wlb_axis = _wlb_axis(job)
        if is_busan_candidate:
            busan_axis = _lifestyle_axis(
                "confirmed",
                "\uacf5\uace0\uc758 \uadfc\ubb34\uc9c0 \ud544\ub4dc\uc5d0 \ubd80\uc0b0\uc774 \uba85\uc2dc\ub410\uc2b5\ub2c8\ub2e4.",
                [f"\uacf5\uac1c \uadfc\ubb34\uc9c0: {location}"],
                ["\uc815\ud655\ud55c \uc0ac\ubb34\uc2e4 \uc8fc\uc18c", "\ud558\uc774\ube0c\ub9ac\ub4dc\u00b7\uc678\uadfc \ube44\uc911"],
            )
        else:
            busan_axis = _lifestyle_axis(
                "unknown",
                "\uacf5\uac1c \uadfc\ubb34\uc9c0\uc5d0 \ubd80\uc0b0\uc774 \uba85\uc2dc\ub418\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4.",
                [],
                ["\ubd80\uc0b0 \uc2e4\uc81c \uadfc\ubb34\uc9c0 \uc5ec\ubd80"],
            )

        jayang_status = _combined_lifestyle_status(commute_axis["status"], wlb_axis["status"])
        busan_status = busan_axis["status"]
        if is_jayang_candidate:
            jayang_rows.append((job_id, jayang_status))
        if is_busan_candidate:
            busan_rows.append((job_id, busan_status))
        items.append(
            {
                "jobId": job_id,
                "title": str(job.get("title") or ""),
                "company": str(job.get("company") or job.get("employer") or ""),
                "location": location,
                "market": market,
                "source": str(job.get("source") or ""),
                "url": str(job.get("url") or ""),
                "lifestyleEvidence": {
                    "axes": {
                        "jayangCommute": commute_axis,
                        "wlb": wlb_axis,
                        "busanWorkplace": busan_axis,
                    },
                    "lanes": {"jayang_wlb": jayang_status, "busan": busan_status},
                },
            }
        )

    discovery = {
        "schemaVersion": LIFESTYLE_METHOD_VERSION,
        "methodVersion": LIFESTYLE_METHOD_VERSION,
        "asOf": str(payload.get("dataAsOf") or payload.get("generatedAt") or ""),
        "scoreImpact": "none",
        "sourceJobCount": len(jobs),
        "universeLabel": "\ud604\uc7ac \uacf5\uac1c \uc218\uc9d1\ubcf8\uc758 \uc9c0\uc6d0 \uac00\ub2a5 \uacf5\uace0",
        "limitations": [
            "\uc804\uccb4 \ucc44\uc6a9\uc2dc\uc7a5\uc774 \uc544\ub2c8\ub77c \ud604\uc7ac \uacf5\uac1c \uc218\uc9d1\ubcf8\uc785\ub2c8\ub2e4.",
            "\ud1b5\uadfc \uc18c\uc694 \uc2dc\uac04\uc740 \uc815\ud655\ud55c \uc0ac\ubb34\uc2e4\u00b7\ucd9c\uadfc\uc77c\u00b7\ub300\uc911\uad50\ud1b5 \uac80\uc99d \uc804\uae4c\uc9c0 \ud655\uc815\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.",
            "\uc6d0\uaca9\u00b7\ud558\uc774\ube0c\ub9ac\ub4dc\ub098 \ubcf5\uc9c0 \ubb38\uad6c\ub9cc\uc73c\ub85c \uc6cc\ub77c\ubc38\uc744 \ud655\uc815\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.",
            "\uc0dd\ud65c \uc870\uac74\uc740 \ucd94\ucc9c \uc810\uc218\uc5d0 \ubc18\uc601\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.",
        ],
        "items": items,
        "lanes": {
            "jayang_wlb": {
                "label": "\uc790\uc591\ub3d9 \ud1b5\uadfc\u00b7\uc6cc\ub77c\ubc38",
                "reviewIds": [job_id for job_id, _ in jayang_rows],
                "counts": _lifestyle_counts(jayang_rows),
            },
            "busan": {
                "label": "\ubd80\uc0b0 \u00b7 \uc804 \uc9c1\uc885",
                "reviewIds": [job_id for job_id, _ in busan_rows],
                "counts": _lifestyle_counts(busan_rows),
            },
        },
    }
    digest_payload = json.dumps(discovery, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    discovery["digest"] = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
    payload["lifestyleDiscovery"] = discovery
    jobs_after = json.dumps(jobs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if jobs_before != jobs_after:
        raise AssertionError("lifestyle discovery must not mutate jobs or recommendation scores")


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
        payload["graduateEvidenceCoverage"] = _graduate_evidence_coverage(payload["programs"])
        _apply_decision_support(payload)
        _apply_lifestyle_discovery(payload)
        payload["graduateDataLineage"] = _graduate_data_lineage(payload)
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
            "graduateEvidenceCoverage": _graduate_evidence_coverage(payload["programs"]),
        }
    )
    _apply_decision_support(payload)
    _apply_lifestyle_discovery(payload)
    payload["graduateDataLineage"] = _graduate_data_lineage(payload)
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

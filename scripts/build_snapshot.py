"""Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


IHE_DELFT = "IHE Delft Institute for Water Education"
MINIMUM_EXPERIENCE_EXCLUSION_YEARS = 2
LIFESTYLE_METHOD_VERSION = "lifestyle-evidence-v2"
LIFESTYLE_SOURCE_ARTIFACT = "job_search/work/recommendation-v4/g003-posting-facts.json"
LIFESTYLE_STATUSES = frozenset({"confirmed", "claimed", "unknown", "negative"})
LIFESTYLE_CANDIDATE_CLASSES = frozenset({"statusRecheck", "verifiedOpen"})
SEOUL_LOCATION_PATTERN = re.compile(r"(?i)\uc11c\uc6b8(?:\ud2b9\ubcc4\uc2dc)?|seoul|\uad11\uc9c4(?:\uad6c)?|\uc790\uc591(?:\ub3d9)?")
BUSAN_LOCATION_PATTERN = re.compile(r"(?i)\ubd80\uc0b0|busan")
SUBSTANTIVE_LIFESTYLE_SECTOR_IDS = frozenset({
    "ai_adjacent_transition",
    "civil_infrastructure",
    "climate_environment",
    "data_ml_engineering",
    "generative_ai",
    "geo_ai",
    "gis_geospatial",
    "infrastructure_ai",
    "international_development",
    "ai_governance",
    "ai_product_solutions",
    "kr_civil_service",
    "water_climate_ai",
    "water_hydrology",
})
JUNIOR_SIGNAL_PATTERN = re.compile(
    r"(?i)\uc2e0\uc785|\uacbd\ub825\s*\ubb34\uad00|\uc778\ud134|\uc8fc\ub2c8\uc5b4|\ucd08\uae09|entry(?:[- ]level)?|graduate|junior|new\s*grad|no\s*experience"
)
SENIOR_BLOCK_PATTERN = re.compile(
    r"(?i)\uacbd\ub825\s*(?:[5-9]|\d{2,})\s*\ub144|(?:[5-9]|\d{2,})\s*\ub144\s*(?:\uc774\uc0c1|\u2191)|"
    r"\uc784\uc6d0|\uc6d0\uc7a5|\uc13c\ud130\uc7a5|\ud300\uc7a5|\ubd80\uc7a5|\ucc28\uc7a5|\uacfc\uc7a5|\ucc45\uc784|\uc218\uc11d|\uc120\uc784|senior|lead|principal|director|postdoc|\ubc15\uc0ac\ud6c4"
)
ROLE_DENY_PATTERN = re.compile(
    r"(?i)\uac04\ud638|\uac04\ud638\uc9c1|\uc870\ub9ac|\uae09\uc2dd|\uacbd\ube44|\ubcf4\uc548|\uccad\uc18c|\ubbf8\ud654|\uc6b4\uc804|\ubc30\uc1a1|\ubb3c\ub958|\uc6b0\ud3b8|\uc6b0\ud3b8\ubb3c|"
    r"\ub9e4\uc7a5\s*\ud310\ub9e4|\uc678\uadfc\s*\uc601\uc5c5|\uc601\uc5c5\s*\ud64d\ubcf4|\uc601\uc5c5\ud300|\ub9c8\ucf00\ud305|\uc778\uc0ac|\ucd1d\ubb34|\ud68c\uacc4|\uc7ac\ubb34|\ucf5c\uc13c\ud130|\uc0c1\ub2f4|"
    r"\uac80\ud45c|\uce74\ud398|\uc57d\uc0ac|\uc758\uc0ac|\uc758\ub8cc|\ubcd1\uc6d0|\uc694\uc591|\uc0ac\ud68c\ubcf5\uc9c0|\ubc29\ubb38|compositing|3dmax|\ub77c\uc774\ub178|\uc77c\ub7ec\uc2a4\ud2b8|\ud30c\uc774\ub110\ucef7|\ub514\uc790\uc778"
)
CONTEXT_DENY_PATTERN = re.compile(
    r"(?i)\uc804\uae30|\uae30\uacc4|\uc2dc\uc124|\uc0dd\uc0b0|\uc81c\uc870|\uc870\uacbd|\uac74\ucd95|\uc2dc\uacf5|\uacf5\ubb34|\ud488\uc9c8|\uce21\ub7c9|\ud604\uc7a5\uc5c5\ubb34|\uadf8\ub77c\uc6b0\ud305|\uc720\uc9c0\uad00\ub9ac|"
    r"\uc548\uc804\uad00\ub9ac\uc790|\uad50\uc0ac|\uac15\uc0ac|\uad50\uc721|\ub77c\ubca8\ub9c1"
)
DOMAIN_OVERRIDE_PATTERN = re.compile(
    r"(?i)\uc218\uc790\uc6d0|\uc218\ubb38|\uc218\ub9ac|\ud558\ucc9c|\ud64d\uc218|\uce58\uc218|\ubb3c\uad00\ub9ac|\uc218\uc9c8|\uc218\ucc98\ub9ac|water|hydro|GIS|"
    r"\uacf5\uac04\uc815\ubcf4|\ud1a0\ubaa9|civil|\ud658\uacbd|environment|\uae30\ud6c4|climate|\ub514\uc9c0\ud138\ud2b8\uc708|R&D|\uc5f0\uad6c|\uc815\ucc45|ODA|\uad6d\uc81c\uac1c\ubc1c|\uac1c\ubc1c\ud611\ub825"
)
DOMAIN_SIGNAL_PATTERN = re.compile(
    r"(?i)\uc218\uc790\uc6d0|\uc218\ubb38|\uc218\ub9ac|\ud558\ucc9c|\ud64d\uc218|\uce58\uc218|\ubb3c\uad00\ub9ac|\uc218\uc9c8|\uc218\ucc98\ub9ac|water|hydro|"
    r"\ud658\uacbd|environment|climate|\uae30\ud6c4|GIS|\uacf5\uac04\uc815\ubcf4|\uc9c0\ub9ac\uc815\ubcf4|(?<![A-Za-z])AI(?![A-Za-z])|\uc778\uacf5\uc9c0\ub2a5|\ub370\uc774\ud130|data|\ub514\uc9c0\ud138\ud2b8\uc708|"
    r"ODA|\uad6d\uc81c\uac1c\ubc1c|\uac1c\ubc1c\ud611\ub825|\uc815\ucc45|\uc5f0\uad6c|research|R&D|engineer|engineering|\uc5d4\uc9c0\ub2c8\uc5b4|\ud1a0\ubaa9|civil|"
    r"\uc778\ud504\ub77c|infrastructure|ESG|sustainability|\uc7ac\ub09c|\ubc29\uc7ac|\ucee8\uc124\ud305|\uc0ac\uc5c5\uad00\ub9ac|(?<![A-Za-z])PM(?![A-Za-z])|\uacf5\uae30\uc5c5|\uacf5\uacf5"
)
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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_active_repository(
    repo_root: Path,
    output_path: Path,
    *,
    personalized_runtime: bool = False,
    job_search_root: Path | None = None,
) -> None:
    """GOV-230: fail closed outside the active repo or canonical output."""
    expected_root = Path(__file__).resolve().parents[1]
    resolved_root = repo_root.resolve()
    if resolved_root != expected_root:
        raise RuntimeError(f"snapshot producer is not running from its active repository: {resolved_root}")

    git_root = Path(
        subprocess.run(
            ["git", "-C", str(resolved_root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    ).resolve()
    if git_root != expected_root:
        raise RuntimeError(f"git root does not match the active snapshot repository: {git_root}")

    origin = subprocess.run(
        ["git", "-C", str(resolved_root), "remote", "get-url", "origin"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    normalized_origin = origin.replace("https://", "").replace("ssh://git@", "").replace("git@github.com:", "github.com/")
    normalized_origin = normalized_origin.rstrip("/")
    expected_origin = "github.com/JUNPINMOON/career-job-compass.git"
    if normalized_origin.casefold() != expected_origin.casefold():
        raise RuntimeError(f"unexpected snapshot repository origin: {origin}")

    canonical_output = (resolved_root / "data" / "app-data.json").resolve()
    if personalized_runtime:
        if job_search_root is None:
            raise ValueError("personalized runtime builds require the job-search root")
        private_output = (
            job_search_root.resolve() / "state_v4" / "career-compass-personalized-snapshot.json"
        ).resolve()
        if output_path.resolve() != private_output:
            raise ValueError(f"personalized runtime builds may write only to: {private_output}")
    elif output_path.resolve() != canonical_output:
        raise ValueError(f"public snapshot builds may write only to: {canonical_output}")


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


def _fact_value(posting: Mapping[str, Any], group: str, field: str) -> Any:
    container = posting.get(group)
    if not isinstance(container, Mapping):
        return None
    fact = container.get(field)
    if not isinstance(fact, Mapping):
        return None
    return fact.get("value")


def _text_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _posting_relevant_sector_ids(posting: Mapping[str, Any]) -> set[str]:
    result: set[str] = set()
    for value in posting.get("relevantSectors") or []:
        if isinstance(value, Mapping):
            for key in ("sectorId", "id", "name"):
                text = str(value.get(key) or "").strip()
                if text:
                    result.add(text)
                    break
        else:
            text = str(value).strip()
            if text:
                result.add(text)
    return result


def _unique_pattern_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    return list(dict.fromkeys(match.group(0).strip() for match in pattern.finditer(text) if match.group(0).strip()))


def _sector_evidence(rows: list[dict[str, str]]) -> list[str]:
    return [
        " · ".join(filter(None, (row.get("sectorId", ""), row.get("sectorLabel", ""), row.get("matchState", ""))))
        for row in rows
    ]


def _lifestyle_role_gate(
    posting: Mapping[str, Any],
    title: str,
    company: str,
) -> tuple[bool, str, list[str], list[str]]:
    """Return a defensible role gate without letting polluted location text create a match."""
    sector_rows = _substantive_sector_rows(posting)
    sector_evidence = _sector_evidence(sector_rows)
    sector_text = " ".join(sector_evidence)
    role_text = " ".join(filter(None, (title, company, sector_text)))
    domain_signals = _unique_pattern_matches(DOMAIN_SIGNAL_PATTERN, " ".join(filter(None, (title, company))))
    if not sector_evidence and not domain_signals:
        return False, "excludedNoRoleSignal", sector_evidence, domain_signals
    if ROLE_DENY_PATTERN.search(" ".join(filter(None, (title, company)))):
        return False, "excludedRoleNoise", sector_evidence, domain_signals
    if CONTEXT_DENY_PATTERN.search(role_text) and not DOMAIN_OVERRIDE_PATTERN.search(role_text):
        return False, "excludedRoleNoise", sector_evidence, domain_signals
    return True, "strictLocation+relevantDomain+juniorAttainable", sector_evidence, domain_signals


def _wlb_axis(posting: Mapping[str, Any]) -> dict[str, Any]:
    # Use only explicit title/work-mode text. Portal/location blobs caused false hits.
    condition_text = " ".join(
        _text_values(_fact_value(posting, "facts", "title"))
        + _text_values(_fact_value(posting, "requirements", "workMode"))
    )
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


def _axis_counts(items: list[dict[str, Any]], review_ids: list[str]) -> dict[str, dict[str, int]]:
    selected = set(review_ids)
    result: dict[str, dict[str, int]] = {}
    for axis_name in ("jayangCommute", "wlb", "busanWorkplace"):
        rows = [
            (str(item["jobId"]), str(item["lifestyleEvidence"]["axes"][axis_name]["status"]))
            for item in items
            if str(item["jobId"]) in selected
        ]
        result[axis_name] = _lifestyle_counts(rows)
    return result


def _candidate_class_counts(items: list[dict[str, Any]], review_ids: list[str]) -> dict[str, int]:
    selected = set(review_ids)
    return {
        "statusRecheck": sum(
            1 for item in items if str(item["jobId"]) in selected and item.get("candidateClass") == "statusRecheck"
        ),
        "verifiedOpen": sum(
            1 for item in items if str(item["jobId"]) in selected and item.get("candidateClass") == "verifiedOpen"
        ),
    }


def _source_status(posting: Mapping[str, Any]) -> dict[str, str]:
    eligibility = posting.get("recommendationEligibility")
    eligibility = eligibility if isinstance(eligibility, Mapping) else {}
    partition = str(eligibility.get("currentStatusPartition") or "status_unknown")
    deadline_values = _text_values(_fact_value(posting, "facts", "deadline"))
    labels = {
        "known_open": "공개 상태 확인",
        "known_closed": "마감 확인",
        "status_unknown": "현재 공개 여부 재확인 필요",
        "archived_reference": "보관 자료",
    }
    return {
        "state": partition,
        "deadline": deadline_values[0] if deadline_values else "",
        "statusLabel": labels.get(partition, "현재 공개 여부 재확인 필요"),
    }


def _strict_location(location: str) -> dict[str, Any] | None:
    """Accept an explicit city/district field and reject portal-metadata lookalikes."""
    text = re.sub(r"\s+", " ", str(location or "")).strip()
    if not text:
        return None
    korean_specs = (
        ("seoul", "\uc11c\uc6b8", r"^\s*\uc11c\uc6b8(?:\ud2b9\ubcc4\uc2dc)?(?:\s+|[,/\u00b7-]+)(?P<district>[\uac00-\ud7a3]{1,8}\uad6c)?(?=$|\s|[,/\u00b7()\-])"),
        ("busan", "\ubd80\uc0b0", r"^\s*\ubd80\uc0b0(?:\uad11\uc5ed\uc2dc)?(?:\s+|[,/\u00b7-]+)(?P<district>[\uac00-\ud7a3]{1,8}(?:\uad6c|\uad70))?(?=$|\s|[,/\u00b7()\-])"),
    )
    exact_korean = {
        "\uc11c\uc6b8": ("seoul", "\uc11c\uc6b8"),
        "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc": ("seoul", "\uc11c\uc6b8"),
        "\ubd80\uc0b0": ("busan", "\ubd80\uc0b0"),
        "\ubd80\uc0b0\uad11\uc5ed\uc2dc": ("busan", "\ubd80\uc0b0"),
    }
    if text in exact_korean:
        city_code, city_label = exact_korean[text]
        return {
            "matched": True,
            "cityCode": city_code,
            "cityLabel": city_label,
            "district": "",
            "normalized": city_label,
            "sourceText": text,
        }
    for city_code, city_label, pattern in korean_specs:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            district = str(match.group("district") or "")
            return {
                "matched": True,
                "cityCode": city_code,
                "cityLabel": city_label,
                "district": district,
                "normalized": " ".join(filter(None, (city_label, district))),
                "sourceText": text,
            }
    english_specs = (
        ("seoul", "\uc11c\uc6b8", r"^Seoul(?:,?\s+(?:South Korea|Republic of Korea|Korea|KR))(?:,?\s+HQ)?$|^Seoul$"),
        ("busan", "\ubd80\uc0b0", r"^Busan(?:,?\s+(?:South Korea|Republic of Korea|Korea|KR))?$"),
    )
    for city_code, city_label, pattern in english_specs:
        if re.fullmatch(pattern, text, flags=re.IGNORECASE):
            return {
                "matched": True,
                "cityCode": city_code,
                "cityLabel": city_label,
                "district": "",
                "normalized": city_label,
                "sourceText": text,
            }
    return None


def _substantive_sector_rows(posting: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in posting.get("relevantSectors") or []:
        if not isinstance(raw, Mapping):
            continue
        sector_id = str(raw.get("sectorId") or "").strip()
        if sector_id not in SUBSTANTIVE_LIFESTYLE_SECTOR_IDS:
            continue
        rows.append(
            {
                "sectorId": sector_id,
                "sectorLabel": str(raw.get("sectorLabel") or sector_id).strip(),
                "matchState": str(raw.get("matchState") or "needs_evidence").strip(),
            }
        )
    return rows


def _minimum_experience_years(posting: Mapping[str, Any]) -> float | None:
    value = _fact_value(posting, "facts", "experience")
    if not isinstance(value, Mapping):
        return None
    minimum = value.get("minimum_years")
    if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
        return None
    return float(minimum)


def _entry_signals(text: str) -> list[str]:
    return list(dict.fromkeys(match.group(0).strip() for match in JUNIOR_SIGNAL_PATTERN.finditer(text)))


def _lifestyle_lane_funnel_counts() -> dict[str, int]:
    return {
        "rawLocation": 0,
        "strictLocation": 0,
        "relevantDomain": 0,
        "roleFit": 0,
        "juniorAttainable": 0,
        "wlbNotNegative": 0,
        "reviewCandidate": 0,
        "statusRecheck": 0,
        "verifiedOpen": 0,
    }


def _lifestyle_blank_candidate_filter() -> dict[str, bool]:
    return {
        "rawLocation": False,
        "strictLocation": False,
        "relevantDomain": False,
        "roleFit": False,
        "juniorAttainable": False,
        "wlbNotNegative": False,
        "reviewCandidate": False,
        "statusRecheck": False,
        "verifiedOpen": False,
    }


def _empty_filter_counts(source_count: int) -> dict[str, int]:
    return {
        "sourcePostingCount": source_count,
        "nonClosed": 0,
        "rawLocation": 0,
        "strictLocation": 0,
        "relevantDomain": 0,
        "roleFit": 0,
        "juniorAttainable": 0,
        "wlbNotNegative": 0,
        "deduplicated": 0,
        "statusRecheck": 0,
        "verifiedOpen": 0,
        "publishedCandidate": 0,
    }


def _decision_readiness(items: list[dict[str, Any]], review_ids: list[str], required_axes: tuple[str, ...]) -> str:
    selected_ids = set(review_ids)
    selected = [item for item in items if str(item.get("jobId")) in selected_ids]
    if not selected:
        return "insufficient"
    for item in selected:
        axes = item["lifestyleEvidence"]["axes"]
        if item["sourceStatus"]["state"] != "known_open":
            return "partial"
        if any(axes[axis]["status"] not in {"confirmed", "claimed"} for axis in required_axes):
            return "partial"
    return "ready"


def _apply_lifestyle_discovery(payload: dict[str, Any], posting_facts_path: Path) -> None:
    """DATA-241/DATA-242/DATA-243: search the full ledger and separate source hits from review candidates."""
    jobs = payload.get("jobs") or []
    jobs_before = json.dumps(jobs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    source = _read_json(posting_facts_path)
    postings = source.get("postings")
    if not isinstance(postings, list):
        raise ValueError(f"posting-facts artifact has no postings array: {posting_facts_path}")
    declared_count = source.get("canonicalPostingCount")
    if not isinstance(declared_count, int) or declared_count != len(postings):
        raise ValueError("posting-facts canonicalPostingCount does not match its postings array")
    artifact_digest = str(source.get("artifactDigest") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", artifact_digest):
        raise ValueError("posting-facts artifactDigest must be a lowercase SHA-256 digest")
    relevant_count = source.get("relevantUniqueJobCount")
    if (
        isinstance(relevant_count, bool)
        or not isinstance(relevant_count, int)
        or relevant_count < 0
        or relevant_count > declared_count
    ):
        raise ValueError("posting-facts relevantUniqueJobCount is invalid")

    items: list[dict[str, Any]] = []
    jayang_rows: list[tuple[str, str]] = []
    busan_rows: list[tuple[str, str]] = []
    seen_job_ids: set[str] = set()
    seen_urls: set[str] = set()
    filter_counts = {
        "sourcePostings": declared_count,
        "openOrUnknown": 0,
        "targetLocation": 0,
        "strictLocation": 0,
        "relevantDomain": 0,
        "roleFit": 0,
        "juniorAttainable": 0,
        "wlbNotNegative": 0,
        "publishedCandidates": 0,
        "excludedClosed": 0,
        "excludedArchived": 0,
        "excludedMalformed": 0,
        "excludedDuplicate": 0,
        "excludedNoTargetLocation": 0,
        "excludedNoStrictLocation": 0,
        "excludedRoleNoise": 0,
        "excludedSenior": 0,
        "excludedNoRoleSignal": 0,
        "excludedNotJunior": 0,
        "excludedWlbNegative": 0,
    }
    detailed_filter_counts = _empty_filter_counts(declared_count)
    lane_filter_counts = {
        "jayang_wlb": _lifestyle_lane_funnel_counts(),
        "busan": _lifestyle_lane_funnel_counts(),
    }

    for posting in postings:
        if not isinstance(posting, Mapping):
            filter_counts["excludedMalformed"] += 1
            continue
        source_status = _source_status(posting)
        if source_status["state"] == "known_closed":
            filter_counts["excludedClosed"] += 1
            continue
        if source_status["state"] == "archived_reference":
            filter_counts["excludedArchived"] += 1
            continue
        if source_status["state"] not in {"known_open", "status_unknown"}:
            filter_counts["excludedArchived"] += 1
            continue
        filter_counts["openOrUnknown"] += 1
        detailed_filter_counts["nonClosed"] += 1
        job_id = str(posting.get("jobId") or "").strip()
        title = " / ".join(_text_values(_fact_value(posting, "facts", "title")))
        company = " / ".join(_text_values(_fact_value(posting, "facts", "employer")))
        location = " / ".join(_text_values(_fact_value(posting, "facts", "location")))
        url = str(posting.get("url") or "").strip()
        if not job_id or not title or not re.match(r"^https?://", url):
            filter_counts["excludedMalformed"] += 1
            continue

        strict = _strict_location(location)
        strict_jayang = strict is not None and strict.get("cityCode") == "seoul"
        strict_busan = strict is not None and strict.get("cityCode") == "busan"
        raw_jayang = bool(SEOUL_LOCATION_PATTERN.search(location)) or strict_jayang
        raw_busan = bool(BUSAN_LOCATION_PATTERN.search(location)) or strict_busan
        candidate_filter = {
            "jayang_wlb": _lifestyle_blank_candidate_filter(),
            "busan": _lifestyle_blank_candidate_filter(),
        }
        for lane_key, raw_match, strict_match in (
            ("jayang_wlb", raw_jayang, strict_jayang),
            ("busan", raw_busan, strict_busan),
        ):
            if raw_match:
                candidate_filter[lane_key]["rawLocation"] = True
                lane_filter_counts[lane_key]["rawLocation"] += 1
            if strict_match:
                candidate_filter[lane_key]["strictLocation"] = True
                lane_filter_counts[lane_key]["strictLocation"] += 1
        if not (raw_jayang or raw_busan):
            filter_counts["excludedNoTargetLocation"] += 1
            continue
        filter_counts["targetLocation"] += 1
        detailed_filter_counts["rawLocation"] += 1
        if not (strict_jayang or strict_busan):
            filter_counts["excludedNoStrictLocation"] += 1
            continue
        filter_counts["strictLocation"] += 1
        detailed_filter_counts["strictLocation"] += 1

        role_ok, role_reason, sector_evidence, domain_signals = _lifestyle_role_gate(posting, title, company)
        relevant_domain = bool(sector_evidence or domain_signals)
        if relevant_domain:
            filter_counts["relevantDomain"] += 1
            detailed_filter_counts["relevantDomain"] += 1
            for lane_key in ("jayang_wlb", "busan"):
                if candidate_filter[lane_key]["strictLocation"]:
                    candidate_filter[lane_key]["relevantDomain"] = True
                    lane_filter_counts[lane_key]["relevantDomain"] += 1
        if not role_ok:
            filter_counts[role_reason] += 1
            continue
        filter_counts["roleFit"] += 1
        detailed_filter_counts["roleFit"] += 1
        for lane_key in ("jayang_wlb", "busan"):
            if candidate_filter[lane_key]["strictLocation"]:
                candidate_filter[lane_key]["roleFit"] = True
                lane_filter_counts[lane_key]["roleFit"] += 1

        experience_value = _fact_value(posting, "facts", "experience")
        experience_text = json.dumps(experience_value, ensure_ascii=False, sort_keys=True, default=str)
        entry_signal_text = " ".join(filter(None, (title, company, experience_text)))
        entry_signals = _entry_signals(entry_signal_text)
        minimum_experience_years = _minimum_experience_years(posting)
        if (
            minimum_experience_years is not None
            and minimum_experience_years >= MINIMUM_EXPERIENCE_EXCLUSION_YEARS
        ) or SENIOR_BLOCK_PATTERN.search(entry_signal_text):
            filter_counts["excludedSenior"] += 1
            continue
        if not entry_signals and not (
            minimum_experience_years is not None
            and minimum_experience_years < MINIMUM_EXPERIENCE_EXCLUSION_YEARS
        ):
            filter_counts["excludedNotJunior"] += 1
            continue
        filter_counts["juniorAttainable"] += 1
        detailed_filter_counts["juniorAttainable"] += 1
        for lane_key in ("jayang_wlb", "busan"):
            if candidate_filter[lane_key]["strictLocation"]:
                candidate_filter[lane_key]["juniorAttainable"] = True
                lane_filter_counts[lane_key]["juniorAttainable"] += 1

        wlb_axis = _wlb_axis(posting)
        if wlb_axis["status"] == "negative":
            filter_counts["excludedWlbNegative"] += 1
            continue
        filter_counts["wlbNotNegative"] += 1
        detailed_filter_counts["wlbNotNegative"] += 1
        for lane_key in ("jayang_wlb", "busan"):
            if candidate_filter[lane_key]["strictLocation"]:
                candidate_filter[lane_key]["wlbNotNegative"] = True
                lane_filter_counts[lane_key]["wlbNotNegative"] += 1

        if job_id in seen_job_ids or url in seen_urls:
            filter_counts["excludedDuplicate"] += 1
            continue
        seen_job_ids.add(job_id)
        seen_urls.add(url)
        detailed_filter_counts["deduplicated"] += 1

        for lane_key in ("jayang_wlb", "busan"):
            if not candidate_filter[lane_key]["strictLocation"]:
                continue
            candidate_filter[lane_key]["reviewCandidate"] = True
            lane_filter_counts[lane_key]["reviewCandidate"] += 1
            if source_status["state"] == "known_open":
                candidate_filter[lane_key]["verifiedOpen"] = True
                lane_filter_counts[lane_key]["verifiedOpen"] += 1
            else:
                candidate_filter[lane_key]["statusRecheck"] = True
                lane_filter_counts[lane_key]["statusRecheck"] += 1

        if candidate_filter["jayang_wlb"]["reviewCandidate"]:
            commute_axis = _lifestyle_axis(
                "unknown",
                "서울권 공개 근무지로 검토 후보에 포함했지만 자양동 출발 통근 가능성은 아직 미확인입니다.",
                [f"공개 근무지: {location or 'location not stated'}"],
                ["정확한 사무실 주소", "주간 출근 횟수", "출퇴근 대중교통 소요 시간"],
            )
        else:
            commute_axis = _lifestyle_axis(
                "unknown",
                "자양동 통근 후보로 분류할 근거가 없습니다.",
                [],
                ["정확한 근무지", "출퇴근 소요 시간"],
            )

        if candidate_filter["busan"]["reviewCandidate"]:
            busan_axis = _lifestyle_axis(
                "claimed",
                "공고의 근무지 필드에 부산이 명시됐습니다.",
                [f"공개 근무지: {location}"],
                ["정확한 사무실 주소", "하이브리드·외근 비중"],
            )
        else:
            busan_axis = _lifestyle_axis(
                "unknown",
                "공개 근무지에 부산이 명시되지 않았습니다.",
                [],
                ["부산 실제 근무지 여부"],
            )

        jayang_status = _combined_lifestyle_status(commute_axis["status"], wlb_axis["status"])
        busan_status = busan_axis["status"]
        if candidate_filter["jayang_wlb"]["reviewCandidate"]:
            jayang_rows.append((job_id, jayang_status))
        if candidate_filter["busan"]["reviewCandidate"]:
            busan_rows.append((job_id, busan_status))
        candidate_class = "verifiedOpen" if source_status["state"] == "known_open" else "statusRecheck"
        detailed_filter_counts[candidate_class] += 1
        role_evidence = sector_evidence or domain_signals
        role_summary = ", ".join(role_evidence[:3])
        entry_summary = ", ".join(entry_signals[:3])
        entry_reason = f"\uc9c4\uc785 \uac00\ub2a5 \uc2e0\ud638: {entry_summary}"
        if not entry_summary:
            entry_reason = f"\uacf5\uac1c \ucd5c\uc18c \uacbd\ub825 {minimum_experience_years:g}\ub144"
        strict_label = str(strict["normalized"])
        status_label = str(source_status["statusLabel"])
        inclusion_reasons = [
            f"\uc6d0\ucc9c \uc704\uce58\uac00 {strict_label}\ub85c \uc5c4\uaca9 \uc77c\uce58",
            f"\uc9c1\ubb34\u00b7\ubd84\uc57c \uadfc\uac70: {role_summary}",
            entry_reason,
            f"\uacf5\uac1c \uc0c1\ud0dc \ubd84\ub958: {status_label}",
        ]
        missing_reasons: list[str] = []
        if candidate_class == "statusRecheck":
            missing_reasons.append("\ud604\uc7ac \uacf5\uace0\uac00 \uc2e4\uc81c \uc811\uc218 \uc911\uc778\uc9c0 \uc6d0\ubb38 \uc7ac\ud655\uc778 \ud544\uc694")
        if strict_jayang:
            missing_reasons.append("\uc790\uc591\ub3d9 \ucd9c\ubc1c \uc2e4\uc81c \uc8fc\uc18c\u00b7\ucd9c\uadfc\uc77c\u00b7\ub300\uc911\uad50\ud1b5 \uc2dc\uac04 \ubbf8\ud655\uc778")
        if strict_busan:
            missing_reasons.append("\ubd80\uc0b0\uc758 \uc815\ud655\ud55c \uc0ac\ubb34\uc2e4 \uc8fc\uc18c\u00b7\uc678\uadfc\u00b7\ud558\uc774\ube0c\ub9ac\ub4dc \uc870\uac74 \ubbf8\ud655\uc778")
        if wlb_axis["status"] == "unknown":
            missing_reasons.append("\uadfc\ubb34\uc2dc\uac04\u00b7\ucd08\uacfc\uadfc\ubb34\u00b7\ud734\uac00 \uc0ac\uc6a9 \ub4f1 \uc6cc\ub77c\ubc38 \uadfc\uac70 \ubbf8\ud655\uc778")
        items.append(
            {
                "jobId": job_id,
                "title": title,
                "company": company,
                "location": location,
                "market": "domestic",
                "domestic": True,
                "strictLocation": {
                    **strict,
                    "domestic": True,
                    "locationText": location,
                    "lanes": {
                        "jayang_wlb": candidate_filter["jayang_wlb"]["strictLocation"],
                        "busan": candidate_filter["busan"]["strictLocation"],
                    },
                },
                "filterReason": role_reason,
                "candidateFilter": candidate_filter,
                "candidateEvidence": [
                    {
                        "source": LIFESTYLE_SOURCE_ARTIFACT,
                        "method": LIFESTYLE_METHOD_VERSION,
                        "text": (
                            f"근무지={location or '미기재'}; "
                            f"직무필터={role_reason}; "
                            f"공개상태={source_status['state']}"
                        ),
                    }
                ],
                "inclusionReasons": inclusion_reasons,
                "missingReasons": missing_reasons,
                "scoreImpactReason": "\uc9c0\uc5ed\u00b7\ud1b5\uadfc\u00b7\uc6cc\ub77c\ubc38\uc740 \ucd94\ucc9c \uc810\uc218\uc5d0 \ub123\uc9c0 \uc54a\uace0 \ubcc4\ub3c4 \ubd84\ub958\u00b7\uac80\uc99d\ud569\ub2c8\ub2e4.",
                "entrySignals": entry_signals,
                # JSON.parse/JSON.stringify normalizes 1.0 to 1 in the browser.
                # Keep the signed snapshot digest identical in Python and the PWA.
                "minimumExperienceYears": (
                    int(minimum_experience_years)
                    if minimum_experience_years is not None and minimum_experience_years.is_integer()
                    else minimum_experience_years
                ),
                "sectorEvidence": sector_evidence,
                "domainSignals": domain_signals,
                "source": str(posting.get("source") or ""),
                "url": url,
                "sourceStatus": source_status,
                "candidateClass": candidate_class,
                "relevantSectors": sorted(_posting_relevant_sector_ids(posting)),
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

    status_order = {"known_open": 0, "status_unknown": 1, "archived_reference": 2}
    evidence_order = {"confirmed": 0, "claimed": 1, "unknown": 2, "negative": 3}
    items.sort(
        key=lambda item: (
            status_order.get(str(item["sourceStatus"]["state"]), 9),
            evidence_order.get(str(item["lifestyleEvidence"]["axes"]["wlb"]["status"]), 9),
            str(item.get("company") or "").casefold(),
            str(item.get("title") or "").casefold(),
            str(item["jobId"]),
        )
    )
    jayang_ids = [str(item["jobId"]) for item in items if item["candidateFilter"]["jayang_wlb"]["reviewCandidate"]]
    busan_ids = [str(item["jobId"]) for item in items if item["candidateFilter"]["busan"]["reviewCandidate"]]
    filter_counts["publishedCandidates"] = len(items)
    detailed_filter_counts["publishedCandidate"] = len(items)
    verified_open_count = detailed_filter_counts["verifiedOpen"]
    searched_at = datetime.now(timezone.utc).isoformat()
    discovery = {
        "schemaVersion": LIFESTYLE_METHOD_VERSION,
        "methodVersion": LIFESTYLE_METHOD_VERSION,
        "asOf": str(payload.get("dataAsOf") or payload.get("generatedAt") or ""),
        "searchState": "searched",
        "searchedAt": searched_at,
        "scoreImpact": "none",
        "sourceArtifact": "job_search/work/recommendation-v4/g003-posting-facts.json",
        "sourceArtifactDigest": artifact_digest,
        "sourceFileSha256": _file_sha256(posting_facts_path),
        "sourcePostingCount": declared_count,
        "sourceRelevantPostingCount": relevant_count,
        "publicRecommendationCount": verified_open_count,
        "publicCandidateCount": len(items),
        "universeLabel": "G003 전체 채용 원장 중 국내 위치·직무 신호 필터",
        "candidateFilter": filter_counts,
        "filterCounts": detailed_filter_counts,
        "limitations": [
            "검색 범위는 G003 원장 전체이며, 전체 채용시장 전수조사는 아닙니다.",
            "원천 위치 일치는 수집 원문 히트이고, 엄격 후보는 공개 근무지·직무 신호·공개 상태를 다시 통과한 별도 검토 대상입니다.",
            "통근 소요 시간은 정확한 사무실·출근일·대중교통 검증 전까지 확정하지 않습니다.",
            "원격·하이브리드나 복지 문구만으로 워라밸을 확정하지 않습니다.",
            "생활 조건은 추천 점수에 반영하지 않습니다.",
            "서울/부산 표기는 추천 확정이 아니라 생활조건 확인을 시작하기 위한 필터입니다.",
        ],
        "items": items,
        "lanes": {
            "jayang_wlb": {
                "label": "자양동 출발 서울권 · 통근/WLB 확인",
                "searchState": "searched",
                "searchedAt": searched_at,
                "reviewIds": jayang_ids,
                "matchedCount": len(jayang_ids),
                "counts": _lifestyle_counts(jayang_rows),
                "filterCounts": lane_filter_counts["jayang_wlb"],
                "classCounts": _candidate_class_counts(items, jayang_ids),
                "axisCounts": _axis_counts(items, jayang_ids),
                "decisionReadiness": _decision_readiness(items, jayang_ids, ("jayangCommute", "wlb")),
            },
            "busan": {
                "label": "부산 근무지 검토 · WLB 별도 확인",
                "searchState": "searched",
                "searchedAt": searched_at,
                "reviewIds": busan_ids,
                "matchedCount": len(busan_ids),
                "counts": _lifestyle_counts(busan_rows),
                "filterCounts": lane_filter_counts["busan"],
                "classCounts": _candidate_class_counts(items, busan_ids),
                "axisCounts": _axis_counts(items, busan_ids),
                "decisionReadiness": _decision_readiness(items, busan_ids, ("busanWorkplace",)),
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
    parser.add_argument(
        "--personalized-runtime",
        action="store_true",
        help="Build the authenticated Supabase runtime artifact outside the public app repository.",
    )
    args = parser.parse_args()
    app_root = Path(__file__).resolve().parents[1]
    root = args.job_search_root.resolve(strict=True)
    # DATA-249: static GitHub Pages output is anonymous by default.  Only the
    # explicit authenticated lane may carry preferences, and it has one private
    # producer/consumer path: state_v4/career-compass-personalized-snapshot.json.
    assert_active_repository(
        app_root,
        args.output,
        personalized_runtime=args.personalized_runtime,
        job_search_root=root,
    )
    if args.programs_only and args.personalized_runtime:
        raise ValueError("programs-only and personalized-runtime cannot be combined")
    posting_facts_path = root / "work" / "recommendation-v4" / "g003-posting-facts.json"
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
        _apply_lifestyle_discovery(payload, posting_facts_path)
        payload["graduateDataLineage"] = _graduate_data_lineage(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.output}: enriched {len(payload['programs'])} programs")
        return
    raw_job_slice = build_public_job_slice(
        actions_path=root / "work" / "recommendation-v4" / "g006-cross-sector-actions.json",
        posting_facts_path=posting_facts_path,
        include_personalization=args.personalized_runtime,
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
            # DATA-247: in the authenticated runtime only, carry the durable
            # archive through the exact producer path consumed by the mobile
            # overlay. Public builds receive an empty collection from the slice.
            "savedJobs": job_slice["savedJobs"],
            "reviewQueue": job_slice["reviewQueue"],
            "graduateEvidenceCoverage": _graduate_evidence_coverage(payload["programs"]),
        }
    )
    _apply_decision_support(payload)
    _apply_lifestyle_discovery(payload, posting_facts_path)
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

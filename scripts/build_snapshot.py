"""Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit, urlunsplit


IHE_DELFT = "IHE Delft Institute for Water Education"
MINIMUM_EXPERIENCE_EXCLUSION_YEARS = 2
LIFESTYLE_METHOD_VERSION = "lifestyle-evidence-v2"
GRADUATE_LINEAGE_METHOD_VERSION = "graduate-lineage-v2"
GRADUATE_EVIDENCE_AXES = (
    ("faculty", "faculty"),
    ("recentPapers", "recent_papers"),
    ("fundedProjects", "recent_projects"),
    ("graduateDestinations", "graduate_destinations"),
    ("testimonials", "graduate_testimonials"),
)
GRADUATE_CLAIM_STATE_BY_EVIDENCE = {
    "present": "evidence_present",
    "not_researched": "no_claim",
    "reviewed_no_qualifying": "no_claim",
    "searched_none": "search_no_result",
    "verified_none": "source_asserts_none",
}
# data-requirement-id="SEC-298": public graduate records carry official facts,
# never candidate-specific readiness. The legacy englishGapPlan field is private.
PRIVATE_PROGRAM_READINESS_KEYS = frozenset({"englishgapplan", "privateadmissionsreadiness"})
PRIVATE_PROGRAM_READINESS_PATTERNS = (
    "expired certs",
    "candidate's",
    "candidate must retake",
    "his english certs",
    "as a korean domestic applicant he",
    "as a korean domestic student he",
    "strongest path for this candidate",
    "candidate is most likely ineligible",
    "\uc9c0\uc6d0\uc790 swmm",
)
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


def _decision_framework_source_metrics(job_search_root: Path) -> dict[str, dict[str, Any]]:
    """Read measured decision-support artifacts without treating their dates as posting proof."""

    specs: dict[str, tuple[str, str, str]] = {
        "funding_strategy": ("artifacts/funding/funding_opportunities_latest.json", "opportunities", "count"),
        "application_packaging": ("artifacts/applications/application_sprint_latest.json", "candidates", "count"),
        "source_quality": ("artifacts/source_quality/source_quality_latest.json", "sources", "sourceCount"),
        "research_frontier": ("artifacts/research/expert_topics_normalized.json", "items", "count"),
    }
    metrics: dict[str, dict[str, Any]] = {}
    for lane_id, (relative_path, list_key, count_key) in specs.items():
        path = job_search_root / relative_path
        lane: dict[str, Any] = {
            "available": False,
            "path": relative_path,
            count_key: 0,
            "artifactDateIsPostingProof": False,
        }
        if path.is_file():
            artifact = _read_json(path)
            values = artifact.get(list_key)
            if not isinstance(values, list):
                raise ValueError(f"decision framework source must contain a list at {list_key}: {path}")
            lane["available"] = True
            lane[count_key] = len(values)
            lane["artifactGeneratedAt"] = str(
                artifact.get("generated_at") or artifact.get("generatedAt") or ""
            )
            if lane_id == "source_quality":
                lane["jobCount"] = _int_metric(artifact.get("job_count"))
            if lane_id == "research_frontier":
                strategy_counts = artifact.get("strategy_fit_counts")
                lane["strategyFitCounts"] = dict(strategy_counts) if isinstance(strategy_counts, Mapping) else {}
        metrics[lane_id] = lane
    return metrics


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Replace one JSON artifact only after its complete payload is durable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{os.getpid()}.{secrets.token_hex(6)}.tmp"
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text_file_sha256(path: Path) -> str:
    """Hash text provenance after canonicalizing all supported line endings."""
    raw = path.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(canonical).hexdigest()


_LINEAGE_TEXT_SUFFIXES = frozenset({
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
})


def _lineage_file_sha256(path: Path) -> str:
    """Hash lineage inputs consistently across Windows and Linux checkouts."""
    if path.suffix.lower() in _LINEAGE_TEXT_SUFFIXES:
        return _text_file_sha256(path)
    return _file_sha256(path)


def _repository_commit(repo_root: Path) -> str:
    commit = subprocess.run(
        ["git", "-C", str(repo_root.resolve()), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError(f"invalid repository commit for lineage: {repo_root}")
    return commit


def _lineage_artifact(role: str, path: Path, repo_root: Path, repo_label: str) -> dict[str, str]:
    resolved_path = path.resolve(strict=True)
    resolved_root = repo_root.resolve(strict=True)
    try:
        relative_path = resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"graduate lineage source is outside {repo_label}: {resolved_path}") from exc
    return {
        "role": role,
        "path": f"{repo_label}/{relative_path}",
        "sha256": _lineage_file_sha256(resolved_path),
    }


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
        # data-requirement-id="DATA-276": build into one fenced run artifact;
        # the worker promotes it only after Supabase accepts the same claim.
        if job_search_root is None:
            raise ValueError("personalized runtime builds require the job-search root")
        private_output = (
            job_search_root.resolve() / "state_v4" / "career-compass-personalized-snapshot.json"
        ).resolve()
        staging_root = (job_search_root.resolve() / "state_v4" / ".refresh-staging").resolve()
        candidate = output_path.resolve()
        is_run_staging_artifact = (
            candidate.parent == staging_root
            and re.fullmatch(r"[0-9a-f]{64}\.json", candidate.name) is not None
        )
        if candidate != private_output and not is_run_staging_artifact:
            raise ValueError(
                "personalized runtime builds may write only to the private current artifact "
                f"or one fenced run artifact under: {staging_root}"
            )
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


def current_or_recent_years(value: Any) -> bool:
    """DATA-254: accept only an evidenced year in the current five-year window.

    Missing years are unknown, not recent.  A future-only range is also not a
    current research result; an active range still passes when it contains a
    year between the cutoff and today.
    """
    years = [int(year) for year in re.findall(r"\b20\d{2}\b", str(value or ""))]
    current_year = datetime.now().year
    cutoff = current_year - 4
    return any(cutoff <= year <= current_year for year in years)


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


def _first_text(source: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(source.get(key) or "").strip()
        if value:
            return value
    return ""


def _evidence_quality(source: Mapping[str, Any]) -> str:
    quality = _first_text(source, "evidence_quality", "evidenceQuality").upper()
    return quality if quality in {"A1", "A2", "B", "C", "D", "U"} else "U"


def verified_funded_project(project: Mapping[str, Any]) -> bool:
    """DATA-254: require a funder and a stable award reference or public URL."""
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
    award_id = _first_text(
        project,
        "award_id",
        "awardId",
        "grant_id",
        "grantId",
        "project_id",
        "projectId",
    )
    evidence_url = _public_url(
        _first_text(project, "award_url", "official_url", "url")
    )
    return bool(
        _first_text(project, "title")
        and _first_text(project, "funder")
        and (award_id or evidence_url)
        and not any(marker in evidence_text for marker in non_contract_markers)
    )


def verified_research_project(project: Mapping[str, Any]) -> bool:
    """DATA-216: compatibility contract now delegates to the stricter funded gate."""
    return verified_funded_project(project)


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
            "evidenceQuality": _evidence_quality(source),
        }
        if entry not in sources:
            sources.append(entry)
    return sources


def _graduate_claim_axis(
    source: Mapping[str, Any],
    *,
    axis: str,
    source_key: str,
    record_count: int,
    raw_candidate_count: int,
) -> dict[str, Any]:
    """Keep an empty collection unknown unless a sourced absence was declared."""
    configured = source.get("evidence_states")
    if not isinstance(configured, Mapping):
        configured = source.get("evidenceStates")
    configured = configured if isinstance(configured, Mapping) else {}
    specification = configured.get(source_key, configured.get(axis))

    if record_count > 0:
        if isinstance(specification, Mapping) and specification.get("state") in {
            "searched_none",
            "verified_none",
        }:
            raise ValueError(f"{axis} evidence state contradicts collected records")
        return {
            "claimState": "evidence_present",
            "evidenceState": "present",
            "recordCount": record_count,
            "sources": [],
        }

    if specification is None:
        evidence_state = "reviewed_no_qualifying" if raw_candidate_count else "not_researched"
        return {
            "claimState": GRADUATE_CLAIM_STATE_BY_EVIDENCE[evidence_state],
            "evidenceState": evidence_state,
            "recordCount": None,
            "sources": [],
        }
    if not isinstance(specification, Mapping):
        raise ValueError(f"{axis} evidence state must be an object")

    evidence_state = str(specification.get("state", "")).strip()
    if evidence_state not in GRADUATE_CLAIM_STATE_BY_EVIDENCE:
        raise ValueError(f"unsupported graduate evidence state: {evidence_state or 'blank'}")
    if evidence_state == "present":
        raise ValueError(f"{axis} present evidence state requires collected records")
    sources = _typed_sources(
        specification.get("sources"),
        fallback_url=specification.get("url"),
        default_type="graduate_axis_state_source",
        default_label="graduate evidence state source",
    )
    if evidence_state in {"searched_none", "verified_none"} and not sources:
        raise ValueError(f"{evidence_state} requires public source evidence")
    return {
        "claimState": GRADUATE_CLAIM_STATE_BY_EVIDENCE[evidence_state],
        "evidenceState": evidence_state,
        "recordCount": 0 if evidence_state in {"searched_none", "verified_none"} else None,
        "sources": sources,
    }


def _public_research(source: dict[str, Any]) -> dict[str, Any]:
    """DATA-213/DATA-255: preserve claim evidence, never alumni identity."""
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
                "doi": _first_text(paper, "doi"),
                "authorRole": _first_text(paper, "author_role", "authorRole"),
                "sourceType": _first_text(paper, "source_type", "sourceType"),
                "evidenceQuality": _evidence_quality(paper),
            }
            for paper in person.get("recent_papers", [])
            if (
                isinstance(paper, dict)
                and paper.get("title")
                and current_or_recent_years(paper.get("year"))
            )
        ]
        projects = [
            {
                "title": str(project.get("title", "")).strip(),
                "funder": str(project.get("funder", "")).strip(),
                "period": str(project.get("period", "")).strip(),
                "amount": str(project.get("amount", "")).strip(),
                "url": _public_url(
                    _first_text(project, "award_url", "official_url", "url")
                ),
                "awardId": _first_text(
                    project,
                    "award_id",
                    "awardId",
                    "grant_id",
                    "grantId",
                    "project_id",
                    "projectId",
                ),
                "facultyRole": _first_text(project, "faculty_role", "facultyRole"),
                "sourceType": _first_text(project, "source_type", "sourceType"),
                "evidenceQuality": _evidence_quality(project),
                "evidenceStatus": "verified_funded_project",
            }
            for project in person.get("recent_projects", [])
            if (
                isinstance(project, dict)
                and project.get("title")
                and current_or_recent_years(project.get("period"))
                and verified_funded_project(project)
            )
        ]
        faculty.append(
            {
                "name": str(person.get("name", "")).strip(),
                "title": str(person.get("title", "")).strip(),
                "labOrGroup": str(person.get("lab_or_group", "")).strip(),
                "orcid": _first_text(person, "orcid", "orcid_id", "orcidId"),
                "evidenceQuality": _evidence_quality(person),
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
            "cohort": _first_text(item, "cohort", "year_range"),
            "degree": _first_text(item, "degree", "degree_level"),
            "destination": str(item.get("destination", "")).strip(),
            "role": str(item.get("role", "")).strip(),
            "aggregationLevel": _first_text(
                item,
                "aggregation_level",
                "aggregationLevel",
            ) or "unknown",
            "evidenceQuality": _evidence_quality(item),
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
    raw_faculty = source.get("faculty") if isinstance(source.get("faculty"), list) else []
    raw_counts = {
        "faculty": len(raw_faculty),
        "recentPapers": sum(
            len(person.get("recent_papers", []))
            for person in raw_faculty
            if isinstance(person, dict) and isinstance(person.get("recent_papers", []), list)
        ),
        "fundedProjects": sum(
            len(person.get("recent_projects", []))
            for person in raw_faculty
            if isinstance(person, dict) and isinstance(person.get("recent_projects", []), list)
        ),
        "graduateDestinations": len(source.get("graduate_destinations", []))
        if isinstance(source.get("graduate_destinations"), list)
        else 0,
        "testimonials": len(source.get("graduate_testimonials", []))
        if isinstance(source.get("graduate_testimonials"), list)
        else 0,
    }
    record_counts = {
        "faculty": len(faculty),
        "recentPapers": sum(len(person["recentPapers"]) for person in faculty),
        "fundedProjects": sum(len(person["recentProjects"]) for person in faculty),
        "graduateDestinations": len(destinations),
        "testimonials": len(testimonials),
    }
    claim_evidence = {
        axis: _graduate_claim_axis(
            source,
            axis=axis,
            source_key=source_key,
            record_count=record_counts[axis],
            raw_candidate_count=raw_counts[axis],
        )
        for axis, source_key in GRADUATE_EVIDENCE_AXES
    }
    evidence_states = {item["evidenceState"] for item in claim_evidence.values()}
    if "present" in evidence_states:
        evidence_status = "\ud56d\ubaa9\ubcc4 \uacf5\uac1c \uadfc\uac70 \uc77c\ubd80 \ud655\uc778"
    elif "reviewed_no_qualifying" in evidence_states:
        evidence_status = "\ud6c4\ubcf4 \uadfc\uac70 \uac80\ud1a0 \ud6c4 \uc694\uac74 \ucda9\uc871 \uc790\ub8cc \uc5c6\uc74c"
    else:
        evidence_status = "\uacf5\uac1c \uc5f0\uad6c\uc790\ub8cc \ubbf8\uc870\uc0ac"
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
        "claimEvidence": claim_evidence,
        "lastVerified": _verified_date(source),
        "evidenceStatus": evidence_status,
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


def _validate_shortlist_source_lineage(
    shortlist: Mapping[str, Any],
    research_path: Path,
) -> None:
    """DATA-282: reject a shortlist that was not built from this research artifact."""
    lineage = shortlist.get("source_lineage")
    if not isinstance(lineage, dict):
        raise ValueError("graduate shortlist source lineage is missing")
    expected_relative_path = "config/grad_school_programs.researched.json"
    if str(lineage.get("source_path") or "").replace("\\", "/") != expected_relative_path:
        raise ValueError("graduate shortlist source path mismatch")
    if not research_path.is_file():
        raise ValueError("graduate research source is missing")
    research = _read_json_list(research_path)
    if str(lineage.get("source_sha256") or "") != _file_sha256(research_path):
        raise ValueError("graduate shortlist source digest mismatch")
    if lineage.get("source_program_count") != len(research):
        raise ValueError("graduate shortlist source count mismatch")
    programs = shortlist.get("programs")
    if not isinstance(programs, list) or lineage.get("shortlist_program_count") != len(programs):
        raise ValueError("graduate shortlist output count mismatch")


def _apply_latest_programs(payload: dict[str, Any], shortlist_path: Path, research_path: Path) -> str:
    """Refresh compact programme records from the lightweight current shortlist."""
    shortlist = _read_json(shortlist_path)
    _validate_shortlist_source_lineage(shortlist, research_path)
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
                    "publicResearch": _public_research(research) if research else _public_research({}),
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
                }
            )
        item["publicResearch"] = _public_research(research) if research else _public_research({})
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


def _public_program_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _strip_private_program_text(value: str) -> str:
    segments = re.split(r"(?<=[.!?。！？])\s+|\r?\n+", value)
    kept = [
        segment
        for segment in segments
        if segment.strip()
        and not any(pattern in segment.casefold() for pattern in PRIVATE_PROGRAM_READINESS_PATTERNS)
    ]
    return " ".join(segment.strip() for segment in kept)


def _sanitize_public_program_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, nested in value.items():
            if _public_program_key(key) in PRIVATE_PROGRAM_READINESS_KEYS:
                continue
            cleaned = _sanitize_public_program_value(nested)
            # DATA-306: an empty source list is an explicit public-evidence
            # boundary, not missing data; preserve it for claim validation.
            if cleaned not in (None, "", [], {}) or str(key) == "sources":
                sanitized[str(key)] = cleaned
        return sanitized
    if isinstance(value, list):
        sanitized_items = [_sanitize_public_program_value(item) for item in value]
        return [item for item in sanitized_items if item not in (None, "", [], {})]
    if isinstance(value, str):
        return _strip_private_program_text(value)
    return value


def _sanitize_public_programs(payload: dict[str, Any]) -> None:
    """Fail closed when a public programme record still contains private readiness."""
    programs = payload.get("programs")
    if not isinstance(programs, list):
        raise ValueError("public graduate programme list is missing")
    payload["programs"] = [
        cleaned
        for item in programs
        if isinstance(item, Mapping)
        for cleaned in [_sanitize_public_program_value(item)]
        if isinstance(cleaned, dict)
    ]
    serialized = json.dumps(payload["programs"], ensure_ascii=False).casefold()
    if any(pattern in serialized for pattern in PRIVATE_PROGRAM_READINESS_PATTERNS):
        raise ValueError("public graduate privacy sanitization failed")
    if any(_public_program_key(key) in serialized for key in PRIVATE_PROGRAM_READINESS_KEYS):
        raise ValueError("public graduate privacy field removal failed")


def _graduate_evidence_coverage(programs: Any) -> dict[str, int]:
    """Expose programme-level evidence coverage against the complete public list."""
    records = [item for item in programs if isinstance(item, dict)] if isinstance(programs, list) else []
    research = [
        item.get("publicResearch") if isinstance(item.get("publicResearch"), dict) else {}
        for item in records
    ]
    claim_states = [
        item.get("claimEvidence") if isinstance(item.get("claimEvidence"), dict) else {}
        for item in research
    ]

    def evidence_state(claims: Mapping[str, Any], axis: str) -> str:
        value = claims.get(axis)
        return str(value.get("evidenceState", "not_researched")) if isinstance(value, dict) else "not_researched"

    has_faculty = [evidence_state(item, "faculty") == "present" for item in claim_states]
    has_papers = [evidence_state(item, "recentPapers") == "present" for item in claim_states]
    has_projects = [evidence_state(item, "fundedProjects") == "present" for item in claim_states]
    has_outcomes = [evidence_state(item, "graduateDestinations") == "present" for item in claim_states]
    has_testimonials = [evidence_state(item, "testimonials") == "present" for item in claim_states]
    has_any = [
        any(values)
        for values in zip(has_faculty, has_papers, has_projects, has_outcomes, has_testimonials)
    ]
    unresearched = [
        all(evidence_state(claims, axis) == "not_researched" for axis, _ in GRADUATE_EVIDENCE_AXES)
        for claims in claim_states
    ]
    return {
        "totalPrograms": len(records),
        "programsWithAnyEvidence": sum(has_any),
        "programsWithFaculty": sum(has_faculty),
        "programsWithRecentPapers": sum(has_papers),
        "programsWithFundedProjects": sum(has_projects),
        "programsWithGraduateDestinations": sum(has_outcomes),
        "programsWithTestimonials": sum(has_testimonials),
        "unresearchedPrograms": sum(unresearched),
    }


def _graduate_data_lineage(
    payload: Mapping[str, Any],
    *,
    app_root: Path,
    job_search_root: Path,
    catalog_source: Path,
    shortlist_source: Path,
    research_source: Path,
) -> dict[str, Any]:
    """DATA-227/DATA-256: bind the payload to its exact sources and producer."""
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
    payload_digest = hashlib.sha256(canonical).hexdigest()
    producer_code_digest = _text_file_sha256(Path(__file__).resolve())
    producer_commit = _repository_commit(app_root)
    source_commit = _repository_commit(job_search_root)
    source_artifacts = [
        _lineage_artifact("catalog", catalog_source, app_root, "career-job-compass"),
        _lineage_artifact("programDiscovery", shortlist_source, job_search_root, "job_search"),
        _lineage_artifact("researchEvidence", research_source, job_search_root, "job_search"),
    ]
    source_manifest_digest = hashlib.sha256(
        json.dumps(source_artifacts, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    generation_inputs = {
        "methodVersion": GRADUATE_LINEAGE_METHOD_VERSION,
        "producerCodeSha256": producer_code_digest,
        "producerRepositoryCommit": producer_commit,
        "sourceRepositoryCommit": source_commit,
        "sourceManifestSha256": source_manifest_digest,
        "payloadSha256": payload_digest,
    }
    generation_inputs_digest = hashlib.sha256(
        json.dumps(generation_inputs, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schemaVersion": GRADUATE_LINEAGE_METHOD_VERSION,
        "methodVersion": GRADUATE_LINEAGE_METHOD_VERSION,
        "producer": "career-job-compass/scripts/build_snapshot.py",
        "artifact": "career-job-compass/data/app-data.json",
        "producerCodeSha256": producer_code_digest,
        "producerRepositoryCommit": producer_commit,
        "sourceRepositoryCommit": source_commit,
        "sourceArtifacts": source_artifacts,
        "sourceManifestSha256": source_manifest_digest,
        "generationInputsSha256": generation_inputs_digest,
        "payloadSha256": payload_digest,
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
    testimonials = research.get("graduateTestimonials") if isinstance(research.get("graduateTestimonials"), list) else []
    papers = sum(len(item.get("recentPapers") or []) for item in faculty if isinstance(item, dict))
    claims = research.get("claimEvidence") if isinstance(research.get("claimEvidence"), dict) else {}

    def evidence_state(axis: str) -> str:
        value = claims.get(axis)
        return str(value.get("evidenceState", "not_researched")) if isinstance(value, dict) else "not_researched"

    evidence_label = str(research.get("evidenceStatus") or "\uacf5\uac1c \uc5f0\uad6c\uc790\ub8cc")
    known = [
        _fact("\uc900\ube44 \uc0c1\ud0dc", program.get("applicationStatusLabel"), "\ubd84\ub958 \uc5d4\uc9c4"),
        _fact("\ud559\uc704\u00b7\uad6d\uac00", " \u00b7 ".join(filter(None, [program.get("degree"), program.get("country")]))),
        _fact("\ub9c8\uac10", program.get("deadline")),
        _fact("\uc7ac\uc815 \uc9c0\uc6d0", program.get("funding")),
        _fact("\uc601\uc5b4 \uc694\uac74", program.get("english")),
    ]

    axis_facts = (
        ("\uad50\uc218", "faculty", f"\uacf5\uac1c \ud504\ub85c\ud544 {len(faculty)}\uba85"),
        ("\ucd5c\uadfc 5\ub144 \ub17c\ubb38", "recentPapers", f"\uacf5\uac1c \ub17c\ubb38 {papers}\uac74"),
        ("\ucd5c\uadfc 5\ub144 \uc5f0\uad6c\uc6a9\uc5ed", "fundedProjects", f"\ud655\uc778\ub41c \uc5f0\uad6c\uc6a9\uc5ed {len(projects)}\uac74"),
        ("\uc878\uc5c5\uc0dd \uc9c4\ub85c", "graduateDestinations", f"\uacf5\uac1c \uc9c4\ub85c \uadfc\uac70 {len(outcomes)}\uac74"),
        ("\uc878\uc5c5\uc0dd \ud6c4\uae30", "testimonials", f"\uacf5\uac1c \ud6c4\uae30 {len(testimonials)}\uac74"),
    )
    for label, axis, value in axis_facts:
        state = evidence_state(axis)
        if state == "present":
            known.append(_fact(label, value, evidence_label))
        elif state == "verified_none":
            known.append(_fact(label, "\uacf5\uac1c \uadfc\uac70\uc0c1 \ud574\ub2f9 \uc5c6\uc74c", evidence_label))

    missing = []
    if not program.get("deadline"):
        missing.append({"label": "\ub9c8\uac10\uc77c", "why": "\ucd5c\uc2e0 \uc785\ud559 \uacf5\uace0 \uc7ac\ud655\uc778 \ud544\uc694"})
    missing_reason = {
        "not_researched": "\ubbf8\uc870\uc0ac",
        "reviewed_no_qualifying": "\ud6c4\ubcf4\ub97c \uac80\ud1a0\ud588\uc9c0\ub9cc \uacf5\uac1c \uadfc\uac70 \uc694\uac74\uc744 \ucda9\uc871\ud558\uc9c0 \ubabb\ud568",
        "searched_none": "\uac80\uc0c9\ud588\uc9c0\ub9cc \uacf5\uac1c \uadfc\uac70\ub97c \ucc3e\uc9c0 \ubabb\ud568",
    }
    for label, axis, _ in axis_facts:
        state = evidence_state(axis)
        if state not in {"present", "verified_none"}:
            missing.append({"label": label, "why": missing_reason.get(state, "\uc0c1\ud0dc \uc7ac\ud655\uc778 \ud544\uc694")})
    missing.append({"label": "\ud3c9\uade0 \uc878\uc5c5 \uae30\uac04\u00b7\uc911\ub3c4\ud0c8\ub77d", "why": "\uacfc\uc815 \uc644\uc8fc \uc704\ud5d8 \uadfc\uac70 \ubbf8\ud655\uc778"})
    missing.append({"label": "\uc5f0\uad6c\uc2e4 \ubb38\ud654\u00b7\uc9c0\ub3c4 \ubc29\uc2dd", "why": "\uc7ac\ud559\uc0dd\u00b7\uc878\uc5c5\uc0dd \ud6c4\uae30 \ucd94\uac00 \ud655\uc778 \ud544\uc694"})
    research_present = evidence_state("faculty") == "present" or evidence_state("recentPapers") == "present"
    outcome_present = evidence_state("graduateDestinations") == "present"
    research_value = (
        "\uad50\uc218\u00b7\ub17c\ubb38 \uacf5\uac1c \uadfc\uac70 \ud655\uc778"
        if research_present
        else "\uad50\uc218\u00b7\ub17c\ubb38 \uadfc\uac70 \ubbf8\uc870\uc0ac\u00b7\ud655\uc778 \ud544\uc694"
    )
    outcome_value = (
        f"\uacf5\uac1c \uc9c4\ub85c \uadfc\uac70 {len(outcomes)}\uac74"
        if outcome_present
        else "\uc878\uc5c5\uc0dd \uc9c4\ub85c \uadfc\uac70 \ubbf8\uc870\uc0ac\u00b7\ud655\uc778 \ud544\uc694"
    )
    dimensions = [
        {"label": "\uc9c0\uc6d0 \uac00\ub2a5\uc131", "status": "\ubd80\ubd84 \ud655\uc778", "value": str(program.get("applicationStatusLabel") or "\uc6d0\ubb38 \ud655\uc778")},
        {"label": "\uc5f0\uad6c \uc801\ud569", "status": "\uadfc\uac70 \uc788\uc74c" if research_present else "\uc815\ubcf4 \ubd80\uc871", "value": research_value},
        {"label": "\ube44\uc6a9\u00b7\uc7ac\uc815", "status": "\ud655\uc778" if program.get("funding") else "\uc815\ubcf4 \ubd80\uc871", "value": str(program.get("funding") or program.get("tuition") or "\ucd94\uac00 \ud655\uc778")},
        {"label": "\uc878\uc5c5 \ud6c4 \uc9c4\ub85c", "status": "\uadfc\uac70 \uc788\uc74c" if outcome_present else "\uc815\ubcf4 \ubd80\uc871", "value": outcome_value},
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


def _framework_subfield(
    key: str,
    label: str,
    depth: str,
    process: str,
    gate: str,
    loop: str,
    evidence: list[str],
    status: str = "active",
) -> dict[str, Any]:
    return {
        "id": key,
        "label": label,
        "depth": depth,
        "process": process,
        "gate": gate,
        "loop": loop,
        "requiredEvidence": evidence,
        "status": status,
        "implementationState": "planned",
        "gateState": "hold",
        "currentMetrics": ["No connected measurement"],
        "followup": "Connect the evidence producer and consumer before re-evaluation",
        "evidencePath": "unconnected",
    }


def _framework_domain(key: str, label: str, signal: str, subfields: list[dict[str, Any]]) -> dict[str, Any]:
    return {"id": key, "label": label, "currentSignal": signal, "subfields": subfields}


FRAMEWORK_IMPLEMENTATION_STATES = frozenset({"connected", "partial", "runtime_only", "planned"})
FRAMEWORK_GATE_STATES = frozenset({"pass", "review", "hold", "runtime"})
# data-requirement-id="DATA-294": required_framework_domain_ids are an
# expandable minimum contract, not a fixed domain/subfield ceiling.
REQUIRED_FRAMEWORK_DOMAIN_IDS = frozenset(
    {
        "career",
        "graduate",
        "lifestyle",
        "feedback",
        "reliability",
        "execution",
        "application_feasibility",
        "decision_economics",
        "career_capital",
        "organizational_reality",
        "application_pipeline",
        "uncertainty_risk",
    }
)
REQUIRED_FRAMEWORK_SUBFIELD_IDS = frozenset(
    {
        "water_hydrology",
        "climate_env_ai",
        "gis_remote_sensing",
        "oda_policy_pm",
        "domestic_wlb",
        "research_frontier",
        "supervisor_fit",
        "papers",
        "funded_projects",
        "alumni_outcomes",
        "lab_life",
        "funding_strategy",
        "toefl_transcript_readiness",
        "jayang_commute",
        "busan_lane",
        "city_safety_quality",
        "structured_reasons",
        "all_rows_compare",
        "negative_learning",
        "official_jobs",
        "community_leads",
        "alumni_public",
        "source_quality",
        "producer_consumer",
        "phase_gate_loop",
        "mobile_release",
        "eligibility_hard_gates",
        "timing_documents",
        "compensation_contract",
        "skill_gap_bridge",
        "application_packaging",
        "salary_living_cost",
        "opportunity_cost",
        "evidence_confidence",
        "portfolio_balance",
        "work_substance",
        "skill_compounding",
        "exit_options",
        "stability_contract",
        "manager_team",
        "culture_workload",
        "priority_actionability",
        "materials_readiness",
        "interview_feedback",
        "posting_currentness",
        "provenance_dedup",
        "reversibility_red_flags",
    }
)


def _int_metric(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _mapping_at(source: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = source.get(key)
    return value if isinstance(value, Mapping) else {}


def _framework_state(
    implementation_state: str,
    gate_state: str,
    current_metrics: list[str],
    followup: str,
    evidence_path: str,
) -> dict[str, Any]:
    if implementation_state not in FRAMEWORK_IMPLEMENTATION_STATES:
        raise ValueError(f"invalid framework implementation state: {implementation_state}")
    if gate_state not in FRAMEWORK_GATE_STATES:
        raise ValueError(f"invalid framework gate state: {gate_state}")
    metrics = [str(metric).strip() for metric in current_metrics if str(metric).strip()]
    if not metrics:
        raise ValueError("framework state requires at least one current metric")
    if not str(followup).strip() or not str(evidence_path).strip():
        raise ValueError("framework state requires followup and evidence path")
    return {
        "implementationState": implementation_state,
        "gateState": gate_state,
        "currentMetrics": metrics,
        "followup": str(followup).strip(),
        "evidencePath": str(evidence_path).strip(),
    }


def _sector_job_count(payload: Mapping[str, Any], *sector_ids: str) -> int:
    wanted = set(sector_ids)
    count = 0
    for job in payload.get("jobs") or []:
        if isinstance(job, Mapping) and _posting_relevant_sector_ids(job) & wanted:
            count += 1
    return count


def _lane_metric(lane: Mapping[str, Any], key: str) -> int:
    return _int_metric(lane.get(key))


def _graduate_admissions_requirement_metrics(programs: Any) -> dict[str, int]:
    """Count public admissions facts without inferring one person's readiness."""
    records = [item for item in (programs or []) if isinstance(item, Mapping)]
    english_count = 0
    threshold_count = 0
    waiver_count = 0
    transcript_count = 0
    for record in records:
        text = json.dumps(record, ensure_ascii=False).casefold()
        if re.search(r"toefl|ielts|teps|english|영어", text):
            english_count += 1
        if re.search(r"(?:toefl|ielts|teps)[^0-9]{0,30}[0-9]", text):
            threshold_count += 1
        if re.search(r"waiv(?:e|er)|면제", text):
            waiver_count += 1
        if re.search(r"transcript|gpa|성적증명|학점", text):
            transcript_count += 1
    return {
        "programs": len(records),
        "englishEvidence": english_count,
        "numericThreshold": threshold_count,
        "waiverEvidence": waiver_count,
        "transcriptGpaEvidence": transcript_count,
    }


def _canonical_job_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except ValueError:
        return ""
    if parts.scheme.casefold() not in {"http", "https"} or not parts.netloc:
        return ""
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), path, "", ""))


def _decision_readiness_boundary(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Keep exploration inventory separate from items safe to act on."""
    jobs = [job for job in (payload.get("jobs") or []) if isinstance(job, Mapping)]
    verified_open = [
        job
        for job in jobs
        if str(_mapping_at(job, "postingCurrentness").get("status") or "unverified") == "verified_open"
    ]
    apply_ready = [
        job
        for job in verified_open
        if str(job.get("queue") or job.get("actionQueue") or "").casefold() == "apply"
    ]
    if not verified_open:
        state = "exploration_only"
        label = "공식 원문에서 현재 접수 중임이 확인된 행동 후보가 없어 탐색 후보만 표시합니다."
    elif not apply_ready:
        state = "verification_required"
        label = "공식 원문 확인 항목은 있으나 지원 준비 게이트가 남아 있습니다."
    else:
        state = "apply_ready_present"
        label = "공식 원문과 지원 게이트를 통과한 행동 후보가 있습니다."
    return {
        # data-requirement-id="DATA-301": verified-open proof is the public action boundary.
        "state": state,
        "label": label,
        "publishedCount": len(jobs),
        "verifiedOpenCount": len(verified_open),
        "applyReadyCount": len(apply_ready),
    }


def _framework_operational_states(
    payload: Mapping[str, Any],
    stats: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    jobs_count = _int_metric(stats.get("jobs", len(payload.get("jobs") or [])))
    programs_count = _int_metric(stats.get("programs", len(payload.get("programs") or [])))
    funding_count = _int_metric(stats.get("funding", len(payload.get("funding") or [])))
    queue_counts = _mapping_at(stats, "queueCounts")
    market_counts = _mapping_at(stats, "marketCounts")
    preference_summary = _mapping_at(stats, "preferenceSummary")
    preference_discovery = _mapping_at(stats, "preferenceDiscovery")
    lifestyle = _mapping_at(payload, "lifestyleDiscovery")
    candidate_filter = _mapping_at(lifestyle, "candidateFilter")
    lanes = _mapping_at(lifestyle, "lanes")
    jayang_lane = _mapping_at(lanes, "jayang_wlb")
    busan_lane = _mapping_at(lanes, "busan")
    framework_sources = _mapping_at(payload, "decisionFrameworkSources")
    funding_strategy = _mapping_at(framework_sources, "funding_strategy")
    application_packaging = _mapping_at(framework_sources, "application_packaging")
    source_quality = _mapping_at(framework_sources, "source_quality")
    research_frontier = _mapping_at(framework_sources, "research_frontier")
    jobs = [job for job in (payload.get("jobs") or []) if isinstance(job, Mapping)]
    admissions = _graduate_admissions_requirement_metrics(payload.get("programs"))
    currentness_counts = {"verified_open": 0, "verified_closed": 0, "unverified": 0}
    for job in jobs:
        status = str(_mapping_at(job, "postingCurrentness").get("status") or "unverified")
        currentness_counts[status if status in currentness_counts else "unverified"] += 1
    job_identity_values = [str(job.get("id") or job.get("jobId") or "").strip() for job in jobs]
    identity_complete = all(job_identity_values)
    unique_job_ids = len(set(job_identity_values))
    identity_unique = identity_complete and unique_job_ids == len(job_identity_values)
    canonical_job_urls = [_canonical_job_url(job.get("url")) for job in jobs]
    canonical_url_complete = sum(bool(url) for url in canonical_job_urls)
    duplicate_canonical_url_count = len([url for url in canonical_job_urls if url]) - len(
        {url for url in canonical_job_urls if url}
    )
    source_lineage_complete = sum(
        bool(str(job.get("sourceKey") or "").strip())
        and bool(str(job.get("sourceLabel") or "").strip())
        for job in jobs
    )
    provenance_complete = bool(jobs) and all(
        (
            identity_unique,
            canonical_url_complete == len(jobs),
            duplicate_canonical_url_count == 0,
            source_lineage_complete == len(jobs),
        )
    )
    decision_support_count = sum(bool(_mapping_at(job, "decisionSupport")) for job in jobs)
    lifestyle_state = "connected" if lifestyle else "planned"
    lifestyle_gate = "review" if lifestyle else "hold"
    feedback_runtime_metrics = [
        "authenticated runtime preference rows are hidden from public snapshot",
        f"public preference digest present={bool(preference_summary.get('digest'))}",
        f"runtime discovery current={bool(preference_discovery.get('current'))}",
    ]

    return {
        "water_hydrology": _framework_state(
            "connected",
            "review",
            [f"published jobs={jobs_count}", f"water-sector jobs={_sector_job_count(payload, 'water_resources', 'hydrology', 'flood')}"],
            "Deepen official-source role extraction for water and hydrology matches.",
            "stats.jobs + jobs[].relevantSectors",
        ),
        "climate_env_ai": _framework_state(
            "connected",
            "review",
            [f"published jobs={jobs_count}", f"climate/env AI tagged jobs={_sector_job_count(payload, 'climate_ai', 'environmental_ai', 'ai_data')}"],
            "Separate real data/model work from AI-title decoration in each posting.",
            "jobs[].relevantSectors + jobs[].decisionSupport",
        ),
        "gis_remote_sensing": _framework_state(
            "connected",
            "review",
            [f"published jobs={jobs_count}", f"GIS/remote sensing tagged jobs={_sector_job_count(payload, 'gis', 'remote_sensing', 'spatial_information')}"],
            "Keep tool and deliverable evidence visible before ranking GIS roles.",
            "jobs[].relevantSectors + jobs[].decisionSupport",
        ),
        "oda_policy_pm": _framework_state(
            "connected",
            "review",
            [f"published jobs={jobs_count}", f"ODA/policy/PM tagged jobs={_sector_job_count(payload, 'oda', 'policy_pm', 'international_development')}"],
            "Recheck contract terms and field-city risk before promotion.",
            "jobs[].relevantSectors + jobs[].decisionSupport",
        ),
        "domestic_wlb": _framework_state(
            "partial",
            "review",
            [
                f"domestic jobs={_int_metric(market_counts.get('domestic'))}",
                f"overseas jobs={_int_metric(market_counts.get('overseas'))}",
                f"lifestyle candidates={_int_metric(lifestyle.get('publicCandidateCount'))}",
            ],
            "Use domestic/overseas only as a lane split; keep region out of scoring until city evidence is defensible.",
            "stats.marketCounts + lifestyleDiscovery.candidateFilter",
        ),
        "research_frontier": _framework_state(
            "connected" if research_frontier.get("available") else "planned",
            "review" if research_frontier.get("available") else "hold",
            [
                f"research topics={_int_metric(research_frontier.get('count'))}",
                f"strategy lanes={len(_mapping_at(research_frontier, 'strategyFitCounts'))}",
                "artifact date is lineage only, not posting proof",
            ],
            "Revalidate useful research themes against current official jobs, projects, or faculty pages before action.",
            str(research_frontier.get("path") or "unconnected research-frontier artifact"),
        ),
        "supervisor_fit": _framework_state(
            "partial",
            "review",
            [f"faculty evidence={_int_metric(coverage.get('programsWithFaculty'))}/{_int_metric(coverage.get('totalPrograms', programs_count))}"],
            "Fill missing faculty/lab pages before making fit conclusions.",
            "graduateEvidenceCoverage.programsWithFaculty",
        ),
        "papers": _framework_state(
            "partial",
            "review",
            [f"recent-paper evidence={_int_metric(coverage.get('programsWithRecentPapers'))}/{_int_metric(coverage.get('totalPrograms', programs_count))}"],
            "Collect current-five-year paper titles with public links for uncovered programs.",
            "graduateEvidenceCoverage.programsWithRecentPapers",
        ),
        "funded_projects": _framework_state(
            "partial",
            "review",
            [f"funded-project evidence={_int_metric(coverage.get('programsWithFundedProjects'))}/{_int_metric(coverage.get('totalPrograms', programs_count))}"],
            "Keep amount and sponsor blank unless the public project source supports them.",
            "graduateEvidenceCoverage.programsWithFundedProjects",
        ),
        "alumni_outcomes": _framework_state(
            "partial",
            "review",
            [
                f"destination evidence={_int_metric(coverage.get('programsWithGraduateDestinations'))}/{_int_metric(coverage.get('totalPrograms', programs_count))}",
                f"testimonial evidence={_int_metric(coverage.get('programsWithTestimonials'))}/{_int_metric(coverage.get('totalPrograms', programs_count))}",
            ],
            "Show destination types only from public alumni, lab, LinkedIn, or review evidence.",
            "graduateEvidenceCoverage.programsWithGraduateDestinations",
        ),
        "lab_life": _framework_state(
            "partial",
            "review",
            [f"funding records={funding_count}", f"unresearched programs={_int_metric(coverage.get('unresearchedPrograms'))}"],
            "Separate official funding facts from student-review life signals.",
            "stats.funding + graduateEvidenceCoverage.unresearchedPrograms",
        ),
        "funding_strategy": _framework_state(
            "connected" if funding_strategy.get("available") else "planned",
            "review" if funding_strategy.get("available") else "hold",
            [
                f"funding opportunities={_int_metric(funding_strategy.get('count'))}",
                f"artifact generated={funding_strategy.get('artifactGeneratedAt') or 'unknown'}",
                "artifact date is lineage only, not posting proof",
            ],
            "Check each funding route against the current official call, eligibility, deadline, and program fit.",
            str(funding_strategy.get("path") or "unconnected funding-strategy artifact"),
        ),
        "toefl_transcript_readiness": _framework_state(
            "partial",
            "review",
            [
                # data-requirement-id="DATA-299": admissions facts are public;
                # private readiness is not serialized.
                f"programs={admissions['programs']}",
                f"English evidence={admissions['englishEvidence']}",
                f"numeric threshold={admissions['numericThreshold']}",
                f"waiver evidence={admissions['waiverEvidence']}",
                f"transcript/GPA evidence={admissions['transcriptGpaEvidence']}",
                "private readiness is not serialized",
            ],
            "Collect official TOEFL/IELTS, waiver, transcript, GPA, and deadline rules without judging a named applicant.",
            "programs[].english + programs[].englishCriteria + public admissions requirements",
        ),
        "jayang_commute": _framework_state(
            lifestyle_state,
            lifestyle_gate,
            [
                f"matched candidates={_lane_metric(jayang_lane, 'matchedCount')}",
                f"verified open={_int_metric(_mapping_at(jayang_lane, 'classCounts').get('verifiedOpen'))}",
                f"decision readiness={jayang_lane.get('decisionReadiness', 'missing')}",
            ],
            "Verify exact office address, commute time, and actual WLB before treating the lane as ready.",
            "lifestyleDiscovery.lanes.jayang_wlb",
        ),
        "busan_lane": _framework_state(
            lifestyle_state,
            lifestyle_gate,
            [
                f"matched candidates={_lane_metric(busan_lane, 'matchedCount')}",
                f"verified open={_int_metric(_mapping_at(busan_lane, 'classCounts').get('verifiedOpen'))}",
                f"decision readiness={busan_lane.get('decisionReadiness', 'missing')}",
            ],
            "Keep Busan separate from broad Yeongnam location text until strict address evidence is present.",
            "lifestyleDiscovery.lanes.busan",
        ),
        "city_safety_quality": _framework_state(
            "planned",
            "hold",
            ["city KPI is intentionally excluded from score", f"overseas jobs for later city review={_int_metric(market_counts.get('overseas'))}"],
            "Define a city-level safety/life evidence source before any overseas-city promotion.",
            "stats.marketCounts.overseas",
        ),
        "structured_reasons": _framework_state("runtime_only", "runtime", feedback_runtime_metrics, "Collect scoreable reason codes in authenticated Supabase runtime.", "Supabase runtime feedback tables"),
        "all_rows_compare": _framework_state("runtime_only", "runtime", feedback_runtime_metrics, "Compare every authenticated preference row at refresh time without fixed top-N limits.", "Supabase runtime feedback tables"),
        "negative_learning": _framework_state("runtime_only", "runtime", feedback_runtime_metrics, "Convert repeated negative reason codes into gates only after authenticated runtime comparison.", "Supabase runtime feedback tables"),
        "official_jobs": _framework_state(
            "partial",
            "review",
            [f"published jobs={jobs_count}", f"source-review candidates={_int_metric(stats.get('sourceReviewCandidates'))}", f"excluded unverified={_int_metric(stats.get('excludedUnverifiedCandidates'))}"],
            "Correct source labels at catalog level and recheck official URLs before source-of-truth claims.",
            "stats.sourceReviewCandidates + stats.excludedUnverifiedCandidates",
        ),
        "community_leads": _framework_state(
            "planned",
            "hold",
            ["community leads are discovery-only", f"source-review candidates={_int_metric(stats.get('sourceReviewCandidates'))}"],
            "Use community posts only as leads and require an official posting URL before publication.",
            "source catalog review queue",
        ),
        "alumni_public": _framework_state(
            "partial",
            "review",
            [f"destination evidence={_int_metric(coverage.get('programsWithGraduateDestinations'))}", f"testimonials={_int_metric(coverage.get('programsWithTestimonials'))}"],
            "Keep only public destination types and avoid private-person inference.",
            "graduateEvidenceCoverage + program.researchEvidence",
        ),
        "source_quality": _framework_state(
            "connected" if source_quality.get("available") else "planned",
            "review" if source_quality.get("available") else "hold",
            [
                f"reviewed sources={_int_metric(source_quality.get('sourceCount'))}",
                f"covered jobs={_int_metric(source_quality.get('jobCount'))}",
                "artifact date is lineage only, not posting proof",
            ],
            "Use source quality to order rechecks, never to infer that an individual posting is still open.",
            str(source_quality.get("path") or "unconnected source-quality artifact"),
        ),
        "producer_consumer": _framework_state(
            "connected",
            "pass",
            ["producer=scripts/build_snapshot.py", "output=data/app-data.json", "consumer=app.js decisionFrameworkPanel"],
            "After artifact regeneration, verify generatedFrom still names the same producer/output/consumer path.",
            "decisionFramework.generatedFrom",
        ),
        "phase_gate_loop": _framework_state(
            "connected",
            "pass",
            [
                "required domain IDs are present",
                "required decision questions are present and unique",
                "each subfield has process/gate/loop/state",
            ],
            "Keep new decision areas behind explicit PROCESS, GATE, LOOP and measurable state.",
            "decisionFramework.domains[].subfields[]",
        ),
        "mobile_release": _framework_state(
            "partial",
            "hold",
            ["public snapshot updated by build only", "iPhone cache remains a release verification gate"],
            "After parent regenerates and releases, verify the iPhone Sources panel reads decision-framework-v3.",
            "sw.js cache + iPhone runtime screen",
        ),
        "eligibility_hard_gates": _framework_state(
            "partial",
            "review",
            [f"action candidates={_int_metric(stats.get('actionCandidates'))}", f"experience exclusions={_int_metric(stats.get('excludedExperienceCandidates'))}", f"unverified exclusions={_int_metric(stats.get('excludedUnverifiedCandidates'))}"],
            "Turn eligibility, citizenship, degree, language, and experience misses into explicit hard-gate fields.",
            "stats.actionCandidates + stats.excludedExperienceCandidates",
        ),
        "timing_documents": _framework_state(
            "partial",
            "review",
            [f"apply queue={_int_metric(queue_counts.get('apply'))}", f"verify queue={_int_metric(queue_counts.get('verify'))}", f"hold queue={_int_metric(queue_counts.get('hold'))}"],
            "Track deadline, resume, transcript, recommendation, portfolio, and visa-document readiness per item.",
            "stats.queueCounts",
        ),
        "application_packaging": _framework_state(
            "connected" if application_packaging.get("available") else "planned",
            "review" if application_packaging.get("available") else "hold",
            [
                f"application candidates={_int_metric(application_packaging.get('count'))}",
                f"artifact generated={application_packaging.get('artifactGeneratedAt') or 'unknown'}",
                "artifact date is lineage only, not posting proof",
            ],
            "Recheck the official deadline and required materials before turning a prepared package into an apply action.",
            str(application_packaging.get("path") or "unconnected application-packaging artifact"),
        ),
        "compensation_contract": _framework_state(
            "planned",
            "hold",
            [f"funding records={funding_count}", "job compensation contract fields are not yet normalized"],
            "Normalize salary, stipend, contract length, renewal, insurance, and relocation before decision scoring.",
            "funding[] + future job compensation fields",
        ),
        "skill_gap_bridge": _framework_state(
            "planned",
            "hold",
            ["skill-gap evidence is not yet connected", f"sector inventory={_int_metric(stats.get('sectorInventoryCount'))}"],
            "Map required tools/methods to current portfolio evidence and a bridge plan.",
            "future skill inventory + sectors",
        ),
        "salary_living_cost": _framework_state(
            "planned",
            "hold",
            ["salary/cost KPI is intentionally not scored yet", "city-level cost source required"],
            "Add reliable salary, stipend, rent, tax, insurance, and commute-cost evidence before comparison.",
            "future compensation and living-cost evidence",
        ),
        "opportunity_cost": _framework_state(
            "planned",
            "hold",
            ["opportunity-cost model not connected", f"programs={programs_count}", f"published jobs={jobs_count}"],
            "Compare time-to-degree, application effort, career delay, and fallback value after hard-gate readiness.",
            "future decision-economics model",
        ),
        "evidence_confidence": _framework_state(
            "connected",
            "review",
            [f"jobs={jobs_count}", f"programs={programs_count}", f"programs with any evidence={_int_metric(coverage.get('programsWithAnyEvidence'))}", f"lifestyle source postings={_int_metric(lifestyle.get('sourcePostingCount'))}"],
            "Show confidence from source coverage and leave weak areas as visible blanks.",
            "stats + graduateEvidenceCoverage + lifestyleDiscovery",
        ),
        "portfolio_balance": _framework_state(
            "connected",
            "review",
            [f"action jobs={_int_metric(stats.get('actionCandidates'))}", f"explore jobs={_int_metric(stats.get('explorationCandidates'))}", f"programs={programs_count}", f"funding={funding_count}"],
            "Balance near-term jobs, graduate programs, funding, and lifestyle lanes instead of overfitting one source.",
            "stats.actionCandidates + stats.explorationCandidates + stats.programs + stats.funding",
        ),
        "work_substance": _framework_state(
            "partial",
            "review",
            [f"jobs with decision support={decision_support_count}/{len(jobs)}", "task evidence must come from posting text"],
            "Extract daily tasks, deliverables, fieldwork, analysis, and administrative share before calling the role a fit.",
            "jobs[].decisionSupport",
        ),
        "skill_compounding": _framework_state(
            "planned",
            "hold",
            ["skill accumulation model not connected", f"published jobs available for later mapping={len(jobs)}"],
            "Map tools, methods, outputs, and portfolio evidence to a reusable skill graph before scoring growth.",
            "future skill-capital artifact",
        ),
        "exit_options": _framework_state(
            "planned",
            "hold",
            ["next-role and graduate-path outcomes are not connected", f"program destination evidence={_int_metric(coverage.get('programsWithGraduateDestinations'))}"],
            "Collect public transition evidence and name realistic next roles without inferring private careers.",
            "future career-transition artifact + graduateEvidenceCoverage",
        ),
        "stability_contract": _framework_state(
            "partial",
            "review",
            ["employment and compensation fields are not uniformly normalized", f"funding records={funding_count}"],
            "Normalize permanent, fixed-term, renewal, probation, benefits, and relocation terms from official text.",
            "jobs[].decisionSupport + funding[]",
        ),
        "manager_team": _framework_state(
            "planned",
            "hold",
            ["manager and team evidence not connected", "public team pages cannot prove day-to-day management quality"],
            "Collect public team structure and interview questions while keeping private-person inference out of the app.",
            "future organization-reality artifact",
        ),
        "culture_workload": _framework_state(
            lifestyle_state,
            lifestyle_gate,
            [
                f"lifestyle review candidates={_int_metric(lifestyle.get('publicCandidateCount'))}",
                f"verified open candidates={_int_metric(lifestyle.get('verifiedOpenCount'))}",
                "WLB claims remain unknown without hours, duty, travel, or review evidence",
            ],
            "Verify workload facts and label official claims separately from public reviews before promotion.",
            "lifestyleDiscovery.items[].lifestyleEvidence.axes.wlb",
        ),
        "priority_actionability": _framework_state(
            "partial",
            "review",
            [
                f"apply queue={_int_metric(queue_counts.get('apply'))}",
                f"verify queue={_int_metric(queue_counts.get('verify'))}",
                f"hold queue={_int_metric(queue_counts.get('hold'))}",
            ],
            "Order actions only after currentness, eligibility, deadline, and material readiness gates are visible.",
            "stats.queueCounts",
        ),
        "materials_readiness": _framework_state(
            "connected" if application_packaging.get("available") else "planned",
            "review" if application_packaging.get("available") else "hold",
            [
                f"prepared application candidates={_int_metric(application_packaging.get('count'))}",
                "materials readiness does not prove the posting is open",
            ],
            "Bind each resume, transcript, reference, and portfolio checklist to a currently verified target.",
            str(application_packaging.get("path") or "unconnected application-packaging artifact"),
        ),
        "interview_feedback": _framework_state(
            "runtime_only",
            "runtime",
            ["interview outcomes are private runtime evidence", "public snapshot publishes no personal outcome counts"],
            "Capture stage, question theme, outcome, and learning privately, then expose only safe aggregate actions.",
            "future authenticated interview feedback runtime",
        ),
        "posting_currentness": _framework_state(
            "connected" if jobs else "planned",
            "review" if currentness_counts["unverified"] else "pass",
            [
                f"verified open={currentness_counts['verified_open']}",
                f"verified closed={currentness_counts['verified_closed']}",
                f"unverified={currentness_counts['unverified']}",
            ],
            "Recheck unverified or stale items at the official posting before any apply action.",
            "jobs[].postingCurrentness",
        ),
        "provenance_dedup": _framework_state(
            "connected" if provenance_complete else "partial",
            "pass" if provenance_complete else "review",
            [
                # data-requirement-id="GOV-300": identity alone is insufficient.
                f"published jobs={len(jobs)}",
                f"unique nonblank job IDs={unique_job_ids}",
                f"identity complete={identity_complete}",
                f"canonical URL complete={canonical_url_complete}/{len(jobs)}",
                f"duplicate canonical URLs={duplicate_canonical_url_count}",
                f"duplicateCanonicalUrlCount={duplicate_canonical_url_count}",
                f"source lineage complete={source_lineage_complete}/{len(jobs)}",
                f"sourceLineageComplete={source_lineage_complete}/{len(jobs)}",
            ],
            "Repair missing or duplicate identities and preserve official-source lineage before publication.",
            "jobs[].id + jobs[].url + jobs[].sourceKey/sourceLabel",
        ),
        "reversibility_red_flags": _framework_state(
            "planned",
            "hold",
            [
                "lock-in and recovery-cost evidence is not normalized",
                "location and prestige cannot compensate for an irreversible risk",
            ],
            "Collect probation, repayment, relocation, visa, funding-loss, and career-lock-in facts before promoting high-cost choices.",
            "future reversibility-risk artifact",
        ),
    }


def _framework_domains(
    payload: Mapping[str, Any],
    stats: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> list[dict[str, Any]]:
    sf = _framework_subfield
    domains: list[dict[str, Any]] = []
    career: list[dict[str, Any]] = []
    career.append(sf("water_hydrology", "Water resources / hydrology / flood", "River, flood, hydrologic model, public water agency and engineering roles.", "Extract role evidence from the official posting body.", "If water-role evidence is absent, keep it as a lead only.", "Promote matched liked keywords into the next search set.", ["official posting", "role description", "deadline"]))
    career.append(sf("climate_env_ai", "Climate and environmental AI", "Climate data, environmental prediction, AI/data modelling and remote sensing roles.", "Check whether AI is real work or title decoration.", "Do not classify as AI without data or model work.", "Expand queries from liked AI work phrases.", ["model work", "tools", "data type"]))
    career.append(sf("gis_remote_sensing", "GIS / spatial information / remote sensing", "GIS analysis, satellite data, digital twin and public geodata roles.", "Separate tools and deliverables from the posting body.", "Low-priority if it is only clerical GIS.", "Add preferred tools and research experience to matching rules.", ["GIS tools", "spatial data", "deliverable"]))
    career.append(sf("oda_policy_pm", "ODA / policy / PM", "UN, MDB, KOICA and research-institute policy or project-management work.", "Separate institution prestige from the actual assigned work.", "Hold if field safety or living risk is unverified.", "Turn repeated dislikes into risk gates.", ["institution page", "work city", "contract terms"]))
    career.append(sf("domestic_wlb", "Domestic WLB and commute", "Seoul Jayang commute, Busan lane, permanent and contract roles.", "Check commute and work format after role fit.", "Recheck when night, shift, duty or frequent travel is explicit.", "Feed real commute and WLB findings back into filters.", ["workplace", "employment type", "WLB wording"]))
    career.append(sf("research_frontier", "Research frontier", "Emerging water, climate, environmental AI and policy themes that can open future roles or study paths.", "Read the measured topic artifact, then revalidate useful themes against current official sources.", "An old research artifact cannot prove that a posting or funding call is currently open.", "Return validated themes to job, faculty and funding queries with separate currentness checks.", ["topic artifact", "official current source", "validation date"]))
    domains.append(_framework_domain("career", "Career lanes", "job candidates", career))
    graduate: list[dict[str, Any]] = []
    graduate.append(sf("supervisor_fit", "Supervisor and lab fit", "Faculty lab, recent projects and possible supervision field.", "Check department pages and faculty homepages separately.", "No recommendation conclusion when faculty evidence is missing.", "Send matched faculty names into the next research queue.", ["faculty homepage", "lab page", "research keywords"]))
    graduate.append(sf("papers", "Recent papers", "Last-five-year papers, themes and methods.", "Cross-check public databases, CVs and scholar pages.", "Do not score papers with unclear year or authorship.", "Convert paper keywords into subfield tags.", ["last five years", "paper title", "author/link"]))
    graduate.append(sf("funded_projects", "Funded projects", "Amount, sponsor, topic and period for lab execution strength.", "Show amounts only from official public project evidence.", "If amount is unsourced, show type only.", "Leave missing sponsor or amount as the next search task.", ["sponsor", "amount", "period"]))
    graduate.append(sf("alumni_outcomes", "Alumni outcomes", "Public alumni, LinkedIn, lab alumni and review-based destination types.", "Separate personal public info from official school evidence.", "No private inference or personal data hoarding.", "Accumulate verified destination types in program detail.", ["official alumni", "public LinkedIn", "review link"]))
    graduate.append(sf("lab_life", "Lab life and funding reality", "Scholarship, RA/TA, coursework, graduation rules and living cost.", "Separate official tuition/stipend facts from student reviews.", "Reviews alone cannot become confirmed facts.", "Add missing cost and life risks to the question list.", ["tuition", "stipend", "student review"]))
    graduate.append(sf("funding_strategy", "Funding strategy", "Scholarships, assistantships, fellowships and project-funded routes with different eligibility and deadlines.", "Use the measured funding inventory only as a lead, then verify the current official call.", "No funding action when eligibility, amount, duration or deadline is unverified.", "Turn each missing condition into a current-call research task.", ["official call", "eligibility", "amount/duration", "deadline"]))
    graduate.append(sf("toefl_transcript_readiness", "Public admissions requirements", "Official TOEFL, IELTS, waiver, transcript, GPA, and deadline requirements for each programme.", "Extract only public programme requirements and their source lineage.", "Do not publish or infer a named applicant's readiness, certificate history, GPA, or transcript.", "Return missing public admissions facts to the official programme source queue.", ["English threshold", "waiver rule", "transcript/GPA rule", "official source"]))
    domains.append(_framework_domain("graduate", "Graduate school decision", f"programs {stats.get('programs', len(payload.get('programs') or []))}, faculty evidence {coverage.get('programsWithFaculty', 0)}", graduate))
    lifestyle: list[dict[str, Any]] = []
    lifestyle.append(sf("jayang_commute", "Seoul Jayang commute", "Commute time, transfers and remote-work possibility.", "Classify commute only after workplace and work format are known.", "Unknown address cannot become commute-fit.", "Feed real commute checks into the next filter.", ["workplace", "station access", "remote option"]))
    lifestyle.append(sf("busan_lane", "Busan lane", "Busan living fit and institution stability.", "Separate Busan workplace evidence from broad regional text.", "Do not misclassify non-Busan Yeongnam roles as Busan.", "Accumulate Busan reactions in a separate lane.", ["Busan address", "employment type", "living conditions"]))
    lifestyle.append(sf("city_safety_quality", "City safety and quality", "For overseas roles, judge city-level safety, hygiene and cost of living.", "Use city evidence, not country stereotypes.", "Hold risky cities instead of compensating with score.", "Promote only approved cities into preference filters.", ["city", "safety signal", "life review"], "review"))
    domains.append(_framework_domain("lifestyle", "Lifestyle and city risk", "commute and city gates", lifestyle))
    feedback: list[dict[str, Any]] = []
    feedback.append(sf("structured_reasons", "Structured reasons", "Collect like/dislike reasons as scoreable categories.", "Store reason codes before scoring.", "Free notes alone do not affect score.", "Promote repeated reasons into gate questions.", ["reason code", "note", "job id"]))
    feedback.append(sf("all_rows_compare", "All feedback rows", "Compare every like and dislike, whether there are 2 or 100.", "Aggregate all rows, not a fixed top-N.", "Zero-signal rows must be visible as no influence.", "Show influential and zero rows separately.", ["compared count", "influential count", "zero-signal count"]))
    feedback.append(sf("negative_learning", "Negative learning", "Separate dislike reasons into hard gates and soft penalties.", "Store repeated dislike reasons as risks.", "Do not turn one emotional note into a permanent ban.", "Remove only repeated avoid conditions from search queries.", ["dislike reason", "repeat count", "exception"]))
    domains.append(_framework_domain("feedback", "Feedback learning", "structured preference loop", feedback))
    reliability: list[dict[str, Any]] = []
    reliability.append(sf("official_jobs", "Official job sources", "Use Employment24, institution pages and company career pages as source of truth.", "Store source name and original URL separately.", "Hold display if source lineage is wrong.", "Send bad source labels into the catalog-fix queue.", ["source name", "original URL", "collected at"]))
    reliability.append(sf("community_leads", "Community leads", "Use cafes and communities as discovery leads only.", "Extract candidate URLs read-only after user login.", "Do not create confirmed postings from unofficial posts only.", "Recheck repeated community leads against official pages.", ["post URL", "official source", "duplicate status"]))
    reliability.append(sf("alumni_public", "Public alumni evidence", "Use LinkedIn, lab alumni and reviews only within public evidence boundaries.", "Store public link and destination type, not private personal detail.", "No private inference or excessive scraping.", "Show only verified destination types in graduate detail.", ["public link", "destination type", "verified date"]))
    reliability.append(sf("source_quality", "Source quality", "Measure source coverage and quality without confusing artifact freshness with posting currentness.", "Use the source-quality artifact to prioritize official-source rechecks.", "A high source score cannot turn an unverified posting into an open one.", "Send low-quality or stale sources to the recheck queue and retain lineage.", ["source inventory", "quality signal", "official recheck"]))
    domains.append(_framework_domain("reliability", "Source reliability", "official facts vs leads", reliability))
    execution: list[dict[str, Any]] = []
    execution.append(sf("producer_consumer", "Producer and consumer path", "build_snapshot writes data/app-data.json and app.js reads that payload.", "Expose producer, outputPath and consumer in the payload.", "Data made in another file does not count as done.", "Verify generatedFrom after every snapshot build.", ["producer", "outputPath", "consumer"]))
    execution.append(sf("phase_gate_loop", "PROCESS / GATE / LOOP", "Every subfield carries process, gate and loop text.", "Each subfield must state PROCESS, GATE and LOOP.", "Expansion without a gate stays in review.", "Return blanks and risks to the next collection loop.", ["PROCESS", "GATE", "LOOP"]))
    execution.append(sf("mobile_release", "iPhone release path", "Advance the service-worker cache and verify the mobile shell sees the panel.", "App-shell cache key must change with this screen.", "Stale cache remains a release risk until checked on iPhone.", "After release, refresh on iPhone and inspect Sources.", ["cache key", "reqgate", "mobile screen"]))
    domains.append(_framework_domain("execution", "Execution connectivity", "same generated and read file", execution))
    feasibility: list[dict[str, Any]] = []
    feasibility.append(sf("eligibility_hard_gates", "Eligibility hard gates", "Citizenship, degree, language, years of experience, license, visa and location eligibility.", "Extract hard requirements into explicit fields before ranking.", "Fail closed when a hard gate is unknown and material.", "Return missing eligibility facts to the next source check.", ["citizenship", "degree", "experience", "visa"]))
    feasibility.append(sf("timing_documents", "Timing and documents", "Deadline, start date, transcript, references, portfolio and application-material readiness.", "Check timing and documents after role fit but before promotion.", "Hold items that cannot be acted on before the deadline.", "Convert missing documents into a preparation task list.", ["deadline", "start date", "required documents"]))
    feasibility.append(sf("compensation_contract", "Compensation and contract", "Salary, stipend, contract duration, renewal, insurance, relocation and work conditions.", "Normalize compensation and contract terms separately from prestige.", "Do not score compensation when amount or contract basis is missing.", "Add compensation gaps to the collection queue.", ["salary/stipend", "contract term", "benefits"]))
    feasibility.append(sf("skill_gap_bridge", "Skill gap bridge", "Required methods, tools, credentials and portfolio evidence with a bridge plan.", "Map every major requirement to current evidence or a learning action.", "A missing critical skill stays a gap, not a soft preference.", "Use repeated skill gaps to shape study and portfolio tasks.", ["required skill", "current evidence", "bridge plan"]))
    feasibility.append(sf("application_packaging", "Application packaging", "Resume, cover letter, transcript, references and portfolio packages prepared for specific targets.", "Read the measured application artifact and bind each package to a currently verified target.", "Prepared documents do not prove that a posting is open or that eligibility is met.", "Return expired, unbound or incomplete packages to target verification and materials preparation.", ["target binding", "materials checklist", "current deadline"]))
    domains.append(_framework_domain("application_feasibility", "Application feasibility", "eligibility, timing, compensation and skill gates", feasibility))
    economics: list[dict[str, Any]] = []
    economics.append(sf("salary_living_cost", "Salary and living cost", "Net salary or stipend, rent, tax, insurance, transport and city cost burden.", "Compare money only from reliable salary and cost evidence.", "No region bonus until city-level evidence is credible.", "Collect salary/cost sources before ranking by economics.", ["salary/stipend", "rent/cost", "tax/insurance"]))
    economics.append(sf("opportunity_cost", "Opportunity cost", "Time-to-degree, application effort, career delay, alternative job value and risk of lock-in.", "Compare each path against the best realistic alternative.", "Do not hide multi-year cost behind a high-fit label.", "Add missing cost-of-delay facts to decision review.", ["duration", "application effort", "fallback option"]))
    economics.append(sf("evidence_confidence", "Evidence confidence", "How much of the decision is supported by official, public, current, and connected evidence.", "Show confidence from coverage rather than score inflation.", "Weak evidence stays visible as a blank or review flag.", "Target the lowest-confidence high-impact blanks first.", ["source coverage", "verified date", "missing axis"]))
    economics.append(sf("portfolio_balance", "Portfolio balance", "Mix of near-term jobs, graduate options, funding paths, local lifestyle candidates and long-term bets.", "Keep lanes balanced so one source does not dominate decisions.", "Do not overfit to today's small set of visible items.", "Rebalance after each feedback and collection refresh.", ["jobs", "programs", "funding", "lifestyle lanes"]))
    domains.append(_framework_domain("decision_economics", "Decision economics", "cost, confidence and portfolio balance", economics))
    career_capital: list[dict[str, Any]] = []
    career_capital.append(sf("work_substance", "Work substance", "Daily tasks, outputs, analysis, fieldwork, coordination and administrative share.", "Extract concrete task and deliverable evidence from the official posting.", "A prestigious title without substantive work evidence stays in review.", "Ask for missing task evidence and refine role-fit queries from validated work phrases.", ["daily tasks", "deliverables", "work mix"]))
    career_capital.append(sf("skill_compounding", "Skill compounding", "Tools, methods, domain knowledge and portfolio outputs that remain valuable after this role.", "Map each substantive task to a reusable skill and demonstrable output.", "Do not score growth from generic training or mission language alone.", "Feed recurring gaps into a learning and portfolio plan.", ["tool/method", "reusable skill", "portfolio output"]))
    career_capital.append(sf("exit_options", "Exit options", "Realistic next roles, graduate routes and sector transitions supported by public outcome evidence.", "Collect public transition types without inferring private career histories.", "Unknown outcomes remain unknown rather than becoming a prestige proxy.", "Use confirmed transitions to refine a reversible next-step portfolio.", ["next-role type", "public outcome source", "fallback path"]))
    domains.append(_framework_domain("career_capital", "Career capital", "work substance, compounding skills and exit options", career_capital))
    organizational_reality: list[dict[str, Any]] = []
    organizational_reality.append(sf("stability_contract", "Stability and contract", "Employment type, duration, renewal, probation, benefits, relocation and repayment conditions.", "Normalize official contract facts before comparing organizations.", "Missing material terms block stability conclusions.", "Return contract gaps to official-source review or interview questions.", ["employment type", "term/renewal", "benefits/conditions"]))
    organizational_reality.append(sf("manager_team", "Manager and team", "Reporting line, team mandate, collaboration structure and public evidence about how work is organized.", "Separate public structure facts from private-person inference and interview hypotheses.", "A team page cannot prove management quality.", "Convert unknowns into respectful interview questions and post-interview notes.", ["team page", "reporting structure", "interview question"]))
    organizational_reality.append(sf("culture_workload", "Culture and workload", "Hours, duty, travel, flexibility, review signals and conflicts between official claims and lived reports.", "Label official policy, public review and inference separately.", "Unknown workload cannot become a WLB recommendation.", "Recheck high-impact contradictions and capture confirmed interview evidence privately.", ["hours/duty", "travel/flexibility", "evidence class"]))
    domains.append(_framework_domain("organizational_reality", "Organizational reality", "contract, team and workload evidence", organizational_reality))
    application_pipeline: list[dict[str, Any]] = []
    application_pipeline.append(sf("priority_actionability", "Priority and actionability", "Whether the next safe action is apply, verify, prepare, compare, hold or exclude.", "Order actions only after currentness, eligibility, deadline and material-readiness gates.", "A high fit score cannot bypass an unmet hard gate.", "Send each failed gate to one named verification or preparation task.", ["current state", "blocking gate", "next action"]))
    application_pipeline.append(sf("materials_readiness", "Materials readiness", "Target-bound resume, cover letter, transcript, reference and portfolio completion.", "Bind materials to one verified target and checklist.", "Generic or stale materials remain preparation, not apply-ready.", "Update only the missing target-specific evidence in the next loop.", ["target", "required material", "completion evidence"]))
    application_pipeline.append(sf("interview_feedback", "Interview feedback", "Private stage outcomes, question themes, gaps and lessons that improve the next application.", "Capture structured private evidence after each stage.", "Do not publish personal outcomes or silently turn one result into a permanent rule.", "Aggregate repeated lessons into questions, materials and skill actions.", ["stage", "question theme", "learning/action"]))
    domains.append(_framework_domain("application_pipeline", "Application pipeline", "priority, materials and interview learning", application_pipeline))
    uncertainty_risk: list[dict[str, Any]] = []
    uncertainty_risk.append(sf("posting_currentness", "Posting currentness", "Open, closed or unverified status checked against the official posting.", "Separate posting verification time from artifact generation time.", "Unverified or closed items cannot become apply actions.", "Recheck only the highest-value unverified items and retain the result.", ["official URL", "status", "verified at"]))
    uncertainty_risk.append(sf("provenance_dedup", "Provenance and deduplication", "Stable identity, official-source lineage and duplicate control across collectors and snapshots.", "Require a nonblank unique job ID and preserve source identity through generation and consumption.", "Missing or duplicate identity blocks publication as a distinct item.", "Repair the producer path and rerun the same identity gate.", ["job ID", "source identity", "duplicate decision"]))
    uncertainty_risk.append(sf("reversibility_red_flags", "Reversibility and red flags", "Lock-in, visa/funding loss, repayment, relocation and other costs that are hard to reverse.", "Collect explicit downside and recovery-cost facts before a high-cost decision.", "Do not offset a material red flag with prestige, location or a soft score.", "Hold the option, research the missing downside, and keep a fallback path.", ["red flag", "recovery cost", "fallback path"]))
    domains.append(_framework_domain("uncertainty_risk", "Uncertainty and downside risk", "currentness, provenance and reversibility", uncertainty_risk))
    operational_states = _framework_operational_states(payload, stats, coverage)
    domain_ids = [str(domain.get("id") or "") for domain in domains]
    if len(domain_ids) != len(set(domain_ids)):
        raise ValueError("duplicate framework domain id")
    missing_domains = REQUIRED_FRAMEWORK_DOMAIN_IDS - set(domain_ids)
    if missing_domains:
        raise ValueError(f"missing required framework domains: {sorted(missing_domains)}")
    seen: set[str] = set()
    for domain in domains:
        for subfield in domain["subfields"]:
            subfield_id = str(subfield.get("id"))
            if subfield_id in seen:
                raise ValueError(f"duplicate framework subfield id: {subfield_id}")
            seen.add(subfield_id)
            state = operational_states.get(subfield_id)
            if state is None:
                raise ValueError(f"missing framework operational state: {subfield_id}")
            subfield.update(state)
    missing_subfields = REQUIRED_FRAMEWORK_SUBFIELD_IDS - seen
    if missing_subfields:
        raise ValueError(f"missing required framework subfields: {sorted(missing_subfields)}")
    return domains


def _review_protocol(payload: Mapping[str, Any], *, snapshot_ready: bool = False) -> dict[str, Any]:
    stats = payload.get("stats") if isinstance(payload.get("stats"), Mapping) else {}
    jobs = payload.get("jobs") if isinstance(payload.get("jobs"), list) else []
    programs = payload.get("programs") if isinstance(payload.get("programs"), list) else []
    coverage = payload.get("graduateEvidenceCoverage") if isinstance(payload.get("graduateEvidenceCoverage"), Mapping) else {}
    lifestyle = payload.get("lifestyleDiscovery") if isinstance(payload.get("lifestyleDiscovery"), Mapping) else {}

    def as_number(value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return default

    def ratio(numerator: Any, denominator: Any, fallback: float = 0.0) -> float:
        denominator_value = as_number(denominator)
        if denominator_value <= 0:
            return fallback
        return min(1.0, as_number(numerator) / denominator_value)

    job_count = int(as_number(stats.get("jobs"), len(jobs))) or len(jobs)
    status_counts: dict[str, int] = {}
    for job in jobs:
        currentness = job.get("postingCurrentness") if isinstance(job, Mapping) else None
        status = str(currentness.get("status") if isinstance(currentness, Mapping) else "unverified")
        status_counts[status] = status_counts.get(status, 0) + 1
    verified_open = status_counts.get("verified_open", 0)
    verified_closed = status_counts.get("verified_closed", 0)
    unverified = max(0, job_count - verified_open - verified_closed)

    source_complete = sum(
        bool(job.get("url")) and bool(job.get("sourceKey") or job.get("sourceLabel"))
        for job in jobs
        if isinstance(job, Mapping)
    )
    lineage_confidence = ratio(source_complete, job_count, 0.35)
    requirement_known = sum(
        bool(job.get("decisionSupport", {}).get("requirements"))
        for job in jobs
        if isinstance(job, Mapping) and isinstance(job.get("decisionSupport"), Mapping)
    )
    program_requirement_known = sum(
        bool(program.get("admissionRequirements"))
        for program in programs
        if isinstance(program, Mapping)
    )
    attachment_confidence = ratio(requirement_known + program_requirement_known, job_count + len(programs), 0.35)

    preference_summary = stats.get("preferenceSummary") if isinstance(stats.get("preferenceSummary"), Mapping) else {}
    preference_discovery = stats.get("preferenceDiscovery") if isinstance(stats.get("preferenceDiscovery"), Mapping) else {}
    preference_current = bool(preference_discovery.get("current"))
    preference_confidence = 0.82 if preference_current else (0.45 if as_number(preference_summary.get("rowCount")) else 0.30)

    total_programs = as_number(coverage.get("totalPrograms"), len(programs)) or len(programs)
    graduate_dimensions = [
        coverage.get("programsWithFaculty"),
        coverage.get("programsWithRecentPapers"),
        coverage.get("programsWithFundedProjects"),
        coverage.get("programsWithGraduateDestinations"),
    ]
    graduate_confidence = sum(ratio(item, total_programs) for item in graduate_dimensions) / len(graduate_dimensions) if total_programs else 0.0
    unresearched = int(as_number(coverage.get("unresearchedPrograms")))

    public_lifestyle = as_number(lifestyle.get("publicCandidateCount"))
    verified_lifestyle = as_number(lifestyle.get("verifiedOpenCount", lifestyle.get("publicRecommendationCount")))
    lifestyle_confidence = min(1.0, 0.2 + 0.8 * ratio(verified_lifestyle, public_lifestyle, 0.0))

    snapshot_framework = payload.get("decisionFramework") if isinstance(payload.get("decisionFramework"), Mapping) else {}
    snapshot_has_protocol = bool(snapshot_framework.get("reviewProtocol")) or snapshot_ready
    mobile_confidence = 0.90 if snapshot_has_protocol else 0.20
    source_review_candidates = int(as_number(stats.get("sourceReviewCandidates")))
    perspective_specs = [
        {"id": "rebuttal", "label": "rebuttal", "purpose": "find counterexamples", "question": "what could be false?", "gate": "compare source and status", "loop": "send counterexample to next query", "status": "review" if unverified or source_review_candidates else "pass", "finding": f"unverified={unverified}; review={source_review_candidates}"},
        {"id": "first_principle_purpose", "label": "first principle purpose", "purpose": "reduce the decision to its goal", "question": "which goal does this evidence serve?", "gate": "link goal to evidence", "loop": "create a query when goal is empty", "status": "pass", "finding": "goals remain separate from candidate score"},
        {"id": "first_principle_assumptions", "label": "first principle assumptions", "purpose": "separate assumptions from facts", "question": "does a hidden constant distort ranking?", "gate": "exclude region KPI and fixed top-N", "loop": "turn violated assumptions into feedback", "status": "pass", "finding": "regionWeight=0; domestic/overseas is classification only"},
        {"id": "expansion_combination", "label": "expansion combination", "purpose": "combine independent evidence", "question": "are positive and negative feedback compared?", "gate": "record lineage with similarity", "loop": "reuse combined signals in search", "status": "review" if preference_confidence < 0.8 else "pass", "finding": f"feedback_confidence={round(preference_confidence * 100)}%"},
        {"id": "expansion_absence", "label": "expansion absence", "purpose": "find missing evidence", "question": "are attachments and graduate facts absent?", "gate": "separate unknown from none", "loop": "add missing fields to collection queue", "status": "review" if unresearched or attachment_confidence < 0.7 else "pass", "finding": f"unresearched_programs={unresearched}; requirement_confidence={round(attachment_confidence * 100)}%"},
        {"id": "outsider", "label": "outsider", "purpose": "test first-time comprehension", "question": "are score and blank meanings visible?", "gate": "show formula and boundaries on mobile", "loop": "turn confusion into UX regression", "status": "review" if not snapshot_has_protocol else "pass", "finding": "snapshot protocol presence is checked"},
        {"id": "executor", "label": "executor", "purpose": "choose the next executable step", "question": "which action raises trust fastest?", "gate": "rank impact, confidence, leverage", "loop": "recalculate after each completion", "status": "pass", "finding": "goal priority table is generated"},
        {"id": "blind_spot", "label": "blind spot", "purpose": "surface hidden public-data risks", "question": "can feedback or leads reveal private traits?", "gate": "exclude personal counts and raw notes", "loop": "move exposure risk to revalidation queue", "status": "review" if source_review_candidates else "pass", "finding": "public candidates must not enable inference"},
    ]

    formula = "priority = 5 * impact * evidence confidence * execution leverage"
    # data-requirement-id="DATA-310": this score orders project workstreams only.
    # It must never be reused as a job/programme suitability or candidate-ranking input.
    score_contract = {
        "scoreType": "project_workstream_priority",
        "candidateSuitability": False,
        "candidateRankingInput": False,
        "regionExcludedFromScore": True,
        "regionWeight": 0,
        "allowedInputs": ["impact", "evidenceConfidence", "executionLeverage"],
        "forbiddenInputs": ["candidateProfile", "privateFeedbackNotes", "region"],
        "outputUse": "project_execution_priority_only",
    }
    workstream_specs = [
        ("lineage", "data lineage", min(1.0, 0.35 + 0.65 * lineage_confidence), lineage_confidence, 0.90, "source URL and source key must survive producer to mobile"),
        ("attachments", "requirement attachments", 0.85, attachment_confidence, 0.80, "public postings often keep requirements in PDF or HWP"),
        ("feedback", "structured feedback", 0.90, preference_confidence, 0.82, "positive and negative reasons must become comparable fields"),
        ("graduate", "graduate evidence", 0.88, graduate_confidence, 0.78, "faculty, papers, funded work, and destinations are separate facts"),
        ("mobile_refresh", "mobile refresh", 0.92, mobile_confidence, 0.95, "queue status must be truthful from iPhone to worker"),
        ("lifestyle", "lifestyle filter", 0.70, lifestyle_confidence, 0.65, "commute and work-life claims need public verification"),
    ]

    def ranked(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ordered = sorted(rows, key=lambda row: (-float(row["priority"]), str(row["id"])))
        return [dict(row, rank=index) for index, row in enumerate(ordered, start=1)]

    workstreams = ranked([
        {"id": item_id, "label": label, "impact": round(impact, 3), "evidenceConfidence": round(confidence, 3), "executionLeverage": round(leverage, 3), "priority": round(5 * impact * confidence * leverage, 1), "basis": basis}
        for item_id, label, impact, confidence, leverage, basis in workstream_specs
    ])

    by_id = {row["id"]: row for row in workstreams}
    goal_specs = [
        ("decision_support", "decision support", "graduate", "ranked evidence before opinion"),
        ("data_lineage", "data lineage", "lineage", "one producer and one public snapshot"),
        ("feedback_loop", "feedback loop", "feedback", "structured positive and negative reasons"),
        ("mobile_observability", "mobile observability", "mobile_refresh", "truthful queue and progress state"),
        ("graduate_evidence", "graduate evidence", "graduate", "faculty papers funded work destinations"),
        ("lifestyle_filter", "lifestyle filter", "lifestyle", "commute and safety remain evidence-bound"),
    ]
    goal_rows = ranked([
        {"id": goal_id, "label": label, "priority": by_id[workstream_id]["priority"], "evidenceConfidence": by_id[workstream_id]["evidenceConfidence"], "basis": basis, "workstream": workstream_id}
        for goal_id, label, workstream_id, basis in goal_specs
    ])
    goals = {row["id"]: row["priority"] for row in goal_rows}

    blockers: list[str] = []
    if unverified:
        blockers.append(f"{unverified} job records are not verified open or closed")
    if unresearched:
        blockers.append(f"{unresearched} graduate programs still lack a complete evidence pack")
    if source_review_candidates:
        blockers.append(f"{source_review_candidates} source leads still require official revalidation")
    if not snapshot_has_protocol:
        blockers.append("the current public snapshot does not yet carry this review protocol")
    synthesis = {
        "recommendation": "verified_facts_first" if blockers else "ranked_review",
        "summary": "Keep unknowns visible, rank only evidence-backed work, then loop missing fields into collection.",
        "blockers": blockers,
        "nextActions": [
            "rebuild the public snapshot from the same producer after reviewProtocol is present",
            "revalidate attachment-only requirements before treating a posting as eligible",
            "collect structured positive and negative reasons without publishing raw personal notes",
        ],
        "boundaries": {
            "candidateSuitability": score_contract["candidateSuitability"],
            "candidateRankingInput": score_contract["candidateRankingInput"],
            "regionWeight": score_contract["regionWeight"],
            "regionRule": "domestic/overseas classification only",
            "publicFeedbackRule": "exclude personal counts and original notes",
        },
    }

    return {
        "version": "review-protocol-v1",
        "stages": [
            {"id": "perspectives", "title": "stage 1 - eight perspectives", "items": perspective_specs},
            {"id": "ranking", "title": "stage 2 - goal ranking", "items": goal_rows, "workstreams": workstreams, "formula": formula},
            {"id": "synthesis", "title": "stage 3 - synthesis", "items": synthesis["nextActions"], "result": synthesis},
        ],
        "goalPriority": {
            "scale": {"min": 0, "max": 5},
            "scoreType": score_contract["scoreType"],
            "candidateSuitability": score_contract["candidateSuitability"],
            "candidateRankingInput": score_contract["candidateRankingInput"],
            "regionExcludedFromScore": score_contract["regionExcludedFromScore"],
            "allowedInputs": score_contract["allowedInputs"],
            "forbiddenInputs": score_contract["forbiddenInputs"],
            "outputUse": score_contract["outputUse"],
            "formula": formula,
            "goals": goals,
            "rankedGoals": goal_rows,
            "workstreams": workstreams,
        },
        "candidateSimilarity": {
            "regionWeight": score_contract["regionWeight"],
            "goalPriorityInput": False,
        },
        "synthesis": synthesis,
    }

def _decision_framework(payload: Mapping[str, Any], *, snapshot_ready: bool = False) -> dict[str, Any]:
    stats = payload.get("stats") if isinstance(payload.get("stats"), Mapping) else {}
    coverage = payload.get("graduateEvidenceCoverage") if isinstance(payload.get("graduateEvidenceCoverage"), Mapping) else {}
    lifestyle = payload.get("lifestyleDiscovery") if isinstance(payload.get("lifestyleDiscovery"), Mapping) else {}
    return {
        # Compatibility lineage for the append-only requirements ledger:
        # decision-framework-v2 and framework-state-v2 are superseded by v3.
        # data-requirement-id="DATA-297": v3 is expandable by required IDs, not fixed counts.
        "schemaVersion": "decision-framework-v3",
        "stateSchemaVersion": "framework-state-v3",
        "dataRequirementId": "DATA-297",
        "generatedFrom": {
            "producer": "scripts/build_snapshot.py",
            "outputPath": "data/app-data.json",
            "consumer": "app.js decisionFrameworkPanel",
            "jobDataAsOf": stats.get("jobDataAsOf") or payload.get("dataAsOf"),
            "graduateGeneratedAt": stats.get("graduateGeneratedAt"),
        },
        "principles": [
            {"label": "PROCESS", "copy": "먼저 넓게 후보군을 만들고, 같은 data/app-data.json 경로로 화면까지 전달합니다."},
            {"label": "GATE", "copy": "공식 원문, 공개 연구근거, 구조화 피드백이 없으면 결론 대신 빈칸으로 둡니다."},
            {"label": "LOOP", "copy": "관심·별로예요 사유와 미확인 항목을 다음 수집 질문으로 되돌립니다."},
        ],
        "scoreBoundaries": [
            "지역은 국내·국외 분류와 생활 리스크 검토에만 쓰고 추천 점수 KPI에서 제외합니다.",
            "자유 메모는 검토용이며 구조화 항목으로 확인되기 전까지 점수에 반영하지 않습니다.",
            "커뮤니티·카페·링크드인 신호는 후보 발견용 lead이고 공식 원문으로 재검증해야 합니다.",
        ],
        "reviewProtocol": _review_protocol(payload, snapshot_ready=snapshot_ready),
        "readinessBoundary": _decision_readiness_boundary(payload),
        "domains": _framework_domains(payload, stats, coverage),
        "signals": {
            "jobs": stats.get("jobs", len(payload.get("jobs") or [])),
            "programs": stats.get("programs", len(payload.get("programs") or [])),
            "preferenceRuntime": {
                "state": "authenticated_runtime_required",
                "publicSnapshot": "anonymous_no_user_counts",
                "countsPublished": False,
            },
            "programsWithFaculty": coverage.get("programsWithFaculty", 0),
            # data-requirement-id="DATA-295": review candidates are not verified-open recommendations.
            "lifestylePublicCandidates": lifestyle.get("publicCandidateCount", 0),
            "lifestyleVerifiedOpen": lifestyle.get("verifiedOpenCount", lifestyle.get("publicRecommendationCount", 0)),
        },
    }


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
        # data-requirement-id="DATA-294": verified open is distinct from review candidates.
        "verifiedOpenCount": verified_open_count,
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
                # data-requirement-id="DATA-295": Busan is ready only when workplace and WLB are both evidenced.
                "decisionReadiness": _decision_readiness(items, busan_ids, ("busanWorkplace", "wlb")),
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

    def normalize_public_discovery(job: dict[str, Any]) -> None:
        """DATA-281: published jobs must carry the same action/explore contract the app verifies."""
        tier = str(job.get("discoveryTier") or "").strip()
        queue = str(job.get("queue") or "").strip()
        if tier not in {"action", "explore"}:
            tier = "action" if queue in {"verify", "apply", "stretch"} else "explore"
        job["discoveryTier"] = tier
        if not str(job.get("discoveryLabel") or "").strip():
            job["discoveryLabel"] = "행동 후보" if tier == "action" else "탐색 후보"
        if not str(job.get("discoveryReason") or "").strip():
            if tier == "action":
                job["discoveryReason"] = "원문 확인 또는 지원 검토 큐에 들어간 행동 후보입니다."
            else:
                job["discoveryReason"] = (
                    "공식 URL과 분야 근거가 있어 넓게 살펴볼 탐색 후보입니다. "
                    "지원 가능 여부와 조건은 아직 원문에서 재확인해야 합니다."
                )

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
        normalize_public_discovery(job)
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
    payload["decisionFrameworkSources"] = _decision_framework_source_metrics(root)
    if args.programs_only:
        graduate_generated_at = _apply_latest_programs(
            payload,
            root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json",
            root / "config" / "grad_school_programs.researched.json",
        )
        _sanitize_public_programs(payload)
        stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
        stats.update({"programs": len(payload["programs"]), "graduateGeneratedAt": graduate_generated_at})
        payload["stats"] = stats
        payload["graduateEvidenceCoverage"] = _graduate_evidence_coverage(payload["programs"])
        _apply_decision_support(payload)
        _apply_lifestyle_discovery(payload, posting_facts_path)
        payload["graduateDataLineage"] = _graduate_data_lineage(
            payload,
            app_root=app_root,
            job_search_root=root,
            catalog_source=args.catalog_source,
            shortlist_source=root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json",
            research_source=root / "config" / "grad_school_programs.researched.json",
        )
        payload["decisionFramework"] = _decision_framework(payload, snapshot_ready=True)
        _atomic_write_json(args.output, payload)
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
    _sanitize_public_programs(payload)
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
    payload["graduateDataLineage"] = _graduate_data_lineage(
        payload,
        app_root=app_root,
        job_search_root=root,
        catalog_source=args.catalog_source,
        shortlist_source=root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json",
        research_source=root / "config" / "grad_school_programs.researched.json",
    )
    payload["decisionFramework"] = _decision_framework(payload, snapshot_ready=True)
    _atomic_write_json(args.output, payload)
    print(
        f"wrote {args.output}: {len(payload['jobs'])} job candidates, "
        f"{len(payload['programs'])} programs, {len(payload['funding'])} funding opportunities"
    )


if __name__ == "__main__":
    main()

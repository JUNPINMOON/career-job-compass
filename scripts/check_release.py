"""Dependency-free release checks for the static Career Compass PWA."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Iterator, Mapping


ROOT = Path(__file__).resolve().parents[1]
LIFESTYLE_METHOD_VERSION = "lifestyle-evidence-v2"
GRADUATE_LINEAGE_METHOD_VERSION = "graduate-lineage-v2"
GRADUATE_EVIDENCE_AXES = {
    "faculty": "faculty",
    "recentPapers": "recentPapers",
    "fundedProjects": "recentProjects",
    "graduateDestinations": "graduateDestinations",
    "testimonials": "graduateTestimonials",
}
GRADUATE_CLAIM_STATE_BY_EVIDENCE = {
    "present": "evidence_present",
    "not_researched": "no_claim",
    "reviewed_no_qualifying": "no_claim",
    "searched_none": "search_no_result",
    "verified_none": "source_asserts_none",
}
LIFESTYLE_LEGACY_METHOD_VERSION = "lifestyle-evidence-v1"
LIFESTYLE_STATUSES = {"confirmed", "claimed", "unknown", "negative"}
LIFESTYLE_LANES = {"jayang_wlb", "busan"}
LIFESTYLE_AXES = {"jayangCommute", "wlb", "busanWorkplace"}
LIFESTYLE_SEARCH_STATES = {"searched", "not_searched", "partial", "failed", "stale"}
LIFESTYLE_READINESS = {"ready", "partial", "insufficient"}
LIFESTYLE_SOURCE_STATES = {"known_open", "known_closed", "status_unknown", "archived_reference"}
LIFESTYLE_SOURCE_ARTIFACT = "job_search/work/recommendation-v4/g003-posting-facts.json"
LIFESTYLE_CANDIDATE_CLASSES = {"statusRecheck", "verifiedOpen"}
LIFESTYLE_CANDIDATE_FILTER_KEYS = {
    "sourcePostings",
    "openOrUnknown",
    "targetLocation",
    "strictLocation",
    "relevantDomain",
    "roleFit",
    "juniorAttainable",
    "wlbNotNegative",
    "publishedCandidates",
    "excludedClosed",
    "excludedArchived",
    "excludedMalformed",
    "excludedDuplicate",
    "excludedNoTargetLocation",
    "excludedNoStrictLocation",
    "excludedRoleNoise",
    "excludedSenior",
    "excludedNoRoleSignal",
    "excludedNotJunior",
    "excludedWlbNegative",
}
LIFESTYLE_FILTER_COUNT_KEYS = {
    "sourcePostingCount",
    "nonClosed",
    "rawLocation",
    "strictLocation",
    "relevantDomain",
    "roleFit",
    "juniorAttainable",
    "wlbNotNegative",
    "deduplicated",
    "statusRecheck",
    "verifiedOpen",
    "publishedCandidate",
}
LIFESTYLE_LANE_FILTER_KEYS = {
    "rawLocation",
    "strictLocation",
    "relevantDomain",
    "roleFit",
    "juniorAttainable",
    "wlbNotNegative",
    "reviewCandidate",
    "statusRecheck",
    "verifiedOpen",
}
STRICT_LOCATION_KEYS = {
    "matched",
    "cityCode",
    "cityLabel",
    "district",
    "normalized",
    "sourceText",
    "domestic",
    "locationText",
    "lanes",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HTTP_URL = re.compile(r"^https?://", re.IGNORECASE)
PUBLIC_TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".map",
    ".md",
    ".svg",
    ".txt",
    ".webmanifest",
    ".xml",
}
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")
RELEASE_TEXT_LEAK_PATTERNS = (
    ("file URI", re.compile(r"(?i)\bfile://")),
    ("absolute local path", re.compile(r"(?i)\b[A-Z]:[\\/]")),
    ("AppData or temp path", re.compile(r"(?i)\b(?:AppData|Local[\\/]Temp|Temp[\\/])\b")),
    ("secret marker", re.compile(r"(?i)\b(?:service_role|secret_key|refresh_token|access_token|auth_token|auth_header|session_token|cookie)\b")),
)
RELEASE_STRUCTURED_LEAK_PATTERNS = (
    (
        "profile/user identifier field",
        re.compile(
            r"(?i)[\"'](?:user_id|userId|owner_id|ownerId|auth_user_id|authUserId|"
            r"profile_id|profileId|profile_digest|profileDigest|account_id|accountId)[\"']\s*:"
        ),
    ),
    (
        "raw feedback field",
        re.compile(
            r"(?i)[\"'](?:rawFeedback|feedbackPayload|reasonEvidence|reason_evidence|"
            r"structuredReasons|feedbackReasons|groupNotes|reasonCounts)[\"']\s*:"
        ),
    ),
)
PUBLIC_GRADUATE_PRIVATE_READINESS_KEYS = frozenset(
    {
        "englishgapplan",
        "privateadmissionsreadiness",
    }
)
PUBLIC_GRADUATE_PRIVATE_READINESS_PATTERNS = (
    re.compile(r"\bexpired\s+(?:english\s+)?(?:certificates?|certs?)\b", re.IGNORECASE),
    re.compile(r"\bcandidate['\u2019]s\b", re.IGNORECASE),
    re.compile(r"\bcandidate\s+must\s+retake\b", re.IGNORECASE),
    re.compile(r"\b(?:his|her)\s+english\s+(?:certificates?|certs?)\b", re.IGNORECASE),
    re.compile(
        r"\bas\s+a\s+korean\s+domestic\s+(?:applicant|student)\s+(?:he|she)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bstrongest\s+path\s+for\s+(?:this|the)\s+candidate\b", re.IGNORECASE),
    re.compile(r"\bcandidate\s+(?:is\s+)?most\s+likely\s+ineligible\b", re.IGNORECASE),
    re.compile(r"지원자\s*swmm", re.IGNORECASE),
)


def require(path: Path, label: str) -> None:
    if not path.is_file():
        raise SystemExit(f"missing {label}: {path}")


def contains_forbidden_key(value: object) -> bool:
    forbidden = {"abstentionreason", "candidateaction", "applicantprofile", "credentials", "crm", "token", "email", "profiledigest"}
    if isinstance(value, dict):
        return any(str(key).replace("_", "").lower() in forbidden or contains_forbidden_key(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_forbidden_key(item) for item in value)
    return False


def support_only_title(title: object) -> bool:
    """Mirror DATA-215 at the release boundary."""
    text = str(title or "").strip()
    support_role = re.search(
        r"\b(finance intern|finance and budget officer|recruit(?:ment|er)|"
        r"human resources?|payroll|reception(?:ist)?|account executive)\b",
        text,
        flags=re.IGNORECASE,
    )
    title_grounded_target = re.search(
        r"\b(water|hydro|flood|climate|adaptation|resilien(?:ce|t)|coastal|"
        r"environment|gis|geospatial|remote sensing|data|machine learning|ai|"
        r"artificial intelligence|project)\b",
        text,
        flags=re.IGNORECASE,
    )
    return bool(support_role and not title_grounded_target)


def experienced_only_title(title: object) -> bool:
    """DATA-234."""
    text = str(title or "").replace(" ", "")
    return "\uacbd\ub825\uc9c1" in text and "\uc2e0\uc785" not in text and "\uacbd\ub825\ubb34\uad00" not in text


def valid_decision_support(record: dict, expected_type: str) -> bool:
    support = record.get("decisionSupport")
    return (
        isinstance(support, dict)
        and support.get("recordType") == expected_type
        and isinstance(support.get("knownInformation"), list)
        and isinstance(support.get("missingInformation"), list)
        and isinstance(support.get("nextActions"), list)
        and len(support.get("dimensions") or []) == 5
    )


def contains_non_contract_research(value: object) -> bool:
    """Mirror DATA-216 at the release boundary."""
    markers = (
        "not a funded grant", "editorial", "guest editor", "special issue",
        "publication dates", "specific grant id not disclosed",
    )
    if isinstance(value, dict):
        return any(contains_non_contract_research(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_non_contract_research(item) for item in value)
    return isinstance(value, str) and any(marker in value.lower() for marker in markers)


def _lifestyle_digest(discovery: dict) -> str:
    digest_source = dict(discovery)
    digest_source.pop("digest", None)
    return hashlib.sha256(
        json.dumps(digest_source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive_kind(path: Path) -> str | None:
    name = path.name.lower()
    if name.endswith(".zip"):
        return "zip"
    if name.endswith(ARCHIVE_SUFFIXES[1:]):
        return "tar"
    return None


def _is_public_text_label(label: str) -> bool:
    member_label = label.split("!", 1)[-1].lower()
    return any(member_label.endswith(suffix) for suffix in PUBLIC_TEXT_SUFFIXES)


def _is_structured_public_label(label: str) -> bool:
    member_label = label.split("!", 1)[-1].lower()
    return member_label.endswith((".json", ".webmanifest"))


def _safe_archive_member_name(name: str, artifact_label: str) -> str:
    normalized = name.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"(?i)^[a-z]:", normalized)
        or ".." in parts
    ):
        raise SystemExit(f"release privacy scan failed ({artifact_label}: unsafe archive member path)")
    return normalized


def _scan_release_text(label: str, text: str) -> None:
    for leak_label, pattern in RELEASE_TEXT_LEAK_PATTERNS:
        if pattern.search(text):
            raise SystemExit(f"release privacy scan failed ({label}: {leak_label})")
    if _is_structured_public_label(label):
        for leak_label, pattern in RELEASE_STRUCTURED_LEAK_PATTERNS:
            if pattern.search(text):
                raise SystemExit(f"release privacy scan failed ({label}: {leak_label})")


def iter_archive_member_texts(path: Path, artifact_label: str) -> Iterator[tuple[str, str]]:
    """Yield public text members from zip/tar release archives without trusting member paths."""
    kind = _archive_kind(path)
    if kind == "zip":
        try:
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    member_name = _safe_archive_member_name(member.filename, artifact_label)
                    label = f"{artifact_label}!{member_name}"
                    if _is_public_text_label(label):
                        yield label, archive.read(member).decode("utf-8", errors="replace")
        except (OSError, zipfile.BadZipFile) as error:
            raise SystemExit(f"release privacy scan failed ({artifact_label}: unreadable archive {error.__class__.__name__})") from None
    elif kind == "tar":
        try:
            with tarfile.open(path) as archive:
                for member in archive.getmembers():
                    if not member.isfile():
                        continue
                    member_name = _safe_archive_member_name(member.name, artifact_label)
                    label = f"{artifact_label}!{member_name}"
                    if not _is_public_text_label(label):
                        continue
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        raise SystemExit(f"release privacy scan failed ({label}: unreadable archive member)")
                    yield label, extracted.read().decode("utf-8", errors="replace")
        except (OSError, tarfile.TarError) as error:
            raise SystemExit(f"release privacy scan failed ({artifact_label}: unreadable archive {error.__class__.__name__})") from None


def iter_public_artifact_texts(root: Path = ROOT, artifact_root: Path | None = None) -> Iterator[tuple[str, str]]:
    """SEC-277 data-requirement-id="SEC-277": recursively scan the packaged public artifact."""
    root = Path(root)
    artifact_root = Path(artifact_root) if artifact_root is not None else root / "_site"
    resolved_root = root.resolve()
    resolved_artifact = artifact_root.resolve(strict=True)
    try:
        resolved_artifact.relative_to(resolved_root)
    except ValueError:
        raise SystemExit("release privacy scan failed: artifact escaped the release root") from None
    if not resolved_artifact.is_dir():
        raise SystemExit("release privacy scan failed: artifact root is not a directory")
    for path in sorted(resolved_artifact.rglob("*")):
        if not path.is_file():
            continue
        try:
            resolved_path = path.resolve(strict=True)
            resolved_path.relative_to(resolved_artifact)
            artifact_label = resolved_path.relative_to(resolved_root).as_posix()
        except (OSError, ValueError):
            raise SystemExit("release privacy scan failed: file escaped the artifact root") from None
        archive_kind = _archive_kind(path)
        if archive_kind:
            yield from iter_archive_member_texts(path, artifact_label)
        elif _is_public_text_label(artifact_label):
            try:
                yield artifact_label, path.read_text(encoding="utf-8", errors="replace")
            except OSError as error:
                raise SystemExit(f"release privacy scan failed ({artifact_label}: unreadable text {error.__class__.__name__})") from None


def validate_release_privacy_scan(root: Path = ROOT, artifact_root: Path | None = None) -> int:
    """Scan the exact packaged public artifact tree and reject private release text."""
    scanned = 0
    for label, text in iter_public_artifact_texts(root, artifact_root):
        _scan_release_text(label, text)
        scanned += 1
    if scanned == 0:
        raise SystemExit("release privacy scan failed: no public text artifacts were inspected")
    return scanned


def _contains_float(value: object) -> bool:
    """The PWA digest uses JSON.stringify, so v2 keeps numeric fields integral."""
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return isinstance(value, float)


def _count_statuses(values: list[str]) -> dict[str, int]:
    return {status: values.count(status) for status in sorted(LIFESTYLE_STATUSES)}


def _count_candidate_classes(values: list[str]) -> dict[str, int]:
    return {name: values.count(name) for name in sorted(LIFESTYLE_CANDIDATE_CLASSES)}


def _require_non_negative_count_map(value: object, expected_keys: set[str], label: str) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise SystemExit(f"{label} must declare exactly {sorted(expected_keys)}")
    for key, count in value.items():
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise SystemExit(f"{label}.{key} must be a non-negative integer")
    return dict(value)


def _validate_candidate_filter(value: object, source_status: dict, label: str) -> dict[str, dict[str, bool]]:
    if not isinstance(value, dict) or set(value) != LIFESTYLE_LANES:
        raise SystemExit(f"{label} must expose exactly {sorted(LIFESTYLE_LANES)}")
    result: dict[str, dict[str, bool]] = {}
    for lane_name, lane_filter in value.items():
        if not isinstance(lane_filter, dict) or set(lane_filter) != LIFESTYLE_LANE_FILTER_KEYS:
            raise SystemExit(f"{label}.{lane_name} must declare exactly {sorted(LIFESTYLE_LANE_FILTER_KEYS)}")
        if any(not isinstance(flag, bool) for flag in lane_filter.values()):
            raise SystemExit(f"{label}.{lane_name} values must be booleans")
        expected_review = all(
            lane_filter[key]
            for key in (
                "strictLocation",
                "relevantDomain",
                "roleFit",
                "juniorAttainable",
                "wlbNotNegative",
            )
        )
        if lane_filter["reviewCandidate"] != expected_review:
            raise SystemExit(f"{label}.{lane_name} reviewCandidate must equal every strict admission gate")
        if lane_filter["reviewCandidate"]:
            expected_verified = source_status.get("state") == "known_open"
            if lane_filter["verifiedOpen"] != expected_verified or lane_filter["statusRecheck"] != (not expected_verified):
                raise SystemExit(f"{label}.{lane_name} status class must match sourceStatus")
        elif lane_filter["verifiedOpen"] or lane_filter["statusRecheck"]:
            raise SystemExit(f"{label}.{lane_name} cannot carry a status class without reviewCandidate")
        result[lane_name] = dict(lane_filter)
    return result


def _expected_lifestyle_readiness(items: list[dict], review_ids: list[str], required_axes: tuple[str, ...]) -> str:
    selected = [item for item in items if str(item.get("jobId") or "") in set(review_ids)]
    if not selected:
        return "insufficient"
    for item in selected:
        source_status = item.get("sourceStatus") if isinstance(item.get("sourceStatus"), dict) else {}
        axes = item.get("lifestyleEvidence", {}).get("axes", {})
        if source_status.get("state") != "known_open":
            return "partial"
        if any(axes.get(axis, {}).get("status") not in {"confirmed", "claimed"} for axis in required_axes):
            return "partial"
    return "ready"


def _validate_lifestyle_axis(axis: object) -> None:
    if (
        not isinstance(axis, dict)
        or axis.get("status") not in LIFESTYLE_STATUSES
        or not isinstance(axis.get("summary"), str)
        or not axis.get("summary")
        or not isinstance(axis.get("evidence"), list)
        or not isinstance(axis.get("missing"), list)
    ):
        raise SystemExit("invalid lifestyleEvidence axis")
    if any(not isinstance(value, str) for value in axis.get("evidence", []) + axis.get("missing", [])):
        raise SystemExit("lifestyleEvidence axis evidence and missing fields must be strings")


def _validate_strict_location(value: object, lane_name: str, item_location: str) -> None:
    if not isinstance(value, dict) or set(value) != STRICT_LOCATION_KEYS:
        raise SystemExit(f"lifestyleDiscovery strictLocation must declare exactly {sorted(STRICT_LOCATION_KEYS)}")
    lanes = value.get("lanes")
    if (
        value.get("matched") is not True
        or value.get("cityCode") not in {"seoul", "busan"}
        or not isinstance(value.get("cityLabel"), str)
        or not value["cityLabel"].strip()
        or not isinstance(value.get("district"), str)
        or not isinstance(value.get("normalized"), str)
        or not value["normalized"].strip()
        or not isinstance(value.get("sourceText"), str)
        or not value["sourceText"].strip()
        or value.get("domestic") is not True
        or not isinstance(value.get("locationText"), str)
        or not value["locationText"].strip()
        or value["locationText"] != item_location
        or not isinstance(lanes, dict)
        or set(lanes) != LIFESTYLE_LANES
        or any(not isinstance(flag, bool) for flag in lanes.values())
    ):
        raise SystemExit("lifestyleDiscovery strictLocation must prove domestic lane location")
    expected_city = "seoul" if lane_name == "jayang_wlb" else "busan"
    if value.get("cityCode") != expected_city:
        raise SystemExit("lifestyleDiscovery strictLocation cityCode must match its lane")
    if lanes.get(lane_name) is not True:
        raise SystemExit("lifestyleDiscovery lane reviewIds must match strictLocation flags")


def _validate_candidate_evidence(value: object) -> None:
    if not isinstance(value, list) or not value:
        raise SystemExit("lifestyleDiscovery item missing candidateEvidence")
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {"source", "method", "text"}:
            raise SystemExit("lifestyleDiscovery candidateEvidence entries must expose source, method, and text")
        if entry.get("source") != LIFESTYLE_SOURCE_ARTIFACT or entry.get("method") != LIFESTYLE_METHOD_VERSION:
            raise SystemExit("lifestyleDiscovery candidateEvidence must retain exact source and method")
        if not isinstance(entry.get("text"), str) or not entry["text"].strip():
            raise SystemExit("lifestyleDiscovery candidateEvidence text must be public evidence")


def _validate_lifestyle_discovery_v1(discovery: dict, jobs: list[dict]) -> None:
    """Legacy DATA-240 boundary: v1 items were a subset of released jobs."""
    if discovery.get("methodVersion") != LIFESTYLE_LEGACY_METHOD_VERSION:
        raise SystemExit("lifestyleDiscovery methodVersion mismatch")
    if discovery.get("scoreImpact") != "none":
        raise SystemExit("lifestyleDiscovery must not affect recommendation scores")
    if discovery.get("sourceJobCount") != len(jobs):
        raise SystemExit("lifestyleDiscovery sourceJobCount must match released jobs")
    if not isinstance(discovery.get("limitations"), list) or not discovery["limitations"]:
        raise SystemExit("lifestyleDiscovery must disclose limitations")
    if discovery.get("digest") != _lifestyle_digest(discovery):
        raise SystemExit("lifestyleDiscovery digest mismatch")
    items = discovery.get("items")
    lanes = discovery.get("lanes")
    if not isinstance(items, list) or not isinstance(lanes, dict) or set(lanes) != LIFESTYLE_LANES:
        raise SystemExit("lifestyleDiscovery must include both supported lanes")
    job_ids = {str(job.get("id") or "") for job in jobs}
    item_by_id: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            raise SystemExit("lifestyleDiscovery items must be objects")
        job_id = str(item.get("jobId") or "")
        if not job_id or job_id not in job_ids or job_id in item_by_id:
            raise SystemExit("lifestyleDiscovery item IDs must be unique released job IDs")
        lifestyle_evidence = item.get("lifestyleEvidence")
        if not isinstance(lifestyle_evidence, dict):
            raise SystemExit("lifestyleDiscovery item missing lifestyleEvidence")
        axes = lifestyle_evidence.get("axes")
        item_lanes = lifestyle_evidence.get("lanes")
        if not isinstance(axes, dict) or set(axes) != LIFESTYLE_AXES:
            raise SystemExit("lifestyleEvidence must separate commute, WLB, and Busan axes")
        if not isinstance(item_lanes, dict) or set(item_lanes) != LIFESTYLE_LANES:
            raise SystemExit("lifestyleEvidence must expose both lane statuses")
        for axis in axes.values():
            _validate_lifestyle_axis(axis)
        if axes["wlb"]["status"] == "negative":
            raise SystemExit("lifestyleDiscovery published candidates cannot carry explicit negative WLB evidence")
        if set(item_lanes.values()) - LIFESTYLE_STATUSES:
            raise SystemExit("invalid lifestyleEvidence lane status")
        item_by_id[job_id] = item

    expected_global_classes = _count_candidate_classes([item["candidateClass"] for item in items])
    if (
        filter_counts["statusRecheck"] != expected_global_classes["statusRecheck"]
        or filter_counts["verifiedOpen"] != expected_global_classes["verifiedOpen"]
    ):
        raise SystemExit("lifestyleDiscovery global status counts do not match item candidate classes")

    reviewed_ids: set[str] = set()
    for lane_name, lane in lanes.items():
        if not isinstance(lane, dict):
            raise SystemExit("lifestyleDiscovery lane must be an object")
        review_ids = lane.get("reviewIds")
        counts = lane.get("counts")
        if not isinstance(review_ids, list) or len(review_ids) != len(set(review_ids)):
            raise SystemExit("lifestyleDiscovery lane reviewIds must be unique")
        if not isinstance(counts, dict) or set(counts) != LIFESTYLE_STATUSES:
            raise SystemExit("lifestyleDiscovery lane counts must cover every status")
        if any(job_id not in item_by_id for job_id in review_ids):
            raise SystemExit("lifestyleDiscovery lane references an unknown item")
        expected_counts = _count_statuses([
            item_by_id[job_id]["lifestyleEvidence"]["lanes"][lane_name]
            for job_id in review_ids
        ])
        if counts != expected_counts or sum(counts.values()) != len(review_ids):
            raise SystemExit("lifestyleDiscovery lane counts do not match reviewIds")
        reviewed_ids.update(review_ids)
    if reviewed_ids != set(item_by_id):
        raise SystemExit("lifestyleDiscovery items must equal the union of lane reviewIds")


def validate_lifestyle_discovery(snapshot: dict, jobs: list[dict]) -> None:
    """DATA-240/DATA-241/DATA-242: verify the separate lifestyleEvidence contract at release."""
    discovery = snapshot.get("lifestyleDiscovery")
    if not isinstance(discovery, dict):
        raise SystemExit("snapshot must include lifestyleDiscovery")
    schema_version = discovery.get("schemaVersion")
    if schema_version == LIFESTYLE_LEGACY_METHOD_VERSION:
        _validate_lifestyle_discovery_v1(discovery, jobs)
        return
    if schema_version != LIFESTYLE_METHOD_VERSION:
        raise SystemExit("lifestyleDiscovery schemaVersion mismatch")
    if discovery.get("methodVersion") != LIFESTYLE_METHOD_VERSION:
        raise SystemExit("lifestyleDiscovery methodVersion mismatch")
    if discovery.get("scoreImpact") != "none":
        raise SystemExit("lifestyleDiscovery must not affect recommendation scores")
    if not isinstance(discovery.get("limitations"), list) or not discovery["limitations"]:
        raise SystemExit("lifestyleDiscovery must disclose limitations")
    if discovery.get("searchState") not in LIFESTYLE_SEARCH_STATES:
        raise SystemExit("lifestyleDiscovery must declare a valid searchState")
    if not isinstance(discovery.get("searchedAt"), str) or not discovery["searchedAt"]:
        raise SystemExit("lifestyleDiscovery must declare searchedAt")
    if discovery.get("sourceArtifact") != LIFESTYLE_SOURCE_ARTIFACT:
        raise SystemExit("lifestyleDiscovery must point to the canonical G003 posting facts artifact")
    if not isinstance(discovery.get("universeLabel"), str) or not discovery["universeLabel"]:
        raise SystemExit("lifestyleDiscovery must label the searched universe")
    for key in ("sourceArtifactDigest", "sourceFileSha256", "digest"):
        if not isinstance(discovery.get(key), str) or not HEX64.fullmatch(discovery[key]):
            raise SystemExit(f"lifestyleDiscovery {key} must be a SHA-256 hex digest")
    for key in (
        "sourcePostingCount",
        "sourceRelevantPostingCount",
        "publicRecommendationCount",
        "publicCandidateCount",
    ):
        if not isinstance(discovery.get(key), int) or discovery[key] < 0:
            raise SystemExit(f"lifestyleDiscovery {key} must be a non-negative integer")
    if discovery["sourcePostingCount"] < discovery["sourceRelevantPostingCount"]:
        raise SystemExit("lifestyleDiscovery relevant posting count cannot exceed source posting count")
    candidate_filter = _require_non_negative_count_map(
        discovery.get("candidateFilter"),
        LIFESTYLE_CANDIDATE_FILTER_KEYS,
        "lifestyleDiscovery candidateFilter",
    )
    filter_counts = _require_non_negative_count_map(
        discovery.get("filterCounts"),
        LIFESTYLE_FILTER_COUNT_KEYS,
        "lifestyleDiscovery filterCounts",
    )
    if candidate_filter["sourcePostings"] != discovery["sourcePostingCount"]:
        raise SystemExit("lifestyleDiscovery candidateFilter.sourcePostings must match sourcePostingCount")
    if filter_counts["sourcePostingCount"] != discovery["sourcePostingCount"]:
        raise SystemExit("lifestyleDiscovery filterCounts.sourcePostingCount must match sourcePostingCount")
    detailed_funnel = (
        "sourcePostingCount",
        "nonClosed",
        "rawLocation",
        "strictLocation",
        "relevantDomain",
        "roleFit",
        "juniorAttainable",
        "wlbNotNegative",
        "deduplicated",
    )
    if any(filter_counts[left] < filter_counts[right] for left, right in zip(detailed_funnel, detailed_funnel[1:])):
        raise SystemExit("lifestyleDiscovery filterCounts must retain a monotonic strict-admission funnel")

    if discovery.get("digest") != _lifestyle_digest(discovery):
        raise SystemExit("lifestyleDiscovery digest mismatch")
    if _contains_float({key: value for key, value in discovery.items() if key != "digest"}):
        raise SystemExit("lifestyleDiscovery v2 must avoid floats so the browser digest is stable")

    items = discovery.get("items")
    lanes = discovery.get("lanes")
    if not isinstance(items, list) or not isinstance(lanes, dict) or set(lanes) != LIFESTYLE_LANES:
        raise SystemExit("lifestyleDiscovery must include both supported lanes")
    if not (
        candidate_filter["publishedCandidates"]
        == filter_counts["publishedCandidate"]
        == filter_counts["deduplicated"]
        == discovery["publicCandidateCount"]
        == len(items)
    ):
        raise SystemExit("lifestyleDiscovery candidate counts must equal the released item set")
    if filter_counts["statusRecheck"] + filter_counts["verifiedOpen"] != len(items):
        raise SystemExit("lifestyleDiscovery status classes must partition the released item set")
    if discovery["publicRecommendationCount"] != filter_counts["verifiedOpen"]:
        raise SystemExit("lifestyleDiscovery publicRecommendationCount must count verified-open lifestyle items only")
    top_to_detail = {
        "openOrUnknown": "nonClosed",
        "targetLocation": "rawLocation",
        "strictLocation": "strictLocation",
        "relevantDomain": "relevantDomain",
        "roleFit": "roleFit",
        "juniorAttainable": "juniorAttainable",
        "wlbNotNegative": "wlbNotNegative",
        "publishedCandidates": "publishedCandidate",
    }
    if any(candidate_filter[top] != filter_counts[detail] for top, detail in top_to_detail.items()):
        raise SystemExit("lifestyleDiscovery candidateFilter and filterCounts describe different funnels")
    item_by_id: dict[str, dict] = {}
    urls: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise SystemExit("lifestyleDiscovery items must be objects")
        job_id = str(item.get("jobId") or "")
        if not job_id or job_id in item_by_id:
            raise SystemExit("lifestyleDiscovery item IDs must be unique")
        url = str(item.get("url") or "")
        if not HTTP_URL.search(url) or url in urls:
            raise SystemExit("lifestyleDiscovery items must retain unique public source URLs")
        urls.add(url)
        if item.get("market") != "domestic":
            raise SystemExit("lifestyleDiscovery lifestyle lanes are domestic filters only")
        if item.get("domestic") is not True:
            raise SystemExit("lifestyleDiscovery items must carry an explicit domestic=true proof field")
        if not isinstance(item.get("filterReason"), str) or not item["filterReason"]:
            raise SystemExit("lifestyleDiscovery item must disclose its filter reason")
        source_status = item.get("sourceStatus")
        if (
            not isinstance(source_status, dict)
            or source_status.get("state") not in {"known_open", "status_unknown"}
            or not isinstance(source_status.get("statusLabel"), str)
            or "deadline" not in source_status
        ):
            raise SystemExit("lifestyleDiscovery items may only expose known-open or status-recheck source states")
        for key in ("title", "location", "source"):
            if not isinstance(item.get(key), str):
                raise SystemExit(f"lifestyleDiscovery item {key} must be public text")
        candidate_class = item.get("candidateClass")
        expected_class = "verifiedOpen" if source_status.get("state") == "known_open" else "statusRecheck"
        if candidate_class not in LIFESTYLE_CANDIDATE_CLASSES or candidate_class != expected_class:
            raise SystemExit("lifestyleDiscovery candidateClass must match sourceStatus")
        candidate_lane_filter = _validate_candidate_filter(
            item.get("candidateFilter"),
            source_status,
            f"lifestyleDiscovery {job_id} candidateFilter",
        )
        _validate_candidate_evidence(item.get("candidateEvidence"))
        for key in ("inclusionReasons", "missingReasons", "entrySignals", "sectorEvidence", "domainSignals"):
            values = item.get(key)
            if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
                raise SystemExit(f"lifestyleDiscovery item {key} must be an array of non-empty public strings")
        if not item["inclusionReasons"]:
            raise SystemExit("lifestyleDiscovery items must explain why they were admitted")
        if not (item["sectorEvidence"] or item["domainSignals"]):
            raise SystemExit("lifestyleDiscovery items must retain substantive sector or domain evidence")
        if not isinstance(item.get("scoreImpactReason"), str) or not item["scoreImpactReason"].strip():
            raise SystemExit("lifestyleDiscovery items must explain why location and WLB do not affect score")
        minimum_experience = item.get("minimumExperienceYears")
        if (
            minimum_experience is not None
            and (
                isinstance(minimum_experience, bool)
                or not isinstance(minimum_experience, (int, float))
                or minimum_experience < 0
                or minimum_experience >= 2
            )
        ):
            raise SystemExit("lifestyleDiscovery items must be junior-attainable under the two-year gate")
        strict_location = item.get("strictLocation")
        if not isinstance(strict_location, dict):
            raise SystemExit("lifestyleDiscovery item missing strictLocation")
        strict_lane = "jayang_wlb" if strict_location.get("cityCode") == "seoul" else "busan"
        _validate_strict_location(strict_location, strict_lane, item["location"])
        lifestyle_evidence = item.get("lifestyleEvidence")
        if not isinstance(lifestyle_evidence, dict):
            raise SystemExit("lifestyleDiscovery item missing lifestyleEvidence")
        axes = lifestyle_evidence.get("axes")
        item_lanes = lifestyle_evidence.get("lanes")
        if not isinstance(axes, dict) or set(axes) != LIFESTYLE_AXES:
            raise SystemExit("lifestyleEvidence must separate commute, WLB, and Busan axes")
        if not isinstance(item_lanes, dict) or set(item_lanes) != LIFESTYLE_LANES:
            raise SystemExit("lifestyleEvidence must expose both lane statuses")
        if any(
            lane_status != "unknown" and item.get("strictLocation", {}).get("lanes", {}).get(lane_name) is not True
            for lane_name, lane_status in item_lanes.items()
        ):
            raise SystemExit("lifestyleEvidence lane status must be backed by strictLocation")
        for lane_name, lane_filter in candidate_lane_filter.items():
            if lane_filter["reviewCandidate"] and item.get("strictLocation", {}).get("lanes", {}).get(lane_name) is not True:
                raise SystemExit("lifestyleDiscovery candidateFilter reviewCandidate must be backed by strictLocation")
        for axis in axes.values():
            _validate_lifestyle_axis(axis)
        if set(item_lanes.values()) - LIFESTYLE_STATUSES:
            raise SystemExit("invalid lifestyleEvidence lane status")
        item_by_id[job_id] = item

    lane_required_axes = {
        "jayang_wlb": ("jayangCommute", "wlb"),
        # data-requirement-id="GOV-296": match the producer's strict Busan readiness gate.
        "busan": ("busanWorkplace", "wlb"),
    }
    reviewed_ids: set[str] = set()
    for lane_name, lane in lanes.items():
        if not isinstance(lane, dict):
            raise SystemExit("lifestyleDiscovery lane must be an object")
        review_ids = lane.get("reviewIds")
        counts = lane.get("counts")
        axis_counts = lane.get("axisCounts")
        filter_counts = _require_non_negative_count_map(
            lane.get("filterCounts"),
            LIFESTYLE_LANE_FILTER_KEYS,
            f"lifestyleDiscovery {lane_name} filterCounts",
        )
        class_counts = _require_non_negative_count_map(
            lane.get("classCounts"),
            LIFESTYLE_CANDIDATE_CLASSES,
            f"lifestyleDiscovery {lane_name} classCounts",
        )
        if not isinstance(review_ids, list) or len(review_ids) != len(set(review_ids)):
            raise SystemExit("lifestyleDiscovery lane reviewIds must be unique")
        if lane.get("matchedCount") != len(review_ids):
            raise SystemExit("lifestyleDiscovery lane matchedCount must equal reviewIds")
        if lane.get("searchState") not in LIFESTYLE_SEARCH_STATES:
            raise SystemExit("lifestyleDiscovery lane must declare a valid searchState")
        if not isinstance(lane.get("searchedAt"), str) or not lane["searchedAt"]:
            raise SystemExit("lifestyleDiscovery lane must declare searchedAt")
        if not isinstance(lane.get("label"), str) or not lane["label"]:
            raise SystemExit("lifestyleDiscovery lane must keep a public label")
        if not isinstance(counts, dict) or set(counts) != LIFESTYLE_STATUSES:
            raise SystemExit("lifestyleDiscovery lane counts must cover every status")
        if not isinstance(axis_counts, dict) or set(axis_counts) != LIFESTYLE_AXES:
            raise SystemExit("lifestyleDiscovery lane axisCounts must cover every axis")
        if any(job_id not in item_by_id for job_id in review_ids):
            raise SystemExit("lifestyleDiscovery lane references an unknown item")
        for job_id in review_ids:
            _validate_strict_location(item_by_id[job_id].get("strictLocation"), lane_name, item_by_id[job_id]["location"])
            lane_filter = item_by_id[job_id]["candidateFilter"][lane_name]
            if not all(
                lane_filter[key]
                for key in (
                    "reviewCandidate",
                    "strictLocation",
                    "relevantDomain",
                    "roleFit",
                    "juniorAttainable",
                    "wlbNotNegative",
                )
            ):
                raise SystemExit("lifestyleDiscovery lane reviewIds must reference strict review candidates")
            if sum(1 for key in ("statusRecheck", "verifiedOpen") if lane_filter[key]) != 1:
                raise SystemExit("lifestyleDiscovery lane reviewIds must have one status class")
        expected_counts = _count_statuses([
            item_by_id[job_id]["lifestyleEvidence"]["lanes"][lane_name]
            for job_id in review_ids
        ])
        if counts != expected_counts or sum(counts.values()) != len(review_ids):
            raise SystemExit("lifestyleDiscovery lane counts do not match reviewIds")
        for axis_name, axis_status_counts in axis_counts.items():
            if not isinstance(axis_status_counts, dict) or set(axis_status_counts) != LIFESTYLE_STATUSES:
                raise SystemExit("lifestyleDiscovery axisCounts must cover every status")
            expected_axis_counts = _count_statuses([
                item_by_id[job_id]["lifestyleEvidence"]["axes"][axis_name]["status"]
                for job_id in review_ids
            ])
            if axis_status_counts != expected_axis_counts or sum(axis_status_counts.values()) != len(review_ids):
                raise SystemExit("lifestyleDiscovery axisCounts do not match reviewIds")
        lane_funnel = (
            "rawLocation",
            "strictLocation",
            "relevantDomain",
            "roleFit",
            "juniorAttainable",
            "wlbNotNegative",
            "reviewCandidate",
        )
        if any(filter_counts[left] < filter_counts[right] for left, right in zip(lane_funnel, lane_funnel[1:])):
            raise SystemExit("lifestyleDiscovery lane filterCounts must retain a monotonic funnel")
        if filter_counts["reviewCandidate"] != len(review_ids):
            raise SystemExit("lifestyleDiscovery lane filterCounts.reviewCandidate must match reviewIds")
        expected_status_recheck = sum(
            1 for job_id in review_ids if item_by_id[job_id]["candidateFilter"][lane_name]["statusRecheck"]
        )
        expected_verified_open = sum(
            1 for job_id in review_ids if item_by_id[job_id]["candidateFilter"][lane_name]["verifiedOpen"]
        )
        if filter_counts["statusRecheck"] != expected_status_recheck or filter_counts["verifiedOpen"] != expected_verified_open:
            raise SystemExit("lifestyleDiscovery lane filterCounts status classes do not match reviewIds")
        expected_class_counts = _count_candidate_classes([
            item_by_id[job_id]["candidateClass"]
            for job_id in review_ids
        ])
        if class_counts != expected_class_counts or sum(class_counts.values()) != len(review_ids):
            raise SystemExit("lifestyleDiscovery lane classCounts do not match reviewIds")
        expected_readiness = _expected_lifestyle_readiness(items, review_ids, lane_required_axes[lane_name])
        if lane.get("decisionReadiness") not in LIFESTYLE_READINESS or lane["decisionReadiness"] != expected_readiness:
            raise SystemExit("lifestyleDiscovery lane decisionReadiness is inconsistent")
        reviewed_ids.update(review_ids)
    if reviewed_ids != set(item_by_id):
        raise SystemExit("lifestyleDiscovery items must equal the union of lane reviewIds")


def validate_saved_jobs(snapshot: dict, jobs: list[dict]) -> None:
    """DATA-246: keep every liked job without publishing private feedback."""
    saved_jobs = snapshot.get("savedJobs")
    stats = snapshot.get("stats") if isinstance(snapshot.get("stats"), dict) else {}
    summary = stats.get("preferenceSummary") if isinstance(stats.get("preferenceSummary"), dict) else {}
    expected_count = summary.get("likedCount")
    if not isinstance(expected_count, int) or expected_count < 0:
        raise SystemExit("preferenceSummary.likedCount must be a non-negative integer")
    if not isinstance(saved_jobs, list) or len(saved_jobs) != expected_count:
        raise SystemExit("savedJobs must preserve every liked preference")
    active_ids = {str(job.get("id") or "") for job in jobs}
    saved_ids = [str(job.get("id") or "") for job in saved_jobs if isinstance(job, dict)]
    if len(saved_ids) != len(saved_jobs) or any(not job_id for job_id in saved_ids) or len(saved_ids) != len(set(saved_ids)):
        raise SystemExit("savedJobs IDs must be non-empty and unique")
    forbidden = {"reasons", "note", "updatedat", "userid", "ownerid", "owner"}

    def contains_saved_private_key(value: object) -> bool:
        if isinstance(value, dict):
            return any(
                str(key).replace("_", "").casefold() in forbidden or contains_saved_private_key(item)
                for key, item in value.items()
            )
        if isinstance(value, list):
            return any(contains_saved_private_key(item) for item in value)
        return False
    for job in saved_jobs:
        job_id = str(job.get("id") or "")
        archived = job.get("archivedFromPreference")
        exact = (job.get("personalization") or {}).get("exactFeedbackOverride")
        if archived not in {True, False}:
            raise SystemExit("savedJobs archivedFromPreference must be boolean")
        if archived == (job_id in active_ids):
            raise SystemExit("savedJobs archivedFromPreference must match active inventory membership")
        if not isinstance(job.get("title"), str) or not job["title"].strip():
            raise SystemExit("savedJobs missing title must use 저장한 공고 정보 복구 필요")
        if not isinstance(exact, dict) or exact.get("sentiment") != "liked":
            raise SystemExit("savedJobs must expose the direct liked classification")
        if contains_saved_private_key(job):
            raise SystemExit("savedJobs contains private feedback fields")


def validate_public_privacy_boundary(
    snapshot: dict,
    jobs: list[dict],
    *,
    artifact_label: str = "data/app-data.json",
) -> None:
    """DATA-248: distinguish an anonymous schema from authenticated values."""

    def reject(detail: str) -> None:
        raise SystemExit(
            f"public snapshot contains authenticated preference data ({artifact_label}: {detail})"
        )

    stats = snapshot.get("stats") if isinstance(snapshot.get("stats"), dict) else {}
    preference_summary = stats.get("preferenceSummary")
    anonymous_summary_fields = {"rowCount", "likedCount", "dislikedCount", "digest"}
    if not isinstance(preference_summary, dict):
        reject("preferenceSummary is missing")
    if set(preference_summary) != anonymous_summary_fields:
        reject("preferenceSummary has non-anonymous fields")
    if any(preference_summary.get(field) != 0 for field in ("rowCount", "likedCount", "dislikedCount")):
        reject("preferenceSummary contains non-zero user counts")
    if preference_summary.get("digest") is not None:
        reject("preferenceSummary contains a user digest")
    if stats.get("recommendationSource") != "baseline":
        reject("recommendationSource is personalized")
    if snapshot.get("savedJobs") != []:
        reject("savedJobs contains or omits the required empty public scaffold")

    discovery = stats.get("preferenceDiscovery")
    anonymous_discovery_fields = {
        "current",
        "evaluatedCandidateCount",
        "positiveCandidateCount",
        "discoveredCandidateCount",
    }
    if not isinstance(discovery, dict) or set(discovery) != anonymous_discovery_fields:
        reject("preferenceDiscovery has non-anonymous fields")
    if discovery.get("current") is not False:
        reject("preferenceDiscovery marks a personalized run current")
    for field in ("evaluatedCandidateCount", "positiveCandidateCount", "discoveredCandidateCount"):
        if discovery.get(field) != 0:
            reject(f"preferenceDiscovery.{field} is non-zero")

    def normalized_key(value: object) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value).casefold())

    # These names carry private state regardless of which public collection they
    # are placed in. Generic catalogue `score` fields are deliberately absent:
    # programme/funding scores are public editorial data, while job preference
    # scores are checked separately below.
    private_fields = {
        "personalization",
        "preferencesimilarity",
        "preferencedigest",
        "matchedfeedback",
        "matchedpreference",
        "exactfeedbackoverride",
        "positivereasonsignals",
        "appliedreasons",
        "likedevidencecount",
        "dislikedevidencecount",
        "reasonevidencecount",
        "structuredreasons",
        "feedbackreasons",
        "reasoncounts",
        "groupnotes",
        "preferencefeedback",
        "feedbackpayload",
        "userid",
        "ownerid",
        "authuserid",
        "accountid",
        "accesstoken",
        "refreshtoken",
        "authtoken",
        "authheader",
        "sessiontoken",
        "cookie",
    }
    job_private_fields = private_fields | {
        "score",
        "scorebreakdown",
        "recommendationscore",
    }

    def private_trace_path(
        value: object,
        *,
        path: tuple[str, ...] = (),
        forbidden: set[str] = private_fields,
    ) -> tuple[str, ...] | None:
        if isinstance(value, dict):
            for field, item in value.items():
                field_name = str(field)
                next_path = (*path, field_name)
                normalized = normalized_key(field_name)
                normalized_path = tuple(normalized_key(part) for part in next_path)
                if normalized in forbidden:
                    return next_path
                if normalized == "savedjobs" and normalized_path != ("savedjobs",):
                    return next_path
                if normalized == "preferencesummary" and normalized_path != ("stats", "preferencesummary"):
                    return next_path
                if normalized == "preferencediscovery" and normalized_path != ("stats", "preferencediscovery"):
                    return next_path
                nested = private_trace_path(item, path=next_path, forbidden=forbidden)
                if nested:
                    return nested
        elif isinstance(value, list):
            for item in value:
                nested = private_trace_path(item, path=(*path, "[]"), forbidden=forbidden)
                if nested:
                    return nested
        return None

    trace = private_trace_path(snapshot)
    if trace:
        reject(f"private field at {'.'.join(trace)}")
    for collection_name, collection in (("jobs", jobs), ("reviewQueue", snapshot.get("reviewQueue"))):
        trace = private_trace_path(collection, path=(collection_name,), forbidden=job_private_fields)
        if trace:
            reject(f"personalized job field at {'.'.join(trace)}")


def validate_public_data_artifacts(root: Path = ROOT) -> dict:
    """Validate the canonical public data and every deploy copy under `_site`."""
    root = Path(root)
    resolved_root = root.resolve()
    canonical = root / "data" / "app-data.json"
    if not canonical.is_file():
        raise SystemExit("public data/app-data.json is missing")
    canonical_digest = _file_sha256(canonical)

    artifact_paths = [canonical]
    site_root = root / "_site"
    if site_root.exists():
        if not site_root.is_dir():
            raise SystemExit("cannot verify _site public data: _site is not a directory")
        try:
            site_root.resolve(strict=True).relative_to(resolved_root)
        except (OSError, ValueError):
            raise SystemExit("cannot verify _site public data outside the release root") from None
        site_artifacts = sorted(path for path in site_root.rglob("app-data.json") if path.is_file())
        if not site_artifacts:
            raise SystemExit("cannot verify _site public data: no app-data.json artifact")
        artifact_paths.extend(site_artifacts)

    canonical_snapshot: dict | None = None
    for path in artifact_paths:
        try:
            resolved_path = path.resolve(strict=True)
            resolved_path.relative_to(resolved_root)
            label = path.relative_to(root).as_posix()
        except (OSError, ValueError):
            raise SystemExit("cannot verify public data artifact outside the release root") from None
        try:
            snapshot = json.loads(resolved_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise SystemExit(f"{label} is not valid JSON: {error.__class__.__name__}") from None
        if not isinstance(snapshot, dict):
            raise SystemExit(f"{label} must contain a JSON object")
        jobs = snapshot.get("jobs")
        if not isinstance(jobs, list):
            raise SystemExit(f"{label} jobs must be a list")
        validate_public_privacy_boundary(snapshot, jobs, artifact_label=label)
        if path == canonical:
            canonical_snapshot = snapshot
        elif _file_sha256(resolved_path) != canonical_digest:
            raise SystemExit(f"{label} is stale: digest differs from data/app-data.json")

    if canonical_snapshot is None:  # Defensive: canonical is always first above.
        raise SystemExit("public data/app-data.json was not validated")
    return canonical_snapshot


def public_graduate_privacy_violation(programs: object) -> str | None:
    """Return a non-sensitive reason code when public graduate data leaks private readiness."""

    def visit(value: object) -> str | None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized_key = re.sub(r"[^a-z0-9]", "", str(key).casefold())
                if normalized_key in PUBLIC_GRADUATE_PRIVATE_READINESS_KEYS:
                    return "private_readiness_field"
                nested = visit(item)
                if nested is not None:
                    return nested
            return None
        if isinstance(value, (list, tuple)):
            for item in value:
                nested = visit(item)
                if nested is not None:
                    return nested
            return None
        if isinstance(value, str):
            normalized_text = re.sub(r"\s+", " ", value.casefold())
            if any(pattern.search(normalized_text) for pattern in PUBLIC_GRADUATE_PRIVATE_READINESS_PATTERNS):
                return "private_readiness_phrase"
        return None

    return visit(programs)


def validate_graduate_claim_evidence(programs: list[dict]) -> dict[str, int]:
    """Reject fabricated zero semantics and derive coverage from explicit claim states."""
    state_rows: list[dict[str, str]] = []
    for index, program in enumerate(programs):
        research = program.get("publicResearch") if isinstance(program, dict) else None
        claims = research.get("claimEvidence") if isinstance(research, dict) else None
        if not isinstance(claims, dict) or set(claims) != set(GRADUATE_EVIDENCE_AXES):
            raise SystemExit(f"graduate claim evidence contract is missing or incomplete at programme {index}")

        faculty = research.get("faculty") if isinstance(research.get("faculty"), list) else []
        actual_counts = {
            "faculty": len(faculty),
            "recentPapers": sum(
                len(person.get("recentPapers") or [])
                for person in faculty
                if isinstance(person, dict) and isinstance(person.get("recentPapers") or [], list)
            ),
            "fundedProjects": len(research.get("recentProjects"))
            if isinstance(research.get("recentProjects"), list)
            else 0,
            "graduateDestinations": len(research.get("graduateDestinations"))
            if isinstance(research.get("graduateDestinations"), list)
            else 0,
            "testimonials": len(research.get("graduateTestimonials"))
            if isinstance(research.get("graduateTestimonials"), list)
            else 0,
        }
        row: dict[str, str] = {}
        for axis in GRADUATE_EVIDENCE_AXES:
            claim = claims.get(axis)
            if not isinstance(claim, dict):
                raise SystemExit(f"graduate claim evidence contract has a malformed {axis} axis")
            evidence_state = str(claim.get("evidenceState", ""))
            expected_claim_state = GRADUATE_CLAIM_STATE_BY_EVIDENCE.get(evidence_state)
            if expected_claim_state is None or claim.get("claimState") != expected_claim_state:
                raise SystemExit(f"graduate claim evidence contract has an invalid {axis} state")
            sources = claim.get("sources")
            if not isinstance(sources, list):
                raise SystemExit(f"graduate claim evidence contract has malformed {axis} sources")
            actual_count = actual_counts[axis]
            if evidence_state == "present":
                if actual_count <= 0 or claim.get("recordCount") != actual_count:
                    raise SystemExit(f"graduate claim evidence contract count mismatch for {axis}")
            elif evidence_state in {"not_researched", "reviewed_no_qualifying"}:
                if actual_count != 0 or claim.get("recordCount") is not None or sources:
                    raise SystemExit(f"graduate claim evidence contract fabricates an empty {axis} result")
            else:
                if actual_count != 0 or claim.get("recordCount") != 0 or not sources:
                    raise SystemExit(f"graduate claim evidence contract lacks sourced absence for {axis}")
                if any(
                    not isinstance(source, dict) or not HTTP_URL.match(str(source.get("url", "")))
                    for source in sources
                ):
                    raise SystemExit(f"graduate claim evidence contract has invalid {axis} source evidence")
            row[axis] = evidence_state
        state_rows.append(row)

    evidence_flags = {
        axis: [row[axis] == "present" for row in state_rows]
        for axis in GRADUATE_EVIDENCE_AXES
    }
    any_flags = [any(row[axis] == "present" for axis in GRADUATE_EVIDENCE_AXES) for row in state_rows]
    return {
        "totalPrograms": len(programs),
        "programsWithAnyEvidence": sum(any_flags),
        "programsWithFaculty": sum(evidence_flags["faculty"]),
        "programsWithRecentPapers": sum(evidence_flags["recentPapers"]),
        "programsWithFundedProjects": sum(evidence_flags["fundedProjects"]),
        "programsWithGraduateDestinations": sum(evidence_flags["graduateDestinations"]),
        "programsWithTestimonials": sum(evidence_flags["testimonials"]),
        "unresearchedPrograms": sum(
            all(row[axis] == "not_researched" for axis in GRADUATE_EVIDENCE_AXES)
            for row in state_rows
        ),
    }


def validate_graduate_data_lineage(
    lineage: object,
    programs: list[dict],
    funding: list[dict],
    *,
    source_roots: Mapping[str, Path] | None = None,
) -> None:
    """GOV-257: reject payload-only lineage and malformed source provenance."""
    if not isinstance(lineage, dict):
        raise SystemExit("snapshot must declare graduateDataLineage")
    canonical_payload = json.dumps(
        {"programs": programs, "funding": funding},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if lineage.get("schemaVersion") != GRADUATE_LINEAGE_METHOD_VERSION or lineage.get("methodVersion") != GRADUATE_LINEAGE_METHOD_VERSION:
        raise SystemExit("graduate lineage method version mismatch")
    if lineage.get("producer") != "career-job-compass/scripts/build_snapshot.py":
        raise SystemExit("graduate lineage producer mismatch")
    if lineage.get("artifact") != "career-job-compass/data/app-data.json":
        raise SystemExit("graduate lineage artifact mismatch")
    if lineage.get("producerCodeSha256") != _file_sha256(ROOT / "scripts" / "build_snapshot.py"):
        raise SystemExit("graduate lineage producer code mismatch")
    expected_payload_digest = hashlib.sha256(canonical_payload).hexdigest()
    if not HEX64.fullmatch(str(lineage.get("payloadSha256", ""))):
        raise SystemExit("graduate lineage payload digest is malformed")
    if lineage.get("payloadSha256") != expected_payload_digest:
        raise SystemExit("graduateDataLineage does not match the released graduate payload")
    if lineage.get("programCount") != len(programs) or lineage.get("fundingCount") != len(funding):
        raise SystemExit("graduateDataLineage counts do not match the released graduate payload")
    for key in ("producerRepositoryCommit", "sourceRepositoryCommit"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(lineage.get(key, ""))):
            raise SystemExit(f"graduate lineage {key} is malformed")

    source_artifacts = lineage.get("sourceArtifacts")
    if not isinstance(source_artifacts, list):
        raise SystemExit("graduate lineage sourceArtifacts must be a list")
    required_roles = {"catalog", "programDiscovery", "researchEvidence"}
    roles = [item.get("role") for item in source_artifacts if isinstance(item, dict)]
    if len(source_artifacts) != len(required_roles) or set(roles) != required_roles or len(roles) != len(set(roles)):
        raise SystemExit("graduate lineage source roles mismatch")
    for item in source_artifacts:
        path = str(item.get("path", ""))
        if (
            not path
            or "\\" in path
            or path.startswith(("/", "./"))
            or re.match(r"^[A-Za-z]:", path)
            or ".." in Path(path).parts
        ):
            raise SystemExit("graduate lineage source path is not normalized")
        if not HEX64.fullmatch(str(item.get("sha256", ""))):
            raise SystemExit("graduate lineage source digest is malformed")

    canonical_sources = json.dumps(
        source_artifacts,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected_manifest_digest = hashlib.sha256(canonical_sources).hexdigest()
    if not HEX64.fullmatch(str(lineage.get("sourceManifestSha256", ""))):
        raise SystemExit("graduate lineage source manifest digest is malformed")
    if lineage.get("sourceManifestSha256") != expected_manifest_digest:
        raise SystemExit("graduate lineage source manifest does not match source artifacts")

    generation_inputs = {
        "methodVersion": GRADUATE_LINEAGE_METHOD_VERSION,
        "producerCodeSha256": lineage.get("producerCodeSha256"),
        "producerRepositoryCommit": lineage.get("producerRepositoryCommit"),
        "sourceRepositoryCommit": lineage.get("sourceRepositoryCommit"),
        "sourceManifestSha256": expected_manifest_digest,
        "payloadSha256": expected_payload_digest,
    }
    expected_generation_digest = hashlib.sha256(
        json.dumps(generation_inputs, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if not HEX64.fullmatch(str(lineage.get("generationInputsSha256", ""))):
        raise SystemExit("graduate lineage generation input digest is malformed")
    if lineage.get("generationInputsSha256") != expected_generation_digest:
        raise SystemExit("graduate lineage generation inputs do not match the released payload")

    if source_roots:
        for item in source_artifacts:
            path_parts = str(item["path"]).split("/")
            root = source_roots.get(path_parts[0])
            if root is None:
                continue
            resolved_root = Path(root).resolve()
            try:
                source_path = resolved_root.joinpath(*path_parts[1:]).resolve(strict=True)
                source_path.relative_to(resolved_root)
            except (OSError, ValueError):
                raise SystemExit("graduate lineage source digest mismatch") from None
            if not source_path.is_file() or _file_sha256(source_path) != item.get("sha256"):
                raise SystemExit("graduate lineage source digest mismatch")


def main() -> None:
    requirement_check = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_requirements.py"), "--root", str(ROOT)],
        check=False,
    )
    if requirement_check.returncode:
        raise SystemExit("check_requirements.py failed")

    for relative in (
        "index.html", "styles.css", "app.js", "sw.js", "manifest.webmanifest",
        "icons/app-icon.svg", "icons/app-icon-maskable.svg", "icons/apple-touch-icon.png",
        "assets/route-map-editorial-v2.webp", "assets/study-steps-editorial-v2.webp",
        "data/app-data.json", "data/catalog-source.json",
        "supabase/migrations/202607280003_create_refresh_queue.sql",
        "requirements/ledger.yaml", "scripts/check_requirements.py", "DESIGN.md",
    ):
        require(ROOT / relative, relative)

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for marker in (
        "manifest.webmanifest", "apple-touch-icon", "apple-mobile-web-app-capable",
        "apple-mobile-web-app-status-bar-style", "mainContent", "filterSheet", "dossier", "bottom-nav", "queueFilter",
    ):
        if marker not in html:
            raise SystemExit(f"index.html missing marker: {marker}")

    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    if manifest.get("display") != "standalone" or not manifest.get("start_url") or manifest.get("scope") != "./":
        raise SystemExit("manifest must declare standalone display, start_url, and relative scope")

    snapshot = validate_public_data_artifacts(ROOT)
    if (ROOT / "_site").exists():
        validate_release_privacy_scan(ROOT, ROOT / "_site")
    app_source = (ROOT / "app.js").read_text(encoding="utf-8")
    # DATA-232: provenance sentinels remain machine-readable, but an internal
    # graduate evidence review state must never leak into the public UI or data.
    internal_review_label = "유형 재검증 필요"
    if internal_review_label in app_source or internal_review_label in json.dumps(snapshot, ensure_ascii=False):
        raise SystemExit("public artifact exposes an internal graduate evidence review state")
    if "refresh_runs" not in app_source or "refresh-bridge.json" in app_source or "tailscale" in app_source.casefold():
        raise SystemExit("mobile refresh must use the Supabase queue without a private bridge URL")
    jobs = snapshot.get("jobs")
    review_queue = snapshot.get("reviewQueue")
    programs = snapshot.get("programs")
    funding = snapshot.get("funding")
    if snapshot.get("schemaVersion", 0) < 3:
        raise SystemExit("snapshot must use schemaVersion 3 or later")
    if snapshot.get("releaseVersion") != "decision-support-v2":
        raise SystemExit("snapshot must declare decision-support-v2")
    if not isinstance(jobs, list) or not jobs:
        raise SystemExit("snapshot must contain title-grounded job exploration or action candidates")
    validate_lifestyle_discovery(snapshot, jobs)
    sectors = snapshot.get("sectors")
    if not isinstance(sectors, list) or len(sectors) != 20:
        raise SystemExit("snapshot must preserve the 20-sector job inventory")
    if not isinstance(review_queue, list) or len(review_queue) > 3:
        raise SystemExit("snapshot review queue must contain at most three confirmed actions")
    if not isinstance(programs, list) or len(programs) < 90:
        raise SystemExit("snapshot must contain the full graduate research catalog")
    # SEC-298: public programme research may contain institution requirements,
    # but never this applicant's readiness, eligibility conclusion, or gap plan.
    if public_graduate_privacy_violation(programs) is not None:
        raise SystemExit("public graduate catalog contains private applicant-readiness data")
    if not isinstance(funding, list) or len(funding) < 186:
        raise SystemExit("snapshot must contain the full funding research catalog")
    if any(not valid_decision_support(job, "job") for job in jobs):
        raise SystemExit("every job must include the decision-support contract")
    if any(not valid_decision_support(program, "program") for program in programs):
        raise SystemExit("every programme must include the decision-support contract")
    expected_graduate_coverage = validate_graduate_claim_evidence(programs)
    # DATA-227/GOV-257: bind the released graduate projection to exact sources.
    lineage_roots = {"career-job-compass": ROOT}
    job_search_root = ROOT.parent / "job_search"
    if job_search_root.is_dir():
        lineage_roots["job_search"] = job_search_root
    validate_graduate_data_lineage(
        snapshot.get("graduateDataLineage"),
        programs,
        funding,
        source_roots=lineage_roots,
    )
    if {job.get("queue") for job in jobs} - {"verify", "hold", "apply", "stretch"}:
        raise SystemExit("public jobs must only use active public V4 queues")
    stats = snapshot.get("stats")
    if not isinstance(stats, dict):
        raise SystemExit("snapshot must include public stats")
    market_counts = stats.get("marketCounts")
    if not isinstance(market_counts, dict) or set(market_counts) != {"domestic", "overseas", "unknown"}:
        raise SystemExit("snapshot stats must include domestic, overseas, and unknown job counts")
    if any(not isinstance(market_counts[market], int) or market_counts[market] < 0 for market in market_counts):
        raise SystemExit("snapshot market counts must be non-negative integers")
    if sum(market_counts.values()) != len(jobs):
        raise SystemExit("snapshot market counts must match the public job set")
    if stats.get("recommendationSurface") not in {"ranked", "review_inventory", "exploration_only"}:
        raise SystemExit("snapshot must declare whether candidates are ranked, actions, or interest exploration")
    if stats.get("recommendationSource") not in {"baseline", "personalized"}:
        raise SystemExit("snapshot must declare its recommendation source")
    if not isinstance(stats.get("jobDataAsOf"), str) or not stats["jobDataAsOf"]:
        raise SystemExit("snapshot must expose the job data date separately from graduate research")
    if any(item.get("market") not in {"domestic", "overseas", "unknown"} for item in jobs + programs + funding):
        raise SystemExit("every public record must declare a verified domestic/overseas market or unknown")
    if any(not job.get("url") for job in jobs):
        raise SystemExit("every public action candidate must retain its official URL")
    if any(job.get("discoveryTier") not in {"action", "explore"} for job in jobs):
        raise SystemExit("every public job must be an action candidate or title-grounded exploration item")
    if any(job.get("discoveryTier") == "explore" and not job.get("discoveryReason") for job in jobs):
        raise SystemExit("exploration candidates must disclose why they are shown")
    if any(not isinstance(job.get("sectors"), list) or not job["sectors"] for job in jobs):
        raise SystemExit("every public job must retain one or more sector labels")
    if any(
        float(job.get("minimumExperienceYears", 0) or 0) >= 2
        or job.get("publicEligibility") == "excluded"
        for job in jobs
    ):
        raise SystemExit("public jobs must exclude explicit multi-year experience requirements")
    if any(support_only_title(job.get("title")) for job in jobs):
        raise SystemExit("public jobs must exclude generic support-only titles")
    if any(experienced_only_title(job.get("title")) for job in jobs):
        raise SystemExit("public jobs must exclude experienced-only titles")
    if any(item.get("applicationStatus") not in {"open", "prepare", "research"} for item in programs):
        raise SystemExit("every programme must disclose whether it is open, preparation, or research")
    public_projects = [
        project for item in programs
        for project in (item.get("publicResearch") or {}).get("recentProjects", [])
    ]
    if contains_non_contract_research(public_projects):
        raise SystemExit("graduate research contracts contain editorial or publication-inferred records")
    # DATA-220: the mobile coverage panel must be derived from the records it describes.
    coverage = snapshot.get("graduateEvidenceCoverage")
    if not isinstance(coverage, dict) or coverage.get("totalPrograms") != len(programs):
        raise SystemExit("graduate evidence coverage denominator must match the public programme set")
    if coverage != expected_graduate_coverage:
        raise SystemExit("graduateEvidenceCoverage is stale or inconsistent with public programme evidence")
    if stats["recommendationSurface"] == "exploration_only" and review_queue:
        raise SystemExit("exploration-only snapshots must not imply an action-ready review queue")
    if any(not item.get("officialUrl") and item.get("verification") != "official_search_required" for item in programs + funding):
        raise SystemExit("research records without an official URL must explicitly require official discovery")
    if contains_forbidden_key(snapshot):
        raise SystemExit("snapshot contains a private or application-state field")
    print(f"release check ok: {len(jobs)} public job candidates, {len(programs)} programs, {len(funding)} funding opportunities")


if __name__ == "__main__":
    main()

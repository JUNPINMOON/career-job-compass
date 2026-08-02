"""Dependency-free release checks for the static Career Compass PWA."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIFESTYLE_METHOD_VERSION = "lifestyle-evidence-v2"
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
        "busan": ("busanWorkplace",),
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


def validate_public_privacy_boundary(snapshot: dict, jobs: list[dict]) -> None:
    """DATA-248: public snapshot contains no authenticated preference data."""
    stats = snapshot.get("stats") if isinstance(snapshot.get("stats"), dict) else {}
    preference_summary = stats.get("preferenceSummary")
    if not isinstance(preference_summary, dict):
        raise SystemExit("public snapshot preferenceSummary must be present and anonymous")
    expected_zero_fields = ("rowCount", "likedCount", "dislikedCount")
    if any(preference_summary.get(field) != 0 for field in expected_zero_fields):
        raise SystemExit("public snapshot contains authenticated preference data")
    if preference_summary.get("digest") is not None:
        raise SystemExit("public snapshot contains authenticated preference data")
    if stats.get("recommendationSource") != "baseline":
        raise SystemExit("public snapshot contains authenticated preference data")
    if snapshot.get("savedJobs") != []:
        raise SystemExit("public snapshot contains authenticated preference data")
    discovery = stats.get("preferenceDiscovery")
    if not isinstance(discovery, dict) or discovery.get("current") is not False:
        raise SystemExit("public snapshot contains authenticated preference data")
    for field in ("evaluatedCandidateCount", "positiveCandidateCount", "discoveredCandidateCount"):
        if discovery.get(field) != 0:
            raise SystemExit("public snapshot contains authenticated preference data")
    forbidden_public_fields = {
        "personalization",
        "score",
        "scoreBreakdown",
        "recommendationScore",
        "preferenceSimilarity",
        "matchedFeedback",
        "matchedPreference",
        "preferenceDigest",
        "exactFeedbackOverride",
        "positiveReasonSignals",
        "appliedReasons",
        "likedEvidenceCount",
        "dislikedEvidenceCount",
        "reasonEvidenceCount",
    }

    def contains_authenticated_trace(value: object) -> bool:
        if isinstance(value, dict):
            return any(
                field in forbidden_public_fields or contains_authenticated_trace(item)
                for field, item in value.items()
            )
        if isinstance(value, list):
            return any(contains_authenticated_trace(item) for item in value)
        return False

    if contains_authenticated_trace(jobs) or contains_authenticated_trace(snapshot.get("reviewQueue")):
        raise SystemExit("public snapshot contains authenticated preference data")


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

    snapshot = json.loads((ROOT / "data/app-data.json").read_text(encoding="utf-8"))
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
    validate_public_privacy_boundary(snapshot, jobs)
    validate_lifestyle_discovery(snapshot, jobs)
    sectors = snapshot.get("sectors")
    if not isinstance(sectors, list) or len(sectors) != 20:
        raise SystemExit("snapshot must preserve the 20-sector job inventory")
    if not isinstance(review_queue, list) or len(review_queue) > 3:
        raise SystemExit("snapshot review queue must contain at most three confirmed actions")
    if not isinstance(programs, list) or len(programs) < 90:
        raise SystemExit("snapshot must contain the full graduate research catalog")
    if not isinstance(funding, list) or len(funding) < 186:
        raise SystemExit("snapshot must contain the full funding research catalog")
    if any(not valid_decision_support(job, "job") for job in jobs):
        raise SystemExit("every job must include the decision-support contract")
    if any(not valid_decision_support(program, "program") for program in programs):
        raise SystemExit("every programme must include the decision-support contract")
    # DATA-227: prove that the file being released is the canonical graduate
    # producer artifact, rather than a separately projected look-alike.
    graduate_lineage = snapshot.get("graduateDataLineage")
    canonical_graduate_payload = json.dumps(
        {"programs": programs, "funding": funding},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected_graduate_digest = hashlib.sha256(canonical_graduate_payload).hexdigest()
    if not isinstance(graduate_lineage, dict):
        raise SystemExit("snapshot must declare graduateDataLineage")
    if (
        graduate_lineage.get("payloadSha256") != expected_graduate_digest
        or graduate_lineage.get("programCount") != len(programs)
        or graduate_lineage.get("fundingCount") != len(funding)
    ):
        raise SystemExit("graduateDataLineage does not match the released graduate payload")
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
    programme_research = [
        item.get("publicResearch") if isinstance(item.get("publicResearch"), dict) else {}
        for item in programs
    ]
    faculty_flags = [bool(item.get("faculty")) for item in programme_research]
    paper_flags = [
        any(person.get("recentPapers") for person in item.get("faculty", []) if isinstance(person, dict))
        for item in programme_research
    ]
    project_flags = [bool(item.get("recentProjects")) for item in programme_research]
    outcome_flags = [bool(item.get("graduateDestinations")) for item in programme_research]
    testimonial_flags = [bool(item.get("graduateTestimonials")) for item in programme_research]
    any_flags = [
        any(values)
        for values in zip(faculty_flags, paper_flags, project_flags, outcome_flags, testimonial_flags)
    ]
    expected_coverage = {
        "totalPrograms": len(programs),
        "programsWithAnyEvidence": sum(any_flags),
        "programsWithFaculty": sum(faculty_flags),
        "programsWithRecentPapers": sum(paper_flags),
        "programsWithFundedProjects": sum(project_flags),
        "programsWithGraduateDestinations": sum(outcome_flags),
        "programsWithTestimonials": sum(testimonial_flags),
        "unresearchedPrograms": len(programs) - sum(any_flags),
    }
    if coverage != expected_coverage:
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

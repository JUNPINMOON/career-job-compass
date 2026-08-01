"""Dependency-free release checks for the static Career Compass PWA."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIFESTYLE_METHOD_VERSION = "lifestyle-evidence-v1"
LIFESTYLE_STATUSES = {"confirmed", "claimed", "unknown", "negative"}
LIFESTYLE_LANES = {"jayang_wlb", "busan"}


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


def validate_lifestyle_discovery(snapshot: dict, jobs: list[dict]) -> None:
    """DATA-240: verify the separate lifestyleEvidence contract at release."""
    discovery = snapshot.get("lifestyleDiscovery")
    if not isinstance(discovery, dict):
        raise SystemExit("snapshot must include lifestyleDiscovery")
    if discovery.get("schemaVersion") != LIFESTYLE_METHOD_VERSION:
        raise SystemExit("lifestyleDiscovery schemaVersion mismatch")
    if discovery.get("methodVersion") != LIFESTYLE_METHOD_VERSION:
        raise SystemExit("lifestyleDiscovery methodVersion mismatch")
    if discovery.get("scoreImpact") != "none":
        raise SystemExit("lifestyleDiscovery must not affect recommendation scores")
    if discovery.get("sourceJobCount") != len(jobs):
        raise SystemExit("lifestyleDiscovery sourceJobCount must match released jobs")
    if not isinstance(discovery.get("limitations"), list) or not discovery["limitations"]:
        raise SystemExit("lifestyleDiscovery must disclose limitations")

    digest_source = dict(discovery)
    actual_digest = digest_source.pop("digest", None)
    expected_digest = hashlib.sha256(
        json.dumps(digest_source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if actual_digest != expected_digest:
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
        if not isinstance(axes, dict) or set(axes) != {"jayangCommute", "wlb", "busanWorkplace"}:
            raise SystemExit("lifestyleEvidence must separate commute, WLB, and Busan axes")
        if not isinstance(item_lanes, dict) or set(item_lanes) != LIFESTYLE_LANES:
            raise SystemExit("lifestyleEvidence must expose both lane statuses")
        for axis in axes.values():
            if (
                not isinstance(axis, dict)
                or axis.get("status") not in LIFESTYLE_STATUSES
                or not isinstance(axis.get("summary"), str)
                or not isinstance(axis.get("evidence"), list)
                or not isinstance(axis.get("missing"), list)
            ):
                raise SystemExit("invalid lifestyleEvidence axis")
        if set(item_lanes.values()) - LIFESTYLE_STATUSES:
            raise SystemExit("invalid lifestyleEvidence lane status")
        item_by_id[job_id] = item

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
        expected_counts = {
            status: sum(
                1
                for job_id in review_ids
                if item_by_id[job_id]["lifestyleEvidence"]["lanes"][lane_name] == status
            )
            for status in LIFESTYLE_STATUSES
        }
        if counts != expected_counts or sum(counts.values()) != len(review_ids):
            raise SystemExit("lifestyleDiscovery lane counts do not match reviewIds")
        reviewed_ids.update(review_ids)
    if reviewed_ids != set(item_by_id):
        raise SystemExit("lifestyleDiscovery items must equal the union of lane reviewIds")


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

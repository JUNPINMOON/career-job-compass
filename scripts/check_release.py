"""Dependency-free release checks for the static Career Compass PWA."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
        "data/app-data.json", "data/catalog-source.json", "data/refresh-bridge.json",
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
    bridge = json.loads((ROOT / "data/refresh-bridge.json").read_text(encoding="utf-8"))
    if bridge.get("schemaVersion") != 1 or not isinstance(bridge.get("enabled"), bool) or not isinstance(bridge.get("baseUrl"), str):
        raise SystemExit("refresh bridge must declare schemaVersion, enabled, and baseUrl")
    if bridge["enabled"] and not bridge["baseUrl"].startswith("https://"):
        raise SystemExit("an enabled refresh bridge must use HTTPS")
    jobs = snapshot.get("jobs")
    review_queue = snapshot.get("reviewQueue")
    programs = snapshot.get("programs")
    funding = snapshot.get("funding")
    if snapshot.get("schemaVersion", 0) < 3:
        raise SystemExit("snapshot must use schemaVersion 3 or later")
    if not isinstance(jobs, list) or not jobs:
        raise SystemExit("snapshot must contain title-grounded job exploration or action candidates")
    sectors = snapshot.get("sectors")
    if not isinstance(sectors, list) or len(sectors) != 20:
        raise SystemExit("snapshot must preserve the 20-sector job inventory")
    if not isinstance(review_queue, list) or len(review_queue) > 3:
        raise SystemExit("snapshot review queue must contain at most three confirmed actions")
    if not isinstance(programs, list) or len(programs) < 90:
        raise SystemExit("snapshot must contain the full graduate research catalog")
    if not isinstance(funding, list) or len(funding) < 186:
        raise SystemExit("snapshot must contain the full funding research catalog")
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

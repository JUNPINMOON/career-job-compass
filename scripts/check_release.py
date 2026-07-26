"""Dependency-free release checks for the static Career Compass PWA."""

from __future__ import annotations

import json
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


def main() -> None:
    for relative in (
        "index.html", "styles.css", "app.js", "sw.js", "manifest.webmanifest",
        "icons/app-icon.svg", "icons/app-icon-maskable.svg", "icons/apple-touch-icon.png",
        "assets/route-map-editorial-v2.webp", "assets/study-steps-editorial-v2.webp", "data/app-data.json", "data/refresh-bridge.json", "DESIGN.md",
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
    if stats["recommendationSurface"] == "exploration_only" and review_queue:
        raise SystemExit("exploration-only snapshots must not imply an action-ready review queue")
    if any(not item.get("officialUrl") and item.get("verification") != "official_search_required" for item in programs + funding):
        raise SystemExit("research records without an official URL must explicitly require official discovery")
    if contains_forbidden_key(snapshot):
        raise SystemExit("snapshot contains a private or application-state field")
    print(f"release check ok: {len(jobs)} public job candidates, {len(programs)} programs, {len(funding)} funding opportunities")


if __name__ == "__main__":
    main()

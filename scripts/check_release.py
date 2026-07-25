"""Small dependency-free release checks for the static PWA."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path: Path, label: str) -> None:
    if not path.is_file():
        raise SystemExit(f"missing {label}: {path}")


def main() -> None:
    for relative in (
        "index.html", "styles.css", "app.js", "sw.js", "manifest.webmanifest",
        "icons/app-icon.svg", "icons/app-icon-maskable.svg", "icons/apple-touch-icon.png",
        "assets/route-map-editorial-v2.webp", "assets/study-steps-editorial-v2.webp", "data/app-data.json", "DESIGN.md",
    ):
        require(ROOT / relative, relative)

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for marker in (
        "manifest.webmanifest", "apple-touch-icon", "apple-mobile-web-app-capable",
        "apple-mobile-web-app-status-bar-style", "mainContent", "filterSheet", "dossier", "bottom-nav",
    ):
        if marker not in html:
            raise SystemExit(f"index.html missing marker: {marker}")

    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    if manifest.get("display") != "standalone" or not manifest.get("start_url") or manifest.get("scope") != "./":
        raise SystemExit("manifest must declare standalone display, start_url, and relative scope")

    snapshot = json.loads((ROOT / "data/app-data.json").read_text(encoding="utf-8"))
    jobs = snapshot.get("jobs")
    review_queue = snapshot.get("reviewQueue")
    study = snapshot.get("study")
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 80:
        raise SystemExit("snapshot must contain 1-80 compact jobs")
    if not isinstance(study, list) or not 1 <= len(study) <= 16:
        raise SystemExit("snapshot must contain 1-16 study routes")
    if not isinstance(review_queue, list) or len(review_queue) > 3:
        raise SystemExit("snapshot must contain a 0-3 item review queue")
    if snapshot.get("schemaVersion", 0) < 2:
        raise SystemExit("snapshot must use schemaVersion 2 or later")
    if any(
        "water quality" in str(job.get("title", "")).lower()
        for job in (*jobs, *review_queue)
    ):
        raise SystemExit("snapshot must not publish explicitly excluded water-quality roles")
    companies = [str(job.get("company", "")).strip().lower() for job in jobs]
    if len(companies) != len(set(companies)):
        raise SystemExit("snapshot must publish at most one job per company")
    job_ids = {job.get("id") for job in jobs}
    if any(job.get("id") not in job_ids for job in review_queue):
        raise SystemExit("review queue items must be present in the public jobs collection")
    if any(job.get("status") != "확인 필요" for job in review_queue):
        raise SystemExit("review queue must contain only source-verification candidates")
    forbidden = {"description", "preferred_summary", "credentials", "crm", "token", "email"}
    for collection in (jobs, review_queue, study):
        for item in collection:
            if forbidden.intersection(item):
                raise SystemExit("snapshot contains a prohibited public field")
    print(f"release check ok: {len(jobs)} jobs, {len(review_queue)} review queue items, {len(study)} study routes")


if __name__ == "__main__":
    main()

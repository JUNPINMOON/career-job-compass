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
    study = snapshot.get("study")
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 80:
        raise SystemExit("snapshot must contain 1-80 compact jobs")
    if not isinstance(study, list) or not 1 <= len(study) <= 16:
        raise SystemExit("snapshot must contain 1-16 study routes")
    forbidden = {"description", "preferred_summary", "credentials", "crm", "token", "email"}
    for collection in (jobs, study):
        for item in collection:
            if forbidden.intersection(item):
                raise SystemExit("snapshot contains a prohibited public field")
    print(f"release check ok: {len(jobs)} jobs, {len(study)} study routes")


if __name__ == "__main__":
    main()

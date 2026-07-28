"""Merge source-backed graduate evidence and audit the complete programme set.

The canonical input remains job_search/config/grad_school_programs.researched.json.
Evidence patches are ordinary JSON arrays keyed by university and programme, so
there is no fixed target count. The output is always written explicitly and can
be inspected before replacing the already-dirty canonical source.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


VERIFIED_ON = "2026-07-28"


def program_key(record: dict[str, Any]) -> tuple[str, str]:
    return (
        str(record.get("university", "")).strip().casefold(),
        str(record.get("program", "")).strip().casefold(),
    )


def merge_named(existing: Any, additions: Any, key: str) -> list[Any]:
    merged = list(existing) if isinstance(existing, list) else []
    positions = {
        str(item.get(key, "")).strip().casefold(): index
        for index, item in enumerate(merged)
        if isinstance(item, dict) and item.get(key)
    }
    for addition in additions if isinstance(additions, list) else []:
        if not isinstance(addition, dict) or not addition.get(key):
            continue
        identity = str(addition.get(key, "")).strip().casefold()
        if identity in positions:
            current = merged[positions[identity]]
            merged[positions[identity]] = {**current, **addition}
        else:
            positions[identity] = len(merged)
            merged.append(addition)
    return merged


def read_array(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, list):
        raise ValueError(f"Expected a JSON array: {path}")
    return [item for item in value if isinstance(item, dict)]


def merge_patch(record: dict[str, Any], patch: dict[str, Any]) -> None:
    record["faculty"] = merge_named(record.get("faculty"), patch.get("faculty"), "name")
    record["graduate_destinations"] = merge_named(
        record.get("graduate_destinations"),
        patch.get("graduate_destinations"),
        "destination",
    )
    record["graduate_testimonials"] = merge_named(
        record.get("graduate_testimonials"),
        patch.get("graduate_testimonials"),
        "person",
    )
    for field in (
        "application_deadline",
        "official_verification_status",
        "source_urls",
        "keywords",
    ):
        if field in patch:
            record[field] = patch[field]
    record["faculty_last_verified"] = str(patch.get("verified_on") or VERIFIED_ON)
    record["last_verified"] = str(patch.get("verified_on") or VERIFIED_ON)
    record["faculty_evidence_status"] = (
        "source_backed_official_profiles"
        if record.get("faculty")
        else "public_research_evidence_missing"
    )


def validate_new_program(record: dict[str, Any], source_path: Path) -> None:
    """DATA-221: admit discoveries only with an official course and faculty trail."""
    university = str(record.get("university", "")).strip()
    program = str(record.get("program", "")).strip()
    official_url = str(record.get("url", "")).strip()
    if not university or not program:
        raise ValueError(f"New programme lacks university or program: {source_path}")
    if not official_url.startswith("https://"):
        raise ValueError(f"New programme lacks an HTTPS official URL: {university} / {program}")
    if str(record.get("official_verification_status", "")).strip() != "verified":
        raise ValueError(f"New programme is not officially verified: {university} / {program}")
    faculty = record.get("faculty")
    if not isinstance(faculty, list) or not faculty:
        raise ValueError(f"New programme lacks faculty evidence: {university} / {program}")
    has_official_faculty_source = any(
        isinstance(person, dict)
        and any(
            isinstance(source, dict)
            and str(source.get("source_type", "")).startswith("official_")
            and str(source.get("url", "")).startswith("https://")
            for source in person.get("profile_sources", [])
        )
        for person in faculty
    )
    if not has_official_faculty_source:
        raise ValueError(
            f"New programme lacks a typed official faculty source: {university} / {program}"
        )


def is_recent_five_years(value: Any) -> bool:
    years = [int(year) for year in re.findall(r"\b20\d{2}\b", str(value or ""))]
    return not years or max(years) >= datetime.now().year - 4


def has_recent_papers(record: dict[str, Any]) -> bool:
    return any(
        isinstance(person, dict)
        and any(
            isinstance(paper, dict) and paper.get("title") and is_recent_five_years(paper.get("year"))
            for paper in person.get("recent_papers", [])
        )
        for person in record.get("faculty", [])
    )


def has_funded_projects(record: dict[str, Any]) -> bool:
    non_contract_markers = (
        "not a funded grant",
        "editorial",
        "guest editor",
        "special issue",
        "publication dates",
        "specific grant id not disclosed",
    )
    return any(
        isinstance(person, dict)
        and any(
            isinstance(project, dict)
            and project.get("title")
            and is_recent_five_years(project.get("period"))
            and not any(
                marker in " ".join(
                    str(project.get(field, "")).strip().lower()
                    for field in ("title", "funder", "period")
                )
                for marker in non_contract_markers
            )
            for project in person.get("recent_projects", [])
        )
        for person in record.get("faculty", [])
    )


def build_coverage_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    """DATA-219: audit every canonical programme, never a fixed expansion list."""
    unresearched = [
        {
            "university": str(record.get("university", "")).strip(),
            "program": str(record.get("program", "")).strip(),
        }
        for record in records
        if not any(
            (
                record.get("faculty"),
                has_recent_papers(record),
                has_funded_projects(record),
                record.get("graduate_destinations"),
                record.get("graduate_testimonials"),
            )
        )
    ]
    return {
        "generatedAt": VERIFIED_ON,
        "totalPrograms": len(records),
        "programsWithFaculty": sum(bool(record.get("faculty")) for record in records),
        "programsWithRecentPapers": sum(has_recent_papers(record) for record in records),
        "programsWithFundedProjects": sum(has_funded_projects(record) for record in records),
        "programsWithGraduateDestinations": sum(
            bool(record.get("graduate_destinations")) for record in records
        ),
        "programsWithTestimonials": sum(
            bool(record.get("graduate_testimonials")) for record in records
        ),
        "unresearchedPrograms": unresearched,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--evidence",
        type=Path,
        action="append",
        default=[],
        help="JSON array of evidence patches keyed by university and program; repeatable.",
    )
    parser.add_argument(
        "--new-programs",
        type=Path,
        action="append",
        default=[],
        help="JSON array of new officially verified programmes; repeatable.",
    )
    parser.add_argument("--coverage-output", type=Path)
    args = parser.parse_args()

    records = read_array(args.input)
    by_key = {program_key(record): record for record in records}
    if len(by_key) != len(records):
        raise ValueError("Canonical programme source contains duplicate university/program keys")
    added_programs = 0
    for discovery_path in args.new_programs:
        for discovery in read_array(discovery_path):
            validate_new_program(discovery, discovery_path)
            key = program_key(discovery)
            if key in by_key:
                raise ValueError(
                    f"New programme duplicates an existing key: "
                    f"{discovery.get('university')} / {discovery.get('program')}"
                )
            discovery.setdefault("faculty_last_verified", VERIFIED_ON)
            discovery.setdefault("last_verified", VERIFIED_ON)
            discovery.setdefault("faculty_evidence_status", "source_backed_official_profiles")
            records.append(discovery)
            by_key[key] = discovery
            added_programs += 1
    applied: set[tuple[str, str]] = set()
    for patch_path in args.evidence:
        for patch in read_array(patch_path):
            key = program_key(patch)
            if not all(key):
                raise ValueError(f"Evidence patch lacks university or program: {patch_path}")
            record = by_key.get(key)
            if record is None:
                raise ValueError(
                    f"Evidence target not found: {patch.get('university')} / {patch.get('program')}"
                )
            merge_patch(record, patch)
            applied.add(key)

    coverage = build_coverage_report(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.coverage_output:
        args.coverage_output.parent.mkdir(parents=True, exist_ok=True)
        args.coverage_output.write_text(
            json.dumps(coverage, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        f"Audited {coverage['totalPrograms']} programmes; "
        f"added {added_programs} new programmes; "
        f"merged {len(applied)} evidence patches -> {args.output}"
    )
    print(
        "Coverage: "
        f"faculty {coverage['programsWithFaculty']}/{coverage['totalPrograms']}, "
        f"papers {coverage['programsWithRecentPapers']}/{coverage['totalPrograms']}, "
        f"projects {coverage['programsWithFundedProjects']}/{coverage['totalPrograms']}, "
        f"outcomes {coverage['programsWithGraduateDestinations']}/{coverage['totalPrograms']}, "
        f"testimonials {coverage['programsWithTestimonials']}/{coverage['totalPrograms']}; "
        f"unresearched {len(coverage['unresearchedPrograms'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

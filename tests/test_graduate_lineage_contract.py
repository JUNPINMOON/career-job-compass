from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_snapshot = _module("career_build_snapshot", ROOT / "scripts" / "build_snapshot.py")
check_release = _module("career_check_release", ROOT / "scripts" / "check_release.py")


def test_shortlist_consumer_requires_the_exact_enriched_research_source(tmp_path: Path) -> None:
    research_path = tmp_path / "config" / "grad_school_programs.researched.json"
    research_path.parent.mkdir(parents=True)
    research_records = [
        {"university": "One", "program": "Water AI"},
        {"university": "Two", "program": "Hydroinformatics"},
    ]
    research_bytes = json.dumps(research_records, ensure_ascii=False).encode("utf-8")
    research_path.write_bytes(research_bytes)
    shortlist = {
        "source_lineage": {
            "source_path": "config/grad_school_programs.researched.json",
            "source_sha256": hashlib.sha256(research_bytes).hexdigest(),
            "source_program_count": 2,
            "shortlist_program_count": 1,
        },
        "programs": [{"university": "One", "program": "Water AI"}],
    }

    build_snapshot._validate_shortlist_source_lineage(shortlist, research_path)

    changed = copy.deepcopy(shortlist)
    changed["source_lineage"]["source_program_count"] = 3
    with pytest.raises(ValueError, match="source count mismatch"):
        build_snapshot._validate_shortlist_source_lineage(changed, research_path)


def test_producer_code_digest_accepts_git_line_ending_normalization(tmp_path: Path) -> None:
    source = tmp_path / "build_snapshot.py"
    source.write_bytes(b"one\r\ntwo\r\n")

    lf_digest = hashlib.sha256(b"one\ntwo\n").hexdigest()

    assert lf_digest in check_release._file_sha256_variants(source)
    assert build_snapshot._text_file_sha256(source) == lf_digest


def test_graduate_lineage_binds_every_source_role_and_validates(tmp_path: Path) -> None:
    app_root = tmp_path / "career-job-compass"
    source_root = tmp_path / "job_search"
    catalog = app_root / "data" / "catalog-source.json"
    shortlist = source_root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json"
    research = source_root / "config" / "grad_school_programs.researched.json"
    for path, value in ((catalog, "catalog"), (shortlist, "shortlist"), (research, "research")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    payload = {"programs": [{"id": "p1"}], "funding": [{"id": "f1"}]}
    with patch.object(build_snapshot, "_repository_commit", side_effect=["1" * 40, "2" * 40]):
        lineage = build_snapshot._graduate_data_lineage(
            payload,
            app_root=app_root,
            job_search_root=source_root,
            catalog_source=catalog,
            shortlist_source=shortlist,
            research_source=research,
        )

    assert lineage["methodVersion"] == "graduate-lineage-v2"
    assert {item["role"] for item in lineage["sourceArtifacts"]} == {
        "catalog",
        "programDiscovery",
        "researchEvidence",
    }
    assert len(lineage["sourceManifestSha256"]) == 64
    assert len(lineage["generationInputsSha256"]) == 64
    roots = {
        "career-job-compass": app_root,
        "job_search": source_root,
    }
    check_release.validate_graduate_data_lineage(
        lineage,
        payload["programs"],
        payload["funding"],
        source_roots=roots,
    )

    catalog.write_text("changed after generation", encoding="utf-8")
    with pytest.raises(SystemExit, match="graduate lineage source digest mismatch"):
        check_release.validate_graduate_data_lineage(
            lineage,
            payload["programs"],
            payload["funding"],
            source_roots=roots,
        )


def test_graduate_lineage_rejects_a_missing_source_role(tmp_path: Path) -> None:
    app_root = tmp_path / "career-job-compass"
    source_root = tmp_path / "job_search"
    catalog = app_root / "data" / "catalog-source.json"
    shortlist = source_root / "artifacts" / "grad_school" / "grad_school_shortlist_latest.json"
    research = source_root / "config" / "grad_school_programs.researched.json"
    for path in (catalog, shortlist, research):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source", encoding="utf-8")
    payload = {"programs": [], "funding": []}
    with patch.object(build_snapshot, "_repository_commit", side_effect=["1" * 40, "2" * 40]):
        lineage = build_snapshot._graduate_data_lineage(
            payload,
            app_root=app_root,
            job_search_root=source_root,
            catalog_source=catalog,
            shortlist_source=shortlist,
            research_source=research,
        )
    invalid = copy.deepcopy(lineage)
    invalid["sourceArtifacts"].pop()
    with pytest.raises(SystemExit, match="graduate lineage source roles mismatch"):
        check_release.validate_graduate_data_lineage(invalid, [], [])


def test_release_rejects_missing_graduate_claim_evidence() -> None:
    programmes = [
        {
            "publicResearch": {
                "faculty": [],
                "recentProjects": [],
                "graduateDestinations": [],
                "graduateTestimonials": [],
            }
        }
    ]

    with pytest.raises(SystemExit, match="graduate claim evidence contract"):
        check_release.validate_graduate_claim_evidence(programmes)

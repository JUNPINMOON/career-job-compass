from __future__ import annotations

import ast
import copy
import io
import importlib.util
import json
import tarfile
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_release = _module("career_public_privacy_check_release", ROOT / "scripts" / "check_release.py")


def _anonymous_snapshot() -> dict:
    return {
        "stats": {
            "preferenceSummary": {
                "rowCount": 0,
                "likedCount": 0,
                "dislikedCount": 0,
                "digest": None,
            },
            "preferenceDiscovery": {
                "current": False,
                "evaluatedCandidateCount": 0,
                "positiveCandidateCount": 0,
                "discoveredCandidateCount": 0,
            },
            "recommendationSource": "baseline",
        },
        "savedJobs": [],
        "jobs": [{"id": "job-1", "title": "Public candidate"}],
        "reviewQueue": [],
        # Public catalogue scores are not authenticated preference scores.
        "programs": [{"id": "program-1", "score": 80}],
        "funding": [{"id": "funding-1", "score": 70}],
    }


def _write_snapshot(path: Path, snapshot: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot), encoding="utf-8")


def test_anonymous_aggregate_shape_is_not_mistaken_for_personal_data() -> None:
    snapshot = _anonymous_snapshot()

    check_release.validate_public_privacy_boundary(snapshot, snapshot["jobs"])


@pytest.mark.parametrize(
    ("mutate", "detail"),
    [
        (lambda value: value["savedJobs"].append({"id": "private-liked-job"}), "savedJobs"),
        (lambda value: value["stats"]["preferenceSummary"].update({"likedCount": 1}), "likedCount"),
        (
            lambda value: value["stats"]["preferenceSummary"].update(
                {"reasonCounts": {"work_conditions": 1}}
            ),
            "reasonCounts",
        ),
        (lambda value: value["jobs"][0].update({"preference_digest": "private"}), "preference_digest"),
        (lambda value: value["programs"][0].update({"owner_id": "private"}), "owner_id"),
    ],
)
def test_actual_private_values_or_keys_fail_closed(mutate, detail: str) -> None:
    snapshot = copy.deepcopy(_anonymous_snapshot())
    mutate(snapshot)

    with pytest.raises(SystemExit, match="public snapshot contains authenticated preference data"):
        check_release.validate_public_privacy_boundary(snapshot, snapshot["jobs"])


def test_release_gate_checks_canonical_and_existing_site_copy(tmp_path: Path) -> None:
    canonical = _anonymous_snapshot()
    leaked_site_copy = copy.deepcopy(canonical)
    leaked_site_copy["jobs"][0]["personalization"] = {"preferenceDigest": "private"}
    _write_snapshot(tmp_path / "data" / "app-data.json", canonical)
    _write_snapshot(tmp_path / "_site" / "data" / "app-data.json", leaked_site_copy)

    with pytest.raises(SystemExit, match=r"_site/data/app-data\.json"):
        check_release.validate_public_data_artifacts(tmp_path)


def test_release_gate_accepts_anonymous_canonical_and_site_copy(tmp_path: Path) -> None:
    snapshot = _anonymous_snapshot()
    _write_snapshot(tmp_path / "data" / "app-data.json", snapshot)
    _write_snapshot(tmp_path / "_site" / "data" / "app-data.json", snapshot)

    assert check_release.validate_public_data_artifacts(tmp_path) == snapshot


def test_existing_site_data_copy_must_match_canonical_snapshot(tmp_path: Path) -> None:
    canonical = _anonymous_snapshot()
    stale_site_copy = copy.deepcopy(canonical)
    stale_site_copy["jobs"][0]["title"] = "Old public candidate"
    _write_snapshot(tmp_path / "data" / "app-data.json", canonical)
    _write_snapshot(tmp_path / "_site" / "data" / "app-data.json", stale_site_copy)

    with pytest.raises(SystemExit, match=r"_site/data/app-data\.json is stale"):
        check_release.validate_public_data_artifacts(tmp_path)


def test_existing_site_without_verifiable_data_fails_closed(tmp_path: Path) -> None:
    _write_snapshot(tmp_path / "data" / "app-data.json", _anonymous_snapshot())
    (tmp_path / "_site").mkdir()

    with pytest.raises(SystemExit, match="cannot verify _site public data"):
        check_release.validate_public_data_artifacts(tmp_path)


def test_malformed_deploy_copy_fails_closed(tmp_path: Path) -> None:
    _write_snapshot(tmp_path / "data" / "app-data.json", _anonymous_snapshot())
    site_snapshot = tmp_path / "_site" / "data" / "app-data.json"
    site_snapshot.parent.mkdir(parents=True)
    site_snapshot.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SystemExit, match=r"_site/data/app-data\.json.*not valid JSON"):
        check_release.validate_public_data_artifacts(tmp_path)


def test_release_privacy_scan_rejects_nested_public_json_without_echoing_value(tmp_path: Path) -> None:
    leaked_value = r"C:\Users\mjb58\AppData\Local\Temp\private-feedback.json"
    artifact = tmp_path / "_site"
    (artifact / "assets").mkdir(parents=True)
    (artifact / "index.html").write_text("<main>public</main>", encoding="utf-8")
    (artifact / "assets" / "dirty-other.json").write_text(
        json.dumps({"reasonEvidence": leaked_value}),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as error:
        check_release.validate_release_privacy_scan(tmp_path, artifact)
    message = str(error.value)
    assert "dirty-other.json" in message
    assert "raw feedback field" in message or "absolute local path" in message
    assert leaked_value not in message


def test_release_privacy_scan_rejects_zip_member_leaks_without_echoing_value(tmp_path: Path) -> None:
    leaked_value = "private-user-123"
    artifact = tmp_path / "_site"
    artifact.mkdir()
    (artifact / "index.html").write_text("<main>public</main>", encoding="utf-8")
    with zipfile.ZipFile(artifact / "public.zip", "w") as archive:
        archive.writestr("nested/leak.json", json.dumps({"ownerId": leaked_value}))

    with pytest.raises(SystemExit) as error:
        check_release.validate_release_privacy_scan(tmp_path, artifact)
    message = str(error.value)
    assert "public.zip!nested/leak.json" in message
    assert "profile/user identifier field" in message
    assert leaked_value not in message


def test_release_privacy_scan_rejects_tar_member_leaks_without_echoing_value(tmp_path: Path) -> None:
    leaked_value = "file:///C:/Users/mjb58/private.json"
    artifact = tmp_path / "_site"
    artifact.mkdir()
    (artifact / "index.html").write_text("<main>public</main>", encoding="utf-8")
    payload = json.dumps({"note": leaked_value}).encode("utf-8")
    member = tarfile.TarInfo("nested/leak.json")
    member.size = len(payload)
    with tarfile.open(artifact / "public.tar", "w") as archive:
        archive.addfile(member, io.BytesIO(payload))

    with pytest.raises(SystemExit) as error:
        check_release.validate_release_privacy_scan(tmp_path, artifact)
    message = str(error.value)
    assert "public.tar!nested/leak.json" in message
    assert "file URI" in message
    assert leaked_value not in message


def test_main_never_invokes_legacy_private_saved_jobs_validator() -> None:
    source = (ROOT / "scripts" / "check_release.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    main_node = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    called_names = {
        node.func.id
        for node in ast.walk(main_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "validate_public_data_artifacts" in called_names
    assert "validate_saved_jobs" not in called_names

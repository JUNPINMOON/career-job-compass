from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_snapshot import _atomic_write_json, assert_active_repository


ROOT = Path(__file__).resolve().parents[1]


def test_personalized_builder_accepts_only_run_scoped_staging_json(tmp_path: Path) -> None:
    job_root = tmp_path / "job_search"
    staged = job_root / "state_v4" / ".refresh-staging" / ("a" * 64 + ".json")

    assert_active_repository(
        ROOT,
        staged,
        personalized_runtime=True,
        job_search_root=job_root,
    )

    with pytest.raises(ValueError, match="fenced run artifact"):
        assert_active_repository(
            ROOT,
            job_root / "state_v4" / ".refresh-staging" / "shared.json",
            personalized_runtime=True,
            job_search_root=job_root,
        )


def test_atomic_json_writer_leaves_only_complete_destination(tmp_path: Path) -> None:
    destination = tmp_path / "snapshot.json"
    destination.write_text('{"old":true}', encoding="utf-8")

    _atomic_write_json(destination, {"new": [1, 2, 3]})

    assert json.loads(destination.read_text(encoding="utf-8")) == {"new": [1, 2, 3]}
    assert list(tmp_path.glob("*.tmp")) == []

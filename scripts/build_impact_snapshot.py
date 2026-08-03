#!/usr/bin/env python3
"""data-requirement-id="DATA-319": publish impact briefs through one canonical path.

The public impact source is the source of truth.  This producer validates that source,
copies only the impact fields into the app snapshot, and records enough lineage
for the release gate to prove that the mobile consumer reads the same records.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SOURCE = ROOT / "data" / "impact-opportunities.json"
CANONICAL_OUTPUT = ROOT / "data" / "app-data.json"
PRODUCER = "scripts/build_impact_snapshot.py"
SOURCE_PATH = "data/impact-opportunities.json"
OUTPUT_PATH = "data/app-data.json"
CONSUMER = "app.js impactOpportunityPage"
SCHEMA_VERSION = "social-environment-ai-v1"

REQUIRED_RECORD_FIELDS = {
    "id",
    "title",
    "problem",
    "affectedPeople",
    "directUsers",
    "decisionToImprove",
    "aiRole",
    "dataInputs",
    "firstProof",
    "jobKeywords",
    "programKeywords",
    "sources",
    "boundary",
    "dataAssets",
    "evidenceGap",
    "koreaUse",
}
REQUIRED_ASSET_FIELDS = {
    "title",
    "url",
    "access",
    "coverage",
    "use",
    "limitation",
    "sourceTier",
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_text_sha256(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _require_text(record: Mapping[str, Any], field: str, record_id: str) -> None:
    if not isinstance(record.get(field), str) or not str(record[field]).strip():
        raise ValueError(f"impact record {record_id} has no {field}")


def validate_impact_opportunities(records: object) -> list[dict[str, Any]]:
    """DATA-319: fail closed unless each public brief is usable and sourced."""
    if not isinstance(records, list) or len(records) < 6:
        raise ValueError("impact source must contain at least six impact opportunities")

    validated: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for index, raw_record in enumerate(records):
        if not isinstance(raw_record, dict):
            raise ValueError(f"impact record {index} must be an object")
        record = dict(raw_record)
        record_id = str(record.get("id") or f"index-{index}")
        if not REQUIRED_RECORD_FIELDS.issubset(record):
            missing = sorted(REQUIRED_RECORD_FIELDS - set(record))
            raise ValueError(f"impact record {record_id} is missing {missing}")
        if record_id in identifiers:
            raise ValueError(f"duplicate impact record id: {record_id}")
        identifiers.add(record_id)

        for field in (
            "id",
            "title",
            "problem",
            "affectedPeople",
            "directUsers",
            "decisionToImprove",
            "aiRole",
            "dataInputs",
            "firstProof",
            "boundary",
            "evidenceGap",
            "koreaUse",
        ):
            _require_text(record, field, record_id)
        if record["directUsers"].strip() == record["affectedPeople"].strip():
            raise ValueError(f"impact record {record_id} confuses affected people with direct users")
        for field in ("jobKeywords", "programKeywords"):
            if not isinstance(record[field], list) or not record[field]:
                raise ValueError(f"impact record {record_id} has no {field}")

        sources = record["sources"]
        if not isinstance(sources, list) or len(sources) < 2:
            raise ValueError(f"impact record {record_id} needs at least two official sources")
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError(f"impact record {record_id} has malformed source evidence")
            if source.get("sourceTier") != "official":
                raise ValueError(f"impact record {record_id} has a non-official primary source")
            if not str(source.get("url") or "").startswith("https://"):
                raise ValueError(f"impact record {record_id} has an invalid source URL")

        assets = record["dataAssets"]
        if not isinstance(assets, list) or not assets:
            raise ValueError(f"impact record {record_id} has no usable public dataset")
        for asset in assets:
            if not isinstance(asset, dict) or not REQUIRED_ASSET_FIELDS.issubset(asset):
                raise ValueError(f"impact record {record_id} has malformed dataset evidence")
            if asset.get("sourceTier") != "official":
                raise ValueError(f"impact record {record_id} has a non-official dataset")
            if not str(asset.get("url") or "").startswith("https://"):
                raise ValueError(f"impact record {record_id} has an invalid dataset URL")
        validated.append(record)
    return validated


def _expected_lineage(
    records: list[dict[str, Any]],
    existing_lineage: object,
) -> dict[str, Any]:
    previous = existing_lineage if isinstance(existing_lineage, dict) else {}
    generated_at = previous.get("generatedAt")
    if not isinstance(generated_at, str) or not generated_at:
        generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "schemaVersion": SCHEMA_VERSION,
        "producer": PRODUCER,
        "sourcePath": SOURCE_PATH,
        "outputPath": OUTPUT_PATH,
        "consumer": CONSUMER,
        "contract": (
            f"producer={PRODUCER}; source={SOURCE_PATH}; "
            f"output={OUTPUT_PATH}; consumer={CONSUMER}"
        ),
        "producerCodeSha256": _canonical_text_sha256(Path(__file__)),
        "recordsSha256": _canonical_json_sha256(records),
        "recordCount": len(records),
        "generatedAt": generated_at,
    }


def _assert_canonical_path(path: Path, expected: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    if resolved != expected.resolve(strict=True):
        raise ValueError(f"{label} must be the canonical {expected.relative_to(ROOT).as_posix()} path")
    return resolved


def refresh_impact_snapshot(source_path: Path, output_path: Path, *, check: bool) -> None:
    source_path = _assert_canonical_path(source_path, CANONICAL_SOURCE, "impact source")
    output_path = _assert_canonical_path(output_path, CANONICAL_OUTPUT, "impact output")
    source = _read_json(source_path)
    output = _read_json(output_path)
    records = validate_impact_opportunities(source.get("impactOpportunities"))
    expected_lineage = _expected_lineage(records, source.get("impactOpportunityLineage"))

    if check:
        if source.get("impactOpportunityLineage") != expected_lineage:
            raise ValueError("impact source lineage does not match its producer and records")
        if output.get("impactOpportunities") != records:
            raise ValueError("app-data impact records differ from the canonical impact source")
        if output.get("impactOpportunityLineage") != expected_lineage:
            raise ValueError("app-data impact lineage differs from the canonical impact source")
        print(
            f"impact snapshot check ok: {len(records)} records, "
            f"{SOURCE_PATH} -> {OUTPUT_PATH} -> {CONSUMER}"
        )
        return

    source["impactOpportunityLineage"] = expected_lineage
    output["impactOpportunities"] = records
    output["impactOpportunityLineage"] = expected_lineage
    _atomic_write_json(source_path, source)
    _atomic_write_json(output_path, output)
    print(
        f"impact snapshot refreshed: {len(records)} records, "
        f"{SOURCE_PATH} -> {OUTPUT_PATH} -> {CONSUMER}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--impact-source", type=Path, default=CANONICAL_SOURCE)
    parser.add_argument("--output", type=Path, default=CANONICAL_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    refresh_impact_snapshot(args.impact_source, args.output, check=args.check)


if __name__ == "__main__":
    main()

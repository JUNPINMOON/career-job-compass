#!/usr/bin/env python3
"""Small, dependency-free gate for the append-only dashboard requirement ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _items(value: object) -> list[str]:
    return value if isinstance(value, list) else [value]  # type: ignore[list-item]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    ledger_path = root / "requirements" / "ledger.yaml"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    requirements = ledger.get("requirements", [])
    ids = [item.get("id") for item in requirements]
    failures: list[str] = []
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        failures.append("requirement IDs must be present and unique")

    for item in requirements:
        if item.get("status") != "active":
            continue
        assertion = item.get("assert") or {}
        target = root / assertion.get("path", assertion.get("file", ""))
        if not target.is_file():
            failures.append(f"{item['id']}: assertion target missing: {target}")
            continue
        content = target.read_text(encoding="utf-8")
        required = assertion.get("needles", []) if assertion.get("type") == "text_present" else assertion.get("contains", [])
        forbidden = assertion.get("needles", []) if assertion.get("type") == "text_absent" else assertion.get("absent", [])
        for needle in _items(required):
            if needle and needle not in content:
                failures.append(f"{item['id']}: missing required marker {needle!r}")
        for needle in _items(forbidden):
            if needle and needle in content:
                failures.append(f"{item['id']}: forbidden marker remains {needle!r}")

    if failures:
        print("REQUIREMENTS FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(f"REQUIREMENTS PASS: {len(requirements)} active requirements covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

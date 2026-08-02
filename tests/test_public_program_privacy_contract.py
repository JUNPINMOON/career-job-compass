from __future__ import annotations

import json
from pathlib import Path

from scripts import build_snapshot
from scripts import check_release


PRIVATE_READINESS_PHRASES = (
    "expired certs",
    "candidate's",
    "candidate must retake",
    "his english certs",
    "as a korean domestic applicant he",
    "as a korean domestic student he",
    "strongest path for this candidate",
    "candidate is most likely ineligible",
    "지원자 swmm",
)


def _serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).lower()


def _private_program() -> dict[str, object]:
    return {
        "id": "private-program",
        "english": "Official requirement: TOEFL iBT 80. Candidate must retake expired certs.",
        "funding": (
            "Tuition waiver available. "
            "As a Korean domestic applicant he should use the strongest path for this candidate."
        ),
        "englishGapPlan": ["His English certs are expired."],
        "privateAdmissionsReadiness": {"gpa": 3.2, "transcript": "candidate's transcript"},
        "publicResearch": {
            "faculty": [
                {
                    "name": "Public Professor",
                    "recentPapers": [
                        {"title": "Flood modelling", "venue": "지원자 SWMM 경험 우대. Water Research."}
                    ],
                }
            ]
        },
    }


def test_public_program_sanitizer_removes_private_readiness_without_erasing_official_facts() -> None:
    payload = {"programs": [_private_program()]}

    build_snapshot._sanitize_public_programs(payload)

    program = payload["programs"][0]
    serialized = _serialized(program)
    assert "englishGapPlan" not in program
    assert "privateAdmissionsReadiness" not in program
    assert "toefl ibt 80" in serialized
    assert "tuition waiver available" in serialized
    assert "water research" in serialized
    assert not any(phrase in serialized for phrase in PRIVATE_READINESS_PHRASES)


def test_release_gate_rejects_private_graduate_readiness_and_accepts_sanitized_programs() -> None:
    private_program = _private_program()
    assert check_release.public_graduate_privacy_violation([private_program]) is not None

    payload = {"programs": [private_program]}
    build_snapshot._sanitize_public_programs(payload)
    assert check_release.public_graduate_privacy_violation(payload["programs"]) is None


def test_generated_public_snapshot_contains_no_private_graduate_readiness() -> None:
    snapshot_path = Path(__file__).resolve().parents[1] / "data" / "app-data.json"
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    programs = payload.get("programs", [])

    assert check_release.public_graduate_privacy_violation(programs) is None
    serialized = _serialized(programs)
    assert "englishgapplan" not in serialized
    assert "privateadmissionsreadiness" not in serialized
    assert not any(phrase in serialized for phrase in PRIVATE_READINESS_PHRASES)

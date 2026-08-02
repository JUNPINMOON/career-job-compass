from __future__ import annotations

import pytest

from scripts import check_release


@pytest.mark.parametrize(
    "private_text",
    (
        "Expired certs must be replaced.",
        "The candidate's transcript is already available.",
        "Candidate must retake the English test.",
        "His English certs are expired.",
        "As a Korean domestic applicant he should use this route.",
        "As a Korean domestic student he is not eligible.",
        "This is the strongest path for this candidate.",
        "Candidate is most likely INELIGIBLE.",
        "지원자 SWMM 경험 우대",
    ),
)
def test_public_graduate_privacy_violation_detects_private_readiness_without_echoing_it(
    private_text: str,
) -> None:
    result = check_release.public_graduate_privacy_violation(
        [{"publicResearch": {"faculty": [{"note": private_text}]}}]
    )

    assert result == "private_readiness_phrase"
    assert private_text.casefold() not in result.casefold()


@pytest.mark.parametrize("private_key", ("englishGapPlan", "privateAdmissionsReadiness"))
def test_public_graduate_privacy_violation_detects_private_keys_recursively(private_key: str) -> None:
    result = check_release.public_graduate_privacy_violation(
        [{"publicResearch": {"faculty": [{private_key: {"value": "redacted"}}]}}]
    )

    assert result == "private_readiness_field"
    assert private_key.casefold() not in result.casefold()


def test_public_graduate_privacy_violation_retains_generic_institution_requirements() -> None:
    public_programs = [
        {
            "english": "Applicants must submit TOEFL iBT 80 or IELTS 6.5.",
            "admissions": "Official transcripts and GPA evidence are required.",
            "funding": "The institution offers a tuition waiver and research assistantship.",
        }
    ]

    assert check_release.public_graduate_privacy_violation(public_programs) is None

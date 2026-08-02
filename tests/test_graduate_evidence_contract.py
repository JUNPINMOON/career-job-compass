from __future__ import annotations

from datetime import datetime

import pytest

from scripts.build_snapshot import (
    _program_decision_support,
    _public_research,
    current_or_recent_years,
    verified_funded_project,
)


def test_recent_window_rejects_unknown_and_future_only_periods() -> None:
    current_year = datetime.now().year

    assert current_or_recent_years("") is False
    assert current_or_recent_years("period not disclosed") is False
    assert current_or_recent_years(f"{current_year + 1}-{current_year + 3}") is False
    assert current_or_recent_years(f"{current_year - 1}-{current_year + 2}") is True
    assert current_or_recent_years(str(current_year - 4)) is True
    assert current_or_recent_years(str(current_year - 5)) is False


def test_funded_project_requires_funder_and_stable_public_evidence() -> None:
    base = {
        "title": "Flood resilience decision support",
        "funder": "National Research Agency",
        "period": "2024-2026",
    }

    assert verified_funded_project(base) is False
    assert verified_funded_project({**base, "url": "not-public"}) is False
    assert verified_funded_project({**base, "url": "https://example.edu/award/42"}) is True
    assert verified_funded_project({**base, "award_id": "AWARD-42"}) is True
    assert verified_funded_project({**base, "funder": ""}) is False


def test_public_research_preserves_claim_context_without_alumni_identity() -> None:
    current_year = datetime.now().year
    result = _public_research(
        {
            "faculty": [
                {
                    "name": "Professor A",
                    "orcid": "0000-0000-0000-0001",
                    "evidence_quality": "A2",
                    "profile_sources": [
                        {
                            "url": "https://example.edu/faculty/a",
                            "source_type": "official_faculty_profile",
                            "evidence_quality": "A2",
                        }
                    ],
                    "recent_papers": [
                        {
                            "year": str(current_year),
                            "title": "Paper A",
                            "doi": "10.1234/example",
                            "author_role": "corresponding_author",
                            "evidence_quality": "C",
                        }
                    ],
                    "recent_projects": [
                        {
                            "title": "Project A",
                            "funder": "Agency A",
                            "period": str(current_year),
                            "award_id": "A-1",
                            "faculty_role": "PI",
                            "evidence_quality": "A1",
                        }
                    ],
                }
            ],
            "graduate_destinations": [
                {
                    "person": "Private Alumni Name",
                    "year_range": "2022 cohort",
                    "degree": "MSc",
                    "destination": "Public water agency",
                    "role": "Engineer",
                    "aggregation_level": "individual_case",
                    "evidence_quality": "B",
                    "sources": [
                        {
                            "url": "https://example.edu/alumni/outcome",
                            "source_type": "official_alumni_story",
                            "evidence_quality": "B",
                        }
                    ],
                }
            ],
        }
    )

    faculty = result["faculty"][0]
    project = faculty["recentProjects"][0]
    destination = result["graduateDestinations"][0]

    assert faculty["orcid"] == "0000-0000-0000-0001"
    assert faculty["evidenceQuality"] == "A2"
    assert faculty["recentPapers"][0]["doi"] == "10.1234/example"
    assert project["awardId"] == "A-1"
    assert project["facultyRole"] == "PI"
    assert project["evidenceStatus"] == "verified_funded_project"
    assert destination["cohort"] == "2022 cohort"
    assert destination["degree"] == "MSc"
    assert destination["aggregationLevel"] == "individual_case"
    assert destination["evidenceQuality"] == "B"
    assert "person" not in destination
    assert "Private Alumni Name" not in str(result)


def test_untyped_sources_remain_unknown_quality() -> None:
    result = _public_research(
        {
            "faculty": [
                {
                    "name": "Professor B",
                    "profile_urls": ["https://example.edu/faculty/b"],
                    "recent_papers": [],
                    "recent_projects": [],
                }
            ]
        }
    )

    assert result["faculty"][0]["profileSources"][0]["evidenceQuality"] == "U"
    assert result["faculty"][0]["evidenceQuality"] == "U"


def test_empty_research_is_unknown_and_never_rendered_as_verified_zero() -> None:
    research = _public_research({})

    assert set(research["claimEvidence"]) == {
        "faculty",
        "recentPapers",
        "fundedProjects",
        "graduateDestinations",
        "testimonials",
    }
    assert all(
        axis == {
            "claimState": "no_claim",
            "evidenceState": "not_researched",
            "recordCount": None,
            "sources": [],
        }
        for axis in research["claimEvidence"].values()
    )

    support = _program_decision_support({"publicResearch": research})
    rendered = str(support)
    assert "\u0030\uac74" not in rendered
    assert "\uad50\uc218 \u0030\uba85" not in rendered
    assert "\ubbf8\uc870\uc0ac" in rendered


def test_explicit_none_requires_source_evidence() -> None:
    with pytest.raises(ValueError, match="verified_none requires public source evidence"):
        _public_research(
            {
                "evidence_states": {
                    "graduate_destinations": {"state": "verified_none"},
                }
            }
        )

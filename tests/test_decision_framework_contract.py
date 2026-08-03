from __future__ import annotations

from typing import Any

from scripts.build_snapshot import _decision_framework


REQUIRED_DOMAINS = {
    "career",
    "graduate",
    "lifestyle",
    "feedback",
    "reliability",
    "execution",
    "application_feasibility",
    "decision_economics",
    "career_capital",
    "organizational_reality",
    "application_pipeline",
    "uncertainty_risk",
}

REQUIRED_SUBFIELDS = {
    "water_hydrology",
    "climate_env_ai",
    "gis_remote_sensing",
    "oda_policy_pm",
    "domestic_wlb",
    "supervisor_fit",
    "papers",
    "funded_projects",
    "alumni_outcomes",
    "lab_life",
    "jayang_commute",
    "busan_lane",
    "city_safety_quality",
    "structured_reasons",
    "all_rows_compare",
    "negative_learning",
    "official_jobs",
    "community_leads",
    "alumni_public",
    "producer_consumer",
    "phase_gate_loop",
    "mobile_release",
    "eligibility_hard_gates",
    "timing_documents",
    "compensation_contract",
    "skill_gap_bridge",
    "salary_living_cost",
    "opportunity_cost",
    "evidence_confidence",
    "portfolio_balance",
    "research_frontier",
    "funding_strategy",
    "source_quality",
    "application_packaging",
    "work_substance",
    "skill_compounding",
    "exit_options",
    "stability_contract",
    "manager_team",
    "culture_workload",
    "priority_actionability",
    "materials_readiness",
    "interview_feedback",
    "posting_currentness",
    "provenance_dedup",
    "reversibility_red_flags",
    "toefl_transcript_readiness",
}


def _sample_payload() -> dict[str, Any]:
    return {
        "dataAsOf": "2026-08-02",
        "jobs": [
            {
                "id": "water-1",
                "relevantSectors": [{"sectorId": "water_resources"}],
                "postingCurrentness": {"status": "verified_open"},
                "decisionSupport": {"requirements": ["hydrology"]},
            },
            {
                "id": "gis-1",
                "relevantSectors": [{"sectorId": "gis"}],
                "postingCurrentness": {"status": "unverified"},
                "decisionSupport": {"requirements": []},
            },
            {
                "id": "oda-1",
                "relevantSectors": [{"sectorId": "oda"}],
                "postingCurrentness": {"status": "verified_closed"},
                "decisionSupport": {"requirements": ["project management"]},
            },
        ],
        "programs": [
            {
                "english": "TOEFL iBT 80 or IELTS 6.0; waiver available under the official rules.",
                "admissionRequirements": ["Official transcript", "minimum GPA 3.0"],
            },
            {},
        ],
        "funding": [{}, {}, {}],
        "stats": {
            "jobs": 3,
            "programs": 2,
            "funding": 3,
            "queueCounts": {"verify": 1, "hold": 2, "apply": 3, "stretch": 4},
            "marketCounts": {"domestic": 7, "overseas": 11, "unknown": 13},
            "actionCandidates": 5,
            "explorationCandidates": 8,
            "excludedExperienceCandidates": 2,
            "excludedUnverifiedCandidates": 4,
            "sectorInventoryCount": 20,
            "sourceReviewCandidates": 6,
            "preferenceSummary": {
                "rowCount": 0,
                "likedCount": 0,
                "dislikedCount": 0,
                "digest": None,
            },
            "preferenceDiscovery": {
                "current": False,
                "evaluatedCandidateCount": 0,
            },
        },
        "graduateEvidenceCoverage": {
            "totalPrograms": 2,
            "programsWithAnyEvidence": 1,
            "programsWithFaculty": 1,
            "programsWithRecentPapers": 1,
            "programsWithFundedProjects": 1,
            "programsWithGraduateDestinations": 1,
            "programsWithTestimonials": 0,
            "unresearchedPrograms": 1,
        },
        "lifestyleDiscovery": {
            "sourcePostingCount": 100,
            "publicCandidateCount": 9,
            "verifiedOpenCount": 3,
            "candidateFilter": {"publishedCandidates": 9},
            "lanes": {
                "jayang_wlb": {
                    "matchedCount": 5,
                    "classCounts": {"verifiedOpen": 2},
                    "decisionReadiness": "partial",
                },
                "busan": {
                    "matchedCount": 4,
                    "classCounts": {"verifiedOpen": 1},
                    "decisionReadiness": "needs_review",
                },
            },
        },
        "decisionFrameworkSources": {
            "funding_strategy": {
                "available": True,
                "path": "artifacts/funding/funding_opportunities_latest.json",
                "count": 180,
                "artifactDateIsPostingProof": False,
            },
            "application_packaging": {
                "available": True,
                "path": "artifacts/applications/application_sprint_latest.json",
                "count": 8,
                "artifactDateIsPostingProof": False,
            },
            "source_quality": {
                "available": True,
                "path": "artifacts/source_quality/source_quality_latest.json",
                "sourceCount": 35,
                "jobCount": 1000,
                "artifactDateIsPostingProof": False,
            },
            "research_frontier": {
                "available": True,
                "path": "artifacts/research/expert_topics_normalized.json",
                "count": 24,
                "strategyFitCounts": {"portfolio_now": 14, "job_search_fit": 8},
                "artifactDateIsPostingProof": False,
            },
        },
    }


def _subfields(framework: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        subfield["id"]: subfield
        for domain in framework["domains"]
        for subfield in domain["subfields"]
    }


def test_decision_framework_v3_contains_required_expandable_contract() -> None:
    framework = _decision_framework(_sample_payload())
    subfields = _subfields(framework)

    domain_ids = [domain["id"] for domain in framework["domains"]]
    subfield_ids = [
        subfield["id"]
        for domain in framework["domains"]
        for subfield in domain["subfields"]
    ]

    assert framework["schemaVersion"] == "decision-framework-v3"
    assert framework["stateSchemaVersion"] == "framework-state-v3"
    assert REQUIRED_DOMAINS <= set(domain_ids)
    assert REQUIRED_SUBFIELDS <= set(subfield_ids)
    assert len(domain_ids) == len(set(domain_ids))
    assert len(subfield_ids) == len(set(subfield_ids))


def test_every_framework_subfield_has_truthful_operational_state() -> None:
    framework = _decision_framework(_sample_payload())
    subfields = _subfields(framework)
    implementation_states = {"connected", "partial", "runtime_only", "planned"}
    gate_states = {"pass", "review", "hold", "runtime"}

    for subfield in subfields.values():
        assert subfield["implementationState"] in implementation_states
        assert subfield["gateState"] in gate_states
        assert subfield["currentMetrics"]
        assert all(str(metric).strip() for metric in subfield["currentMetrics"])
        assert str(subfield["followup"]).strip()
        assert str(subfield["evidencePath"]).strip()
        assert subfield["process"]
        assert subfield["gate"]
        assert subfield["loop"]


def test_public_feedback_signals_are_runtime_only_not_false_zero_counts() -> None:
    framework = _decision_framework(_sample_payload())
    subfields = _subfields(framework)
    signals = framework["signals"]

    assert "liked" not in signals
    assert "disliked" not in signals
    assert signals["preferenceRuntime"] == {
        "state": "authenticated_runtime_required",
        "publicSnapshot": "anonymous_no_user_counts",
        "countsPublished": False,
    }
    for key in ("structured_reasons", "all_rows_compare", "negative_learning"):
        assert subfields[key]["implementationState"] == "runtime_only"
        assert subfields[key]["gateState"] == "runtime"
        assert any("authenticated runtime" in metric for metric in subfields[key]["currentMetrics"])


def test_lifestyle_and_decision_economics_use_real_connected_metrics() -> None:
    framework = _decision_framework(_sample_payload())
    subfields = _subfields(framework)
    economics = next(domain for domain in framework["domains"] if domain["id"] == "decision_economics")

    assert "matched candidates=5" in subfields["jayang_commute"]["currentMetrics"]
    assert "verified open=2" in subfields["jayang_commute"]["currentMetrics"]
    assert "matched candidates=4" in subfields["busan_lane"]["currentMetrics"]
    assert "verified open=1" in subfields["busan_lane"]["currentMetrics"]
    assert {subfield["id"] for subfield in economics["subfields"]} == {
        "salary_living_cost",
        "opportunity_cost",
        "evidence_confidence",
        "portfolio_balance",
    }
    assert framework["signals"]["lifestylePublicCandidates"] == 9
    assert framework["signals"]["lifestyleVerifiedOpen"] == 3


def test_measured_expansion_lanes_expose_artifact_counts_without_faking_posting_freshness() -> None:
    framework = _decision_framework(_sample_payload())
    subfields = _subfields(framework)

    assert "research topics=24" in subfields["research_frontier"]["currentMetrics"]
    assert "funding opportunities=180" in subfields["funding_strategy"]["currentMetrics"]
    assert "application candidates=8" in subfields["application_packaging"]["currentMetrics"]
    assert "reviewed sources=35" in subfields["source_quality"]["currentMetrics"]
    for key in ("research_frontier", "funding_strategy", "application_packaging", "source_quality"):
        assert subfields[key]["implementationState"] == "connected"
        assert subfields[key]["gateState"] == "review"
        assert any("not posting proof" in metric for metric in subfields[key]["currentMetrics"])


def test_currentness_and_new_deep_domains_keep_unknowns_visible() -> None:
    framework = _decision_framework(_sample_payload())
    subfields = _subfields(framework)

    assert "verified open=1" in subfields["posting_currentness"]["currentMetrics"]
    assert "verified closed=1" in subfields["posting_currentness"]["currentMetrics"]
    assert "unverified=1" in subfields["posting_currentness"]["currentMetrics"]
    assert subfields["manager_team"]["gateState"] == "hold"
    assert subfields["interview_feedback"]["implementationState"] == "runtime_only"
    assert subfields["reversibility_red_flags"]["gateState"] == "hold"


def test_graduate_admissions_gate_measures_public_requirements_without_private_readiness() -> None:
    framework = _decision_framework(_sample_payload())
    subfield = _subfields(framework)["toefl_transcript_readiness"]

    assert "programs=2" in subfield["currentMetrics"]
    assert "English evidence=1" in subfield["currentMetrics"]
    assert "numeric threshold=1" in subfield["currentMetrics"]
    assert "waiver evidence=1" in subfield["currentMetrics"]
    assert "transcript/GPA evidence=1" in subfield["currentMetrics"]
    assert any("private readiness is not serialized" in item for item in subfield["currentMetrics"])
    assert subfield["gateState"] == "review"


def test_provenance_gate_requires_complete_url_and_source_lineage_not_only_unique_ids() -> None:
    incomplete_framework = _decision_framework(_sample_payload())
    incomplete = _subfields(incomplete_framework)["provenance_dedup"]
    assert incomplete["implementationState"] == "partial"
    assert incomplete["gateState"] == "review"
    assert "source lineage complete=0/3" in incomplete["currentMetrics"]
    assert "canonical URL complete=0/3" in incomplete["currentMetrics"]

    complete_payload = _sample_payload()
    for index, job in enumerate(complete_payload["jobs"], start=1):
        job["url"] = f"https://example.org/jobs/{index}?utm_source=test"
        job["sourceKey"] = "official-careers"
        job["sourceLabel"] = "Official careers"
    complete_framework = _decision_framework(complete_payload)
    complete = _subfields(complete_framework)["provenance_dedup"]
    assert complete["implementationState"] == "connected"
    assert complete["gateState"] == "pass"
    assert "duplicate canonical URLs=0" in complete["currentMetrics"]
    assert complete["evidencePath"] == "jobs[].id + jobs[].url + jobs[].sourceKey/sourceLabel"


def test_all_unverified_jobs_are_explicitly_exploration_only() -> None:
    payload = _sample_payload()
    for job in payload["jobs"]:
        job["postingCurrentness"] = {"status": "unverified"}

    framework = _decision_framework(payload)

    assert framework["readinessBoundary"]["state"] == "exploration_only"
    assert framework["readinessBoundary"]["verifiedOpenCount"] == 0
    assert framework["readinessBoundary"]["applyReadyCount"] == 0
    assert "공식 원문" in framework["readinessBoundary"]["label"]


def test_review_protocol_exposes_eight_perspectives_and_non_candidate_scoring_boundary() -> None:
    framework = _decision_framework(_sample_payload())
    protocol = framework["reviewProtocol"]

    assert protocol["version"] == "review-protocol-v1"
    assert len(protocol["stages"]) == 3
    assert len(protocol["stages"][0]["items"]) == 8
    assert protocol["goalPriority"]["candidateSuitability"] is False
    assert protocol["goalPriority"]["regionExcludedFromScore"] is True
    assert protocol["goalPriority"]["scale"] == {"min": 0, "max": 5}
    assert len(protocol["goalPriority"]["workstreams"]) >= 6
    assert all(0 <= float(row["priority"]) <= 5 for row in protocol["goalPriority"]["workstreams"])
    assert protocol["candidateSimilarity"]["regionWeight"] == 0


def test_review_protocol_is_payload_derived_and_has_gate_loop_synthesis() -> None:
    payload = _sample_payload()
    payload["stats"]["sourceReviewCandidates"] = 4
    protocol = _decision_framework(payload)["reviewProtocol"]

    perspective_ids = [item["id"] for item in protocol["stages"][0]["items"]]
    assert perspective_ids == [
        "rebuttal",
        "first_principle_purpose",
        "first_principle_assumptions",
        "expansion_combination",
        "expansion_absence",
        "outsider",
        "executor",
        "blind_spot",
    ]
    assert all(item["gate"] and item["loop"] and item["finding"] for item in protocol["stages"][0]["items"])
    assert "priority = 5 * impact" in protocol["goalPriority"]["formula"]
    assert protocol["synthesis"]["recommendation"] == "verified_facts_first"
    assert protocol["synthesis"]["blockers"]
    assert protocol["stages"][1]["items"][0]["rank"] == 1

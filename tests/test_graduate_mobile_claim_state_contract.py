from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "app.js").read_text(encoding="utf-8")


def test_mobile_graduate_claims_keep_unknown_distinct_from_zero() -> None:
    assert "function graduateClaimStateCopy" in APP_JS
    assert "recordCount === null" in APP_JS
    assert 'claim.evidenceState === "searched_none" && recordCount === 0' in APP_JS
    assert 'claim.evidenceState === "verified_none" && recordCount === 0' in APP_JS


def test_each_graduate_axis_uses_the_claim_evidence_contract() -> None:
    for axis in (
        "faculty",
        "recentPapers",
        "fundedProjects",
        "graduateDestinations",
        "testimonials",
    ):
        assert f'graduateClaimStateCopy(research, "{axis}"' in APP_JS


def test_empty_panels_render_claim_specific_evidence_instead_of_a_generic_zero() -> None:
    assert "graduateClaimEmpty(claimStates.faculty)" in APP_JS
    assert "graduateClaimEmpty(claimStates.projects)" in APP_JS
    assert "graduateClaimEmpty(claimStates.destinations)" in APP_JS
    assert "graduateClaimEmpty(claimStates.testimonials)" in APP_JS

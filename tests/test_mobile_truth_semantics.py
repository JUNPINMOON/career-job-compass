from __future__ import annotations

import re
from pathlib import Path


APP_JS_PATH = Path(__file__).resolve().parents[1] / "app.js"
APP_JS = APP_JS_PATH.read_text(encoding="utf-8")


def _function_block(name: str) -> str:
    match = re.search(
        rf"(?ms)^  function {re.escape(name)}\([^\n]*\) \{{.*?(?=^  function |\Z)",
        APP_JS,
    )
    assert match is not None, f"app.js is missing function {name}()"
    return match.group(0)


def test_exploration_only_source_stat_uses_exploration_inventory_semantics() -> None:
    render_sources = _function_block("renderSources")

    assert "explorationCandidates" in render_sources, (
        "The exploration-only source summary must read stats.explorationCandidates; "
        "stats.actionCandidates is the apply-ready count and can truthfully be zero."
    )
    assert "탐색 후보" in render_sources, (
        "The exploration-only count must be labelled '탐색 후보', not as an action/interest count."
    )
    assert not re.search(
        r'exploration_only[^\n]{0,180}\?\s*["\']관심 후보["\']',
        render_sources,
    ), "Exploration inventory must not be presented as '관심 후보'."


def test_source_link_copy_is_truthful_and_job_official_status_is_evidence_gated() -> None:
    official_link = _function_block("officialLink")
    render_job_detail = _function_block("renderJobDetail")

    assert "출처 원문 열기" in official_link or "원문 후보 열기" in official_link, (
        "Arbitrary URLs need a non-official source label; officialLink() must not universally "
        "call every destination an official original."
    )
    assert re.search(r"function officialLink\([^)]*,", official_link), (
        "officialLink() needs an explicit truth/evidence argument before it may render official copy."
    )
    assert "canonicalEmployerVerified" in render_job_detail, (
        "A job link may be labelled official only when canonical employer ownership is verified."
    )
    assert "verified_open" in render_job_detail, (
        "A job link may be labelled official only when the posting is currently verified open."
    )
    assert re.search(r"officialLink\(job\.url\s*,", render_job_detail), (
        "renderJobDetail() must pass the verified canonical-employer predicate to officialLink()."
    )


def test_program_ui_describes_public_evidence_not_private_readiness() -> None:
    program_surfaces = "\n".join(
        (
            _function_block("programReadinessLabel"),
            _function_block("renderStudy"),
            _function_block("renderRecordDetail"),
        )
    )

    assert "\uc9c0\uae08 \uc900\ube44" not in program_surfaces
    assert "englishGapPlan" not in _function_block("renderRecordDetail")


def test_comparison_card_keeps_funding_record_kind_for_detail_route() -> None:
    comparison_card = _function_block("comparisonCard")

    assert not re.search(r'data-open-record=["\']program:\$\{', comparison_card), (
        "Non-job comparison cards must not be hardcoded to the program detail route; "
        "funding records would open the wrong panel."
    )
    assert re.search(
        r'data-open-record=["\']\$\{(?:escapeHtml\()?\s*(?:kind|recordKind|detailKind)',
        comparison_card,
    ), "The detail route must interpolate the comparison record's real kind (including funding)."

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
SW = (ROOT / "sw.js").read_text(encoding="utf-8")


def function_block(name, next_name):
    pattern = rf"  function {re.escape(name)}\(.*?(?=\n  function {re.escape(next_name)}\()"
    match = re.search(pattern, APP, flags=re.S)
    if not match:
        raise AssertionError(f"function block missing: {name}")
    return match.group(0)


class MainDecisionLanesContractTest(unittest.TestCase):
    def test_main_routes_consume_decision_lane_panel(self):
        self.assertIn('data-requirement-id="UX-312"', APP)
        self.assertIn("function decisionLanePanel(", APP)
        self.assertIn('decisionLanePanel("jobs")', function_block("renderToday", "renderJobResults"))
        self.assertIn('decisionLanePanel("jobs")', function_block("renderJobs", "comparisonCard"))
        self.assertIn('decisionLanePanel("graduate")', function_block("renderStudyLegacy", "renderStudy"))

    def test_record_cards_surface_evidence_gaps(self):
        self.assertIn("candidateEvidenceSummary(job)", function_block("candidateRow", "renderToday"))
        self.assertIn("programEvidenceSummary(item)", function_block("studyRow", "renderStudyResults"))

    def test_program_readiness_label_is_readable(self):
        block = function_block("programReadinessLabel", "chunks")
        self.assertIn('"공개 근거 추가 확인"', block)
        self.assertIn('"공개 근거 조사"', block)
        self.assertNotIn("String.fromCharCode", block)

    def test_impact_lane_is_a_bounded_trial_not_a_ranked_list(self):
        self.assertIn("function impactExecutionContract()", APP)
        self.assertIn("impactExperimentStatus", APP)
        self.assertIn("하나를 골라 검토받는 실험실입니다", APP)
        self.assertIn("공개 데이터로 판단 자료", APP)

    def test_service_worker_lineage_advances(self):
        self.assertIn('data-requirement-id="GOV-313"', SW)
        self.assertIn("career-compass-v60-measured-framework", SW)
        self.assertIn("career-compass-v61-main-decision-lanes", SW)
        self.assertIn('const CACHE = "career-compass-v62-impact-opportunities";', SW)
        self.assertIn('const CACHE = "career-compass-v63-claude-experiment-gate";', SW)
        self.assertIn('const CACHE = "career-compass-v64-impact-evidence-pack";', SW)


if __name__ == "__main__":
    unittest.main()

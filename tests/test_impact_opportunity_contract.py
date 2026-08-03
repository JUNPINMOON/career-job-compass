import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
IMPACT_BUILDER = (ROOT / "scripts" / "build_impact_snapshot.py").read_text(encoding="utf-8")
RELEASE_CHECK = (ROOT / "scripts" / "check_release.py").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
SW = (ROOT / "sw.js").read_text(encoding="utf-8")
DATA = json.loads((ROOT / "data" / "app-data.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "data" / "catalog-source.json").read_text(encoding="utf-8"))


class ImpactOpportunityContractTest(unittest.TestCase):
    def test_snapshot_has_connected_problem_to_action_records(self):
        self.assertIn("def validate_impact_opportunities(", IMPACT_BUILDER)
        self.assertIn("def refresh_impact_snapshot(", IMPACT_BUILDER)
        records = DATA.get("impactOpportunities", [])
        self.assertGreaterEqual(len(records), 6)
        required = {
            "id", "title", "problem", "affectedPeople", "decisionToImprove",
            "aiRole", "dataInputs", "firstProof", "jobKeywords",
            "programKeywords", "sources", "boundary", "directUsers",
            "dataAssets", "evidenceGap", "koreaUse",
        }
        for record in records:
            self.assertTrue(required.issubset(record), record.get("id"))
            self.assertGreaterEqual(len(record["sources"]), 1)
            self.assertTrue(all(source.get("sourceTier") == "official" for source in record["sources"]))
            self.assertTrue(all(str(source.get("url", "")).startswith("https://") for source in record["sources"]))
        self.assertEqual(records, CATALOG.get("impactOpportunities"))
        lineage = DATA.get("impactOpportunityLineage", {})
        self.assertEqual(lineage, CATALOG.get("impactOpportunityLineage"))
        self.assertEqual(lineage.get("producer"), "scripts/build_impact_snapshot.py")
        self.assertEqual(lineage.get("sourcePath"), "data/catalog-source.json")
        self.assertEqual(lineage.get("outputPath"), "data/app-data.json")
        self.assertEqual(lineage.get("consumer"), "app.js impactOpportunityPage")
        self.assertEqual(len(lineage.get("producerCodeSha256", "")), 64)
        self.assertEqual(len(lineage.get("recordsSha256", "")), 64)

    def test_today_has_mobile_interaction_and_evidence_boundary(self):
        self.assertIn("function impactOpportunityPage(", APP)
        self.assertIn("function impactOpportunityDetail(", APP)
        self.assertIn('data-open-impact=', APP)
        self.assertIn(".impact-opportunity-grid", CSS)
        self.assertIn(".impact-detail-evidence", CSS)
        self.assertIn("2주 첫 실험", APP)

    def test_each_problem_has_usable_public_materials_and_explicit_gaps(self):
        records = DATA.get("impactOpportunities", [])
        self.assertGreaterEqual(len(records), 6)
        asset_fields = {"title", "url", "access", "coverage", "use", "limitation", "sourceTier"}
        for record in records:
            self.assertGreaterEqual(len(record.get("sources", [])), 2, record.get("id"))
            self.assertGreaterEqual(len(record.get("dataAssets", [])), 1, record.get("id"))
            self.assertNotEqual(record.get("directUsers"), record.get("affectedPeople"), record.get("id"))
            self.assertTrue(record.get("evidenceGap"), record.get("id"))
            self.assertTrue(record.get("koreaUse"), record.get("id"))
            for asset in record["dataAssets"]:
                self.assertTrue(asset_fields.issubset(asset), (record.get("id"), asset))
                self.assertEqual(asset["sourceTier"], "official")
                self.assertTrue(asset["url"].startswith("https://"))

    def test_mobile_detail_exposes_evidence_workspace(self):
        self.assertIn("IMPACT_SELECTION_STORAGE_KEY", APP)
        self.assertIn("function selectImpactOpportunity(", APP)
        self.assertIn('data-action="select-impact"', APP)
        self.assertIn("function impactDataAssetList(", APP)
        self.assertIn("impact-data-list", APP)
        self.assertIn("opportunity.evidenceGap", APP)
        self.assertIn("opportunity.koreaUse", APP)
        self.assertIn("impact-selection-summary", APP)

    def test_public_impact_refresh_does_not_require_private_job_data(self):
        self.assertIn("CANONICAL_SOURCE", IMPACT_BUILDER)
        self.assertIn("CANONICAL_OUTPUT", IMPACT_BUILDER)
        self.assertIn('"--catalog-source"', IMPACT_BUILDER)
        self.assertIn('"--check"', IMPACT_BUILDER)
        self.assertNotIn("job-search-root", IMPACT_BUILDER)
        self.assertNotIn("job_search", IMPACT_BUILDER)

    def test_release_gate_proves_source_producer_output_and_consumer(self):
        self.assertIn('data-requirement-id="DATA-322"', RELEASE_CHECK)
        self.assertIn("def validate_impact_opportunity_lineage(", RELEASE_CHECK)
        self.assertIn("impact producer-output mismatch", RELEASE_CHECK)
        self.assertIn("producerCodeSha256", RELEASE_CHECK)
        self.assertIn("recordsSha256", RELEASE_CHECK)

    def test_service_worker_lineage_advances(self):
        self.assertIn("career-compass-v61-main-decision-lanes", SW)
        self.assertIn('const CACHE = "career-compass-v62-impact-opportunities";', SW)
        self.assertIn('const CACHE = "career-compass-v64-impact-evidence-pack";', SW)


if __name__ == "__main__":
    unittest.main()

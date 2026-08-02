from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608020004_bind_refresh_run_lineage.sql"
)


class RefreshRunLineageMigrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_snapshot_is_bound_to_one_owned_source_run(self) -> None:
        self.assertIn("add column if not exists source_run_id uuid", self.sql)
        self.assertIn("foreign key (source_run_id, user_id)", self.sql)
        self.assertIn("references public.refresh_runs (id, user_id)", self.sql)
        self.assertIn("source_attempt_count", self.sql)
        self.assertIn("personalized_snapshots_source_run_id_key", self.sql)

    def test_claim_has_attempt_identity_lease_and_stale_recovery(self) -> None:
        for column in (
            "attempt_count",
            "worker_id",
            "lease_expires_at",
            "heartbeat_at",
        ):
            self.assertIn(f"add column if not exists {column}", self.sql)
        self.assertRegex(
            self.sql,
            r"(?s)run\.state\s*=\s*'running'.*?run\.lease_expires_at\s*<=\s*claim_time",
        )
        self.assertIn("for update skip locked", self.sql)
        self.assertIn("attempt_count = claimed.attempt_count + 1", self.sql)
        self.assertIn("lease_expires_at = claim_time + interval '5 minutes'", self.sql)

    def test_publish_canonicalizes_every_required_lineage_field(self) -> None:
        binding = re.search(
            r"normalized_binding\s*:=\s*jsonb_build_object\((.*?)\);",
            self.sql,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(binding)
        for field in (
            "'runid', claimed.id",
            "'userid', claimed.user_id",
            "'preferencedigest', effective_digest",
            "'likedcount', claimed.liked_count",
            "'dislikedcount', claimed.disliked_count",
            "'rowcount', claimed.row_count",
            "'modelversion', claimed.model_version",
        ):
            self.assertIn(field, binding.group(1))
        for mismatch in (
            "refresh binding run id mismatch",
            "refresh binding user id mismatch",
            "refresh binding preference digest mismatch",
            "refresh binding liked count mismatch",
            "refresh binding disliked count mismatch",
            "refresh binding row count mismatch",
            "refresh binding model version mismatch",
            "snapshot model version does not match the claimed run",
        ):
            self.assertIn(mismatch, self.sql)

    def test_terminal_publication_is_immutable_but_exact_retry_is_idempotent(self) -> None:
        self.assertIn("terminal_payload_hash", self.sql)
        self.assertIn("claimed.terminal_payload_hash = terminal_hash", self.sql)
        self.assertIn("terminal refresh publication is immutable", self.sql)
        self.assertIn("enforce_refresh_run_terminal_immutability", self.sql)
        self.assertIn("old.state in ('succeeded', 'failed')", self.sql)

    def test_public_rpc_signatures_and_security_boundary_remain_stable(self) -> None:
        self.assertIn(
            "create or replace function public.claim_refresh_run(worker_secret text)",
            self.sql,
        )
        self.assertRegex(
            self.sql,
            r"create or replace function public\.publish_refresh_run\(\s*"
            r"worker_secret text,\s*run_id uuid,\s*run_status jsonb,\s*"
            r"personalized_snapshot jsonb default null",
        )
        self.assertGreaterEqual(self.sql.count("security definer"), 6)
        self.assertGreaterEqual(self.sql.count("set search_path = ''"), 6)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import re
import unittest
from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "supabase"
    / "migrations"
    / "202608020005_refresh_claim_fencing.sql"
)


class RefreshClaimFencingMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = MIGRATION.read_text(encoding="utf-8")
        cls.normalized = re.sub(r"\s+", " ", cls.sql.lower())

    def test_plaintext_claim_token_is_not_persisted(self) -> None:
        self.assertIn("claim_token_hash", self.normalized)
        self.assertIn("extensions.digest", self.normalized)
        self.assertNotRegex(self.normalized, r"add column(?: if not exists)? claim_token\s")

    def test_claim_issues_one_server_token_and_persists_only_its_verifier(self) -> None:
        self.assertIn("clear_claim_token := extensions.gen_random_uuid()::text", self.normalized)
        self.assertIn("set claim_token_hash = token_hash", self.normalized)
        self.assertIn(
            "jsonb_build_object('claimtoken', clear_claim_token)",
            self.normalized,
        )
        self.assertNotRegex(self.normalized, r"set\s+claim_token\s*=")

    def test_legacy_unfenced_entry_points_are_not_callable_by_api_roles(self) -> None:
        self.assertIn("rename to claim_refresh_run_unfenced_legacy", self.normalized)
        self.assertIn("rename to publish_refresh_run_unfenced_legacy", self.normalized)
        self.assertRegex(
            self.normalized,
            r"revoke all on function public\.publish_refresh_run_unfenced_legacy.*from public, anon, authenticated",
        )

    def test_heartbeat_and_publication_bind_run_user_and_token(self) -> None:
        self.assertIn("heartbeat_refresh_run", self.normalized)
        self.assertIn("publish_refresh_run_fenced", self.normalized)
        self.assertRegex(
            self.normalized,
            r"where run\.id = heartbeat_refresh_run\.run_id "
            r"and run\.user_id = heartbeat_refresh_run\.user_id .*"
            r"run\.claim_token_hash = presented_token_hash .*"
            r"run\.lease_expires_at > heartbeat_time",
        )
        self.assertRegex(
            self.normalized,
            r"where run\.id = publish_refresh_run_fenced\.run_id "
            r"and run\.user_id = publish_refresh_run_fenced\.user_id .*"
            r"claimed\.claim_token_hash is distinct from presented_token_hash .*"
            r"claimed\.lease_expires_at <= checked_at",
        )

    def test_old_publish_signature_remains_but_fails_closed(self) -> None:
        self.assertIn(
            "create or replace function public.publish_refresh_run( worker_secret text, run_id uuid, run_status jsonb, personalized_snapshot jsonb default null )",
            self.normalized,
        )
        self.assertIn("claim token is required", self.normalized)


if __name__ == "__main__":
    unittest.main()

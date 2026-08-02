from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "app.js"


def app_source() -> str:
    return APP_JS.read_text(encoding="utf-8")


def function_block(source: str, signature: str, next_signature: str) -> str:
    start = source.index(signature)
    end = source.index(next_signature, start)
    return source[start:end]


def test_private_feedback_is_not_hydrated_before_supabase_identity() -> None:
    source = app_source()

    assert "bookmarks: new Set(readJSON(BOOKMARK_STORAGE_KEY" not in source
    assert "feedback: readJSON(FEEDBACK_STORAGE_KEY" not in source
    assert "comparison: readJSON(COMPARISON_STORAGE_KEY" not in source


def test_private_live_snapshot_is_not_used_before_supabase_identity() -> None:
    source = app_source()

    assert "selectFreshestSnapshot(bundled, readJSON(LIVE_SNAPSHOT_STORAGE_KEY" not in source


def test_private_storage_writes_are_scoped_to_authenticated_owner() -> None:
    source = app_source()

    assert "state.preferenceUserId" in source
    assert "ownerStorageKey" in source or "scopedStorageKey" in source
    assert "store(FEEDBACK_STORAGE_KEY, state.feedback)" not in source
    assert "store(BOOKMARK_STORAGE_KEY, [...state.bookmarks])" not in source
    assert "store(COMPARISON_STORAGE_KEY, state.comparison)" not in source
    assert "store(LIVE_SNAPSHOT_STORAGE_KEY" not in source


def test_preference_migration_runs_after_authenticated_owner_is_known() -> None:
    source = app_source()
    block = function_block(source, "async function connectPreferences()", "  function parseStructuredFeedbackNote")

    identity_index = block.index("state.preferenceUserId =")
    bookmark_migration_index = block.index("migrateLocalBookmarks()")
    feedback_migration_index = block.index("migrateLegacyFeedback()")

    assert identity_index < bookmark_migration_index
    assert identity_index < feedback_migration_index


def test_supabase_polling_outage_is_not_a_terminal_refresh_state() -> None:
    source = app_source()

    assert '"connection_failed"' not in source
    assert "renderRefreshConnectionFailure" not in source


def test_refresh_reconnect_checks_supabase_for_active_runs_without_cached_watch_gate() -> None:
    source = app_source()
    block = function_block(source, "async function connectRefreshQueue()", "  function graduateLineageMatches")

    active_index = block.index("activeRefreshRun()")
    cached_watch_index = block.find("readJSON(REFRESH_WATCH_STORAGE_KEY")

    assert cached_watch_index == -1 or active_index < cached_watch_index


def test_refresh_reconnect_is_triggered_by_browser_resume_events() -> None:
    source = app_source()

    assert 'addEventListener("online"' in source
    assert 'addEventListener("focus"' in source
    assert 'addEventListener("visibilitychange"' in source


def test_succeeded_backend_run_with_snapshot_mismatch_is_publication_pending() -> None:
    source = app_source()
    block = function_block(source, "function renderRefreshErrorState(status, error)", "  async function watchRefresh()")

    assert "publication_pending" in block or "snapshot_publication_pending" in block
    assert 'state: "failed"' not in block


def test_refresh_status_cache_is_scoped_to_authenticated_owner() -> None:
    source = app_source()

    assert "store(REFRESH_STATUS_STORAGE_KEY, status)" not in source
    assert "readJSON(REFRESH_STATUS_STORAGE_KEY" not in source


def test_refresh_watch_cache_is_scoped_to_authenticated_owner() -> None:
    source = app_source()

    assert "store(REFRESH_WATCH_STORAGE_KEY" not in source
    assert "readJSON(REFRESH_WATCH_STORAGE_KEY" not in source

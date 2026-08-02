from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "app.js"


def app_source() -> str:
    return APP_JS.read_text(encoding="utf-8")


def function_block(source: str, signature: str, next_signature: str) -> str:
    start = source.index(signature)
    end = source.index(next_signature, start)
    return source[start:end]


def run_node(script: str) -> dict:
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def merge_candidates(payload: dict) -> dict:
    source = app_source()
    function = function_block(source, "function mergePreferenceCandidates", "  function saveFilters")
    return run_node(
        f"{function}\n"
        f"const result = mergePreferenceCandidates({json.dumps(payload)});\n"
        "console.log(JSON.stringify(result));"
    )


def test_explicit_remote_dislike_beats_legacy_liked_bookmark() -> None:
    result = merge_candidates(
        {
            "remoteRows": [
                {
                    "job_id": "job-1",
                    "sentiment": "not_for_me",
                    "reasons": ["role:wrong_fit"],
                    "note": "explicit dislike",
                    "updated_at": "2026-08-02T00:00:00.000Z",
                    "job_snapshot": {"feedback_revision": "remote-r1"},
                }
            ],
            "legacyBookmarks": ["job-1"],
            "migrationTimestamp": "2026-08-02T01:00:00.000Z",
        }
    )

    assert result["feedback"]["job-1"]["sentiment"] == "not_for_me"
    assert result["feedback"]["job-1"]["preferenceSource"] == "explicit_remote"
    assert result["migrationCandidates"] == []


def test_missing_remote_row_creates_provenanced_legacy_migration_candidate() -> None:
    migrated_at = "2026-08-02T01:00:00.000Z"
    result = merge_candidates(
        {
            "remoteRows": [],
            "legacyBookmarks": ["job-legacy"],
            "migrationTimestamp": migrated_at,
        }
    )

    preference = result["feedback"]["job-legacy"]
    assert preference["sentiment"] == "liked"
    assert preference["preferenceSource"] == "legacy_bookmark"
    assert preference["migrationProvenance"] == {
        "source": "legacy_bookmark",
        "migratedAt": migrated_at,
    }
    assert result["migrationCandidates"] == [
        {"jobId": "job-legacy", "preference": preference}
    ]


def test_supabase_failure_keeps_pending_outbox_entry_unacknowledged() -> None:
    source = app_source()
    ack_error = function_block(source, "function preferenceAckRequired", "  function recordPreferenceAcknowledgement")
    flush = function_block(source, "async function performPreferenceOutboxFlush", "  /* data-requirement-id=\"DATA-270\" */")
    result = run_node(
        f"{ack_error}\n{flush}\n"
        "const entry = {userId: 'owner-1', jobId: 'job-1', operation: 'upsert', "
        "preference: {sentiment: 'liked'}, feedback_revision: 'local-r1'};\n"
        "let persistCalls = 0; let acknowledgementCalls = 0;\n"
        "const failingBuilder = {select() { return {async maybeSingle() { "
        "return {data: null, error: new Error('offline')}; }}; }};\n"
        "const state = {preferenceUserId: 'owner-1', pendingPreferenceWrites: {'job-1': entry}, "
        "preferenceClient: {from() { return {upsert() { return failingBuilder; }}; }}};\n"
        "function preferencePayload() { return {}; }\n"
        "function persistPreferenceOutbox() { persistCalls += 1; }\n"
        "function recordPreferenceAcknowledgement() { acknowledgementCalls += 1; "
        "delete state.pendingPreferenceWrites['job-1']; }\n"
        "(async () => { let errorCode = null; try { await performPreferenceOutboxFlush(); } "
        "catch (error) { errorCode = error.code; } console.log(JSON.stringify({errorCode, persistCalls, "
        "acknowledgementCalls, pending: Boolean(state.pendingPreferenceWrites['job-1'])})); })();"
    )

    assert result == {
        "errorCode": "PREFERENCE_ACK_REQUIRED",
        "persistCalls": 1,
        "acknowledgementCalls": 0,
        "pending": True,
    }


def test_refresh_does_not_enqueue_when_preference_ack_flush_fails() -> None:
    source = app_source()
    refresh = function_block(source, "async function refreshEngine", "  async function connectRefreshQueue")
    result = run_node(
        f"{refresh}\n"
        "let enqueueCalls = 0; const state = {preferenceClient: {}, preferenceUserId: 'owner-1', "
        "feedback: {}, pendingPreferenceWrites: {'job-1': {}}, refreshConnectionErrors: 0};\n"
        "const engineRefresh = {disabled: false}; const snapshotLabel = {textContent: ''};\n"
        "const REFRESH_WATCH_STORAGE_KEY = 'watch';\n"
        "function setEngineBusy() {} function storeOwner() {} function renderRefreshMonitor() {}\n"
        "async function flushPreferenceOutbox() { const error = new Error('offline'); "
        "error.code = 'PREFERENCE_ACK_REQUIRED'; throw error; }\n"
        "async function enqueueRefreshRun() { enqueueCalls += 1; return {id: 'run-1'}; }\n"
        "async function watchRefresh() {} function stopRefreshPolling() {}\n"
        "function refreshErrorLabel() { return 'retry'; } function renderRefreshConnectionUnavailable() {}\n"
        "console.error = () => {};\n"
        "(async () => { await refreshEngine(); console.log(JSON.stringify({enqueueCalls, "
        "pending: Boolean(state.pendingPreferenceWrites['job-1']), label: snapshotLabel.textContent})); })();"
    )

    assert result["enqueueCalls"] == 0
    assert result["pending"] is True
    assert result["label"] == "retry"


def test_ack_gate_and_owner_scoped_storage_markers_are_present() -> None:
    source = app_source()
    refresh = function_block(source, "async function refreshEngine", "  async function connectRefreshQueue")

    assert 'data-requirement-id="DATA-270"' in source
    assert 'data-requirement-id="DATA-271"' in source
    assert "feedback_revision" in source
    assert "migrationProvenance" in source
    assert "explicit_remote" in source
    assert "legacy_bookmark" in source
    assert "ownerStorageKey(PREFERENCE_OUTBOX_STORAGE_KEY)" in source
    assert refresh.index("await flushPreferenceOutbox()") < refresh.index("await enqueueRefreshRun()")

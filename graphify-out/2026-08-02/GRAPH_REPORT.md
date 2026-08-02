# Graph Report - career-job-compass  (2026-08-02)

## Corpus Check
- 43 files · ~577,937 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 669 nodes · 1706 edges · 39 communities (31 shown, 8 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `eb590df1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- connectPreferences
- build_snapshot.py
- escapeHtml
- Career Compass — calm field guide
- watchRefresh
- watchRefresh
- Calm field guide motion plan
- check_release.py
- Career Compass
- ⚠ 볼트 우선 계약 — 모든 에이전트 공통 (Claude / Codex / Gemini / agy)
- Requirement Checks
- sw.js
- plans/README.md
- expand_graduate_evidence.py
- CLAUDE.md
- _site/sw.js
- refreshRunStatus
- app.js
- _site/app.js
- renderJobs
- escapeHtml
- renderJobs
- renderLifestyle
- renderSources
- renderSaved
- isSnapshot
- refreshRunStatus
- renderLifestyle
- test_public_privacy_release_gate.py
- lifestyleCard
- test_mobile_identity_refresh_contract.py
- test_graduate_lineage_contract.py
- test_feedback_ack_conflict_contract.py
- RefreshRunLineageMigrationContractTests
- RefreshClaimFencingMigrationTests

## God Nodes (most connected - your core abstractions)
1. `escapeHtml()` - 34 edges
2. `escapeHtml()` - 34 edges
3. `_apply_lifestyle_discovery()` - 25 edges
4. `renderLifestyle()` - 21 edges
5. `renderLifestyle()` - 21 edges
6. `_public_research()` - 18 edges
7. `Career Compass — calm field guide` - 18 edges
8. `renderSources()` - 17 edges
9. `renderSources()` - 17 edges
10. `renderJobs()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `test_recent_window_rejects_unknown_and_future_only_periods()` --calls--> `current_or_recent_years()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py
- `test_funded_project_requires_funder_and_stable_public_evidence()` --calls--> `verified_funded_project()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py
- `test_explicit_none_requires_source_evidence()` --calls--> `_public_research()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py
- `test_public_research_preserves_claim_context_without_alumni_identity()` --calls--> `_public_research()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py
- `test_untyped_sources_remain_unknown_quality()` --calls--> `_public_research()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py

## Import Cycles
- None detected.

## Communities (39 total, 8 thin omitted)

### Community 0 - "connectPreferences"
Cohesion: 0.16
Nodes (24): connectPreferences(), createFeedbackRevision(), flushPreferenceOutbox(), importFeedbackBackup(), jobSnapshot(), mergePreferenceCandidates(), migrateLegacyFeedback(), migrateLocalBookmarks() (+16 more)

### Community 1 - "build_snapshot.py"
Cohesion: 0.06
Nodes (91): Pattern, _application_readiness(), _apply_decision_support(), _apply_latest_programs(), _apply_lifestyle_discovery(), _apply_public_eligibility(), assert_active_repository(), _atomic_write_json() (+83 more)

### Community 2 - "escapeHtml"
Cohesion: 0.11
Nodes (33): candidateRow(), comparisonKey(), decisionFrameworkDomainRows(), decisionFrameworkPanel(), decisionSupportPanel(), detailList(), effectivePreferenceFor(), escapeHtml() (+25 more)

### Community 3 - "Career Compass — calm field guide"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 4 - "watchRefresh"
Cohesion: 0.24
Nodes (16): activeRefreshRun(), connectRefreshQueue(), enqueueRefreshRun(), formatRuntime(), loadLastSuccessfulRefresh(), refreshEngine(), refreshErrorLabel(), refreshStatus() (+8 more)

### Community 5 - "watchRefresh"
Cohesion: 0.20
Nodes (18): activeRefreshRun(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), connectRefreshQueue(), enqueueRefreshRun(), formatRuntime(), loadLastSuccessfulRefresh(), pendingPreferenceCount() (+10 more)

### Community 6 - "Calm field guide motion plan"
Cohesion: 0.33
Nodes (5): Audit findings, Calm field guide motion plan, Rollback boundary, Token contract, Verification after implementation

### Community 7 - "check_release.py"
Cohesion: 0.07
Nodes (48): _archive_kind(), _contains_float(), contains_forbidden_key(), contains_non_contract_research(), _count_candidate_classes(), _count_statuses(), _expected_lifestyle_readiness(), experienced_only_title() (+40 more)

### Community 8 - "Career Compass"
Cohesion: 0.40
Nodes (4): Career Compass, Local preview, Refresh model, Release boundary

### Community 14 - "expand_graduate_evidence.py"
Cohesion: 0.28
Nodes (15): build_coverage_report(), has_funded_projects(), has_recent_papers(), is_recent_five_years(), main(), merge_named(), merge_patch(), program_key() (+7 more)

### Community 17 - "refreshRunStatus"
Cohesion: 0.40
Nodes (11): completedSnapshotBinding(), completedSnapshotMatches(), loadMatchingCompletedSnapshot(), refreshRunStatus(), refreshStatus(), safeRefreshGate(), safeRefreshLoopPolicy(), safeRefreshNumber() (+3 more)

### Community 19 - "app.js"
Cohesion: 0.08
Nodes (41): allJobSectors(), BridgeError, buildFeedbackExport(), canonicalJSONString(), clearPrivateState(), exportFeedback(), exportFeedbackBackup(), feedbackBackupPayload() (+33 more)

### Community 20 - "_site/app.js"
Cohesion: 0.09
Nodes (31): authenticatedRefreshHeaders(), authenticatedRefreshRequest(), BridgeError, buildFeedbackExport(), canonicalJSONString(), exportFeedback(), exportFeedbackBackup(), feedbackBackupPayload() (+23 more)

### Community 21 - "renderJobs"
Cohesion: 0.12
Nodes (35): activeFilters(), candidateRow(), chunks(), closeDetail(), comparisonRecords(), diversifiedJobs(), filteredJobs(), filteredStudy() (+27 more)

### Community 22 - "escapeHtml"
Cohesion: 0.11
Nodes (35): comparisonCard(), comparisonKey(), decisionFrameworkDomainRows(), decisionFrameworkPanel(), decisionSupportPanel(), detailList(), displayDate(), effectivePreferenceFor() (+27 more)

### Community 23 - "renderJobs"
Cohesion: 0.13
Nodes (31): activeFilters(), chunks(), closeDetail(), diversifiedJobs(), filteredJobs(), filteredStudy(), funding(), go() (+23 more)

### Community 24 - "renderLifestyle"
Cohesion: 0.23
Nodes (17): lifestyleAxisCounts(), lifestyleCount(), lifestyleDateTime(), lifestyleDiscovery(), lifestyleFilterFlow(), lifestyleGlobalFilterCounts(), lifestyleItemById(), lifestyleItemIsVerified() (+9 more)

### Community 25 - "renderSources"
Cohesion: 0.12
Nodes (31): clearPrivateState(), connectPreferences(), createFeedbackRevision(), displayDate(), feedbackBackupPanel(), feedbackReviewList(), flushPreferenceOutbox(), importFeedbackBackup() (+23 more)

### Community 26 - "renderSaved"
Cohesion: 0.24
Nodes (10): allJobSectors(), comparisonCard(), comparisonRecords(), jobById(), jobs(), normalizeFilters(), openFilters(), openJobDetail() (+2 more)

### Community 27 - "isSnapshot"
Cohesion: 0.29
Nodes (11): graduateLineageMatches(), isSnapshot(), load(), loadCloudSnapshot(), mergeGraduateEvidence(), renderError(), selectFreshestSnapshot(), setSnapshot() (+3 more)

### Community 28 - "refreshRunStatus"
Cohesion: 0.47
Nodes (10): completedSnapshotBinding(), completedSnapshotMatches(), loadMatchingCompletedSnapshot(), refreshRunStatus(), safeRefreshGate(), safeRefreshLoopPolicy(), safeRefreshNumber(), safeRefreshPhase() (+2 more)

### Community 29 - "renderLifestyle"
Cohesion: 0.23
Nodes (17): lifestyleAxisCounts(), lifestyleCount(), lifestyleDateTime(), lifestyleDiscovery(), lifestyleFilterFlow(), lifestyleGlobalFilterCounts(), lifestyleItemById(), lifestyleItemIsVerified() (+9 more)

### Community 30 - "test_public_privacy_release_gate.py"
Cohesion: 0.27
Nodes (15): parametrize, _anonymous_snapshot(), _module(), Path, test_actual_private_values_or_keys_fail_closed(), test_anonymous_aggregate_shape_is_not_mistaken_for_personal_data(), test_existing_site_data_copy_must_match_canonical_snapshot(), test_existing_site_without_verifiable_data_fails_closed() (+7 more)

### Community 31 - "lifestyleCard"
Cohesion: 0.28
Nodes (9): lifestyleAxis(), lifestyleCandidateLabel(), lifestyleCard(), lifestyleEvidenceTexts(), lifestyleItemLaneFilter(), lifestyleList(), lifestyleSignalTexts(), lifestyleSourceLabel() (+1 more)

### Community 32 - "test_mobile_identity_refresh_contract.py"
Cohesion: 0.32
Nodes (12): app_source(), function_block(), test_preference_migration_runs_after_authenticated_owner_is_known(), test_private_feedback_is_not_hydrated_before_supabase_identity(), test_private_live_snapshot_is_not_used_before_supabase_identity(), test_private_storage_writes_are_scoped_to_authenticated_owner(), test_refresh_reconnect_checks_supabase_for_active_runs_without_cached_watch_gate(), test_refresh_reconnect_is_triggered_by_browser_resume_events() (+4 more)

### Community 33 - "test_graduate_lineage_contract.py"
Cohesion: 0.47
Nodes (4): _module(), Path, test_graduate_lineage_binds_every_source_role_and_validates(), test_graduate_lineage_rejects_a_missing_source_role()

### Community 34 - "test_feedback_ack_conflict_contract.py"
Cohesion: 0.49
Nodes (9): app_source(), function_block(), merge_candidates(), run_node(), test_ack_gate_and_owner_scoped_storage_markers_are_present(), test_explicit_remote_dislike_beats_legacy_liked_bookmark(), test_missing_remote_row_creates_provenanced_legacy_migration_candidate(), test_refresh_does_not_enqueue_when_preference_ack_flush_fails() (+1 more)

## Knowledge Gaps
- **31 isolated node(s):** `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES`, `APP_SHELL`, `graphify` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `escapeHtml()` connect `escapeHtml` to `_site/app.js`, `renderJobs`, `renderSources`, `renderSaved`, `renderLifestyle`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `escapeHtml()` connect `escapeHtml` to `renderLifestyle`, `app.js`, `renderJobs`, `lifestyleCard`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **What connects `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `build_snapshot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055364905056051246 - nodes in this community are weakly interconnected._
- **Should `escapeHtml` be split into smaller, more focused modules?**
  _Cohesion score 0.10984848484848485 - nodes in this community are weakly interconnected._
- **Should `Career Compass — calm field guide` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `check_release.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07450980392156863 - nodes in this community are weakly interconnected._
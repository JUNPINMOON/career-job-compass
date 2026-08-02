# Graph Report - career-job-compass  (2026-08-03)

## Corpus Check
- 47 files · ~592,602 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 732 nodes · 1868 edges · 51 communities (43 shown, 8 thin omitted)
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
- connectPreferences
- renderSources
- _public_research
- main
- renderLifestyle
- test_public_privacy_release_gate.py
- renderSources
- test_mobile_identity_refresh_contract.py
- test_graduate_lineage_contract.py
- test_feedback_ack_conflict_contract.py
- RefreshRunLineageMigrationContractTests
- RefreshClaimFencingMigrationTests
- _decision_framework
- Any
- lifestyleCard
- lifestyleCard
- _apply_latest_programs
- _program_decision_support
- _apply_public_eligibility
- test_mobile_truth_semantics.py
- test_public_program_privacy_contract.py
- _sanitize_public_programs
- render
- test_graduate_public_privacy_release_guard.py

## God Nodes (most connected - your core abstractions)
1. `escapeHtml()` - 35 edges
2. `escapeHtml()` - 35 edges
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
- `test_empty_research_is_unknown_and_never_rendered_as_verified_zero()` --calls--> `_public_research()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py
- `test_explicit_none_requires_source_evidence()` --calls--> `_public_research()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py
- `test_public_research_preserves_claim_context_without_alumni_identity()` --calls--> `_public_research()`  [EXTRACTED]
  tests/test_graduate_evidence_contract.py → scripts/build_snapshot.py

## Import Cycles
- None detected.

## Communities (51 total, 8 thin omitted)

### Community 0 - "connectPreferences"
Cohesion: 0.13
Nodes (26): clearPrivateState(), connectPreferences(), createFeedbackRevision(), flushPreferenceOutbox(), importFeedbackBackup(), includesAny(), jobSnapshot(), mergePreferenceCandidates() (+18 more)

### Community 1 - "build_snapshot.py"
Cohesion: 0.15
Nodes (26): Pattern, _apply_lifestyle_discovery(), _axis_counts(), _candidate_class_counts(), _combined_lifestyle_status(), _decision_readiness(), _empty_filter_counts(), _entry_signals() (+18 more)

### Community 2 - "escapeHtml"
Cohesion: 0.16
Nodes (24): comparisonCard(), comparisonKey(), decisionFrameworkDomainRows(), decisionFrameworkPanel(), decisionSupportPanel(), detailList(), escapeHtml(), evidenceItem() (+16 more)

### Community 3 - "Career Compass — calm field guide"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 4 - "watchRefresh"
Cohesion: 0.11
Nodes (38): activeRefreshRun(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), clearPrivateState(), completedSnapshotBinding(), completedSnapshotMatches(), connectRefreshQueue(), enqueueRefreshRun() (+30 more)

### Community 5 - "watchRefresh"
Cohesion: 0.21
Nodes (18): activeRefreshRun(), comparisonKey(), connectRefreshQueue(), enqueueRefreshRun(), formatRuntime(), isCompared(), loadLastSuccessfulRefresh(), refreshEngine() (+10 more)

### Community 6 - "Calm field guide motion plan"
Cohesion: 0.33
Nodes (5): Audit findings, Calm field guide motion plan, Rollback boundary, Token contract, Verification after implementation

### Community 7 - "check_release.py"
Cohesion: 0.07
Nodes (50): _archive_kind(), _contains_float(), contains_forbidden_key(), contains_non_contract_research(), _count_candidate_classes(), _count_statuses(), _expected_lifestyle_readiness(), experienced_only_title() (+42 more)

### Community 8 - "Career Compass"
Cohesion: 0.40
Nodes (4): Career Compass, Local preview, Refresh model, Release boundary

### Community 14 - "expand_graduate_evidence.py"
Cohesion: 0.28
Nodes (15): build_coverage_report(), has_funded_projects(), has_recent_papers(), is_recent_five_years(), main(), merge_named(), merge_patch(), program_key() (+7 more)

### Community 17 - "refreshRunStatus"
Cohesion: 0.44
Nodes (10): completedSnapshotBinding(), completedSnapshotMatches(), refreshRunStatus(), refreshStatus(), safeRefreshGate(), safeRefreshLoopPolicy(), safeRefreshNumber(), safeRefreshPhase() (+2 more)

### Community 19 - "app.js"
Cohesion: 0.08
Nodes (41): allJobSectors(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), BridgeError, buildFeedbackExport(), canonicalJSONString(), exportFeedback(), exportFeedbackBackup() (+33 more)

### Community 20 - "_site/app.js"
Cohesion: 0.09
Nodes (32): allJobSectors(), BridgeError, buildFeedbackExport(), canonicalJSONString(), exportFeedback(), exportFeedbackBackup(), feedbackBackupPayload(), includesAny() (+24 more)

### Community 21 - "renderJobs"
Cohesion: 0.17
Nodes (23): activeFilters(), chunks(), diversifiedJobs(), filteredJobs(), filteredStudy(), funding(), jobSectors(), marketCount() (+15 more)

### Community 22 - "escapeHtml"
Cohesion: 0.12
Nodes (32): candidateRow(), decisionFrameworkDomainRows(), decisionFrameworkPanel(), decisionSupportPanel(), detailList(), effectivePreferenceFor(), escapeHtml(), evidenceItem() (+24 more)

### Community 23 - "renderJobs"
Cohesion: 0.14
Nodes (30): activeFilters(), candidateRow(), chunks(), diversifiedJobs(), effectivePreferenceFor(), filteredJobs(), filteredStudy(), funding() (+22 more)

### Community 24 - "renderLifestyle"
Cohesion: 0.23
Nodes (17): lifestyleAxisCounts(), lifestyleCount(), lifestyleDateTime(), lifestyleDiscovery(), lifestyleFilterFlow(), lifestyleGlobalFilterCounts(), lifestyleItemById(), lifestyleItemIsVerified() (+9 more)

### Community 25 - "connectPreferences"
Cohesion: 0.15
Nodes (24): connectPreferences(), createFeedbackRevision(), flushPreferenceOutbox(), hydrateOwnerState(), mergePreferenceCandidates(), migrateLegacyFeedback(), migrateLocalBookmarks(), normalizeLegacyFeedbackPreference() (+16 more)

### Community 26 - "renderSources"
Cohesion: 0.21
Nodes (13): comparisonRecords(), displayDate(), feedbackBackupPanel(), feedbackReviewList(), importFeedbackBackup(), jobById(), jobs(), openJobDetail() (+5 more)

### Community 27 - "_public_research"
Cohesion: 0.13
Nodes (24): current_or_recent_years(), _evidence_quality(), _first_text(), _graduate_claim_axis(), _public_program_from_research(), _public_research(), _public_url(), DATA-254: accept only an evidenced year in the current five-year window.… (+16 more)

### Community 28 - "main"
Cohesion: 0.17
Nodes (19): assert_active_repository(), _atomic_write_json(), _decision_framework_source_metrics(), _file_sha256(), _graduate_data_lineage(), _graduate_evidence_coverage(), _lineage_artifact(), main() (+11 more)

### Community 29 - "renderLifestyle"
Cohesion: 0.23
Nodes (17): lifestyleAxisCounts(), lifestyleCount(), lifestyleDateTime(), lifestyleDiscovery(), lifestyleFilterFlow(), lifestyleGlobalFilterCounts(), lifestyleItemById(), lifestyleItemIsVerified() (+9 more)

### Community 30 - "test_public_privacy_release_gate.py"
Cohesion: 0.27
Nodes (15): _anonymous_snapshot(), _module(), parametrize, Path, test_actual_private_values_or_keys_fail_closed(), test_anonymous_aggregate_shape_is_not_mistaken_for_personal_data(), test_existing_site_data_copy_must_match_canonical_snapshot(), test_existing_site_without_verifiable_data_fails_closed() (+7 more)

### Community 31 - "renderSources"
Cohesion: 0.15
Nodes (19): closeDetail(), comparisonCard(), comparisonRecords(), displayDate(), feedbackBackupPanel(), go(), jobById(), jobs() (+11 more)

### Community 32 - "test_mobile_identity_refresh_contract.py"
Cohesion: 0.32
Nodes (12): app_source(), function_block(), test_preference_migration_runs_after_authenticated_owner_is_known(), test_private_feedback_is_not_hydrated_before_supabase_identity(), test_private_live_snapshot_is_not_used_before_supabase_identity(), test_private_storage_writes_are_scoped_to_authenticated_owner(), test_refresh_reconnect_checks_supabase_for_active_runs_without_cached_watch_gate(), test_refresh_reconnect_is_triggered_by_browser_resume_events() (+4 more)

### Community 33 - "test_graduate_lineage_contract.py"
Cohesion: 0.43
Nodes (5): _module(), Path, test_graduate_lineage_binds_every_source_role_and_validates(), test_graduate_lineage_rejects_a_missing_source_role(), test_shortlist_consumer_requires_the_exact_enriched_research_source()

### Community 34 - "test_feedback_ack_conflict_contract.py"
Cohesion: 0.49
Nodes (9): app_source(), function_block(), merge_candidates(), run_node(), test_ack_gate_and_owner_scoped_storage_markers_are_present(), test_explicit_remote_dislike_beats_legacy_liked_bookmark(), test_missing_remote_row_creates_provenanced_legacy_migration_candidate(), test_refresh_does_not_enqueue_when_preference_ack_flush_fails() (+1 more)

### Community 39 - "_decision_framework"
Cohesion: 0.44
Nodes (13): _decision_framework(), Any, _sample_payload(), _subfields(), test_all_unverified_jobs_are_explicitly_exploration_only(), test_currentness_and_new_deep_domains_keep_unknowns_visible(), test_decision_framework_v3_contains_required_expandable_contract(), test_every_framework_subfield_has_truthful_operational_state() (+5 more)

### Community 40 - "Any"
Cohesion: 0.23
Nodes (16): _canonical_job_url(), _decision_readiness_boundary(), _framework_domain(), _framework_domains(), _framework_operational_states(), _framework_state(), _framework_subfield(), _graduate_admissions_requirement_metrics() (+8 more)

### Community 41 - "lifestyleCard"
Cohesion: 0.20
Nodes (12): jobSnapshot(), lifestyleAxis(), lifestyleCandidateLabel(), lifestyleCard(), lifestyleEvidenceTexts(), lifestyleItemLaneFilter(), lifestyleList(), lifestyleSignalTexts() (+4 more)

### Community 42 - "lifestyleCard"
Cohesion: 0.28
Nodes (9): lifestyleAxis(), lifestyleCandidateLabel(), lifestyleCard(), lifestyleEvidenceTexts(), lifestyleItemLaneFilter(), lifestyleList(), lifestyleSignalTexts(), lifestyleSourceLabel() (+1 more)

### Community 43 - "_apply_latest_programs"
Cohesion: 0.29
Nodes (8): _application_readiness(), _apply_latest_programs(), _key(), Keep an actionable preparation lane distinct from a verified open call. The…, DATA-282: reject a shortlist that was not built from this research artifact., Refresh compact programme records from the lightweight current shortlist., _read_json_list(), _validate_shortlist_source_lineage()

### Community 44 - "_program_decision_support"
Cohesion: 0.40
Nodes (6): _apply_decision_support(), _fact(), _job_decision_support(), _program_decision_support(), DATA-233: confirmed facts and unresolved questions., test_empty_research_is_unknown_and_never_rendered_as_verified_zero()

### Community 45 - "_apply_public_eligibility"
Cohesion: 0.33
Nodes (6): _apply_public_eligibility(), experienced_only_title(), DATA-210: recheck eligibility and canonical duplicates after expansion., DATA-214: fail closed when the title itself explicitly says 경력직., DATA-215: keep employer context from turning Finance Intern into a technical…, support_only_title()

### Community 46 - "test_mobile_truth_semantics.py"
Cohesion: 0.60
Nodes (5): _function_block(), test_comparison_card_keeps_funding_record_kind_for_detail_route(), test_exploration_only_source_stat_uses_exploration_inventory_semantics(), test_program_ui_describes_public_evidence_not_private_readiness(), test_source_link_copy_is_truthful_and_job_official_status_is_evidence_gated()

### Community 47 - "test_public_program_privacy_contract.py"
Cohesion: 0.60
Nodes (5): _private_program(), _serialized(), test_generated_public_snapshot_contains_no_private_graduate_readiness(), test_public_program_sanitizer_removes_private_readiness_without_erasing_official_facts(), test_release_gate_rejects_private_graduate_readiness_and_accepts_sanitized_programs()

### Community 48 - "_sanitize_public_programs"
Cohesion: 0.50
Nodes (5): _public_program_key(), Fail closed when a public programme record still contains private readiness., _sanitize_public_program_value(), _sanitize_public_programs(), _strip_private_program_text()

### Community 49 - "render"
Cohesion: 0.40
Nodes (5): closeDetail(), go(), render(), renderStudy(), setActiveTab()

### Community 50 - "test_graduate_public_privacy_release_guard.py"
Cohesion: 0.50
Nodes (3): parametrize, test_public_graduate_privacy_violation_detects_private_keys_recursively(), test_public_graduate_privacy_violation_detects_private_readiness_without_echoing_it()

## Knowledge Gaps
- **31 isolated node(s):** `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES`, `APP_SHELL`, `graphify` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_decision_framework()` connect `_decision_framework` to `Any`, `build_snapshot.py`, `main`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **Why does `_public_research()` connect `_public_research` to `Any`, `build_snapshot.py`, `_apply_latest_programs`, `_program_decision_support`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Why does `_apply_lifestyle_discovery()` connect `build_snapshot.py` to `Any`, `main`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **What connects `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `connectPreferences` be split into smaller, more focused modules?**
  _Cohesion score 0.13230769230769232 - nodes in this community are weakly interconnected._
- **Should `Career Compass — calm field guide` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `watchRefresh` be split into smaller, more focused modules?**
  _Cohesion score 0.10668563300142248 - nodes in this community are weakly interconnected._
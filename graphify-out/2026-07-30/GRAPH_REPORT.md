# Graph Report - career-job-compass  (2026-07-30)

## Corpus Check
- 31 files · ~582,273 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 352 nodes · 894 edges · 29 communities (22 shown, 7 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6af9d871`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- renderSources
- build_snapshot.py
- escapeHtml
- Career Compass — calm field guide
- _site/app.js
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
- app.js
- renderToday
- renderToday
- escapeHtml
- renderSources
- renderJobs
- jobs
- watchRefresh
- renderJobs
- BridgeError

## God Nodes (most connected - your core abstractions)
1. `escapeHtml()` - 23 edges
2. `escapeHtml()` - 23 edges
3. `Career Compass — calm field guide` - 18 edges
4. `renderJobs()` - 15 edges
5. `renderSources()` - 15 edges
6. `renderJobs()` - 15 edges
7. `renderSources()` - 15 edges
8. `renderToday()` - 14 edges
9. `renderToday()` - 14 edges
10. `renderStudy()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `renderSaved()` --indirect_call--> `comparisonCard()`  [INFERRED]
  _site/app.js → _site/app.js  _Bridges community 2 → community 20_
- `renderSaved()` --indirect_call--> `comparisonCard()`  [INFERRED]
  app.js → app.js  _Bridges community 22 → community 21_
- `persistPreferences()` --calls--> `store()`  [EXTRACTED]
  _site/app.js → _site/app.js  _Bridges community 4 → community 23_
- `refreshEngine()` --calls--> `store()`  [EXTRACTED]
  _site/app.js → _site/app.js  _Bridges community 4 → community 26_
- `saveFilters()` --calls--> `store()`  [EXTRACTED]
  _site/app.js → _site/app.js  _Bridges community 4 → community 27_

## Import Cycles
- None detected.

## Communities (29 total, 7 thin omitted)

### Community 0 - "renderSources"
Cohesion: 0.17
Nodes (19): connectPreferences(), displayDate(), feedbackBackupPanel(), feedbackReviewList(), importFeedbackBackup(), jobById(), jobSnapshot(), migrateLocalBookmarks() (+11 more)

### Community 1 - "build_snapshot.py"
Cohesion: 0.12
Nodes (38): _application_readiness(), _apply_decision_support(), _apply_latest_programs(), _apply_public_eligibility(), experienced_only_title(), _fact(), _graduate_data_lineage(), _graduate_evidence_coverage() (+30 more)

### Community 2 - "escapeHtml"
Cohesion: 0.23
Nodes (16): comparisonCard(), comparisonKey(), decisionSupportPanel(), detailList(), escapeHtml(), evidenceItem(), evidenceSources(), graduateResearchPanels() (+8 more)

### Community 3 - "Career Compass — calm field guide"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 4 - "_site/app.js"
Cohesion: 0.17
Nodes (23): activeRefreshRun(), allJobSectors(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), connectRefreshQueue(), enqueueRefreshRun(), graduateLineageMatches(), isSnapshot() (+15 more)

### Community 5 - "watchRefresh"
Cohesion: 0.13
Nodes (28): activeRefreshRun(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), connectRefreshQueue(), enqueueRefreshRun(), formatRuntime(), graduateLineageMatches(), isSnapshot() (+20 more)

### Community 6 - "Calm field guide motion plan"
Cohesion: 0.33
Nodes (5): Audit findings, Calm field guide motion plan, Rollback boundary, Token contract, Verification after implementation

### Community 7 - "check_release.py"
Cohesion: 0.26
Nodes (11): contains_forbidden_key(), contains_non_contract_research(), experienced_only_title(), main(), Path, Dependency-free release checks for the static Career Compass PWA., Mirror DATA-215 at the release boundary., Mirror DATA-216 at the release boundary. (+3 more)

### Community 8 - "Career Compass"
Cohesion: 0.40
Nodes (4): Career Compass, Local preview, Refresh model, Release boundary

### Community 14 - "expand_graduate_evidence.py"
Cohesion: 0.28
Nodes (15): build_coverage_report(), has_funded_projects(), has_recent_papers(), is_recent_five_years(), main(), merge_named(), merge_patch(), program_key() (+7 more)

### Community 19 - "app.js"
Cohesion: 0.11
Nodes (25): allJobSectors(), BridgeError, buildFeedbackExport(), closeDetail(), exportFeedback(), exportFeedbackBackup(), feedbackBackupPayload(), go() (+17 more)

### Community 20 - "renderToday"
Cohesion: 0.23
Nodes (19): candidateRow(), chunks(), comparisonRecords(), diversifiedJobs(), filteredStudy(), funding(), icon(), openRecordDetail() (+11 more)

### Community 21 - "renderToday"
Cohesion: 0.25
Nodes (17): candidateRow(), chunks(), comparisonRecords(), filteredStudy(), funding(), icon(), openRecordDetail(), pageFrame() (+9 more)

### Community 22 - "escapeHtml"
Cohesion: 0.23
Nodes (16): comparisonCard(), comparisonKey(), decisionSupportPanel(), detailList(), escapeHtml(), evidenceItem(), evidenceSources(), graduateResearchPanels() (+8 more)

### Community 23 - "renderSources"
Cohesion: 0.15
Nodes (22): closeDetail(), connectPreferences(), displayDate(), feedbackBackupPanel(), feedbackReviewList(), go(), importFeedbackBackup(), migrateLocalBookmarks() (+14 more)

### Community 24 - "renderJobs"
Cohesion: 0.31
Nodes (9): activeFilters(), diversifiedJobs(), filteredJobs(), jobSectors(), marketCount(), marketSwitch(), recommendationJobs(), renderJobResults() (+1 more)

### Community 25 - "jobs"
Cohesion: 0.20
Nodes (10): buildFeedbackExport(), exportFeedback(), exportFeedbackBackup(), feedbackBackupPayload(), isEligiblePublicJob(), jobById(), jobs(), openJobDetail() (+2 more)

### Community 26 - "watchRefresh"
Cohesion: 0.31
Nodes (11): formatRuntime(), refreshEngine(), refreshErrorLabel(), refreshEstimate(), refreshRunStatus(), refreshStatus(), renderRefreshConnectionFailure(), renderRefreshMonitor() (+3 more)

### Community 27 - "renderJobs"
Cohesion: 0.27
Nodes (10): activeFilters(), filteredJobs(), jobSectors(), jobSnapshot(), marketCount(), marketSwitch(), recommendationJobs(), renderJobs() (+2 more)

## Knowledge Gaps
- **31 isolated node(s):** `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES`, `APP_SHELL`, `graphify` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BridgeError` connect `BridgeError` to `_site/app.js`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **What connects `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `build_snapshot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12280701754385964 - nodes in this community are weakly interconnected._
- **Should `Career Compass — calm field guide` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `watchRefresh` be split into smaller, more focused modules?**
  _Cohesion score 0.12698412698412698 - nodes in this community are weakly interconnected._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.11264367816091954 - nodes in this community are weakly interconnected._
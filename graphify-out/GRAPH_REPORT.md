# Graph Report - career-job-compass  (2026-07-28)

## Corpus Check
- 25 files · ~232,200 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 198 nodes · 453 edges · 14 communities (10 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9fb6fd5d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Program Management
- Build and Snapshot
- Job Detail Rendering
- Record Handling
- Job Filtering
- Bridge Communication
- UI Navigation
- Release Checks
- Filter Management
- Sector Normalization
- Requirement Checks
- Service Worker
- plans/README.md

## God Nodes (most connected - your core abstractions)
1. `escapeHtml()` - 19 edges
2. `Career Compass — calm field guide` - 18 edges
3. `renderJobs()` - 15 edges
4. `renderToday()` - 14 edges
5. `renderStudy()` - 13 edges
6. `render()` - 12 edges
7. `preferenceFor()` - 11 edges
8. `renderSources()` - 11 edges
9. `watchRefresh()` - 11 edges
10. `_apply_latest_programs()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `jobs()` --indirect_call--> `isEligiblePublicJob()`  [INFERRED]
  app.js → app.js  _Bridges community 5 → community 4_
- `candidateRow()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 4 → community 2_
- `renderJobs()` --calls--> `saveFilters()`  [EXTRACTED]
  app.js → app.js  _Bridges community 5 → community 2_

## Import Cycles
- None detected.

## Communities (14 total, 4 thin omitted)

### Community 0 - "Program Management"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 1 - "Build and Snapshot"
Cohesion: 0.14
Nodes (31): _application_readiness(), _apply_latest_programs(), _apply_public_eligibility(), experienced_only_title(), _graduate_evidence_coverage(), _key(), main(), _public_program_from_research() (+23 more)

### Community 2 - "Job Detail Rendering"
Cohesion: 0.13
Nodes (36): activeFilters(), candidateRow(), chunks(), detailList(), diversifiedJobs(), escapeHtml(), evidenceItem(), evidenceSources() (+28 more)

### Community 3 - "Record Handling"
Cohesion: 0.28
Nodes (15): build_coverage_report(), has_funded_projects(), has_recent_papers(), is_recent_five_years(), main(), merge_named(), merge_patch(), program_key() (+7 more)

### Community 4 - "Job Filtering"
Cohesion: 0.14
Nodes (23): buildFeedbackExport(), closeDetail(), connectPreferences(), displayDate(), exportFeedback(), feedbackReviewList(), go(), jobById() (+15 more)

### Community 5 - "Bridge Communication"
Cohesion: 0.12
Nodes (36): activeRefreshRun(), allJobSectors(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), BridgeError, connectRefreshQueue(), enqueueRefreshRun(), formatRuntime() (+28 more)

### Community 6 - "UI Navigation"
Cohesion: 0.33
Nodes (5): Audit findings, Calm field guide motion plan, Rollback boundary, Token contract, Verification after implementation

### Community 7 - "Release Checks"
Cohesion: 0.29
Nodes (9): contains_forbidden_key(), contains_non_contract_research(), main(), Path, Dependency-free release checks for the static Career Compass PWA., Mirror DATA-215 at the release boundary., Mirror DATA-216 at the release boundary., require() (+1 more)

### Community 8 - "Filter Management"
Cohesion: 0.40
Nodes (4): Career Compass, Local preview, Refresh model, Release boundary

## Knowledge Gaps
- **28 isolated node(s):** `RETIRED_CACHES`, `APP_SHELL`, `graphify`, `Source of truth`, `Brand` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `escapeHtml()` connect `Job Detail Rendering` to `Job Filtering`, `Bridge Communication`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `RETIRED_CACHES`, `APP_SHELL`, `graphify` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Program Management` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Build and Snapshot` be split into smaller, more focused modules?**
  _Cohesion score 0.1431451612903226 - nodes in this community are weakly interconnected._
- **Should `Job Detail Rendering` be split into smaller, more focused modules?**
  _Cohesion score 0.13174603174603175 - nodes in this community are weakly interconnected._
- **Should `Job Filtering` be split into smaller, more focused modules?**
  _Cohesion score 0.1422924901185771 - nodes in this community are weakly interconnected._
- **Should `Bridge Communication` be split into smaller, more focused modules?**
  _Cohesion score 0.11666666666666667 - nodes in this community are weakly interconnected._
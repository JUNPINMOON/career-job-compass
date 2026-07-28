# Graph Report - career-job-compass  (2026-07-28)

## Corpus Check
- 18 files · ~217,196 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 173 nodes · 399 edges · 15 communities (11 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `374808a8`
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
- renderStudy

## God Nodes (most connected - your core abstractions)
1. `escapeHtml()` - 18 edges
2. `Career Compass — calm field guide` - 18 edges
3. `renderJobs()` - 15 edges
4. `renderToday()` - 14 edges
5. `renderStudy()` - 13 edges
6. `render()` - 12 edges
7. `refreshEngine()` - 12 edges
8. `preferenceFor()` - 11 edges
9. `renderSources()` - 11 edges
10. `watchRefresh()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `persistPreferences()` --calls--> `store()`  [EXTRACTED]
  app.js → app.js  _Bridges community 5 → community 4_
- `buildFeedbackExport()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 2 → community 3_
- `connectPreferences()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 2 → community 4_
- `renderStudy()` --calls--> `saveFilters()`  [EXTRACTED]
  app.js → app.js  _Bridges community 4 → community 14_
- `openFilters()` --calls--> `escapeHtml()`  [EXTRACTED]
  app.js → app.js  _Bridges community 2 → community 5_

## Import Cycles
- None detected.

## Communities (15 total, 4 thin omitted)

### Community 0 - "Program Management"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 1 - "Build and Snapshot"
Cohesion: 0.17
Nodes (25): Any, _application_readiness(), _apply_latest_programs(), _apply_public_eligibility(), experienced_only_title(), _key(), main(), _public_research() (+17 more)

### Community 2 - "Job Detail Rendering"
Cohesion: 0.17
Nodes (30): activeFilters(), candidateRow(), chunks(), detailList(), displayDate(), diversifiedJobs(), escapeHtml(), evidenceItem() (+22 more)

### Community 3 - "Record Handling"
Cohesion: 0.22
Nodes (9): buildFeedbackExport(), exportFeedback(), isEligiblePublicJob(), jobById(), jobs(), jobSnapshot(), openJobDetail(), requiredExperienceYears() (+1 more)

### Community 4 - "Job Filtering"
Cohesion: 0.21
Nodes (13): closeDetail(), connectPreferences(), go(), migrateLocalBookmarks(), persistPreferences(), preferencePayload(), render(), resetFilters() (+5 more)

### Community 5 - "Bridge Communication"
Cohesion: 0.14
Nodes (31): allJobSectors(), authenticatedRefreshHeaders(), BridgeError, bridgeRequest(), bridgeUrl(), connectBridge(), formatRuntime(), isSnapshot() (+23 more)

### Community 6 - "UI Navigation"
Cohesion: 0.33
Nodes (5): Audit findings, Calm field guide motion plan, Rollback boundary, Token contract, Verification after implementation

### Community 7 - "Release Checks"
Cohesion: 0.29
Nodes (9): contains_forbidden_key(), contains_non_contract_research(), main(), Path, Dependency-free release checks for the static Career Compass PWA., Mirror DATA-215 at the release boundary., Mirror DATA-216 at the release boundary., require() (+1 more)

### Community 8 - "Filter Management"
Cohesion: 0.40
Nodes (4): Career Compass, Local preview, Refresh model, Release boundary

### Community 14 - "renderStudy"
Cohesion: 0.31
Nodes (10): filteredStudy(), funding(), marketCount(), marketSwitch(), openRecordDetail(), programReadiness(), programs(), recordById() (+2 more)

## Knowledge Gaps
- **27 isolated node(s):** `APP_SHELL`, `graphify`, `Source of truth`, `Brand`, `Product goals` (+22 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `escapeHtml()` connect `Job Detail Rendering` to `Bridge Communication`, `renderStudy`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `APP_SHELL`, `graphify`, `Source of truth` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Program Management` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Bridge Communication` be split into smaller, more focused modules?**
  _Cohesion score 0.1411764705882353 - nodes in this community are weakly interconnected._
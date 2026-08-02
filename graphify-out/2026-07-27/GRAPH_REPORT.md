# Graph Report - career-job-compass  (2026-07-27)

## Corpus Check
- 18 files · ~187,749 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 149 nodes · 323 edges · 15 communities (10 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `384bbba8`
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
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `Career Compass — calm field guide` - 18 edges
2. `renderToday()` - 16 edges
3. `escapeHtml()` - 15 edges
4. `renderJobs()` - 13 edges
5. `renderStudy()` - 13 edges
6. `renderSources()` - 11 edges
7. `render()` - 11 edges
8. `preferenceFor()` - 10 edges
9. `renderJobDetail()` - 10 edges
10. `watchRefresh()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `jobs()` --indirect_call--> `isEligiblePublicJob()`  [INFERRED]
  app.js → app.js  _Bridges community 5 → community 0_
- `persistPreferences()` --calls--> `store()`  [EXTRACTED]
  app.js → app.js  _Bridges community 5 → community 4_
- `candidateRow()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 4 → community 2_
- `renderToday()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 4 → community 0_
- `openFilters()` --calls--> `escapeHtml()`  [EXTRACTED]
  app.js → app.js  _Bridges community 2 → community 5_

## Import Cycles
- None detected.

## Communities (15 total, 5 thin omitted)

### Community 0 - "Program Management"
Cohesion: 0.19
Nodes (22): activeFilters(), chunks(), diversifiedJobs(), filteredJobs(), filteredStudy(), funding(), jobById(), jobs() (+14 more)

### Community 1 - "Build and Snapshot"
Cohesion: 0.31
Nodes (12): Any, _application_readiness(), _apply_latest_programs(), _apply_public_eligibility(), _key(), main(), Path, Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle (+4 more)

### Community 2 - "Job Detail Rendering"
Cohesion: 0.28
Nodes (13): candidateRow(), detailList(), escapeHtml(), icon(), marketLabel(), officialLink(), openJobDetail(), openRecordDetail() (+5 more)

### Community 3 - "Record Handling"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 4 - "Job Filtering"
Cohesion: 0.17
Nodes (18): closeDetail(), connectPreferences(), displayDate(), feedbackReviewList(), go(), jobSectors(), jobSnapshot(), migrateLocalBookmarks() (+10 more)

### Community 5 - "Bridge Communication"
Cohesion: 0.12
Nodes (31): allJobSectors(), authenticatedRefreshHeaders(), BridgeError, bridgeRequest(), bridgeUrl(), buildFeedbackExport(), connectBridge(), exportFeedback() (+23 more)

### Community 6 - "UI Navigation"
Cohesion: 0.33
Nodes (5): Audit findings, Calm field guide motion plan, Rollback boundary, Token contract, Verification after implementation

### Community 7 - "Release Checks"
Cohesion: 0.47
Nodes (5): contains_forbidden_key(), main(), Path, Dependency-free release checks for the static Career Compass PWA., require()

### Community 8 - "Filter Management"
Cohesion: 0.40
Nodes (4): Career Compass, Local preview, Refresh model, Release boundary

## Knowledge Gaps
- **28 isolated node(s):** `APP_SHELL`, `graphify`, `⚠ 볼트 우선 계약 — 모든 에이전트 공통 (Claude / Codex / Gemini / agy)`, `Source of truth`, `Brand` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `renderToday()` connect `Program Management` to `Job Detail Rendering`, `Job Filtering`, `Bridge Communication`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `APP_SHELL`, `graphify`, `⚠ 볼트 우선 계약 — 모든 에이전트 공통 (Claude / Codex / Gemini / agy)` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Record Handling` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Bridge Communication` be split into smaller, more focused modules?**
  _Cohesion score 0.12299465240641712 - nodes in this community are weakly interconnected._
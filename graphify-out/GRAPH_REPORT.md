# Graph Report - career-job-compass  (2026-07-27)

## Corpus Check
- 17 files · ~181,154 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 137 nodes · 293 edges · 14 communities (10 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5fdd7137`
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
1. `Career Compass — calm field guide` - 18 edges
2. `renderToday()` - 16 edges
3. `escapeHtml()` - 14 edges
4. `renderJobs()` - 13 edges
5. `renderStudy()` - 13 edges
6. `render()` - 11 edges
7. `renderJobDetail()` - 10 edges
8. `preferenceFor()` - 8 edges
9. `icon()` - 8 edges
10. `jobs()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `jobs()` --indirect_call--> `isEligiblePublicJob()`  [INFERRED]
  app.js → app.js  _Bridges community 5 → community 0_
- `buildFeedbackExport()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 4 → community 5_
- `candidateRow()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 4 → community 0_
- `renderJobDetail()` --calls--> `preferenceFor()`  [EXTRACTED]
  app.js → app.js  _Bridges community 4 → community 2_
- `renderJobDetail()` --calls--> `escapeHtml()`  [EXTRACTED]
  app.js → app.js  _Bridges community 0 → community 2_

## Import Cycles
- None detected.

## Communities (14 total, 4 thin omitted)

### Community 0 - "Program Management"
Cohesion: 0.18
Nodes (27): candidateRow(), chunks(), detailList(), diversifiedJobs(), escapeHtml(), filteredJobs(), filteredStudy(), funding() (+19 more)

### Community 1 - "Build and Snapshot"
Cohesion: 0.31
Nodes (12): Any, _application_readiness(), _apply_latest_programs(), _apply_public_eligibility(), _key(), main(), Path, Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle (+4 more)

### Community 2 - "Job Detail Rendering"
Cohesion: 0.47
Nodes (6): jobById(), jobSectors(), jobSnapshot(), openJobDetail(), refreshPreferenceUI(), renderJobDetail()

### Community 3 - "Record Handling"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 4 - "Job Filtering"
Cohesion: 0.16
Nodes (18): closeDetail(), connectPreferences(), displayDate(), go(), migrateLocalBookmarks(), openFeedback(), persistPreferences(), preferenceFor() (+10 more)

### Community 5 - "Bridge Communication"
Cohesion: 0.14
Nodes (23): activeFilters(), allJobSectors(), bridgeRequest(), bridgeUrl(), buildFeedbackExport(), exportFeedback(), isEligiblePublicJob(), isSnapshot() (+15 more)

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
- **27 isolated node(s):** `APP_SHELL`, `graphify`, `Source of truth`, `Brand`, `Product goals` (+22 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `renderToday()` connect `Program Management` to `Job Detail Rendering`, `Job Filtering`, `Bridge Communication`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `escapeHtml()` connect `Program Management` to `Job Detail Rendering`, `Job Filtering`, `Bridge Communication`?**
  _High betweenness centrality (0.003) - this node is a cross-community bridge._
- **What connects `APP_SHELL`, `graphify`, `Source of truth` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Record Handling` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Bridge Communication` be split into smaller, more focused modules?**
  _Cohesion score 0.1396011396011396 - nodes in this community are weakly interconnected._
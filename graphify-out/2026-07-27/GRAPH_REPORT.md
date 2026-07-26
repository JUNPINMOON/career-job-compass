# Graph Report - /mnt/c/Users/mjb58/career-job-compass  (2026-07-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 87 nodes · 220 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.5)
- Token cost: 455 input · 108 output

## Graph Freshness
- Built from commit: `928e16ae`
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

## God Nodes (most connected - your core abstractions)
1. `escapeHtml()` - 14 edges
2. `renderToday()` - 14 edges
3. `renderJobs()` - 13 edges
4. `renderStudy()` - 13 edges
5. `render()` - 10 edges
6. `icon()` - 9 edges
7. `pageFrame()` - 8 edges
8. `renderJobDetail()` - 8 edges
9. `_apply_latest_programs()` - 8 edges
10. `jobs()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `normalizeFilters()` --calls--> `saveFilters()`  [EXTRACTED]
  app.js → app.js  _Bridges community 8 → community 9_
- `renderJobs()` --calls--> `saveFilters()`  [EXTRACTED]
  app.js → app.js  _Bridges community 8 → community 4_
- `renderStudy()` --calls--> `saveFilters()`  [EXTRACTED]
  app.js → app.js  _Bridges community 8 → community 0_
- `openFilters()` --calls--> `escapeHtml()`  [EXTRACTED]
  app.js → app.js  _Bridges community 2 → community 9_
- `pageFrame()` --calls--> `escapeHtml()`  [EXTRACTED]
  app.js → app.js  _Bridges community 2 → community 0_

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Program Management"
Cohesion: 0.29
Nodes (13): chunks(), diversifiedJobs(), filteredStudy(), funding(), marketCount(), marketSwitch(), pageFrame(), programReadiness() (+5 more)

### Community 1 - "Build and Snapshot"
Cohesion: 0.36
Nodes (10): Any, _application_readiness(), _apply_latest_programs(), _key(), main(), Path, Build the GitHub Pages fallback without regenerating the 218 MB dashboard bundle, Keep an actionable preparation lane distinct from a verified open call.      The (+2 more)

### Community 2 - "Job Detail Rendering"
Cohesion: 0.40
Nodes (11): candidateRow(), detailList(), escapeHtml(), icon(), jobSectors(), officialLink(), programReadinessLabel(), queueCopy() (+3 more)

### Community 3 - "Record Handling"
Cohesion: 0.33
Nodes (8): isSnapshot(), load(), openRecordDetail(), recordById(), renderError(), setSnapshot(), sourceDate(), updateNetwork()

### Community 4 - "Job Filtering"
Cohesion: 0.25
Nodes (9): activeFilters(), filteredJobs(), isEligiblePublicJob(), jobById(), jobs(), openJobDetail(), renderJobs(), requiredExperienceYears() (+1 more)

### Community 5 - "Bridge Communication"
Cohesion: 0.42
Nodes (9): bridgeRequest(), bridgeUrl(), connectBridge(), loadLiveSnapshot(), refreshEngine(), refreshStatus(), setEngineBusy(), stopRefreshPolling() (+1 more)

### Community 6 - "UI Navigation"
Cohesion: 0.33
Nodes (6): closeDetail(), displayDate(), go(), render(), renderSources(), setActiveTab()

### Community 7 - "Release Checks"
Cohesion: 0.47
Nodes (5): contains_forbidden_key(), main(), Path, Dependency-free release checks for the static Career Compass PWA., require()

### Community 8 - "Filter Management"
Cohesion: 0.50
Nodes (4): resetFilters(), route(), saveFilters(), store()

### Community 9 - "Sector Normalization"
Cohesion: 0.67
Nodes (3): allJobSectors(), normalizeFilters(), openFilters()

## Knowledge Gaps
- **1 isolated node(s):** `APP_SHELL`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `renderToday()` connect `Program Management` to `Job Detail Rendering`, `Record Handling`, `Job Filtering`, `UI Navigation`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `escapeHtml()` connect `Job Detail Rendering` to `Program Management`, `Record Handling`, `Job Filtering`, `UI Navigation`, `Sector Normalization`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `renderJobs()` connect `Job Filtering` to `Program Management`, `Job Detail Rendering`, `Record Handling`, `UI Navigation`, `Filter Management`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **What connects `APP_SHELL` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
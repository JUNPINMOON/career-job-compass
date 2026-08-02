# Graph Report - career-job-compass  (2026-07-29)

## Corpus Check
- 31 files · ~419,506 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 328 nodes · 823 edges · 19 communities (13 shown, 6 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6a1dce56`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.js
- build_snapshot.py
- _site/app.js
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

## God Nodes (most connected - your core abstractions)
1. `escapeHtml()` - 20 edges
2. `escapeHtml()` - 20 edges
3. `Career Compass — calm field guide` - 18 edges
4. `renderJobs()` - 15 edges
5. `renderSources()` - 15 edges
6. `renderJobs()` - 15 edges
7. `renderSources()` - 15 edges
8. `renderToday()` - 14 edges
9. `renderToday()` - 14 edges
10. `renderStudy()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `persistPreferences()` --calls--> `store()`  [EXTRACTED]
  _site/app.js → _site/app.js  _Bridges community 4 → community 2_
- `persistPreferences()` --calls--> `store()`  [EXTRACTED]
  app.js → app.js  _Bridges community 5 → community 0_

## Import Cycles
- None detected.

## Communities (19 total, 6 thin omitted)

### Community 0 - "app.js"
Cohesion: 0.08
Nodes (77): activeFilters(), allJobSectors(), BridgeError, buildFeedbackExport(), candidateRow(), chunks(), closeDetail(), connectPreferences() (+69 more)

### Community 1 - "build_snapshot.py"
Cohesion: 0.14
Nodes (33): _application_readiness(), _apply_latest_programs(), _apply_public_eligibility(), experienced_only_title(), _graduate_data_lineage(), _graduate_evidence_coverage(), _key(), main() (+25 more)

### Community 2 - "_site/app.js"
Cohesion: 0.08
Nodes (77): activeFilters(), allJobSectors(), BridgeError, buildFeedbackExport(), candidateRow(), chunks(), closeDetail(), connectPreferences() (+69 more)

### Community 3 - "Career Compass — calm field guide"
Cohesion: 0.11
Nodes (18): Acceptance check, Accessibility, Brand, Career Compass — calm field guide, Components and disclosure, Content voice, Design principles, Information architecture (+10 more)

### Community 4 - "watchRefresh"
Cohesion: 0.13
Nodes (28): activeRefreshRun(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), connectRefreshQueue(), enqueueRefreshRun(), formatRuntime(), graduateLineageMatches(), isSnapshot() (+20 more)

### Community 5 - "watchRefresh"
Cohesion: 0.13
Nodes (28): activeRefreshRun(), authenticatedRefreshHeaders(), authenticatedRefreshRequest(), connectRefreshQueue(), enqueueRefreshRun(), formatRuntime(), graduateLineageMatches(), isSnapshot() (+20 more)

### Community 6 - "Calm field guide motion plan"
Cohesion: 0.33
Nodes (5): Audit findings, Calm field guide motion plan, Rollback boundary, Token contract, Verification after implementation

### Community 7 - "check_release.py"
Cohesion: 0.29
Nodes (9): contains_forbidden_key(), contains_non_contract_research(), main(), Path, Dependency-free release checks for the static Career Compass PWA., Mirror DATA-215 at the release boundary., Mirror DATA-216 at the release boundary., require() (+1 more)

### Community 8 - "Career Compass"
Cohesion: 0.40
Nodes (4): Career Compass, Local preview, Refresh model, Release boundary

### Community 14 - "expand_graduate_evidence.py"
Cohesion: 0.28
Nodes (15): build_coverage_report(), has_funded_projects(), has_recent_papers(), is_recent_five_years(), main(), merge_named(), merge_patch(), program_key() (+7 more)

## Knowledge Gaps
- **31 isolated node(s):** `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES`, `APP_SHELL`, `graphify` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `RETIRED_CACHES`, `APP_SHELL`, `RETIRED_CACHES` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.07592592592592592 - nodes in this community are weakly interconnected._
- **Should `build_snapshot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13725490196078433 - nodes in this community are weakly interconnected._
- **Should `_site/app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.07592592592592592 - nodes in this community are weakly interconnected._
- **Should `Career Compass — calm field guide` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `watchRefresh` be split into smaller, more focused modules?**
  _Cohesion score 0.12698412698412698 - nodes in this community are weakly interconnected._
- **Should `watchRefresh` be split into smaller, more focused modules?**
  _Cohesion score 0.12698412698412698 - nodes in this community are weakly interconnected._
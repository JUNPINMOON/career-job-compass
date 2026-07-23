# Design

## Source of truth

- Status: Active
- Last refreshed: 2026-07-23
- Primary product surfaces: iPhone Safari Home Screen PWA, mobile browser, desktop browser
- Evidence reviewed:
  - `C:\Users\mjb58\career-ui-learning-lab\job-search-interface-inventory.md`
  - `C:\Users\mjb58\career-ui-learning-lab\evidence\crawl-observations.json`
  - Antigravity Gemini review run via `agy` on 2026-07-23
  - existing `job_search` data schemas: 13,884 raw jobs, 5,944 scored jobs, 107 source-health records
  - user rejection: static report/card-wall dashboard is not acceptable

## Brand

- Personality: calm, decisive, evidence-led work tool; Korean-first, international-data capable
- Trust signals: snapshot time, explicit verification state, official-source link, visible data limits
- Avoid: marketing hero copy, gradient decoration, bento/card walls, oversized score circles, fake native iOS chrome, copied vendor branding

## Product goals

- Goals:
  - Let the user answer “what should I verify or open next?” in seconds.
  - Make job, graduate/funding, and data-confidence decisions readable on an iPhone.
  - Preserve a stable offline-capable snapshot that can be published on GitHub Pages without credentials.
- Non-goals:
  - Apply, send messages, log in, alter CRM, claim a job is live, or replace the local job-search pipeline.
  - Native iOS/IPA distribution or real-time collection from GitHub Pages.
- Success signals:
  - First-time reader can name the active task, data age, and next action within five seconds.
  - On mobile, filtering and opening details preserve the list context.
  - Every external opportunity link is labeled as an official-source check, not an application result.

## Personas and jobs

- Primary personas: the user, a Korean water/GIS professional transitioning toward AI/data/international opportunities.
- User jobs:
  - scan a curated snapshot; filter without losing context; understand why an item is present; open the official source; review study/funding routes; judge data freshness.
- Key contexts of use: iPhone Safari/Home Screen during short sessions, desktop for deeper comparison, unreliable mobile network.

## Information architecture

- Primary navigation: fixed mobile bottom tabs — Today, Jobs, Sectors, Study/Funding, Data Trust.
- Core routes/screens:
  - `#/today`, `#/jobs`, `#/jobs/:id`, `#/sectors`, `#/study`, `#/trust`.
- Content hierarchy:
  - Today: small action queue and snapshot status.
  - Jobs: list → optional filter sheet → stable detail route → official source.
  - Sectors and Study/Funding: purpose-specific exploration, not appended to every job row.
  - Data Trust: data age, limits, source health and static-snapshot boundary.

## Design principles

- Principle 1: show a decision before an explanation. The row answers what it is, status, and why to open it.
- Principle 2: separate ranking, eligibility, freshness, and source truth; no single score implies all four.
- Principle 3: mobile is complete by itself. Desktop may place list and detail side by side but cannot be the only usable mode.
- Tradeoffs: a small static snapshot is intentionally less comprehensive than the local pipeline, but keeps GitHub Pages fast and honest on iPhone.

## Visual language

- Color: warm off-white background; graphite text; cobalt only for active navigation/links; teal for verified/current; amber for verification needed; red only for failures/expired states.
- Typography: `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Noto Sans KR", system-ui, sans-serif`; 17px body minimum on mobile; tabular numerals for scores and dates.
- Spacing/layout rhythm: 4px base; 16px page gutters; 12–16px list-row vertical rhythm; no dense nested cards.
- Shape/radius/elevation: 12px maximum for panels and controls; 0–2px restrained shadow; clear dividers do more work than elevation.
- Motion: 160–220ms opacity/transform only; honor `prefers-reduced-motion`; never make loading look like success.
- Imagery/iconography: inline geometric SVG icons with text labels for primary actions; no emoji as a sole status indicator.

## Components

- Existing components to reuse: none; this is a clean static PWA.
- New/changed components: app shell, status strip, list row, filter sheet, detail route, evidence disclosure, bottom tab bar, offline banner, skeleton rows.
- Variants and states: verified/current, verification-needed, stale, source-failed, empty, loading, offline, disabled.
- Token/component ownership: CSS custom properties in `styles.css`; behavior in `app.js`; snapshot facts only in `data/app-data.json`.

## Accessibility

- Target standard: WCAG 2.2 AA where practical for this static app.
- Keyboard/focus behavior: visible focus ring; Escape closes filter sheet and returns focus to its trigger; hash navigation moves focus to the main heading.
- Contrast/readability: text/status contrast meets AA intent; color never carries meaning alone; touch targets at least 44px.
- Screen-reader semantics: semantic nav/main/article/button; labels for SVG icons; live region only for filter result changes and offline state.
- Reduced motion and sensory considerations: disable route/sheet transitions for reduced motion; avoid automatic carousels or animated counters.

## Responsive behavior

- Supported breakpoints/devices: 320px–430px iPhone widths first; 768px tablet; 1024px+ desktop.
- Layout adaptations: mobile uses a single reading column and fixed bottom tabs; desktop keeps the same routes but can pin a selected job detail next to the list.
- Touch/hover differences: touch uses explicit buttons and labels; hover styles are additive only.

## Interaction states

- Loading: fixed-height skeleton rows, no layout shift.
- Empty: show active filters and one clear reset action.
- Error: failed static-data load names the failure and retains a retry action.
- Success: local bookmark state confirms only local storage, never an external application.
- Disabled: source button disabled only when URL is absent, with explanation.
- Offline/slow network: offline banner, cached app shell/snapshot when available, and last snapshot timestamp.

## Content voice

- Tone: short, factual, calm Korean; English original titles remain intact.
- Terminology: “원문 확인” for external links; “확인 필요” for unverified eligibility; “스냅샷” for static published data.
- Microcopy rules: state the fact and the next safe action; do not say “지원 완료” unless user explicitly records local status.

## Implementation constraints

- Framework/styling system: dependency-free HTML/CSS/JavaScript so GitHub Pages works from a repository without an npm build.
- Design-token constraints: system font and CSS variables only; no remote font dependency.
- Performance constraints: compact curated JSON (at most 80 jobs and 16 study/funding routes); render incrementally in the DOM; no client-side processing of the full 5,944-row pool.
- Compatibility constraints: manifest, service worker, iOS safe-area CSS, hash routing, no server API requirement.
- Test/screenshot expectations: JSON validation, JavaScript syntax check, static server smoke, desktop + 390px mobile Playwright screenshots, PWA manifest/service-worker checks. Physical iPhone install remains a separate required gate.

## Open questions

- [ ] Which local job-search run should produce the next public snapshot, and who verifies its freshness?
- [ ] Does the user want the eventual GitHub Pages repository public or private with a different host? Current request implies public Pages, but visibility is an external-release decision.
- [ ] Which study/funding entries are safe and useful to include in a public snapshot after their deadlines are rechecked?

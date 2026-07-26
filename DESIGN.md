# Career Compass — calm field guide

## Source of truth

This file is the design decision contract for the static Career Compass PWA. When implementation and this document differ, update the implementation or record the unresolved decision under Open questions before release.

## Brand

Career Compass is calm, precise, evidence-led, and Korean-first. It helps a user decide what to inspect next without pretending that a collected record is an application recommendation.

## Product goals

Career Compass is a Korean-first mobile reading tool for choosing what to inspect next: domestic and overseas jobs, graduate programs, and funding. It is not a landing page, an inspirational poster, or an application portal. A source is always the authority for eligibility and deadlines.

The app should feel quiet, precise, and personal on an iPhone Home Screen: a small number of clear choices per page, dense enough comparison when browsing, and no decorative explanation that competes with a title or source.

## Personas and jobs to be done

- A first-time job seeker needs entry-accessible domestic and overseas roles without experienced-only listings appearing as viable candidates.
- A graduate-study researcher needs to compare programs and funding while seeing whether each record is open, preparation-only, or still research.
- A returning user needs a short Today route, saved items, and source dates without re-learning the interface.

## Information architecture

| Tab | Question | Must preserve |
| --- | --- | --- |
| Today | What is worth opening now? | Snapshot date, priority/inventory context, direct route to jobs and study |
| Explore | What options exist across my interests? | Search, domestic/overseas switch, sector inventory, filters, save and source detail |
| Study | Which programs or funding routes deserve review? | Program/funding switch, domestic/overseas switch, open/prepare state, online filter, source detail |
| Sources | What can this snapshot truthfully say? | Data date, coverage, verification and limitations |

Adding a new filter or source never replaces an existing inventory or route.

## Visual language

- **Canvas:** muted green-white `#F3F6F1`; the page is not pure clinical white.
- **Surface:** almost-white `#FBFCF9`; use it for the header, sheet, and small controls only.
- **Ink:** deep leaf `#19271E`; body copy is charcoal-green, never washed-out gray.
- **Structure:** moss `#4F7D5D` and forest `#255B40` for navigation, focus and primary action.
- **Highlight:** softened lime `#DCE9CC`, reserved for selected state and a single action. It is not a full-screen background or a neon accent.
- **Warning:** muted ochre `#9B6B2F`, only where source verification is still needed.
- **Geometry:** open reading rails and divider lines before containers. A rounded surface is reserved for touch controls and modal sheets, not every datum.
- **Type:** Pretendard Variable first, then the iOS/system Korean stack. Titles are compact and single-purpose; labels are short Korean nouns, not invented English dashboard jargon.
- **Images:** editorial images can support route recognition, but never fill the whole screen, repeat as texture, or obscure information.

## Mobile reading rhythm

The first viewport prioritizes the active title, the essential controls, and the first real candidate. Major views must never reserve a full viewport for a hero, illustration, or page-control rail. Result groups stay short and easy to scan, but flow naturally after the controls so that no empty “page” stands between a question and an option.

## Design principles

1. Source authority before confidence: eligibility and deadlines stay conditional until the official source is opened.
2. Candidate before decoration: the first real option follows the essential controls without a hero-sized gap.
3. Comparison before isolation: browsing keeps all sectors reachable and uses compact repeated rows.
4. Progressive disclosure before density loss: details belong in a compact sheet, not an oversized card.

## Components and disclosure

- A **card** is a contained surface for an independent, comparable unit. It is not a default page-layout device. If removing its border and background does not reduce comprehension, it should be a reading row or a divider instead.
- Job and program candidates use compact **list rows**: source/category, title, one decisive fact, then an affordance. Their container must never be taller than the information it contains.
- Search and filters are **toolbar controls**, not hero panels. On mobile the filter trigger is a 42–44px icon control; search is a 44–48px input on the reading rail.
- A **bottom sheet / drawer** is progressive disclosure. It opens only as high as the form needs, keeps the close control and title together, and uses ordinary-sized fields and a single 50px primary action. The primary button may carry an 18px icon, never an unconstrained SVG.
- Radius expresses interaction, not decoration: 10–12px for inputs and sheets, pill geometry only for chips/status, and no radius on reading rows or section dividers.

## Accessibility

- Interactive controls keep at least a 42px touch target and a visible keyboard focus ring.
- Color never carries queue, readiness, or selected state by itself; text labels remain present.
- Dialogs keep a readable title and textual close action, and reduced-motion preferences disable non-essential motion.
- Source dates and conditional status text remain readable at 200% zoom without horizontal page scrolling.

## Responsive behavior

- At 760px and below, routes use natural document flow, wrapped sector controls, and content-height sheets.
- Above 760px, the bottom navigation becomes a compact top rail and details may use a right-side drawer.
- No breakpoint may hide sectors, markets, source links, readiness, or eligibility caveats.

## Interaction states and motion

| Interaction | Motion | Duration | Rule |
| --- | --- | ---: | --- |
| Button press | scale to 0.98 | 120ms | Press feedback only; no bouncing or shadow jump. |
| Bottom sheet | opacity + 14px translate | 180ms | Only when it opens or closes. |
| Refresh indicator | rotate | while fetching | Stop when fetching ends and disable under reduced motion. |

Hover affordances exist only for `hover:hover` and `pointer:fine`; touch screens receive press feedback instead. Reduced-motion users retain opacity and color state changes but do not receive smooth scrolling or perpetual rotation.

## Non-negotiable exclusions

- No cobalt cover, fluorescent lime, coral offset shadows, diagonal clipped cards, or competing accent colors.
- No generic rounded-card grid, motivational paragraphs, fake score confidence, or English labels used as decoration.
- No background scheduler, server control, widget, startup item, automatic refresh, credential, application, CRM write, or external side effect in this static app.
- No copied third-party design or source code. The installed public design skills are review criteria, not a template to imitate.

## Acceptance check

1. A first-time user sees the current data date, a route to the full inventory, and one unambiguous next action without reading an explanatory paragraph.
2. The Explore tab still reveals all sectors and domestic/overseas options; the Study tab still reveals programs, funding, readiness, and online study.
3. No screen depends on a large saturated hero or an ornamental card to establish hierarchy.
4. Any claim requiring a source remains visibly conditional until the official source is opened.

## Content voice

Use short Korean nouns and direct actions such as `원문 확인`, `추가 검토`, and `전체 보기`. Avoid motivational copy, unexplained internal labels, and language that converts exploration into a recommendation.

## Technical constraints

The app is a dependency-free static PWA. `data/catalog-source.json` is the maintained catalog input; `data/app-data.json` is generated output. Builds must exclude explicit requirements of two or more years of experience and releases must pass the requirement ledger.

## Open questions

- Whether future verified one-year requirements should remain visible with a caveat or move to a separate stretch inventory.
- Whether the Study view eventually needs a second comparison density for desktop without changing the mobile reading order.

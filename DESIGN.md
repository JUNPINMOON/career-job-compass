# Career Compass — calm field guide

## Product stance

Career Compass is a Korean-first mobile reading tool for choosing what to inspect next: domestic and overseas jobs, graduate programs, and funding. It is not a landing page, an inspirational poster, or an application portal. A source is always the authority for eligibility and deadlines.

The app should feel quiet, precise, and personal on an iPhone Home Screen: a small number of clear choices per page, dense enough comparison when browsing, and no decorative explanation that competes with a title or source.

## Information architecture that must remain intact

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

## Motion contract

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

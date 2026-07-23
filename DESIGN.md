# Career Compass — product design contract

## Status and evidence

- **Status:** visual architecture replaced on 2026-07-24; the earlier dark fieldbook/ledger system is retired.
- **Surface:** Korean-first iPhone Safari Home Screen PWA first, then mobile Safari and desktop browser.
- **Product question:** “오늘 무엇을 더 확인해야 하는가?”
- **Source boundary:** static public snapshot only. A score orders reading; only an official source can confirm deadline, eligibility, or application availability.
- **Reference method:** candidates were discovered by web search, then their official App Store / Apple pages were crawled with Crawl4AI and `check_robots_txt=True`. Google result pages were not crawled after robots.txt refusal. Evidence is under `output/commercial-reference-crawl-2026-07-24/` (ignored release output).

## Reference roles, not visual copying

| Reference | What is studied | What must not enter Career Compass |
| --- | --- | --- |
| Toss | decisive hierarchy for high-stakes information; a single obvious next action | finance promo modules, transaction-dashboard density, visual imitation |
| Zigzag | fast horizontal category selection and short-listing behavior | discount banners, ecommerce grids, urgency tricks |
| Karrot | warm, plain-language trust and next-action cues | chat-marketplace metaphors or social proof theater |
| Bandana | browse → detail → save → apply reading sequence | salary-first claims when source data does not provide salary |
| 29CM | Korean editorial rhythm: restrained promo copy, deliberate image/text composition, a high-confidence taste signal | product grids, discount urgency, or copying the brand’s fashion voice |
| Partiful | event-poster confidence: one dominant visual, a concise metadata line, and a single obvious response | party/social features, glitter overload, GIF noise, or invitation metaphors |
| Day One | a calm, context-rich record: date, source condition, and a readable sequence before decoration | diary metaphors, private-life imagery, or turning every data point into metadata |
| Not Boring Habits | delight at the moment of action: tactile press feedback and visible progress, not a decorative dashboard | 3D spectacle, skins, games, sound, or reward loops that distract from source checking |
| Apple Design Awards / Gen Z editorial | a clear visual voice and motion used in service of a task | meme maximalism, mascots, 3D gimmicks, decorative motion |

The product is therefore neither a Toss clone nor an e-commerce feed. It is a bright editorial decision tool: focused enough for an institutional source check, energetic enough to feel like a consumer app.

## Information architecture

| Tab | Question answered | Primary action |
| --- | --- | --- |
| 오늘 | What is worth opening first? | Open one of three ordered source checks. |
| 탐색 | What survives my search or interest area? | Search, choose an area, filter, then open a detail sheet. |
| 진학 | Which study/funding route deserves parallel review? | Read route context and open the official page. |
| 자료 | What is this snapshot able to say? | Inspect date, volume, source-state distribution, and limits. |

There is no “sector terrain” tab. Sectors belong inside exploration, where they directly change what the user sees.

## Primary screen contract

### Today

1. Identify the snapshot date and the first source to open within five seconds.
2. Show only three priority opportunities in an ordered, numbered reading list.
3. On every opportunity, show institution, title, location, score, and the precise condition that still requires source checking.
4. Put study/funding on its own editorial route below the work decision rather than mixing it into the same feed.

### Exploration

1. Search comes before browsing.
2. Interest areas are horizontally scrollable selections, not a wall of chips.
3. An opportunity has one reading action and one secondary save action.
4. Status is a short inline sentence with a coloured dot; it is never a cloud of badges.

### Detail sheet

The existing list stays underneath. The sheet contains score context, facts, the mandatory check, a real outbound official-source link, and a local-only save action. It never claims the user can apply through the PWA.

## Visual system

- **Canvas:** warm paper `#F7F4ED`, rather than clinical white or a dark terminal.
- **Ink:** navy `#142238` for readable structure.
- **Energy:** cobalt `#2458D9` is the Today cover; lime `#D4F12C` frames the app chrome and primary action; white is reserved for information pills and the active tab; coral `#FF6C42` is a small offset or unresolved-verification signal. Do not leave the top and bottom chrome in unrelated pale neutrals.
- **Typography:** Pretendard Variable when online, then iOS/system Korean fallback. Korean titles are compact and heavy; English names remain inline and never become an all-caps visual system. Minimum text size is 11px; body starts at 14px.
- **Geometry:** lines, sequence numbers, asymmetrical clipped planes, and a few deliberately shaped controls. Default content is not boxed in generic rounded cards. The mobile page deck adds a short cobalt progress rail and an active next-page control; they describe reading position rather than gamify it.
- **First screen:** Today opens as the approved cobalt cover composition: a small metadata line, one original route collage, large two-line Korean decision title, and one lime source-check action. Do not replace this composition with a sparse score card or generic dashboard heading; later refinements preserve its hierarchy and energy.
- **Original images:** `daily-brief-cover-v3.png` is the route collage for the Today cover; `study-steps-editorial-v2.webp` means “academic progression”. They do not repeat as texture or act as decoration.
- **Icon rule:** one 1.8px inline stroke set; no icon tile wall. The Home Screen icon uses the same cobalt/cream/lime language.

## Interaction and responsive behavior

- All navigation and controls have a 44px or larger practical touch area.
- The mobile bottom bar has four durable labels and safe-area padding. Desktop retains the same IA and only changes its footprint.
- Search filters update the current list immediately; the full filter dialog explicitly resets or applies.
- Detail and filter surfaces use native `dialog` semantics, focus return, Escape close, backdrop close, and transform/opacity motion below 250ms.
- `prefers-reduced-motion` disables nonessential motion.
- If offline, a concise notice preserves the last snapshot rather than pretending the data is live.

## Acceptance test

The redesign fails if any of these are true:

1. A first-time user cannot name the first item to inspect and why it is not yet confirmed.
2. The mobile home becomes a hero-first landing page with no immediate next action.
3. More than one decorative badge/chip is attached to an opportunity.
4. A route to source checking is hidden behind an unrelated page change.
5. The screen reads as a dark terminal, a generic white rounded-card dashboard, or an ecommerce clone.
6. New imagery, fonts, or motion obscure source uncertainty or make the PWA materially slower to open.

## Implementation boundaries

- Keep dependency-free HTML/CSS/JS, hash routes, local snapshot data, GitHub Pages compatibility, and service-worker shell caching.
- A small online Pretendard stylesheet improves Korean typography; all essential UI remains fully readable with system-font fallback and cached local shell assets.
- Do not use third-party visual assets, copied code, tracking, login, applications, CRM writes, or background mutation.

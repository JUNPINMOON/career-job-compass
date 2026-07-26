# Calm field guide motion plan

**Reviewed commit:** `4096db9`  
**Scope:** static Career Compass CSS and `app.js` page-frame markup only.  
**Out of scope:** data collection, refresh bridge, server control, startup items, scheduled tasks, desktop widgets, service worker behavior, and publishing.

## Audit findings

| Current behavior | Replacement | Reason |
| --- | --- | --- |
| `styles.css` animated `.opportunity-main` padding and background on hover. | Keep row geometry fixed; reserve interaction feedback for arrow opacity and a touch press scale. | Padding changes move the reading column and make dense lists jitter. |
| `styles.css` animated `.study-row` padding and background on hover. | Keep the row fixed and gate desktop hover to fine pointers only. | A touch UI should not inherit desktop hover choreography. |
| Mobile `.page-frame::before` animated `width`. | Animate `transform: scaleX(var(--page-progress))` from the left edge. | Transform does not trigger layout while page position changes. |
| `.page-turn-next` animated offset shadow while translating. | Use a static border and 0.98 press scale. | The former hard shadow competes with content and produces a visual jump. |
| Global reduced-motion rule forced all transitions to `0.01ms`. | Disable smooth scrolling and rotation, retain short opacity/color state changes. | Reduction should be comprehensible rather than abruptly erase all feedback. |

## Token contract

```css
--motion-press: 120ms;
--motion-state: 160ms;
--motion-sheet: 180ms;
--motion-page: 220ms;
--ease-out: cubic-bezier(.2,.8,.2,1);
```

## Verification after implementation

1. `node --check app.js` succeeds.
2. `py -3.12 -B scripts/check_release.py` succeeds without a server.
3. Inspect the built page markup: `--page-progress` is a unitless number and the CSS rail uses only `transform`.
4. On iPhone, confirm each `다음` press moves a single page; with Reduce Motion enabled it jumps without scrolling animation.

## Rollback boundary

If a visual change harms navigation, revert only the relevant static `app.js`, `styles.css`, or `DESIGN.md` patch after inspecting the user’s current worktree. Do not reset the repository, delete data, alter GitHub Pages, or start/stop a local service.

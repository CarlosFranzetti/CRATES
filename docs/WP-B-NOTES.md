# WP-B: flip through a spot

Branch `worktree-agent-aeb3509acf927b1fe`. Everything is in `crates.html` (CSS block and JS block both marked `WP-B: flip stack`) plus tests `WB01..WB12`.

## What it is

`stackView(list)` renders a spot's records as a stack of sleeves seen from the front. The current cover is large and square in front; the next four peek behind it (12 px steps up, 5.5% smaller each, fading); the previous one has been flipped forward and down and shows as a sliver under the front sleeve. Under the stack: a scrubber (ticks), the caption (title, artist, label · year, "3 of 12") and one row of actions (Play, Preview 30s, Detail, Move…, list toggle).

- It is the default in the Map spot panel and in the Columns middle column (desktop and phone). `S.settings.spotMode = 'stack' | 'list'`, sanitised in `migrate()`, saved with the rest of settings.
- The list shows instead whenever Select mode or "Not played in a year" is on. In list mode a small "Show as stack" chip sits above the list (`stkModeBar()`); in stack mode the last action button switches to the list.
- No `render()` per flip. `stkApply()` updates the 13 cards in the window (current ±6) by `style.cssText` (transform, opacity, z-index; 160 ms `cubic-bezier(.2,.8,.2,1)` transition, off under `prefers-reduced-motion`), the caption, the scrubber tick, the action buttons' `data-r` and the preview button. Cards outside the window are removed, new ones are inserted with their target style (covers lazy-load via `cover()`).
- `dig()` calls `stkApply()` first, so the old arrow-key handler, the Columns prev/next buttons and anything else that calls `dig()` get the fast path for free.

## Inputs

| Input | Behaviour |
|---|---|
| ArrowLeft/Right | existing global handler -> `dig()` |
| J / K | next / previous (only when the type-ahead buffer is empty) |
| Home / End, PageUp / PageDown | first / last, ±10 |
| letters and digits | type-ahead: next artist starting with the buffer (800 ms buffer) |
| wheel / trackpad | a mouse notch (|delta| >= 90) is exactly one record; smaller deltas accumulate, one record per 48 px; `preventDefault` inside the stage only |
| pointer swipe (touch, pen, mouse) | 64 px of travel = one record while dragging; on release the velocity over the last 90 ms is projected like a scroll view (`v * .998 / (1 - .998)`, capped at 30 records) and walked with ease-out timing, 260..700 ms; touching again stops it |
| click a peeking sleeve | jump to it |
| click / tap the front sleeve | Detail (`A.detail` if it exists, else `edit-rec`); in Columns on a phone it pushes the record pane |
| scrubber | pointer down/drag anywhere on the tick row; capped at 60 ticks (each tick is a bucket above 60 records) |

Drag and drop: the front sleeve carries `data-drag="<record id>"` and the class `stk-s` (added next to `sleeve` in the existing `isSleeve` check so a horizontal mouse move flips instead of starting a drag). On touch the existing long-press timer is cancelled by the first horizontal move over 8 px, so a swipe never turns into a drag and a long-press still does. A swipe sets a 400 ms click guard so it does not open Detail.

Accessibility: `.stk` is `tabindex=0`, `role=group`, labelled; `.stk-live` (`aria-live=polite`) says "Strings Of Life, Rhythim Is Rhythim, 2 of 5". Key and click flips update it at once; scrub, wheel, drag and glide flips update it 260 ms after the last move so a flick does not read out every record. The scrubber is `role=slider` with `aria-valuenow`. The cover sleeves are `aria-hidden`.

## Existing code touched (smallest possible edits)

- `migrate()`: `s.spotMode`.
- `dig()`: tries `stkApply()` before falling back to `render()`.
- `spotPanel()` and `renderColumns()`: use `stackView(list)` when `stkOn()`, otherwise the old list plus the mode chip.
- `renderColumns()`: the right pane markup moved verbatim into `colDetail(u, list, cur)` so the stack can refresh that pane alone (debounced 110 ms after a flip). No behaviour change.
- Drag `isSleeve` check.

## Decisions and deviations

- J = next, K = previous (vim/Gmail order). Because J and K are navigation, an artist starting with J or K can only be reached by continuing a buffer ("ja…" after another letter), not as a first letter. Every other letter and digit is type-ahead.
- The Preview button is my own labelled "Preview 30s" button (same `preview` action and link-mode fallback as `previewBtn`), not the round `.pv` icon, so it reads as an action in the row. On phones its icon is hidden to keep all five actions on one 44 px row at 390 px.
- The stack height is derived from the container (`min(78cqw, 42vh, 380px)` on desktop, `min(78cqw, 40vh)` on phones), so at 390x844 with the sheet full the cover is 78% of the width and everything (stage, scrubber, caption, actions) fits in the panel body without scrolling. In the half-height sheet the body scrolls, as the list did.
- Flat look first; Booth and Shop only change tokens. No shadows or glows were added.
- `R10` (compact rows) was already failing on `main` before this work (the flat look's `.li` padding overrides the compact density); I added a one-line CSS override in the WP-B block so compact rows are shorter again, and switched the test to list mode.

## Numbers

150 records in a crate: 50 consecutive `dig(1)` calls average 0.2 to 0.45 ms of script time per flip over several runs (worst single flip 2.6 ms), 13 covers in the DOM at all times. Full suite: 79/79 (67 existing + WB01..WB12).

Test changes: R02, R10, X20 and X23 switch to list mode (`S.settings.spotMode='list'`) because they test list rows; R12 accepts stack covers and now uses a single route handler with a flag instead of swapping routes (the swap raced with in-flight image requests, which the stack's extra covers made likelier). R10 needed a CSS fix (`:root[data-look="flat"][data-density="compact"] .li`), see above.

## Open issues

- Right-hand Columns pane re-renders 110 ms after the last flip (not per flip); during a very fast flick it can lag the caption briefly.
- The half-height phone sheet is not tuned for the stack (it scrolls).
- No letter bubble while scrubbing, and no haptic beyond `navigator.vibrate(4)` at most every 60 ms.

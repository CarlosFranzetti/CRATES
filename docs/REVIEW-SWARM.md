# Review swarm: Map, Columns, Collection and files (commit 987e22c)

Five specialist reviews of the work in `987e22c`, with these new parts: the Map view (pan and pinch canvas, spot panel and phone sheet), the Columns view, the phone tab bar, density, the full-height Collection table, the standby YouTube player, backups, local save and load, and Discogs import. The owner asked for an app that "reacts like an Apple app".

How it ran. The Agent tool wasn't available in this session, so the conductor ran the five briefs one after another, in the same order and with the same rules. Every pass was read-only until the merge. Runtime evidence came from a Playwright probe (`build_harness.build()`, local server, system Chrome, `--no-sandbox --no-proxy-server`, all external requests aborted). Screenshots are in the session scratchpad (`probe/*.png`) and aren't committed.

Severity: **High** means it crashes, loses data or is exploitable. **Medium** means a feature is broken or clearly below the bar. **Low** means it's cosmetic or a nice-to-have. Line numbers refer to `crates.html` at `987e22c` unless marked "now".

---

## 1. Code review (12 findings)

| # | Sev | Where | What | Why it matters | Fix |
|---|---|---|---|---|---|
| C1 | High | `mapReveal` L2584 | `vh = m.clientHeight - (… vh0(vh)*0 + vh*.46 …)` reads `vh` inside its own initializer, which is a TDZ `ReferenceError` | Every reveal on a phone with the sheet up throws: deep links, search results, the arrow keys and cue taps | Measure `H` first and derive `vh` from it. Drop `vh0`. |
| C2 | High | `recordFromDiscogsRow` L3094-3098 | Imported records have no `custom` or `cs`, and `orig` only holds artist and title | **Edit details** throws (`r.custom.map`) on every imported record. "Edited by me" can't see label or year edits. | Add the fields and fill `orig` with all six Discogs fields |
| C3 | Medium | `colGo` L2731-2739 | `pushState` only runs on the view-transition path. Spot-step pushes again while already in the records column. In-app back never consumes history. | With reduced motion, without view transitions, or in tests, the system Back leaves the app. Elsewhere, entries pile up. | Push on every real push, skip same-column moves, and make `col-back` call `history.back()` |
| C4 | Medium | resize handler L2291 | Re-renders only when the map hasn't been moved, and never in Columns | Crossing 780px leaves the sheet undraggable and desktop wording on a phone | Re-render when `isPhone()` flips |
| C5 | Medium | `migrate` L955-960 | Assumes `settings` and the arrays exist | A file or backup without `settings` throws inside `FileReader.onload` with no message | Total `migrate()` and a try/catch around load and restore |
| C6 | Medium | `openAddRecord` L1488 | `S.units[0].id` with an empty room | Add, then Record, throws | Guard with a toast |
| C7 | Medium | `bindSheetDrag` L2680-2694 | Snap velocity is the average over the whole drag | A flick at the end of a slow drag is ignored. A fast drag that stops still flings. (Spec 2.3.) | Use release velocity from the last ~100 ms, or zero if the finger stopped |
| C8 | Low | `selectSpot` L2444 | Both branches of the `V.dig` ternary compute `opts.dig ?? 0` | Re-selecting the current spot resets the selected record | Keep `V.dig` when the spot is unchanged and no `dig` is given |
| C9 | Low | `renderMap` L2497, `digView` L1169-1173 | `V._lastUnit` is never set. `digView` computes `atHome/bag/inBag/ed/dot` that moved into `recInfo`. | Dead code | Delete |
| C10 | Low | `map-unit` L2835 | Calls `mapZoomUnit` before and after `selectSpot`, and the first result is thrown away by `render()` | Wasted work | Call it once, after |
| C11 | Low | `tick` L2169 | The progress interval is never cleared | Polls the DOM every 500 ms forever after the first play | Clear it on pause, end and preview stop |
| C12 | Low | `popstate` L2740 | Hash navigation also fires `popstate` | A deep link while a phone column is pushed pops a column | Ignore `popstate` events without `state.crates` |

Conventions: there's no `alert`, `confirm` or `prompt` anywhere. Moves go through `place()`; the only direct `loc` writes are in `migrate()`. `esc()` is on every user string in text, but ids, colors, photo URLs and YouTube ids reach attributes raw (see S1).

## 2. Error checks (11 findings)

Probe flows: phone reveal paths, an empty room, malformed and BOM CSV, a malformed or sparse collection file, a crafted file, restoring with a sheet open, resizing 1440 → 390 → 780 → 1440 mid-view, phone Columns with the system Back, keyboard only, full storage, then 30 units with 300 and 2,000 records.

| # | Sev | Flow | Result |
|---|---|---|---|
| E1 | High | 390px: `goSpot('B1')`, `#B1`, search then Enter, ArrowDown | `ReferenceError: Cannot access 'vh' before initialization` on each (C1). Shots `E01`-`E04`. |
| E2 | High | Import the demo Discogs collection, then Edit details | `TypeError: reading 'map'` (C2). Shot `E11`. |
| E3 | High | Load from file, with a crafted collection | Script ran (`window.__pwn=2` from a record id). See S1. |
| E4 | Medium | Empty room, then Add, then Record | `TypeError: reading 'id'` (C6) |
| E5 | Medium | Load a file without `settings` | Uncaught `TypeError: reading 'discogsSync'` and no message (C5) |
| E6 | Medium | 390px Columns: open a spot, then the browser Back | The page leaves the app. `history.length` didn't grow (C3). |
| E7 | Medium | 1440px, pan the map, then resize to 390 | Sheet has no drag handler, and the footer says "Drag a record onto any cubby…" (C4) |
| E8 | Medium | Keyboard: open Settings, then Escape | Focus lands on `<body>`, not the Settings button |
| E9 | Medium | Storage full (patched `setItem`) | Every save failed silently. The four full-state backups share the quota. |
| E10 | Low | CSV with an unterminated quote | The rest of the file becomes one cell. The import says nothing. |
| E11 | Info | Empty room: map, columns, table, Play collection, stickers, new gig; restore with a sheet open; 30 units with 300 records in every view | No errors. Empty states read honestly. |

## 3. User testing, Apple detail pass (12 findings)

Run at 390x844 and 1440x900, dark and light, with reduced motion emulated. Map and Columns rows share one type scale (title 15/600, sub 13/400, code 30/800), so the views are consistent.

| # | Sev | Where (selector, size) | What | Fix |
|---|---|---|---|---|
| U1 | Medium | `#main.shell` at 390px (main 358px wide, `scrollWidth` 374) | The full-bleed map, sheet and columns are clipped 16px on the left ("ress and hold…"), and `#main` scrolls sideways | On phones `#main.shell` spans the width with the gutter as padding |
| U2 | Medium | Global | No `:active` rules at all, the default tap-highlight flash, no `touch-action: manipulation` (checklist 1, 2) | Press scale (opacity under reduced motion), transparent highlight, manipulation |
| U3 | Medium | `.pv` 32x32 on every row; `.backlink` 59x20; top `.icon-btn` 34x34; `.map-tools button` 34x34; `.step .round` 36x36 | Under 44px (checklist 3) | 6px hit slop through `::before`; `min-height:44px` on `.backlink` |
| U4 | Medium | `.map-tools` 236-380 x 156-196 vs the K1 plate 139-293 x 162-252 | Fit room puts the Kallax under the zoom tools on phones | 58px top inset in `mapFit` on phones |
| U5 | Medium | `.cue:hover`, `.spot-row:hover` | Hover sticks after a tap on touch screens (checklist 16) | Wrap them in `@media (hover:hover)` |
| U6 | Medium | Every sheet | Closing it drops focus to `<body>` (checklist 18) | Return focus to the trigger, or to the same control after a re-render |
| U7 | Medium | Phone: `.spot-tools .chip` 33px, `.seg button` 30px, `.viewbar .tools-r .btn` 32px; map cubbies 34px at Fit room | Still under 44px. Hit slop would overlap neighbours at 6px gaps. | Layout pass: taller chips, or a row of 44px controls |
| U8 | Low | Phone sheet, expanded row | `recInfo` repeats the row's title and artist straight under it | Hide `h3` and `.by` inside `.rec-x` |
| U9 | Low | `.rec-x` | Fades in on every re-render, so Log a play or Select makes it flash | Animate only when the selected record changes |
| U10 | Low | Phone `.viewbar .tools-r` | "Play collection" is cut at the edge with no fade hint | Edge mask or a More menu |
| U11 | Low | CSS | No `prefers-contrast: more`; no `content-visibility` on long lists (checklist 10, 15) | Add both |
| U12 | Low | Keyboard on the Map | Every cubby and plate name is a tab stop, so it takes about 20 Tab presses to get from the map to the records panel, and there's no skip link (checklist 18) | Roving tabindex on the cubbies, or a "Skip to records" link |

## 4. Security sweep (9 findings)

| # | Sev | Where | What | Fix |
|---|---|---|---|---|
| S1 | High | `cover` L1001, `spines` L1016, `drawShelf` L1022/1025, `unitCard` L1117, `recordRows` L1218, `mainBtn`/`previewBtn` L2186/2382, the `data-u`/`data-r`/`data-p`/`data-g` attributes throughout | Ids, palette colors, finish hex, photo URLs, playlist colors and YouTube ids go into attributes unescaped. Load from file (and restore) accepts any shape, so a shared "collection" file is stored XSS. Proven with a record id `r"><img onerror=…>`. | `migrate()` forces ids into `[A-Za-z0-9_-]`, colors into hex, photos into `data:image/*;base64`, YouTube ids into `[\w-]{6,20}` and cell keys into `r-c`, and rewrites every reference to a renamed id |
| S2 | Medium | `vercel.json` CSP | `script-src 'unsafe-inline'` makes any injection executable on the live site | `scripts/build.mjs` adds a meta CSP that allows the page's inline scripts by SHA-256 only. Both policies apply, so injected inline handlers are blocked. |
| S3 | Medium | `migrate`, `loadCollectionFile`, `restoreBackup` | A corrupted or hand-edited file or backup throws. No prototype pollution was found: `JSON.parse` makes `__proto__` an own key, and nothing deep-merges untrusted objects. | Total `migrate()`, validate before backing up, toast on failure |
| S4 | Medium | `save`, `backupNow` | The four full-state backups (photos are ~100 KB data URLs) share the 5 MB quota with the live state. Once full, every save failed silently and the next reload lost work. | `save()` drops the oldest backups until the state fits, says so, and warns if nothing fits |
| S5 | Medium | `csvCell` L2996 | A bare CR wasn't quoted, so a note with `\r` splits the row and shifts columns in Excel | Quote on `[",\r\n]` |
| S6 | Low | `csvCell` | The formula guard misses a leading space before `=` | Trim-left before the check |
| S7 | Low | `loadZXing` L1747 | jsDelivr script without SRI | WP4 already plans SRI |
| S8 | Info | Links, history, deep links | Every `target="_blank"` has `rel="noopener"`. `pushState` carries only `{crates:col}` and no URL. `routeHash` is anchored and strict. | None |
| S9 | Info | Secrets, CSP host list | No tokens or keys in the client or the build. The CSP host list matches what loads: Google Fonts CSS and fonts, YouTube `iframe_api` and both nocookie frames, jsDelivr ZXing, `/_vercel`. | None |

## 5. Speed (8 findings, measured)

Median of 5 `render()` calls, 1440x900, Chrome headless:

| Data | Map | Columns | Collection | Map spot click | `save()` | State size |
|---|---|---|---|---|---|---|
| 10 records, 3 units | 5.4 ms, 380 nodes | 6.2 ms, 413 nodes | 23 ms, 996 nodes | 7.6 ms | 0.04 ms | 6.8 KB |
| 300 records, 30 units | 35 ms, 1,234 nodes | 15 ms, 970 nodes | **1,700 ms, 53,076 nodes** | 28 ms | 1.6 ms | 163 KB |
| 2,000 records, 30 units | 66 ms, 3,039 nodes | 42 ms, 1,608 nodes | **13,800 ms, 350,012 nodes** | 78 ms | 18.7 ms | 1,055 KB |

There were no long tasks over 60 frames of map panning (transform only). The heap grew 0.42 MB over 50 open and close cycles of a sheet, with no upward trend. The two YouTube iframes couldn't be measured because external requests are blocked in tests.

| # | Sev | What | Cheapest fix |
|---|---|---|---|
| P1 | High | The Collection table built every shelf into every Home spot `<select>`: 1.7 s and 53k nodes per render at 300 records, and every sort, filter and edit re-renders | Lazy options above 60 rows (applied: now ~0.85 s, 26k nodes) |
| P2 | Medium | What remains of the table cost is 900 `<select>`s and 3,000 `<input>`s: about 380 ms of the ~670 ms DOM time is the selects | Window the rows, or render the first 80 and stream the rest (WP9) |
| P3 | Low | The map re-renders the whole world on every spot select | Patch `aria-pressed` and `.sel`, and replace only `.spot-panel` |
| P4 | Low | `save()` stringifies the whole state on every render (18.7 ms at 2,000 records) | Debounce to idle with a `pagehide` flush (WP1) |
| P5 | Low | `render()` forces 2-3 synchronous layouts (`--top-h`, `layoutVars`) | Read once with a `ResizeObserver` |
| P6 | Low | The progress `setInterval` never stops (C11) | Clear it on pause and stop |
| P7 | Low | No `content-visibility` on `.li` rows | `content-visibility:auto; contain-intrinsic-size:auto 56px` |
| P8 | Info | `fitCue` reads `clientWidth` once and `mapLayout` is pure arithmetic, so there's no layout thrash there | None |

Five cheapest fixes with the biggest effect, in order: P1 (applied), P2, P4, P3, P7.

---

## Applied

All of these are in `crates.html` unless noted. "Now" line numbers are from the working tree.

1. **C1, E1. Phone reveal crash.** `mapReveal` measures `H` before deriving `vh`, and `vh0` is removed (now L2671). Test X15.
2. **S1, E3. Sanitizing `migrate()`.** It runs on boot, Load from file and restore. It forces safe ids (renamed ids are rewritten in locations, homes, came-from, playlists, gigs, the sync queue and recents), hex colors, `data:image` photos, YouTube ids, cell keys, plays dates, gig status, settings enums and value types (now L971-1027). The boot preset loop skips non-objects (now L1127). Test X16.
3. **S2. Hashed meta CSP.** In `scripts/build.mjs` L4 and L32-38. Verified on `dist/`: the app boots, and an injected `onerror` is refused. Test X24 checks that every inline script's hash is in the policy.
4. **C2, E2. Imported records.** They now carry `cs`, `custom` and a full `orig` (now L3202). Test X17.
5. **C5, S3, E5. Load and restore.** Both validate and migrate before backing up, and toast on failure (now L3148, L3178). Test X17.
6. **P1. Lazy Home spot options** above 60 rows: `shelfOpt`, `homeSelectOptions`, `hydrateHome` on `pointerdown` or `focusin` (now L3017-3038). Test X18.
7. **S4, E9. Full storage.** `save()` drops the oldest backups until the state fits and says so. If nothing fits it warns once (now L1129-1149). Test X22.
8. **U1. Phone gutters.** `#main.shell` spans full width on phones with the gutter as padding (now L814). Test X19.
9. **U4. Fit room on phones** leaves a 58px top inset for the zoom tools (`mapFit`, now L2654). Test X19.
10. **C4, E7. Re-render when the phone breakpoint flips** (`V.phone` set in `render`, now L1176; resize handler, now L2380). Test X19.
11. **C3, E6. Columns history.** Every push gets an entry, same-column moves don't, and `col-back` goes through `history.back()` (now L2821, L2931). Test X20.
12. **C7. Sheet release velocity** from the last ~100 ms, or zero if the finger stopped (now L2768). Test X21.
13. **U6, E8. Focus returns to the sheet's trigger**, or to the same control after a re-render (`openSheet`/`closeSheet`, now L2106-2124). Test X23.
14. **C6, E4. Add, then Record, in an empty room** says "Add a shelf, crate or bag first" (now L1565). Test X23.
15. **S5. `csvCell` quotes a bare CR** (now L3102). Test X23.
16. **U2, U3, U5. Touch feel.** Press states, no tap flash, `touch-action: manipulation`, hit slop on `.pv`, `.icon-btn`, `.step .round` and `.map-tools button`, a 44px `.backlink`, and hover only where hover exists (now L604, L757, L812-824). Test X23 asserts touch-action and slop.

Every new test fails on `987e22c` and passes now. Each batch got `node --check` on every inline script and a full suite run.

## Open

| Finding | Why not applied |
|---|---|
| P2: the table still takes ~0.85 s at 300 records | Needs row windowing or streaming, which is WP9's section and a structural change (B-129) |
| U7: chips, the segmented control and toolbar buttons are 30-33px on phones; map cubbies are 34px at fit | Needs a layout and density decision; hit slop would overlap 6px gaps (B-130) |
| P3: full map re-render on spot select | 28 ms at 300 records is acceptable; a partial render touches `render()` structure (B-131) |
| P4: whole-state `save()` per render | WP1 owns debounced save (B-132) |
| C8-C12, P5-P7 | Low; small cleanups listed as B-133 to B-135 and B-139 |
| E10: an unterminated CSV quote is silent | Low (B-136) |
| S6, S7 | Low; WP4 and WP8 own them (B-137) |
| U8-U12 | Low polish (B-138, B-139) |

## Result

Final suite: **65/65 passed** (the 55 existing tests plus X15 to X24), run with `CRATES_NO_PATCH=1 python3 tests/test_crates.py`.

# Bugs

Known issues in the Crates prototype (`crates.html`) and the database (`app/db/`). When you fix one, move it to **Fixed** with the commit, and add or point to a test that would catch it coming back. Code-review findings and the full error-handling audit are in [QA.md](QA.md).

Severity: **High** means it crashes or loses data, **Medium** means a feature is broken or the layout breaks, **Low** means it's cosmetic or a minor wrong behavior.

## Open

| ID | Severity | Area | What happens | Notes / proposed fix |
|---|---|---|---|---|
| B-101 | Low | Cubby move | Moving a named cubby onto a cubby that already has a subtitle overwrites it without asking ("A1 → A2" loses "Acid"). | Undo restores it. Ask which subtitle to keep, or keep both ("Acid / Detroit & Chicago"). |
| B-102 | Low | Gigs | During load-out, unticking "packed" on a record that was already in the gig's bag before the gig moves it out to its home shelf. | Remember the pre-gig location per gig item and restore that instead. |
| B-103 | Low | Collection | Changing **Home spot** on a record that's sitting on a shelf also moves the record there. | By design today (on a shelf, home follows location). Decide: separate "Move to" and "Set home" columns? |
| B-104 | Low | Deep links | (Fixed) QR codes made in the claude.ai preview now point at the live site, https://crates-livid.vercel.app/. | Moved to Fixed when confirmed on a phone. |
| B-105 | Medium | Player | YouTube can't embed inside the claude.ai preview, so play opens YouTube in a new tab and the fallback chain only runs as a dry run. | Expected in the preview. Verify inline playback and the chain on the Vercel deploy. |
| B-106 | Medium | Barcode | Barcode lookups return example pressings, not real Discogs data. | Simulated on purpose. The real app calls `GET /database/search?barcode=` server-side with a Discogs token. |
| B-107 | Medium | Discogs sync | "Save locations to Discogs" only queues updates; "Sync now (demo)" marks them saved without calling Discogs. | Simulated on purpose. Needs a server job using the collection custom-fields endpoints within the 60 requests/min limit. |
| B-108 | Low | Data | Unit ID prefixes (K/S/C/B) and gig status names differ between the prototype and `docs/DATA_MODEL.md` / `003_features.sql`. | Pick one set before the React port. See the open questions in PRD.md. |
| B-109 | Medium | DB | `records.discogs_instance_id` isn't unique per owner, so a re-import could duplicate rows. | Add a unique index on `(owner_id, discogs_instance_id) where discogs_instance_id is not null`. |
| B-111 | High | References | Deleting a bag that a gig uses, then packing that gig, puts records into a unit that no longer exists, so they vanish from the room. | QA.md work package 2: block or reassign when deleting a unit referenced by gigs, playlists or the sync queue. |
| B-112 | Medium | Performance | Every action re-renders the whole page and writes all state to localStorage. Around 2,000 records, one arrow press takes 160–300 ms, and the Collection table builds every shelf option into every row. | QA.md work package 6: id maps, memoized covers and QR codes, debounced saves, partial renders. |
| B-113 | Medium | Escaping / a11y | Some attribute values (photo URLs, colors, ids) are inserted without `esc()`, and sheets don't trap focus. | Since the review swarm, `migrate()` forces these values into safe shapes (B-116) and closing a sheet returns focus (B-124). Still to do: `esc()` on the attributes themselves (QA.md work package 8) and a focus trap (work package 7). |
| B-114 | Medium | DB | The documented bag-scan and gig-return queries can leave homeless records unplaced. Deleting a unit has trigger side effects (it can queue a blank Location). There's no owner check or row-level security across tables, and the playlist reorder query accepts duplicate ids. | QA.md work package 12: migration 005. |
| B-129 | Medium | Performance | The Collection table still takes about 0.85 s per render at 300 records (900 `<select>`s and 3,000 `<input>`s), and every sort, filter or edit re-renders it. | Lazy Home spot options halved it (B-118). Next: window the rows or stream them after the first 80 (QA.md work package 9). See docs/REVIEW-SWARM.md P2. |
| B-130 | Medium | Touch targets | On phones, the spot-tool chips are 33px tall, the Map/Columns control 30px, the view-bar buttons 32px, and map cubbies 34px at Fit room. | Hit slop would overlap the 6px gaps. Needs a layout pass with taller controls. REVIEW-SWARM U7. |
| B-131 | Low | Performance | Selecting a spot on the Map re-renders the whole world (28 ms at 300 records, 78 ms at 2,000). | Patch `aria-pressed`/`.sel` and replace only `.spot-panel`. REVIEW-SWARM P3. |
| B-132 | Low | Performance | `save()` writes the whole state on every render (18.7 ms at 2,000 records). | Debounce to idle with a `pagehide` flush (work package 1). |
| B-133 | Low | Code | `selectSpot` resets the selected record when the same spot is selected again (both branches of the `V.dig` ternary are the same). There's dead code: `V._lastUnit`, the unused locals in `digView`, and a double `mapZoomUnit` in `map-unit`. | REVIEW-SWARM C8 to C10. |
| B-134 | Low | Player | The progress `setInterval` from `tick()` is never cleared, so it polls the DOM every 500 ms after the first play. | Clear it on pause, end and preview stop. REVIEW-SWARM C11. |
| B-135 | Low | Deep links | Hash navigation fires `popstate`, so opening a sticker link while a phone column is pushed also pops a column. | Ignore `popstate` without `state.crates`. REVIEW-SWARM C12. |
| B-136 | Low | Import | A Discogs CSV with an unterminated quote silently merges the rest of the file into one cell. | Detect an open quote at the end of the file and say so. |
| B-137 | Low | Security | The CSV formula guard misses a leading space before `=`, and ZXing loads from jsDelivr without SRI. | Trim-left before the check (work package 8); SRI (work package 4). |
| B-138 | Low | Polish | Phone sheet: the expanded record repeats the row's title and artist, and fades in again on every re-render. The phone view-bar tools are cut at the edge with no fade hint. | REVIEW-SWARM U8 to U10. |
| B-139 | Low | Accessibility | There's no `prefers-contrast: more` style, no `content-visibility` on long lists, and the map takes about 20 Tab presses before the records panel, with no skip link. | REVIEW-SWARM U11, U12, P7. |

## Fixed

| ID | Severity | What was wrong | Fix | Test |
|---|---|---|---|---|
| B-001 | High | First visit with no saved data crashed: the state block ran before the helper `const`s existed (TDZ), so the published preview could fail to load. | Moved the state block below the helpers. Tests now run with `CRATES_NO_PATCH=1`. | 01 Boot |
| B-002 | High | Naming or moving a cubby on a unit added this session crashed (`labels` undefined). | New units get `labels:{}`; the handlers guard with `||= {}`. | X9, X10 |
| B-003 | Medium | A malformed deep link (`#%E0%A4%A`) threw in `decodeURIComponent` and stopped the player from starting. | `try/catch` around the decode. | N12 |
| B-004 | Medium | The QR stickers sheet scrolled sideways at 390px (long unbroken URL). | `overflow-wrap:anywhere` on the URL. | N13 |
| B-005 | Low | Cubby subtitles overlapped the record count on the big shelf drawing. | Label is clipped with an ellipsis before the count. | X13 |
| B-006 | Low | The subtitle toast named the wrong cubby when you clicked another chip before pressing Enter. | Capture the cubby key when the change fires. | X11 |
| B-007 | Low | The deep-link hash was never cleared, so reopening the same sticker link did nothing and refresh always jumped back. | `history.replaceState` after routing. | X14 |
| B-008 | Low | Collection thumbnails rendered at 15px. | Override the `.mini-btn svg` size for covers. | N14 |
| B-009 | Low | With "Not played in a year" on, Play queued the whole cubby. | Play uses the filtered list. | — |
| B-010 | Low | After a 12-second timeout the barcode library loader stayed stuck until reload. | Reset the loader on timeout. | — |
| B-012 | High | A saved collection was silently replaced by the demo seed whenever a unit's preset key no longer existed (for example after regenerating presets). | Unknown presets now map to a close match; the seed is used only when there's no usable saved state. | 15 Persistence |
| B-013 | Medium | "Add" crashed with an empty collection; CSV export didn't neutralise formula cells (`=`, `+`, `-`, `@`). | Placeholder thumb; CSV cells starting with those characters are prefixed with `'`. | — |
| B-011 | Medium | Earlier fixes: an empty cell plus arrow key plus Undo crashed; a record filed straight into a bag couldn't unpack; removing a unit left records pointing at it; slot changes wiped typed fields; "Undo edit" lost unsaved fields; the playlist picker allowed duplicates; 4px of overflow at 390px from the sleeve stack. | See commits before `74425ac`. | X1–X8, 14 |
| B-110 | High | Partial or old saved data could crash startup to a blank app, and a full localStorage failed silently. | `migrate()` now fills or repairs every field and drops malformed entries. When storage is full, `save()` removes the oldest backups until the collection fits and says so; if nothing fits, it warns. (Review swarm, uncommitted.) | X16, X17, X22 |
| B-115 | High | Map on a phone: `mapReveal` read `vh` inside its own initializer, so deep links, search results, cue taps and the arrow keys threw whenever the sheet was up. | Measure the height first. (Review swarm.) | X15 |
| B-116 | High | Load from file (and restore) trusted ids, colors, photo URLs and YouTube ids that are put into attributes, so a crafted collection file ran script. | `migrate()` forces safe ids (and rewrites every reference), hex colors, `data:image` photos, YouTube ids and cell keys. The build adds a meta CSP that allows the inline scripts by hash only. (Review swarm.) | X16, X24 |
| B-117 | High | Records imported from Discogs had no `custom` or `cs`, so Edit details threw on them. A file without `settings` threw with no message. | Imported records get every field and a full Discogs `orig`. Load and restore validate first and say when a file can't be read. (Review swarm.) | X17 |
| B-118 | High | The Collection table built every shelf into every Home spot select: 1.7 s and 53k nodes per render at 300 records. | Options load on first touch or focus above 60 rows (0.85 s, 26k nodes). The rest is B-129. (Review swarm.) | X18 |
| B-119 | Medium | On phones, the edge-to-edge map, sheet and columns were clipped 16px on the left and `#main` scrolled sideways. Fit room put units under the zoom tools. | `#main.shell` spans the width with the gutter as padding; a 58px top inset in `mapFit`. (Review swarm.) | X19 |
| B-120 | Medium | Resizing across 780px with the map moved, or in Columns, left the sheet undraggable and desktop wording on a phone. | Re-render when the phone breakpoint flips. (Review swarm.) | X19 |
| B-121 | Medium | Phone Columns: without view transitions (reduced motion, older browsers) no history entry was pushed, so Back left the app; stepping spots stacked entries. | Every push gets one entry, same-column moves don't, and the in-app back goes through `history.back()`. (Review swarm.) | X20 |
| B-122 | Medium | The phone sheet snapped by the average speed of the whole drag, so a final flick was ignored. | Release velocity from the last 100 ms, or zero if the finger stopped. (Review swarm.) | X21 |
| B-123 | Medium | The four full-state backups share the storage quota with the collection. Once full, saves failed silently. | Covered by the B-110 fix. (Review swarm.) | X22 |
| B-124 | Medium | Closing a sheet (Escape, ✕ or the scrim) dropped keyboard focus to the page. | Focus returns to the control that opened it, or to the same control after a re-render. (Review swarm.) | X23 |
| B-125 | Medium | Add, then Record, in an empty room threw. | Shows "Add a shelf, crate or bag first". (Review swarm.) | X23 |
| B-126 | Medium | CSV export didn't quote cells containing a bare CR, so Excel split the row. | Quote on CR too. (Review swarm.) | X23 |
| B-127 | Medium | No press feedback, a grey tap flash, double-tap delay, sticky hover on touch, and 20-36px targets for preview, back, icon, step and zoom buttons. | Press states (opacity under reduced motion), `touch-action: manipulation`, hover only where hover exists, 6px hit slop, and a 44px back link. (Review swarm.) | X23 |
| B-128 | Medium | The live site's CSP allowed `'unsafe-inline'` scripts, so any injected inline handler would run. | `scripts/build.mjs` adds a meta CSP that allows the page's own inline scripts by SHA-256 only; both policies apply. The header stays the same for the claude.ai preview. (Review swarm.) | X24 |

## How to report

Add a row to **Open** with: steps to reproduce, expected and actual behavior, the browser and window size, and the console error if there is one. If you're an agent in the swarm, also add a failing test (`tests/test_crates.py`, named `X<n> …`) in the same PR.

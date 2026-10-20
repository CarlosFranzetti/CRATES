# Crates QA: checks, test catalog, error audit, review, work packages

Snapshot reviewed on 2026-10-20: `crates.html` 2,091 lines (md5 `ca157a85…`, includes the COLLECTION TABLE section and the lead's fixes for N12, N13 and X9-X14) and `tests/test_crates.py` 45 tests (md5 `6383f318…`). `crates.html` is being edited in parallel, so line numbers (`L1234`) can drift by a few lines. **Search by the function or action name first**, then use the line number. Statuses come from full `CRATES_NO_PATCH=1` runs on scratch copies: **45/45 PASS** on this snapshot, which matches `tests/REPORT.md`. The previous snapshot (md5 `8fd65fcd…`) was 37/45. A *filtered* run overwrites `tests/results.json` with just the subset, so check its length before trusting it. Raw probe output is in `docs/REVIEW-NOTES.md`.

Legend: risk **H/M/L**. **P** = prototype-only (fix in `crates.html` only if cheap). **R** = must be fixed or designed in for the React port (Vite + React + TS + Tailwind + Vercel functions + Neon, per `docs/ARCHITECTURE.md`).

---

## 1. How to run checks

```bash
cd /home/claude/crates

# 1a. Build the test harness (wraps crates.html into tests/harness.html; prints "unpatched" when the TDZ patch is a no-op)
python3 tests/build_harness.py
#     The TDZ boot-order bug is fixed in source: the state block (L747-749) now comes after `const finishesFor` (L653), so the patch does nothing.
#     Still run with CRATES_NO_PATCH=1 so a regression shows up as a crash.

# 1b. Full suite (writes tests/results.json, tests/harness.html, tests/shots/*.png; about 3.5 min)
CRATES_NO_PATCH=1 python3 tests/test_crates.py

# 1c. Single test or subset: positional args, case-insensitive SUBSTRING match on the test name, OR'd together
CRATES_NO_PATCH=1 python3 tests/test_crates.py "04 Move"
CRATES_NO_PATCH=1 python3 tests/test_crates.py N12 X9 "Collection table"
#     Caveats: "01" also matches "N01", and "X1" matches X1 and X10-X14. A filtered run OVERWRITES results.json with the subset.
#     Minimal runner change (WP10): add exact/regex selection and keep partial runs out of results.json:
#       import argparse; ap = argparse.ArgumentParser(); ap.add_argument("-k", default=None); ap.add_argument("names", nargs="*")
#       args = ap.parse_args(); want = lambda n: (not args.k or re.search(args.k, n, re.I)) and (not args.names or any(o.lower() in n.lower() for o in args.names))
#       ... out = "results.json" if not (args.k or args.names) else "results.partial.json"
#     Usage then: python3 tests/test_crates.py -k '^X1 '   (exactly X1)

# 1d. Run in isolation so you don't clobber another agent's results.json / harness.html / shots
T=$(mktemp -d) && mkdir -p $T/tests && cp crates.html $T/ && cp tests/test_crates.py tests/build_harness.py $T/tests/ \
  && (cd $T && CRATES_NO_PATCH=1 python3 -I tests/test_crates.py) ; echo "results: $T/tests/results.json"

# 1e. Syntax-check every inline <script> (qrcode lib + app). `<\/script>` inside printHtml is escaped, so the regex splits correctly.
d=$(mktemp -d) && python3 -c "import re,sys;[open(f'{sys.argv[1]}/s{i}.js','w').write(m) for i,m in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',open('crates.html',encoding='utf-8').read(),re.S))]" "$d" \
  && for f in "$d"/*.js; do node --check "$f" || exit 1; done && echo "scripts OK: $(ls "$d" | wc -l)"
#     Same for the deploy page (it adds the Vercel analytics inline scripts):
node scripts/build.mjs && d=$(mktemp -d) && python3 -c "import re,sys;[open(f'{sys.argv[1]}/d{i}.js','w').write(m) for i,m in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',open('dist/index.html',encoding='utf-8').read(),re.S))]" "$d" && for f in "$d"/*.js; do node --check "$f" || exit 1; done

# 1f. Validate SVGs (xmllint is installed at /usr/bin/xmllint)
for f in logos/*.svg; do xmllint --noout "$f" || exit 1; done && echo "SVG OK"
#     Generated sticker SVGs: N11 downloads them; add `xmllint --noout` on the downloaded file in that test (backlog T-S3).

# 1g. Validate vercel.json (syntax, plus the rewrite must not swallow /api or /_vercel)
python3 -m json.tool vercel.json >/dev/null && echo "vercel.json OK"
python3 -c "import json,re;r=json.load(open('vercel.json'))['rewrites'][0]['source'];p=re.compile('^'+r.replace('(?!','(?!')+'$');[print(u,'REWRITTEN' if p.match(u) else 'passthrough') for u in ['/','/K1-A2','/logos/mark-3.svg','/_vercel/insights/script.js','/api/units']]"
#     Today /api/units prints REWRITTEN (to index.html). Add "api/" to the negative lookahead before any function ships (ARCHITECTURE section 5 says so).

# 1h. Migrations: always on a Neon BRANCH, never on main (project super-sea-94522798, db crates)
neonctl branches create --project-id super-sea-94522798 --name qa/<wp> --parent main   # or the Neon MCP create_branch tool
URL=$(neonctl connection-string qa/<wp> --project-id super-sea-94522798 --database-name crates --pooled)
for f in app/db/0*.sql; do psql "$URL" -v ON_ERROR_STOP=1 -q -f "$f" || break; done   # apply in order
for f in app/db/0*.sql; do psql "$URL" -v ON_ERROR_STOP=1 -q -f "$f" || break; done   # second pass must be a no-op (idempotency)
psql "$URL" -c "explain (analyze, buffers) <query from docs/DATA_MODEL.md with literals>"
neonctl branches delete qa/<wp> --project-id super-sea-94522798
#     psql is installed at /usr/bin/psql. neonctl is NOT installed here: use `npx neonctl@latest` or the Neon MCP tools (create_branch, run_sql_transaction, explain_sql_statement, delete_branch).
```

---

## 2. Test catalog

All 45 tests in `tests/test_crates.py`. Every test except the browser-level ones (14, X7, N13, N14b, N15, X13) gets a fresh context, `localStorage.clear()`, the demo seed, and external requests aborted. Status: **45/45 PASS** on the current snapshot. N12, N13 and X9-X14 failed on the previous snapshot. Each exposed a real app bug, and the lead has since fixed all of them, so they now act as regression guards. The bold text in those rows describes the bug each one guards. X11 was timing-sensitive while the bug existed: the toast read `V.cell` inside `setTimeout`, and the fix captures `k` first.

| ID | Name | Covers | Key assertions | Status |
|---|---|---|---|---|
| 01 | Boot | Initial view, mini player, link-mode fallback | K1 detail open on A1, "1 of 5", 5 list rows, play button is a youtube.com/watch link, K1 is 2x4, no console errors | PASS |
| 02 | Search | `#q` search, Enter/arrows, unit hits | "voodoo" first hit is Voodoo Ray with chip "Crater"; Enter opens the bag and clears the query; "zzz" shows "No match"; "kallax" gives an open-unit hit | PASS |
| 03 | Flip-through | `dig`, arrows, chips, cube click, swipe | Prev disabled at 1; arrow keys clamp at 5; All=7; empty cell shows "empty"; swipe advances | PASS |
| 04 | Move one record | `move`, `move-to`, undo | Toast "Moved to K1·B3"; loc and home updated; chip counts; undo restores loc and home | PASS |
| 05 | Put in bag / Back home | `to-bag`, `go-home` | r9 into B1; "Back to K1·A1" button; toast "Back in K1·A1" | PASS |
| 06 | Bag scan + unpack | `scan-*`, `empty-bag` | Diff rows = "Update N"; total stays 10; undo restores every loc; unpack sends records to home slots | PASS |
| 07 | Add furniture | Preset group and preset, finish, custom color, rows/cols, duplicate ID | 2x2 prefill; 3x5 preview has 15 cubes; custom #ff00aa; name survives re-render; C5 chip; "ID K1 is taken" | PASS |
| 08 | Add bag | Brand filter, preset, color, custom color | Filter counts per brand; All restores; B2 card shows the custom hex | PASS |
| 09 | Add record | `ar-loc`, manual add | Lands on K1·B2 "1 of 1"; search finds it with chip K1·B2 | PASS |
| 10 | Edit details | Edit sheet, stars, custom fields, revert | Title edit shows the edited dot; 128 BPM and ★★★★; 2 tags; custom kv; revert restores the title and keeps BPM | PASS |
| 11 | Playlists | Rename, up/down, remove plus undo, picker, sort, duplicate, delete, pack | Item orders exact; "Add 2 records"; pull-order sort; duplicate "copy"; in-page delete confirm; pack moves all to B1 | PASS |
| 12 | Player | Now-playing sheet, tabs, dry run, prev/next wrap, Esc | 4 links, 5 chain steps, dry-run steps animate; queue 10; wrap to "Around The World"; Esc closes | PASS |
| 13 | Settings | Accent, reset confirm | data-accent changes; reset waits for confirm; 10 records restored; toast | PASS |
| 14 | Layout + screenshots | 390/1280, light/dark, 7 states | scrollWidth ≤ 390 in every state; screenshots | PASS |
| 15 | Persistence | localStorage round trip | Move and rename survive reload; key `crates-demo-v3` | PASS |
| X1 | Empty cell arrow, then Undo | Undo after empty-bag plus arrow | No error; "1 of 3" | PASS |
| X2 | Homeless bag record stays on unpack | Record filed into a bag has no home | Stays in bag; toast says "no home shelf" | PASS |
| X3 | Removing a unit that is a home | `del-unit-yes` with homes pointing at it | 10 records still visible; search Enter does not throw | PASS |
| X4 | Add record keeps typing on slot change | Draft survives re-render | Artist kept | PASS |
| X5 | Undo edit keeps unsaved fields | `revert` | Unsaved BPM kept | PASS |
| X6 | Picker blocks duplicates | Playlist picker | Already-present record is disabled; appears once | PASS |
| X7 | YouTube API hang → link mode | `loadYT` 6 s timeout | Link mode in under 8 s (measured 5.8 s) | PASS |
| X8 | Look & name custom color | `applyCustom('eu')` | K1 finish = #123456 | PASS |
| N01 | Duplicate warning | `findDupes`, `showDupe`, barcode dupe | Banner text and location; "Add another copy"; case-insensitive; "Show it" navigates; 3 candidates flagged "own" | PASS |
| N02 | Barcode lookup | `lookupBarcode`, `bc-pick`, photo fallback | 3 example candidates labelled; pick fills 5 fields; short-code message; PNG with no barcode shows "Couldn't read" | PASS |
| N03 | Discogs Location sync | Settings toggle, `sync-run`, queue plus undo | 10 waiting; pills; queue after move = `r9=K1·B3`; undo restores the queue | PASS |
| N04 | Cubby subtitle | `#cell-name` change, search by subtitle | Chip and cube label; toast; search "house" finds r9; clearing removes it | PASS |
| N05 | Whole-cubby move | `cubby-move`, `cubby-to`, undo, into bag | Homes, label and view follow; undo labels exact; bag keeps home and from | PASS |
| N06 | Swap cubbies | `cubby-swap`, `swap-to` | Counts, labels and homes swapped; undo | PASS |
| N07 | Multi-select move | `toggle-sel`, `sel-move`, `multi-to`, `sel-all` | Move 2 to crate sets `from`; undo; select-all = 7 | PASS |
| N08 | Came-from | `from` chips in bag view | "from K1·A2" rows; dig info "came from" | PASS |
| N09 | Set history + stale | `log-play`, stale list, stale playlist, stale filter | Stale 6 → 5 → undo; 6 rows; playlist of 6; empty-state copy | PASS |
| N10 | Gigs | Plan → load-out → out → return → done, new gig, delete | Pack moves to bag with `from`; play logged on the gig date; summary "1 not checked back in"; new gig from playlist; confirm delete | PASS |
| N11 | QR stickers | Sheet, sizes, cubby toggle, unit toggle, html/svg/png download | 11 stickers; path length > 500; widths 96/144/192; 3 downloads; no errors | PASS |
| N12 | Deep links | `routeHash` | `#K1-B2` boot; `B1`; invalid ignored; lowercase; out-of-range → All; **malformed `%E0%A4%A` throws `URIError`** | PASS (fixed; was FAIL) |
| N13 | 390px + no errors on new flows | 11 new-flow states at 390 | **stickers sheet is 417px wide (overflow)** | PASS (fixed; was FAIL) |
| N14 | Collection table | `go-table`, filters, inline edit plus Enter, rating, bag/home selects, `t-back`, sort, bulk put-back plus undo, search | Rows 10, bag filter 3, edits keep `orig`, toasts, aria-sort, undo | PASS |
| N14b | Collection 390px + 844x390 | Table layout | No page overflow, with and without selbar | PASS |
| N15 | README screenshots | 14 screenshots | No errors | PASS |
| X9 | Subtitle on a just-added shelf | New unit lacks `labels` | **TypeError "setting '0-0'"** (L1414) | PASS (fixed; was FAIL) |
| X10 | Named cubby into a just-added shelf | `cubbyMove` into a new unit | **TypeError after records already moved; sheet stays open; state half-applied** (L1434) | PASS (fixed; was FAIL) |
| X11 | Subtitle toast after blur-by-click | Toast reads `V.cell` lazily inside `setTimeout` | **Toast names the wrong cubby when the click lands before the timer** (race, L1415) | PASS (fixed; was FAIL) |
| X12 | Same sticker link twice | Hash never cleared | **Re-scanning the same QR does nothing** | PASS (fixed; was FAIL) |
| X13 | Cube subtitle vs count overlap | `.lbl em` vs `.cnt` geometry | **Overlap at 1280 (A1) and 390 (A1, A2)** | PASS (fixed; was FAIL) |
| X14 | Collection thumbnails full size | `.mini-btn svg` rule | **Cover draws at 15px inside a 32px thumb** | PASS (fixed; was FAIL) |

### 2.1 Coverage gaps (measured)

I measured V8 function call counts (CDP `Profiler.startPreciseCoverage`) over the whole suite. Method and raw data are in REVIEW-NOTES. 121 action keys: **86 called, 35 never**. `pk-done` is a false negative: it is a closure assigned at runtime (L1269) and test 11 does click it. 164 top-level functions: **150 called, 14 never**.

**Actions never invoked by any test** (definition line):
`dig-to` 1842 · `eu-finish` 1866 · `eu-nophoto` 1867 · `file-found` 1871 · `er-delkv` 1876 · `add-to-pl` 1877 · `atp` 1878 · `atp-new` 1879 · `new-pl` 1881 · `pl-color` 1882 · `pl-play` 1883 · `pl-shuffle` 1884 · `pl-del-no` 1892 · `play-rec` 1899 · `play-unit` 1900 · `play-all` 1901 · `p-toggle` 1902 · `p-at` 1903 · `close-np` 1904 (Esc path only) · `open-gig` 1911 · `gig-rm` 1913 · `gig-add` 1914 · `gpk-done` 1919 · `gig-back` 1922 · `gig-reopen` 1923 · `gig-play` 1924 · `gig-del-no` 1926 · `stale-play` 1930 · `sel-bag` 1936 · `stk-print` 1949 · `t-back-all` 2070 · `t-sel-none` 2071 · `t-sel-pl` 2073 · `t-pl-to` 2076.

**Functions never called**: `setQueue` 1698 (so nothing ever starts a new queue), `loadCandidate` 1711, `onYTState` 1719, `failCandidate` 1730, `toggle` 1741, `tick` 1747, `fmt` 1748 (the whole inline-YouTube path: tests abort `iframe_api`), `runScanAI` 922, `identifyShelf` 1136, `foundList` 1131 (Claude vision paths), `shrink` 1155 (no photo upload test), `openAddToPlaylist` 1271, `printStickers` 1611, `awayFromHome` 1971.

**Non-action paths with no test**: the `change` handlers for `t-sel-bag` (bulk to bag, L2034ff) and `gig-pl` (add playlist to gig, L1532ff); the `pl` drag reorder (`bindPlaylist` pointer events, L1240); the `keydown` Enter-to-next-cell in the table (L2047); `#t-q` debounce (partially covered by N14); the AI error codes (`not_granted`, `rate_limited`); localStorage failure modes; old or partial saved-state shapes; the 2,000+ record scale.

### 2.2 Proposed tests: the swarm's backlog

Steps are written against the existing `App` helper. "Expect" is the pass condition. IDs are suggestions: `T-` means a new feature test, `E-` means an error or negative test.

| ID | Name | Steps | Expect |
|---|---|---|---|
| T-P1 | Play from shelf | K1 → click `.dig-nav [data-act=play-rec]` | `P.queue` = A1 ids, `P.i`=0, mini player title = r9, `P.src`="K1·A1" |
| T-P2 | Play unit / all / stale / gig / playlist / shuffle | Click each of `play-unit`, `play-all`, `stale-play`, `gig-play`, `pl-play`, `pl-shuffle` | Queue length = source size; `#np-sheet` opens where documented; shuffle is a permutation |
| T-P3 | Queue jump and toggle | Open NP, queue tab, click `.pli[data-i=3]`; then `p-toggle` (yt mode via stub) | `P.i`=3; playing flips |
| T-P4 | YT stub: fallback chain | `route` `iframe_api` → fulfill with a fake `YT.Player` that emits `onError(150)` for id #0 and state 1 for id #1 | `st.fails[0]` set, `st.cand`=1, status "Playing", links tab shows primary red |
| T-P5 | YT stub: all links dead | Stub emits error for every id | After the last link: `non_working`, auto-skip in 1.5 s; **after N consecutive dead tracks the player stops** (needs the dead-list guard, PLAYER hazard 4) |
| T-P6 | YT stub: teaser | Stub reports `getDuration()=12` on state 1 | Candidate failed "likely a teaser"; the next candidate loads |
| T-P7 | Close NP by grab / scrim | Click `.np-scrim` and `.grab` | `#np-sheet` gone, `P.open` false |
| T-L1 | Add to playlist from record | `+ Playlist` → `atp` on p2 → reopen → p2 disabled; `atp-new` | p2 gains r9 once; new playlist "New playlist" with [r9]; view = playlists |
| T-L2 | New playlist, color, cancel delete | `new-pl`, `pl-color`, `pl-del`, `pl-del-no` | Playlist added; color saved; confirm disappears, nothing deleted |
| T-L3 | Drag reorder | Mouse down on `[data-handle=0]`, move below item 2, up | Order r4,r7,r1,…; saved to localStorage |
| T-L4 | Drag reorder by keyboard | Focus handle, Space, ArrowDown, Space | Same as T-L3 (fails until a11y WP7) |
| T-G1 | Gig add/remove records | `gig-add` check 2 → `gpk-done`; `gig-rm` one | Items +2 then −1 |
| T-G2 | Gig back to plan / reopen / cancel delete | Pack 1, `gig-back`; finish with missing, `gig-reopen`; `gig-del-no` | Defined behavior for packed items when going back (today they stay in the bag with `packed=true`); status `return` after reopen |
| T-G3 | Gig add playlist via select | Select `#gig-pl` = p2 | Toast "N added from Acid hour"; no duplicates |
| T-U1 | Unit finish / photo | `eu-finish` swatch; upload `_png()` to `#eu-photo`; `eu-nophoto` | Finish saved; `u.photo` starts `data:image/jpeg`; back to drawing |
| T-U2 | Add furniture/bag with photo | Upload to `#af-photo` / `#ab-photo` | "Photo added ✓"; unit card shows `<img>` |
| T-U3 | Corrupt image upload | Upload a 10-byte file named `x.jpg` | `shrink` resolves null; no error; label stays "Take or choose…" |
| T-R1 | File found records | Inject `addRec.found=[…]` via ev, `renderAddRecord()`, untick 1, `file-found` | Only ticked records filed; "Tick at least one record" when none |
| T-R2 | Custom field delete | Edit → `er-addkv` ×2 → `er-delkv` first | One field saved |
| T-R3 | Dig by clicking list/sleeve | Click `.list .li[data-i=3]` and a side sleeve | Counter "4 of 5" |
| T-S1 | Bulk to bag (single bag) | Select 2 → `sel-bag` | Both in B1, `from` set, undo works |
| T-S2 | Print stickers | Stub `window.print`; click `stk-print` | `#print-sheet` holds N page SVGs; print called once |
| T-S3 | Sticker SVG well-formed | Save SVG download → parse with `xml.dom.minidom` | Parses; one `<path>` per sticker |
| T-T1 | Table: all actions | `t-back-all`, select → `t-sel-none`, select 2 → `t-sel-pl` → `t-pl-to` (existing and new), `t-sel-bag` select | Counts and toasts; undo for back-all and bulk bag |
| T-T2 | Table: Enter moves to next cell, Shift+Enter back | Fill title, Enter; Shift+Enter | Focus on next/previous row's title input; value saved |
| T-T3 | Table: undo a cell edit | Edit title, then `undo` | Title restored (fails today: `tCommit` sets no `lastUndo`) |
| T-T4 | Table: CSV formula neutralised | Set r1.title = `=HYPERLINK("x")`, `+1`, `-1`, `@a`; export with downloads stub | Every such cell starts with `'` (or a tab); quotes doubled |
| T-T5 | Table at 2,000 rows | Inject 2,000 records, `go-table` | Render < 300 ms; scroll stays smooth (measure); no errors |
| E-1 | Corrupt saved state | For each mutation in REVIEW-NOTES P1 (`{v:2}`, no settings, record without yt/tags, no recent), set localStorage, reload | App boots (room shows ≥1 card) and shows a "restored/repaired" notice; **today 4 of 6 crash** |
| E-2 | Unknown preset key keeps data | Add a record, set `S.units[0].preset='gone'`, save, reload | My record still present (**today: whole collection silently reseeded**) |
| E-3 | Quota exceeded | Override `Storage.prototype.setItem` to throw, then move | Visible warning "Couldn't save…" (**today: silent**) |
| E-4 | Boot survives any routing/boot throw | Make `routeHash` throw (monkeypatch via `add_init_script`), then load | Room and mini player still render; one error toast. Malformed `%E0%A4%A` is already covered by N12, fixed on this snapshot |
| E-5 | Gig bag deleted | Gig with bag B2; delete B2; tick pack | Pack disabled or error toast; record never gets `loc.u` of a missing unit (**today it vanishes from the room**) |
| E-6 | Empty collection | `S.records=[]`, `open-add` | Add sheet opens (today TypeError in `cover`) |
| E-7 | Async result after sheet closed | Stub `AI.json` / ZXing to resolve after 500 ms, close sheet first | No error writing to `#scan-out` / `#ar-bc` |
| E-8 | Downloads capability rejects | Stub `window.claude.use('downloads')` to resolve `{save:()=>Promise.reject({code:'declined'})}` | "Save cancelled." / "Export cancelled" |
| E-9 | Escaping fuzz | Create unit name, record fields, playlist name, gig name, tags and custom kv with `"><img src=x onerror=window.__x=1>` | `window.__x` undefined everywhere; text renders literally |
| E-10 | Duplicate ids in state | Push a record with an existing id; reload | Repaired or warned; `rec()` deterministic |

---

## 3. Error-checking audit

`BUGS.md` does not yet list rows #1, #2, #3, #5, #18, #21, #25 and #26 below. The owning work package should add them as B-1xx when it starts. Also, two `BUGS.md` Fixed rows cite the wrong test: B-003 (malformed deep link) is guarded by **N12**, and B-006 (subtitle toast) by **X11**.

| # | Failure point (where) | Current behavior (verified = probe or test) | Risk | Recommended fix |
|---|---|---|---|---|
| 1 | Saved-state load `L747-749` | `JSON.parse` in try/catch: invalid JSON → reseed (verified). Shape checks are only `S.v===2` plus `units.every(preset resolvable)`. Missing `units` → TypeError at top level, **blank app** (verified). | H | Wrap load+migrate in try/catch; on failure keep the raw string under `crates-demo-v3.bak-<ts>`, reseed, toast "Couldn't read saved data; a backup was kept". |
| 2 | Unknown preset key `L748` | Any unit whose preset key vanished (e.g. after `research/build_presets.py` renames keys) makes the **whole saved collection silently replaced by the seed**, then saved over (verified P2). | **H** | Never reseed for preset misses: `presetOf()` already falls back (`L651`). Remove the `every()` clause or map unknown keys to a fallback and flag the unit. Add E-2. |
| 3 | `migrate()` `L635` | Fills gigs, syncQueue, discogsSync, labels, plays, barcode, from. Not filled: `settings` (crash, verified), `recent` (Move sheet never opens, verified), `playlists`, `records[].yt/tags/custom/orig/pal/pat/rating` (`stOf` and `search` crash, verified), `units[].finish`. | H | Make `migrate` total: default every field and drop records whose `loc` is invalid into a "Lost" bucket. Validate with a small schema (Zod in the port). |
| 4 | v2/v3 versioning | Key `crates-demo-v3` with `S.v===2`. No version bump path; any `v` other than 2 → reseed (data loss). | M | `S.v` = schema version; `migrations[v]` chain; never reseed for an unknown version, refuse and keep a backup. |
| 5 | `save()` `L750` | `try{setItem}catch{}`: QuotaExceeded is silent (verified P9). Called on **every** `render()` (`L763`), so every arrow key serialises the whole state (1 MB at 2k records). Photos are stored inline as data URLs (~60-150 KB each), so the 5 MB quota is reached at roughly 30-60 photos. | H | Debounce (250 ms plus `pagehide`); surface a persistent banner on failure; move photos to IndexedDB (prototype) or Blob storage (port). |
| 6 | `claude.use('sample')` `L2084` | Null or rejected → `AI=null`; UI hides photo buttons. `limits()` failure → `AI_IMAGES=false`. OK. | L | Keep it. Log the reason in a debug panel. |
| 7 | `AI.json` errors `runScanAI L922`, `identifyShelf L1136`, barcode `L1361` | `not_granted` and `rate_limited` are handled in scan; identify handles `not_granted` only; barcode swallows everything. Any other code shows a generic "try a brighter photo". **No timeout**. Results write into `$('#scan-out')`/`$('#ar-out')` after `await` with no check that the sheet is still open, so they throw if it was closed. | M | Shared `aiCall()` with a timeout (30 s), an AbortController and a code → message map (`not_granted`, `rate_limited`, `declined`, `timeout`, `bad_json`). Check `scan`/`addRec` identity before writing. Validate the JSON shape (ids are strings, ≤ 40 items). |
| 8 | `claude.use('downloads')` `saveStickers L1586`, `exportCSV L2053` | Null → anchor download outside the artifact, or "not available" inside it. `declined` handled; other errors give a generic message. | L | OK. Add E-8. |
| 9 | YouTube IFrame API `loadYT L1680` | 6 s timeout → link mode (X7 verified 5.8 s); a second 6 s `onReady` timer (`L1695`). A late `onReady` flips back to `yt` mid-session. `onYouTubeIframeAPIReady` is overwritten globally. | M | One state machine (PLAYER section 5); ignore a late ready unless the user opts in; never flip mode while a track plays. |
| 10 | YT `onError` `L1694` | Every code is treated as "try next candidate". Spec: 100/2/5 terminal, 150/101 recoverable. | M (R) | Classify codes as in PLAYER section 3.3. |
| 11 | Dead queue | `playAt` resets `non_working` to pending (`L1705`); records with no links skip every 3 s. **No consecutive-skip limit**, so an all-dead queue loops forever (PLAYER hazard 4, by code reading). | M (R) | Stop after `queue.length` consecutive failures and show "Nothing playable". |
| 12 | Teaser guard `onYTState L1719` | `getDuration()<30` is checked without confirming the loaded video id (PLAYER section 3.4 hazard). `tick()` `setInterval` (`L1747`) is never cleared on pause, close or reset. | M (R) | Compare `getVideoData().video_id`; clear the interval in `toggle`, `closeNP` and `reset-yes`; `reset-yes` should call `clearTimers()` and `P.yt?.stopVideo()`. |
| 13 | ZXing CDN `loadZXing L1344` | Timeout and `onerror` now reset `zxingLoading` (fixed on this snapshot). Still no SRI, and the timeout keeps firing after a successful load (harmless no-op). CSP allows jsdelivr. | L | Pin with an `integrity` hash; self-host in the port. |
| 14 | BarcodeDetector `L1348ff` | Feature-detected; errors swallowed; `createImageBitmap` result is never `.close()`d. | L | Close the bitmap; a single try/catch per tier is fine. |
| 15 | FileReader/image decode `shrink L1155` | `onerror` → null. No type or size check before decode (a 50 MP HEIC can OOM a phone). Canvas from `img.width` is fine; `toDataURL` can throw on a tainted canvas (not possible from a blob). EXIF orientation is ignored on older Safari. | M | Accept `image/jpeg,png,webp` only; reject > 15 MB; use `createImageBitmap(file,{imageOrientation:'from-image'})`; strip EXIF GPS (ARCHITECTURE section 5). |
| 16 | Canvas `toBlob` `svgToPng L1606` | Null blob → reject('png') → caught by `saveStickers`. Large multi-page sheets at scale 3 (2448×3168) are fine. | L | OK. |
| 17 | Hash routing `routeHash L1614` | **Fixed on this snapshot**: `decodeURIComponent` is in try/catch, and the hash is cleared with `history.replaceState`, so the same QR works twice (N12, X12 pass). Remaining: the two-letter row parse ignores the first letter (`AB` = `BB`); boot (`L2089-2090`) still has no per-step isolation, so any other boot throw would skip player init. | L | Strict row parse; wrap boot steps individually. |
| 18 | Deleted units referenced elsewhere | `del-unit-yes L1869` cleans `home` and `recent` only. Not cleaned: `gigs[].bag` (packing puts records into the missing unit, so they **disappear from the room**, verified P4); `from` (handled by `fromOf` fallback); `stk.units`; `V.unit` (reset); `syncQueue` values. | H | Block delete when a gig references the unit, or null `g.bag` and disable load-out; a generic `place()` guard: `if(!unit(to.u)) throw`. |
| 19 | Deleted records referenced | There is no record delete in the prototype. Playlists, gigs, `P.queue` and `syncQueue` already tolerate missing ids (`rec(id)?`, filters). | L now, H in port | Port: FK cascades (exist in SQL) plus client cache invalidation. |
| 20 | New units missing fields `bindDraftForm L1043-1058` | **Mitigated on this snapshot**: new units get `labels:{}`, and the subtitle, cubby-move and swap handlers default `labels \|\|= {}` (X9, X10 pass). There is still no single unit factory, so other fields (`finish`, `photo`) depend on each creator, and `cubbyMove` still mutates before validating. | M | `makeUnit()` factory; validate before mutating (X10 showed half-applied state was possible). |
| 21 | Empty collections | `openAdd` crashes with zero records (`thumb(S.records[0])` `L982`, verified). `openAddRecord` needs `S.units[0]` (`L1096`). Play-all with none: safe. | M | Guard both; empty-state copy. |
| 22 | Duplicate IDs | Unit ids sanitised to `[A-Z0-9]` and checked on create; not re-validated on load. Record ids `uid()` (time+rand 1e4, `L669`). Duplicates from storage make `rec()` return the first. | L | Validate on load; `crypto.randomUUID()`. |
| 23 | Large collections | 2,007 records in K1 All: `render` 195-235 ms, each `dig` arrow 160-300 ms (3 runs), state 1 MB (verified P7). Table at 2k: renders `rows × all shelf cells` `<option>`s (`shelfOptions L1987`, called per row). | M (R) | See section 4 items 1-4. |
| 24 | Async gig/scan state | `gigCheck L1525` assumes `curGig()`; `scanApply L965` assumes `scan` non-null. Reachable only via their sheets today. | L | Early-return guards. |
| 25 | CSV export `L2052-2053` | `csvCell` quotes `,"\n` but doesn't neutralise **formula injection** (`=`,`+`,`-`,`@`, tab, CR at cell start). Discogs titles and notes are untrusted. Also no BOM (Excel mangles non-ASCII). | M (R) | Prefix a single `'` when `/^[=+\-@\t\r]/`; add a `﻿` BOM; T-T4. |
| 26 | Table edits `tCommit L2025` | Writes any `data-tedit` field with no allowlist, no undo, and no validation of year/BPM; saves without render (OK). | M (R) | Allowlist fields; numeric validation; `lastUndo`; in the port use the API's column allowlist (ARCHITECTURE section 1). |
| 27 | Undo model | Single-level `lastUndo`, overwritten by any later action. Unit delete, reset, table edits and drag reorder have no undo. Undo of a sort restores an array reference. | M | Command stack (port: event log + `/api/moves/:id/undo`). |

### 3.1 Runtime assertions and guards worth adding

- [ ] `assertState(S)` after load and after each action in dev: every `r.loc.u` and `r.home?.u` resolves; cell keys are within `rows×cols`; unique ids; `S.recent`, `S.playlists`, `S.gigs` and `S.syncQueue` are arrays.
- [ ] `place()` refuses an unknown target unit or an out-of-range cell and logs it.
- [ ] `save()` reports failure once with a banner. Debounced. Writes a backup on schema change.
- [ ] A load failure never overwrites the stored string without a backup.
- [x] `routeHash` try/catch, then clear the hash (done on this snapshot).
- [ ] Async writers check that their sheet or draft is still current (`if(scan!==mine) return`).
- [ ] `loadZXing` resets its cached promise on timeout; script has `integrity`.
- [ ] Player: consecutive-failure counter; `clearInterval(P.progT)` on pause, close and reset; video-id check before the teaser guard.
- [ ] `makeUnit()` factory with `labels:{}`; `del-unit` checks gigs.
- [ ] CSV: formula neutralisation and BOM.
- [ ] In dev, a global `window.onerror` that shows a toast so silent breakage is visible during manual QA.

---

## 4. Code review: optimization and maintainability

Ranked by impact × effort. Impact and effort are each 1-3 (3 = high impact, 1 = low effort). Measured numbers come from probe P7: 2,007 records in K1, Chrome, desktop.

| # | Finding (lines) | Impact | Effort | Scope |
|---|---|---|---|---|
| 1 | **Full re-render via `innerHTML` on every action**: `render()` `L754-763` rebuilds `#main`, including the room cards (each a full furniture drawing with up to 40 spines per cell) and the entire dig list (`digView L814`, one `<button>` with an SVG cover per record). One arrow press takes 160-300 ms at 2k records. The table does the same per bag/home change (`setTimeout(render)` at `L2037-2046`). | 3 | 2 | R: React keyed components; virtualise `.list`, `.pick` and table rows (`@tanstack/react-virtual`). P: render only `.dig` on `dig`/`dig-to`. |
| 2 | **`save()` on every render** (`L763`) plus `tCommit` (`L2032`): `JSON.stringify` of 1 MB each time. | 3 | 1 | P: debounce 250 ms plus `pagehide`. R: server is the source of truth; TanStack Query cache. |
| 3 | **Repeated O(n) scans**: `inCell` (`L664`) is a full filter, called per cube, per chip and per room card (20 call sites); `rec()` and `unit()` (`L647-648`) are `find` (21 and 42 call sites), inside loops (`renderItems`, `sortPl` comparator is O(n log n × n), `renderGig`, `search`). `editedSet` runs 6× per table row. | 2 | 1 | P: build `byId`, `unitById` and `byCell` maps once per render (memo keyed on a mutation counter). R: selectors with normalized store. |
| 4 | **Table renders `shelfOptions()` per row** (`L1987`, inside `renderTable L1990`): rows × cells `<option>`s. 2k records × 8 cells = 16k options plus 2k bag selects. | 2 | 1 | P: render the home select lazily on focus, or one shared `<datalist>`. R: combobox popover. |
| 5 | **`cover()` regenerated per render** (`L671`): pattern 3 emits 36 circles. Each record's SVG is rebuilt for list, sleeve, thumb, player and table. It also emits `id="sh${r.id}"`, so the same record twice produces **duplicate DOM ids** (3 duplicates at boot, verified P10). | 2 | 1 | P: memoize by `id+pal+pat`; drop the gradient id (use a CSS overlay). R: real Discogs cover `<img loading=lazy>`; placeholder art via CSS. |
| 6 | **QR generation per render** `qrPath L1542` via `stickerSVG L1549`. `renderStickers L1569` calls `sheetPages(items)` **only to count pages**, which builds every page SVG and so every QR a second time. Every chip toggle re-runs everything. | 2 | 1 | P: memoize `qrPath(url)`; compute pages arithmetically. R: same, inside `useMemo`. |
| 7 | **Delegated listeners scattered**: listeners are registered once (no per-render accumulation, verified), but there are 4 document `change` listeners (`L1082, L1413, L1532, L2034`), 3 document `keydown` (`L1418, L1957, L2047`) plus `#q` keydown, 1 document `input` (`L2050`) plus `#q` input, 2 document `click` (`L1663, L1951`). Order-dependent and hard to reason about. Also around 40 `el.onX =` re-bindings per render (safe, but easy to forget). | 1 | 1 | P: one dispatcher per event type keyed by `data-*`. R: disappears with React handlers. |
| 8 | **Runtime mutation of the action map**: `A['pk-done']` (`L1269`) and `A['gpk-done']` (`L1919`) capture stale closures. A static catalog is impossible. | 1 | 1 | P: pass state through `draft`. R: component state. |
| 9 | **Large inline `RESEARCH` JSON** (`L573`, about 38 KB on one line) plus 20 KB qrcode lib: 235 KB → 252 KB page. | 1 | 1 | R: `GET /api/presets` (ARCHITECTURE section 3), cached; qrcode as an npm dep, lazy-loaded with the sticker sheet. |
| 10 | **Async UI races**: AI, ZXing and barcode writers touch DOM nodes that may be gone (section 3 #7). The subtitle toast read `V.cell` late (X11, now fixed by capturing `k`); the same pattern remains in other `setTimeout` toasts, e.g. table `tbag`/`thome` read `t.value` and `r` late. | 2 | 1 | P: capture values before `setTimeout`; identity checks. R: effects with abort and cleanup. |
| 11 | **`simScan` comparator** (`L939`) uses `hash(a.id+Date.now())`, so `Date.now()` can differ between calls and the comparator is inconsistent. Harmless (sim only). | 1 | 1 | P. |
| 12 | **`dig()` uses the unfiltered list** (`L859`) while the view filters stale. `renderDetail` re-clamps, so no visible bug (verified P6), but there are two sources of truth. | 1 | 1 | R: one derived list. |
| 13 | **CSS size and duplication**: about 430 lines. The dark-mode token block is duplicated (`L19-24`: `prefers-color-scheme` and `[data-theme=dark]`, required by the artifact contract). Many inline `style="font-size:13px"` and `muted` combinations in templates (search `style="font-size:13px`). New table and landscape CSS (`L432-489`). | 1 | 2 | R: Tailwind tokens in `tailwind.config` plus a `text-meta` utility; no inline styles. |
| 14 | **Accessibility: sheets** (`openSheet L1628`): `role=dialog aria-modal` without a label (verified P8); **no focus trap** (Tab leaves the sheet, verified); focus not restored to the opener on close; Escape works. The NP sheet has `aria-label` but the same trap and restore gaps. | 3 | 1 | R: Radix/shadcn `Dialog`/`Sheet`. P: `aria-labelledby` the `h2`, trap and restore. |
| 15 | **Accessibility: toggles and tabs**: section tabs use `aria-pressed` (should be `aria-current="page"`); NP tabs have `role=tab` with `aria-pressed` (needs `aria-selected` plus `role=tabpanel`) (`L1821`); stars have no `aria-pressed`; chips use `aria-pressed` (OK). | 2 | 1 | R and P. |
| 16 | **Accessibility: contrast** (computed): light `.pill.out`/`.own` 3.2:1, `.pill.in` 3.5:1 at 11.5px; `.stale` on `--bg` 3.4:1; toast Undo in dark mode with brass 2.7:1 and cyan 2.3:1; red focus ring on `--bg` 3.9:1 (≥3 OK). AA needs 4.5:1 for this text size. | 2 | 1 | Darken `--warn`/`--ok` text tokens for pills (e.g. `--warn-ink:#8A5300`); toast Undo uses `--bg`-relative accent. |
| 17 | **Accessibility: drag reorder** (`bindPlaylist L1240`): pointer only. The handle is a button with no key handler. Up/down buttons exist as an alternative (OK), but the "Drag to reorder" label promises a gesture that keyboard users can't perform. | 1 | 1 | R: `@dnd-kit` keyboard sensor (space plus arrows, PLAYER section 7). |
| 18 | **Layout bugs found by tests**: sticker sheet 417px at 390 (N13), cube label/count overlap (X13), table thumbnail 15px (X14). **All fixed on this snapshot**; keep the tests. | 0 | 0 | Done. |
| 19 | **Security: unescaped interpolations**. All user text goes through `esc()` (`L646`). Not escaped, but stored-state-controlled: `src="${u.photo}"` (`L771, L803`); `style="--pc:${p.color}"` (`L1196, L1274, L2075`); `--c:${r.pal[0]}` (`L696`); `--fin:${f.hex}` (`L702`); `data-u="${u.id}"`, `data-r="${r.id}"` (many); YouTube ids in text and `href` (`L1804`, `mainBtn L1761`); `c.note` (`L1326`) and `a.bcMsg` (`L1110`) are trusted HTML strings (built with `esc()` today, but fragile). Exploitable only by whoever controls storage today (self-XSS). In the port these come from the DB or Discogs. | 2 | 1 | R: JSX escapes text, but validate `href`/`src` schemes, hex colors (`/^#[0-9a-f]{6}$/i`) and YT ids (`/^[\w-]{11}$/`); never use `dangerouslySetInnerHTML`. P: `esc()` every attribute. |
| 20 | **Security: CSV formula injection** (section 3 #25). | 2 | 1 | R and P. |
| 21 | **Security: third-party script** ZXing from jsdelivr has no SRI. `build.mjs` injects Vercel Analytics and Speed Insights (`/_vercel/insights/script.js`, `/_vercel/speed-insights/script.js`): allowed by CSP `script-src 'self'` and `connect-src 'self'`. They 404 until enabled in the Vercel dashboard (not a functional problem). | 1 | 1 | Pin or self-host ZXing. Note analytics in a privacy line on the page. |
| 22 | **Copy and terminology**: "cubby", "shelf", "slot", "cell" and "spot" are all used for the same thing (e.g. "Home spot" in the table vs "home slot" in moves vs "shelf B2" in addresses); "Bag" vs "Bag or crate" (gigs accept crates); "Put back" (table) vs "Back to K1·A1" (dig) vs "Unpack to home slots" (bag). Status names differ between prototype gigs (`packing/return/done`) and SQL (`packed/returned`). | 1 | 1 | Glossary in PRD: **unit**, **cubby** (UI) = cell (code), **home**, **came from**; one verb "Put back". |
| 23 | **Table `thome` semantics** (`L2040`): changing the home of a shelf record also **moves** it (`place(r,to)`), while for a bagged record it only sets home. Surprising for "Home spot" edits. | 1 | 1 | Separate "Move" from "Set home"; the toast says which happened. |
| 24 | **Gig "Back to plan"** (`gig-back L1922`) leaves packed records in the bag with `packed=true`; `gig-rm` of a packed item leaves the record in the bag. | 1 | 1 | Unpack or warn on back; disable remove for packed items. |

---

## 5. Database review (`app/db/001_init.sql`, `003_features.sql`, seeds `002`, `004`)

Reviewed by reading. Nothing was executed on Neon. Query-plan notes are reasoned, **unverified with EXPLAIN** (DATA_MODEL says its EXPLAINs ran against a 10-row seed, which says nothing about plans at scale). Run them on a branch (section 1h) with a generated 5k-record owner.

**Constraint gaps**
- `records.discogs_instance_id` (003 L55) has no uniqueness. Add `create unique index … on records(owner_id, discogs_instance_id) where discogs_instance_id is not null` (DATA_MODEL gap 2).
- `tracks (record_id, position)` is not unique (gap 3). `media_links.external_id` has no format check (YouTube is 11 chars `[\w-]`).
- `units.rows/cols` have no `check (rows between 1 and 26)`. `cell_code` (003 L105) uses `chr(65+r)`, which breaks past Z, and the prototype uses `AA…` (`rowLetter`). `kind` is nullable. `finish_hex` has no format check.
- `record_locations`: no check that the cell is inside the unit's grid, no "row and col both null or both set" rule, and **no owner consistency** (a record of owner A can point at a unit of owner B). Fix with composite FKs: add `owner_id` to `record_locations`, plus `unique(owner_id,id)` on units and records, and FK `(owner_id, unit_id) → units(owner_id,id)`. Or use a check trigger.
- `records.custom jsonb default '{}'`, but the prototype stores an ordered array of `{k,v}`. Pick the array.
- `gigs.status` enum (`planning/packed/out/returned`) ≠ prototype (`planning/packing/out/return/done`).
- `playlist_items.track_id` has no `on delete` (gap 8). There is no unique `(playlist_id, position)`, by design.
- `units.qr_token` is 8 hex chars of `md5(random())`: 32 bits, not cryptographic, global. If `/u/<token>` ever resolves without auth it is enumerable. Use `encode(gen_random_bytes(9),'base64')` (pgcrypto is installed) and keep auth on the route. Prototype stickers use `#K1-A2`, not the token, so decide which.

**Trigger side effects**
- `record_locations_track_prev` (003 L26) can't tell "caller explicitly set prev_* to NULL" from "unchanged NULL". So the gig-return query, which nulls prev, gets prev overwritten with the bag when prev was already null.
- **Unit deletion** sets `unit_id`/`home_unit_id`/`prev_unit_id` to NULL through FK actions. The FK action UPDATE fires `before update of unit_id`, so prev is set to the unit being deleted, and the FK on `prev_unit_id` may then reject the delete or leave a dangling id, depending on RI trigger order (**unverified, test on a branch**). The same update fires `enqueue_discogs_location` with `coalesce(v,'')`, which **queues a blank Discogs Location**.
- `enqueue_discogs_location` ignores the owner's sync setting (the prototype only queues when `discogsSync` is on). Every insert or move queues. Its value format (`K1·A2`, bare unit name) differs from the prototype (`K1·A2 (Acid)`, `Bag: Crater`).
- `create or replace function record_dup_key` with a changed body does **not** recompute the stored `dup_key`. Add a migration that runs `update records set artist=artist`, or drop and re-add the column, whenever it changes.

**RLS / owner scoping**
- No RLS anywhere. `owner_id text` exists only on units, records, playlists, gigs and barcode_lookups. Child tables (tracks, media_links, record_locations, location_events, playlist_items, bag_scans, cell_labels, discogs_sync_queue, gig_items, plays, sticker_prints) have no owner, so every route must join to a parent. That's fine if the API is disciplined. For RLS, add `owner_id` to the hot children or write `exists(...)` policies. Seed rows use `owner_id='demo'` in what will become prod.

**Indexes**
- FK columns without an index (cascade and set-null deletes seq-scan them): `record_locations(home_unit_id)`, `(prev_unit_id)`; `playlist_items(record_id)`; `media_links(track_id)`; `gigs(bag_unit_id)`; `plays(gig_id)`; `bag_scans(unit_id)`; `sticker_prints(unit_id)`; `discogs_sync_queue(record_id)` (only pending rows are indexed).
- `records_owner_idx` is redundant with the three `(owner_id, …)` indexes from 003.

**Migration ordering and idempotency**
- Order 001 → 002 → 003 → 004 works. 003's prev backfill (L19) needs 002's data. Every statement uses `if not exists` or drop-then-create. Re-running 003 drops and re-adds `location_events_reason_check` (ACCESS EXCLUSIVE lock plus full validation each time). Adding `dup_key` (stored generated) and `qr_token` (volatile default) rewrites the table: OK now, slow later.
- There is no migration ledger. Add `schema_migrations(version, checksum, applied_at)` and `scripts/migrate.mjs` (ARCHITECTURE section 6).

**Documented example queries (DATA_MODEL)**
- Q1 find: the trigram GIN helps only for terms of 3 or more characters; `owner_id` isn't in the GIN, so it rechecks rows of all owners. It covers artist and title only (the prototype search also covers label, catno, tags, notes and cubby names). Suggest a generated `search_text` plus `gin (owner_id, search_text gin_trgm_ops)` via `btree_gin`.
- Q2 move: sets home for **any non-`bag` kind**, so a crate would become a home. The prototype only sets home on shelves. Use `t.kind = 'shelf'`. There is no cell bounds check.
- Q3 bag reconcile: `to_home` includes records with `home_unit_id IS NULL`, so `unit_id` becomes NULL and the **record becomes unplaced**. The prototype keeps homeless records in the bag (X2). Add `and home_unit_id is not null`.
- Q4 reorder: `count(*)` equality plus "all exist" accepts a list with one id duplicated and another missing, which yields duplicate positions. Use `count(distinct item_id) = count(*) = (select count(*) …)`. The 409 requires the API to check the affected row count.
- Gig return: `coalesce(prev, home)` NULL for both → unplaced (same fix as Q3).
- "Not played in a year": the `records_last_played` view aggregates **all owners' plays** before the join. Use `left join lateral (select max(played_at), count(*) from plays p where p.record_id=r.id) lp on true`, which uses `plays_record_idx`.

---

## 6. Swarm work packages

Rules: one branch per package (`wp/<slug>`). `crates.html` is shared, so each package owns the **sections** listed and only appends its own test functions at the end of `tests/test_crates.py`, in its own `TESTS += [...]` block, with IDs from section 2.2. Re-run the full suite (section 1b) before the PR. 45/45 is today's baseline. Nothing may go red, and new tests that expose a not-yet-fixed bug must be marked `xfail` in their name (e.g. `E-2 (xfail)`) until the owning package lands.

| WP | Title | Scope and sections (crates.html) | Acceptance criteria | Tests to add | Avoid conflicts with |
|---|---|---|---|---|---|
| 1 | **State load/save hardening** | State block `L747-763` (`S` load, `migrate`, `save`), `seed`, `seedExtras` | Audit #1-5 fixed: total migrate, no reseed on unknown preset/version, backup on failure, debounced save with a `pagehide` flush, quota banner | E-1, E-2, E-3, E-10 | WP6 (don't touch `render()` beyond removing the `save()` call; expose `scheduleSave()`) |
| 2 | **Unit lifecycle and referential integrity** | `bindDraftForm` unit creation, `del-unit`/`del-unit-yes`, `cubbyMove`/`cubbySwap` preconditions, `place()` guard, gig bag guard, `gig-back`/`gig-rm` rules | X9, X10 stay green; P4 (gig bag deleted, then pack) can't happen; `makeUnit()` used by all creators; mutations validate before mutating | E-5, T-G2 plus unit-delete-with-gig test | WP1 (migrate also adds `labels`; coordinate the default list), WP9 (`place` callers) |
| 3 | **Boot resilience and global error surface** | Boot lines `L2088-2090`, `routeHash` row parse, a dev-only `window.onerror`/`unhandledrejection` toast, `assertState()` (dev) | Any single boot step can throw without blanking the app; strict deep-link parse; dev assertions from section 3.1 run after every action in tests | E-4, plus a test that `assertState()` passes after every test (hook in `App.close`) | WP1 (state block: call `assertState` only, don't edit load/save), WP5 (boot line sets `P.queue`) |
| 4 | **Async I/O robustness** | `runScanAI`, `identifyShelf`, `scanBarcodePhoto`, `loadZXing`, `shrink`, `saveStickers`, `svgToPng`, `exportCSV` (I/O part only), AI error map | Audit #7, #13-16 fixed: timeouts, stale-sheet guards, ZXing retry plus SRI, file type and size limits | E-7, E-8, T-U1, T-U2, T-U3; AI stubs via `window.claude` injected with `add_init_script` | WP8 (CSV escaping lives in `csvCell`, owned by WP8) |
| 5 | **Player robustness (port-ready state machine)** | PLAYER block `L1671-1834`: `loadYT`, `playAt`, `loadCandidate`, `onYTState`, `failCandidate`, `toggle`, `tick`, `reset-yes` timer cleanup | Error-code classes, dead-list guard, teaser video-id check, interval cleanup; follows PLAYER section 5 | **Fake `YT.Player` stub** (route `iframe_api` → fulfill stub JS), T-P1-T-P7 | WP3 (boot), WP7 (NP sheet markup) |
| 6 | **Render performance and indexes** | Helpers `L646-669` (add maps), `cover`, `qrPath`/`renderStickers` page count, `digView` partial render, `.list`/`.pick` windowing | 2k records: `dig` < 50 ms, `render` < 120 ms; no duplicate DOM ids; QR computed once per URL+size | T-T5, perf probe (P7) as a test with thresholds; duplicate-id check in 01 | WP1 (save), WP9 (table rendering is WP9's); keep function signatures |
| 7 | **Accessibility and layout** | `openSheet`/`closeSheet`, NP tabs, section tabs, stars, drag handle keys, CSS tokens for pill and toast contrast, N13/X13/X14 CSS | Focus trap and restore; labelled dialogs; `aria-current`/`aria-selected`; contrast ≥ 4.5:1; N13, X13, X14 stay green | T-L4; axe-core run (inject `axe.min.js` from the scratch dir) with 0 serious violations | WP6 (template strings: change attributes only), WP8 |
| 8 | **Escaping and input validation** | Every template interpolation (attribute values), `csvCell`, color and photo validators, YT id validator | No unescaped `${…}` in attributes (grep from REVIEW-NOTES returns only numerics); CSV formula-safe plus BOM | E-9, T-T4 | Everyone touching templates: land WP8 **early** or as one mechanical PR, then rebase the others |
| 9 | **Collection table** | COLLECTION TABLE section `L1965-2081` | Undo for cell edits; field allowlist plus numeric validation; partial row update instead of full `render()` on bag/home change; lazy home select; Move vs Set-home split | T-T1, T-T2, T-T3, plus a table rendering-time test | WP6, WP8 (`csvCell`) |
| 10 | **Test infrastructure** | `tests/test_crates.py` runner (`main`, `App`), `tests/build_harness.py` | `-k` regex and exact selection; `results.partial.json` for filtered runs; `CRATES_OUT` env var for results and shots dir; coverage mode (`--cov`, CDP precise coverage) writing `tests/coverage.json`; `REPORT.md` generator | Self-test: runner selects exactly X1 with `-k '^X1 '` | All test-adding WPs: WP10 changes only the runner and helpers, never test bodies |
| 11 | **Uncovered-action test backlog** | Tests only | Every action in section 2.1 is invoked by at least one test (coverage ≥ 95% of actions) | T-L1, T-L2, T-L3, T-G1, T-G3, T-R1, T-R2, T-R3, T-S1, T-S2, T-S3 | Append-only; never edit app code (file bugs in `BUGS.md` instead) |
| 12 | **DB migration 005 and query fixes** | `app/db/005_constraints.sql` (new), `docs/DATA_MODEL.md` queries, `scripts/migrate.mjs` (new) | Section 5 items: instance-id unique, tracks unique, rows/cols checks, FK indexes, owner-consistent FKs, trigger fixes (sync setting, unit-delete path), Q2/Q3/Q4/gig-return/not-played fixes; idempotent on a second run; EXPLAIN on a 5k-row branch pasted into DATA_MODEL | SQL tests on a Neon branch: delete a unit with located records; bag scan with a homeless record; reorder with a duplicate id → 0 rows | None in `crates.html`; coordinate the enum names (gig status, kinds) with WP2 |

**Suggested order**: WP10 and WP8 first (infrastructure and the mechanical escaping pass), then WP1, WP2, WP3, WP12 in parallel, then WP4, WP5, WP6, WP7, WP9, WP11.

# Review notes: raw data behind QA.md

These are raw notes from the 2026-10-20 review, kept for reproducibility. They are not a spec. `QA.md` is the curated version.

## Snapshots and runs

| crates.html md5 | test_crates.py md5 | Result (CRATES_NO_PATCH=1, scratch copy) |
|---|---|---|
| (pre-table, 13:31) | 23-test version | 36/41 (N12, N13, X9, X10, X12 FAIL) |
| `8fd65fcd209183c498033ed1f64318ee` | `6383f318b1bafd46c509004bf0ebd282` | 37/45 (N12, N13, X9-X14 FAIL; X11 flaky) |
| `ca157a850f9379c3ce876c2bf501e749` | `6383f318b1bafd46c509004bf0ebd282` | **45/45** |

The runs were done on scratch copies so other agents' `tests/results.json`, `harness.html` and `shots/` were not clobbered (`QA.md` section 1d). The syntax check (`node --check`, both inline scripts) passes, `logos/*.svg` parse, and `vercel.json` is valid JSON.

## Probe results (Playwright, unpatched page, external requests aborted)

The probe script is not committed. Each probe is a few lines of `page.evaluate` against the global `S`, `V`, `A` and helpers.

```
P1 corrupt state  {v:2}                → 0 unit cards, player hidden, "Cannot read properties of undefined (reading 'every')"
P1 corrupt state  no settings          → 0 unit cards, "…(reading 'discogsSync')"           (migrate)
P1 corrupt state  record without yt    → renders, 2 errors "…(reading 'length')"           (stOf at boot)
P1 corrupt state  record without tags  → 0 unit cards, "…(reading 'length')"
P1 corrupt state  not JSON             → reseeded, no error (handled)
P1 corrupt state  no recent            → Move sheet never opens, "…(reading 'filter')"
P2 unknown preset key on K1            → reload gives 10 records; my added record GONE (silent reseed)
P3 '#%E0%A4%A' at boot / at runtime    → URIError on 8fd65fcd; fixed on ca157a85 (no error)
P3c '#K1-Z9'                           → unit K1, cell 'all' (OK)
P4 gig bag B2 deleted, then tick pack  → r1.loc.u = 'B2' (missing unit); room shows 9 of 10 records
P5 S.records=[] then open-add          → TypeError in cover() (reading 'pal'); play-all and stale-list OK
P6 stale filter + 8× ArrowRight        → V.dig clamps to 3 of 4 (OK, two sources of truth but no visible bug)
P7 2,007 records in K1, cell=all       → render 191-235 ms, dig 159-299 ms, search 5-7 ms, room 17-24 ms,
                                         save 12-16 ms, localStorage 1,028 KB, 2,007 list rows
P8 focus                               → focus enters the sheet; Tab leaves it (no trap); after Esc focus is on a
                                         background list button (not the opener); .sheet has no aria-label(ledby)
P9 setItem throws QuotaExceededError   → toast "Moved to K1·B3", no warning (silent loss)
P10 duplicate DOM ids at boot          → 3 id values used more than once (cover gradient ids `sh<recordId>`)
```

## Coverage method

The suite was run with a wrapper that monkeypatches `App.__init__`/`App.close` in `test_crates.py` to open a CDP session, call `Profiler.startPreciseCoverage({callCount:true, detailed:false})` after the page loads, and on close sum `Profiler.takePreciseCoverage` call counts by `functionName` for the `harness.html` script. Object-literal arrow functions are named by their key (`'go-room'`), so action keys map directly.

Limitations:
- Boot-time calls before coverage starts are not counted. That only matters for functions called solely at boot; none were.
- Tests that `goto()` again (N12, X12) lose the pre-navigation counts.
- `A['pk-done'] = …` closures get a different inferred name, so `pk-done` shows 0 even though test 11 clicks it.

Results on `ca157a85`: 121 action keys, 86 called. 164 top-level functions, 150 called. The lists are in QA.md section 2.1.

## Contrast ratios computed (WCAG relative luminance, tint blended over the surface)

```
light .pill.out  #B26F05 on 20% tint  3.19     light .pill.in  #17894B on 18% tint  3.53
light .pill.own  #B26F05 on 18% tint  3.27     light .stale on --bg               3.39
toast Undo (dark theme, ink bg #E8EBED): red 3.87, brass 2.70, cyan 2.31
add button: red/white 4.63, brass/dark 5.73, cyan/dark 6.85      dark pills 5.5+ (OK)
```

## Grep used for unescaped attribute interpolation

```bash
grep -noP '(src|href|style|data-[a-z]+|id|value|aria-label|title)="[^"]*?\$\{(?!esc\()[^}]{1,50}\}' crates.html \
  | awk -F: '$1>466' | grep -vE '\$\{(i|k|n|x|z|S96|W|H|s|d|q0|pad|mod)\}'
```

On `8fd65fcd` this returned about 90 hits. Nearly all are ids, numbers or colors from state. The ones worth fixing are listed in QA.md section 4 #19.

## Things checked and found fine

- Document-level listeners are registered once at top level. There is no per-render accumulation: `bindNPSwipe` adds 2 listeners to a freshly created `#np-sheet` each time it opens, and the old node is discarded.
- The harness TDZ patch is a no-op on the current source (the state block comes after the helpers).
- `zxingLoading` is reset on timeout as of `ca157a85`.
- Vercel analytics scripts injected by `scripts/build.mjs` are same-origin `/_vercel/*`, which the CSP allows (`script-src 'self'`, `connect-src 'self'`). The `vercel.json` rewrite does not touch them (the path contains a dot). It **does** rewrite `/api/*` to `index.html`.

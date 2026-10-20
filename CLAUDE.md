# CLAUDE.md

Rules and context for Claude (and every agent in a swarm) working in this repo. Read this first, then `QA.md` for the test catalog and work packages.

## What this is

Crates is a DJ vinyl librarian: it maps every record to a physical spot (furniture unit + cubby, crate or bag), plays records through YouTube, and keeps your own data next to Discogs data.

- **Owner:** Carlos "Los" Franzetti (GitHub `CarlosFranzetti`).
- **Today:** a single-file prototype, `crates.html`. It is HTML, CSS and vanilla JS with no framework and no build step beyond wrapping.
- **Next:** the real app is Vite + React + TypeScript + Tailwind + shadcn/ui, Vercel functions and Neon Postgres. That matches the sibling repo `CarlosFranzetti/discogs-stream`, whose player and fallback chain we port (see `docs/PLAYER.md`).

## Repo map

| Path | What it is |
|---|---|
| `crates.html` | The prototype. Page content only: no `<html>/<head>/<body>`, because the claude.ai artifact host and `scripts/build.mjs` wrap it. |
| `scripts/build.mjs` | Wraps `crates.html` into `dist/index.html` and copies `logos/`. Vercel runs this. |
| `vercel.json` | Static deploy config: build, output `dist`, rewrites, CSP, Permissions-Policy (`camera=(self)`). |
| `app/db/001…004*.sql` | Neon schema and seeds, applied in order. 003 adds gigs, plays, cell labels, the sync queue and QR tokens. |
| `research/` | Furniture and bag preset research (`*.json`, `*.md`). `build_presets.py` rewrites the `/*PRESETS_START*/…/*PRESETS_END*/` block in `crates.html`. |
| `logos/` | Logo concepts. **The chosen logo is concept 3** (`crates-logo-{light,dark}.svg`, `crates-mark-{light,dark}.svg`). |
| `tests/` | Playwright suite (`test_crates.py`), harness builder; run screenshots land in `tests/shots/` (gitignored). |
| `docs/screenshots/` | README screenshots (copied from `tests/shots/readme-*`). |
| `docs/` | Engineering docs: ARCHITECTURE, DATA_MODEL, PLAYER, ROADMAP, INFRA. |
| `PRD.md`, `HOWTO.md`, `LIST.md`, `FUTURE.md`, `BUGS.md`, `QA.md` | Product requirements, user and dev guide, the full feature checklist, ideas, known bugs, QA catalog and review. |

## Commands

```bash
# build the deployable page
node scripts/build.mjs                 # -> dist/index.html

# serve locally
npx serve dist                         # or: python3 -m http.server -d dist

# tests (Playwright + system Chrome at /opt/google/chrome/chrome, or set the path in test_crates.py)
pip install --break-system-packages playwright
CRATES_NO_PATCH=1 python3 tests/test_crates.py      # writes tests/results.json, tests/shots/

# syntax-check every inline <script>
python3 -c "import re,sys;[open(f'/tmp/c{i}.js','w').write(m) for i,m in enumerate(re.findall(r'<script>(.*?)</script>',open('crates.html').read(),re.S))]" && for f in /tmp/c*.js; do node --check $f || exit 1; done

# regenerate presets after editing research/*.json
python3 research/build_presets.py
```

Always run tests with `CRATES_NO_PATCH=1`. Without it the harness rewrites the boot order, which once hid a real crash.

## How the prototype is organised (`crates.html`)

The code is in this order. Keep it that way, because top-level `const` helpers must exist before the state block runs (a TDZ crash happened when they didn't):

1. CSS: tokens on `:root`, dark overrides via `prefers-color-scheme` plus `[data-theme]`, then component sections.
2. Markup shell: top bar, `#main`, `#player`, `#yt-host`, `#layer` (sheets), `#np` (slide-up player), `#print-sheet`.
3. Inlined `qrcode-generator` (MIT). Don't swap it for a CDN; it must work offline and in tests.
4. Presets: `BASE_*` fallbacks, then the generated `RESEARCH` block. Don't hand-edit inside the markers.
5. Seed data (`seed`, `seedExtras`, `migrate`), helpers, drawing (`drawShelf`, `drawBag`, `drawCrate`), then the **state block** (`S`, `V`, `save`), then render functions.
6. Feature modules: moving (`place`, `snap`, `moveRecord`), bag scan, add flows, edit, playlists, settings, then the features block (dupes, barcode, Discogs sync, plays, cubby moves, gigs, QR, deep links).
7. Player port: `P`, `loadYT`, the fallback chain, `renderPlayer`, `renderNP`.
8. Actions: one `const A = {…}` map plus `Object.assign(A, {…})`. A single delegated click listener dispatches `data-act`.

Conventions:
- **Moving records:** always call `place(r, to, opts)`. It sets `from` (came-from) when entering a bag or crate, sets `home` when landing on a shelf (unless `{setHome:false}`), and enqueues the Discogs Location sync. Take an undo snapshot first with `lastUndo = snap(records, extraRestore)`. Never assign `r.loc` directly.
- **Addresses:** a cell key is `"row-col"`, zero-based. Display it as row letter + column number (`A1`). The full code is `UNIT·A1`, e.g. `K1·B2`. Cubby subtitles live in `unit.labels[cellKey]`.
- **Rendering:** `render()` rebuilds `#main` from state and saves to localStorage. Sheets use `openSheet(html)` / `closeSheet()`. If you re-render from inside a `change` or `blur` handler, defer it with `setTimeout(…,0)`, or the DOM node gets removed mid-event.
- **Escaping:** every interpolated user string goes through `esc()`. No exceptions.
- **No `alert`/`confirm`/`prompt`.** Confirmations are in-page (`*-confirm` containers).
- **Copy:** sentence case. A button says exactly what happens and the toast mirrors it ("Move…" → "Moved to K1·B3"). Simulated features must say they're simulated (barcode candidates, Discogs sync).
- **Colors:** tokens only. Both themes must work, and there must be no horizontal scroll at 390px (test 14 checks this).

## Data and secrets

- Neon project `crates` (id `super-sea-94522798`, us-east-2, PG17), branch `main`, database `crates`. Test migrations on a **Neon branch**, never on `main` first.
- `DATABASE_URL`, the Discogs token and any API keys are server-only. Never commit them, never print them, never give them a `VITE_` prefix.
- Discogs API terms: attribution, data no more than 6 hours stale, and images are restricted data (`research/features.md`). Don't mirror Discogs images.

## Git and deploy

- Work on a branch per work package (`wp/<short-name>`), open a PR to `main`, keep commits focused.
- End commit messages with the session's Co-Authored-By trailer when one is provided.
- Before pushing: syntax check, full test suite green, and no new console errors.
- Vercel: the repo deploys as a static site via `vercel.json`. The Vercel connector in Claude sessions can't create projects, so the project has to be created or linked in the Vercel dashboard.
- The claude.ai preview of the prototype is published separately from `crates.html` and is updated by the lead session.

## Swarm etiquette

- Pick one work package from `QA.md` section 6 and stay inside its listed files.
- `crates.html` is one file, so coordinate by section. Don't reformat or reorder code outside your package's section.
- Add or adjust tests in `tests/test_crates.py` for every behavior change, and update `BUGS.md` when you fix or find a bug.
- If something in the docs disagrees with the code, the code wins. Fix the doc in the same PR.

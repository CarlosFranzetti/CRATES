# Crates: Roadmap and Test Strategy

Last updated 2026-10-20. Each phase ends with something the owner can use. Exit criteria are testable.

## Phase 0: Prototype (done)

- `crates.html`: single-file clickable prototype (about 77 KB) with presets, room view, unit and cell flipping, search, move, a catalog flow, seeded demo records.
- `app/db/001_init.sql` and `002_seed.sql` applied to Neon project `crates`; seed lookup verified ([INFRA.md](INFRA.md)).
- 2026-10-20: live at https://crates-livid.vercel.app/ (Vercel project `crates`, linked to GitHub `main`). Map and Columns layouts, phone tab bar and sheet, density, full-height Collection, YouTube prefetch, 4-slot backups, file save/load, Discogs CSV import. `app/db/005_stream_parity.sql` written (apply on a Neon branch first).

## Phase 1: Real app skeleton on Neon

Scope
- Vite + React + TS + Tailwind + shadcn app in `app/`, ported tokens (vinyl, groove, theme classes) from discogs-stream.
- `app/api` with the Neon driver, auth middleware (JWT verify, owner scoping), Zod schemas in `app/shared`.
- Units CRUD and presets; room view; unit/cell flip view; search; single-record move with undo (queries 1 and 2 of [DATA_MODEL.md](DATA_MODEL.md)); addressing helpers (`K2·B2` format and parse).
- Migration runner; schema fixes from the DATA_MODEL gaps list that block later phases (`tracks` uniqueness, `discogs_instance_id`, cell order).
- Vercel project, `DATABASE_URL`, preview deploys with a Neon branch per PR.

Exit
- Owner signs in on a phone, sees the seeded demo collection under their own id, finds a record, moves it in two taps, undoes it.
- No secret in the client bundle (CI check passes).

## Phase 2: Capture and Discogs

Scope
- Camera capture, client resize, Blob upload.
- `/api/identify`: vision pass, Discogs confirm, candidate review UI; shelf-by-shelf capture ([ARCHITECTURE.md](ARCHITECTURE.md) section 2).
- Record creation: snapshot, display columns, tracks, `media_links` from Discogs `videos`.
- Bag scan: propose, review, atomic apply (query 3).
- Optional: import an existing Discogs collection to seed records.

Exit
- Photographing one full Kallax cell yields at least 90% correct matches on the eval set, with confirm UI for the rest.
- A 40-record bag scan applies in one transaction; going-in and returning-home lists match the expected sets.

Risks: vision accuracy on spines (mitigate with cover shots and manual search); Discogs rate limits (throttle, cache); photo privacy.

## Phase 3: Player port

Scope (spec in [PLAYER.md](PLAYER.md))
- IFrame wrapper, queue, slide-up shell, spinning vinyl.
- Fallback state machine: 3s window, alternate, one forced re-search, skip; teaser guard; dead-list guard.
- `/api/media/resolve`, `/api/media/:id/report`, verifier queue with prefetch of 4, Vercel Cron link check.
- Quota row with Open in YouTube; daily reset of the flag.
- Fix the documented hazards rather than porting them.

Exit
- All fault-injection tests pass (below). On the seeded 10 records, at least 80% of tracks play without a skip on a real device, and failures dim and retry.

## Phase 4: Playlists and edits

Scope
- Playlist CRUD, duplicate, drag reorder (query 4), add from shelf, bag and search, whole-record expansion.
- Large-font playlist view, filters, runtime.
- Edit screen for owner fields and custom fields; `edited_fields`; reset to Discogs; re-sync that respects edits.

Exit
- Reorder survives reload and a stale-client 409 recovers cleanly. Re-sync leaves edited fields untouched in a test with a changed Discogs snapshot.

## Phase 5: Polish and deploy

- Visual pass: motion, empty states, loading skeletons, dark theme, `prefers-reduced-motion`.
- Accessibility: focus order, labels, 44px targets, screen-reader names for cells ("Kallax 2, row B, column 2").
- Performance: list virtualisation above about 300 rows, image sizing, Lighthouse mobile budget.
- Media Session lock-screen controls (optional), PWA install, error tracking.
- Production deploy, custom domain, backups (Neon branch snapshot schedule), remove `demo` seed.

## Test strategy

| Level | Tool | What it covers |
|---|---|---|
| Unit | Vitest (as discogs-stream: Vitest 4, jsdom) | Addressing format/parse (`K2·B2`, 0-based to letter/number, bounds); edited-field merge; bag diff computation; queue and skip logic |
| Player state machine | Vitest, fake timers, fake `YT.Player` | See fault injection below |
| SQL | Vitest against a throwaway Neon branch | DATA_MODEL queries 1-4 with fixtures: move rules (shelf sets home, bag does not), reconcile (in, out, no-home, foreign bag), reorder (stale client updates zero rows), events written |
| API | Vitest + `vercel dev` | Auth required, owner scoping (user A cannot read or write user B), Zod validation, 409 paths |
| Component | Testing Library | Flip view, move sheet, playlist drag with keyboard, dimmed rows and retry |
| E2E | Playwright, mobile viewport, fake camera stream | Capture to confirm to search to move to bag scan to play, against a preview deployment |
| Vision eval | Script + labeled photo set | Precision and recall of identify (fixed set of about 30 photos: shelf cells, bags, bad light); tracks cost per image; run on prompt or model change |
| Security | CI grep + manual | No server secret names or `neon(` in `app/src`; CSP loads YouTube frames and camera works |

**Player fault injection** (each is a named test):
1. Link-less track, resolve takes 2s: plays, timer cleared. Takes 5s, player idle: marked non_working and skipped at 3s.
2. Link-less track while the player reports state 1 or 3 on the **expected** video id: not skipped at 3s.
3. Error 150 on a track with a rank-1 link: swaps once. Second 150: one forced re-search with `exclude`. Third: non_working and skip.
4. Errors 100, 2, 5: skip immediately, no recovery attempts.
5. `duration` 12s against unknown or 240s expected: recovery path; against a 20s expected: left alone. Stale duration from the previous video is ignored.
6. All tracks non_working: stops after one lap with "nothing playable".
7. Search returns `quota_exceeded` (as HTTP 200 body, as 429, as message text): flag set, banner shown, nothing cached as unavailable, flag resets next day.
8. Prefetch requests the next 4 only, in batches of 3, and never writes non_working to the database from a miss.
9. Dependency change mid-resolve does not cancel the window (regression for hazard 2).

**Definition of done for every phase:** types check, lint clean, tests above for the phase green in CI, a preview deployment the owner can open on a phone.

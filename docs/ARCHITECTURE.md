# Crates: Architecture

Proposed stack and boundaries. Nothing here is built yet beyond the database (see [INFRA.md](INFRA.md)) and the single-file prototype `crates.html`. Last updated 2026-10-20.

## 1. Stack

| Layer | Choice | Why |
|---|---|---|
| UI | Vite 7 + React 18 + TypeScript + Tailwind 3 + shadcn/ui | Matches discogs-stream (`package.json`: vite ^7.3.1, react ^18.3.1, tailwindcss ^3.4.17), so the player, tokens and sheet components port directly |
| Routing / data | React Router 6, TanStack Query 5, Zod | Already used in discogs-stream; Zod shares request schemas with the API |
| Drag and drop | `@dnd-kit/sortable` | New dependency, for playlist reorder |
| API | Vercel Functions in `app/api/*.ts` (Node runtime by default) | Same host as the SPA; keeps secrets server-side |
| Database | Neon Postgres via `@neondatabase/serverless` | Schema exists (`app/db/001_init.sql`) |
| Auth | Neon Auth (JWT, verified in each route) or similar | Single owner in v1; `owner_id` = auth user id |
| Photos | Vercel Blob (private, signed URLs); alternative: Neon storage | `units.photo_url`, `bag_scans.photo_url` need object storage |
| Vision | Claude vision (model id from env) | Identify records from a photo |
| Catalog | Discogs REST API (token) | Confirm and fetch the canonical release |
| Playback | YouTube IFrame API, ported from discogs-stream | See [PLAYER.md](PLAYER.md) |

Proposed layout: `app/src/` (SPA), `app/api/` (functions), `app/db/` (migrations, exists), `app/shared/` (Zod schemas, addressing helpers, used by both sides).

### Database access

- `neon()` (HTTP) for single statements. Every example in [DATA_MODEL.md](DATA_MODEL.md) is one statement, so each is atomic with no interactive transaction.
- For multi-step work that must read then write (Discogs re-sync), use `Pool` over WebSockets in a Node-runtime route, or `sql.transaction([...])` for a fixed batch. Check the current driver docs when wiring this up.
- Use the pooled connection string. Parameterised queries only (tagged template or `$n`); never interpolate user text. Column names for edits come from an allowlist.

## 2. Capture and identification pipeline

```
camera -> client resize (long edge 1600px, JPEG q0.8) -> POST /api/uploads (Blob) -> photo_url
photo_url -> POST /api/identify { unit_id, cell?, photo_url }
   1. Vision pass: structured JSON [{artist, title, catno?, label?, confidence}]
   2. For each candidate: Discogs search (catno first, then artist + title)
   3. Return top 3 matches per candidate with cover, year, label, country
user confirms (pre-checked when confidence >= 0.85 AND an exact Discogs match)
-> POST /api/records { discogs_release_id, unit_id, row, col }
   server: GET /releases/{id} -> discogs_snapshot, display columns, tracks,
           media_links from snapshot.videos (quota-free), record_locations
           (current = home = slot), location_events 'add'
```

- **No silent writes.** Nothing is saved without a user confirm in v1.
- Vision output is **untrusted** (text on sleeves can carry instructions). Parse it against a Zod schema, use it only as search input, never as a tool call, URL fetch or SQL.
- Furniture capture (step 1 of the product) needs no vision: the photo is the cover; the preset supplies rows and columns.
- Bag scan: `POST /api/bag-scans` stores the photo, runs the same vision plus Discogs match restricted to the owner's own records (match against `records`, not the whole of Discogs), and returns a proposed `found` list. Apply is a separate call (the reconcile query in DATA_MODEL.md).
- Discogs: send a `User-Agent`, use a personal access token, throttle to about 1 request/second (discogs-stream's scraper does the same). Discogs documents 60 requests/minute authenticated and 25 unauthenticated; confirm at build time.
- Fallback when vision is down or low-confidence: manual search box that hits `/api/discogs/search`.

## 3. API routes

All routes require `Authorization: Bearer <JWT>` and scope every query to the caller's `owner_id`. Errors: 400 validation, 401, 404 (also for other owners' ids), 409 stale client.

| Route | Purpose |
|---|---|
| `GET /api/presets` | Furniture presets: Kallax sizes and finishes, other shelving, milk crates (color), boxes, DJ bags (UDG, Magma, ...) with per-bag colors |
| `GET /api/units`, `POST /api/units` | List and create units (assigns the next code, e.g. `K3`) |
| `PATCH /api/units/:id`, `DELETE /api/units/:id` | Rename, finish, photo; delete refuses if records are located there |
| `POST /api/uploads` | Signed upload for photos |
| `GET /api/units/:id/records?cell=B2` | Records in a unit; `cell` omitted = All |
| `POST /api/identify` | Photo to candidate matches |
| `POST /api/records` | Confirm a candidate; create record, tracks, links, location |
| `GET /api/records?q=` | Search; returns `place` ("K2·B2", "bag Crater") and `is_away` |
| `GET/PATCH/DELETE /api/records/:id` | Read, edit fields (updates `edited_fields`), delete |
| `POST /api/records/:id/resync` | Re-fetch Discogs, respect `edited_fields` |
| `POST /api/records/:id/move` | `{ unit_id, row, col }`; writes event; returns event id for undo |
| `POST /api/moves/:eventId/undo` | Reverse an event |
| `POST /api/bag-scans`, `POST /api/bag-scans/:id/apply` | Propose, then apply a reconcile |
| `GET /api/records/:id/media` | Links ordered by rank |
| `POST /api/media/resolve` | Server search chain; accepts `{ record_id, track_id?, force?, exclude[] }` |
| `POST /api/media/:id/report` | Client reports `working` / `non_working` after playback |
| `GET/POST /api/playlists`, `PATCH/DELETE /api/playlists/:id` | List, create, rename, delete |
| `POST /api/playlists/:id/duplicate` | Copy with items |
| `PUT /api/playlists/:id/order` | Full ordered item-id list (DATA_MODEL query 4) |
| `POST /api/playlists/:id/items`, `DELETE /api/playlists/:id/items/:itemId` | Add (record or track), remove |
| `GET /api/cron/verify-links` | Vercel Cron: re-check stale `media_links` (replaces discogs-stream's `youtube-rescan-weekly`) |

Media resolve runs the discogs-stream tier order: stored links, Discogs `videos`, quota-free search (results-page scrape, Invidious, Piped), official API last. Port from `supabase/functions/youtube-search/index.ts` (640 lines; the scoring, the under-60s filter and the embeddability probe are worth keeping). It returns up to `maxResults` ranked candidates and the route stores them as `media_links` ranks 0..n, where discogs-stream kept only two.

## 4. Environment variables (names only)

Names are provisional until Neon Auth and Blob are provisioned.

| Name | Scope | Used for |
|---|---|---|
| `DATABASE_URL` | server only | Neon pooled connection |
| `NEON_AUTH_JWKS_URL` | server only | Verify JWTs |
| `VITE_NEON_AUTH_URL` | client (public) | Auth endpoint for sign-in |
| `OWNER_USER_ID` | server only | Optional allowlist for single-owner v1 |
| `DISCOGS_TOKEN` | server only | Discogs API |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_VISION_MODEL` | server only | Vision identification; model id is config, not code |
| `YOUTUBE_API_KEY` | server only | Official API tier and embeddability probe |
| `BLOB_READ_WRITE_TOKEN` | server only | Photo storage |
| `CRON_SECRET` | server only | Authorise the cron route |

Rule: anything prefixed `VITE_` is compiled into the public bundle. No secret ever gets that prefix.

## 5. Security notes

- **`DATABASE_URL` never reaches the client.** Only `app/api/*` imports the Neon driver. The browser talks to `/api/*` and nothing else. Add a CI grep that fails the build if `DATABASE_URL`, `neon(` or the Anthropic/Discogs/YouTube key names appear under `app/src/`.
- **Authorisation is in the query.** Every statement filters on `owner_id` (or joins to a parent that does). Cross-owner ids return 404. Consider Postgres RLS as a second layer once `owner_id` maps to the auth id.
- **Photos can show the owner's home.** Store them private, serve signed short-lived URLs, cap uploads (10 MB, JPEG/PNG/WebP only), strip EXIF GPS on the client before upload.
- **Cost and abuse.** `/api/identify` and `/api/bag-scans` call a paid model. Require auth, rate-limit per user, cap images per request.
- **CSP.** Start from discogs-stream's `vercel.json` (allows `youtube-nocookie.com` frames and `s.ytimg.com`/`youtube.com` scripts, `i.discogs.com` images). Two changes are required: its `Permissions-Policy` sets `camera=()`, which would block capture, so use `camera=(self)`; and `connect-src` must allow the Blob host while dropping `*.supabase.co`. `vercel.json` rewrites must exclude `/api`.
- **Seed data** uses `owner_id = 'demo'`. Remove or isolate it before real auth ids exist.
- **External IDs** from Discogs and YouTube are validated (numeric release id; 11-character video id) before being stored or used in URLs.

## 6. Deployment

- Vercel project `crates`. As of `INFRA.md`, project creation returned 403 for the connected tooling, so the first deploy needs the project made in the dashboard or write scope granted.
- Preview deployments use a Neon branch per PR (copy-on-write), `DATABASE_URL` set per environment.
- Migrations are numbered SQL files applied in order and idempotent (`001`, `002` already are). Add a `migrate` script and run it in CI against the preview branch first.

# Crates — Infrastructure

_Last updated 2026-10-20. No secrets in this file; credentials are stored in Neon / Vercel._

## Neon (Postgres) — DONE

| Item | Value |
|---|---|
| Project | `crates` — id `super-sea-94522798` (already existed, created 2026-10-20 via console; reused) |
| Org | `Carlos` (`org-frosty-heart-10711045`, console-managed, free plan) |
| Region | `aws-us-east-2` |
| Postgres | 17.11 |
| Branch | `main` — `br-proud-mountain-b4v80224` (default, primary) |
| Database | `crates` (owner role = default; connection string stored in Neon) |
| Extensions | `pgcrypto`, `pg_trgm` |

Migrations (idempotent, run via `run_sql_transaction`):
- `app/db/001_init.sql` — schema, indexes, `records.updated_at` trigger
- `app/db/002_seed.sql` — demo owner `demo`

Tables and seeded row counts:

| Table | Rows | Notes |
|---|---|---|
| units | 2 | K1 Kallax 1 (shelf 2x4, White #F2F0EB); B1 "Crater" (bag, udg-ultimate-60, Black #1D1F22) |
| records | 10 | 808/acid/house classics; `discogs_*` ids left null (to be filled from Discogs) |
| tracks | 0 | |
| media_links | 29 | YouTube ids in rank order, status `pending` |
| record_locations | 10 | K1 A1: 5, K1 A2: 2, bag Crater: 3 (with home cubbies) |
| location_events | 10 | one `add` event per record |
| playlists | 1 | "Warm-up" |
| playlist_items | 4 | Can You Feel It, Pacific State, Voodoo Ray, Good Life |
| bag_scans | 0 | |

Indexes: `records(owner_id)`, GIN trigram on `lower(artist)` and `lower(title)`, `record_locations(unit_id, cell_row, cell_col)`, `playlist_items(playlist_id, position)`, `tracks(record_id)`, `media_links(record_id, rank)`, `location_events(record_id, at desc)`.

Cell convention: `cell_row` 0 = A, 1 = B; `cell_col` 0 = 1. Bags use (0,0).
Verified: lookup of "Voodoo Ray" returns `B1 "Crater"`, home `K1 A1`.

## Vercel — BLOCKED (permissions)

- Team: `carlosfranzetti` — `team_2sVeVCDGjXW2eMc1O6Qr78l5` (slug `carlosfranzettis-projects`)
- No `crates` project exists. `create_project` returned **403 forbidden**: the MCP connection can read (list projects/teams) but not create. No local Vercel CLI or token available as fallback.
- Vercel project id: **none yet**.

Deploy method (for a single static file) once write access exists — `mcp__Vercel__create_deployment`:

```json
{
  "teamId": "team_2sVeVCDGjXW2eMc1O6Qr78l5",
  "requestBody": {
    "name": "crates",
    "project": "crates",
    "target": "production",
    "files": [{ "file": "index.html", "data": "<html contents>", "encoding": "utf-8" }],
    "projectSettings": { "framework": null, "buildCommand": null, "installCommand": null, "outputDirectory": null }
  },
  "skipAutoDetectionConfirmation": "1"
}
```

`projectSettings` is required on a project's first deployment. Large files can instead go through `upload_file` (SHA1 digest), then be referenced as `{file, sha, size}`. Not tested, since testing would deploy.

Env var: `DATABASE_URL` (pooled Neon connection string, type `sensitive`, targets production + preview) via `create_project_env`. Not set yet.
Neon–Vercel link: a Vercel-managed Neon org exists (`Vercel: carlosfranzetti`, `org-cold-bread-57649439`), but `crates` lives in the console org, so it isn't auto-linked. Listing integrations also returned 403. Practical route: set `DATABASE_URL` manually with `create_project_env` once writes work.

## GitHub — NOT ATTEMPTED

Local `gh` token is invalid; no repo created. Local git repo at `/home/claude/crates` only.

## Open items

1. Grant the Vercel MCP connection write scope (or create the `crates` project in the dashboard), then deploy with the shape above.
2. Set `DATABASE_URL` on the Vercel project (sensitive).
3. Fix `gh` auth and create `CarlosFranzetti/crates`.
4. Backfill `discogs_release_id`/`cover_url`/tracks from Discogs; run the YouTube link health check to set `media_links.status`.
5. Seed uses `owner_id = 'demo'`; replace it with real auth user ids once auth exists.

## API (Vercel functions) — added 2026-10-21

- `api/_lib.js`, `api/sync.js`, `api/collection.js`, `api/img.js`. Node ESM, `@neondatabase/serverless`. `vercel.json` excludes `/api/` from the SPA rewrite and sets `maxDuration` 60 s for sync.
- Env vars (server only): `DISCOGS_TOKEN`, `DISCOGS_USERNAME`, `DATABASE_URL`. Optional later: `YOUTUBE_API_KEY`.
- Migrations `005_stream_parity.sql` and `006_sync.sql` applied to Neon `crates` on 2026-10-21 (branch `migrations-005-006` first, then `main`).
- Discogs terms: images are fetched through `/api/img` with the Crates User-Agent and CDN-cached for 6 hours; the database keeps urls and metadata, never image bytes; the listing is re-checked every 6 hours.

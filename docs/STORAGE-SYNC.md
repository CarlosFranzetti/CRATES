# Crates: photo storage, identify-from-photo, two-device sync, loan reminders

Status: design, written 2026-11-13. Prices and limits below were read from the cited pages on 2026-11-13; they change, so re-check before committing money. "(unverified)" means I could not confirm it from a primary source. This file changes no existing file; where it says an existing file needs a change, that is a recommendation for the build phase.

## 0. Decisions at a glance
| Topic | Pick | Runner-up | Steady-state cost |
|---|---|---|---|
| 1. Photo storage | Cloudflare R2, presigned direct uploads, client-made 1600px and 320px JPEGs | Vercel Blob (needs Pro past about 2,300 photos) | $0 (6,000 photos is about 2.6 GB, free tier is 10 GB) |
| 2. Identify | Claude Haiku 5.5 reads, escalate to Sonnet 5.5; own Discogs collection matched first; ZXing for barcodes | Google Vision OCR as a catno-only fallback | about $0.0004 per photo on Haiku |
| 3. Sync | Pairing by QR/code, device cookie, op log in Neon, foreground polling | Ably push on top of the same log | $0 |
| 4. Loans | In-app badge + daily Resend digest + `sms:` link built in the app | Web Push, then .ics | $0 |
| 5. Migration | `entities` + `ops` tables mirror the prototype state; import once; localStorage stays as cache | Normalise straight into `001_init.sql` tables | $0 |

Total: about $0 to $1 a month at 2,000 records, 6,000 photos, 2 devices, if the owner stays on Vercel Hobby, Neon Free and R2. One-off backlog identify run: about $2 to $10 (section 6).

Existing-code findings that matter here:
- `api/sync.js`, `api/collection.js`, `api/img.js` have no authentication. Anyone with the URL can read the collection or burn the Discogs budget. Phase 1 must put a device check in front of all three.
- `api/_lib.js` paces Discogs with a module-level `lastCall`. That variable is per function instance, so two concurrent instances (a sync plus an identify) can exceed 60 requests a minute. Section 2.4 replaces it with a budget in Postgres.
- `docs/ARCHITECTURE.md` proposes Neon Auth and Vercel Blob. This design replaces both for v1 (reasons in sections 1 and 3).

## 1. Photo storage
### 1.1 Sizing used throughout
One photo = 1600px long edge JPEG q0.82 (about 350 to 450 KB for a busy sleeve) plus a 320px thumb (about 15 to 30 KB). Assume 425 KB per photo, both files. That gives 0.85 GB at 2,000 photos, 2.55 GB at 6,000, 4.25 GB at 10,000. These are estimates; measure 50 real shots in Phase 1.

### 1.2 Comparison
| | Free tier | 2k photos | 6k photos | 10k photos | Direct phone upload | Per-file limit | Delete | Source |
|---|---|---|---|---|---|---|---|---|
| Cloudflare R2 | 10 GB-month, 1M writes, 10M reads, free egress | $0 | $0 | $0 | Presigned PUT (S3 API) | 5 GB per PUT, 5 TB multipart (unverified, standard S3 figures) | Free operation | https://developers.cloudflare.com/r2/pricing/ |
| Vercel Blob | Hobby 1 GB, 10 GB transfer, 2,000 advanced ops; over the cap Blob stops working for 30 days | $0 (just fits) | Pro $20 plan (usage about $0.12) | Pro $20 (usage about $0.2) | `upload()` client token via `handleUpload` | 5 TB | Free | https://vercel.com/docs/vercel-blob/usage-and-pricing |
| Supabase Storage | Free 1 GB, 50 MB per file, no image transformations | $0 | Pro $25 | Pro $25 | Signed upload URL (unverified detail) | 50 MB free | n/a | https://supabase.com/pricing |
| UploadThing | Free 2 GB; $10 a month for 100 GB | $0 | $10 | $10 | Yes, its own SDK and route | unverified | unverified | https://uploadthing.com/ |
| Neon bytea | Free 0.5 GB; Launch $0.35 per GB-month | $0.30 (Launch) | $0.89 | $1.49 | No: must pass through a function, 4.5 MB body cap | 4.5 MB per request | SQL delete | https://neon.com/pricing (rate from a third-party calculator, makerkit.dev) |

Vercel Blob usage rates on Pro: $0.023 per GB-month, $5 per million advanced operations, $0.05 per GB transfer. Blob's cheapness is real, but it only arrives after the $20 Pro plan, because Hobby caps storage at 1 GB (about 2,350 photos). Vercel's function body cap is 4.5 MB (https://vercel.com/docs/functions/limitations), so uploads must go direct to storage, never through a function.

### 1.3 Recommendation: R2, with a private bucket
- Why: 10 GB free covers about 23,000 photos, direct uploads are plain S3 presigned PUTs (one small dependency, `aws4fetch` or `@aws-sdk/s3-request-presigner`), egress is free, deletes are free.
- Cost of the choice: a second vendor and a one-time CORS rule on the bucket (allow PUT/GET from the app origin). R2 may require a payment method on file even inside the free tier (unverified).
- Privacy: bucket stays private. `GET /api/photo/:id?s=thumb|full` checks the device cookie and 302s to a presigned GET valid for 1 hour. This matches the ARCHITECTURE.md rule that photos of the owner's home are not public.
- Caching: the presigned URL changes, so the browser cannot cache by URL. A photo's bytes never change for a given id, so the client keeps thumbs in the Cache API keyed by `photo id + size` and treats them as immutable. 6,000 thumbs is about 150 MB, which is evictable cache, not storage of record.
- Runner-up, Vercel Blob: pick it if the owner would rather pay $20 a month for one vendor, or is already on Pro. Same design: `handleUpload` mints a client token (long-lived `BLOB_READ_WRITE_TOKEN` is required for that), private store, and a function that streams `get(pathname,{access:'private'})`. Docs: https://vercel.com/docs/vercel-blob/client-uploads and https://vercel.com/docs/vercel-blob/private-storage.
- Not recommended: Neon bytea (bloats the database that also holds the op log and every branch copy), UploadThing (third vendor for no gain), Supabase (only makes sense if the whole backend moves to Supabase, which would also bring Realtime and Auth; that is a bigger decision than photos).

### 1.4 Thumbnails: make them in the browser
The client already decodes the image to resize it, so a second canvas pass for the 320px thumb is free. Transform services cost money or lock-in: Supabase charges $5 per 1,000 origin images on Pro (https://supabase.com/pricing). Serving two pre-made files also needs no image CDN. Also store a 24px blur placeholder (`lqip`, a base64 JPEG of 400 to 700 bytes) in the database row so lists paint instantly.

### 1.5 Client pipeline
1. Capture. Two sources, same pipeline after this step: `getUserMedia` live viewfinder (section 3.5) and `<input type="file" accept="image/*">` for the photo library and desktop.
2. Decode and resize in one call, not via a full-size canvas: `createImageBitmap(file, { resizeWidth, resizeHeight, resizeQuality: 'high' })` computed from the source dimensions so the long edge is 1600. iOS limits canvas area (about 16.7 MP, from WebKit practice, unverified), and a 48 MP photo would fail on a naive `drawImage`.
3. Orientation. Modern browsers apply EXIF orientation when decoding (`imageOrientation: 'from-image'` is the default). Re-encoding through canvas bakes the rotation in and drops all EXIF, which also removes GPS, satisfying the ARCHITECTURE.md rule. Test with a portrait shot on a real iPhone; this is the usual place for sideways photos.
4. Encode JPEG with `canvas.toBlob(cb,'image/jpeg',0.82)` for the 1600px file and q0.70 for the 320px thumb. Do not use WebP: Safari canvas has historically not encoded WebP (unverified for current iOS), and JPEG is accepted by Claude (JPEG, PNG, GIF, WebP) and everything else.
5. HEIC. Safari generally hands pages a JPEG for library picks (reported, not in Apple docs; verify on the owner's phone). `getUserMedia` frames are never HEIC. The remaining case is a HEIC file dragged onto desktop Chrome or Firefox, which cannot decode it. Sniff the `ftyp` brand (`heic`, `heix`, `mif1`); if `createImageBitmap` throws, lazy-load a wasm decoder (`heic2any` or libheif) on desktop only, and otherwise show "Export as JPEG first".
6. Hash the 1600px blob (SHA-256, `crypto.subtle`) for dedupe and idempotent upload.
7. Write both blobs to IndexedDB `photo_outbox` with status `local`, then upload.
8. Upload: `POST /api/photos/sign` returns two presigned PUT URLs and creates the `photos` row as `pending`; client PUTs both files; `POST /api/photos/complete` HEADs the objects and flips the row to `ready`; client deletes the 1600px blob from the outbox, keeps the thumb in cache.

### 1.6 Local-first fallback and iOS storage
- WebKit (Safari 17+) gives an origin up to about 60% of disk for browsers and for sites saved to the Home Screen, and about 15% for in-app web views. Older Safari used a 1 GiB prompt. Source: https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria and https://webkit.org/blog/14403/updates-to-storage-policy/.
- The seven-day rule: script-writable storage (IndexedDB, Cache API) of a site in Safari is deleted after seven days of Safari use without interaction. Installed Home Screen web apps are exempt (same sources). So the capture phone must run the installed PWA, and the app should call `navigator.storage.persist()` and show a banner if it is running in a plain Safari tab.
- Rules: IndexedDB is a buffer, not the store of record. Never put image data in the prototype state `S` (localStorage is about 5 MB). Cap the outbox at 300 photos or 150 MB with a visible "Not uploaded yet: 12" chip; refuse new shots past the cap rather than fail silently.
- Local-only mode (claude.ai preview, no server): the same code path keeps photos in IndexedDB with status `local` and never leaves `local`. Thumbs are served from the blob store.

### 1.7 Table design
Photos belong to a subject by `(subject_kind, subject_id)` text, not foreign keys, because the prototype's record ids are not the `001_init.sql` uuids yet (section 5). Moving a photo to another release is one `update`.

```sql
create table photos (
  id           uuid primary key default gen_random_uuid(),
  owner_key    text not null,
  subject_kind text not null check (subject_kind in ('record','unit','capture','inbox')),
  subject_id   text,                                  -- record id / unit code / capture uuid; null in 'inbox'
  kind         text not null default 'other' check (kind in
               ('cover','back','label','insert','spine','detail','unit','bag','other')),
  ord          int  not null default 0,               -- order within the subject
  key_full     text not null,                         -- r2 object key, random: p/<uuid>/full.jpg
  key_thumb    text not null,
  width int, height int, bytes int,
  sha256       text not null,                         -- of the 1600px file; dedupe per owner
  lqip         text,
  source       text check (source in ('camera','library','desktop')),
  device_id    uuid,
  status       text not null default 'pending' check (status in ('pending','ready','failed')),
  taken_at     timestamptz, created_at timestamptz not null default now(),
  moved_from   jsonb,                                 -- last {subject_kind, subject_id}, for undo
  deleted_at   timestamptz                            -- soft delete; cron removes objects after 30 days
);
create unique index photos_owner_sha on photos(owner_key, sha256) where deleted_at is null;
create index photos_subject on photos(owner_key, subject_kind, subject_id, ord) where deleted_at is null;
```

Cover choice is per record, not per photo, so two "cover" flags cannot race. In the entity store (section 5) a record carries `cover: { source: 'discogs' | 'photo', photoId?: uuid }`. Default is `discogs`; setting `photo` requires a `ready` photo. If the chosen photo is deleted or moved away, the client falls back to `discogs` and the next op writes it back. Discogs images stay proxied through `api/img.js` and are never copied into R2 (research/discogs-api.md section 4 treats them as restricted data).

Deletion: `DELETE /api/photos/:id` sets `deleted_at`. A daily cron (`/api/cron/purge`) deletes R2 objects and rows older than 30 days. R2 deletes are free.

## 2. Identify from photo
### 2.1 Signals compared
| Signal | Where it runs | Cost | iOS Safari | Role |
|---|---|---|---|---|
| Barcode | Client, from the captured frame | $0 | `BarcodeDetector` is "disabled by default" on every iOS Safari version caniuse lists through 27.2 (https://caniuse.com/mdn-api_barcodedetector_detect). Chrome on Android supports it. | Use ZXing compiled to wasm (`zxing-wasm`; pin an exact version at build time, I did not verify a version) on all devices; ignore `BarcodeDetector` |
| Claude vision | Server | Haiku 5.5: input $0.10 per MTok (prompts up to 100k), output $0.50 per MTok. Sonnet 5.5: $2 and $10. Opus 5.5: $4 and $20 (https://platform.claude.com/docs/en/about-claude/pricing) | n/a | Primary reader |
| Google Vision OCR | Server | 1,000 units a month free, then $1.50 per 1,000 (summary from third-party page plus https://cloud.google.com/vision/pricing; verify) | n/a | Text only, so it still needs a parser to find artist, title and catalogue number; no cheaper than Haiku per photo ($0.0015 vs about $0.0004) |
| Discogs `/database/search` | Server | 1 of 60 requests a minute | n/a | Resolve text or barcode to a release |

Model ids (https://platform.claude.com/docs/en/about-claude/models/overview, checked today): `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`. Keep them in env (`ANTHROPIC_VISION_MODEL`, `ANTHROPIC_VISION_MODEL_ESCALATE`), as ARCHITECTURE.md already says. Per-image token cost is `ceil(w/28) * ceil(h/28)`, capped at 4,784 tokens and 2,576px on Claude 4.7-and-later models (https://platform.claude.com/docs/en/build-with-claude/vision). A 1600x1200 photo is 58 x 43 = 2,494 tokens.

Per photo, with a roughly 600-token prompt and 250 output tokens:
- Haiku 5.5: 3,100 in x $0.10/M + 250 out x $0.50/M = about $0.0004.
- Sonnet 5.5: 3,100 x $2/M + 250 x $10/M = about $0.009.
- Opus 5.5: about $0.018.
These ignore thinking tokens, which bill as output. The Models API reports per model whether thinking can be turned off (the docs say Sonnet 5.5 rejects `thinking: disabled`); check `capabilities.thinking` at build time and set low effort. Treat the figures above as a floor and budget 2x until measured. The Batch API is 50% off (Haiku 5.5 $0.05 in / $0.25 out) and suits the set-aside lane, not the live loop.

### 2.2 Pipeline (per capture)
```
phone shutter -> client resize/thumb -> ZXing on the frame (barcode, free)
  -> IDB outbox -> R2 upload -> POST /api/captures -> POST /api/captures/:id/identify
server identify:
  1. barcode present?  -> own collection by barcode, else Discogs search?barcode=  (0 to 1 call)
  2. else/also: Claude (forced single tool "report_release", strict schema, all photos of the capture in one request, each preceded by "Image n:")
     -> {artist, title, catno, label, year, format, barcode, side_notes, confidence}
  3. match against the owner's own synced collection first (discogs_releases, pg_trgm), no Discogs call
  4. only if no good own-collection match: Discogs /database/search (catno first, then artist+title), top 3
  5. score, store candidates, set status
```

Matching the owner's own collection first is the big saving. `discogs_releases` (006_sync.sql) already holds artist, title, label and catno for every owned release. Add a trigram index on `lower(data->>'title')`, on the joined artists, and on the catno with spaces and hyphens stripped. If most photographed records are already in the Discogs collection, identification costs zero Discogs requests. Only records not yet in the collection need the search endpoint.

Vision output is untrusted (ARCHITECTURE.md section 2): parse it with Zod, use it only as search input, never as a URL, tool call or SQL fragment. Sleeve text can carry instructions.

### 2.3 Capture state machine
```
local --(upload ok)--> uploaded --(POST /captures)--> queued
queued --(claim: update ... where status='queued' returning)--> reading
reading --(barcode/vision done)--> matching
matching --> ready          (score >= 0.85, margin >= 0.10, strong anchor)  [one tap or batch confirm]
matching --> review         (anything else with at least one candidate)
matching --> no_match       (no candidate; manual search box)
ready|review|no_match --(owner confirms)--> confirmed   [creates or links the record, moves photos]
any non-terminal --(timeout 30 s, or 2 failures)--> set_aside {reason, retry_at}
set_aside --(sweep or "retry set-aside")--> queued  [escalated model, or Batch API]
any --(owner)--> discarded
```

- Idempotency: `identify` claims the row with a single `update captures set status='reading', locked_until=now()+interval '60 seconds' where id=$1 and (status='queued' or locked_until < now()) returning *`. A repeated call is a no-op.
- Slow ones are set aside: the server aborts the Claude call at 30 s and the client does not wait on any single capture; the shutter loop never blocks on a result. The set-aside chip shows a count; the owner drains it later, or the sweep re-queues it on the escalated model.
- Nothing saves without an owner confirm (ARCHITECTURE.md "no silent writes"). `ready` only means pre-checked; the desktop review screen has "Confirm all N ready".
- Client concurrency: up to 3 uploads and 2 identify calls in flight. The server is stateless, so no worker is needed; each identify call is one function invocation (set `maxDuration` 60 in `vercel.json` like `sync.js`).

### 2.4 Confidence score
For each candidate release, from the best of the Claude fields and barcode:

```
sim_title  = trigram/Jaro-Winkler on normalised strings (lowercase, no "the", no punctuation)
sim_artist = same
catno_hit  = 1 if catno equal after stripping spaces, hyphens, case; else 0
bc_hit     = 1 if a barcode decoded or read from the photo equals the release barcode
owned      = 1 if the candidate is in the owner's collection

score = 0.40*sim_title + 0.25*sim_artist + 0.20*catno_hit + 0.05*sim_label + 0.10*owned
score = max(score, 0.95) if bc_hit and exactly one candidate has it
score = min(score, 0.80) if Claude confidence < 0.5        # the model's own number is a weak input, never raises a score
margin = score(top1) - score(top2)
```

Status `ready` needs: `score >= 0.85`, `margin >= 0.10`, and an anchor (`bc_hit`, `catno_hit`, or `owned` with a single owned release of that artist and title). Otherwise `review`. Multiple pressings sharing artist and title are the normal ambiguous case; the review card shows country, year, catno and format side by side, as research/discogs-api.md section 3 recommends. Log score, margin, model and token counts on the capture row so thresholds can be tuned from real data.

### 2.5 Shared Discogs budget
Authenticated limit is 60 requests a minute as a moving average over 60 s; image requests count too (research/discogs-api.md section 1). The existing in-memory pacing does not hold across serverless instances, so keep the counter in Postgres:

```sql
create table discogs_calls (at timestamptz not null default now(), lane text not null check (lane in ('interactive','background')));
create index discogs_calls_at on discogs_calls(at);

-- try to take one slot; zero rows returned = wait and retry
with u as (select count(*) total, count(*) filter (where lane = $1) mine
           from discogs_calls where at > now() - interval '60 seconds')
insert into discogs_calls(lane)
select $1 from u
where total < 54 and ($1 = 'interactive' or mine < 34)
returning at;
```

- 54 of 60 leaves headroom for clock skew; the background lane (sync, enrich) is capped at 34 so interactive work (identify, manual search) always has 20 a minute.
- On no row, sleep about 1.1 s and retry until the call's deadline, then fail soft (`set_aside` with reason `rate`). Also read `X-Discogs-Ratelimit-Remaining` from each response and stop the lane at 3 or fewer.
- Cost per identified record: 0 requests if it is in the owned collection; 1 search (sometimes 2); +1 `GET /releases/{id}` at confirm for a record that is not yet in `discogs_releases`. At 54 a minute that is 18 or more records a minute, faster than anyone can shoot and confirm.
- `api/sync.js` and `api/img.js` must take slots from the same table. The initial 2,000-release enrichment still takes about 34 minutes (research/discogs-api.md), so run it before the big photo session, not during.
- Prune with `delete from discogs_calls where at < now() - interval '5 minutes'` on every acquire (cheap, table stays tiny).

### 2.6 Grouping multi-photo batches into releases
- Unit of work is a capture: 1 to 4 photos of one release (front, back, label, barcode close-up).
- Default grouping in the shoot loop: a gap of more than 10 s between shutters starts a new capture, and a big "Next record" button starts one immediately. A "Same record" toggle keeps adding. The capture screen shows the current group as a strip of thumbs.
- Repair, not guess: on the review screen, `split` (drag a photo out into a new capture) and `merge` (join two captures) are one-tap actions. Auto-grouping by asking the model "are these the same release" costs a call per pair and is the first thing to cut.
- When sending to Claude, all photos of the capture go in one request. That is cheaper than one call per photo, and the back cover often carries the catalogue number the front lacks.
- A confirmed capture moves its photos to the record: `update photos set subject_kind='record', subject_id=$rec, moved_from=... where subject_kind='capture' and subject_id=$cap`. The first front shot becomes the optional personal cover.

### 2.7 Endpoints (new)
| Route | Purpose |
|---|---|
| `POST /api/photos/sign`, `POST /api/photos/complete` | Presigned PUT pair; mark ready |
| `GET /api/photo/:id?s=thumb|full` | Cookie-checked 302 to a presigned GET |
| `PATCH/DELETE /api/photos/:id` | Move, reorder, change kind, soft delete |
| `POST /api/captures` | Create from photo ids and an optional barcode |
| `POST /api/captures/:id/identify` | Idempotent run of section 2.2 |
| `GET /api/captures?status=` | Queue and review lists |
| `POST /api/captures/:id/confirm` | `{ discogs_release_id } | { record_id }`; creates or links, moves photos |
| `POST /api/captures/:id/split`, `/merge`, `/set-aside`, `/discard` | Repair and triage |
| `POST /api/discogs/search` | Manual search box, interactive lane |
| `GET /api/cron/identify-sweep` | Re-queue set-aside and stuck `reading` rows (daily on Hobby; also runs when the app opens) |

## 3. Phone and desktop, one owner
### 3.1 Auth: pair devices, no user accounts
Threat model: one owner, two or three devices, public URL. Needs: nobody else reads photos or loans, and no password typing on a phone.

- A `devices` table holds one row per paired device with a SHA-256 hash of a random 256-bit token. The token lives in an `__Host-crates` cookie (`HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age` one year). A cookie, not a bearer header, because `<img>` tags for `/api/photo/:id` carry cookies but not headers.
- First device: `OWNER_BOOTSTRAP_TOKEN` env var (32 random bytes). The owner opens `/?claim=<token>` on the desktop once. It works only while `devices` is empty, then the env var can be deleted. Locked out: set a new one and redeploy.
- Add a device: signed-in desktop calls `POST /api/auth/pair/start`, which stores an 8-character base32 code (40 bits) hashed, 5-minute expiry, single use, and shows a QR of `https://<app>/pair#<code>` plus the code in text. The phone posts the code to `POST /api/auth/pair/claim`, receives its cookie. Rate limit: 5 wrong attempts and the code dies.
- iOS trap: a Home Screen web app has its own cookie and storage jar, separate from Safari (widely reported; verify on the owner's phone). A QR scanned with the Camera app opens Safari, so the cookie would land in the wrong place. Flow: install to Home Screen first, open the installed app, then type the 8-character code or scan inside the app. The in-app scanner is the same ZXing code as the barcode reader.
- Revoke: Settings lists devices with last seen; revoke sets `revoked_at`. Every `/api` route runs `requireDevice()` (hash lookup, update `last_seen_at` at most once a minute).
- CSRF: `SameSite=Strict` plus requiring `Content-Type: application/json` and an `X-Crates: 1` header on writes.
- Runner-up: Neon Auth (email OTP or magic link) as ARCHITECTURE.md proposes. It adds a vendor and an email round trip per device for no gain with one owner. Revisit if a second person ever shares the app. I did not verify Neon Auth's current feature set.
- Cron routes are authenticated by `Authorization: Bearer $CRON_SECRET`, not a device cookie. Vercel documents sending the secret that way; confirm when wiring.

```sql
create table devices (id uuid primary key default gen_random_uuid(), owner_key text not null, name text,
  token_hash text not null unique, created_at timestamptz default now(), last_seen_at timestamptz, revoked_at timestamptz);
create table pair_codes (code_hash text primary key, owner_key text not null, expires_at timestamptz not null,
  attempts int default 0, used_at timestamptz);
```

### 3.2 Live updates
| Option | Verdict |
|---|---|
| Polling `GET /api/sync?since=<seq>` | Pick. Two devices, one human, changes are rare. Poll every 4 s while the tab is visible and on focus; stop when hidden. One tiny indexed query per poll. |
| SSE from a Vercel function | Works but each stream is a running function that must reconnect before `maxDuration` (300 s on Hobby, https://vercel.com/docs/functions/limitations). More moving parts than polling for no visible benefit. |
| Neon `LISTEN/NOTIFY` | Not on pooled connections: Neon's PgBouncer runs in transaction mode, so session features such as LISTEN/NOTIFY do not work (https://neon.com/faqs/best-postgres-services-connection-pooling). A direct connection per client would also keep compute awake. Reject. |
| Ably | Upgrade path. Free: 6M messages a month, 200 connections (https://ably.com/compare/ably-vs-pusher/pricing). The server publishes `{seq}` after a write; clients pull `since` on the ping. Polling code stays as the fallback. |
| Pusher, Supabase Realtime, PartyKit | Equivalent or needs a new vendor (Pusher Sandbox: 200k messages a day, 100 connections; others not evaluated, unverified). |

Neon cost watch: Free gives 100 compute-hours a month per project and scales to zero when idle (https://neon.com/pricing). A 0.25 CU compute awake 24 hours a day is about 180 CU-hours, so never poll in the background. Foreground-only polling keeps the database awake only while the app is open.

### 3.3 Sync model: server op log, field-level last-writer-wins
CRDTs (Automerge, Yjs) solve many simultaneous editors. One person with two devices does not need them; they add bundle size and a storage format. Use a server-ordered op log.

- Entity: `(kind, id)`. Kinds mirror the prototype: `unit`, `record`, `playlist`, `gig`, `loan`, `setting`. Photos are their own table (section 1.7) but emit ops for cover choice.
- Op: `{ id (client uuid), device, ts (client clock, ms), kind, eid, set: {field: value, ...}, del?: [fields], tomb?: true }`.
- Server applies ops in one transaction: insert into `ops` (idempotent `on conflict (id) do nothing`); for each field in `set`, write it only if `op.ts` is newer than the field's stamp in `entities.stamps`. This gives field-level merge when devices touch different fields and last-writer-wins on the same field.
- Atomic groups: a record's location (`loc`, `from`, `home`, `lent`) is one object field, replaced whole, so a half-merged location is impossible. `place()` in `crates.html` already treats these together.
- Deletes are tombstones (`deleted_at`), not row deletes, so a stale device cannot resurrect a record. A later `set` with newer `ts` revives it deliberately (undo).
- Clock skew: clamp `ts` to at most `server_now + 5 min`, and to at least `server_now - 30 days`; with two personal devices this is enough.
- Pull: `GET /api/sync?since=<seq>&limit=500` returns ops with `seq > since`. `seq` is a `bigserial` assigned by Postgres, so ordering is total and clients never need clocks to read.
- Offline queue: client ops go to IndexedDB `outbox` (not localStorage), flush on `online`, `visibilitychange` and after each write, in order. On flush the response returns the new head `seq`; the client then pulls and applies ops from other devices.
- Local apply: optimistic. Client applies its own op to `S` immediately; when it later receives the same op back from the pull it is skipped by id.

### 3.4 Hooking the prototype without touching every mutation
The prototype mutates `S` and calls `save()`. Add a hook: `save()` schedules (300 ms debounce) `emitOps(shadow, S)`, which diffs each unit, record, playlist and gig against a `shadow` copy and emits field ops. Measure at 2,000 records; fall back to per-record dirty flags if it exceeds about 20 ms. `place()` already funnels moves.

### 3.5 PWA and capture notes
- Install: `manifest.webmanifest` (`display: standalone`, icons from `logos/crates-mark-*.svg` rasterised to 192 and 512 PNG, `apple-touch-icon`), plus a service worker that precaches the shell. Guard registration so it only runs on the real origin (section 5).
- Camera, two modes:
  - `getUserMedia` live viewfinder: best for the shoot-and-keep-shooting loop (one tap per frame, no "Use photo" step) and lets ZXing scan frames continuously. Request `{ facingMode: 'environment', width: { ideal: 1920 } }`. Frames are video quality (less processing than the native camera), but 1920 px is enough for 1600 px output. Works in installed iOS web apps (iOS 13.4+, from memory, unverified).
  - `<input type="file" accept="image/*" capture="environment">`: full camera quality, but opens the native camera for each photo, which is slower. Use as the fallback and for desktop and library picks.
- Wake lock: `navigator.wakeLock.request('screen')` is supported in Safari on iOS 16.4+ (https://caniuse.com/wake-lock); an older caniuse note says it did not work in standalone Home Screen apps. Verify on the owner's iOS version; fallback is the hidden looping video trick. Re-request on `visibilitychange`.
- Web Push on iOS needs iOS 16.4+, the site added to the Home Screen, and the permission request triggered by a tap (https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/ and https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers). Not used in v1 (section 4).
- Do not rely on background sync (not available on iOS Safari, unverified). Uploads run while the app is open; the outbox chip shows what is waiting.
- Keep `Permissions-Policy: camera=(self)` as already set in `vercel.json`. CSP `connect-src` must add the R2 endpoint host (`https://<account>.r2.cloudflarestorage.com`) and `img-src` the same host.

## 4. Reminders for lent records
Owner's choice: in-app badge, plus an email digest to himself, plus a one-tap prefilled text to the borrower. Nothing else.

### 4.1 Rule
A loan is due at `lent_on + 14 days`. The first reminder fires on the due date. After that, once a week until returned. Snooze pushes `next_remind_on` out by 7 days.

```sql
create table loans (
  id uuid primary key default gen_random_uuid(),
  owner_key text not null,
  record_id text not null,                  -- entity id (section 5)
  borrower_name text not null,              -- first name or nickname is enough
  borrower_phone_enc text,                  -- AES-256-GCM, optional (see 4.5)
  lent_on date not null,
  due_on date not null,                     -- lent_on + 14
  next_remind_on date not null,             -- starts = due_on
  remind_count int not null default 0,
  last_digest_on date,                      -- idempotency for the cron
  last_nudged_at timestamptz,               -- owner tapped the text link (not proof it was sent)
  snoozed_until date,
  returned_on date,
  forget_after date,                        -- returned_on + 90 days; cron nulls name and phone
  note text
);
create index loans_open on loans(owner_key, next_remind_on) where returned_on is null;
```

A record that is lent gets `loc.lent = loanId` through the normal op path, so search shows "lent to Maya" and the record counts as away.

### 4.2 In-app badge
Client-computed from the loan entities: open loans with `today >= next_remind_on` and not snoozed. Show the count on a "Lent" tab and the top bar. It works offline and in the claude.ai preview. Do not use `navigator.setAppBadge` in v1: on iOS the icon badge appears to be tied to granting notification permission (WebKit post above), which this design avoids.

### 4.3 Email digest
- Vercel Cron, daily, entry in `vercel.json` `crons` pointing at `/api/cron/reminders`. Hobby allows once a day with hourly precision (plus or minus 59 minutes), 100 cron jobs per project (https://vercel.com/docs/schedules/cron-jobs/usage-and-pricing). A daily digest fits; hourly would need Pro. Pick a time outside 6 to 9 AM Pacific, which is when Vercel notes busier scheduling is typical (approximate; unverified for cron): `0 17 * * *` UTC, midday in New York.
- Compute: `select ... from loans where returned_on is null and next_remind_on <= current_date and (snoozed_until is null or snoozed_until <= current_date) and (last_digest_on is null or last_digest_on < current_date)`.
- Claim before sending: in one statement `update loans set last_digest_on = current_date, remind_count = remind_count + 1, next_remind_on = current_date + 7 where id = any(...) returning ...`, then send; if the email call fails, a second statement sets `last_digest_on = null` and `next_remind_on` back so tomorrow retries. A cron retry therefore cannot double-send.
- One email per day, only if there is at least one due loan: "3 records are out: Voodoo Ray (Maya, 21 days), ..." with a link to `/#lent`. The email contains first names and record titles only, no phone number, so the third party's number never transits an email provider.
- Resend free plan: 3,000 emails a month, 100 a day (https://resend.com/pricing). The free plan may send only from `onboarding@resend.dev` to the account owner's address (unverified; if true, no DNS setup is needed for a self-digest). Env: `RESEND_API_KEY`, `OWNER_EMAIL`, `MAIL_FROM`.

### 4.4 One-tap text to the borrower
Built in the app, on the phone, from data the app already has:

```
sms:<E.164 number>?&body=<encodeURIComponent(message)>
```

Default message, editable in Settings: `Hey {first}, it's Los. Do you still have {artist} - {title}? I lent it on {date}. No rush, just want to know where it is.` The `?&body=` form is the commonly cited cross-platform pattern (iOS and Android differ on `?` versus `&`); verify on the owner's phone and a second OS. Tapping opens Messages with the draft; the owner presses send. The app cannot know whether it was sent, so it records `last_nudged_at` on tap and labels it "Nudged" with undo. No server SMS (Twilio or similar): it needs a paid number and carrier registration, and messaging a third party who never opted in is the wrong default.

If the borrower has no phone saved, the button becomes "Copy message".

### 4.5 Privacy for the borrower's details
- Store the minimum: a first name or nickname is required; phone is optional. No surname, no email, no address, no contact import.
- Encrypt the phone at the application layer (AES-256-GCM, key `LOANS_KEY`, 32 bytes base64, set for Production only). Reason beyond disk encryption: INFRA.md and ARCHITECTURE.md use a Neon branch per preview deployment, and branches copy data; without the key in the preview environment a preview branch holds only ciphertext.
- Never log the name, phone or message body. Never send them to Anthropic, Discogs or Resend. The email digest carries names only (4.3).
- Retention: on return, set `forget_after = returned_on + 90 days`; the daily purge cron nulls `borrower_name` (to "(removed)") and `borrower_phone_enc`, keeping the record's history row. A "Forget this person" button does it immediately.

### 4.6 Not chosen
Web Push (iOS 16.4+, Home Screen install, tap-to-permit, VAPID keys, `web-push`) can ride the same cron if email proves too slow. A client-side .ics with a `VALARM` is a cheap later addition.

## 5. Migration from localStorage to the server
### 5.1 Tables (Phase 1)
The prototype state `S` (`units`, `records`, `playlists`, `gigs`, `settings`) is a JSON document with its own ids; `001_init.sql` is a normalised model with uuids. Mapping one onto the other now would couple the sync work to the React rewrite. So Phase 1 stores `S` as entities and leaves `001` for the rewrite; a one-off projection script moves entities into `001` tables when the SPA arrives.

```sql
create table entities (
  owner_key text not null, kind text not null, id text not null,
  data jsonb not null default '{}',
  stamps jsonb not null default '{}',     -- field -> ts of last accepted write
  deleted_at timestamptz,
  seq bigint not null,                    -- seq of the last op that touched it
  primary key (owner_key, kind, id)
);
create table ops (
  seq bigserial primary key, id uuid not null unique, owner_key text not null, device_id uuid,
  ts bigint not null, kind text not null, eid text not null, body jsonb not null,
  at timestamptz not null default now()
);
create index ops_owner_seq on ops(owner_key, seq);
```

Reuse: `discogs_releases` (006) is unchanged and keeps feeding `api/collection.js`. `discogs_sync_queue` (003) is not used by this path; the Discogs Location write-back moves to a server job that reads `loc` changes from `ops` once the real Discogs write is built (separate work package).

### 5.2 `/api/state` and `/api/sync`
| Route | Behaviour |
|---|---|
| `GET /api/state` | Bootstrap: `{ seq, S }` rebuilt from non-deleted entities (units, records, playlists, gigs, settings) plus photo refs. Cacheable by `seq`. |
| `POST /api/state/import` | One-time upload of the whole local `S`. Refuses if the server already has entities unless `?replace=1` is sent and the client confirms in-page (no `confirm()`); takes an automatic snapshot first (`entities` copy into a `state_backups` row, jsonb, keep the last 5). Explodes `S` into entities and ops in one transaction. |
| `GET /api/sync?since=` / `POST /api/sync` | Pull and push ops (section 3.3). |

### 5.3 Client migration flow
1. App boots from localStorage as it does today (`KEY = 'crates-demo-v3'`). Nothing changes if no server is reachable.
2. After pairing, the app calls `GET /api/state`. If the server is empty, show "Upload this device's collection to the server" (in-page confirm) and call import, keeping a local backup via the existing backups feature first. If the server has data and local has data, show a three-way choice: use server, upload mine (replace, with the automatic server snapshot), or keep both as a downloadable file. Never merge two full states silently.
3. After import: store `serverSeq`, create `shadow = clone(S)`, switch `save()` to emit ops. localStorage keeps being written as an offline cache.
4. Second device pairs, calls `GET /api/state`, replaces its local state (after one backup), then runs on pulls.

### 5.4 Keeping the prototype working offline and in the claude.ai preview
- Mode switch: `const API = location.origin === APP_ORIGIN ? '' : null`, where `APP_ORIGIN` is injected by `scripts/build.mjs` for the Vercel build and left empty for the artifact host. With `API === null` no `fetch('/api/...')` runs, no service worker registers, the capture screen saves photos to IndexedDB only, and the loans tab works from localStorage. The preview therefore behaves exactly like today.
- Reuse the existing probe style: `api/collection.js?ping=1` already answers "configured?" without touching Discogs or the database. Add `?ping=1` to the new auth route so the app can tell "server exists but not paired" from "no server".
- Offline on the real origin: service worker precaches the shell; the app runs from localStorage, the outbox queues ops and photos, and flushes on reconnect. Conflicts resolve by section 3.3.
- Tests: keep `API === null` the default in the harness; add mocked-fetch tests for the op emitter and outbox flush. Rollback: unpair; local `S` is complete because every change applies locally first.

## 6. Build plan, services, cost
### 6.1 Three phases, each shippable
| Phase | Scope | Done when |
|---|---|---|
| 1. Two devices and photos | `devices`, `pair_codes`, `entities`, `ops`, `photos`; `requireDevice()` in front of `sync.js`, `collection.js`, `img.js`; pairing UI; `/api/state` import; `save()` op hook; polling; PWA manifest and service worker; client photo pipeline; R2 sign/complete/serve; attach photos to records, units and bags; personal-cover toggle; move photo between releases; purge cron | The owner photographs a record on the phone, sees it on the desktop within seconds, and can set it as cover; unpair and offline both work |
| 2. Identify loop | Capture screen (`getUserMedia`), ZXing wasm, `captures`, Claude reader with Haiku then Sonnet escalation, own-collection trigram match, `discogs_calls` budget (and `sync.js`, `img.js` on it), review queue and "Confirm all ready" on desktop, set-aside lane, split/merge, sweep cron | A 100-record shoot-and-confirm session with set-asides drained at the end; thresholds tuned from logged scores |
| 3. Loans and live | `loans`, Lent tab and badge, `sms:` button, reminders cron and Resend digest, retention purge, optional Ably ping, optional .ics | A loan crosses day 14 and the digest arrives; tapping the link opens Messages with the draft |

Loans depend only on Phase 1 and are about two days of work; they can move ahead of Phase 2 if the owner prefers.

### 6.2 Env vars (names only, server-side; none get a `VITE_` prefix)
| Name | Phase | Purpose |
|---|---|---|
| `DATABASE_URL`, `DISCOGS_TOKEN`, `DISCOGS_USERNAME` | exist | Already in use |
| `OWNER_BOOTSTRAP_TOKEN` | 1 | First-device claim; delete after use |
| `APP_ORIGIN` | 1 | Origin for the mode switch and pairing URLs |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` | 1 | Presigned PUT and GET |
| `CRON_SECRET` | 1 | Authorises cron routes |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_VISION_MODEL`, `ANTHROPIC_VISION_MODEL_ESCALATE` | 2 | `claude-haiku-5-5`, `claude-sonnet-5-5` |
| `RESEND_API_KEY`, `OWNER_EMAIL`, `MAIL_FROM` | 3 | Digest |
| `LOANS_KEY` | 3 | AES-256-GCM key for phone numbers; Production only |
| `ABLY_API_KEY` (optional) | 3 | Publish only; clients use a short-lived token from the server |

### 6.3 Services to set up
1. Cloudflare account, one R2 bucket (private), an API token scoped to that bucket, CORS rule for the app origin.
2. Anthropic Console key with a monthly spend limit set low (for example $20) before Phase 2.
3. Resend account (Phase 3).
4. Vercel: add `crons` and a `maxDuration` for the identify route; cron needs no plan change on Hobby for daily runs. Neon: apply the new migrations to a branch first, then `main` (CLAUDE.md rule); next numbers are `007_sync_entities.sql`, `008_photos.sql`, `009_captures_budget.sql`, `010_loans.sql`.

### 6.4 Monthly cost at 2,000 records, 6,000 photos, 2 devices
Assumptions: 425 KB per photo (2.55 GB), 12,000 object writes to load them, 100 new records a month at 2 photos each after the backlog, foreground-only polling, Hobby, Neon Free.

| Item | Calculation | Cost |
|---|---|---|
| Vercel | Hobby; daily crons only; no Blob | $0 (Pro $20 only if hourly cron or Blob is chosen) |
| Neon | Data under 0.5 GB (entities, ops, discogs_releases, metadata); compute under 100 CU-hours with foreground polling | $0 (Launch is usage-billed at $0.106 per CU-hour and $0.35 per GB-month if the free limits are exceeded) |
| R2 storage | 2.55 GB, under 10 GB free | $0 (4.3 GB at 10,000 photos is also free) |
| R2 operations | 12,000 writes (1M free), well under 10M reads | $0 |
| Anthropic, steady state | 200 photos a month: Haiku about $0.0004 each; 15% escalate to Sonnet at about $0.009 | about $0.35, budget $1 |
| Anthropic, one-off backlog | 4,000 photos in 2,000 releases: all Haiku about $1.60; with 20% escalation about $9; all Sonnet about $36 (half price on Batch). Double for unmeasured thinking tokens | budget $20 |
| Resend | At most 31 emails a month | $0 |
| Ably (optional) | Far under 6M messages | $0 |
| Total steady state | | about $0.35 to $1 a month |

Alternative with Vercel Blob instead of R2: add the $20 Pro plan (usage itself is about $0.12), so about $20 a month. Alternative on Supabase: $25 Pro for storage beyond 1 GB.

### 6.5 Risks to test early
1. iPhone: `getUserMedia` in the installed app, portrait orientation, wake lock, and the separate Safari and Home Screen cookie jars (pairing flow).
2. R2 CORS and presigned PUT from iOS Safari with a `Blob` body.
3. Haiku 5.5 accuracy on worn sleeves and tiny catalogue numbers; log everything in Phase 2 before trusting `ready`. Read `usage` on every call (thinking tokens may inflate cost).
4. Neon cold start on the first poll after idle: paint cached state first, sync in the background.


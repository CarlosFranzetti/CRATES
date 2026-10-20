# Crates: Data Model

Status: documented from the real file `app/db/001_init.sql` (Neon Postgres 17; extensions `pgcrypto`, `pg_trgm`). `INFRA.md` reports `001_init.sql` and `002_seed.sql` (demo owner `demo`) applied to the Neon project `crates`. The example queries below were written against the file but not executed; run them against the seed before relying on them. Last updated 2026-10-20.

## Tables at a glance

| Table | Purpose | Key columns |
|---|---|---|
| `units` | One row per physical thing: shelf, crate, bag, box, wall, bin | `code` (K1, B1), `name`, `kind`, `preset_key`, `rows`, `cols`, `finish_name/hex`, `photo_url` |
| `records` | One row per owned copy | `discogs_release_id`, `discogs_snapshot`, display columns, `edited_fields`, `bpm`, `musical_key`, `rating`, `tags`, `custom` |
| `tracks` | Tracklist of a record | `record_id`, `position` (Discogs "A1"), `title`, `duration_s`, per-track `bpm`/`musical_key` |
| `media_links` | Playback sources (YouTube) | `record_id`, nullable `track_id`, `external_id`, `rank`, `status`, `last_checked_at` |
| `record_locations` | Where a record is now, and its home | `unit_id`, `cell_row`, `cell_col`, `home_*`; PK = `record_id` |
| `location_events` | Append-only movement history | `from_*`, `to_*`, `reason`, `at` |
| `playlists` / `playlist_items` | Ordered lists | `position` (1-based in seed), optional `track_id`, `note` |
| `bag_scans` | A bag photo and what the vision pass found | `unit_id`, `photo_url`, `found` jsonb, `applied` |

`owner_id text` is on `units`, `records`, `playlists`. Child tables inherit ownership through their parent, so **every API query must join to a parent and filter on `owner_id`**. There are no foreign keys to an auth table and no RLS in `001_init.sql`.

## Addressing scheme

- **Unit code** (`units.code`, unique per owner): a letter prefix plus a number. `K1`, `K2` for Kallax and other shelving, `B1` for bags, and so on. The prefix is chosen from the preset group when the unit is created and never reused after deletion.
- **Cell** (a cubby): row letter plus column number. Stored as **0-based integers** (`cell_row = 0` is row A, `cell_col = 0` is column 1; see the `002_seed.sql` comment). Display: `chr(65 + cell_row)` and `cell_col + 1`.
  - 2x4 Kallax: `A1..A4`, `B1..B4`. 2x2: `A1..A2`, `B1..B2`. Max 26 rows (a 5x5 Kallax is the biggest preset).
- **Shelf code** is always `unit.code + "·" + cell`, for example `K2·B2`. The unit prefix keeps it from reading like a Discogs side/track position (`A1`, `B2`). Never render a bare `B2`.
- **Input parsing** accepts `K2·B2`, `K2-B2`, `K2 B2` (case-insensitive): `^([A-Z]+\d+)[·\- ]([A-Z])(\d+)$`.
- **Non-grid units** (`crate`, `bag`, `box`, `bin`) have `rows = cols = 1`; their location is the unit alone, stored with `cell_row = 0, cell_col = 0`. Display `B1` or the name ("bag Crater"), never a cell.
- **"All"** in the UI is the absence of a cell filter on a unit.
- Bounds (`cell_row < rows`, `cell_col < cols`) are **not** enforced by the database. The API validates them.

## Current location versus home slot

`record_locations` has exactly one row per record (PK `record_id`).

- **Current** (`unit_id`, `cell_row`, `cell_col`): where the record physically is right now. In a bag, `unit_id` is the bag and the cell is `0,0`.
- **Home** (`home_unit_id`, `home_row`, `home_col`): the shelf slot it returns to.
- Rules the API enforces:
  1. Moving a record to a **non-bag** unit sets current **and** home (it was re-shelved).
  2. Moving a record into a **bag** sets current only. Home is untouched.
  3. A record missing from a bag scan returns to its home slot. If home is null it stays unplaced (`unit_id` null) and is flagged "needs a home".
  4. Every change writes a `location_events` row. `reason`: `add` (new record), `move` (manual), `scan` (placed in a bag by a scan), `unpack` (returned home because a scan did not find it), `undo` (reverting an event). The `scan`/`unpack` split is this doc's convention; the check constraint only lists the five values.
- Order *within* a cell is undefined in the current schema (see gaps).

## Discogs snapshot versus owner edits

- `discogs_snapshot` is the raw Discogs release JSON as of the last import or re-sync. It is the source of truth for "what Discogs says" and is never edited by the owner.
- The display columns (`artist`, `title`, `label`, `catno`, `year`, `country`, `format`, `genres`, `styles`, `cover_url`) hold the **effective** value the UI shows and searches.
- `edited_fields text[]` lists the display columns the owner has overridden. Allowlist: those ten column names.
- **Re-sync** (`POST /api/records/:id/resync`): fetch the release, replace `discogs_snapshot`, then rewrite every display column **not** in `edited_fields` from the new snapshot. Edited columns are never touched.
- **Reset to Discogs** for a field: remove it from `edited_fields` and recompute that column from the snapshot.
- **Owner-only fields** (`bpm`, `musical_key`, `rating`, `condition_media`, `condition_sleeve`, `notes`, `tags`, `custom`) are never overwritten by sync and need no `edited_fields` entry. `custom` is a free-form jsonb object of owner-defined fields. `tracks.bpm/musical_key/notes` are likewise owner-only.
- `updated_at` on `records` is maintained by the `records_set_updated_at` trigger.

```sql
-- Edit one overridden field (name comes from the allowlist, never from raw input)
update records
   set title = $3,
       edited_fields = array(select distinct unnest(edited_fields || array['title']))
 where id = $1 and owner_id = $2;
```

## Media links

- `rank` 0 is the primary link, 1 is the cached alternate (the old `youtube2`), 2+ are further candidates.
- `track_id is null` means a record-level link (Discogs videos are per release). Per-track links set `track_id`.
- `status`: `pending` (not yet confirmed), `working`, `non_working`. Unique on `(record_id, provider, external_id)`.
- Semantics and the fallback chain are in [PLAYER.md](PLAYER.md).

## Example queries

### 1. Find where a record is

```sql
select r.id, r.artist, r.title, u.name as unit_name, u.kind,
       case when u.kind = 'shelf'
            then u.code || '·' || chr(65 + l.cell_row) || (l.cell_col + 1)
            else u.code end                         as place,
       (l.unit_id is distinct from l.home_unit_id
        or l.cell_row is distinct from l.home_row
        or l.cell_col is distinct from l.home_col)  as is_away,
       case when h.kind = 'shelf'
            then h.code || '·' || chr(65 + l.home_row) || (l.home_col + 1)
            else h.code end                         as home_place
from records r
join record_locations l on l.record_id = r.id
left join units u on u.id = l.unit_id
left join units h on h.id = l.home_unit_id
where r.owner_id = $1
  and (lower(r.artist) like $2 or lower(r.title) like $2)   -- $2 = '%' || escaped lower(term) || '%'
order by r.artist, r.title
limit 20;
```

The LIKE on `lower(artist)` / `lower(title)` uses the `pg_trgm` GIN indexes. The UI renders `place` as "Kallax 2, shelf B2" (`unit_name`, cell) or "bag Crater".

### 2. Move one record (one or two taps)

```sql
with cur as (
  select * from record_locations where record_id = $2
    and exists (select 1 from records where id = $2 and owner_id = $1)
), tgt as (
  select id, kind from units where id = $3 and owner_id = $1
), upd as (
  update record_locations l
     set unit_id = t.id, cell_row = $4, cell_col = $5, moved_at = now(),
         home_unit_id = case when t.kind = 'bag' then l.home_unit_id else t.id end,
         home_row     = case when t.kind = 'bag' then l.home_row     else $4   end,
         home_col     = case when t.kind = 'bag' then l.home_col     else $5   end
    from tgt t, cur
   where l.record_id = cur.record_id
  returning l.record_id
)
insert into location_events (record_id, from_unit, from_row, from_col, to_unit, to_row, to_col, reason)
select c.record_id, c.unit_id, c.cell_row, c.cell_col, $3, $4, $5, 'move' from cur c join upd using (record_id);
```

For a bag target the API passes `$4 = $5 = 0`. Undo replays the last event in reverse and writes `reason = 'undo'`.

### 3. Reconcile a bag scan in one transaction

One statement, so it is atomic even over Neon's HTTP driver. Inputs: `$1` owner, `$2` bag unit id, `$3 uuid[]` record ids the user confirmed from the photo, `$4` the `bag_scans.id`, `$5` the `found` jsonb. Records in `$3` not yet in the bag go in (`scan`). Records in the bag but not in `$3` go home (`unpack`).

```sql
with bag as (
  select id from units where id = $2 and owner_id = $1 and kind = 'bag'
), found as (
  select id from records where owner_id = $1 and id = any($3::uuid[])
), prev as (                                   -- pre-update snapshot (all CTEs see one snapshot)
  select l.*, b.id as bag_id
  from record_locations l cross join bag b
  where l.record_id in (select id from found) or l.unit_id = b.id
), to_bag as (
  select * from prev where unit_id is distinct from bag_id and record_id in (select id from found)
), to_home as (
  select * from prev where unit_id = bag_id and record_id not in (select id from found)
), mv_in as (
  update record_locations l set unit_id = t.bag_id, cell_row = 0, cell_col = 0, moved_at = now()
  from to_bag t where l.record_id = t.record_id returning 1
), mv_out as (
  update record_locations l set unit_id = t.home_unit_id, cell_row = t.home_row, cell_col = t.home_col, moved_at = now()
  from to_home t where l.record_id = t.record_id returning 1
), ev_in as (
  insert into location_events (record_id, from_unit, from_row, from_col, to_unit, to_row, to_col, reason)
  select record_id, unit_id, cell_row, cell_col, bag_id, 0, 0, 'scan' from to_bag returning 1
), ev_out as (
  insert into location_events (record_id, from_unit, from_row, from_col, to_unit, to_row, to_col, reason)
  select record_id, unit_id, cell_row, cell_col, home_unit_id, home_row, home_col, 'unpack' from to_home returning 1
)
update bag_scans set applied = true, found = $5::jsonb
 where id = $4 and unit_id = (select id from bag)
returning (select count(*) from to_bag) as added, (select count(*) from to_home) as returned;
```

If the bag is not the owner's, `bag` is empty, every downstream CTE is empty, and nothing changes. The review screen shows the same `to_bag` / `to_home` sets as a read-only SELECT before the user confirms. Until then `bag_scans.applied = false`. Proposed `found` shape (not defined by the schema): `[{ "record_id": uuid, "confidence": 0-1, "source": "vision" | "manual" }]`.

### 4. Reorder a playlist

The client sends the full ordered list of item ids after a drag. `position` is 1-based (as in the seed); there is no unique constraint on `(playlist_id, position)`, so no transient conflicts. A stale client (item added or removed elsewhere) updates zero rows and the API answers 409.

```sql
with want as (
  select item_id, ord from unnest($2::uuid[]) with ordinality as o(item_id, ord)
), ok as (
  select 1 from playlists p
   where p.id = $1 and p.owner_id = $3
     and (select count(*) from playlist_items where playlist_id = $1) = (select count(*) from want)
     and not exists (select 1 from want w
                     left join playlist_items i on i.id = w.item_id and i.playlist_id = $1
                     where i.id is null)
)
update playlist_items pi set position = w.ord
  from want w
 where pi.id = w.item_id and pi.playlist_id = $1 and exists (select 1 from ok);
```

## Feature tables (003)

`app/db/003_features.sql` (applied 2026-10-20, seed `004_seed_features.sql`). The queries below were checked with EXPLAIN against the seed.

| Object | What it adds |
|---|---|
| `cell_labels` | Cubby subtitle per `(unit_id, cell_row, cell_col)`: render `K1·A2 (Acid)` |
| `record_locations.prev_*` | "Came from": the slot before the current container. A BEFORE trigger fills it whenever `unit_id` changes and the caller did not set `prev_*`. Show it only when the current unit is a bag/crate |
| `records.dup_key` | Generated: `record_dup_key(artist, title)` = lowercased, quotes dropped, other punctuation to spaces. Indexed with `owner_id`; also indexes on `(owner_id, discogs_release_id)` and `(owner_id, barcode)` |
| `records.barcode`, `discogs_instance_id` | Scan input and Discogs collection instance (still not unique; see gap 2) |
| `barcode_lookups` | One scan: `barcode`, Discogs `candidates` jsonb, `chosen_release_id` |
| `discogs_sync_queue` + `records.discogs_location_synced(_at)` | Outbox for the Discogs "Location" field. Trigger on `record_locations` insert/move enqueues `K1·B2` for grids or the unit name ("Crater") for bags/crates. One `pending` row per record (partial unique index); later moves overwrite its value. The worker sets `done`/`failed`, `attempts`, `last_error`, then `discogs_location_synced*` |
| `cell_code(row, col)` | `cell_code(1,1) = 'B2'` |
| `gigs`, `gig_items` | Packing list: gig → bag, status `planning → packed → out → returned`; items carry `packed_at`, `played`, `returned_at` |
| `plays`, view `records_last_played` | Set history (`gig_id` optional); view gives `last_played_at`, `play_count` |
| `units.qr_token`, `sticker_prints` | 8-char unique token per unit for QR stickers (`/u/<token>`); print log per unit or cell |
| `location_events.reason` | Adds `gig_pack`, `gig_return`, `cubby_move`, `swap` |

```sql
-- Duplicate check on add ($2 release id, $3 barcode, $4 artist, $5 title)
select id, artist, title,
       case when discogs_release_id = $2 then 'release' when barcode = $3 then 'barcode' else 'name' end as matched_on
  from records
 where owner_id = $1
   and (discogs_release_id = $2 or barcode = $3 or dup_key = record_dup_key($4, $5));

-- Cubby move: everything in K1·A2 to K1·B1, one statement, logged
with k as (select id from units where owner_id = $1 and code = 'K1'),
mv as (
  update record_locations l set cell_row = 1, cell_col = 0, home_row = 1, home_col = 0, moved_at = now()
    from k where l.unit_id = k.id and l.cell_row = 0 and l.cell_col = 1
  returning l.record_id, k.id as kid)
insert into location_events (record_id, from_unit, from_row, from_col, to_unit, to_row, to_col, reason)
select record_id, kid, 0, 1, kid, 1, 0, 'cubby_move' from mv;
-- Bagged records whose home is A2, and the A2 label, are moved by separate updates.

-- Swap K1·A1 and K1·B1 (both directions in one update, so no temp slot)
with k as (select id from units where owner_id = $1 and code = 'K1'),
pair(fr, fc, tr, tc) as (values (0,0,1,0), (1,0,0,0)),
sw as (
  update record_locations l set cell_row = p.tr, cell_col = p.tc, home_row = p.tr, home_col = p.tc, moved_at = now()
    from k, pair p where l.unit_id = k.id and l.cell_row = p.fr and l.cell_col = p.fc
  returning l.record_id, k.id as kid, p.fr, p.fc, p.tr, p.tc)
insert into location_events (record_id, from_unit, from_row, from_col, to_unit, to_row, to_col, reason)
select record_id, kid, fr, fc, kid, tr, tc, 'swap' from sw;

-- Gig pack ($2 gig id): items into the gig's bag; trigger records prev_*
with g as (select id, bag_unit_id from gigs where id = $2 and owner_id = $1 and bag_unit_id is not null),
cur as (select l.*, g.bag_unit_id from record_locations l
          join gig_items i on i.record_id = l.record_id join g on g.id = i.gig_id
         where l.unit_id is distinct from g.bag_unit_id),
mv as (update record_locations l set unit_id = c.bag_unit_id, cell_row = 0, cell_col = 0, moved_at = now()
         from cur c where l.record_id = c.record_id returning 1),
ev as (insert into location_events (record_id, from_unit, from_row, from_col, to_unit, to_row, to_col, reason)
       select record_id, unit_id, cell_row, cell_col, bag_unit_id, 0, 0, 'gig_pack' from cur returning 1),
it as (update gig_items set packed_at = now() where gig_id = (select id from g) and packed_at is null returning 1)
update gigs set status = 'packed' where id = (select id from g);

-- Gig return: records still in the bag go back to where they came from (else home)
with g as (select id, bag_unit_id from gigs where id = $2 and owner_id = $1),
cur as (select l.* from record_locations l
          join gig_items i on i.record_id = l.record_id and i.gig_id = (select id from g)
         where l.unit_id = (select bag_unit_id from g)),
mv as (update record_locations l
          set unit_id  = coalesce(c.prev_unit_id, c.home_unit_id),
              cell_row = case when c.prev_unit_id is not null then c.prev_row else c.home_row end,
              cell_col = case when c.prev_unit_id is not null then c.prev_col else c.home_col end,
              prev_unit_id = null, prev_row = null, prev_col = null, moved_at = now()
         from cur c where l.record_id = c.record_id
       returning l.record_id, l.unit_id, l.cell_row, l.cell_col),
ev as (insert into location_events (record_id, from_unit, from_row, from_col, to_unit, to_row, to_col, reason)
       select c.record_id, c.unit_id, c.cell_row, c.cell_col, m.unit_id, m.cell_row, m.cell_col, 'gig_return'
         from cur c join mv m using (record_id) returning 1),
it as (update gig_items set returned_at = now() where gig_id = (select id from g) and returned_at is null returning 1)
update gigs set status = 'returned' where id = (select id from g);
-- Marking a record played: update gig_items set played = true, plus insert into plays (record_id, gig_id, venue).

-- Not played in a year (never-played first)
select r.artist, r.title, lp.last_played_at, coalesce(lp.play_count, 0) as plays
  from records r left join records_last_played lp on lp.record_id = r.id
 where r.owner_id = $1 and (lp.last_played_at is null or lp.last_played_at < now() - interval '1 year')
 order by lp.last_played_at nulls first, r.artist;
```

## Gaps and open items in `001_init.sql`

1. **No ordering inside a cell.** Flip order is undefined. Either sort by artist/title or add `record_locations.slot int`.
2. **No stable import key.** `(owner_id, discogs_release_id)` is correctly not unique (duplicate copies), but re-import needs one. Add `records.discogs_instance_id bigint` and a unique index on `(owner_id, discogs_instance_id)`.
3. **No uniqueness on `tracks (record_id, position)`**, so a re-sync can duplicate tracks. Add it before Phase 2.
4. **`media_links` has no duration or failure count.** The teaser guard (PLAYER.md) benefits from `duration_s` and `fail_count`.
5. **Cell bounds and `kind`/shape consistency** are API-only. A trigger or check could back them.
6. **`preset_key` naming differs** between the prototype (`kallax-2x4`) and the seed (`ikea-kallax-2x4`). Pick one before the preset table is written.
7. **No auth link or RLS.** `owner_id` is plain text. Decide the Neon Auth id mapping in Phase 1 and consider RLS as defence in depth.
8. `playlist_items.track_id` has no `ON DELETE` action, so deleting a single track that is in a playlist fails. Records cascade fine.

-- Crates: feature schema (cubby labels, came-from, dupes, barcodes, Discogs Location sync,
-- gigs, set history, QR stickers). Idempotent. Statements separated by "-- ;;".

-- 1. Cubby subtitles, e.g. "A2 (House)"
create table if not exists cell_labels (
  unit_id  uuid references units(id) on delete cascade,
  cell_row int,
  cell_col int,
  label    text not null,
  primary key (unit_id, cell_row, cell_col)
);
-- ;;
-- 2. "Came from": where a record was before entering its current container
alter table record_locations
  add column if not exists prev_unit_id uuid references units(id) on delete set null,
  add column if not exists prev_row int,
  add column if not exists prev_col int;
-- ;;
update record_locations l
   set prev_unit_id = l.home_unit_id, prev_row = l.home_row, prev_col = l.home_col
  from units u
 where u.id = l.unit_id and u.kind in ('bag','crate') and l.prev_unit_id is null;
-- ;;
-- Keep prev_* current automatically: when unit_id changes and the caller did not set prev_*,
-- remember the old slot.
create or replace function record_locations_track_prev() returns trigger language plpgsql as $$
begin
  if new.unit_id is distinct from old.unit_id
     and new.prev_unit_id is not distinct from old.prev_unit_id
     and new.prev_row is not distinct from old.prev_row
     and new.prev_col is not distinct from old.prev_col then
    new.prev_unit_id := old.unit_id;
    new.prev_row     := old.cell_row;
    new.prev_col     := old.cell_col;
  end if;
  return new;
end;
$$;
-- ;;
drop trigger if exists record_locations_track_prev on record_locations;
-- ;;
create trigger record_locations_track_prev before update of unit_id on record_locations
  for each row execute function record_locations_track_prev();
-- ;;
-- 3. Duplicate detection + Discogs/barcode identity
create or replace function record_dup_key(a text, t text) returns text
  language sql immutable parallel safe as $$
  select trim(regexp_replace(
           regexp_replace(lower(coalesce(a,'') || ' – ' || coalesce(t,'')), '[''’`]', '', 'g'),
           '[^[:alnum:]]+', ' ', 'g'))
$$;
-- ;;
alter table records
  add column if not exists barcode text,
  add column if not exists discogs_instance_id bigint,
  add column if not exists dup_key text generated always as (record_dup_key(artist, title)) stored;
-- ;;
create index if not exists records_dup_key_idx on records (owner_id, dup_key);
-- ;;
create index if not exists records_release_idx on records (owner_id, discogs_release_id);
-- ;;
create index if not exists records_barcode_idx on records (owner_id, barcode);
-- ;;
-- 4. Barcode lookups
create table if not exists barcode_lookups (
  id                uuid primary key default gen_random_uuid(),
  owner_id          text not null,
  barcode           text not null,
  candidates        jsonb default '[]',
  chosen_release_id bigint,
  created_at        timestamptz default now()
);
-- ;;
create index if not exists barcode_lookups_owner_idx on barcode_lookups (owner_id, barcode);
-- ;;
-- 5. Discogs "Location" field sync
alter table records
  add column if not exists discogs_location_synced    text,
  add column if not exists discogs_location_synced_at timestamptz;
-- ;;
create table if not exists discogs_sync_queue (
  id         bigserial primary key,
  record_id  uuid references records(id) on delete cascade,
  field      text default 'Location',
  value      text,
  status     text default 'pending' check (status in ('pending','done','failed')),
  attempts   int default 0,
  last_error text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
-- ;;
-- At most one pending row per record+field; later moves overwrite its value.
create unique index if not exists discogs_sync_queue_pending_uq
  on discogs_sync_queue (record_id, field) where status = 'pending';
-- ;;
create index if not exists discogs_sync_queue_status_idx on discogs_sync_queue (status, created_at);
-- ;;
drop trigger if exists discogs_sync_queue_set_updated_at on discogs_sync_queue;
-- ;;
create trigger discogs_sync_queue_set_updated_at before update on discogs_sync_queue
  for each row execute function set_updated_at();
-- ;;
-- cell_code(0,1) = 'A2'
create or replace function cell_code(r int, c int) returns text
  language sql immutable parallel safe as $$
  select chr(65 + coalesce(r,0)) || (coalesce(c,0) + 1)::text
$$;
-- ;;
create or replace function enqueue_discogs_location() returns trigger language plpgsql as $$
declare v text;
begin
  if tg_op = 'UPDATE'
     and new.unit_id  is not distinct from old.unit_id
     and new.cell_row is not distinct from old.cell_row
     and new.cell_col is not distinct from old.cell_col then
    return null;
  end if;
  select case when u.kind in ('bag','crate') then u.name
              else u.code || '·' || cell_code(new.cell_row, new.cell_col) end
    into v
    from units u where u.id = new.unit_id;
  insert into discogs_sync_queue (record_id, field, value)
  values (new.record_id, 'Location', coalesce(v, ''))
  on conflict (record_id, field) where status = 'pending'
  do update set value = excluded.value, attempts = 0, last_error = null;
  return null;
end;
$$;
-- ;;
drop trigger if exists record_locations_enqueue_discogs on record_locations;
-- ;;
create trigger record_locations_enqueue_discogs
  after insert or update of unit_id, cell_row, cell_col on record_locations
  for each row execute function enqueue_discogs_location();
-- ;;
-- 6. Gig packing list
create table if not exists gigs (
  id          uuid primary key default gen_random_uuid(),
  owner_id    text not null,
  name        text not null,
  venue       text,
  gig_date    date,
  bag_unit_id uuid references units(id) on delete set null,
  status      text default 'planning' check (status in ('planning','packed','out','returned')),
  created_at  timestamptz default now()
);
-- ;;
create index if not exists gigs_owner_date_idx on gigs (owner_id, gig_date desc);
-- ;;
create table if not exists gig_items (
  gig_id      uuid references gigs(id) on delete cascade,
  record_id   uuid references records(id) on delete cascade,
  position    int,
  packed_at   timestamptz,
  played      boolean default false,
  returned_at timestamptz,
  primary key (gig_id, record_id)
);
-- ;;
create index if not exists gig_items_record_idx on gig_items (record_id);
-- ;;
-- 7. Set history
create table if not exists plays (
  id        uuid primary key default gen_random_uuid(),
  record_id uuid references records(id) on delete cascade,
  gig_id    uuid null references gigs(id) on delete set null,
  played_at timestamptz not null default now(),
  venue     text,
  note      text
);
-- ;;
create index if not exists plays_record_idx on plays (record_id, played_at desc);
-- ;;
create or replace view records_last_played as
  select record_id, max(played_at) as last_played_at, count(*) as play_count
    from plays group by record_id;
-- ;;
-- 8. QR stickers
alter table units add column if not exists qr_token text default substring(md5(random()::text), 1, 8);
-- ;;
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'units_qr_token_key') then
    alter table units add constraint units_qr_token_key unique (qr_token);
  end if;
end $$;
-- ;;
create table if not exists sticker_prints (
  id         bigserial primary key,
  unit_id    uuid references units(id) on delete cascade,
  cell_row   int null,
  cell_col   int null,
  printed_at timestamptz default now()
);
-- ;;
-- 9. More location_events reasons
alter table location_events drop constraint if exists location_events_reason_check;
-- ;;
alter table location_events add constraint location_events_reason_check
  check (reason in ('move','scan','unpack','add','undo','gig_pack','gig_return','cubby_move','swap'));

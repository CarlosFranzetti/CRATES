-- Crates: initial schema (Neon Postgres 17)
-- Statements are separated by a line containing only "-- ;;" so tooling can split them.

create extension if not exists pgcrypto;
-- ;;
create extension if not exists pg_trgm;
-- ;;
create table if not exists units (
  id          uuid primary key default gen_random_uuid(),
  owner_id    text not null,
  code        text not null,
  name        text not null,
  kind        text check (kind in ('shelf','crate','bag','box','wall','bin')),
  preset_key  text,
  rows        int not null default 1,
  cols        int not null default 1,
  finish_name text,
  finish_hex  text,
  photo_url   text,
  sort        int default 0,
  created_at  timestamptz default now(),
  unique (owner_id, code)
);
-- ;;
create table if not exists records (
  id                 uuid primary key default gen_random_uuid(),
  owner_id           text not null,
  discogs_release_id bigint,
  discogs_master_id  bigint,
  discogs_snapshot   jsonb,
  artist             text not null,
  title              text not null,
  label              text,
  catno              text,
  year               int,
  country            text,
  format             text,
  genres             text[],
  styles             text[],
  cover_url          text,
  bpm                numeric(5,1),
  musical_key        text,
  rating             smallint check (rating between 0 and 5),
  condition_media    text,
  condition_sleeve   text,
  notes              text,
  tags               text[] default '{}',
  custom             jsonb default '{}',
  edited_fields      text[] default '{}',
  created_at         timestamptz default now(),
  updated_at         timestamptz default now()
);
-- ;;
create table if not exists tracks (
  id          uuid primary key default gen_random_uuid(),
  record_id   uuid references records(id) on delete cascade,
  position    text,
  title       text,
  duration_s  int,
  bpm         numeric(5,1),
  musical_key text,
  notes       text
);
-- ;;
create table if not exists media_links (
  id              uuid primary key default gen_random_uuid(),
  record_id       uuid references records(id) on delete cascade,
  track_id        uuid null references tracks(id) on delete cascade,
  provider        text default 'youtube',
  external_id     text not null,
  rank            smallint default 0,
  status          text default 'pending' check (status in ('pending','working','non_working')),
  last_checked_at timestamptz,
  unique (record_id, provider, external_id)
);
-- ;;
create table if not exists record_locations (
  record_id    uuid primary key references records(id) on delete cascade,
  unit_id      uuid references units(id) on delete set null,
  cell_row     int,
  cell_col     int,
  home_unit_id uuid references units(id) on delete set null,
  home_row     int,
  home_col     int,
  moved_at     timestamptz default now()
);
-- ;;
create table if not exists location_events (
  id        bigserial primary key,
  record_id uuid references records(id) on delete cascade,
  from_unit uuid,
  from_row  int,
  from_col  int,
  to_unit   uuid,
  to_row    int,
  to_col    int,
  reason    text check (reason in ('move','scan','unpack','add','undo')),
  at        timestamptz default now()
);
-- ;;
create table if not exists playlists (
  id          uuid primary key default gen_random_uuid(),
  owner_id    text not null,
  name        text not null,
  description text,
  color       text,
  sort        int default 0,
  created_at  timestamptz default now()
);
-- ;;
create table if not exists playlist_items (
  id          uuid primary key default gen_random_uuid(),
  playlist_id uuid references playlists(id) on delete cascade,
  record_id   uuid references records(id) on delete cascade,
  track_id    uuid null references tracks(id),
  position    int not null,
  note        text
);
-- ;;
create table if not exists bag_scans (
  id         uuid primary key default gen_random_uuid(),
  unit_id    uuid references units(id) on delete cascade,
  photo_url  text,
  found      jsonb,
  applied    boolean default false,
  created_at timestamptz default now()
);
-- ;;
create index if not exists records_owner_idx on records (owner_id);
-- ;;
create index if not exists records_artist_trgm on records using gin (lower(artist) gin_trgm_ops);
-- ;;
create index if not exists records_title_trgm on records using gin (lower(title) gin_trgm_ops);
-- ;;
create index if not exists record_locations_cell_idx on record_locations (unit_id, cell_row, cell_col);
-- ;;
create index if not exists playlist_items_pos_idx on playlist_items (playlist_id, position);
-- ;;
create index if not exists tracks_record_idx on tracks (record_id);
-- ;;
create index if not exists media_links_record_idx on media_links (record_id, rank);
-- ;;
create index if not exists location_events_record_idx on location_events (record_id, at desc);
-- ;;
create or replace function set_updated_at() returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;
-- ;;
drop trigger if exists records_set_updated_at on records;
-- ;;
create trigger records_set_updated_at before update on records
  for each row execute function set_updated_at();

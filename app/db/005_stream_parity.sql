-- 005: parity with discogs-stream's schema, plus collection backups and imports.
-- discogs-stream (CarlosFranzetti/discogs-stream, supabase/migrations) keeps these tables; Crates keeps the same
-- names and columns so the player port and its server jobs (search cache, rescan) can be reused as-is.
-- Apply on a Neon branch first (CLAUDE.md), then main. Idempotent.

-- ---------------------------------------------------------------- discogs-stream tables (verbatim shapes)
create table if not exists youtube_videos (
  id uuid default gen_random_uuid() primary key,
  artist text not null,
  title text not null,
  video_id text not null,
  channel_title text,
  thumbnail text,
  duration_iso text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(artist, title)
);
create index if not exists idx_youtube_videos_artist_title on youtube_videos(artist, title);

create table if not exists search_cache (
  id uuid primary key default gen_random_uuid(),
  query text not null,
  page_token text,
  results jsonb not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
create index if not exists idx_search_cache_query_token on search_cache(query, page_token);

create table if not exists track_media_links (
  id uuid default gen_random_uuid() primary key,
  discogs_username text not null,
  discogs_release_id integer not null,
  track_position text not null,
  track_title text,
  artist text,
  album text,
  provider text not null check (provider in ('youtube', 'bandcamp')),
  youtube_id text,
  bandcamp_embed_src text,
  bandcamp_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(discogs_username, discogs_release_id, track_position, provider)
);

create table if not exists release_cover_art (
  release_id bigint primary key,
  cover_url text,
  thumb_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists discogs_track_cache (
  id uuid primary key default gen_random_uuid(),
  owner_key text not null,
  source text not null check (source in ('collection', 'wantlist', 'similar')),
  track_id text not null,
  release_id bigint,
  track_position text,
  artist text not null,
  title text not null,
  album text,
  genre text,
  label text,
  year integer,
  country text,
  cover1 text, cover2 text, cover3 text, cover4 text,
  youtube1 text, youtube2 text,
  working_status text not null default 'pending' check (working_status in ('working', 'non_working', 'pending')),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(owner_key, track_id)
);
create index if not exists idx_discogs_track_cache_owner_source on discogs_track_cache(owner_key, source);
create index if not exists idx_discogs_track_cache_owner_release on discogs_track_cache(owner_key, release_id);

-- Server-only. Never readable from a client role; the Discogs token stays here.
create table if not exists user_tokens (
  username text primary key,
  discogs_token text not null,
  discogs_secret text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_sync_at timestamptz,
  last_rescan_at timestamptz
);
revoke all on user_tokens from public;

create table if not exists rescan_log (
  id bigserial primary key,
  ran_at timestamptz not null default now(),
  tracks_checked integer not null default 0,
  links_updated integer not null default 0,
  status_flipped_working integer not null default 0,
  status_flipped_non_working integer not null default 0,
  errors integer not null default 0,
  note text
);

create table if not exists track_preferences (
  id uuid not null default gen_random_uuid() primary key,
  owner_id text not null,
  track_id text not null,
  artist text not null,
  title text not null,
  album text,
  cover_url text,
  source text,
  preference text not null check (preference in ('liked', 'disliked')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, track_id)
);

-- ---------------------------------------------------------------- collection backups: 4 rolling slots per owner
create table if not exists collection_backups (
  id uuid primary key default gen_random_uuid(),
  owner_id text not null,
  label text not null,
  kind text not null check (kind in ('manual', 'import', 'restore', 'reset')),
  record_count integer not null default 0,
  unit_count integer not null default 0,
  snapshot jsonb not null,            -- the same shape the prototype saves to localStorage (units, records, playlists, gigs, settings)
  created_at timestamptz not null default now()
);
create index if not exists idx_collection_backups_owner_at on collection_backups(owner_id, created_at desc);

-- keep only the newest 4 per owner (the prototype's BK_MAX)
create or replace function trim_collection_backups() returns trigger language plpgsql as $$
begin
  delete from collection_backups
   where owner_id = new.owner_id
     and id not in (select id from collection_backups where owner_id = new.owner_id order by created_at desc limit 4);
  return null;
end $$;
drop trigger if exists trg_trim_collection_backups on collection_backups;
create trigger trg_trim_collection_backups after insert on collection_backups
  for each row execute function trim_collection_backups();

-- every import (Discogs API, Discogs CSV export, or a saved Crates file) is logged; a backup row is written first
create table if not exists collection_imports (
  id uuid primary key default gen_random_uuid(),
  owner_id text not null,
  source text not null check (source in ('discogs_api', 'discogs_csv', 'crates_file', 'demo')),
  label text,
  added integer not null default 0,
  skipped integer not null default 0,
  backup_id uuid references collection_backups(id) on delete set null,
  created_at timestamptz not null default now()
);

-- uploads to the Discogs collection ride the existing sync queue: kind 'add' = POST .../collection/folders/1/releases/{release_id}
alter table discogs_sync_queue add column if not exists kind text not null default 'location' check (kind in ('location', 'add'));

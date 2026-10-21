-- 006: the Discogs collection sync that api/sync.js writes and api/collection.js reads.
-- One row per release in the owner's Discogs collection, with the slice of the release we keep
-- (metadata, image urls, tracklist, YouTube links). Image bytes are never stored: the client loads them
-- through api/img.js, which caches on the CDN for 6 hours (Discogs terms: data no older than 6 hours).

create table if not exists discogs_releases (
  owner_key    text not null,                 -- the Discogs username
  release_id   bigint not null,
  instance_id  bigint,                        -- collection instance (needed to write the Location field)
  folder_id    integer,
  date_added   timestamptz,
  data         jsonb not null default '{}',   -- shapeRelease() in api/_lib.js: title, artists, labels, year, cover, label_art, images...
  tracklist    jsonb not null default '[]',
  videos       jsonb not null default '[]',   -- [{id, title, duration, from: 'release' | 'master' | 'version:<id>' | 'search'}]
  master_id    bigint,
  listed_at    timestamptz not null default now(),   -- last seen in the collection listing
  enriched_at  timestamptz,                          -- last full /releases/{id} fetch
  removed_at   timestamptz,                          -- no longer in the collection
  primary key (owner_key, release_id)
);
create index if not exists idx_discogs_releases_enrich on discogs_releases(owner_key, enriched_at nulls first) where removed_at is null;

-- one row per owner: where the incremental sync is
create table if not exists discogs_sync_state (
  owner_key     text primary key,
  phase         text not null default 'idle' check (phase in ('idle', 'list', 'enrich', 'done', 'error')),
  page          integer not null default 0,
  pages         integer not null default 0,
  total         integer not null default 0,
  enriched      integer not null default 0,
  started_at    timestamptz,
  listed_at     timestamptz,                  -- when the listing last completed (the 6-hour freshness clock)
  finished_at   timestamptz,
  last_error    text,
  run_id        text
);

-- youtube_videos (005) keeps found links by artist + title; api/sync.js upserts the first working-looking link there too.

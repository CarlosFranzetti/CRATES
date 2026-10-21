// POST /api/sync?mode=check|run|full   Incremental Discogs collection sync into Neon (app/db/006_sync.sql).
// Each call does a bounded amount of Discogs work (about 20 requests, paced to the 60/min limit) and returns
// progress; the client calls again until `done`. Phases: list (collection pages) -> enrich (/releases/{id},
// plus master and version videos when the release lists fewer videos than tracks) -> done.
//   mode=check  only re-lists if the listing is older than 6 hours (the "check for updates at the beginning" path)
//   mode=run    continue whatever is pending
//   mode=full   force a re-list and re-enrich everything (refresh all art and links)
import { env, sql, json, discogs, ytId, shapeRelease, FRESH_MS } from './_lib.js';

const BUDGET = 20;            // Discogs requests per call
const PER_PAGE = 100;

export default async function handler(req, res) {
  if (req.method !== 'POST' && req.method !== 'GET') return json(res, 405, { error: 'POST only' });
  const e = env();
  if (!e.ok) return json(res, 503, { error: 'Not configured', missing: e.missing, hint: 'Add DISCOGS_TOKEN, DISCOGS_USERNAME and DATABASE_URL in Vercel → Settings → Environment Variables.' });
  const url = new URL(req.url, 'http://x');
  const mode = url.searchParams.get('mode') || 'run';
  const db = sql();
  const owner = e.user;
  await db`insert into discogs_sync_state (owner_key) values (${owner}) on conflict do nothing`;
  let [st] = await db`select * from discogs_sync_state where owner_key = ${owner}`;
  let budget = BUDGET;
  const log = [];

  try {
    // decide whether to (re)start
    const stale = !st.listed_at || Date.now() - new Date(st.listed_at).getTime() > FRESH_MS;
    if (mode === 'full' || (st.phase === 'idle' || st.phase === 'done' || st.phase === 'error') && (mode === 'run' || stale)) {
      if (mode === 'full') await db`update discogs_releases set enriched_at = null where owner_key = ${owner}`;
      st = (await db`update discogs_sync_state set phase = 'list', page = 0, pages = 0, total = 0, enriched = 0, started_at = now(), finished_at = null, last_error = null, run_id = ${Date.now().toString(36)} where owner_key = ${owner} returning *`)[0];
      log.push('listing the collection');
    }
    if (mode === 'check' && !stale && st.phase === 'done') {
      const [c] = await db`select count(*)::int as n from discogs_releases where owner_key = ${owner} and removed_at is null`;
      return json(res, 200, { done: true, fresh: true, phase: 'done', total: c.n, listed_at: st.listed_at, finished_at: st.finished_at });
    }

    // ---- phase: list
    if (st.phase === 'list') {
      while (budget > 0) {
        const page = st.page + 1;
        const data = await discogs(`/users/${encodeURIComponent(owner)}/collection/folders/0/releases?page=${page}&per_page=${PER_PAGE}&sort=added&sort_order=desc`, e);
        budget--;
        const pages = data.pagination.pages, total = data.pagination.items;
        for (const it of data.releases) {
          const b = it.basic_information || {};
          const lite = { release_id: it.id, title: b.title, artists: (b.artists || []).map(a => a.name.replace(/\s\(\d+\)$/, '')).join(', '),
            labels: (b.labels || []).map(l => ({ name: l.name.replace(/\s\(\d+\)$/, ''), catno: l.catno })), year: b.year || null,
            genres: b.genres || [], styles: b.styles || [], formats: (b.formats || []).map(f => [f.name, ...(f.descriptions || [])].join(' ')),
            cover: b.cover_image || null, thumb: b.thumb || null, master_id: b.master_id || null };
          await db`insert into discogs_releases (owner_key, release_id, instance_id, folder_id, date_added, data, master_id, listed_at, removed_at)
            values (${owner}, ${it.id}, ${it.instance_id}, ${it.folder_id}, ${it.date_added}, ${JSON.stringify(lite)}, ${b.master_id || null}, now(), null)
            on conflict (owner_key, release_id) do update set instance_id = excluded.instance_id, folder_id = excluded.folder_id, date_added = excluded.date_added,
              data = case when discogs_releases.enriched_at is null then excluded.data else discogs_releases.data || jsonb_build_object('cover', excluded.data->'cover', 'thumb', excluded.data->'thumb') end,
              listed_at = now(), removed_at = null`;
        }
        st = (await db`update discogs_sync_state set page = ${page}, pages = ${pages}, total = ${total} where owner_key = ${owner} returning *`)[0];
        log.push(`page ${page} of ${pages}`);
        if (page >= pages) {
          // anything not seen in this run has left the collection
          await db`update discogs_releases set removed_at = now() where owner_key = ${owner} and removed_at is null and listed_at < ${st.started_at}`;
          st = (await db`update discogs_sync_state set phase = 'enrich', listed_at = now() where owner_key = ${owner} returning *`)[0];
          break;
        }
      }
    }

    // ---- phase: enrich (full release, then more videos from the master and sibling versions if the release is short on them)
    if (st.phase === 'enrich') {
      while (budget > 0) {
        const [row] = await db`select release_id, master_id from discogs_releases where owner_key = ${owner} and removed_at is null and enriched_at is null order by date_added desc nulls last limit 1`;
        if (!row) { st = (await db`update discogs_sync_state set phase = 'done', finished_at = now() where owner_key = ${owner} returning *`)[0]; break; }
        let rel; try { rel = await discogs(`/releases/${row.release_id}`, e); budget--; }
        catch (err) { budget--; if (err.status === 404) { await db`update discogs_releases set enriched_at = now(), removed_at = now() where owner_key = ${owner} and release_id = ${row.release_id}`; continue; } throw err; }
        const shaped = shapeRelease(rel);
        const seen = new Set(shaped.videos.map(v => v.id));
        const need = shaped.tracklist.length || 1;
        // more places: the master's videos, then up to 3 other versions of the master
        if (shaped.videos.length < need && shaped.master_id && budget > 0) {
          try { const m = await discogs(`/masters/${shaped.master_id}`, e); budget--;
            for (const v of m.videos || []) { const id = ytId(v.uri); if (id && !seen.has(id)) { seen.add(id); shaped.videos.push({ id, title: v.title, duration: v.duration || 0, from: 'master' }); } }
          } catch { budget--; }
        }
        if (shaped.videos.length < need && shaped.master_id && budget > 1) {
          try { const vs = await discogs(`/masters/${shaped.master_id}/versions?per_page=8`, e); budget--;
            const others = (vs.versions || []).filter(v => v.id !== shaped.release_id).slice(0, 3);
            for (const v of others) { if (budget <= 0 || shaped.videos.length >= need) break;
              try { const r2 = await discogs(`/releases/${v.id}`, e); budget--;
                for (const vid of r2.videos || []) { const id = ytId(vid.uri); if (id && !seen.has(id)) { seen.add(id); shaped.videos.push({ id, title: vid.title, duration: vid.duration || 0, from: 'version:' + v.id }); } }
              } catch { budget--; } }
          } catch { budget--; }
        }
        await db`update discogs_releases set data = ${JSON.stringify(shaped)}, tracklist = ${JSON.stringify(shaped.tracklist)}, videos = ${JSON.stringify(shaped.videos)}, master_id = ${shaped.master_id}, enriched_at = now() where owner_key = ${owner} and release_id = ${row.release_id}`;
        if (shaped.videos[0]) await db`insert into youtube_videos (artist, title, video_id, duration_iso) values (${shaped.artists}, ${shaped.title}, ${shaped.videos[0].id}, ${String(shaped.videos[0].duration || '')}) on conflict (artist, title) do update set video_id = excluded.video_id, updated_at = now()`;
        st = (await db`update discogs_sync_state set enriched = enriched + 1 where owner_key = ${owner} returning *`)[0];
        log.push(`${shaped.artists} – ${shaped.title}: ${shaped.tracklist.length} tracks, ${shaped.videos.length} links`);
      }
    }

    const [left] = await db`select count(*)::int as n from discogs_releases where owner_key = ${owner} and removed_at is null and enriched_at is null`;
    return json(res, 200, { done: st.phase === 'done', phase: st.phase, page: st.page, pages: st.pages, total: st.total, enriched: st.enriched, left: left.n, listed_at: st.listed_at, finished_at: st.finished_at, log });
  } catch (err) {
    await db`update discogs_sync_state set phase = 'error', last_error = ${String(err.message || err)} where owner_key = ${owner}`;
    return json(res, err.status === 401 ? 401 : 502, { error: String(err.message || err), phase: 'error', log });
  }
}

// GET /api/collection            the synced Discogs collection, shaped for the app (covers and label art via /api/img)
// GET /api/collection?ping=1     is the API configured? (no Discogs call, no database call)
// GET /api/collection?check=1    cheap freshness check: counts and timestamps only
import { env, sql, json, proxied, FRESH_MS } from './_lib.js';

export default async function handler(req, res) {
  const e = env();
  const url = new URL(req.url, 'http://x');
  if (url.searchParams.get('ping')) return json(res, e.ok ? 200 : 503, { ok: e.ok, missing: e.missing, user: e.ok ? e.user : null, version: '0.8b' });
  if (!e.ok) return json(res, 503, { error: 'Not configured', missing: e.missing });
  const db = sql();
  const owner = e.user;
  const [st] = await db`select * from discogs_sync_state where owner_key = ${owner}`;
  const [c] = await db`select count(*)::int as n, max(date_added) as newest, max(enriched_at) as enriched from discogs_releases where owner_key = ${owner} and removed_at is null`;
  const fresh = !!(st?.listed_at && Date.now() - new Date(st.listed_at).getTime() < FRESH_MS);
  const meta = { user: owner, total: c.n, newest: c.newest, enriched_at: c.enriched, listed_at: st?.listed_at || null, phase: st?.phase || 'idle', fresh };
  if (url.searchParams.get('check')) return json(res, 200, meta);

  const rows = await db`select release_id, instance_id, folder_id, date_added, data, tracklist, videos, enriched_at from discogs_releases where owner_key = ${owner} and removed_at is null order by date_added desc nulls last`;
  const records = rows.map(r => {
    const d = r.data || {};
    return {
      releaseId: r.release_id, instanceId: r.instance_id, folderId: r.folder_id, dateAdded: r.date_added,
      artist: d.artists || '', title: d.title || '', label: d.labels?.[0]?.name || '', catno: d.labels?.[0]?.catno || '',
      year: d.year || '', style: (d.styles || [])[0] || (d.genres || [])[0] || '', genres: d.genres || [], styles: d.styles || [],
      formats: d.formats || [], country: d.country || null, barcode: d.barcode || '',
      cover: proxied(d.cover), thumb: proxied(d.thumb), labelArt: proxied(d.label_art) || proxied(d.cover),
      tracks: r.tracklist || [], yt: (r.videos || []).map(v => v.id), videos: r.videos || [],
      enriched: !!r.enriched_at, discogsUrl: d.uri ? 'https://www.discogs.com' + d.uri : `https://www.discogs.com/release/${r.release_id}`,
    };
  });
  return json(res, 200, { ...meta, records }, { 'Cache-Control': 'private, max-age=60' });
}

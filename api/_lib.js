// Shared helpers for the Crates API (Vercel Node functions).
// Secrets live in Vercel env vars only: DISCOGS_TOKEN, DISCOGS_USERNAME, DATABASE_URL (optional YOUTUBE_API_KEY).
import { neon } from '@neondatabase/serverless';

export const UA = 'Crates/0.8b +https://crates-livid.vercel.app';
export const FRESH_MS = 6 * 60 * 60 * 1000;          // Discogs terms: data no older than 6 hours
const GAP_MS = 1100;                                   // 60 requests a minute, authenticated

export function env() {
  const missing = ['DISCOGS_TOKEN', 'DISCOGS_USERNAME', 'DATABASE_URL'].filter(k => !process.env[k]);
  return { ok: !missing.length, missing, token: process.env.DISCOGS_TOKEN, user: process.env.DISCOGS_USERNAME, db: process.env.DATABASE_URL };
}

export function sql() { return neon(process.env.DATABASE_URL); }

export function json(res, status, body, extra = {}) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  for (const [k, v] of Object.entries(extra)) res.setHeader(k, v);
  res.end(JSON.stringify(body));
}

let lastCall = 0;
/** One paced Discogs request. Throws {status} on HTTP errors; retries once on 429 after the window. */
export async function discogs(path, { token } = env(), attempt = 0) {
  const wait = lastCall + GAP_MS - Date.now();
  if (wait > 0) await new Promise(r => setTimeout(r, wait));
  lastCall = Date.now();
  const r = await fetch('https://api.discogs.com' + path, {
    headers: { 'User-Agent': UA, 'Authorization': `Discogs token=${token}`, 'Accept': 'application/vnd.discogs.v2.discogs+json' },
  });
  if (r.status === 429 && attempt < 1) { await new Promise(x => setTimeout(x, 61000 - (Date.now() - lastCall))); return discogs(path, { token }, attempt + 1); }
  if (!r.ok) { const e = new Error(`Discogs ${r.status} for ${path}`); e.status = r.status; throw e; }
  return r.json();
}

/** YouTube id from a Discogs video uri. */
export function ytId(uri) {
  const m = String(uri || '').match(/(?:v=|youtu\.be\/|\/embed\/)([A-Za-z0-9_-]{11})/);
  return m ? m[1] : null;
}

/** Rewrite a Discogs image url to go through our proxy (cached on the CDN for 6 hours, sent with our User-Agent). */
export function proxied(url) {
  if (!url) return null;
  try { const u = new URL(url); if (!/(^|\.)discogs\.com$/.test(u.hostname)) return null; } catch { return null; }
  return '/api/img?u=' + encodeURIComponent(url);
}

/** The slice of a Discogs release we keep (no image bytes; urls only, refreshed within the 6-hour window). */
export function shapeRelease(rel) {
  const images = (rel.images || []).map(i => ({ type: i.type, uri: i.uri, uri150: i.uri150, w: i.width, h: i.height }));
  const cover = images.find(i => i.type === 'primary') || images[0] || null;
  // The label scan is usually a later secondary image that is roughly square; fall back to the second image.
  const secondary = images.filter(i => i !== cover);
  const label = secondary.find(i => i.w && i.h && Math.abs(i.w / i.h - 1) < 0.12 && secondary.indexOf(i) > 0) || secondary[0] || null;
  return {
    release_id: rel.id,
    master_id: rel.master_id || null,
    title: rel.title,
    artists: (rel.artists || []).map(a => a.name.replace(/\s\(\d+\)$/, '')).join(', '),
    labels: (rel.labels || []).map(l => ({ name: l.name.replace(/\s\(\d+\)$/, ''), catno: l.catno })),
    year: rel.year || null,
    country: rel.country || null,
    genres: rel.genres || [],
    styles: rel.styles || [],
    formats: (rel.formats || []).map(f => [f.name, ...(f.descriptions || [])].join(' ')),
    cover: cover ? cover.uri : null,
    thumb: cover ? cover.uri150 : null,
    label_art: label ? label.uri : null,
    images,
    tracklist: (rel.tracklist || []).filter(t => t.type_ === 'track' || !t.type_).map(t => ({ position: t.position, title: t.title, duration: t.duration || '' })),
    videos: (rel.videos || []).map(v => ({ id: ytId(v.uri), title: v.title, duration: v.duration || 0, from: 'release' })).filter(v => v.id),
    barcode: (rel.identifiers || []).find(i => i.type === 'Barcode')?.value || null,
    uri: rel.uri || null,
  };
}

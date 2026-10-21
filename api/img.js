// GET /api/img?u=<https://i.discogs.com/...>   Image proxy for Discogs covers and label scans.
// Fetches with our User-Agent and caches on Vercel's CDN for 6 hours (Discogs terms), so the app can preload
// art without storing image bytes anywhere. Only discogs.com hosts are allowed.
import { UA } from './_lib.js';

export default async function handler(req, res) {
  const url = new URL(req.url, 'http://x');
  const u = url.searchParams.get('u') || '';
  let target;
  try { target = new URL(u); } catch { res.statusCode = 400; return res.end('bad url'); }
  if (!/(^|\.)discogs\.com$/.test(target.hostname) || target.protocol !== 'https:') { res.statusCode = 403; return res.end('host not allowed'); }
  const r = await fetch(target, { headers: { 'User-Agent': UA, 'Accept': 'image/*' } });
  if (!r.ok) { res.statusCode = r.status; res.setHeader('Cache-Control', 'public, s-maxage=300'); return res.end(''); }
  const type = r.headers.get('content-type') || 'image/jpeg';
  if (!type.startsWith('image/')) { res.statusCode = 415; return res.end(''); }
  const buf = Buffer.from(await r.arrayBuffer());
  res.statusCode = 200;
  res.setHeader('Content-Type', type);
  res.setHeader('Content-Length', String(buf.length));
  res.setHeader('Cache-Control', 'public, max-age=3600, s-maxage=21600, stale-while-revalidate=86400');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.end(buf);
}

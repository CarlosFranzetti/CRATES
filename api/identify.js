// POST /api/identify   body: {image: "data:image/jpeg;base64,...", barcode?: "digits"}
// Reads a record cover (or label, or back) and finds Discogs releases for it.
//   1. barcode given  -> Discogs barcode search first (cheapest, exact)
//   2. otherwise      -> Anthropic Messages API reads artist / title / label / catalogue number from the image,
//                        then a Discogs search returns up to 5 candidates.
// Env: ANTHROPIC_API_KEY (required), ANTHROPIC_MODEL (the model id to use; confirm the id and its pricing before relying on it),
//      DISCOGS_TOKEN (optional here: without it only the model's reading comes back, no candidates).
// Replies 200 {guess:{artist,title,label,catno,confidence}|null, candidates:[{releaseId,artist,title,label,catno,year,thumb}]},
//         503 {error:'Not configured', missing:[...]} when ANTHROPIC_API_KEY is absent.
// The image is sent to Anthropic and is not stored or logged here.
import { json, discogs, proxied } from './_lib.js';

const MAX_IMAGE = 4_200_000;   // bytes of base64 (Vercel's request limit is 4.5 MB)
const DEFAULT_MODEL = 'claude-sonnet-4-5';

const SYSTEM = 'You read photographs of vinyl record sleeves, centre labels and sleeve backs for a DJ cataloguing app. '
  + 'Reply with ONLY one JSON object: {"artist":string|null,"title":string|null,"label":string|null,"catno":string|null,"confidence":"high"|"medium"|"low"}. '
  + 'Copy text exactly as printed. Use null for anything you cannot read. Never guess or invent a record you cannot read. No prose, no code fences.';

const clean = (x, n = 200) => (typeof x === 'string' || typeof x === 'number') ? String(x).trim().slice(0, n) : '';

async function readBody(req) {
  if (req.body && typeof req.body === 'object' && !Buffer.isBuffer(req.body)) return req.body;
  if (typeof req.body === 'string') return JSON.parse(req.body);
  const chunks = []; let size = 0;
  for await (const c of req) { size += c.length; if (size > MAX_IMAGE + 1000) throw Object.assign(new Error('too large'), { status: 413 }); chunks.push(c); }
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
}

function shapeResult(x) {
  const [artist, ...rest] = String(x.title || '').split(' - ');
  return {
    releaseId: Number.isInteger(x.id) ? x.id : null,
    artist: clean(rest.length ? artist.replace(/\s\(\d+\)$/, '') : ''),
    title: clean(rest.length ? rest.join(' - ') : x.title),
    label: clean((x.label || [])[0]),
    catno: clean(x.catno, 60),
    year: clean(x.year, 4),
    thumb: proxied(x.thumb || x.cover_image),
  };
}

async function search(params) {
  try {
    const q = new URLSearchParams({ type: 'release', per_page: '8', ...params });
    const r = await discogs('/database/search?' + q.toString());
    return (r.results || []).slice(0, 5).map(shapeResult).filter(c => c.releaseId);
  } catch { return []; }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return json(res, 405, { error: 'POST only' });
  // Only our own pages may spend the model budget.
  const site = req.headers['sec-fetch-site'];
  if (site && site !== 'same-origin' && site !== 'none') return json(res, 403, { error: 'Same-origin requests only' });
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return json(res, 503, { error: 'Not configured', missing: ['ANTHROPIC_API_KEY'] });
  const haveDiscogs = !!process.env.DISCOGS_TOKEN;

  let body;
  try { body = await readBody(req); } catch (e) { return json(res, e.status || 400, { error: 'Bad request body' }); }
  const barcode = String(body.barcode || '').replace(/\D/g, '');
  const m = /^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$/.exec(String(body.image || ''));
  if (!m) return json(res, 400, { error: 'Send {image: "data:image/jpeg;base64,..."}' });
  if (m[2].length > MAX_IMAGE) return json(res, 413, { error: 'Image too large' });

  // 1. an exact barcode wins and costs nothing but a Discogs call
  if (barcode.length >= 8 && haveDiscogs) {
    const candidates = await search({ barcode });
    if (candidates.length) {
      const c = candidates[0];
      return json(res, 200, { guess: { artist: c.artist, title: c.title, label: c.label, catno: c.catno, confidence: 'high' }, candidates, via: 'barcode' });
    }
  }

  // 2. read the image
  let reading = null;
  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      body: JSON.stringify({
        model: process.env.ANTHROPIC_MODEL || DEFAULT_MODEL,
        max_tokens: 300,
        system: SYSTEM,
        messages: [{ role: 'user', content: [
          { type: 'image', source: { type: 'base64', media_type: m[1], data: m[2] } },
          { type: 'text', text: 'Which record is this? Reply with the JSON object only.' },
        ] }],
      }),
    });
    if (!r.ok) return json(res, 502, { error: 'The model request failed', status: r.status });
    const out = await r.json();
    const text = (out.content || []).filter(b => b.type === 'text').map(b => b.text).join('');
    const j = JSON.parse((/\{[\s\S]*\}/.exec(text) || ['{}'])[0]);
    reading = {
      artist: clean(j.artist), title: clean(j.title), label: clean(j.label), catno: clean(j.catno, 60),
      confidence: ['high', 'medium', 'low'].includes(j.confidence) ? j.confidence : 'low',
    };
  } catch {
    return json(res, 502, { error: 'Could not read the model reply' });
  }
  if (!reading.artist && !reading.title && !reading.catno) return json(res, 200, { guess: null, candidates: [] });

  // 3. Discogs candidates for what was read
  let candidates = [];
  if (haveDiscogs) {
    if (reading.catno) candidates = await search({ catno: reading.catno });
    if (!candidates.length && (reading.artist || reading.title)) {
      candidates = await search({ ...(reading.artist ? { artist: reading.artist } : {}), ...(reading.title ? { release_title: reading.title } : {}) });
    }
  }
  return json(res, 200, { guess: reading, candidates, via: 'model' });
}

// POST /api/remind   { digest: string, to?: string }
// Emails the lending digest ("who still has which record") to the owner through Resend's HTTP API.
// Needs two env vars in Vercel: RESEND_API_KEY and REMIND_EMAIL (optional RESEND_FROM, default Resend's test sender).
// Without them it answers 503 and names what is missing. It never sends on its own; the app calls it from a button.
// The recipient is always REMIND_EMAIL: a `to` in the body is accepted but only honoured if it equals REMIND_EMAIL,
// so the endpoint can't be used to mail other people. Secrets are never logged or echoed.
import { json } from './_lib.js';

const MAX_DIGEST = 20000;

export default async function handler(req, res) {
  if (req.method !== 'POST') return json(res, 405, { error: 'POST only' });
  const key = process.env.RESEND_API_KEY, owner = process.env.REMIND_EMAIL;
  const missing = ['RESEND_API_KEY', 'REMIND_EMAIL'].filter(k => !process.env[k]);
  if (missing.length) return json(res, 503, { error: 'Not configured', missing, hint: 'Add RESEND_API_KEY and REMIND_EMAIL in Vercel → Settings → Environment Variables.' });

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = null; } }
  if (!body || typeof body !== 'object') return json(res, 400, { error: 'Send JSON: { "digest": "..." }' });
  const digest = typeof body.digest === 'string' ? body.digest.trim() : '';
  if (!digest) return json(res, 400, { error: 'digest is required' });
  if (digest.length > MAX_DIGEST) return json(res, 413, { error: 'digest is too long' });
  if (typeof body.to === 'string' && body.to.trim() && body.to.trim().toLowerCase() !== owner.trim().toLowerCase()) {
    return json(res, 400, { error: 'to must be the address set in REMIND_EMAIL' });
  }

  try {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: process.env.RESEND_FROM || 'Crates <onboarding@resend.dev>',
        to: [owner.trim()],
        subject: 'Crates: records still out',
        text: digest,
      }),
    });
    if (!r.ok) return json(res, 502, { error: `Email service answered ${r.status}` });
    return json(res, 200, { ok: true });
  } catch {
    return json(res, 502, { error: 'Could not reach the email service' });
  }
}

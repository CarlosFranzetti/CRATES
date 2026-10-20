// Wraps the single-file prototype (crates.html is page content without <html>/<head>/<body>)
// into a full document at dist/index.html for static hosting on Vercel.
import { readFileSync, writeFileSync, mkdirSync, cpSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';

let body = readFileSync('crates.html', 'utf8');
// Lift <title> and claude:* meta tags out of the page content into <head>.
const title = (body.match(/<title>[\s\S]*?<\/title>/) || ['<title>Crates</title>'])[0];
body = body.replace(/<title>[\s\S]*?<\/title>\s*/, '').replace(/<meta name="claude:[^>]*>\s*/g, '');
const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
${title}
<meta name="description" content="Crates, a vinyl DJ librarian: know which shelf, crate or bag every record is in, play it, and pack it for the gig.">
<meta name="theme-color" content="#E8EBED" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1113" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/logos/mark-3.svg" type="image/svg+xml">
<!-- Vercel Web Analytics + Speed Insights (plain-HTML setup; served from this site's /_vercel path) -->
<script>window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };</script>
<script defer src="/_vercel/insights/script.js"></script>
<script>window.si = window.si || function () { (window.siq = window.siq || []).push(arguments); };</script>
<script defer src="/_vercel/speed-insights/script.js"></script>
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}[hidden]{display:none!important}img{max-width:100%}</style>
</head>
<body>
${body}
</body>
</html>
`;
// Defence in depth: a meta CSP that allows only these exact inline scripts (by hash) plus the known script hosts.
// The header CSP in vercel.json keeps 'unsafe-inline' for the claude.ai preview; both policies apply, so on the
// deployed site an injected inline handler (onerror=, onclick=) is blocked even if a string ever slips past esc().
const hashes = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => `'sha256-${createHash('sha256').update(m[1], 'utf8').digest('base64')}'`);
const csp = `script-src 'self' ${hashes.join(' ')} https://www.youtube.com https://s.ytimg.com https://cdn.jsdelivr.net; object-src 'none'; base-uri 'self'`;
const out = html.replace('<meta charset="utf-8">', `<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="${csp}">`);
mkdirSync('dist', { recursive: true });
writeFileSync('dist/index.html', out);
if (existsSync('logos')) cpSync('logos', 'dist/logos', { recursive: true });
console.log('dist/index.html written');

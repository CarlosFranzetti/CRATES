// Wraps the single-file prototype (crates.html is page content without <html>/<head>/<body>)
// into a full document at dist/index.html for static hosting on Vercel.
import { readFileSync, writeFileSync, mkdirSync, cpSync, existsSync } from 'node:fs';

const body = readFileSync('crates.html', 'utf8');
const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
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
mkdirSync('dist', { recursive: true });
writeFileSync('dist/index.html', html);
if (existsSync('logos')) cpSync('logos', 'dist/logos', { recursive: true });
console.log('dist/index.html written');

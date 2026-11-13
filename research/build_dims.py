#!/usr/bin/env python3
"""Rewrites the /*DIMS_START*/…/*DIMS_END*/ block in crates.html from research/dimensions.json.
Maps bag and crate presets to their real outer width and height in cm so the room map is true to size."""
import json, re, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
html = (root / 'crates.html').read_text()
dims = json.loads((root / 'research' / 'dimensions.json').read_text())
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', re.sub(r'\([^)]*\)', '', s.lower())).strip('-')
keys = set(re.findall(r'"key":"([^"]+)"', html)) | set(re.findall(r"key:'([^']+)'", html))
out, miss = {}, []
for b in dims['bags']:
    if not b.get('w_cm') or not b.get('h_cm'): continue
    k = slug(b['brand'] + ' ' + b['model'])
    hit = k if k in keys else next((x for x in keys if x.startswith(k) or k.startswith(x)), None)
    if hit: out[hit] = [b['w_cm'], b['h_cm']]
    else: miss.append(k)
block = "/*DIMS_START*/\nconst DIMS = %s;\n/*DIMS_END*/" % json.dumps(out, separators=(',', ':'), sort_keys=True)
if '/*DIMS_START*/' in html:
    html = re.sub(r'/\*DIMS_START\*/.*?/\*DIMS_END\*/', lambda m: block, html, flags=re.S)
else:
    html = html.replace('function plateSize(u){', block + '\nfunction plateSize(u){', 1)
(root / 'crates.html').write_text(html)
print(len(out), 'presets sized;', len(miss), 'unmatched:', miss[:12])

"""Turn research JSON into the PRESETS block of crates.html."""
import json, re, sys, os

HERE = os.path.dirname(__file__)
PAGE = os.path.join(HERE, '..', 'crates.html')

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:48]

def cap_short(c):
    if not c: return 'Capacity not listed'
    s = str(c)
    if re.search(r'7["”]|7-inch', s) and '12' not in s:
        m = re.search(r'(\d+)', s); return f'~{m.group(1)} 7" singles' if m else s
    m = re.search(r'(\d+)\s*(?:-|–)\s*(\d+)', s)
    if m: return f'~{m.group(1)}–{m.group(2)} LPs'
    m = re.search(r'(\d+)', s)
    return f'~{m.group(1)} LPs' if m else 'Capacity not listed'

def hexok(h):
    return h if re.fullmatch(r'#[0-9a-fA-F]{6}', h or '') else '#1c1c1e'

def clean_color_name(n):
    return re.sub(r'\s*\((?:inferred|on request|unspecified)[^)]*\)', '', n).strip() or 'Default'

# ---------------- bags ----------------
bags_src = json.load(open(os.path.join(HERE, 'bags.json')))
SKIP_BAGS = ('beatles', 'urbanite', 'midi controller')
bags = []
for b in bags_src:
    name = b['model']
    if any(k in name.lower() for k in SKIP_BAGS): continue
    form = b.get('form','').lower()
    f = ('trolley' if 'trolley' in form else 'sling' if 'sling' in form else 'backpack' if 'backpack' in form
         else 'tote' if 'tote' in form else 'case' if 'case' in form else 'shoulder')
    mat = (b.get('material') or '').lower()
    texture = ('canvas' if ('canvas' in mat or 'carpet' in mat) else
               'metal' if (f == 'case' and ('alumin' in mat or 'laminate' in mat or 'flight' in form)) else
               'board' if f == 'case' else 'nylon')
    display = re.sub(r'\s*\((?:U\d|MGA|AMS|G-ONYX|\d{4,}|CR4|LP100)[^)]*\)', '', name).strip()
    colors, seen = [], set()
    for c in b.get('colors', []):
        n = clean_color_name(c['name'])
        if n in seen: continue
        seen.add(n); colors.append({'name': n, 'hex': hexok(c['hex'])})
    if not colors: colors = [{'name': 'Black', 'hex': '#1c1c1e'}]
    brand = b['brand'].replace(' (Technics licensed)', '')
    bags.append({'key': slug(brand + ' ' + display), 'brand': brand, 'name': display, 'form': f,
                 'texture': texture, 'cap': cap_short(b.get('capacity')), 'colors': colors,
                 'conf': b.get('confidence', 'low'), 'src': b.get('sourceUrl', '')})

# ---------------- furniture ----------------
fpath = os.path.join(HERE, 'furniture.json')
furn = []
if os.path.exists(fpath):
    DROP = ('billy', 'lp-bag', 'sandwich bag', 'kolbjorn', 'lixhult')
    MILK_EXTRA = [{'name':'Red','hex':'#C8322B'},{'name':'Yellow','hex':'#E8B921'},{'name':'Orange','hex':'#E86A1C'},{'name':'White','hex':'#E9E9E6'},{'name':'Purple','hex':'#5B3A8C'},{'name':'Pink','hex':'#E35D9B'}]
    for x in json.load(open(fpath)):
        cat = (x.get('category') or '').lower()
        brand, model = x.get('brand', ''), x.get('model', '')
        if any(d in model.lower() for d in DROP): continue
        unknown_grid = not isinstance(x.get('rows'), int) or not isinstance(x.get('cols'), int)
        if brand.upper() == 'IKEA':
            m = re.match(r'([A-ZÅÄÖ]+)\s*(.*)', model)
            if m:
                rest = m.group(2)
                dims = re.search(r'\(([\dx.]+\s*cm)\)', rest)
                rest = re.sub(r'\s*\([^)]*cm\)', '', rest).replace('x', '×') if re.match(r'\d', rest) else re.sub(r'\s*\([^)]*cm\)', '', rest)
                model = (m.group(1).capitalize() + ' ' + rest).strip() + (' · ' + dims.group(1).replace('x', '×') if dims else '')
        rows, cols = x.get('rows') or 1, x.get('cols') or 1
        try: rows, cols = int(rows), int(cols)
        except Exception: rows, cols = 1, 1
        low = (brand + ' ' + model).lower()
        if cat in ('shelf-grid', 'shelf', 'grid', 'cube'):
            kind, style = 'shelf', 'cube'
        elif cat in ('wall', 'ledge'):
            kind, style = 'shelf', 'ledge'
        elif cat in ('bin', 'browser'):
            kind, style = 'shelf', 'bin'
        elif cat == 'crate':
            kind = 'crate'; style = 'milk' if 'milk' in low else 'wood'
        else:  # box | case | other
            kind, style = 'crate', 'case'
        if kind == 'shelf' and unknown_grid: rows, cols = 1, 2
        if kind == 'shelf' and rows * cols > 36: rows, cols = min(rows, 6), min(cols, 6)
        group = ('IKEA Kallax' if 'kallax' in low else 'IKEA (other)' if brand.upper() == 'IKEA'
                 else 'Crates' if kind == 'crate' and style in ('milk', 'wood') else 'Record boxes & cases' if kind == 'crate'
                 else 'Wall & bins' if style in ('ledge', 'bin') else 'Record furniture')
        fins, seen = [], set()
        for f in x.get('finishes') or []:
            n = clean_color_name(f.get('name', ''))
            if not n or n in seen: continue
            seen.add(n)
            fins.append({'name': n, 'hex': hexok(f.get('hex')),
                         **({'grain': 1} if re.search(r'oak|walnut|wood|ash|pine|birch|teak|veneer', n, re.I) else {}),
                         **({'gloss': 1} if 'gloss' in n.lower() else {})})
        if style == 'milk':
            for e in MILK_EXTRA:
                if e['name'] not in seen: fins.append(e); seen.add(e['name'])
        fins = [f for f in fins if not re.search(r'unspecified|names not listed|colors offered|finishes total|varies', f['name'], re.I)] or fins[:1]
        cap = x.get('capacityPerSlot') if kind == 'shelf' else x.get('capacityTotal')
        capt = cap_short(cap) + (' per cube' if kind == 'shelf' and style == 'cube' and cap_short(cap)[0] == '~' else '')
        furn.append({'key': slug(brand + ' ' + model), 'brand': brand, 'name': model, 'kind': kind, 'style': style,
                     'rows': rows if kind == 'shelf' else 1, 'cols': cols if kind == 'shelf' else 1,
                     'cap': capt + (' · set your own sections' if kind == 'shelf' and unknown_grid else ''), 'group': group, 'finishes': fins, 'conf': x.get('confidence', 'low'),
                     'src': x.get('sourceUrl', '')})
    furn.append({'key': 'custom-grid', 'brand': 'Custom', 'name': 'Custom grid', 'kind': 'shelf', 'style': 'cube',
                 'rows': 3, 'cols': 3, 'cap': 'Any rows × columns', 'group': 'Record furniture', 'custom': True,
                 'finishes': [], 'conf': 'high', 'src': ''})
    order = ['IKEA Kallax', 'IKEA (other)', 'Record furniture', 'Wall & bins', 'Crates', 'Record boxes & cases']
    furn.sort(key=lambda f: (order.index(f['group']) if f['group'] in order else 9, f['rows'] * f['cols']))
    # de-dupe keys
    seen = set()
    for f in furn:
        k = f['key']; i = 2
        while f['key'] in seen: f['key'] = f'{k}-{i}'; i += 1
        seen.add(f['key'])

print(f'bags: {len(bags)}  furniture: {len(furn)}', file=sys.stderr)
block = '/*PRESETS_START*/\nconst RESEARCH = ' + json.dumps({'bags': bags, 'furniture': furn}, ensure_ascii=False, separators=(',', ':')) + ';\n/*PRESETS_END*/'
page = open(PAGE).read()
page = re.sub(r'/\*PRESETS_START\*/.*?/\*PRESETS_END\*/', lambda m: block, page, flags=re.S)
open(PAGE, 'w').write(page)
print('written', file=sys.stderr)

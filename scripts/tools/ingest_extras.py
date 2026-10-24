#!/usr/bin/env python3
"""ingest_extras.py: move the "Site extras" downloads (from fetch_site_extras.py) into the map.

  python3 scripts/tools/ingest_extras.py "<staged Site extras folder>"

For every site folder found:
  rain_daily.json          -> map/sites/<id>/rain_daily.json  (Bright Tree: map/rain_daily.json)   30-year daily rain for the tank test
  regional_ecosystems.json -> map/sites/<id>/ecosystems.json  simplified polygons + the RE catalogue (description, VM Act status, biodiversity status)
  ala_species.json         -> map/sites/<id>/species.json     (when present) species seen within 1 km, grouped
  soil_grid.json           -> map/sites/<id>/soils.json       soil numbers by depth at the centre and on the 5 x 5 grid (Soil and Landscape Grid)
  ifd.json                 -> map/sites/<id>/ifd.json         design rainfall table (BoM, ARR 2019), copied as is
  silo_full.json           -> map/sites/<id>/silo_full.json   daily rain, temperatures, radiation, evaporation and ETo, copied as is
  geology.json             -> map/sites/<id>/geology.json     surface geology polygons, clipped to the map square and simplified
  hazard.json              -> map/sites/<id>/hazard.json      bushfire hazard and regulated-vegetation polygons, clipped and simplified

The RE catalogue below is copied from the Queensland Government Regional Ecosystem Description Database (REDD, version 13.1,
apps.des.qld.gov.au/regional-ecosystems) on 24 Oct 2026. Add a line when a new site brings a new code (the script lists any it lacks).
"""
import json, os, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPDIR = {'bright-tree': ROOT / 'map', 'bellbunya': ROOT / 'map/sites/bellbunya', 'noosa-forest-retreat': ROOT / 'map/sites/noosa-forest-retreat',
          'annwn': ROOT / 'map/sites/annwn', 'willow-vale': ROOT / 'map/sites/willow-vale', 'nimbin': ROOT / 'map/sites/nimbin', 'nac': ROOT / 'map/sites/nac'}

# code: (short description, VM Act status, biodiversity status)
REDD = {
 '12.3.1': ('Gallery rainforest (notophyll vine forest) on alluvial plains', 'Endangered', 'Endangered'),
 '12.3.2': ('Eucalyptus grandis (flooded gum) tall open forest on alluvial plains', 'Of concern', 'Of concern'),
 '12.3.4': ('Melaleuca quinquenervia and Eucalyptus robusta (swamp mahogany) woodland on coastal alluvium', 'Of concern', 'Of concern'),
 '12.3.6': ('Melaleuca quinquenervia (paperbark) open forest on coastal alluvial plains', 'Least concern', 'No concern at present'),
 '12.3.7': ('Eucalyptus tereticornis and Casuarina cunninghamiana fringing woodland along watercourses', 'Least concern', 'Of concern'),
 '12.3.11': ('Eucalyptus tereticornis (blue gum) open forest on coastal alluvial plains', 'Of concern', 'Of concern'),
 '12.5.3': ('Eucalyptus racemosa (scribbly gum) woodland on remnant Tertiary surfaces', 'Endangered', 'Endangered'),
 '12.8.8': ('Eucalyptus saligna or E. grandis tall open forest on Cainozoic igneous rocks', 'Of concern', 'Of concern'),
 '12.9-10.4': ('Eucalyptus racemosa (scribbly gum) woodland on sedimentary rocks', 'Least concern', 'No concern at present'),
 '12.9-10.14': ('Eucalyptus pilularis (blackbutt) tall open forest on sedimentary rocks', 'Least concern', 'No concern at present'),
 '12.9-10.16': ('Araucarian microphyll to notophyll vine forest (hoop pine rainforest) on sediments', 'Of concern', 'Of concern'),
 '12.9-10.17': ('Eucalyptus acmenoides, E. major, E. siderophloia (white mahogany, grey gum, ironbark) open forest on sedimentary rocks', 'Least concern', 'No concern at present'),
 '12.11.1': ('Simple notophyll vine forest (gully rainforest) on metamorphics', 'Least concern', 'No concern at present'),
 '12.11.2': ('Eucalyptus saligna or E. grandis, E. microcorys, Lophostemon confertus tall open forest on metamorphics', 'Least concern', 'No concern at present'),
 '12.11.3': ('Eucalyptus siderophloia, E. propinqua (ironbark, grey gum) open forest on metamorphics', 'Least concern', 'No concern at present'),
 '12.11.10': ('Notophyll vine forest, sometimes with Araucaria cunninghamii (hoop pine), on metamorphics', 'Least concern', 'No concern at present'),
 '12.11.16': ('Eucalyptus cloeziana (Gympie messmate) open forest on metamorphics', 'Endangered', 'Endangered'),
 '12.12.1': ('Gully vine forest (simple notophyll vine forest) on igneous rocks', 'Of concern', 'Of concern'),
 '12.12.12': ('Eucalyptus tereticornis (blue gum) woodland on Mesozoic to Proterozoic igneous rocks', 'Of concern', 'Of concern'),
 '12.12.15': ('Mixed open forest of Eucalyptus, Corymbia and Lophostemon on igneous rocks', 'Least concern', 'No concern at present'),
 '12.12.16': ('Notophyll vine forest (rainforest) on igneous rocks', 'Least concern', 'No concern at present'),
}
SPECIAL = {'non-rem': 'Non-remnant: cleared, regrowth younger than remnant status, or built on', 'water': 'Water', 'plantation': 'Plantation', 'ocean': 'Ocean', 'estuary': 'Estuary'}


def dp(pts, tol):
    """Douglas-Peucker line simplification on a closed ring (keeps the first point)."""
    if len(pts) < 5: return pts
    import math
    def seg_d(p, a, b):
        dx, dy = b[0]-a[0], b[1]-a[1]; L = dx*dx+dy*dy
        t = 0 if L == 0 else max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L))
        return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)
    def rec(a, b):
        if b - a < 2: return []
        i, m = max(((i, seg_d(pts[i], pts[a], pts[b])) for i in range(a+1, b)), key=lambda x: x[1])
        return rec(a, i) + [i] + rec(i, b) if m > tol else []
    # split the ring at its farthest point from pts[0] so the two halves simplify well
    far = max(range(1, len(pts)), key=lambda i: (pts[i][0]-pts[0][0])**2+(pts[i][1]-pts[0][1])**2)
    keep = sorted({0, far, len(pts)-1} | set(rec(0, far)) | set(rec(far, len(pts)-1)))
    return [pts[i] for i in keep]


def clip_rect(pts, lo=-100.0, hi=2100.0):
    """Sutherland-Hodgman: clip a ring to the map square (with a 100 m margin) so a huge polygon costs nothing off-map."""
    def clip(poly, inside, inter):
        out = []
        for i in range(len(poly)):
            cur, prev = poly[i], poly[i-1]
            if inside(cur):
                if not inside(prev): out.append(inter(prev, cur))
                out.append(cur)
            elif inside(prev): out.append(inter(prev, cur))
        return out
    def ix(a, b, x): t = (x-a[0])/(b[0]-a[0]); return [x, a[1]+t*(b[1]-a[1])]
    def iy(a, b, y): t = (y-a[1])/(b[1]-a[1]); return [a[0]+t*(b[0]-a[0]), y]
    for inside, inter in ((lambda p: p[0] >= lo, lambda a, b: ix(a, b, lo)), (lambda p: p[0] <= hi, lambda a, b: ix(a, b, hi)),
                          (lambda p: p[1] >= lo, lambda a, b: iy(a, b, lo)), (lambda p: p[1] <= hi, lambda a, b: iy(a, b, hi))):
        pts = clip(pts, inside, inter)
        if len(pts) < 3: return []
    return pts


def ecosystems(src, dst):
    j = json.load(open(src)); polys = []; codes = set(); missing = set()
    for f in j['features']:
        lab = f['attrs'].get('re_label') or '?'; pc = f['attrs'].get('pc_label') or ''
        rings = []
        for r in f['rings']:
            r = clip_rect(r)
            if len(r) >= 4: r = dp(r, 1.0)
            if len(r) >= 4: rings.append([[round(p[0], 1), round(p[1], 1)] for p in r])
        if not rings: continue
        for c in lab.split('/'):
            c = c.strip(); codes.add(c)
            if c not in REDD and c not in SPECIAL: missing.add(c)
        polys.append({'re': lab, 'pc': pc, 'rings': rings})
    cat = {c: {'d': REDD[c][0], 'vm': REDD[c][1], 'bd': REDD[c][2]} for c in codes if c in REDD}
    cat.update({c: {'d': SPECIAL[c], 'vm': '', 'bd': ''} for c in codes if c in SPECIAL})
    out = {'source': 'Queensland Herbarium regional ecosystem mapping (Vegetation Management Act map labels), State of Queensland, CC BY 4.0; downloaded ' + j.get('fetched', ''),
           'catalogue': 'Descriptions and status from the Regional Ecosystem Description Database (REDD) v13.1, remnant extent 2021',
           'cat': cat, 'polys': polys}
    json.dump(out, open(dst, 'w'), separators=(',', ':'))
    print(f'  ecosystems: {len(polys)} polygons, {len(cat)} types, {os.path.getsize(dst)//1024} kB' + (f'  MISSING from REDD table: {sorted(missing)}' if missing else ''))


def species(src, dst):
    j = json.load(open(src)); by = {}
    for name, e in j.get('species', {}).items():
        g = e.get('group') or 'Other'
        by.setdefault(g, []).append({'sci': name, 'common': e.get('common'), 'n': e.get('n', 0), 'last': e.get('last', ''), 'status': e.get('status')})
    for g in by: by[g].sort(key=lambda s: -s['n'])
    json.dump({'source': j.get('source', 'Atlas of Living Australia'), 'fetched': j.get('fetched'), 'total': j.get('total'), 'groups': by}, open(dst, 'w'), separators=(',', ':'))
    print(f'  species: {sum(len(v) for v in by.values())} species in {len(by)} groups')


def clip_feats(feats, tol=1.0):
    """Clip a list of {attrs, rings} features to the map square and simplify them, like the ecosystems layer."""
    out = []
    for f in feats:
        rings = []
        for r in f.get('rings', []):
            r = clip_rect(r)
            if len(r) >= 4: r = dp(r, tol)
            if len(r) >= 4: rings.append([[round(p[0], 1), round(p[1], 1)] for p in r])
        if rings: out.append({'attrs': f.get('attrs', {}), 'rings': rings})
    return out


def soils(src, dst):
    j = json.load(open(src))
    out = {'source': j['source'], 'fetched': j.get('fetched'), 'attrs': j['attrs'], 'depths_cm': j['depths_cm'], 'centre': j['centre'], 'grid_step_m': j.get('grid_step_m', 400), 'grid': j['grid']}
    json.dump(out, open(dst, 'w'), separators=(',', ':'))
    c = j['centre']; top = {k: v.get('0-5') for k, v in c.items() if isinstance(v, dict) and '0-5' in v}
    print(f"  soils: {len(c)} attributes at the centre (topsoil: {top}), {len(j['grid'])} grid points")


def geology(src, dst):
    j = json.load(open(src)); feats = clip_feats(j.get('features', []))
    json.dump({'source': j['source'], 'layer': j.get('layer'), 'fetched': j.get('fetched'), 'features': feats}, open(dst, 'w'), separators=(',', ':'))
    units = {}
    for f in feats:
        k = next((str(v) for kk, v in f['attrs'].items() if 'name' in kk.lower() or 'unit' in kk.lower()), '?'); units[k] = units.get(k, 0) + 1
    print(f"  geology: {len(feats)} polygons, {len(units)} rock units, {os.path.getsize(dst)//1024} kB")


def hazard(src, dst):
    j = json.load(open(src)); layers = []
    for l in j.get('layers', []):
        feats = clip_feats(l.get('features', []))
        layers.append({'kind': l['kind'], 'name': l.get('name'), 'source': l['source'], 'features': feats})
    json.dump({'fetched': j.get('fetched'), 'layers': layers}, open(dst, 'w'), separators=(',', ':'))
    print('  hazard: ' + ', '.join(f"{l['kind']} {len(l['features'])} polygons" for l in layers) + f", {os.path.getsize(dst)//1024} kB")


def main():
    root = Path(sys.argv[1])
    for site, mdir in MAPDIR.items():
        s = root / site
        if not s.is_dir(): continue
        print(site)
        if (s / 'rain_daily.json').exists():
            shutil.copy(s / 'rain_daily.json', mdir / 'rain_daily.json'); os.chmod(mdir / 'rain_daily.json', 0o644)
            r = json.load(open(s / 'rain_daily.json')); print(f"  rain: {r['start']} to {r['end']}")
        if (s / 'regional_ecosystems.json').exists(): ecosystems(s / 'regional_ecosystems.json', mdir / 'ecosystems.json')
        if (s / 'ala_species.json').exists(): species(s / 'ala_species.json', mdir / 'species.json')
        if (s / 'soil_grid.json').exists(): soils(s / 'soil_grid.json', mdir / 'soils.json')
        for plain in ('ifd.json', 'silo_full.json'):
            if (s / plain).exists():
                shutil.copy(s / plain, mdir / plain); os.chmod(mdir / plain, 0o644); print(f'  {plain}: copied')
        if (s / 'geology.json').exists(): geology(s / 'geology.json', mdir / 'geology.json')
        if (s / 'hazard.json').exists(): hazard(s / 'hazard.json', mdir / 'hazard.json')


if __name__ == '__main__':
    main()

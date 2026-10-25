"""Build the Mangiri site (Mongarlowe, Southern Tablelands NSW) from its NSW site pack.
The pack window is already 2 km square (MGA zone 55). The imagery server refused custom-size images, so the aerial is
stitched from its zoom-17 web-map tiles (stitch.py). The register property has three parts; the map's lot is the main
33 ha part (Brett: go with this lot for now) and the two smaller parts south of the road strip are kept as extra outlines.
usage: python3 scripts/analysis/mangiri/prep.py   (expects Mangiri/Site data staged under /mnt/user-data/uploads)"""
import json, os, sys, statistics, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from build_site import ll2mga
D = '/mnt/user-data/uploads/Claude Access--Permiculture Noosa PDC/Mangiri/Site data/'
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'map', 'sites', 'mangiri')); os.makedirs(OUT, exist_ok=True)
W = '/tmp/claude-0/mangiri'; os.makedirs(W, exist_ok=True)
w = json.load(open(D + 'window.json')); E0, N0, zone = w['E0'], w['N0'], w['zone']; assert w['size'] == 2000
# aerial: stitch and line up the web-map tiles
r = subprocess.run(['python3', os.path.join(HERE, 'stitch.py'), D, OUT + '/aerial.jpg'], capture_output=True, text=True); print(r.stdout, r.stderr[-800:])
# rain summary + daily file
j = json.load(open(D + 'silo_daily.json')); rain = {}; tmin = {}; r10 = []; t10 = []
for rr in j['data']:
    y, m = int(rr['date'][:4]), int(rr['date'][5:7]); dr = tn = None
    for v in rr['variables']:
        if v['variable_code'] == 'daily_rain': rain.setdefault((y, m), []).append(v['value']); dr = v['value']
        if v['variable_code'] == 'min_temp': tmin.setdefault(m, []).append(v['value']); tn = v['value']
    r10.append(round((dr or 0) * 10)); t10.append(round(tn * 10) if tn is not None else -999)
years = sorted({y for y, m in rain}); mean = []; med = []; days = []; tm = []
for m in range(1, 13):
    tot = [sum(rain[(y, m)]) for y in years if (y, m) in rain]; dd = [sum(1 for v in rain[(y, m)] if v >= 1) for y in years if (y, m) in rain]
    mean.append(round(sum(tot) / len(tot), 1)); med.append(round(statistics.median(tot), 1)); days.append(round(sum(dd) / len(dd), 1)); tm.append(round(sum(tmin[m]) / len(tmin[m]), 1))
R = {'station': 'SILO gridded data at the property (BoM)', 'distanceKm': 0, 'elevDiffM': 0, 'period': f'{years[0]}–{years[-1]}', 'mean': mean, 'median': med, 'days': days, 'tmin': tm, 'tminStation': 'SILO gridded'}
json.dump({'source': 'SILO gridded daily rainfall at the property (Queensland Government, CC BY 4.0)', 'start': j['data'][0]['date'], 'end': j['data'][-1]['date'], 'rain10': r10, 'tmin10': t10},
          open(OUT + '/rain_daily.json', 'w'), separators=(',', ':'))
print('rain/yr', round(sum(mean)), 'period', R['period'])
# boundary: main part is the map's lot, the others are extra outlines
g = json.load(open(D + 'boundary.geojson')); parts = [p[0] for p in g['features'][0]['geometry']['coordinates']]
def local(ring):
    a = np.array(ring, float); E, N = ll2mga(a[:, 0], a[:, 1], zone); return np.c_[E - E0, N0 - N]
def area(xy): x, y = xy[:, 0], xy[:, 1]; return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
parts.sort(key=lambda r: -area(local(r)))
print('parts ha', [round(area(local(r)) / 1e4, 2) for r in parts])
cfg = {'name': 'Mangiri', 'subtitle': 'Mongarlowe, NSW', 'state': 'NSW', 'council': 'Queanbeyan-Palerang', 'dem': {'2026': [D + 'dem_5m.tif']}, 'boundary': {'lonlat': parts[0]}, 'zone': zone,
       'window': [E0, N0], 'lfw': False, 'rain': R,
       'source': 'NSW 5 m DEM (DCS Spatial Services, from aerial stereo imagery; downloaded 2026), resampled to the 1 m map grid',
       'boundaryNote': 'Property outline from the NSW cadastre 2026 (property register, about ±1–2 m). The map\'s lot is the main 33 ha part; the two smaller parts of the same register property, south of the road strip, are drawn as a thin outline.',
       'soilNote': 'Elevation is 5 m from aerial photos: small banks, tracks and terraces are smoothed out. Check falls on site with a level.', 'out': OUT}
json.dump(cfg, open(W + '/cfg.json', 'w'))
r = subprocess.run(['python3', os.path.join(HERE, '..', 'build_site.py'), W + '/cfg.json'], capture_output=True, text=True); print(r.stdout[-2500:], r.stderr[-1500:])
r = subprocess.run(['python3', os.path.join(HERE, '..', 'hydro_layers.py'), OUT], capture_output=True, text=True); print(r.stdout[-500:], r.stderr[-500:])
# extra outlines: the other register parts. No separate focus area since trial v40: Brett wants the whole 33 ha lot
# as the focus, so the site opens fitted to the lot (focus.json, the clearing outline, is kept but not used)
t = json.load(open(OUT + '/terrain.json'))
t['lotParts'] = [np.round(local(r)[:-1], 1).ravel().tolist() for r in parts[1:]]
t.pop('focus', None)
t['meta']['site']['boundarySrc'] = 'NSW cadastre 2026'
t['meta']['site']['aerialSrc'] = 'NSW aerial 2014'
json.dump(t, open(OUT + '/terrain.json', 'w'), separators=(',', ':'))
print('catchment', t['catch'][0]['ha'], 'ha; runs past window:', t['meta'].get('catchEdge'))

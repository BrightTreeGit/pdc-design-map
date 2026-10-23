"""Build the Annwn site with placeholder elevation (open Terrain Tiles) until LiDAR is available.
usage: python3 prep.py   (expects Annwn/Site data staged under /mnt/user-data/uploads)"""
import json, sys, math, statistics, subprocess, glob, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from build_site import mga2ll
D = '/mnt/user-data/uploads/Claude Access--Permiculture Noosa PDC/Annwn/Site data/'
OUT = os.path.join(HERE, '..', '..', '..', 'map', 'sites', 'annwn')
W = '/tmp/claude-0/annwn'; os.makedirs(W, exist_ok=True)
w = json.load(open(D + 'window.json'))
# ---- placeholder DEM: flat ground at the SILO elevation (the block and street look level), until LiDAR arrives
j0 = json.load(open(D + 'silo_daily.json')); Z = float(j0['location']['elevation'])
step, pad = 5.0, 200
E0, N0 = w['E0'] - pad, w['N0'] + pad; ncell = int((2000 + 2 * pad) / step)
rng = np.random.default_rng(1); dem = Z + rng.normal(0, 0.002, (ncell, ncell))    # millimetre jitter only, so the build's maths has no exact ties
with open(W + '/dem_placeholder.asc', 'w') as f:
    f.write(f"ncols {ncell}\nnrows {ncell}\nxllcorner {E0}\nyllcorner {N0 - ncell * step}\ncellsize {step}\nNODATA_value -9999\n")
    for row in dem: f.write(' '.join(f'{v:.3f}' for v in row) + '\n')
print('placeholder flat DEM at', Z, 'm')
# ---- rainfall from SILO
j = json.load(open(D + 'silo_daily.json')); rain = {}; tmin = {}
for rr in j['data']:
    y, m = int(rr['date'][:4]), int(rr['date'][5:7])
    for v in rr['variables']:
        if v['variable_code'] == 'daily_rain': rain.setdefault((y, m), []).append(v['value'])
        if v['variable_code'] == 'min_temp': tmin.setdefault(m, []).append(v['value'])
years = sorted({y for y, m in rain}); mean = []; med = []; days = []; tm = []
for m in range(1, 13):
    tot = [sum(rain[(y, m)]) for y in years if (y, m) in rain]; dd = [sum(1 for v in rain[(y, m)] if v >= 1) for y in years if (y, m) in rain]
    mean.append(round(sum(tot) / len(tot), 1)); med.append(round(statistics.median(tot), 1)); days.append(round(sum(dd) / len(dd), 1)); tm.append(round(sum(tmin[m]) / len(tmin[m]), 1))
R = {'station': 'SILO gridded data at the property (BoM)', 'distanceKm': 0, 'elevDiffM': 0, 'period': f'{years[0]}–{years[-1]}', 'mean': mean, 'median': med, 'days': days, 'tmin': tm, 'tminStation': 'SILO gridded'}
print('rain/yr', round(sum(mean)))
g = json.load(open(D + 'boundary.geojson')); c = g['features'][0]['geometry']['coordinates'][0]
cfg = {'name': 'Annwn', 'subtitle': 'Capalaba, Redlands Qld', 'state': 'QLD', 'council': 'Redland City', 'dem': {'2026': [W + '/dem_placeholder.asc']}, 'boundary': {'lonlat': c}, 'zone': 56,
       'window': [w['E0'], w['N0']], 'lfw': False, 'rain': R,
       'source': 'PLACEHOLDER: ground shown as level at about '+str(round(Z))+' m until the 1 m LiDAR is available',
       'boundaryNote': 'Lot boundary from the Queensland cadastre (about ±1 m). A small suburban block: zoom in to work on it.',
       'soilNote': 'Placeholder: the ground is shown as level, so there are no slopes, flow lines or contours yet. They appear when the 1 m LiDAR is added. Check falls on site with a level.',
       'out': OUT}
json.dump(cfg, open(W + '/cfg.json', 'w'))
r = subprocess.run(['python3', os.path.join(HERE, '..', 'build_site.py'), W + '/cfg.json'], capture_output=True, text=True); print(r.stdout[-1500:], r.stderr[-1500:])

# flat placeholder: drop terrain products that would only be noise
tp = OUT + '/terrain.json'; T = json.load(open(tp))
for k in ('streams', 'c1', 'c5', 'kp'): T[k] = []
T['catch'] = T['catch'][:1]   # keep the block's own catchment entry (the site tab reads it)
json.dump(T, open(tp, 'w'), separators=(',', ':'))
for f in ('prospects.json',):
    if os.path.exists(OUT + '/' + f): os.remove(OUT + '/' + f)
print('flat placeholder tidy done')

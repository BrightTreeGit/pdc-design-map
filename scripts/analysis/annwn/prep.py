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
# ---- placeholder DEM: terrarium tiles -> 5 m ESRI ascii grid in MGA
tj = json.load(open(D + 'terrain_tiles/tiles.json')); z = tj['zoom']; n = 2 ** z
T = {(x, y): np.array(Image.open(D + 'terrain_tiles/' + f).convert('RGB')).astype(np.float64) for _, x, y, f in tj['tiles']}
T = {k: v[..., 0] * 256 + v[..., 1] + v[..., 2] / 256 - 32768 for k, v in T.items()}
step, pad = 5.0, 200
E0, N0 = w['E0'] - pad, w['N0'] + pad; ncell = int((2000 + 2 * pad) / step)
dem = np.full((ncell, ncell), np.nan)
for r in range(ncell):
    for c in range(ncell):
        lon, lat = mga2ll(E0 + (c + .5) * step, N0 - (r + .5) * step, 56)
        fx = (lon + 180) / 360 * n * 256; fy = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n * 256
        tx, ty = int(fx // 256), int(fy // 256); px, py = fx - tx * 256 - .5, fy - ty * 256 - .5
        t = T.get((tx, ty))
        if t is None: continue
        x0, y0 = int(np.clip(math.floor(px), 0, 254)), int(np.clip(math.floor(py), 0, 254)); ax, ay = np.clip(px - x0, 0, 1), np.clip(py - y0, 0, 1)
        dem[r, c] = (t[y0, x0] * (1 - ax) * (1 - ay) + t[y0, x0 + 1] * ax * (1 - ay) + t[y0 + 1, x0] * (1 - ax) * ay + t[y0 + 1, x0 + 1] * ax * ay)
dem = np.where(np.isnan(dem), np.nanmedian(dem), dem)
with open(W + '/dem_placeholder.asc', 'w') as f:
    f.write(f"ncols {ncell}\nnrows {ncell}\nxllcorner {E0}\nyllcorner {N0 - ncell * step}\ncellsize {step}\nNODATA_value -9999\n")
    for row in dem: f.write(' '.join(f'{v:.2f}' for v in row) + '\n')
print('placeholder DEM', np.nanmin(dem).round(1), np.nanmax(dem).round(1))
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
       'source': 'PLACEHOLDER elevation (open Terrain Tiles, about 30 m detail) until the 1 m LiDAR is available',
       'boundaryNote': 'Lot boundary from the Queensland cadastre (about ±1 m). A small suburban block: zoom in to work on it.',
       'soilNote': 'Placeholder elevation: slopes, flow lines and contours are only indicative here and will sharpen when the 1 m LiDAR is added. Check falls on site with a level.',
       'out': OUT}
json.dump(cfg, open(W + '/cfg.json', 'w'))
r = subprocess.run(['python3', os.path.join(HERE, '..', 'build_site.py'), W + '/cfg.json'], capture_output=True, text=True); print(r.stdout[-1500:], r.stderr[-1500:])

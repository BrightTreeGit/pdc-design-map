"""Build the Regenify site (Koonyum Range, NSW) from its NSW site pack.
The pack's window is 2.5 km square; the map uses 2 km, so the window is re-centred and the aerial cropped to match.
usage: python3 scripts/analysis/regenify/prep.py   (expects Regenify/Site data staged under /mnt/user-data/uploads)"""
import json, os, sys, statistics, subprocess
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
D = '/mnt/user-data/uploads/Claude Access--Permiculture Noosa PDC/Regenify/Site data/'
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'map', 'sites', 'regenify')); os.makedirs(OUT, exist_ok=True)
W = '/tmp/claude-0/regenify'; os.makedirs(W, exist_ok=True)
w = json.load(open(D + 'window.json')); S0 = w['size']; S = 2000; off = (S0 - S) / 2
E0, N0 = w['E0'] + off, w['N0'] - off
# aerial: crop the central 2 km of the 2.5 km image
im = Image.open(D + 'aerial_regenify.jpg').convert('RGB'); px = im.size[0] / S0
im.crop((round(off * px), round(off * px), round((off + S) * px), round((off + S) * px))).resize((3000, 3000), Image.LANCZOS).save(OUT + '/aerial.jpg', quality=84)
# rain summary + daily file
j = json.load(open(D + 'silo_daily.json')); rain = {}; tmin = {}; r10 = []; t10 = []
for r in j['data']:
    y, m = int(r['date'][:4]), int(r['date'][5:7]); dr = tn = None
    for v in r['variables']:
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
print('rain/yr', round(sum(mean)))
g = json.load(open(D + 'boundary.geojson')); c = g['features'][0]['geometry']['coordinates'][0]
cfg = {'name': 'Regenify', 'subtitle': 'Koonyum Range, NSW', 'state': 'NSW', 'council': 'Byron', 'dem': {'2019': [D + 'dem_5m.tif']}, 'boundary': {'lonlat': c}, 'zone': 56,
       'window': [E0, N0], 'lfw': False, 'rain': R,
       'source': 'NSW 5 m elevation (DCS Spatial Services, from aerial stereo imagery), resampled to the 1 m map grid',
       'boundaryNote': 'Property outline from the NSW property register (about ±1–2 m).',
       'soilNote': 'Elevation is 5 m from aerial photos: small banks, tracks and terraces are smoothed out. Check falls on site with a level.', 'out': OUT}
json.dump(cfg, open(W + '/cfg.json', 'w'))
r = subprocess.run(['python3', os.path.join(HERE, '..', 'build_site.py'), W + '/cfg.json'], capture_output=True, text=True); print(r.stdout[-2500:], r.stderr[-1500:])
r = subprocess.run(['python3', os.path.join(HERE, '..', 'hydro_layers.py'), OUT], capture_output=True, text=True); print(r.stdout[-500:], r.stderr[-500:])

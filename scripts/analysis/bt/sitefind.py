"""Cabin and dwelling site finder for Bright Tree.
Scores every 2 m cell on the lot for a small building (cabin, tiny home, retreat hut; a 10 x 10 m footprint) from:
slope, vegetation rules (regional ecosystem status, open ground), creek and drainage-line buffers, fire run and fuel,
trees tall enough to reach it, winter sun (terrain), access (distance to tracks and the road), cold air and wetness,
and the boundary. Each factor is 0-1; the score is their weighted geometric mean, so one bad factor pulls a spot down.
Screening only: every spot needs a site walk, and buildings need council and vegetation approvals as they apply.

usage: python3 sitefind.py <work dir with ground.npy chm.npy slope.npy inlot.npy privacy.npz> <features dir> <out dir>"""
import sys, json, glob, math, zlib, base64, numpy as np
from scipy import ndimage
from matplotlib.path import Path
from PIL import Image
sys.path.insert(0, __file__.rsplit('/', 1)[0]); from viewshed import horizon
LAT = -26.7434
def sunpath(doy=172, step=0.1):
    dec = math.radians(23.44) * math.sin(2 * math.pi * (284 + doy) / 365); la = math.radians(LAT); out = []
    for k in range(int(24 / step)):
        h = math.radians((k * step - 12) * 15)
        alt = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(h))
        if alt <= 0: continue
        az = math.degrees(math.atan2(math.sin(h), math.cos(h) * math.sin(la) - math.tan(dec) * math.cos(la))) + 180
        out.append((math.degrees(alt), az % 360))
    return out
SUNSTEP = 0.1; SUNPATH = sunpath(172, SUNSTEP)
W, FD, OUT = sys.argv[1:4]
M = '/home/claude/pdc-design-map/map/'
g = np.load(W + 'ground.npy').astype(np.float64); chm = np.load(W + 'chm.npy'); inlot = np.load(W + 'inlot.npy')
T = json.load(open(M + 'terrain.json')); lot = np.array(T['lot']).reshape(-1, 2)
N = 2000; S = 2                         # analysis on a 2 m grid (1000 x 1000)
def down(a, f=np.mean):
    return f(f(a.reshape(1000, 2, 1000, 2), axis=3), axis=1)
G2 = down(g); C2 = down(chm, np.max); L2 = down(inlot.astype(float)) > .5
yy, xx = np.mgrid[0:1000, 0:1000]; X, Y = xx * 2 + 1, yy * 2 + 1      # cell centres in map metres
# ---- slope over a 10 x 10 m footprint (plane fit = mean gradient)
gy, gx = np.gradient(ndimage.uniform_filter(G2, 5), 2.0)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
# roughness inside the footprint (how much the ground departs from a plane: rock steps, gullies)
res = G2 - ndimage.uniform_filter(G2, 5); rough = np.sqrt(ndimage.uniform_filter(res * res, 5))
def f_slope(s):
    return np.interp(s, [0, 8, 15, 22, 30, 40], [1, 1, .75, .45, .15, .03])
# ---- vegetation rules: regional ecosystem status; open ground needs no clearing
E = json.load(open(M + 'ecosystems.json')); stat = np.zeros((1000, 1000), np.int8)   # 0 non-remnant, 1 least concern, 2 of concern
pts = np.c_[X.ravel(), Y.ravel()]
for p in E['polys']:
    vm = E['cat'].get(p['re'], {}).get('vm', '')
    k = 2 if vm in ('Of concern', 'Endangered') else 1 if vm == 'Least concern' else 0
    if k == 0: continue
    for ring in p['rings']:
        r = np.array(ring)
        bb = (X >= r[:, 0].min()) & (X <= r[:, 0].max()) & (Y >= r[:, 1].min()) & (Y <= r[:, 1].max())
        if not bb.any(): continue
        ins = np.zeros(bb.shape, bool); ins[bb] = Path(r).contains_points(np.c_[X[bb], Y[bb]])
        stat[ins] = np.maximum(stat[ins], k)
canopy_fp = ndimage.uniform_filter(C2, 5)      # mean canopy height over the footprint
openg = canopy_fp < 3
f_rule = np.where(openg, 1.0, np.where(stat == 2, .15, np.where(stat == 1, .75, .9)))
# ---- creeks and drainage lines
cr = np.zeros((1000, 1000), bool); dl = np.zeros((1000, 1000), bool)
for st in T['streams']:
    p = np.array(st['p']).reshape(-1, 2)
    for (x0, y0), (x1, y1) in zip(p[:-1], p[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) / 1) + 1
        xs = np.clip(((x0 + (x1 - x0) * np.linspace(0, 1, n)) / 2).astype(int), 0, 999); ys = np.clip(((y0 + (y1 - y0) * np.linspace(0, 1, n)) / 2).astype(int), 0, 999)
        if st['k'] >= 2: cr[ys, xs] = True
        elif st['k'] == 1: dl[ys, xs] = True
dcr = ndimage.distance_transform_edt(~cr) * 2; ddl = ndimage.distance_transform_edt(~dl) * 2
f_creek = np.minimum(np.interp(dcr, [0, 10, 20, 30], [.02, .1, .5, 1]), np.interp(ddl, [0, 4, 10], [.3, .6, 1]))
# ---- fire: fire run potential (terrain and NW-W winds) and fuel structure within 30 m
def classes(png, cols, size):
    a = np.array(Image.open(M + png).convert('RGBA')).astype(int)
    out = np.zeros(a.shape[:2], np.int8)
    for k, c in enumerate(cols, 1):
        out[(a[..., 3] > 0) & (np.abs(a[..., :3] - c).sum(-1) < 12)] = k
    if out.shape[0] != size: out = out.reshape(size, out.shape[0] // size, size, -1).max(axis=(1, 3))
    return out
fire = classes('fire.png', [(245, 160, 60), (225, 90, 40), (150, 30, 30)], 1000)
fuel = classes('fuel.png', [(250, 200, 80), (235, 120, 40), (170, 30, 30)], 1000)
fuel30 = ndimage.uniform_filter(fuel.astype(float), 31)
f_fire = np.array([1, .8, .55, .35])[fire] * np.clip(1 - .15 * fuel30, .5, 1)
# ---- trees tall enough to reach the footprint (2022 canopy tops >= 15 m within 60 m)
mx = ndimage.maximum_filter(chm, size=7); tops = (chm == mx) & (chm >= 15)
ty, tx = np.where(tops); th = chm[ty, tx]
reach = np.zeros((1000, 1000), np.int16)
for x, y, h in zip(tx, ty, th):
    r = int((h + 5) / 2) + 1; cx, cy = x // 2, y // 2
    y0, y1, x0, x1 = max(0, cy - r), min(1000, cy + r + 1), max(0, cx - r), min(1000, cx + r + 1)
    d = np.hypot(X[y0:y1, x0:x1] - x, Y[y0:y1, x0:x1] - y)
    reach[y0:y1, x0:x1] += (d <= h - 2) & (d > 5)          # falls onto the footprint edge (5 m half-width)
f_tree = np.interp(reach, [0, 3, 10, 30], [1, .85, .7, .5])
# ---- winter sun (terrain only, 21 June): what a small cleared pad would get
sun = np.frombuffer(zlib.decompress(base64.b64decode(T['meta']['sunh_winter'])), np.uint8).reshape(500, 500) / 10
sun2 = sun.repeat(2, 0).repeat(2, 1)
f_sun = np.interp(sun2, [0, 3, 5, 7, 8.5], [.2, .35, .6, .85, 1])
# ---- access: tracks, roads and paths drawn on the map, plus the public road
acc = np.zeros((1000, 1000), bool); paths = np.zeros((1000, 1000), bool)
ROAD = [(797, 760), (797, 860), (792, 940), (785, 1000), (770, 1060), (752, 1110), (728, 1160), (708, 1205), (695, 1250), (690, 1330)]
def burn(arr, p):
    for (x0, y0), (x1, y1) in zip(p[:-1], p[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        xs = np.clip(((x0 + (x1 - x0) * np.linspace(0, 1, n)) / 2).astype(int), 0, 999); ys = np.clip(((y0 + (y1 - y0) * np.linspace(0, 1, n)) / 2).astype(int), 0, 999)
        arr[ys, xs] = True
burn(acc, ROAD)
named = []
for f in glob.glob(FD + '/*.json'):
    d = json.load(open(f)); d = d.get('data', d); gg = d.get('geom') or {}
    if gg.get('pts') and gg.get('g') == 'line' and d.get('kind') in ('track', 'road'): burn(acc, gg['pts'])
    if gg.get('pts') and gg.get('g') == 'line' and d.get('kind') == 'path': burn(paths, gg['pts'])
    if d.get('kind') in ('cabin', 'building', 'teepee', 'structure', 'greenhouse', 'zone0') and gg.get('pts'):
        named.append((d.get('kind'), d.get('name'), np.mean(np.array(gg['pts'], float), 0).tolist(), gg.get('g')))
dacc = ndimage.distance_transform_edt(~acc) * 2; dpath = ndimage.distance_transform_edt(~paths) * 2
f_acc = np.maximum(np.interp(dacc, [0, 15, 60, 150, 300], [1, 1, .6, .35, .25]), np.interp(dpath, [0, 10, 60], [.75, .7, .3]))
# ---- cold air pooling and wetness
cold = np.array(Image.open(M + 'cold.png'))[..., 3] / 255.0
wet = np.array(Image.open(M + 'wet.png'))[..., 3] / 255.0
f_cw = np.clip(1 - .5 * np.clip(cold / max(cold.max(), 1e-6), 0, 1), .5, 1) * np.clip(1 - .45 * wet / max(wet.max(), 1e-6), .55, 1)
# ---- boundary and existing roofs
lotm = L2; dbound = ndimage.distance_transform_edt(lotm) * 2
f_bound = np.interp(dbound, [0, 6, 10, 15], [.02, .1, .7, 1])
P = "/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/"
bl = np.load(P + 'canopy_bright-tree_2022.npz')['bldg'] > 0
droof = ndimage.distance_transform_edt(~bl) * 2
f_roof = np.interp(droof, [0, 6, 10], [0, .2, 1])
# ---- privacy (terrain-only exposure: viewpoints on the road and at neighbours' houses that would see a 3 m roof here
# if the trees in between were gone) and distance from the road
pv = np.load(W + 'privacy.npz'); expo = down(pv['terrain'].astype(float), np.max); seen_now = down(pv['trees'].astype(float), np.max)
rd = np.zeros((1000, 1000), bool); burn(rd, ROAD); dacc_road = ndimage.distance_transform_edt(~rd) * 2
expw = down(pv['terrain_w'].astype(float), np.mean)
f_priv = np.minimum(np.interp(dacc_road, [0, 30, 80], [.5, .8, 1]), np.interp(expw, [5, 15, 35], [1, .85, .6]))
# ---- combine
F = dict(slope=(f_slope(slope), 1.3), rules=(f_rule, 1.2), creek=(f_creek, 1.0), fire=(f_fire, .8), trees=(f_tree, .4), sun=(f_sun, .6),
         access=(f_acc, .8), coldwet=(f_cw, .5), boundary=(f_bound, .8), roofs=(f_roof, .5), privacy=(f_priv, .3))
HARD = ('slope', 'rules', 'creek', 'boundary', 'roofs')
wsum = sum(w for _, w in F.values())
base = sum(w * v for v, w in F.values()) / wsum                       # weighted average of the factors
cap = np.minimum.reduce([F[k][0] for k in HARD]) + .3                 # one hard limit (steep, protected, creek, boundary) caps it
score = np.minimum(base, cap)
score[~lotm] = 0
score[slope > 35] = np.minimum(score[slope > 35], .05)
house = (906, 947); dhouse = np.hypot(X - house[0], Y - house[1])
# ---- candidate spots: local maxima, 35 m apart
sm = ndimage.uniform_filter(score, 3)
peaks = (sm == ndimage.maximum_filter(sm, size=9)) & (sm > .6) & lotm
cy, cx = np.where(peaks); order = np.argsort(-sm[cy, cx]); picked = []
for i in order:
    x, y = cx[i], cy[i]
    if all(math.hypot(x - a, y - b) * 2 > 35 for a, b in picked): picked.append((x, y))
    if len(picked) >= 14: break
REN = {2: 'of-concern regional ecosystem (needs a vegetation approval to clear)', 1: 'least-concern regional ecosystem', 0: 'non-remnant (regrowth or cleared)'}
def card(x, y, label=None, kind=None):
    i, j = int(y), int(x)
    X1, Y1 = int(x * 2 + 1), int(y * 2 + 1)
    # cut and fill to level an 8 x 10 m pad, long side along the contour (rotated to the slope direction)
    asp = math.atan2(gy[i, j], gx[i, j]); u = np.array([-math.sin(asp), math.cos(asp)]); v = np.array([math.cos(asp), math.sin(asp)])
    a, b = np.meshgrid(np.arange(-4.5, 5, 1.0), np.arange(-3.5, 4, 1.0)); px = X1 + a * u[0] + b * v[0]; py = Y1 + a * u[1] + b * v[1]
    zz = g[np.clip(np.rint(py).astype(int), 0, 1999), np.clip(np.rint(px).astype(int), 0, 1999)]
    cutfill = float(np.abs(zz - zz.mean()).sum() / 2)
    # winter sun on 21 June with today's trees around a cleared 8 m radius (crowns and terrain)
    hz = horizon(g + chm, X1, Y1, g[Y1, X1] + 1.6, 300, nb=360, clear_r=8, ground=g)
    hrs = sum(1 for alt, az in SUNPATH if math.tan(math.radians(alt)) > hz[int(az) % 360]) * SUNSTEP
    hz0 = horizon(g, X1, Y1, g[Y1, X1] + 1.6, 900, nb=360)
    hrs0 = sum(1 for alt, az in SUNPATH if math.tan(math.radians(alt)) > hz0[int(az) % 360]) * SUNSTEP
    d = dict(x=int(x * 2 + 1), y=int(y * 2 + 1), score=round(float(sm[i, j]), 2), z=round(float(G2[i, j])), slope=round(float(slope[i, j])),
             rough=round(float(rough[i, j]), 1), canopy=round(float(canopy_fp[i, j])), open=bool(openg[i, j]), re=int(stat[i, j]),
             creek=round(float(dcr[i, j])), drain=round(float(ddl[i, j])), fire=int(fire[i, j]), fuel=round(float(fuel30[i, j]), 1),
             trees=int(reach[i, j]), sun=round(float(sun2[i, j]), 1), access=round(float(dacc[i, j])), path=round(float(dpath[i, j])),
             cold=round(float(cold[i, j]), 2), wet=round(float(wet[i, j]), 2), boundary=round(float(dbound[i, j])), house=round(float(dhouse[i, j])),
             road=round(float(dacc_road[i, j])), seen_now=bool(seen_now[i, j] > 0), exposure=int(expo[i, j]), expw=round(float(expw[i, j]), 1), cutfill=round(cutfill), sunTrees=round(hrs, 1), sunTerrain=round(hrs0, 1),
             weak=sorted([(k, round(float(v[0][i, j]), 2)) for k, v in F.items()], key=lambda t: t[1])[:3])
    if label: d['label'] = label
    if kind: d['kind'] = kind
    return d
spots = [card(x, y, f'S{k + 1}') for k, (x, y) in enumerate(picked)]
planned = []
for kind, name, c, geo in named:
    if kind in ('zone0', 'building') or 'Bunyip' in (name or '') or name == 'Greenhouse / zome 1': continue
    planned.append(card(c[0] / 2, c[1] / 2, name, kind))
PR = json.load(open(M + 'prospects.json'))
for it in PR['items']:
    if it['kind'] == 'pad': planned.append(card(it['at'][0] / 2, it['at'][1] / 2, it['label'].split(' · ')[0], 'prospect'))
# ---- layer image: colour by score (transparent where under 0.15 or off the lot)
rgb = np.zeros((1000, 1000, 4), np.uint8)
stops = [(0.3, (200, 60, 50)), (0.5, (235, 140, 50)), (0.6, (240, 210, 70)), (0.7, (150, 200, 80)), (0.8, (40, 150, 80))]
sv = score.copy()
for c in range(3):
    rgb[..., c] = np.interp(sv, [s for s, _ in stops], [col[c] for _, col in stops]).astype(np.uint8)
rgb[..., 3] = np.where(lotm & (sv >= .3), np.interp(sv, [.3, .6, .85], [110, 160, 205]), 0).astype(np.uint8)
Image.fromarray(rgb).save(OUT + '/sites.png', optimize=True)
share = lambda m: round(float(m[lotm].mean()), 3)
summary = dict(good=share(score >= .75), fair=share((score >= .6) & (score < .75)), lotHa=round(float(lotm.sum() * 4 / 1e4), 2),
               seenNow=share(seen_now > 0), exposedNoTrees=share(expo > 0))
json.dump(dict(note='Cabin and dwelling site finder: 10 x 10 m footprint scored on slope, vegetation rules, creek and drainage buffers, fire run and fuel, trees that could reach it, winter sun (terrain), access, cold air and wetness, boundary, existing roofs and closeness to the road. Screening only.',
               computed='2026-11-10', sources=['Queensland LiDAR 2022 (ELVIS): ground, canopy, roofs', 'Queensland Herbarium regional ecosystems (REDD v13.1)', 'map flow lines, fire run, fuel, cold air, wetness and winter sun layers', 'tracks and road drawn on the map'],
               weights={k: w for k, (_, w) in F.items()}, summary=summary, spots=spots, planned=planned), open(OUT + '/sites.json', 'w'), separators=(',', ':'))
np.save(W + 'site_score.npy', score.astype(np.float32))
print(json.dumps(summary)); print('spots'); [print(s['label'], s['x'], s['y'], s['score'], 'slope', s['slope'], 'open' if s['open'] else REN[s['re']][:14], 'sun', s['sun'], 'acc', s['access'], 'trees', s['trees'], 'creek', s['creek'], 'house', s['house'], 'cf', s['cutfill'], 'sunT', s['sunTrees'], s['sunTerrain'], s['weak']) for s in spots]
print('planned'); [print(s['label'][:30].ljust(31), s['score'], 'slope', s['slope'], 'open' if s['open'] else REN[s['re']][:14], 'sun', s['sun'], 'acc', s['access'], 'trees', s['trees'], 'creek', s['creek'], 'cf', s['cutfill'], 'sunT', s['sunTrees'], s['weak']) for s in planned]

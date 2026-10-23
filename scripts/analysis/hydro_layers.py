"""Wetness (where water collects) and erosion-risk overlays from each site's 2 m LiDAR terrain.

usage: python3 scripts/analysis/hydro_layers.py map map/sites/bellbunya ...   (folders holding terrain.json)
writes wet.png, erosion.png (1000 x 1000, drawn over the 2 km map square) and hydro.json (classes and
the share of the property in each) into each folder.

How it works, in plain terms:
1. Fill pits in the terrain so water can always run downhill to an edge ("priority-flood").
2. Route rain downhill, sharing each cell's water between all its lower neighbours in proportion to
   how steep each way is (multiple flow direction, Freeman 1991). The total that passes through a
   cell is its upslope contributing area.
3. Wetness index (TWI) = ln(contributing area per metre of contour / tan(slope)). Big area + flat = wet.
4. Erosion risk = the RUSLE slope-length factor LS (Moore & Burch 1986):
   (area per metre / 22.13)^0.4 x (sin slope / 0.0896)^1.3. It is the terrain's share of soil loss
   if the ground were bare; groundcover cuts actual loss by 90%+.
"""
import json, sys, os, zlib, base64, heapq
import numpy as np
from PIL import Image
from matplotlib.path import Path

N = 1000; RES = 2.0
WET = [(0, 6, None, 'Dry: sheds water'), (6, 8, (170, 210, 235, 110), 'Moist'), (8, 10, (90, 160, 220, 160), 'Damp after rain'),
       (10, 12, (30, 100, 200, 200), 'Wet: water gathers'), (12, None, (10, 40, 140, 225), 'Very wet: soaks, springs, flow paths')]
ERO = [(0, 2, None, 'Low'), (2, 5, (245, 215, 80, 130), 'Moderate'), (5, 10, (240, 150, 40, 170), 'High'),
       (10, 20, (215, 60, 40, 200), 'Very high'), (20, None, (120, 20, 80, 225), 'Extreme: gullies start here if bare')]


def load(folder):
    d = json.load(open(os.path.join(folder, 'terrain.json')))
    z = np.frombuffer(zlib.decompress(base64.b64decode(d['meta']['dem']['b64'])), dtype=np.int16).reshape(N, N) / 10.0
    return d, z


def priority_flood(z, nodata):
    """Raise every pit to its spill height (+ a tiny gradient) so all water can leave the grid."""
    f = z.copy(); done = np.zeros_like(nodata); h = []
    edge = np.zeros_like(nodata); edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    edge |= nodata
    for r, c in zip(*np.nonzero(edge)):
        heapq.heappush(h, (f[r, c], r, c)); done[r, c] = True
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    fl = f.tolist(); dl = done.tolist()
    while h:
        zc, r, c = heapq.heappop(h)
        for dr, dc in nb:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N and not dl[rr][cc]:
                dl[rr][cc] = True
                if fl[rr][cc] <= zc: fl[rr][cc] = zc + 1e-4
                heapq.heappush(h, (fl[rr][cc], rr, cc))
    return np.array(fl)


def mfd_accumulation(f, nodata, p=1.1):
    """Cells of upslope area flowing through each cell (multiple flow direction)."""
    acc = np.ones((N, N)); acc[nodata] = 0
    order = np.argsort(-f, axis=None)
    nb = [(-1, -1, 1.414), (-1, 0, 1), (-1, 1, 1.414), (0, -1, 1), (0, 1, 1), (1, -1, 1.414), (1, 0, 1), (1, 1, 1.414)]
    fl = f.tolist(); al = acc.tolist(); nd = nodata.tolist()
    for k in order.tolist():
        r, c = divmod(k, N)
        if nd[r][c]: continue
        zc = fl[r][c]; ws = []; tot = 0.0
        for dr, dc, dist in nb:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N and not nd[rr][cc]:
                dz = zc - fl[rr][cc]
                if dz > 0:
                    w = (dz / dist) ** p; ws.append((rr, cc, w)); tot += w
        if tot > 0:
            a = al[r][c] / tot
            for rr, cc, w in ws: al[rr][cc] += a * w
    return np.array(al)


def colour(v, classes, nodata):
    img = np.zeros((N, N, 4), np.uint8)
    for lo, hi, col, _ in classes:
        if col is None: continue
        m = (v >= lo) & ((v < hi) if hi is not None else True) & ~nodata
        img[m] = col
    return Image.fromarray(img, 'RGBA')


def lot_mask(lot):
    pts = np.array(lot, float).reshape(-1, 2) / RES      # map units (m) -> 2 m cells
    yy, xx = np.mgrid[0:N, 0:N]
    return Path(pts).contains_points(np.c_[xx.ravel() + .5, yy.ravel() + .5]).reshape(N, N)


def shares(v, classes, mask):
    n = mask.sum() or 1
    return [round(float(((v >= lo) & ((v < hi) if hi is not None else True) & mask).sum() / n), 4) for lo, hi, _, _ in classes]


def main(folder):
    d, z = load(folder)
    nodata = z < 0.5 if z.min() < 0.5 else np.zeros_like(z, bool)    # sea at coastal sites
    f = priority_flood(z, nodata)
    acc = mfd_accumulation(f, nodata)
    gy, gx = np.gradient(z, RES)
    tanb = np.maximum(np.hypot(gx, gy), 0.005); sinb = np.sin(np.arctan(tanb))
    sca = acc * RES                                   # contributing area per metre of contour (m)
    twi = np.log(sca / tanb)
    ls = (sca / 22.13) ** 0.4 * (sinb / 0.0896) ** 1.3
    colour(twi, WET, nodata).save(os.path.join(folder, 'wet.png'), optimize=True)
    colour(ls, ERO, nodata).save(os.path.join(folder, 'erosion.png'), optimize=True)
    m = lot_mask(d['lot']) & ~nodata
    out = {'source': 'LiDAR terrain (2 m, as used for this site), computed 24 Oct 2026',
           'wet': {'classes': [[lo, hi, list(c) if c else None, lab] for lo, hi, c, lab in WET], 'lotShare': shares(twi, WET, m)},
           'erosion': {'classes': [[lo, hi, list(c) if c else None, lab] for lo, hi, c, lab in ERO], 'lotShare': shares(ls, ERO, m)},
           'lotHa': round(float(m.sum() * RES * RES / 1e4), 1)}
    json.dump(out, open(os.path.join(folder, 'hydro.json'), 'w'))
    print(folder, out['lotHa'], 'ha  wet', out['wet']['lotShare'], ' erosion', out['erosion']['lotShare'], flush=True)


if __name__ == '__main__':
    for fdr in sys.argv[1:]: main(fdr)

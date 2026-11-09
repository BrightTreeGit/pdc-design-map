"""Distant views from a spot: near field from the 1 m LiDAR (trees or terrain only), far field from the 15 m
regional elevation model out to the coast, with earth curvature and standard refraction."""
import numpy as np, json
CO = '/tmp/claude-0/work/coast/'
D15 = None
def load():
    global D15, SEA, PL
    if D15 is None:
        D15 = np.load(CO + 'dem15.npy').astype(np.float64); D15[D15 < -100] = 0
        SEA = np.load(CO + 'sea.npy'); PL = json.load(open(CO + 'data.json'))['places']
    return D15, SEA, PL
def m2c(x, y):   # map metres -> 15 m grid col,row
    return (12000 + x) / 15 - .5, (23000 + y) / 15 - .5
def far(x, y, eye, near_h, near_r=900, nb=720, maxr=40000):
    """near_h: tan of the near-field horizon per azimuth bin (len nb, 0 = north, clockwise).
    Returns (visible bool on the 15 m grid, sea cells seen, land km2 seen beyond near_r)."""
    Z, SEA, _ = load(); H, W = Z.shape
    oc, orr = m2c(x, y)
    az = (np.arange(nb) + .5) * 360 / nb; a = np.radians(az)
    cs, sn = np.sin(a), -np.cos(a)       # east, south components per bin
    best = near_h.copy()
    vis = np.zeros((H, W), bool)
    for i in range(1, int(maxr / 7.5)):
        d = i * 7.5
        if d < near_r: continue
        c = np.rint(oc + cs * d / 15).astype(int); r = np.rint(orr + sn * d / 15).astype(int)
        ok = (c >= 0) & (c < W) & (r >= 0) & (r < H)
        if not ok.any(): break
        drop = d * d * 0.87 / 12.74e6
        t = (Z[r[ok], c[ok]] - drop - eye) / d
        b = best[ok]; s = t >= b
        vis[r[ok][s], c[ok][s]] = True; best[ok] = np.maximum(b, t)
    return vis

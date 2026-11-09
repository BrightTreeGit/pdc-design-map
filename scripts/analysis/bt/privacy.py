"""Where on the lot a 3 m high cabin would be in sight of the public road or a neighbour's house (2022 LiDAR).
Two runs: with today's trees (canopy treated as solid) and terrain only (if the trees in between were gone)."""
import sys, json, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from viewshed import viewshed
W = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/al/bt/'
g = np.load(W + 'ground.npy'); chm = np.load(W + 'chm.npy'); top = g + chm; inlot = np.load(W + 'inlot.npy')
# public road traced from the LiDAR ground model (benched line just outside the west boundary)
ROAD = [(797, 760), (797, 860), (792, 940), (785, 1000), (770, 1060), (752, 1110), (728, 1160), (708, 1205), (695, 1250), (690, 1330)]
obs = []
for (x0, y0), (x1, y1) in zip(ROAD[:-1], ROAD[1:]):
    L = np.hypot(x1 - x0, y1 - y0)
    for t in np.arange(0, L, 10):
        x, y = x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L
        obs.append(('road', x, y, g[int(y), int(x)] + 1.5))
for x, y, sz, mx, d in json.load(open(W + 'neighbours.json')):
    obs.append(('house', x, y, mx - 1.5))
print(len(obs), 'viewpoints')
seen = {}
for mode, surf in (('trees', top), ('terrain', g)):
    acc = np.zeros(g.shape, np.int16); src = np.zeros(g.shape, np.uint8); wx = np.zeros(g.shape, np.float32)
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    for kind, x, y, eye in obs:
        v = viewshed(surf, g, x, y, eye, 1000, target=3.0, clear_r=3 if kind == 'road' else 8)
        v &= inlot
        acc += v; src[v] |= (1 if kind == 'road' else 2)
        # nearer viewers count for more: a road point 50 m away counts 4 x one 200 m away (houses count double: people live there)
        d = np.hypot(xx - x, yy - y); wx += v * np.clip(200 / np.maximum(d, 25), .1, 8) * (1 if kind == 'road' else 2) / (10 if kind == 'road' else 1)
    seen[mode] = (acc, src, wx)
    print(mode, 'lot share in sight:', round(float((acc[inlot] > 0).mean()), 3), 'road', round(float(((src & 1) > 0)[inlot].mean()), 3), 'houses', round(float(((src & 2) > 0)[inlot].mean()), 3))
np.savez_compressed(W + 'privacy.npz', trees=seen['trees'][0], trees_src=seen['trees'][1], terrain=seen['terrain'][0], terrain_src=seen['terrain'][1], terrain_w=seen['terrain'][2], trees_w=seen['trees'][2])

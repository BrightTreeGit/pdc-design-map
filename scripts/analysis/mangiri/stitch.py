"""Stitch the NSW Imagery web-map tiles (zoom 17, Web Mercator) into the 2 km map window (MGA zone 55, 1 m pixels).
usage: python3 scripts/analysis/mangiri/stitch.py <Site data folder> <out.jpg>"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from build_site import mga2ll
D, OUT = sys.argv[1], sys.argv[2]
w = json.load(open(os.path.join(D, 'window.json'))); E0, N0, S, zone = w['E0'], w['N0'], w['size'], w['zone']
td = os.path.join(D, 'aerial_tiles'); idx = json.load(open(os.path.join(td, 'index.json'))); z = idx['z']
x0, x1, y0, y1 = idx['x0'], idx['x1'], idx['y0'], idx['y1']
mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.uint8); miss = 0
for ty in range(y0, y1 + 1):
    for tx in range(x0, x1 + 1):
        p = os.path.join(td, f'{z}_{tx}_{ty}.jpg')
        if not os.path.exists(p): miss += 1; continue
        mos[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = np.asarray(Image.open(p).convert('RGB').resize((256, 256)))
print('mosaic', mos.shape, 'missing tiles', miss)
PX = int(sys.argv[3]) if len(sys.argv) > 3 else 2000; res = S / PX
cols = E0 + (np.arange(PX) + 0.5) * res; rows = N0 - (np.arange(PX) + 0.5) * res
EE, NN = np.meshgrid(cols, rows); lon, lat = mga2ll(EE, NN, zone); n = 2 ** z
gx = (lon + 180) / 360 * n * 256 - x0 * 256
gy = (1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * n * 256 - y0 * 256
out = np.stack([ndimage.map_coordinates(mos[..., c].astype(np.float32), [gy - 0.5, gx - 0.5], order=1, mode='nearest') for c in range(3)], -1)
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT, quality=86)
print('saved', OUT, PX, 'px,', res, 'm per pixel; source', round(156543.034 * math.cos(math.radians(w['centre_lat'])) / n, 2), 'm per pixel')

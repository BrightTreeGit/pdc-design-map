"""Vegetation structure zones from the 2022 LiDAR canopy grid (canopy_grid.png: R = height x 3, G = gap fraction x 255, 2 m cells).

Classes: height of the tallest layer (Specht / NVIS height bands), plus gaps where the canopy opens up. Smoothed over about 10 m so the zones read as patches, not single trees.

usage: python3 scripts/analysis/veg_structure.py map        -> map/veg.png, map/veg.json
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from matplotlib.path import Path

CLASSES = [  # id, label, rgba, what it means for design
    (1, 'Open ground: grass, gardens, bare (under 2 m)', (236, 220, 140, 150), 'Pasture, lawn, gardens, tracks, recent clearing. Sun all day; the easiest ground to plant into.'),
    (2, 'Shrubs and young regrowth (2-5 m)', (200, 214, 96, 165), 'Lantana, wattle and young regrowth. Often the first place to work: clear weeds, keep the natives, plant into the gaps.'),
    (3, 'Low or young forest (5-15 m)', (150, 195, 85, 175), 'Regrowth and young forest. Good shelter belts and edges; thin selectively for light.'),
    (4, 'Mid forest (15-25 m)', (90, 165, 75, 180), 'Established forest. Shade-tolerant understorey, bush food, habitat; the canopy closes over most plantings.'),
    (5, 'Tall forest (25-35 m)', (45, 130, 70, 190), 'Mature eucalypt forest. Keep buildings, tanks and tracks out of falling distance of the big trees.'),
    (6, 'Very tall forest (over 35 m)', (25, 95, 75, 200), 'Emergent giants: the oldest, most valuable habitat trees on the block.'),
    (7, 'Gaps in the forest canopy', (250, 170, 60, 200), 'Places inside the forest where the canopy opens up (less than three-quarters cover): light wells for planting, or recent tree fall.'),
]

def main(folder):
    a = np.array(Image.open(os.path.join(folder, 'canopy_grid.png')).convert('RGBA')).astype(np.float32)
    h = a[..., 0] / 3.0; cover = 1 - a[..., 1] / 255.0
    hs = ndimage.median_filter(h, size=5); cs = ndimage.uniform_filter(cover, size=5)
    c = np.zeros(h.shape, np.uint8)
    for i, lo, hi in [(1, -1, 2), (2, 2, 5), (3, 5, 15), (4, 15, 25), (5, 25, 35), (6, 35, 999)]:
        c[(hs >= lo) & (hs < hi)] = i
    c[(hs >= 5) & (cs < 0.75)] = 7       # the LiDAR sees almost closed canopy across most forest, so open patches stand out
    c = ndimage.median_filter(c, size=5)                       # tidy speckle into patches
    img = np.zeros((*c.shape, 4), np.uint8)
    for i, _, col, _ in CLASSES: img[c == i] = col
    Image.fromarray(img, 'RGBA').save(os.path.join(folder, 'veg.png'), optimize=True)
    T = json.load(open(os.path.join(folder, 'terrain.json')))
    pts = np.array(T['lot'], float).reshape(-1, 2) / 2
    yy, xx = np.mgrid[0:1000, 0:1000]
    m = Path(pts).contains_points(np.c_[xx.ravel() + .5, yy.ravel() + .5]).reshape(1000, 1000)
    n = m.sum()
    out = {'source': '2022 LiDAR canopy height and cover (Sunshine Coast LiDAR, ELVIS), computed by the map, 24 Oct 2026',
           'classes': [{'id': i, 'label': l, 'rgba': list(col), 'note': note, 'lotHa': round(float(((c == i) & m).sum() * 4 / 1e4), 2), 'lotShare': round(float(((c == i) & m).sum() / n), 3)} for i, l, col, note in CLASSES]}
    json.dump(out, open(os.path.join(folder, 'veg.json'), 'w'))
    for k in out['classes']: print(f"{k['label']:40s} {k['lotHa']:5.2f} ha  {k['lotShare']*100:4.1f}%")


if __name__ == '__main__':
    main(sys.argv[1])

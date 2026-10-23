"""Bronwen's hand sketch -> a design overlay warped onto the lot, plus map features (sketch positions, buildings from the photo)."""
import json, cv2, numpy as np
S = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
SRC = '/mnt/user-data/attachments/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/577ac3ff-image.jpg'
im = cv2.rotate(cv2.imread(SRC), cv2.ROTATE_90_COUNTERCLOCKWISE)        # north to the right, street on the left
K = im.shape[1] / 2000.0                                                 # sketch coords below are on a 2000-wide view
sk = np.float32([[358, 78], [1945, 15], [1995, 835], [358, 855]]) * K     # SW, NW, NE, SE corners of the drawn lot
mp = np.float32([[983.2, 1012.3], [988.6, 976.9], [1010.2, 980.3], [1001.9, 1014.3]])   # same corners on the map (m)
# fit on the lot corners plus the house and big-shed corners matched to the satellite photo (the sketch isn't to scale)
skv = np.float32([[358, 78], [1945, 15], [1995, 835], [358, 855],
                  [612, 145], [1080, 145], [1080, 400], [612, 400],
                  [1310, 285], [1475, 285], [1475, 520], [1310, 520]])
mpv = np.float32([[983.2, 1012.3], [988.6, 976.9], [1010.2, 980.3], [1001.9, 1014.3],
                  [987.0, 1003.9], [987.7, 990.1], [1000.9, 990.7], [1000.2, 1006.0],
                  [995.5, 987.6], [995.5, 981.4], [1001.6, 981.4], [1001.6, 987.6]])
# piecewise-affine warp: exact at every matched corner, smooth in between (the sketch isn't to scale)
from skimage.transform import PiecewiseAffineTransform, warp as skwarp
ext = lambda pts, far: np.vstack([pts, far])
FARs = np.float32([[0, -400], [2600, -400], [2600, 1400], [0, 1400]])        # far-out anchors so the edges extrapolate gently
H0, _ = cv2.findHomography(skv, mpv, 0); FARm = cv2.perspectiveTransform(FARs[None], H0)[0]
PA = PiecewiseAffineTransform(); PA.estimate(ext(skv, FARs), ext(mpv, FARm))          # view -> map
PAi = PiecewiseAffineTransform(); PAi.estimate(ext(mpv, FARm), ext(skv, FARs))        # map -> view
X0, Y0, PPM = 976.0, 970.0, 25.0                                         # overlay image: north-up, 25 px per metre
Wd, Ht = int(42 * PPM), int(50 * PPM)
yy, xx = np.mgrid[0:Ht, 0:Wd]
mxy = np.c_[X0 + (xx.ravel() + .5) / PPM, Y0 + (yy.ravel() + .5) / PPM]
vxy = PAi(mxy) * K
mapx = vxy[:, 0].reshape(Ht, Wd).astype(np.float32); mapy = vxy[:, 1].reshape(Ht, Wd).astype(np.float32)
warp = cv2.remap(im, mapx, mapy, cv2.INTER_LINEAR, borderValue=(255, 255, 255))
mask = cv2.remap(np.full(im.shape[:2], 255, np.uint8), mapx, mapy, cv2.INTER_NEAREST, borderValue=0)
g = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY)
bgp = cv2.GaussianBlur(cv2.dilate(g, np.ones((15, 15), np.uint8)), (0, 0), 25)          # local paper brightness
alpha = np.clip((bgp.astype(int) - g.astype(int) - 6) * 14, 0, 255).astype(np.uint8)     # paper -> transparent, pencil and colour stay
b_, g_, r_ = [warp[..., i].astype(int) for i in range(3)]
alpha[(r_ - b_ > 50) & (g_ - b_ > 15)] = 0                                                 # the wooden table round the page
Tl = json.load(open('/home/claude/pdc-design-map/map/sites/annwn/terrain.json'))
lot = np.array([[(x - X0) * PPM, (y - Y0) * PPM] for x, y in np.array(Tl['lot']).reshape(-1, 2)], np.int32)
clip = np.zeros_like(mask); cv2.fillPoly(clip, [lot], 255); clip = cv2.dilate(clip, np.ones((13, 13), np.uint8))   # lot plus 0.25 m
alpha = np.where((mask > 0) & (clip > 0), alpha, 0).astype(np.uint8)
warp = cv2.convertScaleAbs(warp, alpha=1.0, beta=-40)                                      # darken lines a touch so they read on the photo
rgba = np.dstack([warp, alpha]); cv2.imwrite(S + 'annwn_sketch_overlay.png', rgba)
print('overlay', Wd, Ht, 'a', 1 / PPM, 'c', X0, 'd', Y0)

def P(x, y):
    v = PA(np.array([[x, y]], float))[0]; return [round(float(v[0]), 1), round(float(v[1]), 1)]
def rect(x0, y0, x1, y1): return [P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)]
# photo (Google screenshot, 1000-wide view) -> map, for the existing buildings
A = complex(0.045044294080371576, 0.0021009386177184308); C = complex(929.3368323459488, 954.4538337876861)
def G(x, y):
    m = A * complex(x * 2.292, y * 2.292) + C; return [round(m.real, 1), round(m.imag, 1)]
NOTE = " (From Bronwen's hand sketch, 24 Oct 2026; position approximate: drag to fit.)"
PH = " (Traced from the satellite photo; drag to fit.)"
F = {}
def add(i, kind, name, geom, notes, status='idea', stage='now'):
    F[i] = {'kind': kind, 'name': name, 'geom': geom, 'notes': notes, 'status': status, 'stage': stage, 'source': "Bronwen's sketch (24 Oct 2026)", 'createdAt': '2026-10-23T22:30:00.000Z', 'updatedAt': '2026-10-23T22:30:00.000Z', 'createdBy': None}
add('an01', 'building', 'House (solar panels)', {'g': 'polygon', 'pts': [G(580, 318), G(676, 318), G(676, 400), G(708, 400), G(708, 466), G(580, 452)]}, 'Existing house with solar panels; front door to the street (south), back door on the east side.' + PH, 'built', 'existing')
add('an02', 'shed', 'Shed (north)', {'g': 'polygon', 'pts': [G(652, 231), G(713, 231), G(713, 288), G(652, 288)]}, 'Existing shed in the back yard.' + PH, 'built', 'existing')
add('an03', 'shed', 'Small shed (north-west)', {'g': 'polygon', 'pts': [G(595, 270), G(618, 270), G(618, 305), G(595, 305)]}, 'Small shed by the west fence, with sugar cane beside it.' + PH, 'built', 'existing')
add('an04', 'hedge', 'Camellia hedge (west side)', {'g': 'line', 'pts': [P(660, 120), P(1085, 120)]}, 'Camellias along the west fence beside the house.' + NOTE, 'built', 'existing')
add('an05', 'hedge', 'Camellia (front garden)', {'g': 'line', 'pts': [P(560, 160), P(560, 320)]}, 'Camellias in the front garden by the driveway.' + NOTE, 'built', 'existing')
for i, (n, x, y) in enumerate([('Tahitian lime', 822, 660), ('Imperial mandarin', 1055, 715), ('Jaboticaba', 1168, 715), ('Valencia orange', 1285, 715)]):
    add(f'an1{i}', 'fruittree', n, {'g': 'point', 'pts': [P(x, y)]}, f'{n} in the east-side garden.' + NOTE, 'built', 'existing')
add('an14', 'tree', 'Callistemon (bottlebrush)', {'g': 'point', 'pts': [P(1265, 595)]}, 'Bottlebrush: nectar for birds and bees.' + NOTE, 'built', 'existing')
add('an15', 'tree', 'Large existing tree (front garden)', {'g': 'point', 'pts': [P(690, 712)]}, 'The big tree in the front garden, east of the driveway.' + NOTE, 'built', 'existing')
add('an16', 'fruittree', 'Jiro persimmon', {'g': 'point', 'pts': [P(1378, 100)]}, 'Jiro persimmon (non-astringent) near the north-west corner.' + NOTE)
add('an17', 'fruittree', 'Goldfinger banana', {'g': 'point', 'pts': [P(1570, 182)]}, 'Goldfinger banana clump near the back fence.' + NOTE)
add('an18', 'shrub', 'Sugar cane', {'g': 'point', 'pts': [P(1205, 60)]}, 'Sugar cane along the west fence by the small shed.' + NOTE)
add('an19', 'shrub', 'Bay tree', {'g': 'point', 'pts': [P(850, 478)]}, 'Bay beside the back step.' + NOTE)
add('an20', 'shrub', 'Rosemary', {'g': 'point', 'pts': [P(850, 520)]}, 'Rosemary by the back of the house.' + NOTE)
add('an21', 'shrub', 'Rosemary', {'g': 'point', 'pts': [P(850, 560)]}, 'Rosemary by the back of the house.' + NOTE)
add('an22', 'raisedbed', 'Wicking bed (by the clothes line)', {'g': 'polygon', 'pts': rect(1147, 215, 1188, 305)}, 'Wicking bed north-east of the house.' + NOTE, 'built', 'existing')
add('an23', 'raisedbed', 'Wicking bed (east garden)', {'g': 'polygon', 'pts': rect(818, 750, 915, 778)}, 'Wicking bed in the east-side garden.' + NOTE, 'built', 'existing')
add('an24', 'herbs', 'Long bed (front, east side)', {'g': 'polygon', 'pts': rect(578, 610, 688, 633)}, 'The long blue bed on the sketch: a narrow garden bed or water feature (check with Bronwen).' + NOTE)
add('an25', 'clothesline', 'Clothes line', {'g': 'point', 'pts': [P(1215, 385)]}, 'Clothes line between the house and the shed.' + NOTE, 'built', 'existing')
for i, (x, y) in enumerate([(520, 625), (385, 730), (435, 808)]):
    add(f'an3{i}', 'shrub', 'Rockery shrub', {'g': 'point', 'pts': [P(x, y)]}, 'Shrub in the front rockery garden (south-east corner).' + NOTE, 'built', 'existing')
add('an33', 'structure', 'Round feature, north-east corner (check)', {'g': 'point', 'pts': [P(1612, 795)]}, 'A circle drawn in the north-east corner: a tank, tree or compost bin? Check with Bronwen.' + NOTE)
json.dump(F, open(S + 'annwn_features.json', 'w'))
for k, v in F.items(): print(k, v['name'], v['geom']['pts'][:1])

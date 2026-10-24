"""Ange's updated plan (24 Oct 2026): mask private text, fit to the lot, warp north-up at 5 cm/px, write the overlay PNG + placement JSON.
usage: python3 plan2.py   (reads the photo path below; writes ange_plan2.png / ange_plan2.json / planH2.json here)"""
import json, numpy as np, cv2, os
SRC = '/mnt/user-data/attachments/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/38e37859-image.jpg'
HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, '../../../../map/sites/nac/terrain.json')))
L = np.array(T['lot']).reshape(-1, 2)
im = cv2.imread(SRC)
# ---- privacy: paint over the address line and the street names before anything else is made from this photo
for (x0, y0, x1, y1) in [(520, 655, 1060, 712), (10, 220, 75, 510), (520, 612, 760, 660), (1270, 500, 1400, 650), (40, 40, 160, 110)]:
    cv2.rectangle(im, (x0, y0), (x1, y1), (255, 255, 255), -1)
cv2.imwrite(os.path.join(HERE, 'plan2_masked.jpg'), im, [cv2.IMWRITE_JPEG_QUALITY, 92])
# ---- fit: sketch pixels -> map metres (lot corners from the cadastre, house corners from the recent satellite image)
ga, gc, gd = 0.062325, 934.8, 955.9; gx0, gy0 = 353, 348   # google overlay placement + crop offset used when reading the house
def gmap(cx, cy): return [(cx + gx0) * ga + gc, (cy + gy0) * ga + gd]
house_map = [gmap(700, 258), gmap(975, 290), gmap(960, 470), gmap(695, 440)]
src = np.float32([[120, 222], [1250, 204], [1338, 310], [1274, 598], [140, 595], [95, 480], [725, 262], [1065, 262], [1065, 492], [725, 492]])
dst = np.float32([L[10], L[9], L[8], L[13], L[12], L[11]] + house_map)
H, _ = cv2.findHomography(src, dst, 0)
pr = cv2.perspectiveTransform(src[None], H)[0]
print('residuals m:', np.hypot(*(pr - dst).T).round(1))
json.dump({'H': H.tolist()}, open(os.path.join(HERE, 'planH2.json'), 'w'))
# ---- warp north-up
x0, y0 = L[:, 0].min() - 8, L[:, 1].min() - 8; x1, y1 = L[:, 0].max() + 8, L[:, 1].max() + 8; res = 0.05
W, Hh = int((x1 - x0) / res), int((y1 - y0) / res)
Tm = np.array([[1 / res, 0, -x0 / res], [0, 1 / res, -y0 / res], [0, 0, 1]])
out = cv2.warpPerspective(im, Tm @ H, (W, Hh), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
o = cv2.cvtColor(out, cv2.COLOR_BGR2RGB).astype(np.float32)
bg = cv2.GaussianBlur(o, (0, 0), 25); n = np.clip(o / np.maximum(bg, 1) * 235, 0, 255)
dark = 255 - n.min(axis=2); sat = n.max(axis=2) - n.min(axis=2)
a = np.clip(np.maximum(dark - 10, 0) * 7 + sat * 5, 0, 255); st = np.clip(n - (255 - n) * 1.2, 0, 255); a = np.maximum(a, 95)
rgba = np.dstack([st, a]).astype(np.uint8)
mask = cv2.warpPerspective(np.full(im.shape[:2], 255, np.uint8), Tm @ H, (W, Hh)); rgba[..., 3] = np.minimum(rgba[..., 3], mask)
lm = np.zeros((Hh, W), np.uint8); cv2.fillPoly(lm, [((L - [x0, y0]) / res).astype(np.int32)], 255)
lm = cv2.dilate(lm, np.ones((3, 3), np.uint8), iterations=int(4 / res)); lm = cv2.GaussianBlur(lm, (0, 0), 6)
rgba[..., 3] = (rgba[..., 3].astype(np.float32) * lm / 255).astype(np.uint8)
cv2.imwrite(os.path.join(HERE, 'ange_plan2.png'), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
json.dump({'x0': float(x0), 'y0': float(y0), 'res': res, 'w': W, 'h': Hh}, open(os.path.join(HERE, 'ange_plan2.json'), 'w'))
print(W, Hh, os.path.getsize(os.path.join(HERE, 'ange_plan2.png')) // 1024, 'kB')

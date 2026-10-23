"""Build a site's photo-history slider (map/sites/<site>/history/) from the files fetch_site_history.py downloads.

usage: python3 scripts/analysis/build_photo_history.py <site-id> "<...>/<Site>/Aerial and Google Maps"

- Government orthophotos (history/*.jpg) are already map-accurate: they are just cut to the map square.
- Old film photos (old_photos/wide/*.jpg) come from the archive with only rough positions, so each one is
  pinned to the 2008 (or 1994) orthophoto by matching landmarks (SIFT features + RANSAC homography),
  first over the whole 5 km frame, then again close to the block for a tighter local fit. Photos that
  only match other old photos are chained through them. Anything that can't be pinned reliably is left out.
Output: 1600 x 1600 px images of a 1000 m square centred on the block, plus history.json.
"""
import sys, os, json, glob, hashlib
import numpy as np, cv2

SIZE_M, OUT_PX = 1000, 1600
site, src = sys.argv[1], sys.argv[2]
repo = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sdir = os.path.join(repo, 'map', 'sites', site); out = os.path.join(sdir, 'history'); os.makedirs(out, exist_ok=True)
T = json.load(open(os.path.join(sdir, 'terrain.json')))
E0, N0 = T['E0'], T['N0']
lot = np.array(T['lot'], float).reshape(-1, 2)
cx_m, cy_m = lot.mean(0)                                  # block centre, map metres
x0 = int(np.clip(round(cx_m - SIZE_M / 2), 0, 2000 - SIZE_M)); y0 = int(np.clip(round(cy_m - SIZE_M / 2), 0, 2000 - SIZE_M))
k = SIZE_M / OUT_PX
# output pixel -> MGA:  E = E0 + x0 + i*k ,  N = N0 - (y0 + j*k)
OUT2MGA = np.array([[k, 0, E0 + x0], [0, -k, N0 - y0], [0, 0, 1.]])


def grid2mga(cx, cy, size_m, px):
    s = size_m / px
    return np.array([[s, 0, cx - size_m / 2], [0, -s, cy + size_m / 2], [0, 0, 1.]])


def warp(img, src2mga):
    M = np.linalg.inv(src2mga) @ OUT2MGA                   # output px -> source px
    return cv2.warpPerspective(img, M, (OUT_PX, OUT_PX), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP)


runs = []
# ---------------- orthophotos
H = json.load(open(os.path.join(src, 'history', 'history.json')))
hcx, hcy = H['centre_mga56']; seen = set()
for r in sorted(H['runs'], key=lambda r: (r['year'], r['id'])):
    p = os.path.join(src, 'history', r['file'])
    if not os.path.exists(p): continue
    dig = hashlib.md5(open(p, 'rb').read()).hexdigest()
    if dig in seen: continue                               # the archive sometimes lists one survey twice
    seen.add(dig)
    im = cv2.imread(p); w = warp(im, grid2mga(hcx, hcy, H['size_m'], im.shape[1]))
    cover = float((w.max(2) > 8).mean())
    if cover < 0.3: continue
    fn = f"h{r['year']}_{r['id']}.jpg"; cv2.imwrite(os.path.join(out, fn), w, [cv2.IMWRITE_JPEG_QUALITY, 80])
    runs.append({'y': r['year'], 'id': r['id'], 'from': r['from'], 'to': r['to'], 'res': round(r['res_m'] / 100, 3) if r['res_m'] > 20 else r['res_m'],
                 'f': fn, 'name': r['name'], 'cover': round(cover, 2)})
    print('ortho', fn, round(cover, 2))

# ---------------- old film photos
O = json.load(open(os.path.join(src, 'old_photos', 'old_photos.json')))
ocx, ocy = O['centre_mga56']; WM, WPX = O['wide_m'], O['wide_px']
W2MGA = grid2mga(ocx, ocy, WM, WPX)
S = 0.5                                                    # match at half resolution (2.5 m/px)
sift = cv2.SIFT_create(9000)
clahe = cv2.createCLAHE(3, (8, 8))


def feats(path):
    g = cv2.imread(path, 0); g = cv2.resize(g, None, fx=S, fy=S, interpolation=cv2.INTER_AREA); g = clahe.apply(g)
    kp, d = sift.detectAndCompute(g, (g > 5).astype(np.uint8) * 255)
    d = np.sqrt(d / (d.sum(1, keepdims=True) + 1e-7)).astype(np.float32)   # RootSIFT: steadier across film and colour
    return np.float32([q.pt for q in kp]) / S, d          # keypoints in full-res wide pixels


flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=64))
def homog(fa, fb, ratio=0.8):
    (pa, da), (pb, db) = fa, fb
    if len(da) < 10 or len(db) < 10: return None, 0
    g = [m[0] for m in flann.knnMatch(da, db, k=2) if len(m) == 2 and m[0].distance < ratio * m[1].distance]
    if len(g) < 12: return None, 0
    A = pa[[x.queryIdx for x in g]]; B = pb[[x.trainIdx for x in g]]
    Hm, mask = cv2.findHomography(A, B, cv2.USAC_MAGSAC, 10.0, maxIters=10000, confidence=0.9999)
    if Hm is None or not well(Hm): return None, 0
    return Hm, int(mask.sum())


def well(Hm):                                              # a plausible photo-to-photo fit, not a degenerate one
    sc = np.sqrt(abs(np.linalg.det(Hm[:2, :2])))
    return 0.25 < sc < 4 and np.abs(Hm[2, :2]).max() < 3e-4


def sane(Hm):                                              # the block lands inside the frame at a sensible scale
    sc = np.sqrt(abs(np.linalg.det(Hm[:2, :2])))
    c = Hm @ np.array([WPX / 2, WPX / 2, 1.]); c = c[:2] / c[2]
    return 0.5 < sc < 2 and np.hypot(*(c - WPX / 2)) < WPX * 0.45


wd = os.path.join(src, 'old_photos', 'wide')
nodes = {}
for f in sorted(glob.glob(os.path.join(wd, 'ref_*.jpg'))): nodes['ref' + os.path.basename(f)[4:8]] = feats(f)
olds = {r['id']: r for r in O['runs'] if os.path.exists(os.path.join(src, 'old_photos', r['file']))}
for i, r in olds.items(): nodes[i] = feats(os.path.join(src, 'old_photos', r['file']))
keys = list(nodes); E = {}
for a in range(len(keys)):                                 # every pair: which photos share enough landmarks?
    for b in range(a + 1, len(keys)):
        ka, kb = keys[a], keys[b]
        if isinstance(ka, str) and isinstance(kb, str): continue
        Hm, n = homog(nodes[ka], nodes[kb])
        if n >= 18:
            E.setdefault(ka, []).append((kb, Hm, n)); E.setdefault(kb, []).append((ka, np.linalg.inv(Hm), n))
print('photo pairs that match:', sum(len(v) for v in E.values()) // 2, flush=True)
# strongest chain from the orthophotos (refs are already map-aligned: identity) to each old photo
import heapq
Hs = {}; how = {}; W = {}; h = []
for k in keys:
    if isinstance(k, str): Hs[k] = np.eye(3); W[k] = 10 ** 6; heapq.heappush(h, (-W[k], str(k), k))
done = set()
while h:
    w, _, k = heapq.heappop(h); w = -w
    if k in done: continue
    done.add(k)
    for m, Hkm, n in E.get(k, []):                         # Hkm maps k -> m ; we need m -> ref = Hs[k] @ inv(Hkm)
        if m in done: continue
        cand = min(w, n)
        if cand > W.get(m, 0):
            W[m] = cand; Hs[m] = Hs[k] @ np.linalg.inv(Hkm); heapq.heappush(h, (-cand, str(m), m))
            how[m] = (f"{k}" if isinstance(k, str) else f"via {olds[k]['year']}") + f" (weakest link {cand} matches)"
# local refinement: warp each pinned photo onto the ortho frame, then re-match near the block only
cen = np.array([WPX / 2, WPX / 2]); RAD = 1500 / (WM / WPX)
refk = sorted(k for k in keys if isinstance(k, str))
for i in olds:
    if i not in Hs: continue
    im = cv2.imread(os.path.join(src, 'old_photos', olds[i]['file']), 0)
    wimg = cv2.warpPerspective(im, Hs[i], (WPX, WPX), flags=cv2.INTER_LINEAR)
    tmp = os.path.join('/tmp', f'_w{i}.png'); cv2.imwrite(tmp, wimg); fw = feats(tmp); os.remove(tmp)
    best = (None, 0)
    for rk in refk:
        Hm, n = homog(fw, nodes[rk], 0.85)
        if Hm is None: continue
        pa = fw[0]; c = (Hm @ np.r_[cen, 1])[:2] / (Hm @ np.r_[cen, 1])[2]
        if n > best[1] and np.hypot(*(c - cen)) < 120: best = (Hm, n)
    if best[1] >= 15:
        Hs[i] = best[0] @ Hs[i]; how[i] += f", refined on {best[1]} local matches"
for i, r in sorted(olds.items(), key=lambda t: t[1]['year']):
    if i not in Hs or not sane(Hs[i]): print('old ', r['year'], 'could not be pinned - left out'); continue
    im = cv2.imread(os.path.join(src, 'old_photos', r['file']))
    w = warp(im, W2MGA @ Hs[i]); cover = float((w.max(2) > 8).mean())
    if cover < 0.3: print('old ', r['year'], 'pinned but the block is mostly outside the frame - left out'); continue
    bw = bool(np.abs(w[..., 0].astype(int) - w[..., 2]).mean() < 4)
    fn = f"o{r['year']}_{i}.jpg"; cv2.imwrite(os.path.join(out, fn), w, [cv2.IMWRITE_JPEG_QUALITY, 80])
    runs.append({'y': r['year'], 'id': i, 'from': r['date'], 'to': r['date'], 'res': float(r['scan_res_m'] or 0), 'f': fn,
                 'name': r['frame'], 'old': True, 'bw': bw, 'cover': round(cover, 2), 'pinned': how[i]})
    print('old ', fn, how[i], round(cover, 2))

runs.sort(key=lambda r: (r['y'], r['from']))
json.dump({'x0': x0, 'y0': y0, 'size': SIZE_M, 'source': 'State of Queensland: TimeSeries AerialOrtho and QImagery historical aerial photography (CC BY 4.0)', 'runs': runs},
          open(os.path.join(out, 'history.json'), 'w'), indent=0)
print(len(runs), 'photos ->', out)

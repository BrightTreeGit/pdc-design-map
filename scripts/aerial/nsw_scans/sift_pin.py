"""Pin a scan by SIFT feature matching against an already-pinned neighbouring year (window image over 2000 m).
usage: python3 sift_pin.py <site> <year> <scans-dir> <ref-window.jpg> <out-dir>"""
import sys, json, pathlib, cv2, numpy as np
site, yr, sdir, refp, odir = sys.argv[1:6]
FP = json.load(open(pathlib.Path(__file__).with_name('footprints.json')))[site]
img, denom, bb = FP[yr]; cx, cy = FP['centre']
S = cv2.imread(str(next(pathlib.Path(sdir).glob(f'{yr}_{img}.jpg'))), 0); pm = denom * .23 / S.shape[1]
R = cv2.imread(refp, 0); RM = 2000 / R.shape[1]
W = 2.0; cl = cv2.createCLAHE(2.0, (8, 8))
Rw = cl.apply(cv2.resize(R, None, fx=RM / W, fy=RM / W, interpolation=cv2.INTER_AREA))
f = pm / W; Sw = cl.apply(cv2.resize(S, None, fx=f, fy=f, interpolation=cv2.INTER_AREA))
pc = np.array([(cx - bb[0]) / (bb[2] - bb[0]) * Sw.shape[1], (bb[3] - cy) / (bb[3] - bb[1]) * Sw.shape[0]])
r = int(3500 / W); x0, y0 = int(max(0, pc[0] - r)), int(max(0, pc[1] - r))
sub = Sw[y0:int(pc[1] + r), x0:int(pc[0] + r)]
sift = cv2.SIFT_create(nfeatures=30000, contrastThreshold=0.015)
ka, da = sift.detectAndCompute(Rw, None); kb, db = sift.detectAndCompute(sub, None)
m = cv2.FlannBasedMatcher({'algorithm': 1, 'trees': 5}, {'checks': 64}).knnMatch(da, db, k=2)
good = [a for a, b in m if a.distance < 0.8 * b.distance]
pa = np.float32([ka[g.queryIdx].pt for g in good]); pb = np.float32([kb[g.trainIdx].pt for g in good]) + [x0, y0]
M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=5, maxIters=50000, confidence=0.999)
n = int(inl.sum()); s = np.hypot(M[0, 0], M[1, 0]); ang = np.degrees(np.arctan2(M[1, 0], M[0, 0]))
sel = inl.ravel().astype(bool)
H = np.vstack([M, [0, 0, 1]])
if n >= 20:
    H2, _ = cv2.findHomography(pa[sel], pb[sel], cv2.RANSAC, 4.0)
    if H2 is not None: H = H2
print(f'{site} {yr}: {len(good)} candidates, {n} agree, scale {s:.3f}, turn {ang:.1f}', flush=True)
# map m -> ref work px (/W) -> scan work px (H) -> scan full px (/f)
Hm2s = np.diag([1 / f, 1 / f, 1]) @ H @ np.diag([1 / W, 1 / W, 1])
O = 1600; Do = np.diag([2000 / O, 2000 / O, 1.0])
out = cv2.warpPerspective(S, Hm2s @ Do, (O, O), flags=cv2.INTER_AREA | cv2.WARP_INVERSE_MAP)
pathlib.Path(odir).mkdir(parents=True, exist_ok=True)
cv2.imwrite(f'{odir}/n{yr}_scan.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 84])
fj = pathlib.Path(odir) / 'fits.json'; res = json.load(open(fj)) if fj.exists() else {}
res[yr] = {'img': img, 'scale': denom, 'sift_inliers': n, 'H_map_to_scan': Hm2s.tolist(), 'ref': refp}
json.dump(res, open(fj, 'w'), indent=1)

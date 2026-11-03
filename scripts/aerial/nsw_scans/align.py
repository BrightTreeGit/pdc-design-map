"""Pin a raw NSW scanned aerial frame onto a site's map window by matching features against the site's current aerial.jpg.
usage: python3 align.py <scan.jpg> <map-site> <scale-denominator> [out.json]
Prints inlier count and the fitted transform (scan px -> map metres)."""
import sys, json, cv2, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
scan, site, denom = sys.argv[1], sys.argv[2], float(sys.argv[3])
ROOT = '/home/claude/pdc-design-map/map/sites/'
REF_M = 2000 / 3000                      # aerial.jpg: 3000 px over the 2000 m window
WORK = 2.0                               # metres per pixel for matching
ref = cv2.imread(ROOT + site + '/aerial.jpg', cv2.IMREAD_GRAYSCALE)
ref = cv2.resize(ref, None, fx=REF_M / WORK, fy=REF_M / WORK, interpolation=cv2.INTER_AREA)
im = cv2.imread(scan, cv2.IMREAD_GRAYSCALE)
px_m = denom * 0.23 / im.shape[1]        # nominal ground metres per scan pixel (23 cm frame)
f = px_m / WORK
sm = cv2.resize(im, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
cl = cv2.createCLAHE(3.0, (8, 8))
A, B = cl.apply(ref), cl.apply(sm)
sift = cv2.SIFT_create(nfeatures=40000, contrastThreshold=0.01)
ka, da = sift.detectAndCompute(A, None); kb, db = sift.detectAndCompute(B, None)
m = cv2.BFMatcher().knnMatch(da, db, k=2)
good = [a for a, b in m if a.distance < 0.85 * b.distance]
pa = np.float32([ka[g.queryIdx].pt for g in good]); pb = np.float32([kb[g.trainIdx].pt for g in good])
best = None
for _ in range(3):
    M, inl = cv2.estimateAffinePartial2D(pb, pa, method=cv2.RANSAC, ransacReprojThreshold=4, maxIters=20000, confidence=0.999)
    n = int(inl.sum()) if inl is not None else 0
    if M is not None and (best is None or n > best[1]): best = (M, n, inl)
M, n, inl = best
s = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
print(f'{scan.split("/")[-1]}: {len(good)} candidate matches, {n} agree; scale {s:.3f} (1 = nominal), turn {rot:.1f} deg')
# refine with full homography on the inliers (allows tilt), if enough
sel = inl.ravel().astype(bool)
H = np.vstack([M, [0, 0, 1]])
if n >= 25:
    H2, inl2 = cv2.findHomography(pb[sel], pa[sel], cv2.RANSAC, 3.0)
    if H2 is not None: H = H2
# scan full-res px -> work px -> ref work px -> map metres
T = np.diag([WORK, WORK, 1]) @ H @ np.diag([f, f, 1])
if len(sys.argv) > 4:
    json.dump({'scan': scan, 'site': site, 'inliers': n, 'scale': s, 'turn': rot, 'T': T.tolist()}, open(sys.argv[4], 'w'))

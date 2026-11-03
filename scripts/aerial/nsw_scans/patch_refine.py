"""Refine a pinned scan with many small local matches across the whole 2 km window (houses, roads, clearings,
creek bends, inside and outside the lot), then fit one affine correction with RANSAC.
usage: python3 patch_refine.py <map-site> <scan.jpg> <fits.json> <year> <out-window.jpg>"""
import sys, json, cv2, numpy as np
site, scan, fitsp, yr, outp = sys.argv[1:6]
import os
R = cv2.imread(os.environ.get('REFWIN', f'/home/claude/pdc-design-map/map/sites/{site}/aerial.jpg'), 0)   # or a pinned neighbouring year
R = cv2.resize(R, (2000, 2000), interpolation=cv2.INTER_AREA)             # 1 m per pixel
S = cv2.imread(scan, 0); H = np.array(json.load(open(fitsp))[yr]['H_map_to_scan'])
W = cv2.warpPerspective(S, H, (2000, 2000), flags=cv2.INTER_AREA | cv2.WARP_INVERSE_MAP)
cl = cv2.createCLAHE(2.5, (8, 8))
def bp(g):
    g = cl.apply(g).astype(np.float32); g = g - cv2.GaussianBlur(g, (0, 0), 20); return cv2.GaussianBlur(g, (0, 0), 1.2)
Rb, Wb = bp(R), bp(W); valid = W > 8
P, SR = 70, int(os.environ.get('SR', 70))          # half patch, search radius (m)
src, dst, sc = [], [], []
for cy in range(P + SR, 2000 - P - SR, 50):
    for cx in range(P + SR, 2000 - P - SR, 50):
        if not valid[cy - P - SR:cy + P + SR, cx - P - SR:cx + P + SR].all(): continue
        T = Rb[cy - P:cy + P, cx - P:cx + P]
        if T.std() < 1e-3: continue
        A = Wb[cy - P - SR:cy + P + SR, cx - P - SR:cx + P + SR]
        r = cv2.matchTemplate(A, T, cv2.TM_CCOEFF_NORMED)
        _, m1, _, l1 = cv2.minMaxLoc(r)
        r2 = r.copy(); cv2.circle(r2, l1, 12, -1, -1); m2 = r2.max()
        if m1 < 0.12 or m1 - m2 < 0.04: continue      # weak or ambiguous
        dx, dy = l1[0] - SR, l1[1] - SR                 # ref patch appears in W shifted by (dx,dy)
        src.append([cx + dx, cy + dy]); dst.append([cx, cy]); sc.append(m1)
src, dst = np.float32(src), np.float32(dst)
print(f'{yr}: {len(src)} confident local matches')
M, inl = (cv2.estimateAffinePartial2D if os.environ.get('MODEL') == 'similar' else cv2.estimateAffine2D)(src, dst, method=cv2.RANSAC, ransacReprojThreshold=6, maxIters=20000, confidence=0.999)
n = int(inl.sum()); res = np.linalg.norm((src[inl.ravel() == 1] @ M[:, :2].T + M[:, 2]) - dst[inl.ravel() == 1], axis=1)
moved = np.linalg.norm(np.array([1000, 1000]) @ M[:, :2].T + M[:, 2] - [1000, 1000])
print(f'   {n} agree (typical leftover error {np.median(res):.1f} m); centre moves {moved:.0f} m; corr {M.round(4).tolist()}')
# corrected map->scan: map m -> W px via inverse of M
Minv = cv2.invertAffineTransform(M); A3 = np.vstack([Minv, [0, 0, 1]])
Hn = H @ A3
d = json.load(open(fitsp)); d[yr]['H_map_to_scan'] = Hn.tolist(); d[yr]['patch_refine'] = {'matches': len(src), 'agree': n, 'err_m': round(float(np.median(res)), 1), 'moved_m': round(float(moved))}
json.dump(d, open(fitsp, 'w'), indent=1)
O = 1600; Do = np.diag([2000 / O, 2000 / O, 1.0])
cv2.imwrite(outp, cv2.warpPerspective(S, Hn @ Do, (O, O), flags=cv2.INTER_AREA | cv2.WARP_INVERSE_MAP), [cv2.IMWRITE_JPEG_QUALITY, 84])

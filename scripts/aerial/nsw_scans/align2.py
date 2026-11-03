"""Pin raw NSW scanned aerial frames onto a site's 2000 m map window.
Coarse: normalised cross-correlation of the site's current aerial.jpg against the scan near the spot the NSW index
predicts, over a range of turns and scales. Fine: ECC image alignment (homography) at 2 m per pixel.
usage: python3 align2.py <site-folder-in-scans> <map-site> <scans-dir> <out-dir> [year ...]"""
import sys, json, math, pathlib, cv2, numpy as np
cv2.setNumThreads(4)
site, msite, sdir, odir = sys.argv[1:5]; only = sys.argv[5:]
FP = json.load(open(pathlib.Path(__file__).with_name('footprints.json')))[site]
ROOT = '/home/claude/pdc-design-map/map/sites/'
odir = pathlib.Path(odir); odir.mkdir(parents=True, exist_ok=True)
import os
REF = cv2.imread(os.environ.get('REFIMG', ROOT + msite + '/aerial.jpg'), cv2.IMREAD_GRAYSCALE)   # any square over the 2000 m window
RM = 2000 / REF.shape[1]
RAD = float(os.environ.get('RAD', 2500))
SCALES = [float(v) for v in os.environ.get('SCALES', '0.85,0.92,1.0,1.08,1.16').split(',')]
TURNS = [int(v) for v in os.environ.get('TURNS', '0,90,180,270').split(',')]
cl = cv2.createCLAHE(2.5, (8, 8))
def prep(g, m):  # m = metres per pixel; band-pass so old film and new colour photos look alike
    g = cl.apply(g).astype(np.float32)
    lo = cv2.GaussianBlur(g, (0, 0), 60 / m); g = g - lo
    g = cv2.GaussianBlur(g, (0, 0), 1.0)
    return (g - g.mean()) / (g.std() + 1e-6)
def at(img, src_m, dst_m): return cv2.resize(img, None, fx=src_m / dst_m, fy=src_m / dst_m, interpolation=cv2.INTER_AREA)
cx, cy = FP['centre']
res = {}
for yr, (img, denom, bb) in sorted((k, v) for k, v in FP.items() if k != 'centre'):
    if only and yr not in only: continue
    f = next(pathlib.Path(sdir).glob(f'{yr}_{img}.jpg'))
    S = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
    pm = denom * 0.23 / S.shape[1]
    # predicted window centre in scan px (index footprint, north up)
    fx = (cx - bb[0]) / (bb[2] - bb[0]); fy = (bb[3] - cy) / (bb[3] - bb[1])
    pc = np.array([fx * S.shape[1], fy * S.shape[0]])
    # ---- coarse at 5 m/px
    C = 5.0
    Sc = prep(at(S, pm, C), C); Rc = prep(at(REF, RM, C), C)   # ref 400 px
    best = (-1,)
    for flip in TURNS:
        for rot in range(-12, 13, 3):
            for sc in SCALES:
                h, w = Rc.shape
                M = cv2.getRotationMatrix2D((w / 2, h / 2), flip + rot, sc)
                # enlarge canvas so the turned template fits; use a centred inner square only (avoid empty corners)
                Rt = cv2.warpAffine(Rc, M, (w, h))
                k = int(w * 0.30); T = Rt[k:w - k, k:w - k]
                pcc = pc * pm / C; rr = RAD / C + T.shape[0] / 2
                x0, y0 = int(max(0, pcc[0] - rr)), int(max(0, pcc[1] - rr))
                sub = Sc[y0:int(pcc[1] + rr), x0:int(pcc[0] + rr)]
                if sub.shape[0] <= T.shape[0] or sub.shape[1] <= T.shape[1]: continue
                r = cv2.matchTemplate(sub, T, cv2.TM_CCOEFF_NORMED)
                _, mx, _, loc = cv2.minMaxLoc(r)
                if mx > best[0]: best = (mx, flip + rot, sc, (x0 + loc[0] + T.shape[1] / 2, y0 + loc[1] + T.shape[0] / 2))
    score, ang, sc, cpx = best
    found = np.array(cpx) * C / pm
    off = np.linalg.norm(found - pc) * pm
    print(f'{site} {yr}: coarse match {score:.2f}, turn {ang} deg, scale {sc}, {off:.0f} m from the index guess', flush=True)
    # transform map metres -> scan px (similarity): scan = c + R(ang)*s'*(map - 1000)
    # template was ref rotated by +ang (cv2 ccw) and scaled by sc, so scan_scale = sc*C ... map m -> scan coarse px: (map-1000)/C*sc rotated
    th = math.radians(ang)
    s_map2scan = sc / pm  # map metres -> scan px
    # cv2 positive angle = counter-clockwise in image coords (y down): x' = cos*x + sin*y ; y' = -sin*x + cos*y
    A = s_map2scan * np.array([[math.cos(th), math.sin(th)], [-math.sin(th), math.cos(th)]])
    t = found - A @ np.array([1000, 1000])
    Hm2s = np.vstack([np.hstack([A, t[:, None]]), [0, 0, 1]])
    # ---- fine: ECC at 2.5 m/px in map frame (warp scan into map window with margin, align to ref)
    F = 2.5; N = int(2000 / F)
    Rf = prep(at(REF, RM, F), F).astype(np.float32)
    D = np.diag([F, F, 1.0])                      # map px -> map m
    def warp(Hm2s_):
        return cv2.warpPerspective(S, Hm2s_ @ D, (N, N), flags=cv2.INTER_AREA | cv2.WARP_INVERSE_MAP)
    W0 = prep(warp(Hm2s), F).astype(np.float32)
    Wm = np.eye(3, dtype=np.float32); cc = None
    for mode, it in ((cv2.MOTION_AFFINE, 200), (cv2.MOTION_HOMOGRAPHY, 200)):
        try:
            Wi = Wm if mode == cv2.MOTION_HOMOGRAPHY else Wm[:2]
            cc, Wi = cv2.findTransformECC(Rf, W0, Wi.astype(np.float32), mode, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, it, 1e-6), None, 5)
            Wm = Wi if Wi.shape == (3, 3) else np.vstack([Wi, [0, 0, 1]]).astype(np.float32)
        except cv2.error as e:
            print('   fine step stopped:', str(e).splitlines()[-1][:80]); break
    # W maps ref(map px) -> W0 px ; full map m -> scan px:
    Hfin = Hm2s @ D @ Wm.astype(np.float64) @ np.linalg.inv(D)
    shift = np.linalg.norm((Wm @ [N / 2, N / 2, 1])[:2] / (Wm @ [N / 2, N / 2, 1])[2] - [N / 2, N / 2]) * F
    print(f'   fine: agreement {cc if cc is None else round(cc, 3)}, moved {shift:.0f} m from the coarse fit', flush=True)
    # render 1600 px over the full 2000 m window
    O = 1600; Do = np.diag([2000 / O, 2000 / O, 1.0])
    out = cv2.warpPerspective(S, Hfin @ Do, (O, O), flags=cv2.INTER_AREA | cv2.WARP_INVERSE_MAP, borderValue=0)
    cv2.imwrite(str(odir / f'n{yr}_scan.jpg'), out, [cv2.IMWRITE_JPEG_QUALITY, 84])
    res[yr] = {'img': img, 'scale': denom, 'coarse': round(float(score), 3), 'fine': None if cc is None else round(float(cc), 3), 'turn': ang, 'H_map_to_scan': Hfin.tolist(), 'index_offset_m': round(float(off))}
    json.dump(res, open(odir / 'fits.json', 'w'), indent=1)

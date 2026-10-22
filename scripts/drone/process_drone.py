#!/usr/bin/env python3
"""
process_drone.py: turn a WebODM drone result into map updates for Bright Tree.

Inputs (WebODM outputs, GeoTIFF):  --dsm odm_dem/dsm.tif  [--ortho odm_orthophoto/odm_orthophoto.tif]
Reference: the 2022 LiDAR ground (dem2022.npy) and crown tops (canopy_bright-tree_2022.npz), 1 m map grid
           (x = E - 492000, y = 7043000 - N, 2000 x 2000).

Steps
  1. Read the GeoTIFFs (MGA56 / GDA2020, or UTM 56S / WGS84 - treated as the same grid) and resample to 1 m.
  2. Line up with the LiDAR: horizontal shift by cross-correlating the drone surface against the LiDAR crown
     surface (search +-12 m), then vertical offset from open, flat, unchanged ground.
  3. Today's crown height = drone surface - LiDAR ground.
  4. Changes since 2022, written as suggestions (status 'idea', for review on the map, never auto-applied):
       - crowns gone (were over 5 m, now under 40% of that)  -> lopping jobs marked Built / stage Existing
       - new roofs (bare in 2022, now a smooth surface 2-9 m up, not green)  -> building outlines
       - new long clearings through former canopy  -> track lines
     plus a summary of regrowth.
  5. canopy_grid_drone.png for the light planner and niche map (same format as canopy_grid.png:
     R = height x 3, G = gap fraction x 255, 2 m cells), and an orthophoto crop for the map with its bounds.

Usage: python3 process_drone.py --dsm dsm.tif [--ortho ortho.tif] --out outdir [--date 2026-10-25]
"""
import argparse, json, math, os, sys
import numpy as np
from scipy import ndimage
from PIL import Image

W = '/tmp/claude-0/work/'
LIDAR = '/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/canopy_bright-tree_2022.npz'
MAPDIR = '/home/claude/pdc-design-map/map/'
E0, N0, SIZE = 492000.0, 7043000.0, 2000

def read_geotiff(path):
    """returns (array, (x0, y0) of the top-left corner in MGA metres, (sx, sy) pixel size, epsg)"""
    arr = None; tags = {}
    try:
        import tifffile
        with tifffile.TiffFile(path) as t:
            pg = t.pages[0]
            for k in (33550, 33922, 34735, 42113):
                if k in pg.tags: tags[k] = pg.tags[k].value
            arr = pg.asarray()
    except Exception as e:
        print('  tifffile could not read it (' + str(e)[:60] + '), trying Pillow')
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(path)
        tags = {k: im.tag_v2.get(k) for k in (33550, 33922, 34735, 42113)}
        arr = np.array(im)
    sx, sy = tags[33550][0], tags[33550][1]
    tp = tags[33922]; i0, j0, X, Y = tp[0], tp[1], tp[3], tp[4]
    x0, y0 = X - i0 * sx, Y + j0 * sy
    epsg = None
    gk = tags.get(34735)
    if gk is not None:
        gk = list(gk)
        for q in range(4, len(gk), 4):
            if gk[q] in (3072, 2048) and gk[q + 1] == 0: epsg = gk[q + 3]
    nod = tags.get(42113)
    nod = float(nod) if nod not in (None, '') else None
    return arr, (x0, y0), (sx, sy), epsg, nod

def to_map_grid(arr, origin, px, how='max', nodata=None):
    """resample a north-up raster onto the 1 m map grid (2000 x 2000). Returns float32 with NaN where empty."""
    a = arr.astype(np.float32)
    if nodata is not None: a = np.where(a == nodata, np.nan, a)
    a = np.where(a < -1000, np.nan, a)
    x0, y0 = origin; sx, sy = px
    f = max(1, int(round(1.0 / sx)))           # source cells per metre
    H, Wd = a.shape[:2]; H2, W2 = H // f * f, Wd // f * f
    b = a[:H2, :W2].reshape(H2 // f, f, W2 // f, f, *a.shape[2:])
    with np.errstate(all='ignore'):
        if how == 'max': b = np.nanmax(b, axis=(1, 3))
        else: b = np.nanmean(b, axis=(1, 3))
    cx = x0 - E0; cy = N0 - y0                   # map coords of the top-left corner
    step = sx * f
    out = np.full((SIZE, SIZE) + b.shape[2:], np.nan, np.float32)
    jj, ii = np.mgrid[0:SIZE, 0:SIZE]
    si = np.floor((ii + 0.5 - cx) / step).astype(int); sj = np.floor((jj + 0.5 - cy) / step).astype(int)
    ok = (si >= 0) & (sj >= 0) & (si < b.shape[1]) & (sj < b.shape[0])
    out[ok] = b[sj[ok], si[ok]]
    return out

def register(dsm, ref, search=12):
    """integer-metre shift (dx, dy) that best lines dsm up with ref, by FFT cross-correlation of high-pass surfaces"""
    m = np.isfinite(dsm) & np.isfinite(ref)
    if m.sum() < 5000: return 0, 0, 0.0
    ys, xs = np.nonzero(m); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    A = np.where(m, dsm, np.nan)[y0:y1, x0:x1]; B = np.where(np.isfinite(ref), ref, np.nan)[y0:y1, x0:x1]
    def hp(z):
        z = np.where(np.isfinite(z), z, np.nanmean(z)); return z - ndimage.gaussian_filter(z, 8)
    A, B = hp(A), hp(B)
    best = (-2, 0, 0)
    for dy in range(-search, search + 1):
        for dx in range(-search, search + 1):
            a = A[max(0, dy):A.shape[0] + min(0, dy), max(0, dx):A.shape[1] + min(0, dx)]
            b = B[max(0, -dy):B.shape[0] + min(0, -dy), max(0, -dx):B.shape[1] + min(0, -dx)]
            if a.size < 1000: continue
            c = np.corrcoef(a.ravel()[::7], b.ravel()[::7])[0, 1]
            if c > best[0]: best = (c, dx, dy)
    return best[1], best[2], best[0]

def shift(a, dx, dy):
    out = np.full_like(a, np.nan)
    H, Wd = a.shape[:2]
    out[max(0, -dy):H + min(0, -dy), max(0, -dx):Wd + min(0, -dx)] = a[max(0, dy):H + min(0, dy), max(0, dx):Wd + min(0, dx)]
    return out

def comps(mask, min_area):
    lab, n = ndimage.label(mask)
    if not n: return []
    idx = np.arange(1, n + 1); area = ndimage.sum(mask, lab, idx)
    out = []
    for k, a in zip(idx, area):
        if a < min_area: continue
        ys, xs = np.nonzero(lab == k); out.append((xs, ys, int(a)))
    return out

def oriented_rect(xs, ys, pad=0.5):
    pts = np.c_[xs + 0.5, ys + 0.5]; c = pts.mean(0); u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    p = (pts - c) @ vt.T; lo, hi = p.min(0) - pad, p.max(0) + pad
    corners = np.array([[lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]]]) @ vt + c
    return corners, hi - lo, vt

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dsm', required=True); ap.add_argument('--ortho'); ap.add_argument('--out', required=True)
    ap.add_argument('--date', default=''); ap.add_argument('--privacy', help='folder of map feature JSON files (a data snapshot); privacy zones in it are blanked'); ap.add_argument('--dem', default=W + 'dem2022.npy'); ap.add_argument('--lidar', default=LIDAR)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    dem = np.load(a.dem).astype(np.float32); z = np.load(a.lidar); top = z['top'].astype(np.float32)
    surf = np.where(np.isfinite(top), np.maximum(top, dem), dem)
    chm22 = np.clip(np.where(np.isfinite(top), top - dem, 0), 0, 85)
    print('Reading the drone surface model…')
    arr, org, px, epsg, nod = read_geotiff(a.dsm)
    if epsg not in (None, 7856, 28356, 32756): print(f'  WARNING: unexpected projection EPSG:{epsg}; expected MGA zone 56 or UTM 56S')
    dsm = to_map_grid(arr if arr.ndim == 2 else arr[..., 0], org, px, 'max', nod)
    PZ = []
    if a.privacy:
        import glob
        from matplotlib.path import Path as MP
        for fn in glob.glob(os.path.join(a.privacy, '*.json')):
            d = json.load(open(fn)); d = d.get('data', d)
            if d.get('kind') == 'privacy' and d.get('geom', {}).get('g') == 'polygon': PZ.append(MP(np.array(d['geom']['pts'])))
        if PZ:
            jj, ii = np.mgrid[0:SIZE, 0:SIZE]; pts = np.c_[ii.ravel() + .5, jj.ravel() + .5]
            pm = np.zeros(SIZE * SIZE, bool)
            for P_ in PZ: pm |= P_.contains_points(pts)
            PRIV = pm.reshape(SIZE, SIZE); print(f'  {len(PZ)} privacy zone(s): {PRIV.sum()} m² blanked')
    else: PRIV = None
    cover = np.isfinite(dsm); print(f'  {cover.sum()/1e4:.2f} ha covered, {px[0]*100:.0f} cm cells, EPSG:{epsg}')
    dx, dy, cc = register(dsm, surf); dsm = shift(dsm, dx, dy); cover = np.isfinite(dsm)
    print(f'  horizontal shift to line up with the LiDAR: {dx:+d} m east, {-dy:+d} m north (match {cc:.2f})')
    gy, gx = np.gradient(dem); slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    open_ground = cover & (chm22 < 0.5) & (slope < 15)
    d = (dsm - dem)[open_ground]; d = d[np.abs(d - np.median(d)) < 3] if d.size else d
    dz = float(np.median(d)) if d.size > 200 else float(np.nanmedian(dsm - surf))
    dsm = dsm - dz; print(f'  vertical offset removed: {dz:+.2f} m ({open_ground.sum()} m² of open ground used)')
    if PRIV is not None: dsm[PRIV] = np.nan; cover = np.isfinite(dsm)
    chm = np.clip(dsm - dem, 0, 85)
    sug = []; T = a.date or 'drone survey'
    # crowns gone since 2022
    lost = cover & (chm22 > 5) & (chm < chm22 * 0.4)
    lost = ndimage.binary_opening(lost, iterations=1)
    for xs, ys, ar in comps(lost, 15):
        _, dims, _ = oriented_rect(xs, ys)
        if dims.max() / max(1, dims.min()) >= 4 and ar >= 40: continue   # long strips are clearings/tracks, handled below
        cx, cy = xs.mean() + .5, ys.mean() + .5; r = max(2.0, math.sqrt(ar / math.pi)); h0 = float(np.percentile(chm22[ys, xs], 90))
        sug.append({'kind': 'lop', 'name': 'Tree gone since 2022 (drone)', 'geom': {'g': 'point', 'pts': [[round(cx, 1), round(cy, 1)]], 'r': round(r, 1)},
                    'status': 'idea', 'stage': 'existing', 'lopMode': 'remove', 'reviewAs': {'status': 'built'},
                    'notes': f'Drone survey {T}: crown about {h0:.0f} m tall in the 2022 LiDAR is gone, about {ar} m². Accept to count it as removed in the light planner.'})
    # new roofs
    if a.ortho:
        print('Reading the orthophoto…')
        oa, oorg, opx, oepsg, onod = read_geotiff(a.ortho)
        rgb = to_map_grid(oa[..., :3], oorg, opx, 'mean'); rgb = shift(rgb, dx, dy)
        if PRIV is not None: rgb[PRIV] = np.nan   # privacy zones: no photo kept
        if PRIV is not None: rgb[PRIV] = np.nan
        exg = 2 * rgb[..., 1] - rgb[..., 0] - rgb[..., 2]
    else: rgb = None; exg = np.zeros_like(chm)
    cz = np.nan_to_num(chm); m1 = ndimage.uniform_filter(cz, 3); rough = np.sqrt(np.maximum(ndimage.uniform_filter(cz * cz, 3) - m1 * m1, 0))   # bumpiness of the surface above the ground
    roof = cover & (chm22 < 2.5) & (chm > 2.0) & (chm < 9.0) & (chm - chm22 > 1.5) & (rough < 0.35) & (exg < 20)
    roof = ndimage.binary_dilation(ndimage.binary_opening(roof, iterations=1)) & roof
    for xs, ys, ar in comps(roof, 8):
        corners, dims, _ = oriented_rect(xs, ys, 1.5); h = float(np.median(chm[ys, xs]))   # edges are lost to the roughness test, so pad 1 m
        if dims.min() < 2: continue
        sug.append({'kind': 'building', 'name': 'New roof (drone)', 'geom': {'g': 'polygon', 'pts': [[round(float(x), 1), round(float(y), 1)] for x, y in corners]},
                    'status': 'idea', 'stage': 'existing', 'notes': f'Drone survey {T}: a smooth surface about {h:.1f} m high, {dims[0]:.0f} × {dims[1]:.0f} m, where the 2022 LiDAR had bare ground or low growth. Accept and rename it (shed, carport, house…).'})
    # new long clearings (tracks)
    clear = cover & (chm22 > 3) & (chm < 1.0)
    for xs, ys, ar in comps(clear, 40):
        corners, dims, vt = oriented_rect(xs, ys)
        if dims.max() / max(1, dims.min()) < 4: continue
        c = np.array([xs.mean() + .5, ys.mean() + .5]); half = dims.max() / 2
        p0 = c - vt[0] * half; p1 = c + vt[0] * half
        sug.append({'kind': 'track', 'name': 'New clearing or track (drone)', 'geom': {'g': 'line', 'pts': [[round(float(p0[0]), 1), round(float(p0[1]), 1)], [round(float(p1[0]), 1), round(float(p1[1]), 1)]]},
                    'status': 'idea', 'stage': 'existing', 'notes': f'Drone survey {T}: a strip about {dims.max():.0f} m long and {dims.min():.0f} m wide that was canopy in 2022 is now open.'})
    regrow = cover & (chm - chm22 > 4) & (chm22 < 2)
    summary = {'date': T, 'covered_ha': round(cover.sum() / 1e4, 2), 'shift_m': [dx, -dy], 'match': round(cc, 2), 'vertical_offset_m': round(dz, 2),
               'crowns_gone': sum(1 for s in sug if s['kind'] == 'lop'), 'crown_area_gone_m2': int(lost.sum()), 'new_roofs': sum(1 for s in sug if s['kind'] == 'building'),
               'new_clearings': sum(1 for s in sug if s['kind'] == 'track'), 'regrowth_m2': int(regrow.sum()),
               'mean_crown_height_change_m': round(float(np.nanmean((chm - chm22)[cover & (chm22 > 5)])), 2) if (cover & (chm22 > 5)).any() else None}
    json.dump({'summary': summary, 'suggestions': sug}, open(os.path.join(a.out, 'drone_changes.json'), 'w'), indent=1)
    # canopy grid for the light planner: start from the LiDAR grid, replace heights where the drone saw the canopy
    cg = np.array(Image.open(MAPDIR + 'canopy_grid.png').convert('RGB')).astype(np.float32)
    h2 = cg[..., 0] / 3; gp2 = cg[..., 1] / 255
    chm2 = chm.reshape(1000, 2, 1000, 2); cov2 = np.isfinite(chm2).all(axis=(1, 3))
    with np.errstate(all='ignore'): hn = np.nanmax(chm2, axis=(1, 3))
    lost2 = lost.reshape(1000, 2, 1000, 2).any(axis=(1, 3))
    h2 = np.where(cov2, hn, h2); gp2 = np.where(lost2, 1.0, gp2); gp2 = np.where(cov2 & (hn < 2), 1.0, gp2)
    out = np.dstack([np.clip(h2 * 3, 0, 255), np.clip(gp2 * 255, 0, 255), cg[..., 2]]).astype(np.uint8)
    Image.fromarray(out, 'RGB').save(os.path.join(a.out, 'canopy_grid_drone.png'))
    if rgb is not None:
        m = np.isfinite(rgb[..., 0]); ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        crop = np.nan_to_num(rgb[y0:y1, x0:x1]).clip(0, 255).astype(np.uint8)
        Image.fromarray(crop).save(os.path.join(a.out, 'drone_ortho_1m.jpg'), quality=85)
        json.dump({'x0': int(x0), 'y0': int(y0), 'x1': int(x1), 'y1': int(y1), 'note': 'map metres; full-detail ortho should be cropped from the source at its own resolution'}, open(os.path.join(a.out, 'drone_ortho_bounds.json'), 'w'))
    print(json.dumps(summary, indent=1))

if __name__ == '__main__':
    main()

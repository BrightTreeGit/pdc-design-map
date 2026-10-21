#!/usr/bin/env python3
"""Build a design-map site folder for any Australian block.

usage: python3 build_site.py site.json

site.json:
{
  "name": "Bright Tree",                    # shown in the map header (no street address)
  "subtitle": "Sunshine Coast hinterland",  # region only
  "state": "QLD",                           # QLD | NSW | VIC ...
  "council": "Sunshine Coast",
  "dem": {"2022": ["a.tif", "b.tif"], "2014": [...], "2008": [...]},   # GeoTIFF / .asc / .zip; newest year = main
  "boundary": {"lonlat": [[lon, lat], ...]}  or {"mga": [[E, N], ...], "zone": 56},
  "area_m2": 100000,                        # optional: scale traced boundary to title area
  "zone": 56,                               # optional: forced MGA zone (else from boundary longitude)
  "rain": {...},                            # optional BoM monthly stats (station, period, mean, median, days, tmin)
  "lfw": false,                             # Land for Wildlife notes in weed list
  "template": "index.html",                 # map page to copy
  "out": "/path/to/site-folder"
}
"""
import sys, os, json, math, zlib, base64, glob, heapq, shutil, zipfile, tempfile, re, time
import numpy as np, tifffile
from scipy import ndimage
from skimage import measure
from matplotlib.path import Path as MPath
from PIL import Image

T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.1f}s]', *a, flush=True)

# ---------------------------------------------------------------- projection (GRS80 Krüger)
_a = 6378137.0; _f = 1/298.257222101; _k0 = 0.9996; _FE = 500000.0; _FN = 10000000.0
_n = _f/(2-_f); _A = _a/(1+_n)*(1+_n**2/4+_n**4/64)
_al = [_n/2-2*_n**2/3+5*_n**3/16, 13*_n**2/48-3*_n**3/5, 61*_n**3/240]
_be = [_n/2-2*_n**2/3+37*_n**3/96, _n**2/48+_n**3/15, 17*_n**3/480]
_e = math.sqrt(_f*(2-_f))
def lon0_of(zone): return math.radians(zone*6-183)
def ll2mga(lon, lat, zone):
    lon = np.radians(np.asarray(lon, float)); lat = np.radians(np.asarray(lat, float))
    t = np.sinh(np.arctanh(np.sin(lat))-_e*np.arctanh(_e*np.sin(lat))); dl = lon-lon0_of(zone)
    xi = np.arctan2(t, np.cos(dl)); eta = np.arctanh(np.sin(dl)/np.sqrt(1+t*t))
    X = xi+sum(_al[j]*np.sin(2*(j+1)*xi)*np.cosh(2*(j+1)*eta) for j in range(3))
    Y = eta+sum(_al[j]*np.cos(2*(j+1)*xi)*np.sinh(2*(j+1)*eta) for j in range(3))
    return _FE+_k0*_A*Y, _FN+_k0*_A*X
def mga2ll(E, N, zone):
    xi = (np.asarray(N, float)-_FN)/(_k0*_A); eta = (np.asarray(E, float)-_FE)/(_k0*_A)
    xp = xi-sum(_be[j]*np.sin(2*(j+1)*xi)*np.cosh(2*(j+1)*eta) for j in range(3))
    ep = eta-sum(_be[j]*np.cos(2*(j+1)*xi)*np.sinh(2*(j+1)*eta) for j in range(3))
    chi = np.arcsin(np.sin(xp)/np.cosh(ep)); lat = chi
    for _ in range(6): lat = np.arcsin(np.tanh(np.arctanh(np.sin(chi))+_e*np.arctanh(_e*np.sin(lat))))
    return np.degrees(lon0_of(zone)+np.arctan2(np.sinh(ep), np.cos(xp))), np.degrees(lat)

# ---------------------------------------------------------------- raster readers
def lzw_decode(data):
    out = bytearray(); table = [bytes([i]) for i in range(256)]+[b'', b'']
    bitpos = 0; nbits = 9; prev = None; total = len(data)*8
    while bitpos+nbits <= total:
        byte = bitpos >> 3; chunk = int.from_bytes(data[byte:byte+4].ljust(4, b'\0'), 'big')
        code = (chunk >> (32-(bitpos & 7)-nbits)) & ((1 << nbits)-1); bitpos += nbits
        if code == 256:
            table = table[:258]; nbits = 9; prev = None; continue
        if code == 257: break
        if prev is None:
            entry = table[code]; out += entry; prev = entry; continue
        if code < len(table): entry = table[code]; table.append(prev+entry[:1])
        else: entry = prev+prev[:1]; table.append(entry)
        out += entry; prev = entry
        n = len(table)
        if n >= 511 and nbits == 9: nbits = 10
        elif n >= 1023 and nbits == 10: nbits = 11
        elif n >= 2047 and nbits == 11: nbits = 12
    return bytes(out)

def packbits_decode(data):
    out = bytearray(); i = 0
    while i < len(data):
        n = data[i]; i += 1
        if n < 128: out += data[i:i+n+1]; i += n+1
        elif n > 128: out += bytes([data[i]])*(257-n); i += 1
    return bytes(out)

GEO_EPSG_ZONE = {**{28300+z: z for z in range(49, 57)}, **{7800+z: z for z in range(49, 57)}, **{32700+z: z for z in range(49, 57)}}

def read_tiff(path):
    t = tifffile.TiffFile(path); p = t.pages[0]; tags = p.tags
    H, W = p.shape[:2]; bo = t.byteorder
    bps = p.bitspersample; sf = int(p.sampleformat); spp = p.samplesperpixel
    kind = {1: 'u', 2: 'i', 3: 'f'}[sf]; dt = np.dtype(f'{bo}{kind}{bps//8}')
    comp = int(p.compression); pred = int(p.predictor)
    if p.is_tiled: tw, th = p.tilewidth, p.tilelength; nx = (W+tw-1)//tw
    else: tw = W; th = int(tags['RowsPerStrip'].value) if 'RowsPerStrip' in tags else H; nx = 1
    ny = (H+th-1)//th
    out = np.full((ny*th, nx*tw), np.nan, np.float32)
    fh = t.filehandle
    for i, (off, cnt) in enumerate(zip(p.dataoffsets, p.databytecounts)):
        if cnt == 0: continue
        fh.seek(off); raw = fh.read(cnt)
        if comp == 1: b = raw
        elif comp in (8, 32946): b = zlib.decompress(raw)
        elif comp == 5: b = lzw_decode(raw)
        elif comp == 32773: b = packbits_decode(raw)
        else: raise ValueError(f'{os.path.basename(path)}: compression {comp} not supported; re-save as uncompressed or deflate GeoTIFF')
        r, c = divmod(i, nx)
        rows = th if p.is_tiled else min(th, H-r*th)
        need = rows*tw*spp*dt.itemsize; b = np.frombuffer(b[:need], np.uint8)
        if pred == 3:
            b = b.reshape(rows, tw*spp*dt.itemsize); b = np.cumsum(b, axis=1, dtype=np.uint8)
            b = b.reshape(rows, dt.itemsize, tw*spp).transpose(0, 2, 1).copy()
            v = b.view(np.dtype(f'>{kind}{bps//8}')).reshape(rows, tw*spp)
        else:
            v = b.view(dt).reshape(rows, tw*spp)
            if pred == 2: v = np.cumsum(v, axis=1, dtype=v.dtype)
        v = v[:, ::spp].astype(np.float32)
        out[r*th:r*th+rows, c*tw:(c+1)*tw] = v
    a = out[:H, :W]
    nod = None
    if 42113 in tags:
        try: nod = float(str(tags[42113].value).strip('\0 '))
        except Exception: nod = None
    if nod is not None: a[a == nod] = np.nan
    a[(a < -1000) | (a > 9000)] = np.nan
    sx, sy = tags['ModelPixelScaleTag'].value[:2]; tp = tags['ModelTiepointTag'].value
    x0 = tp[3]-tp[0]*sx; y0 = tp[4]+tp[1]*sy
    crs = {'type': 'projected', 'zone': None}
    gk = t.geotiff_metadata if hasattr(t, 'geotiff_metadata') else None
    if gk:
        pc = gk.get('ProjectedCSTypeGeoKey'); gc = gk.get('GeographicTypeGeoKey')
        pcv = int(getattr(pc, 'value', pc)) if pc is not None else None
        if pcv and pcv in GEO_EPSG_ZONE: crs['zone'] = GEO_EPSG_ZONE[pcv]
        elif pcv is None and gc is not None: crs['type'] = 'geographic'
        if crs['zone'] is None and crs['type'] == 'projected':
            m = re.search(r'zone\s*(\d+)', str(gk.get('PCSCitationGeoKey', '')) + str(gk.get('GTCitationGeoKey', '')), re.I)
            if m: crs['zone'] = int(m.group(1))
        if gk.get('GTRasterTypeGeoKey') in (2, 'RasterPixelIsPoint') or str(gk.get('GTRasterTypeGeoKey')).endswith('Point'):
            x0 -= sx/2; y0 += sy/2
    return dict(a=a, x0=x0, y0=y0, sx=sx, sy=sy, crs=crs, name=os.path.basename(path))

def read_asc(path):
    txt = open(path, 'r', errors='ignore').read(); hdr = {}; lines = txt.split('\n'); k = 0
    while k < len(lines) and re.match(r'^\s*[A-Za-z_]', lines[k]):
        key, val = lines[k].split()[:2]; hdr[key.lower()] = float(val); k += 1
    nc, nr, cs = int(hdr['ncols']), int(hdr['nrows']), hdr['cellsize']
    a = np.fromstring(' '.join(lines[k:]), sep=' ', dtype=np.float32)[:nr*nc].reshape(nr, nc)
    if 'nodata_value' in hdr: a[a == hdr['nodata_value']] = np.nan
    a[(a < -1000) | (a > 9000)] = np.nan
    x0 = hdr.get('xllcorner', hdr.get('xllcenter', 0)-cs/2); yll = hdr.get('yllcorner', hdr.get('yllcenter', 0)-cs/2)
    zone = None; prj = os.path.splitext(path)[0]+'.prj'
    if os.path.exists(prj):
        m = re.search(r'zone[_ ]*(\d+)', open(prj, errors='ignore').read(), re.I)
        if m: zone = int(m.group(1))
    geo = abs(cs) < 0.01
    return dict(a=a, x0=x0, y0=yll+nr*cs, sx=cs, sy=cs, crs={'type': 'geographic' if geo else 'projected', 'zone': zone}, name=os.path.basename(path))

def read_any(path, tmp):
    ext = path.lower().rsplit('.', 1)[-1]
    if ext == 'zip':
        out = []; d = tempfile.mkdtemp(dir=tmp)
        with zipfile.ZipFile(path) as z: z.extractall(d)
        for f in sorted(glob.glob(d+'/**/*', recursive=True)):
            if f.lower().endswith(('.tif', '.tiff', '.asc')): out += read_any(f, tmp)
        return out
    if ext in ('tif', 'tiff'): return [read_tiff(path)]
    if ext == 'asc': return [read_asc(path)]
    raise ValueError('Unsupported elevation file: '+path)

def resample_to_grid(srcs, E0, N0, zone, size=2000, res=1.0):
    """Bilinear-sample source rasters onto the target 1 m grid (pixel centres)."""
    M = np.full((size, size), np.nan, np.float32)
    cols = E0+(np.arange(size)+0.5)*res; rows = N0-(np.arange(size)+0.5)*res
    for s in srcs:
        z = s['crs']['zone'] or zone; a = s['a']; h, w = a.shape
        if s['crs']['type'] == 'projected' and z == zone:
            fc = (cols-s['x0'])/s['sx']-0.5; fr = (s['y0']-rows)/s['sy']-0.5
            ci = np.nonzero((fc > -1) & (fc < w))[0]; ri = np.nonzero((fr > -1) & (fr < h))[0]
            if not len(ci) or not len(ri): continue
            RR, CC = np.meshgrid(fr[ri], fc[ci], indexing='ij')
            tgt = (slice(ri[0], ri[-1]+1), slice(ci[0], ci[-1]+1))
        else:
            EE, NN = np.meshgrid(cols, rows); lon, lat = mga2ll(EE, NN, zone)
            if s['crs']['type'] == 'geographic': X, Y = lon, lat
            else: X, Y = ll2mga(lon, lat, z)
            CC = (X-s['x0'])/s['sx']-0.5; RR = (s['y0']-Y)/s['sy']-0.5
            tgt = (slice(None), slice(None))
        filled = np.where(np.isnan(a), np.nanmedian(a) if np.isfinite(a).any() else 0, a)
        v = ndimage.map_coordinates(filled, [RR.ravel(), CC.ravel()], order=1, mode='nearest').reshape(RR.shape)
        nanm = ndimage.map_coordinates(np.isnan(a).astype(np.float32), [RR.ravel(), CC.ravel()], order=1, mode='constant', cval=1).reshape(RR.shape)
        inside = (RR > -0.5) & (CC > -0.5) & (RR < h-0.5) & (CC < w-0.5) & (nanm < 0.5)
        sub = M[tgt]; put = inside & np.isnan(sub); sub[put] = v[put]; M[tgt] = sub
    return M

def coverage_box(srcs, zone):
    xs, ys = [], []
    for s in srcs:
        h, w = s['a'].shape; X = [s['x0'], s['x0']+w*s['sx']]; Y = [s['y0']-h*s['sy'], s['y0']]
        if s['crs']['type'] == 'geographic':
            E, N = ll2mga([X[0], X[1], X[0], X[1]], [Y[0], Y[0], Y[1], Y[1]], zone); xs += list(E); ys += list(N)
        else:
            z = s['crs']['zone'] or zone
            if z != zone:
                lon, lat = mga2ll([X[0], X[1], X[0], X[1]], [Y[0], Y[0], Y[1], Y[1]], z); E, N = ll2mga(lon, lat, zone); xs += list(E); ys += list(N)
            else: xs += X; ys += Y
    return min(xs), min(ys), max(xs), max(ys)

# ---------------------------------------------------------------- main build
def build(cfg):
    out = cfg['out']; os.makedirs(out, exist_ok=True); tmp = tempfile.mkdtemp()
    S = 2000; R2 = 2.0
    # boundary in lon/lat -> zone
    b = cfg['boundary']
    if 'lonlat' in b:
        ll = np.array(b['lonlat'], float); zone = cfg.get('zone') or int((ll[:, 0].mean()+180)//6)+1
        bE, bN = ll2mga(ll[:, 0], ll[:, 1], zone)
    else:
        zone = cfg.get('zone') or b['zone']; m = np.array(b['mga'], float)
        if b.get('zone', zone) != zone:
            lon, lat = mga2ll(m[:, 0], m[:, 1], b['zone']); bE, bN = ll2mga(lon, lat, zone)
        else: bE, bN = m[:, 0], m[:, 1]
    if np.hypot(bE[0]-bE[-1], bN[0]-bN[-1]) < 0.01: bE, bN = bE[:-1], bN[:-1]
    def parea(x, y): return 0.5*abs(np.dot(x, np.roll(y, 1))-np.dot(y, np.roll(x, 1)))
    if cfg.get('area_m2'):
        cx, cy = bE.mean(), bN.mean(); k = math.sqrt(cfg['area_m2']/parea(bE, bN)); bE = cx+(bE-cx)*k; bN = cy+(bN-cy)*k
    lot = np.c_[bE, bN]; log('zone', zone, 'lot area m2', round(parea(bE, bN)))
    # elevation sources
    years = sorted(cfg['dem'].keys(), reverse=True); main = years[0]
    srcs = {y: [r for f in cfg['dem'][y] for r in read_any(f, tmp)] for y in years}
    for y in years: log('year', y, len(srcs[y]), 'rasters', [f"{s['name'][:40]} {s['sx']:.2f}m z{s['crs']['zone']}" for s in srcs[y][:3]])
    cxmin, cymin, cxmax, cymax = coverage_box(srcs[main], zone)
    lcx, lcy = (bE.min()+bE.max())/2, (bN.min()+bN.max())/2
    def place(c, lo, hi):
        v = c-S/2
        if hi-lo >= S: v = min(max(v, lo), hi-S)
        else: v = (lo+hi)/2-S/2
        return float(round(v))
    E0 = place(lcx, cxmin, cxmax); N0 = place(lcy, cymin, cymax)+S
    if cfg.get('window'): E0, N0 = float(cfg['window'][0]), float(cfg['window'][1])   # keep an existing window (aerial photo stays aligned)
    if cfg.get('window'): E0, N0 = float(cfg['window'][0]), float(cfg['window'][1])   # keep an existing window (aerial photo stays aligned)
    if bE.min() < E0+60 or bE.max() > E0+S-60 or bN.min() < N0-S+60 or bN.max() > N0-60:
        log('WARNING: boundary is near or past the 2 km map window; the lot may be too big for this map size')
    log('window E0', E0, 'N0', N0)
    Z1 = resample_to_grid(srcs[main], E0, N0, zone)
    nod = np.isnan(Z1); log('main DEM', main, 'nodata share', round(float(nod.mean()), 3))
    if nod.all(): raise SystemExit('No elevation data inside the map window: check the files cover the block')
    if nod.any():
        idx = ndimage.distance_transform_edt(nod, return_distances=False, return_indices=True); Z1 = Z1[tuple(idx)]
    Z1 = Z1.astype(np.float64)
    meta = {}
    lotxy = np.c_[lot[:, 0]-E0, N0-lot[:, 1]]
    # ---------------- hydrology on 2 m
    Z2 = Z1.reshape(1000, 2, 1000, 2).mean((1, 3)); H, Wd = Z2.shape
    filled = Z2.copy(); closed = np.zeros_like(Z2, bool); pq = []
    for r in range(H):
        for c in (0, Wd-1): pq.append((filled[r, c], r, c)); closed[r, c] = True
    for c in range(1, Wd-1):
        for r in (0, H-1): pq.append((filled[r, c], r, c)); closed[r, c] = True
    heapq.heapify(pq)
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    fl = filled; cl = closed
    while pq:
        z, r, c = heapq.heappop(pq)
        for dr, dc in nb:
            rr, cc = r+dr, c+dc
            if 0 <= rr < H and 0 <= cc < Wd and not cl[rr, cc]:
                cl[rr, cc] = True
                if fl[rr, cc] <= z: fl[rr, cc] = z+1e-4
                heapq.heappush(pq, (fl[rr, cc], rr, cc))
    log('filled')
    pad = np.pad(filled, 1, constant_values=-1e9); best = np.zeros_like(filled); rec = np.full(filled.shape, -1, np.int64)
    for dr, dc in nb:
        d = math.hypot(dr, dc)*R2; nz = pad[1+dr:1+dr+H, 1+dc:1+dc+Wd]; drop = (filled-nz)/d
        rr = np.clip(np.arange(H)[:, None]+dr, 0, H-1); cc = np.clip(np.arange(Wd)[None, :]+dc, 0, Wd-1)
        better = drop > best; best = np.where(better, drop, best); rec = np.where(better, rr*Wd+cc, rec)
    rf = rec.ravel(); order = np.argsort(-filled.ravel(), kind='stable'); acc = np.full(H*Wd, R2*R2)
    for i in order:
        j = rf[i]
        if j >= 0: acc[j] += acc[i]
    ACC = acc.reshape(H, Wd)
    cc_, rr_ = np.meshgrid(np.arange(Wd), np.arange(H))
    LOT2 = MPath(lotxy).contains_points(np.c_[(cc_.ravel()+0.5)*2, (rr_.ravel()+0.5)*2]).reshape(H, Wd)
    def upstream_of(seed):
        inc = seed.ravel().copy()
        for i in order[::-1]:
            j = rf[i]
            if j >= 0 and inc[j]: inc[i] = True
        return inc.reshape(H, Wd)
    CATCH = upstream_of(LOT2); log('catchment ha', CATCH.sum()*4/1e4)
    catch_edge = bool(CATCH[0].any() or CATCH[-1].any() or CATCH[:, 0].any() or CATCH[:, -1].any())
    if catch_edge: log('NOTE: catchment runs past the 2 km window edge; figures are a minimum')
    # ---------------- images
    def png(arr, name): Image.fromarray(arr, 'RGBA').save(out+'/'+name, optimize=True)
    nod2 = nod.reshape(1000, 2, 1000, 2).mean((1, 3)) > 0.5
    Zs = ndimage.gaussian_filter(Z1, 0.7); gy, gx = np.gradient(Zs); dzdx, dzdy = gx, -gy
    slope = np.arctan(np.hypot(dzdx, dzdy)); aspect = np.arctan2(-dzdx, -dzdy)
    def hs(az, alt):
        az = math.radians(az); alt = math.radians(alt); lx, ly, lz = math.sin(az)*math.cos(alt), math.cos(az)*math.cos(alt), math.sin(alt)
        return (-dzdx*lx-dzdy*ly+lz)/np.sqrt(dzdx**2+dzdy**2+1)
    Hs = np.clip(0.5*hs(315, 40)+0.25*hs(270, 40)+0.25*hs(0, 40), 0, 1)
    zmin, zmax = float(Z1.min()), float(Z1.max()); meta['zmin'] = zmin; meta['zmax'] = zmax
    rng = max(zmax-zmin, 5.0); t = (Z1-zmin)/rng
    stops = np.array([[0, 70, 112, 100], [0.25, 128, 150, 104], [0.45, 182, 170, 120], [0.65, 196, 160, 118], [1, 232, 224, 210]], float)
    tint = np.stack([np.interp(t, stops[:, 0], stops[:, c]) for c in (1, 2, 3)], -1)
    rgb = np.clip(tint*(0.35+0.75*Hs)[..., None], 0, 255).astype(np.uint8); rgb[nod] = (225, 222, 214)
    Image.fromarray(rgb).save(out+'/relief.jpg', quality=80)
    gray = (np.clip(0.25+0.8*Hs, 0, 1)*255).astype(np.uint8); gray[nod] = 225
    Image.fromarray(gray).save(out+'/hillshade.jpg', quality=78)
    slope_pct = np.tan(slope)*100; sp2 = slope_pct.reshape(1000, 2, 1000, 2).mean((1, 3))
    cls = [(0, 10, (46, 160, 90, 150)), (10, 18, (170, 200, 70, 150)), (18, 25, (240, 200, 60, 160)), (25, 33, (240, 140, 50, 170)), (33, 50, (220, 80, 50, 180)), (50, 1e9, (140, 30, 60, 190))]
    img = np.zeros((1000, 1000, 4), np.uint8)
    for lo, hi, col in cls: img[(sp2 >= lo) & (sp2 < hi)] = col
    img[nod2] = 0; png(img, 'slope.png')
    meta['slopeClasses'] = [[lo, hi if hi < 1e8 else None, list(col)] for lo, hi, col in cls]
    LOT1 = np.repeat(np.repeat(LOT2, 2, 0), 2, 1)
    meta['lotSlopeShare'] = [[lo, hi if hi < 1e8 else None, round(float(((slope_pct >= lo) & (slope_pct < hi) & LOT1).sum()/max(1, LOT1.sum())), 5)] for lo, hi, _ in cls]
    asp2 = np.degrees(np.arctan2(ndimage.uniform_filter(np.sin(aspect), 2)[::2, ::2], ndimage.uniform_filter(np.cos(aspect), 2)[::2, ::2])) % 360
    hues = {'N': (235, 150, 40), 'NE': (240, 195, 70), 'E': (210, 215, 110), 'SE': (110, 170, 190), 'S': (70, 110, 200), 'SW': (120, 100, 190), 'W': (215, 95, 90), 'NW': (240, 120, 50)}
    names = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']; img = np.zeros((1000, 1000, 4), np.uint8); k = (((asp2+22.5) % 360)//45).astype(int)
    for i, nm in enumerate(names): img[k == i] = (*hues[nm], 150)
    img[(sp2 < 5) | nod2] = 0; png(img, 'aspect.png'); meta['aspectColors'] = {a: list(v) for a, v in hues.items()}
    yy, xx = np.mgrid[-30:31, -30:31]; ker = (xx*xx+yy*yy <= 900).astype(float); ker /= ker.sum()
    tpi = Z2-ndimage.convolve(Z2, ker, mode='nearest'); cold = np.clip((-tpi-1.5)/6, 0, 1)*np.clip((40-sp2)/30, 0, 1); cold[nod2] = 0
    img = np.zeros((1000, 1000, 4), np.uint8); img[..., 0] = 70; img[..., 1] = 120; img[..., 2] = 230; img[..., 3] = (cold*200).astype(np.uint8); png(img, 'cold.png')
    log('relief, slope, aspect, cold done')
    # ---------------- sun hours on 4 m
    lonC, latC = mga2ll(lot[:, 0].mean(), lot[:, 1].mean(), zone); latC = float(latC); lonC = float(lonC)
    Z4 = Z1.reshape(500, 4, 500, 4).mean((1, 3)); gy4, gx4 = np.gradient(Z4, 4.0); dx4, dy4 = gx4, -gy4
    def sunpos(decl, hour):
        d = math.radians(decl); phi = math.radians(latC); h = math.radians(15*(hour-12))
        alt = math.asin(math.sin(phi)*math.sin(d)+math.cos(phi)*math.cos(d)*math.cos(h))
        az = math.atan2(-math.sin(h)*math.cos(d), math.cos(phi)*math.sin(d)-math.sin(phi)*math.cos(d)*math.cos(h))
        return math.degrees(alt), math.degrees(az) % 360
    def shift(a, dr, dc):
        o = np.full_like(a, -1e9); h_, w_ = a.shape; r0, r1 = max(0, -dr), min(h_, h_-dr); c0, c1 = max(0, -dc), min(w_, w_-dc)
        o[r0:r1, c0:c1] = a[r0+dr:r1+dr, c0+dc:c1+dc]; return o
    def sunhours(decl):
        tot = np.zeros_like(Z4); step = 1/6
        for hr in np.arange(4.5, 19.5, step):
            alt, az = sunpos(decl, hr+step/2)
            if alt <= 1: continue
            a = math.radians(alt); z = math.radians(az); sx, sy = math.sin(z), math.cos(z)
            lit = (-dx4*sx*math.cos(a)-dy4*sy*math.cos(a)+math.sin(a)) > 0
            dist = 4.0; sh = np.zeros_like(lit)
            while dist < 1500:
                dc = int(round(sx*dist/4)); dr = int(round(-sy*dist/4))
                if abs(dc) >= 500 or abs(dr) >= 500: break
                sh |= shift(Z4, dr, dc) > Z4+dist*math.tan(a); dist *= 1.06
            tot += (lit & ~sh)*step
        return tot
    LOT4 = LOT2[::2, ::2]
    for nm, dec in (('winter', 23.44 if latC < 0 else -23.44), ('equinox', 0.0), ('summer', -23.44 if latC < 0 else 23.44)):
        sh = sunhours(dec); meta['sun_'+nm+'_lotmean'] = float(sh[LOT4].mean()) if LOT4.any() else 0.0
        mx = {'winter': 8, 'equinox': 11, 'summer': 13}[nm]; tt = np.clip(sh/mx, 0, 1)
        st = np.array([[0, 30, 40, 110], [0.35, 90, 70, 150], [0.6, 220, 110, 70], [0.85, 250, 200, 70], [1, 255, 245, 170]])
        rgbs = np.stack([np.interp(tt, st[:, 0], st[:, c]) for c in (1, 2, 3)], -1)
        png(np.dstack([rgbs, np.full(tt.shape, 175)]).astype(np.uint8), 'sun_'+nm+'.png')
        meta['sunh_'+nm] = base64.b64encode(zlib.compress(np.round(np.clip(sh, 0, 25.5)*10).astype(np.uint8).tobytes(), 9)).decode()
    log('sun done', {k: round(v, 2) for k, v in meta.items() if k.endswith('lotmean')})
    # ---------------- streams
    A = ACC.ravel()
    def trace_streams(th):
        ok = A >= th; up = np.zeros(A.size, int); idxs = np.nonzero(ok)[0]
        for i in idxs:
            j = rf[i]
            if j >= 0 and ok[j]: up[j] += 1
        seen = np.zeros(A.size, bool); lines = []; heads = [i for i in idxs if up[i] == 0]; heads.sort(key=lambda i: -filled.ravel()[i])
        for h in heads:
            i = h; pts = []
            while i >= 0 and ok[i]:
                r, c = divmod(i, Wd); pts.append((c*2+1.0, r*2+1.0, A[i]))
                if seen[i]: break
                seen[i] = True; i = rf[i]
            if len(pts) >= 3: lines.append(pts)
        return lines
    streams = []
    for pts in trace_streams(2000):
        xy = np.array([(x, y) for x, y, _ in pts]); a = np.array([a for _, _, a in pts]); klass = np.digitize(a, [5000, 20000, 100000]); start = 0
        for i in range(1, len(pts)+1):
            if i == len(pts) or klass[i] != klass[start]:
                seg = xy[start:min(i+1, len(pts))]
                if len(seg) >= 2: streams.append({'k': int(klass[start]), 'p': np.round(measure.approximate_polygon(seg, 0.8), 1).ravel().tolist()})
                start = i
    def outline(mask):
        m = ndimage.binary_closing(ndimage.binary_opening(mask, iterations=1), iterations=2)
        if not m.any(): m = mask
        c = max(measure.find_contours(np.pad(m, 1).astype(float), 0.5), key=len); s = measure.approximate_polygon(c, 1.0)-1
        return np.round(np.c_[s[:, 1]*2+1, s[:, 0]*2+1], 1).ravel().tolist()
    catch = [{'name': 'Everything that drains into '+cfg['name'], 'ha': round(float(CATCH.sum()*4/1e4), 1), 'p': outline(CATCH), 'main': True}]
    L = LOT2.ravel(); inflows = sorted([(A[i], i) for i in np.nonzero(~L)[0] if rf[i] >= 0 and L[rf[i]]], reverse=True); used = []
    for a, i in inflows:
        if a < 8000 or len(used) >= 8: break
        r, c = divmod(i, Wd)
        if any(abs(r-r2)+abs(c-c2) < 15 for r2, c2 in used): continue
        used.append((r, c)); seed = np.zeros(H*Wd, bool); seed[i] = True
        catch.append({'name': 'Inflow', 'ha': round(float(a/1e4), 1), 'p': outline(upstream_of(seed.reshape(H, Wd))), 'at': [c*2+1.0, r*2+1.0]})
    outs = sorted([(A[i], i) for i in np.nonzero(L)[0] if rf[i] >= 0 and not L[rf[i]]], reverse=True)
    if outs: r, c = divmod(outs[0][1], Wd); meta['outlet'] = {'at': [c*2+1.0, r*2+1.0], 'ha': round(float(outs[0][0]/1e4), 1)}
    log('streams', len(streams), 'inflows', [(c_['ha']) for c_ in catch[1:]], 'outlet', meta.get('outlet'))
    # ---------------- contours
    def contours(Z, res, levels, off, tol):
        o = []
        for lv in levels:
            for c in measure.find_contours(Z, lv):
                if len(c) < 4: continue
                s = measure.approximate_polygon(c, tol); xy = np.c_[s[:, 1]*res+off, s[:, 0]*res+off]
                o.append({'z': int(round(lv)) if float(lv).is_integer() else round(float(lv), 1), 'p': np.round(xy, 1).ravel().tolist()})
        return o
    Zc2 = ndimage.gaussian_filter(Z2, 1.0); c5 = contours(Zc2, 2.0, np.arange(math.ceil(zmin/5)*5, zmax, 5), 1.0, 0.6)
    x0 = int(max(0, lotxy[:, 0].min()-120)); x1 = int(min(S, lotxy[:, 0].max()+120)); y0 = int(max(0, lotxy[:, 1].min()-120)); y1 = int(min(S, lotxy[:, 1].max()+120))
    Zc1 = ndimage.gaussian_filter(Z1[y0:y1, x0:x1], 1.6)
    c1 = contours(Zc1, 1.0, list(np.arange(math.ceil(Zc1.min()), Zc1.max(), 1)), 0.5, 0.45)
    for c in c1:
        p = np.array(c['p']).reshape(-1, 2); p[:, 0] += x0; p[:, 1] += y0; c['p'] = np.round(p, 1).ravel().tolist()
    meta['c1box'] = [x0, y0, x1, y1]; log('contours', len(c5), len(c1))
    # ---------------- keypoints
    cand = []
    for stl in trace_streams(6000):
        xy = np.array([(x, y) for x, y, _ in stl]); a = np.array([a for _, _, a in stl]); z = np.array([Z2[int(y//2), int(x//2)] for x, y in xy])
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
        if d[-1] < 60: continue
        dd = np.arange(0, d[-1], 4); zz = ndimage.gaussian_filter1d(np.interp(dd, d, z), 3); g = -np.gradient(zz, 4)
        for k in range(6, len(dd)-6):
            above = g[k-6:k].mean(); below = g[k:k+6].mean()
            if above > 0.12 and below < above*0.55 and below < 0.12:
                x, y = np.interp(dd[k], d, xy[:, 0]), np.interp(dd[k], d, xy[:, 1])
                cand.append({'x': round(float(x), 1), 'y': round(float(y), 1), 'z': round(float(zz[k]), 1), 'above': round(float(above*100)), 'below': round(float(below*100)), 'ha': round(float(np.interp(dd[k], d, a)/1e4), 2), 'score': float(above-below), 'inLot': bool(MPath(lotxy).contains_point((x, y)))})
    cand.sort(key=lambda c: -c['score']); kp = []
    for c in cand:
        if all(math.hypot(c['x']-k['x'], c['y']-k['y']) > 40 for k in kp): kp.append(c)
    kp = [k for k in kp if CATCH[min(999, int(k['y']//2)), min(999, int(k['x']//2))]]
    log('keypoints', len(kp))
    # ---------------- query grids
    meta['dem'] = {'w': 1000, 'h': 1000, 'res': 2.0, 'b64': base64.b64encode(zlib.compress(np.round(Z2*10).astype('<i2').tobytes(), 9)).decode()}
    meta['dem1'] = {'x0': x0, 'y0': y0, 'w': x1-x0, 'h': y1-y0, 'b64': base64.b64encode(zlib.compress(np.round(Z1[y0:y1, x0:x1]*10).astype('<i2').tobytes(), 9)).decode()}
    # ---------------- change since older surveys
    change = {}; changeYears = []
    for yr in years[1:]:
        Zo = resample_to_grid(srcs[yr], E0, N0, zone)
        if np.isnan(Zo).mean() > 0.9: log('skip change', yr, 'little overlap'); continue
        d2 = np.nanmean((Z1.astype(np.float32)-Zo).reshape(1000, 2, 1000, 2), axis=(1, 3)); bad = np.isnan(d2) | nod2
        dz = ndimage.median_filter(np.nan_to_num(d2), 3); dz = dz-ndimage.median_filter(dz, 25); dz[bad] = 0
        tq = np.clip(dz/4, -1, 1); al = np.clip((np.abs(dz)-1.2)/1.3, 0, 1)
        img = np.zeros((1000, 1000, 4), np.uint8); img[..., 0] = np.where(tq < 0, 215, 40); img[..., 1] = np.where(tq < 0, 60, 110); img[..., 2] = np.where(tq < 0, 40, 220); img[..., 3] = (al*210).astype(np.uint8)
        png(img, f'change_{yr}.png'); changeYears.append(yr)
        change[yr] = {'lotLossHa': round(float(((dz < -1) & LOT2).sum()*4/1e4), 2), 'lotGainHa': round(float(((dz > 1) & LOT2).sum()*4/1e4), 2),
                      'lotLossM3': round(float(np.where((dz < -0.5) & LOT2, dz, 0).sum()*4)), 'lotGainM3': round(float(np.where((dz > 0.5) & LOT2, dz, 0).sum()*4))}
        log('change', yr, change[yr])
    # ---------------- fire run potential
    Zs2 = ndimage.gaussian_filter(Z1, 2); gy, gx = np.gradient(Zs2); dzx, dzy = gx, -gy
    sl = np.degrees(np.arctan(np.hypot(dzx, dzy))); asp = np.degrees(np.arctan2(-dzx, -dzy)) % 360
    idx = (2**(np.clip(sl, 0, 40)/10)*(0.35+0.65*(1+np.cos(np.radians(asp-295)))/2)).reshape(1000, 2, 1000, 2).mean((1, 3))
    clf = np.digitize(idx, [2.2, 4, 7, 11]); cols = [(0, 0, 0, 0), (0, 0, 0, 0), (245, 160, 60, 150), (225, 90, 40, 170), (150, 30, 30, 190)]
    img = np.zeros((1000, 1000, 4), np.uint8)
    for k, c in enumerate(cols): img[clf == k] = c
    img[nod2] = 0; png(img, 'fire.png')
    # ---------------- D8 codes + cold grid
    code = np.full((H, Wd), 255, np.uint8); rr0, cc0 = np.divmod(rec, Wd)
    for k, (dr, dc) in enumerate(nb):
        m = (rec >= 0) & (rr0-np.arange(H)[:, None] == dr) & (cc0-np.arange(Wd)[None, :] == dc); code[m] = k
    extra = {'d8': base64.b64encode(zlib.compress(code.tobytes(), 9)).decode(), 'cold': base64.b64encode(zlib.compress((cold*200).astype(np.uint8).tobytes(), 9)).decode(), 'change': change}
    json.dump(extra, open(out+'/extra.json', 'w'), separators=(',', ':'))
    # ---------------- site info + terrain.json
    srcnote = ', '.join(sorted({f"{y}" for y in years}))
    res_main = min(s['sx'] for s in srcs[main]); res_txt = f"{res_main:.0f} m" if res_main >= 1 else f"{res_main:.1f} m"
    meta['catchEdge'] = catch_edge
    meta['site'] = {'name': cfg['name'], 'subtitle': cfg.get('subtitle', ''), 'state': cfg.get('state', ''), 'council': cfg.get('council', ''),
                    'lat': round(latC, 5), 'lon': round(lonC, 5), 'zone': zone, 'years': years, 'main': main, 'res': res_txt,
                    'changeYears': changeYears, 'lfw': bool(cfg.get('lfw', False)), 'areaM2': round(parea(bE, bN)),
                    'nodata': round(float(nod.mean()), 3)}
    if cfg.get('rain'): meta['site']['rain'] = cfg['rain']
    for k in ('source','boundaryNote','soilNote'):
        if cfg.get(k): meta['site'][k] = cfg[k]
    data = {'meta': meta, 'E0': E0, 'N0': N0, 'lot': np.round(lotxy, 1).ravel().tolist(), 'streams': streams, 'catch': catch, 'c5': c5, 'c1': c1, 'kp': kp[:12]}
    json.dump(data, open(out+'/terrain.json', 'w'), separators=(',', ':'))
    tpl = cfg.get('template')
    if tpl and os.path.abspath(tpl) != os.path.abspath(out+'/index.html'): shutil.copy(tpl, out+'/index.html')
    shutil.rmtree(tmp, ignore_errors=True)
    log('done', out, {f: os.path.getsize(out+'/'+f)//1024 for f in sorted(os.listdir(out))})
    return data

if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1]))
    build(cfg)

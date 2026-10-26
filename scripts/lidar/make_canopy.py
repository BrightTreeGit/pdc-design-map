#!/usr/bin/env python3
"""
make_canopy.py: turn LiDAR point clouds (.laz/.las, or the ELVIS .zip files) into small
canopy and vegetation-structure grids for the PDC design map.

It reads every survey year it finds (e.g. 2008, 2014, 2022), keeps only the map's
2 km x 2 km window, and writes one compact file per year:  canopy_<site>_<year>.npz

Each file holds:
  ground   1 m grid: bare-earth height from ground points (class 2), metres AHD
  top      1 m grid: highest first return (tree tops, roofs), metres AHD
  bands    2 m grid x 7: point counts by height above ground
           [<0.5 m, 0.5-2, 2-5, 5-10, 10-20, 20-30, >30 m]
  first    2 m grid: all first returns;  first_hi: first returns above 2 m (canopy cover)
  bldg / water   2 m grids: building (class 6) and water (class 9) point counts
These are small (tens of MB) so Claude can stage them and build the canopy layers.

Usage (Windows, from this folder):  double-click make_canopy.bat
  or:  py make_canopy.py bright-tree "C:\\path\\to\\Point Clouds"
Needs:  py -m pip install "laspy[lazrs]" numpy      (the .bat does this for you)
Time: roughly 2-5 minutes per 1 km tile for the 2022 survey; older surveys are much quicker.
"""
import sys, os, re, glob, zipfile, tempfile, shutil, time
from pathlib import Path
import numpy as np

SITES = {  # map window: west edge E0, north edge N0 (MGA zone 56), size 2000 m
    "bright-tree": (492000, 7043000),
    "noosa-forest-retreat": (483394, 7096927),
    "bellbunya": (484159, 7071282),
    "nimbin": (522889, 6842186),   # Firefly Farm: 2 km window centred on 523889 E, 6841186 N (MGA zone 56)
}
SIZE = 2000
BANDS = [0.5, 2, 5, 10, 20, 30]          # band edges in metres above ground
CHUNK = 4_000_000

def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

def tile_origin(name):
    m = re.search(r'_(\d{6})_(\d{7})_', name)
    return (int(m.group(1)), int(m.group(2))) if m else None

def year_of(name):
    m = re.search(r'(19|20)\d\d', name)
    return m.group(0) if m else 'unknown'

def overlaps(o, E0, N0):
    if o is None: return True
    e, n = o  # SW corner of a 1 km tile
    return e < E0 + SIZE and e + 1000 > E0 and n < N0 and n + 1000 > N0 - SIZE

def laz_files(path, tmp):
    if path.lower().endswith('.zip'):
        d = tempfile.mkdtemp(dir=tmp)
        with zipfile.ZipFile(path) as z:
            for m in z.namelist():
                if m.lower().endswith(('.laz', '.las')):
                    z.extract(m, d)
        return sorted(glob.glob(d + '/**/*.la[sz]', recursive=True))
    return [path]

def fill_gaps(g, iters=60):
    """Fill NaN cells from neighbours (numpy only)."""
    g = g.copy()
    for _ in range(iters):
        nan = np.isnan(g)
        if not nan.any(): break
        s = np.zeros_like(g); c = np.zeros_like(g)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(g, dr, 0), dc, 1); ok = ~np.isnan(sh)
            s[ok] += sh[ok]; c[ok] += 1
        put = nan & (c > 0); g[put] = s[put] / c[put]
    if np.isnan(g).any(): g[np.isnan(g)] = np.nanmedian(g)
    return g

def process_year(year, files, E0, N0, tmp):
    import laspy
    gsum = np.zeros((SIZE, SIZE), np.float64); gcnt = np.zeros((SIZE, SIZE), np.uint32)
    top = np.full((SIZE, SIZE), -9999, np.float32)
    def chunks():
        for f in files:                       # unzip one tile at a time to keep disk use low
          d = tempfile.mkdtemp(dir=tmp)
          try:
            for lz in laz_files(f, d):
             with laspy.open(lz) as r:
                for pts in r.chunk_iterator(CHUNK):
                    x = np.asarray(pts.x); y = np.asarray(pts.y); z = np.asarray(pts.z, np.float32)
                    cls = np.asarray(pts.classification); rn = np.asarray(pts.return_number)
                    col = np.floor(x - E0).astype(np.int64); row = np.floor(N0 - y).astype(np.int64)
                    ok = (col >= 0) & (col < SIZE) & (row >= 0) & (row < SIZE) & (cls != 7) & (cls != 18)
                    if ok.any():
                        yield row[ok], col[ok], z[ok], cls[ok], rn[ok]
          finally:
            shutil.rmtree(d, ignore_errors=True)
    # pass 1: ground and tops
    n = 0
    for row, col, z, cls, rn in chunks():
        idx = row * SIZE + col
        g = cls == 2
        np.add.at(gsum.ravel(), idx[g], z[g]); np.add.at(gcnt.ravel(), idx[g], 1)
        fr = rn == 1
        np.maximum.at(top.ravel(), idx[fr], z[fr]); n += len(z)
    log(f'  {year}: pass 1 done, {n/1e6:.1f} M points in the window')
    if n == 0:
        return None
    ground = np.where(gcnt > 0, gsum / np.maximum(gcnt, 1), np.nan).astype(np.float32)
    gshare = float((gcnt > 0).mean())
    gfill = fill_gaps(ground)
    top[top < -9000] = np.nan
    # pass 2: height bands on a 2 m grid
    H = SIZE // 2
    bands = np.zeros((len(BANDS) + 1, H, H), np.uint16)
    first = np.zeros((H, H), np.uint32); first_hi = np.zeros((H, H), np.uint32)
    bldg = np.zeros((H, H), np.uint16); water = np.zeros((H, H), np.uint16)
    for row, col, z, cls, rn in chunks():
        h = z - gfill[row, col]
        i2 = (row // 2) * H + (col // 2)
        b = np.searchsorted(BANDS, h, side='right')
        np.add.at(bands.reshape(len(BANDS) + 1, -1), (b, i2), 1)
        fr = rn == 1
        np.add.at(first.ravel(), i2[fr], 1); np.add.at(first_hi.ravel(), i2[fr & (h > 2)], 1)
        np.add.at(bldg.ravel(), i2[cls == 6], 1); np.add.at(water.ravel(), i2[cls == 9], 1)
    log(f'  {year}: pass 2 done')
    return dict(ground=ground, top=top, bands=bands, first=first, first_hi=first_hi, bldg=bldg, water=water,
                E0=E0, N0=N0, band_edges=np.array(BANDS), ground_share=gshare, points=n, year=year)

def main():
    site = sys.argv[1] if len(sys.argv) > 1 else 'bright-tree'
    folder = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    if site not in SITES:
        sys.exit(f'Unknown site {site}. Presets: {", ".join(SITES)}')
    try:
        import laspy  # noqa
    except ImportError:
        sys.exit('laspy is not installed. Run:  py -m pip install "laspy[lazrs]" numpy')
    E0, N0 = SITES[site]
    files = sorted(glob.glob(os.path.join(folder, '**', '*.zip'), recursive=True) +
                   glob.glob(os.path.join(folder, '**', '*.la[sz]'), recursive=True))
    by_year = {}
    for f in files:
        name = os.path.basename(f)
        if not overlaps(tile_origin(name), E0, N0):
            continue
        by_year.setdefault(year_of(name), []).append(f)
    if not by_year:
        sys.exit(f'No point-cloud files found under {folder} that overlap the {site} map window')
    outdir = Path(folder).parent / 'Canopy outputs'; outdir.mkdir(exist_ok=True)
    for year in sorted(by_year):
        out = outdir / f'canopy_{site}_{year}.npz'
        if out.exists():
            log(f'{year}: already done ({out.name}), skipping. Delete it to redo.'); continue
        log(f'{year}: {len(by_year[year])} tile file(s)')
        tmp = tempfile.mkdtemp()
        try:
            res = process_year(year, by_year[year], E0, N0, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if res is None:
            log(f'{year}: no points inside the window'); continue
        np.savez_compressed(out, **res)
        log(f'{year}: saved {out} ({out.stat().st_size // 1024 // 1024} MB)')
    log(f'All done. Tell Claude the canopy files are ready in: {outdir}')

if __name__ == '__main__':
    main()

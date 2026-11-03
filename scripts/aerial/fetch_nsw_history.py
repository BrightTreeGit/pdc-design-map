#!/usr/bin/env python3
"""
fetch_nsw_history.py: old aerial photos for the NSW sites, for the map's photo-history slider.

Source: NSW Spatial Services "Historical Imagery" layers (HAPE: Historical Aerial Photo Enhancement). These are
old film photos that the state has already lined up and stitched into one picture per year (1955, 1966, 1980 ...).
They are released bit by bit, so a year may cover only part of a site, or none of it. The script checks every
year, keeps the ones that really show the site, and lines each one up with the design map.

Usage (Windows, from this folder):  double-click get_nsw_history_<site>.bat
   or:  py fetch_nsw_history.py nimbin
        py fetch_nsw_history.py mangiri --list          (just show which years exist over the site)
        py fetch_nsw_history.py nac --size 600 --res 0.3 (smaller square, finer detail)
Sites: nimbin (Firefly Farm), willow-vale, nac, mangiri, regenify

Output: history_nsw/<site>/ with one JPG per year (n<year>.jpg) and history.json in the map's own format.
Tell Claude when it's done; Claude checks the pictures line up and adds them to the trial map.
Gentle on the servers: one request at a time with a short pause, and retries. Run it again any time:
years already downloaded are skipped, so a run that stops halfway just carries on.
Needs: requests, pillow, numpy (the .bat installs them).
"""
import argparse, io, json, math, os, sys, time
from pathlib import Path

import numpy as np
import requests
from PIL import Image

BASE = os.environ.get("NSW_HIST_BASE", "https://portal.spatial.nsw.gov.au/tileservices/Hosted")
SVC = BASE + "/HistoricalImagery{year}/MapServer"
HEADERS = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
SOURCE = "NSW Spatial Services, Historical Imagery (HAPE ortho mosaics), CC BY 4.0"
YEARS = range(1940, 2016)  # HAPE years seen so far run from the 1940s to the 2000s; checking a wider range is cheap
# The map window for each site (from map/sites/<site>/terrain.json): top-left corner E0/N0 in MGA, 2000 m square,
# map x = E - E0, y = N0 - N, 1 m per map unit.
SITES = {
    "nimbin":      {"E0": 523889.0, "N0": 6841186.0, "zone": 56, "name": "Firefly Farm"},
    "willow-vale": {"E0": 383492.0, "N0": 6469820.0, "zone": 56, "name": "Willow Vale"},
    "nac":         {"E0": 409432.0, "N0": 6385368.0, "zone": 56, "name": "NAC"},
    "mangiri":     {"E0": 766045.0, "N0": 6074550.0, "zone": 55, "name": "Mangiri"},
    "regenify":    {"E0": 539619.0, "N0": 6844643.0, "zone": 56, "name": "Regenify"},
}
WINDOW = 2000  # metres, the map window

def get(url, params=None, what="request", binary=False, quiet_404=False):
    for wait in (0, 5, 20, 60):
        if wait:
            print(f"   retrying {what} in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=120)
        except Exception as e:
            print(f"   {what} failed: {e}"); continue
        if r.status_code in (400, 404):
            if not quiet_404:
                print(f"   {what}: not there ({r.status_code})")
            return None
        if not r.ok:
            print(f"   {what}: status {r.status_code}"); continue
        if binary:
            if r.content[:2] == b"\xff\xd8" or r.content[:4] == b"\x89PNG":
                return r.content
            return None  # blank or error tile: treat as no picture here
        try:
            j = r.json()
        except Exception:
            return None
        if isinstance(j, dict) and j.get("error"):
            return None
        return j
    return None

# ---- MGA (GRS80, Krueger series) to latitude/longitude, for whole arrays at once
_a = 6378137.0; _f = 1 / 298.257222101; _k0 = 0.9996
_n = _f / (2 - _f); _A = _a / (1 + _n) * (1 + _n**2 / 4 + _n**4 / 64); _e = math.sqrt(_f * (2 - _f))
_al = [_n/2 - 2*_n**2/3 + 5*_n**3/16, 13*_n**2/48 - 3*_n**3/5, 61*_n**3/240]
_be = [_n/2 - 2*_n**2/3 + 37*_n**3/96, _n**2/48 + _n**3/15, 17*_n**3/480]

def mga2ll(E, N, zone):
    xi = (N - 1e7) / (_k0 * _A); eta = (E - 5e5) / (_k0 * _A)
    xp, ep = xi.copy(), eta.copy()
    for j in range(3):
        k = 2 * (j + 1)
        xp = xp - _be[j] * np.sin(k * xi) * np.cosh(k * eta)
        ep = ep - _be[j] * np.cos(k * xi) * np.sinh(k * eta)
    t0 = np.sin(xp) / np.sqrt(np.sinh(ep)**2 + np.cos(xp)**2)  # tan of conformal latitude
    t = t0.copy()
    for _ in range(6):  # conformal -> geodetic latitude
        s = t / np.sqrt(1 + t * t)
        sig = np.sinh(_e * np.arctanh(_e * s))
        f = t * np.sqrt(1 + sig**2) - sig * np.sqrt(1 + t * t) - t0
        df = (np.sqrt((1 + sig**2) * (1 + t * t)) - sig * t) * (1 - _e**2) * np.sqrt(1 + t * t) / (1 + (1 - _e**2) * t * t)
        t = t - f / df
    lat = np.degrees(np.arctan(t))
    lon = (zone * 6 - 183) + np.degrees(np.arctan2(np.sinh(ep), np.cos(xp)))
    return lat, lon

def ll2merc(lat, lon):
    R = 6378137.0
    return R * np.radians(lon), R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))

# ---- the work
def find_years(out):
    cache = out / "years.json"
    if cache.exists():
        return json.loads(cache.read_text())
    print("Checking which years NSW has published (one quick look per year)...")
    found = {}
    for y in YEARS:
        j = get(SVC.format(year=y), {"f": "json"}, what=f"year {y}", quiet_404=True)
        if j and j.get("tileInfo"):
            lods = {int(l["level"]): float(l["resolution"]) for l in j["tileInfo"]["lods"]}
            found[str(y)] = {"origin": [j["tileInfo"]["origin"]["x"], j["tileInfo"]["origin"]["y"]],
                             "tile": int(j["tileInfo"].get("rows", 256)), "lods": lods}
            print(f"  {y}: yes")
        time.sleep(0.3)
    cache.write_text(json.dumps(found, indent=1))
    print(f"  {len(found)} years published statewide: {', '.join(found) or 'none'}")
    return found

def fetch_year(year, info, mx, my, res, zoom_cap, out, label):
    """Download the tiles under the square for one year and resample them onto the map's grid."""
    lods = {int(k): v for k, v in info["lods"].items()}
    # ground metres per tile pixel are smaller than Mercator metres by cos(latitude)
    coslat = abs(math.cos(math.atan(math.sinh(float(my.mean()) / 6378137.0))))
    pick = [z for z, r in sorted(lods.items()) if r * coslat <= res * 1.05 and z <= zoom_cap]
    z = pick[0] if pick else max(z for z in lods if z <= zoom_cap)
    r = lods[z]; ox, oy = info["origin"]; T = info["tile"]
    c0 = int((mx.min() - ox) // (r * T)); c1 = int((mx.max() - ox) // (r * T))
    r0 = int((oy - my.max()) // (r * T)); r1 = int((oy - my.min()) // (r * T))
    ncol, nrow = c1 - c0 + 1, r1 - r0 + 1
    # look at the centre tile first: if there is no picture there, skip the year without downloading the rest
    cc, rc = (c0 + c1) // 2, (r0 + r1) // 2
    probe = get(SVC.format(year=year) + f"/tile/{z}/{rc}/{cc}", what=f"{year} centre tile", binary=True, quiet_404=True)
    if not probe:
        print(f"  {year}: no picture over {label} (not released here yet)"); return None
    print(f"  {year}: downloading {ncol * nrow} tiles at zoom {z} (about {r * coslat:.2f} m detail)")
    mosaic = np.zeros((nrow * T, ncol * T, 4), dtype=np.uint8)
    for rr in range(r0, r1 + 1):
        for cc_ in range(c0, c1 + 1):
            data = probe if (rr, cc_) == (rc, cc) else get(SVC.format(year=year) + f"/tile/{z}/{rr}/{cc_}", what=f"tile {z}/{rr}/{cc_}", binary=True, quiet_404=True)
            if data:
                im = Image.open(io.BytesIO(data)).convert("RGBA")
                if im.size != (T, T):
                    im = im.resize((T, T))
                mosaic[(rr - r0) * T:(rr - r0 + 1) * T, (cc_ - c0) * T:(cc_ - c0 + 1) * T] = np.asarray(im)
                time.sleep(0.15)
    # map each output pixel to the mosaic (bilinear)
    px = (mx - ox) / r - c0 * T - 0.5
    py = (oy - my) / r - r0 * T - 0.5
    x0 = np.clip(np.floor(px).astype(int), 0, mosaic.shape[1] - 2); y0 = np.clip(np.floor(py).astype(int), 0, mosaic.shape[0] - 2)
    fx = np.clip(px - x0, 0, 1)[..., None]; fy = np.clip(py - y0, 0, 1)[..., None]
    m = mosaic.astype(np.float32)
    img = (m[y0, x0] * (1 - fx) * (1 - fy) + m[y0, x0 + 1] * fx * (1 - fy) + m[y0 + 1, x0] * (1 - fx) * fy + m[y0 + 1, x0 + 1] * fx * fy)
    alpha = img[..., 3] > 128
    rgb = img[..., :3]
    lum = rgb.mean(axis=2)
    real = alpha & (lum > 3) & (lum < 252)  # not empty, not pure black or white fill
    cover = float(real.mean())
    if cover < 0.05:
        print(f"  {year}: under 5% of the square has a picture, skipped"); return None
    rgb[~alpha] = 0
    bw = bool(np.abs(rgb[real][:, 0] - rgb[real][:, 1]).mean() < 3 and np.abs(rgb[real][:, 1] - rgb[real][:, 2]).mean() < 3)
    fn = f"n{year}.jpg"
    Image.fromarray(rgb.astype(np.uint8)).save(out / fn, quality=85)  # saved fresh: no GPS or camera data in the file
    print(f"    saved {fn}: {cover:.0%} of the square covered{', black and white' if bw else ''}")
    return {"y": int(year), "id": f"nsw{year}", "from": None, "to": None, "res": round(res, 2), "f": fn,
            "name": f"NSW HistoricalImagery{year}", "hape": True, "bw": bw, "cover": round(cover, 2), "zoom": z}

def main():
    ap = argparse.ArgumentParser(description="Old NSW aerial photos for the map's photo-history slider")
    ap.add_argument("site", choices=sorted(SITES))
    ap.add_argument("--size", type=float, default=1400, help="square side in metres, centred on the map window (default 1400)")
    ap.add_argument("--res", type=float, default=0.7, help="metres per pixel in the output (default 0.7)")
    ap.add_argument("--zoom-cap", type=int, default=19, help="finest tile zoom to use (default 19)")
    ap.add_argument("--list", action="store_true", help="only list the years that have a picture over the site")
    ap.add_argument("--recheck-years", action="store_true", help="look again for newly published years")
    a = ap.parse_args()
    S = SITES[a.site]
    here = Path(__file__).resolve().parent
    out = here / "history_nsw" / a.site; out.mkdir(parents=True, exist_ok=True)
    if a.recheck_years and (out / "years.json").exists():
        (out / "years.json").unlink()
    size = min(a.size, WINDOW)
    x0 = y0 = (WINDOW - size) / 2  # top-left of the square in map units
    npx = int(round(size / a.res))
    # every output pixel's centre in MGA, then in Web Mercator (the tiles' grid)
    xs = x0 + (np.arange(npx) + 0.5) * a.res
    ys = y0 + (np.arange(npx) + 0.5) * a.res
    X, Y = np.meshgrid(xs, ys)
    lat, lon = mga2ll(S["E0"] + X, S["N0"] - Y, S["zone"])
    mx, my = ll2merc(lat, lon)
    print(f"{S['name']}: {size:.0f} m square at {a.res} m per pixel ({npx} x {npx}), centre {lat.mean():.4f}, {lon.mean():.4f}")

    years = find_years(out)
    if not years:
        sys.exit("No historical imagery years answered. The NSW service may be down; try again later.")
    hj = out / "history.json"
    old = {}
    if hj.exists():
        try:
            old = {str(r["y"]): r for r in json.loads(hj.read_text())["runs"]}
        except Exception:
            old = {}
    runs = []
    for y in sorted(years, key=int):
        if y in old and (out / old[y]["f"]).exists():
            print(f"  {y}: already downloaded"); runs.append(old[y]); continue
        if a.list:
            info = years[y]; lods = {int(k): v for k, v in info["lods"].items()}
            z = min(16, max(lods)); r = lods[z]; ox, oy = info["origin"]; T = info["tile"]
            c = int((float(mx.mean()) - ox) // (r * T)); rw = int((oy - float(my.mean())) // (r * T))
            ok = get(SVC.format(year=y) + f"/tile/{z}/{rw}/{c}", what=f"{y}", binary=True, quiet_404=True)
            print(f"  {y}: {'picture over the site' if ok else 'nothing here yet'}"); time.sleep(0.3); continue
        rec = fetch_year(y, years[y], mx, my, a.res, a.zoom_cap, out, S["name"])
        if rec:
            runs.append(rec)
            hj.write_text(json.dumps({"x0": round(x0), "y0": round(y0), "size": round(size), "source": SOURCE,
                                      "site": a.site, "note": "HAPE mosaics are already lined up by NSW; allow a few metres. Capture dates within the year are not given.",
                                      "runs": sorted(runs, key=lambda r: r["y"])}, indent=1))
    if a.list:
        return
    print(f"\nDone: {len(runs)} years with a picture of {S['name']}, saved in {out}.")
    print("Tell Claude the NSW history photos are ready.")

if __name__ == "__main__":
    main()

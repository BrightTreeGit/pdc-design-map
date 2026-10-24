#!/usr/bin/env python3
"""
fetch_terrain_tiles.py: placeholder elevation for a block while the state elevation services are offline.

Downloads the free, open "Terrain Tiles" (Mapzen / AWS open data, compiled from SRTM, GMTED and national
DEMs) for the site's 2 km window into <folder>/Site data/terrain_tiles/. Much coarser than 1 m LiDAR, so
the map marks it as a placeholder; replace it with LiDAR when the government services are back.

  py fetch_terrain_tiles.py --folder Annwn          (needs Site data/window.json from fetch_qld_site.py)
"""
import argparse, json, math, time
from pathlib import Path
import requests

URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
H = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}


def tile(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--folder", required=True); ap.add_argument("--zoom", type=int, default=15)
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[1] / a.folder / "Site data"
    win = json.loads((root / "window.json").read_text())
    lat, lon = win["centre_lat"], win["centre_lon"]
    d = 0.016                                     # about 1.6 km each way: the 2 km window plus a margin
    x0, y0 = tile(lon - d, lat + d, a.zoom); x1, y1 = tile(lon + d, lat - d, a.zoom)
    out = root / "terrain_tiles"; out.mkdir(exist_ok=True)
    got = []
    xs = range(int(x0), int(x1) + 1); ys = range(int(y0), int(y1) + 1)
    print(f"Downloading {len(xs) * len(ys)} terrain tiles at zoom {a.zoom} ...")
    for x in xs:
        for y in ys:
            fn = out / f"{a.zoom}_{x}_{y}.png"
            if not (fn.exists() and fn.stat().st_size > 1000):
                for wait in (0, 5, 20):
                    if wait: time.sleep(wait)
                    try:
                        r = requests.get(URL.format(z=a.zoom, x=x, y=y), headers=H, timeout=60)
                        if r.ok and r.content[:4] == b"\x89PNG": fn.write_bytes(r.content); break
                        print(f"  tile {x},{y}: status {r.status_code}")
                    except Exception as e:
                        print(f"  tile {x},{y}: {e}")
                time.sleep(0.5)
            if fn.exists(): got.append([a.zoom, x, y, fn.name])
    (out / "tiles.json").write_text(json.dumps({"zoom": a.zoom, "tiles": got, "encoding": "terrarium: (R*256 + G + B/256) - 32768 metres"}, indent=1))
    print(f"  saved {len(got)} tiles to {out}")
    print(f"\nDone. Tell Claude: \"{a.folder} placeholder elevation is ready\".")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
fetch_elvis.py: download the 1 m LiDAR elevation (DEM) tiles for a block from ELVIS (Geoscience Australia's
Elevation Information System), using the window saved by fetch_qld_site.py / fetch_nsw_site.py.

  py fetch_elvis.py --folder Annwn          (reads Annwn/Site data/window.json)

Saves to <folder>/Lidar-survey data/ELVIS/ : every downloadable 1 m DEM tile touching the 2 km window
(newest survey first, older surveys too, for change mapping), plus elvis_index.json listing everything on offer.
If ELVIS only offers the data by order, it opens the ELVIS website with the area ready to draw.
"""
import argparse, json, sys, time, webbrowser
from pathlib import Path
import requests

INDEX = "https://elvis2018-ga.fmecloud.com/fmedatastreaming/elvis_indexes/ReturnDownloadables.fmw"
H = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}


def walk(o, path=()):
    """Yield (path, dict) for every dict in the JSON that has a download link."""
    if isinstance(o, dict):
        if any(k in o for k in ("download_url", "url")) and any(k in o for k in ("file_name", "name", "filename")):
            yield path, o
        for k, v in o.items(): yield from walk(v, path + (str(k),))
    elif isinstance(o, list):
        for v in o: yield from walk(v, path)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--folder", required=True); a = ap.parse_args()
    root = Path(__file__).resolve().parents[1] / a.folder
    win = json.loads((root / "Site data" / "window.json").read_text())
    lat, lon = win["centre_lat"], win["centre_lon"]
    d = 0.012                                    # about 1.3 km each way: the map's 2 km window plus a margin
    bbox = {"xmin": lon - d, "xmax": lon + d, "ymin": lat - d, "ymax": lat + d}
    out = root / "Lidar-survey data" / "ELVIS"; out.mkdir(parents=True, exist_ok=True)
    print(f"Asking ELVIS what elevation data covers {a.folder} ...")
    j = None
    for wait in (0, 10, 30):
        if wait: print(f"  retrying in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(INDEX, params=bbox, headers=H, timeout=120)
            if r.ok: j = r.json(); break
            print(f"  ELVIS status {r.status_code}")
        except Exception as e:
            print(f"  ELVIS request failed: {e}")
    if j is None:
        return order_by_hand(bbox)
    (out / "elvis_index.json").write_text(json.dumps(j, indent=1))
    files = []
    for path, f in walk(j):
        name = f.get("file_name") or f.get("name") or f.get("filename"); url = f.get("download_url") or f.get("url")
        label = " ".join(path) + " " + name
        if "dem" in label.lower() and ("1m" in label.lower().replace(" ", "") or "1 m" in label.lower()) and url and url.startswith("http"):
            files.append((name, url, label))
    print(f"  {len(files)} downloadable 1 m DEM tiles found")
    if not files:
        return order_by_hand(bbox)
    for name, url, label in files:
        fn = out / Path(name).name
        if fn.exists() and fn.stat().st_size > 1000: print(f"  have {fn.name}"); continue
        print(f"  downloading {fn.name}")
        try:
            with requests.get(url, headers=H, timeout=600, stream=True) as r:
                r.raise_for_status()
                with open(fn, "wb") as fh:
                    for chunk in r.iter_content(1 << 20): fh.write(chunk)
        except Exception as e:
            print(f"    failed: {e}")
        time.sleep(2)
    print(f"\nDone. Tell Claude: \"{a.folder} elevation is ready\".")


def order_by_hand(bbox):
    print("\nELVIS didn't offer a direct download for this area, so it has to be ordered (free, a few clicks):")
    print("  1. The ELVIS website is opening. Choose 'Elevation and Depth - Foundation Spatial Data'.")
    print("  2. Zoom to the block, click 'Select area by drawing', and draw a box around it and the hills nearby.")
    print("  3. Tick the newest '1 Metre' DEM (and older 1 m surveys if listed), enter your email, and order.")
    print("  4. The download link arrives by email: save the files into this site's 'Lidar-survey data' folder.")
    print(f"  Area: longitude {bbox['xmin']:.4f} to {bbox['xmax']:.4f}, latitude {bbox['ymin']:.4f} to {bbox['ymax']:.4f}")
    webbrowser.open("https://elevation.fsdf.org.au/")


if __name__ == "__main__":
    main()

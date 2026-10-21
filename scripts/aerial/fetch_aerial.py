#!/usr/bin/env python3
"""
fetch_aerial.py: download a north-up aerial photo that lines up exactly with a PDC design map.

It asks the state government's public imagery service for the map's 2 km x 2 km window,
in the same MGA (GDA2020) coordinates the map uses, so the photo needs no manual alignment.

  QLD: Queensland Government "Latest State Program" imagery (CC BY 4.0, State of Queensland)
  NSW: NSW Spatial Services imagery (CC BY 4.0, NSW Spatial Services)

Usage (Windows, from this folder):
  py fetch_aerial.py bright-tree
  py fetch_aerial.py --e0 492000 --n0 7043000 --zone 56 --state QLD --name my-site

Output: aerial_<name>.jpg (4000 x 4000 px, 0.5 m per pixel) if Pillow is installed,
otherwise four quarter tiles aerial_<name>_r<row>c<col>.jpg (Claude can stitch them).
Gentle on the servers: four requests, two seconds apart, with retries.
"""
import argparse, sys, time
from pathlib import Path
import requests

SERVICES = {
    "QLD": ("https://spatial-img.information.qld.gov.au/arcgis/rest/services/Basemaps/LatestStateProgram_AllUsers/ImageServer/exportImage", "image"),
    "NSW": ("https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Imagery/MapServer/export", "map"),
}
# Map windows (west edge E0, north edge N0, MGA zone, state) for the PDC sites that have maps
SITES = {
    "bright-tree": (492000, 7043000, 56, "QLD"),
    "noosa-forest-retreat": (483394, 7096927, 56, "QLD"),
    "bellbunya": (484159, 7071282, 56, "QLD"),
}
HEADERS = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}

def fetch(url, kind, bbox, sr, px, out):
    params = {"bbox": ",".join(str(v) for v in bbox), "bboxSR": sr, "size": f"{px},{px}", "format": "jpg", "f": "image"}
    if kind == "image":
        params.update({"imageSR": sr, "compression": "JPEG", "compressionQuality": 85})
    else:
        params.update({"imageSR": sr, "dpi": 96, "transparent": "false"})
    for wait in (0, 10, 30):
        if wait:
            print(f"  retrying in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=120)
        except Exception as e:
            print(f"  request failed: {e}"); continue
        ctype = r.headers.get("content-type", "")
        if r.ok and ctype.startswith("image"):
            out.write_bytes(r.content); print(f"  saved {out.name} ({len(r.content)//1024} KB)"); return True
        print(f"  status {r.status_code}, {ctype}: {r.text[:200]!r}")
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?", help="preset name, e.g. bright-tree")
    ap.add_argument("--e0", type=float); ap.add_argument("--n0", type=float)
    ap.add_argument("--zone", type=int, default=56); ap.add_argument("--state", default="QLD")
    ap.add_argument("--name", default=None); ap.add_argument("--size", type=float, default=2000, help="window size in metres")
    a = ap.parse_args()
    if a.site:
        if a.site not in SITES:
            sys.exit(f"Unknown site {a.site}. Presets: {', '.join(SITES)}; or give --e0 --n0 --zone --state")
        e0, n0, zone, state = SITES[a.site]; name = a.name or a.site
    else:
        if a.e0 is None or a.n0 is None:
            sys.exit("Give a preset name or --e0 and --n0 (the map window's west and north edges in MGA metres)")
        e0, n0, zone, state, name = a.e0, a.n0, a.zone, a.state.upper(), a.name or "site"
    url, kind = SERVICES[state]
    half = a.size / 2; px = 2000
    tiles = []
    for row in range(2):
        for col in range(2):
            x0 = e0 + col * half; x1 = x0 + half; y1 = n0 - row * half; y0 = y1 - half
            out = Path(f"aerial_{name}_r{row}c{col}.jpg")
            print(f"Tile row {row} col {col}")
            ok = False
            for sr in (7800 + zone, 28300 + zone):   # GDA2020 MGA first, then GDA94 MGA (about 1.8 m apart)
                ok = fetch(url, kind, (x0, y0, x1, y1), sr, px, out)
                if ok:
                    break
            if not ok:
                sys.exit("Could not get this tile; the imagery service may be busy. Try again later.")
            tiles.append((row, col, out)); time.sleep(2)
    try:
        from PIL import Image
        full = Image.new("RGB", (px * 2, px * 2))
        for row, col, p in tiles:
            full.paste(Image.open(p).convert("RGB"), (col * px, row * px))
        dst = Path(f"aerial_{name}.jpg"); full.save(dst, quality=82)
        for _, _, p in tiles:
            p.unlink()
        print(f"Done: {dst} covers E {e0:.0f}-{e0 + a.size:.0f}, N {n0 - a.size:.0f}-{n0:.0f} (MGA zone {zone})")
    except ImportError:
        print("Pillow isn't installed, so the four tiles were kept. Send them to Claude to stitch, or run: py -m pip install pillow")

if __name__ == "__main__":
    main()

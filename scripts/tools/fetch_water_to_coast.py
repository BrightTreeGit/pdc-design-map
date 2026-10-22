#!/usr/bin/env python3
"""
fetch_water_to_coast.py: elevation and a photo from Bright Tree to the coast, for the
"Bright Tree Water" map (where the water goes after it leaves the block).

Downloads two files, one request each, into  Bright Tree\\Water to the coast\\ :
  coast_dem_15m.tif   ground heights every 15 m (Queensland Government elevation model, CC BY 4.0)
  coast_aerial_15m.jpg  latest state aerial photo of the same area, 15 m per pixel
Area: about 40 km east-west by 36 km north-south, MGA zone 56 (GDA2020), from the Blackall Range
foothills west of Bright Tree to past the coastline.
"""
import json, time, sys
from pathlib import Path
import requests

DEM = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/Elevation/QldDem/ImageServer/exportImage"
ORTHO = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/Basemaps/LatestStateProgram_AllUsers/ImageServer/exportImage"
ORTHO2 = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/TimeSeries/AerialOrtho_AllUsers/ImageServer/exportImage"
H = {"User-Agent": "Mozilla/5.0 (PDC-Design-Map; permaculture course)"}
BBOX = (480000, 7030000, 520000, 7066000)   # E min, N min, E max, N max (MGA56): all of the Bright Tree catchment, north to the river, east past the coast
RES = 15
W, Hh = (BBOX[2]-BBOX[0])//RES, (BBOX[3]-BBOX[1])//RES

def get(url, params, check):
    for w in (0, 5, 20, 60):
        if w: print(f"   retry in {w}s"); time.sleep(w)
        try:
            r = requests.get(url, params=params, headers=H, timeout=600)
            if r.status_code != 200: print("   status", r.status_code); continue
            if check(r.content): return r.content
            print("   unexpected reply:", r.text[:200])
        except Exception as e:
            print("   failed:", e)
    return None

def main():
    here = Path(__file__).resolve().parent
    root = here.parent if here.name == "_tools" else here
    out = root / "Bright Tree" / "Water to the coast"
    out.mkdir(parents=True, exist_ok=True)
    print("Saving into", out)
    common = {"bbox": ",".join(map(str, BBOX)), "bboxSR": 7856, "imageSR": 7856, "size": f"{W},{Hh}", "f": "image"}
    # the server limits each image to a few million cells, so fetch 2 x 2 tiles
    NX, NY = 2, 2
    tw, th = W // NX, Hh // NY
    for j in range(NY):
        for i in range(NX):
            fn = out / f"coast_dem_15m_r{j}c{i}.tif"
            if fn.exists() and fn.stat().st_size > 100000: print(f"Tile {j}{i} already downloaded"); continue
            e0 = BBOX[0] + i * tw * RES; e1 = e0 + tw * RES
            n1 = BBOX[3] - j * th * RES; n0 = n1 - th * RES
            print(f"Downloading heights, tile {j*NX+i+1} of {NX*NY} ({tw} x {th} cells)...")
            d = get(DEM, {"bbox": f"{e0},{n0},{e1},{n1}", "bboxSR": 7856, "imageSR": 7856, "size": f"{tw},{th}", "f": "image",
                          "format": "tiff", "pixelType": "F32", "noData": -9999}, lambda b: b[:2] in (b"II", b"MM"))
            if not d: sys.exit("Could not download the heights. Check the internet connection and run again.")
            fn.write_bytes(d); print("   saved", fn.name, round(len(d)/1e6, 1), "MB"); time.sleep(1)
    fa = out / "coast_aerial_15m.jpg"
    if fa.exists() and fa.stat().st_size > 100000: print("Photo already downloaded")
    else:
        print("Downloading the aerial photo...")
        p = {**common, "format": "jpg", "compressionQuality": 80}
        d = get(ORTHO, p, lambda b: b[:3] == b"\xff\xd8\xff") or get(ORTHO2, p, lambda b: b[:3] == b"\xff\xd8\xff")
        if d: fa.write_bytes(d); print("   saved", fa.name, round(len(d)/1e6, 1), "MB")
        else: print("   no photo this time (the map still works without it)")
    (out / "README.txt").write_text("Bright Tree Water: elevation (QldDem, 15 m) and aerial of the area from Bright Tree to the coast.\n"
        f"Box (MGA56 / EPSG:7856): {BBOX}, {RES} m cells, {W} x {Hh}.\nSource: State of Queensland (CC BY 4.0).\n")
    print("\nDone. Tell Claude: 'water to the coast is ready'.")
    input("Press Enter to close.")

if __name__ == "__main__":
    main()

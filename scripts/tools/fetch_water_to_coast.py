#!/usr/bin/env python3
"""
fetch_water_to_coast.py: elevation and a photo from Bright Tree to the coast, for the
"Bright Tree Water" map (where the water goes after it leaves the block).

Downloads two files, one request each, into  Bright Tree\\Water to the coast\\ :
  coast_dem_10m.tif   ground heights every 10 m (Queensland Government elevation model, CC BY 4.0)
  coast_aerial_10m.jpg  latest state aerial photo of the same area, 10 m per pixel
Area: about 34 km east-west by 30 km north-south, MGA zone 56 (GDA2020), from the Blackall Range
foothills west of Bright Tree to past the coastline.
"""
import json, time, sys
from pathlib import Path
import requests

DEM = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/Elevation/QldDem/ImageServer/exportImage"
ORTHO = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/Basemaps/LatestStateProgram_AllUsers/ImageServer/exportImage"
ORTHO2 = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/TimeSeries/AerialOrtho_AllUsers/ImageServer/exportImage"
H = {"User-Agent": "Mozilla/5.0 (PDC-Design-Map; permaculture course)"}
BBOX = (484000, 7030000, 518000, 7060000)   # E min, N min, E max, N max (MGA56)
RES = 10
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
    fn = out / "coast_dem_10m.tif"
    if fn.exists() and fn.stat().st_size > 100000: print("Heights already downloaded")
    else:
        print(f"Downloading heights ({W} x {Hh} cells)... this can take a minute")
        d = get(DEM, {**common, "format": "tiff", "pixelType": "F32", "compression": "LZ77", "interpolation": "RSP_BilinearInterpolation", "noData": -9999},
                lambda b: b[:2] in (b"II", b"MM"))
        if not d: sys.exit("Could not download the heights. Check the internet connection and run again.")
        fn.write_bytes(d); print("   saved", fn.name, round(len(d)/1e6, 1), "MB")
    fa = out / "coast_aerial_10m.jpg"
    if fa.exists() and fa.stat().st_size > 100000: print("Photo already downloaded")
    else:
        print("Downloading the aerial photo...")
        p = {**common, "format": "jpg", "compressionQuality": 80}
        d = get(ORTHO, p, lambda b: b[:3] == b"\xff\xd8\xff") or get(ORTHO2, p, lambda b: b[:3] == b"\xff\xd8\xff")
        if d: fa.write_bytes(d); print("   saved", fa.name, round(len(d)/1e6, 1), "MB")
        else: print("   no photo this time (the map still works without it)")
    (out / "README.txt").write_text("Bright Tree Water: elevation (QldDem, 10 m) and aerial of the area from Bright Tree to the coast.\n"
        f"Box (MGA56 / EPSG:7856): {BBOX}, {RES} m cells, {W} x {Hh}.\nSource: State of Queensland (CC BY 4.0).\n")
    print("\nDone. Tell Claude: 'water to the coast is ready'.")
    input("Press Enter to close.")

if __name__ == "__main__":
    main()

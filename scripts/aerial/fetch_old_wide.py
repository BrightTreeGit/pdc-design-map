#!/usr/bin/env python3
"""
fetch_old_wide.py: second pass for the old photos. The archive only places old frames roughly, so this grabs a wider
5 km square of each (1 m detail) plus two modern reference photos of the same square, so Claude can match landmarks
(ridges, creeks, roads) and pin each old photo exactly onto the block.
Run: double-click get_old_wide_bright-tree.bat (needs old_photos/old_photos.json from the first pass).
"""
import sys, json, time
from pathlib import Path
import requests

ARCH = "https://qimagery.information.qld.gov.au/proxy?https://spatial-img.information.qld.gov.au/arcgis/rest/services/QImagery/QldArchive_AerialPhotos/ImageServer"
ORTHO = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/TimeSeries/AerialOrtho_AllUsers/ImageServer"
H = {"User-Agent": "Mozilla/5.0 (PDC-Design-Map; permaculture course)", "Referer": "https://qimagery.information.qld.gov.au/"}
WIN, PX = 5000, 4000

def img(base, params):
    for w in (0, 5, 20, 60):
        if w: print(f"   retry in {w}s"); time.sleep(w)
        try:
            r = requests.get(base + "/exportImage?" + requests.compat.urlencode(params), headers=H, timeout=300)
            if r.status_code == 200 and r.content[:3] == b"\xff\xd8\xff": return r.content
            print("   status", r.status_code, r.text[:150])
        except Exception as e:
            print("   failed:", e)
    return None

def main():
    here = Path(__file__).resolve().parent / "old_photos"
    meta = json.loads((here / "old_photos.json").read_text())
    cx, cy = meta["centre_mga56"]
    out = here / "wide"; out.mkdir(exist_ok=True)
    bbox = f"{cx-WIN/2},{cy-WIN/2},{cx+WIN/2},{cy+WIN/2}"
    common = {"bbox": bbox, "bboxSR": 7856, "imageSR": 7856, "size": f"{PX},{PX}", "format": "jpg", "compressionQuality": 85, "noData": 0, "f": "image"}
    jobs = [("ref_2008", ORTHO, 4694), ("ref_1994", ORTHO, 4628)] + [(f"wide_{r['year']}_{r['id']}", ARCH, r["id"]) for r in meta["runs"]]
    for name, base, oid in jobs:
        fn = out / f"{name}.jpg"
        if fn.exists() and fn.stat().st_size > 5000: print(f"  {name}: already done"); continue
        print(f"  {name}")
        data = img(base, dict(common, mosaicRule=json.dumps({"mosaicMethod": "esriMosaicLockRaster", "lockRasterIds": [oid]})))
        if data: fn.write_bytes(data)
        time.sleep(1.5)
    print(f"\nDone. Tell Claude the wide photos are ready.")

if __name__ == "__main__":
    main()

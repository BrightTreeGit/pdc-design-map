#!/usr/bin/env python3
"""
fetch_old_photos.py: downloads the best historical (scanned film) aerial photo for every year the Queensland archive
holds over the site, cut to a 1.4 km square around the block, for the map's history slider.
Source: QImagery historical aerial photography, State of Queensland (CC BY 4.0 / public domain; keep the credit).
Uses the public QImagery viewer's own image service. One request at a time, gently.
Run: double-click get_old_photos_<site>.bat. Output: old_photos/old_<year>_<id>.jpg + old_photos.json
"""
import sys, json, time, datetime
from pathlib import Path
import requests

BASE = "https://qimagery.information.qld.gov.au/proxy?https://spatial-img.information.qld.gov.au/arcgis/rest/services/QImagery/QldArchive_AerialPhotos/ImageServer"
H = {"User-Agent": "Mozilla/5.0 (PDC-Design-Map; permaculture course)", "Referer": "https://qimagery.information.qld.gov.au/"}
SITES = {"bright-tree": (492921, 7041970, 420), "bellbunya": (485272, 7069910, 646), "noosa-forest-retreat": (484394, 7095927, 470)}
WIN, PX = 1400, 2000  # window in metres, output pixels

EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
def dt(ms):
    return EPOCH + datetime.timedelta(milliseconds=ms)

def get(path, params, img=False):
    for w in (0, 5, 20, 60):
        if w: print(f"   retry in {w}s"); time.sleep(w)
        try:
            r = requests.get(BASE + path + "?" + requests.compat.urlencode(params), headers=H, timeout=180)
            if r.status_code != 200: print("   status", r.status_code); continue
            if img:
                if r.headers.get("content-type", "").startswith("image"): return r.content
                print("   not an image:", r.text[:150]); continue
            j = r.json()
            if "error" in j: print("   error", j["error"]); continue
            return j
        except Exception as e:
            print("   failed:", e)
    return None

def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "bright-tree"
    cx, cy, span = SITES[site]
    out = Path(__file__).resolve().parent / "old_photos"; out.mkdir(exist_ok=True)
    h = span / 2
    pts = [(cx, cy), (cx - h, cy - h), (cx + h, cy + h), (cx - h, cy + h), (cx + h, cy - h)]
    frames = {}
    print(f"Finding historical frames over {site}...")
    for x, y in pts:
        j = get("/query", {"geometry": f"{x},{y}", "geometryType": "esriGeometryPoint", "inSR": 7856, "spatialRel": "esriSpatialRelIntersects",
                           "outFields": "objectid,framename,begindate,resolution,attribution", "returnGeometry": "false", "f": "json"})
        for f in (j or {}).get("features", []):
            a = f["attributes"]; d = frames.setdefault(a["objectid"], dict(a, hits=0)); d["hits"] += 1
        time.sleep(1)
    by = {}
    for a in frames.values():
        yr = dt(a["begindate"]).year if a.get("begindate") else 0
        a["year"] = yr; by.setdefault(yr, []).append(a)
    picks = []
    for yr in sorted(by):
        best = sorted(by[yr], key=lambda a: (-a["hits"], float(a.get("resolution") or 9)))[0]
        if best["hits"] < 3: print(f"  {yr}: only covers a corner of the block, skipped"); continue
        picks.append(best)
    print(f"  {len(picks)} years with the whole block in frame: {', '.join(str(p['year']) for p in picks)}")
    recs = []
    for a in picks:
        fn = f"old_{a['year']}_{a['objectid']}.jpg"
        rec = {"id": a["objectid"], "year": a["year"], "frame": a["framename"], "date": dt(a["begindate"]).strftime("%Y-%m-%d"),
               "scan_res_m": a.get("resolution"), "credit": a.get("attribution"), "file": fn, "partial": a["hits"] < 5}
        if not (out / fn).exists():
            print(f"  {a['year']} {a['framename']}")
            data = get("/exportImage", {"bbox": f"{cx-WIN/2},{cy-WIN/2},{cx+WIN/2},{cy+WIN/2}", "bboxSR": 7856, "imageSR": 7856, "size": f"{PX},{PX}",
                                        "format": "jpg", "compressionQuality": 88, "noData": 0,
                                        "mosaicRule": json.dumps({"mosaicMethod": "esriMosaicLockRaster", "lockRasterIds": [a["objectid"]]}), "f": "image"}, img=True)
            if not data: continue
            (out / fn).write_bytes(data); time.sleep(1.5)
        recs.append(rec)
        (out / "old_photos.json").write_text(json.dumps({"site": site, "centre_mga56": [cx, cy], "size_m": WIN, "epsg": 7856,
            "source": "State of Queensland, QImagery historical aerial photography", "runs": recs}, indent=1))
    print(f"\nDone: {len(recs)} old photos in {out}. Tell Claude the old photos are downloaded.")

if __name__ == "__main__":
    main()

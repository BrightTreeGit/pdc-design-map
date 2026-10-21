#!/usr/bin/env python3
"""
fetch_history.py: download every historical aerial photo run the Queensland Government holds over a site,
as north-up images lined up with the PDC design map, for the map's history slider.

Source: Queensland Government "TimeSeries / AerialOrtho" imagery service, orthorectified aerial photo projects
1930s to about three years ago (CC BY 4.0, State of Queensland). Coverage varies by place: some years cover
only part of a site, and the oldest are black and white.

Usage (Windows, from this folder):  double-click get_history.bat
   or:  py fetch_history.py bright-tree
Output: a "history" folder with one JPG per photo run (history_<year>_<id>.jpg) and history.json listing
the year, capture dates, resolution and how much of the site each one covers. Tell Claude when it's done.
Gentle on the servers: one request at a time, a second apart, with retries.
"""
import sys, json, time, datetime
from pathlib import Path
import requests

SVC = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/TimeSeries/AerialOrtho_AllUsers/ImageServer"
HEADERS = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
# site: (centre easting, centre northing, square size in metres) in MGA zone 56
SITES = {
    "bright-tree": (492921, 7041970, 1000),
    "bellbunya": (485272, 7069910, 1200),
    "noosa-forest-retreat": (484394, 7095927, 1000),
}
RES = 0.5  # metres per pixel in the output

def get(url, params, binary=False, what="request"):
    for wait in (0, 5, 20, 60):
        if wait:
            print(f"   retrying {what} in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=180)
        except Exception as e:
            print(f"   {what} failed: {e}"); continue
        if not r.ok:
            print(f"   {what}: status {r.status_code}"); continue
        if binary:
            if r.headers.get("content-type", "").startswith("image"):
                return r.content
            print(f"   {what}: not an image: {r.text[:150]!r}"); continue
        try:
            j = r.json()
        except Exception:
            print(f"   {what}: not JSON"); continue
        if isinstance(j, dict) and j.get("error"):
            print(f"   {what}: server error {j['error']}"); continue
        return j
    return None

def day(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).strftime("%Y-%m-%d") if ms else None

def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "bright-tree"
    if site not in SITES:
        sys.exit(f"Unknown site {site}. Presets: {', '.join(SITES)}")
    cx, cy, size = SITES[site]
    x0, x1, y0, y1 = cx - size / 2, cx + size / 2, cy - size / 2, cy + size / 2
    out = Path(__file__).resolve().parent / "history"; out.mkdir(exist_ok=True)
    print(f"Finding photo runs over {site} ({size} m square)")
    items, sr_used = None, None
    for sr in (7856, 28356):
        env = json.dumps({"xmin": x0, "ymin": y0, "xmax": x1, "ymax": y1, "spatialReference": {"wkid": sr}})
        j = get(SVC + "/query", {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": sr, "spatialRel": "esriSpatialRelIntersects",
                                 "outFields": "objectid,name,year,capturestart,captureend,res_value,product_type", "returnGeometry": "false", "f": "json"}, what="catalogue")
        if j and j.get("features") is not None:
            items = [f["attributes"] for f in j["features"]]; sr_used = sr; break
    if not items:
        sys.exit("The imagery catalogue did not answer. Try again later.")
    items.sort(key=lambda a: (a.get("year") or 0, a.get("res_value") or 99))
    print(f"  {len(items)} photo runs found, {min(a.get('year') or 9999 for a in items)} to {max(a.get('year') or 0 for a in items)}")
    px = int(size / RES)
    done = []
    old = {}
    if (out / "history.json").exists():
        try:
            old = {d["id"]: d for d in json.loads((out / "history.json").read_text())["runs"]}
        except Exception:
            old = {}
    for a in items:
        oid = a["objectid"]; yr = a.get("year") or 0
        fn = f"history_{yr}_{oid}.jpg"
        rec = {"id": oid, "year": yr, "name": a.get("name"), "from": day(a.get("capturestart")), "to": day(a.get("captureend")),
               "res_m": a.get("res_value"), "type": a.get("product_type"), "file": fn}
        if (out / fn).exists() and oid in old:
            done.append(old[oid]); print(f"  {yr} {a.get('name')}: already downloaded"); continue
        print(f"  {yr} {a.get('name')} ({a.get('res_value')} m)")
        data = get(SVC + "/exportImage", {"bbox": f"{x0},{y0},{x1},{y1}", "bboxSR": sr_used, "imageSR": sr_used, "size": f"{px},{px}",
                                          "format": "jpg", "compressionQuality": 85, "noData": 0, "interpolation": "RSP_BilinearInterpolation",
                                          "mosaicRule": json.dumps({"mosaicMethod": "esriMosaicLockRaster", "lockRasterIds": [oid]}), "f": "image"},
                   binary=True, what=f"image {yr}")
        if not data:
            continue
        (out / fn).write_bytes(data)
        try:
            from PIL import Image
            im = Image.open(out / fn).convert("L")
            hist = im.histogram()
            cover = 1 - (hist[0] + hist[1] + hist[2]) / (im.width * im.height)
            rec["cover"] = round(cover, 2)
            if cover < 0.05:
                (out / fn).unlink(); print("    no real coverage here, skipped"); continue
        except ImportError:
            pass
        done.append(rec)
        (out / "history.json").write_text(json.dumps({"site": site, "centre_mga56": [cx, cy], "size_m": size, "res_m": RES, "epsg": sr_used,
                                                      "source": "State of Queensland, TimeSeries AerialOrtho (CC BY 4.0)", "runs": done}, indent=1))
        time.sleep(1)
    print(f"\nDone: {len(done)} photo runs saved in {out}. Tell Claude the history photos are ready.")

if __name__ == "__main__":
    main()

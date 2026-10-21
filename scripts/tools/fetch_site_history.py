#!/usr/bin/env python3
"""
fetch_site_history.py <site>: one-click photo history for a Queensland PDC site.

1. Government orthophotos (lined up exactly), every year the state holds, 1994-ish to recent.
2. Scanned historical film photos back to the 1950s: the best frame per year that covers the block,
   as a wide 5 km square so Claude can pin each one onto the block by matching landmarks.
3. Two modern reference photos of the same 5 km square, used for that matching.

Output goes into the site's own folder:  <Site>\\Aerial and Google Maps\\history  and  ...\\old_photos
Re-running only downloads what's missing. One request at a time, gently.
Sources: State of Queensland TimeSeries AerialOrtho and QImagery historical aerial photography (CC BY 4.0 / public domain).
"""
import sys, json, time, datetime
from pathlib import Path
import requests

ORTHO = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/TimeSeries/AerialOrtho_AllUsers/ImageServer"
ARCH = "https://qimagery.information.qld.gov.au/proxy?https://spatial-img.information.qld.gov.au/arcgis/rest/services/QImagery/QldArchive_AerialPhotos/ImageServer"
H = {"User-Agent": "Mozilla/5.0 (PDC-Design-Map; permaculture course)", "Referer": "https://qimagery.information.qld.gov.au/"}
# site: folder, lot centre (MGA zone 56, GDA2020), lot span (m), ortho window (m)
SITES = {
    "bright-tree": ("Bright Tree", 492921, 7041970, 420, 1000),
    "bellbunya": ("Bellbunya", 485272, 7069910, 646, 1200),
    "noosa-forest-retreat": ("Noosa Forest Retreat", 484394, 7095927, 470, 1000),
}
PX = 2000          # ortho output pixels
WIDE, WPX = 5000, 4000   # old-photo wide window (m) and pixels (server limit 4100)
EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
def day(ms): return (EPOCH + datetime.timedelta(milliseconds=ms)).strftime("%Y-%m-%d") if ms else None
def year(ms): return (EPOCH + datetime.timedelta(milliseconds=ms)).year if ms else 0

def get(base, path, params, img=False):
    for w in (0, 5, 20, 60):
        if w: print(f"   retry in {w}s"); time.sleep(w)
        try:
            r = requests.get(base + path + "?" + requests.compat.urlencode(params), headers=H, timeout=300)
            if r.status_code != 200: print("   status", r.status_code); continue
            if img:
                if r.content[:3] == b"\xff\xd8\xff": return r.content
                print("   not an image:", r.text[:150]); continue
            j = r.json()
            if "error" in j: print("   server error", j["error"]); continue
            return j
        except Exception as e:
            print("   failed:", e)
    return None

def export(base, oid, bbox, px, fn):
    if fn.exists() and fn.stat().st_size > 5000: return True
    data = get(base, "/exportImage", {"bbox": ",".join(map(str, bbox)), "bboxSR": 7856, "imageSR": 7856, "size": f"{px},{px}",
                                      "format": "jpg", "compressionQuality": 85, "noData": 0,
                                      "mosaicRule": json.dumps({"mosaicMethod": "esriMosaicLockRaster", "lockRasterIds": [oid]}), "f": "image"}, img=True)
    if data: fn.write_bytes(data); time.sleep(1.2); return True
    return False

def main():
    site = sys.argv[1] if len(sys.argv) > 1 else ""
    if site not in SITES: sys.exit("Usage: fetch_site_history.py <site>   sites: " + ", ".join(SITES))
    folder, cx, cy, span, win = SITES[site]
    root = Path(__file__).resolve().parents[1] / folder / "Aerial and Google Maps"
    if not root.parent.exists(): sys.exit(f"Can't find the {folder} folder next to _tools")
    hist = root / "history"; old = root / "old_photos"; wide = old / "wide"
    for d in (hist, old, wide): d.mkdir(parents=True, exist_ok=True)

    # 1. orthophotos
    print(f"\n[1/3] Government orthophotos over {folder}")
    bb = (cx - win / 2, cy - win / 2, cx + win / 2, cy + win / 2)
    env = json.dumps({"xmin": bb[0], "ymin": bb[1], "xmax": bb[2], "ymax": bb[3], "spatialReference": {"wkid": 7856}})
    j = get(ORTHO, "/query", {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 7856, "spatialRel": "esriSpatialRelIntersects",
                              "outFields": "*", "returnGeometry": "false", "f": "json"})
    runs = sorted([{k.lower(): v for k, v in f["attributes"].items()} for f in (j or {}).get("features", [])], key=lambda a: (a.get("year") or 0))
    print(f"  {len(runs)} photo runs found")
    recs = []
    for a in runs:
        fn = hist / f"history_{a.get('year')}_{a['objectid']}.jpg"
        print(f"  {a.get('year')} {a.get('name')}")
        if not export(ORTHO, a["objectid"], bb, PX, fn): continue
        try:
            from PIL import Image
            im = Image.open(fn).convert("L"); h = im.histogram(); cover = 1 - sum(h[:3]) / (im.width * im.height)
            if cover < 0.05: fn.unlink(); print("    no real coverage, skipped"); continue
        except ImportError:
            cover = None
        recs.append({"id": a["objectid"], "year": a.get("year"), "name": a.get("name"), "from": day(a.get("capturestart")), "to": day(a.get("captureend")),
                     "res_m": a.get("res_value"), "file": fn.name, "cover": cover})
    (hist / "history.json").write_text(json.dumps({"site": site, "centre_mga56": [cx, cy], "size_m": win, "res_m": win / PX, "epsg": 7856,
        "source": "State of Queensland, TimeSeries AerialOrtho (CC BY 4.0)", "runs": recs}, indent=1))

    # 2. historical frames
    print(f"\n[2/3] Historical film photos over {folder}")
    h = span / 2
    pts = [(cx, cy), (cx - h, cy - h), (cx + h, cy + h), (cx - h, cy + h), (cx + h, cy - h)]
    frames = {}
    for x, y in pts:
        j = get(ARCH, "/query", {"geometry": f"{x},{y}", "geometryType": "esriGeometryPoint", "inSR": 7856, "spatialRel": "esriSpatialRelIntersects",
                                 "outFields": "objectid,framename,begindate,resolution,attribution", "returnGeometry": "false", "f": "json"})
        for f in (j or {}).get("features", []):
            a = f["attributes"]; frames.setdefault(a["objectid"], dict(a, hits=0))["hits"] += 1
        time.sleep(1)
    by = {}
    for a in frames.values(): by.setdefault(year(a.get("begindate")), []).append(a)
    picks = [sorted(v, key=lambda a: (-a["hits"], float(a.get("resolution") or 9)))[0] for y, v in sorted(by.items())]
    picks = [p for p in picks if p["hits"] >= 3]
    print(f"  {len(picks)} years with the block in frame: {', '.join(str(year(p['begindate'])) for p in picks)}")
    wb = (cx - WIDE / 2, cy - WIDE / 2, cx + WIDE / 2, cy + WIDE / 2)
    orecs = []
    for a in picks:
        y = year(a["begindate"]); fn = wide / f"wide_{y}_{a['objectid']}.jpg"
        print(f"  {y} {a['framename']}")
        if export(ARCH, a["objectid"], wb, WPX, fn):
            orecs.append({"id": a["objectid"], "year": y, "frame": a["framename"], "date": day(a["begindate"]), "scan_res_m": a.get("resolution"),
                          "credit": a.get("attribution"), "file": "wide/" + fn.name, "partial": a["hits"] < 5})
    (old / "old_photos.json").write_text(json.dumps({"site": site, "centre_mga56": [cx, cy], "wide_m": WIDE, "wide_px": WPX, "epsg": 7856,
        "source": "State of Queensland, QImagery historical aerial photography", "runs": orecs}, indent=1))

    # 3. reference photos for matching (earliest ortho and one around 2008)
    print(f"\n[3/3] Reference photos for lining up the old ones")
    if recs:
        refs = {recs[0]["year"]: recs[0]["id"]}
        mid = min(recs, key=lambda r: abs((r["year"] or 0) - 2008)); refs[mid["year"]] = mid["id"]
        for y, oid in refs.items():
            print(f"  {y}"); export(ORTHO, oid, wb, WPX, wide / f"ref_{y}_{oid}.jpg")
    print(f"\nDone: {len(recs)} orthophotos and {len(orecs)} old photos for {folder}. Tell Claude the {folder} photo history is ready.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
find_old_photos.py: lists every pre-1994 historical aerial photo frame the Queensland Government holds over a site.
These are scanned film frames from the 1930s on. They are not lined up to the map, and each frame covers several km,
so even partial coverage of the property counts.
Writes old_photos/frames.csv (the list, oldest first) and old_photos/services.txt (what image services are available),
then tries to download a preview of each frame. Run: double-click find_old_photos_<site>.bat
"""
import sys, json, csv, time
from pathlib import Path
import requests

H = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
FOOT = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Imagery/ImageryFootprint/MapServer"
IMG = "https://spatial-img.information.qld.gov.au/arcgis/rest/services"
SITES = {"bright-tree": (492921, 7041970), "bellbunya": (485272, 7069910), "noosa-forest-retreat": (484394, 7095927)}
SEARCH_M = 4000  # frame centres within 4 km can still show the property (a 1:25,000 frame is about 5.7 km wide)

def getj(url, params=None):
    for w in (0, 5, 20):
        if w: time.sleep(w)
        try:
            r = requests.get(url, params=dict(params or {}, f="json"), headers=H, timeout=120)
            j = r.json()
            if "error" not in j: return j
            print("  server error:", j["error"])
        except Exception as e:
            print("  failed:", e)
    return None

def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "bright-tree"
    cx, cy = SITES[site]
    out = Path(__file__).resolve().parent / "old_photos"; out.mkdir(exist_ok=True)
    log = []
    # 1. what image services exist (looking for a historical frames service)
    for folder in ("QImagery", "Basemaps", "TimeSeries", "QldGlobe"):
        j = getj(f"{IMG}/{folder}")
        if j:
            for s in j.get("services", []):
                log.append(f"{s['name']} ({s['type']})")
                if "ImageServer" in s["type"] and any(k in s["name"].lower() for k in ("hist", "frame", "earliest")):
                    info = getj(f"{IMG}/{s['name']}/ImageServer")
                    if info: log.append("   fields: " + ", ".join(f["name"] for f in info.get("fields", [])))
    # earliest ortho at the site
    e = getj(f"{IMG}/Basemaps/EarliestAerialOrtho_AllUsers/ImageServer/identify",
             {"geometry": json.dumps({"x": cx, "y": cy, "spatialReference": {"wkid": 28356}}), "geometryType": "esriGeometryPoint", "returnCatalogItems": "true"})
    if e: log.append("Earliest ortho at site: " + json.dumps([f.get("attributes") for f in (e.get("catalogItems") or {}).get("features", [])])[:1500])
    (out / "services.txt").write_text("\n".join(log))
    # 2. historical frames near the site
    layers = getj(f"{FOOT}/layers") or {"layers": []}
    lid = next((l["id"] for l in layers["layers"] if "frame" in l["name"].lower() and "histor" in l["name"].lower()), None)
    if lid is None:
        sys.exit("Couldn't find the historical frames layer. Send Claude old_photos/services.txt")
    env = json.dumps({"xmin": cx - SEARCH_M, "ymin": cy - SEARCH_M, "xmax": cx + SEARCH_M, "ymax": cy + SEARCH_M, "spatialReference": {"wkid": 28356}})
    rows, off = [], 0
    while True:
        j = getj(f"{FOOT}/{lid}/query", {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 28356, "outSR": 28356,
                                         "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "true",
                                         "resultOffset": off, "resultRecordCount": 1000})
        if not j: break
        for f in j.get("features", []):
            a = {k.lower(): v for k, v in f["attributes"].items()}
            g = f.get("geometry") or {}
            a["centre_e"], a["centre_n"] = g.get("x"), g.get("y")
            if a["centre_e"]:
                a["dist_m"] = round(((a["centre_e"] - cx) ** 2 + (a["centre_n"] - cy) ** 2) ** 0.5)
            rows.append(a)
        if not j.get("exceededTransferLimit"): break
        off += 1000
    if not rows:
        sys.exit("No historical frames found near the site.")
    def yr(a):
        s = str(a.get("capture_date") or "")
        digits = [s[i:i + 4] for i in range(len(s) - 3) if s[i:i + 4].isdigit() and s[i:i + 2] in ("19", "20")]
        return digits[0] if digits else "?"
    for a in rows: a["year"] = yr(a)
    rows.sort(key=lambda a: (a["year"], a.get("dist_m") or 9e9))
    keys = ["year", "capture_date", "project_name", "film_id", "run", "frame_id", "scale", "film_type", "dist_m", "centre_e", "centre_n", "rotation", "coverage", "licence"]
    keys += [k for k in rows[0] if k not in keys and k != "shape"]
    with open(out / "frames.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    years = {}
    for a in rows: years.setdefault(a["year"], []).append(a)
    print(f"\n{len(rows)} historical frames within {SEARCH_M/1000:.0f} km of {site}:")
    for y in sorted(years):
        best = min(years[y], key=lambda a: a.get("dist_m") or 9e9)
        print(f"  {y}: {len(years[y]):3d} frames, closest {best.get('dist_m')} m away, scale 1:{best.get('scale')}, {best.get('film_type') or ''}")
    print(f"\nSaved {out / 'frames.csv'}. Tell Claude the old photo list is ready.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
fetch_qld_site.py: site pack for a new Queensland block, straight from public Queensland Government
services and SILO (CC BY 4.0), so Claude can build its design map.

  boundary.geojson   the lot outline from the Queensland cadastre (found by address, lot on plan or a point)
  dem_<service>.tif  the finest Queensland elevation model available for a 2 km window around the block
                     (1 m LiDAR where the state service has it; otherwise the coarser statewide model)
  aerial.jpg         latest Queensland aerial photo for the same window (0.5 m)
  silo_daily.json    30 years of daily rain and minimum temperature at the block (SILO gridded)
  window.json        the window corners, so everything lines up
  private_notes.md   lot on plan and address: KEEP PRIVATE, never shared

Usage (Windows, from the _tools folder): double-click "<Site> - get site data.bat", or
  py fetch_qld_site.py annwn --folder Annwn --address "26 CHURCHILL STREET CAPALABA"
  py fetch_qld_site.py annwn --folder Annwn --lotplan 12RP123456
  py fetch_qld_site.py annwn --folder Annwn --pin -27.5432,153.1987
Gentle on the servers: a few requests, two seconds apart, with retries.
"""
import argparse, json, math, os, sys, time
from pathlib import Path
import requests

LPPF = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer"
ELEV = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/Elevation"
IMG = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/Basemaps/LatestStateProgram_AllUsers/ImageServer/exportImage"
SILO = "https://www.longpaddock.qld.gov.au/cgi-bin/silo/DataDrillDataset.php"
EMAIL = os.environ.get("SILO_EMAIL", "brighttreewellness@gmail.com")   # SILO asks for a contact email
H = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
SIZE = 2000   # window (m)


def get(url, params, what, binary=False):
    for wait in (0, 10, 30, 60):
        if wait:
            print(f"  retrying {what} in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=H, timeout=180)
        except Exception as e:
            print(f"  {what}: request failed: {e}"); continue
        if not r.ok:
            print(f"  {what}: status {r.status_code}: {r.text[:160]!r}"); continue
        if binary:
            if r.headers.get("content-type", "").startswith(("image", "application/octet")) or r.content[:2] in (b"II", b"MM"):
                time.sleep(2); return r.content
            print(f"  {what}: not an image: {r.text[:160]!r}"); continue
        try:
            j = r.json()
        except Exception:
            print(f"  {what}: not JSON: {r.text[:160]!r}"); continue
        if isinstance(j, dict) and j.get("error"):
            print(f"  {what}: server error {j['error']}"); continue
        time.sleep(2); return j
    return None


# ---- GRS80 / MGA (Krueger series)
_a = 6378137.0; _f = 1 / 298.257222101; _k0 = 0.9996
_n = _f / (2 - _f); _A = _a / (1 + _n) * (1 + _n**2 / 4 + _n**4 / 64)
_al = [_n/2 - 2*_n**2/3 + 5*_n**3/16, 13*_n**2/48 - 3*_n**3/5, 61*_n**3/240]
_e = math.sqrt(_f * (2 - _f))
def ll2mga(lon, lat, zone=56):
    lon = math.radians(lon); lat = math.radians(lat); l0 = math.radians(zone * 6 - 183)
    t = math.sinh(math.atanh(math.sin(lat)) - _e * math.atanh(_e * math.sin(lat))); dl = lon - l0
    xi = math.atan2(t, math.cos(dl)); eta = math.atanh(math.sin(dl) / math.sqrt(1 + t * t))
    X = xi + sum(_al[j] * math.sin(2*(j+1)*xi) * math.cosh(2*(j+1)*eta) for j in range(3))
    Y = eta + sum(_al[j] * math.cos(2*(j+1)*xi) * math.sinh(2*(j+1)*eta) for j in range(3))
    return 500000 + _k0 * _A * Y, 10000000 + _k0 * _A * X


def layers():
    j = get(LPPF, {"f": "json"}, "cadastre service") or {}
    L = {l["name"].lower(): l["id"] for l in j.get("layers", [])}
    addr = next((i for n, i in L.items() if "address" in n), None)
    parcel = next((i for n, i in L.items() if "cadastral parcel" in n), None) or next((i for n, i in L.items() if "parcel" in n), None)
    print(f"  cadastre layers: addresses={addr}, parcels={parcel}")
    return addr, parcel


def lotplan_from_address(addr_layer, address):
    j = get(LPPF + "/find", {"searchText": address.upper(), "contains": "true", "layers": str(addr_layer), "returnGeometry": "false", "f": "json"}, "address search")
    for r in (j or {}).get("results", []):
        a = {k.lower(): v for k, v in r.get("attributes", {}).items()}
        lp = a.get("lotplan") or ((a.get("lot") or "") + (a.get("plan") or ""))
        if lp:
            print(f"  address matched: {r.get('value')}"); return lp
    return None


def parcel(parcel_layer, lotplan=None, pin=None):
    p = {"outFields": "*", "returnGeometry": "true", "outSR": "4326", "f": "geojson"}
    if lotplan:
        p["where"] = f"lotplan='{lotplan.upper()}'"
    else:
        lat, lon = pin
        p.update({"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "where": "1=1"})
    j = get(f"{LPPF}/{parcel_layer}/query", p, "lot outline")
    return (j or {}).get("features", [])


def elevation_services():
    j = get(ELEV, {"f": "json"}, "elevation services") or {}
    out = []
    for s in j.get("services", []):
        if s.get("type") != "ImageServer": continue
        url = f"https://spatial-img.information.qld.gov.au/arcgis/rest/services/{s['name']}/ImageServer"
        info = get(url, {"f": "json"}, s["name"]) or {}
        px = info.get("pixelSizeX")
        if px: out.append((float(px), s["name"].split("/")[-1], url))
    out.sort()
    print("  elevation models: " + ", ".join(f"{n} ({p:g} m)" for p, n, _ in out))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site"); ap.add_argument("--folder", required=True, help="the site's folder next to _tools")
    ap.add_argument("--address"); ap.add_argument("--lotplan"); ap.add_argument("--pin", help="lat,lon of a point inside the lot")
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[1] / a.folder
    out = root / "Site data"; out.mkdir(parents=True, exist_ok=True)
    print(f"Site pack for {a.folder} -> {out}")

    print("1/4 Finding the lot in the Queensland cadastre")
    addr_l, parcel_l = layers()
    lp = a.lotplan or (lotplan_from_address(addr_l, a.address) if a.address and addr_l is not None else None)
    feats = parcel(parcel_l, lotplan=lp) if lp else (parcel(parcel_l, pin=[float(v) for v in a.pin.split(",")]) if a.pin else [])
    if not feats:
        sys.exit("  Couldn't find the lot. Try again with --pin <lat,lon> of a point inside the block (right-click it in Google Maps to copy one).")
    (out / "boundary.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    pts = [c for f in feats for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]) for c in poly[0]]
    clon = sum(p[0] for p in pts) / len(pts); clat = sum(p[1] for p in pts) / len(pts)
    zone = int((clon + 180) // 6) + 1
    cx, cy = ll2mga(clon, clat, zone)
    E0, N0 = round(cx - SIZE / 2), round(cy + SIZE / 2)
    win = {"zone": zone, "E0": E0, "N0": N0, "size": SIZE, "centre_lon": clon, "centre_lat": clat, "epsg": 7800 + zone}
    (out / "window.json").write_text(json.dumps(win, indent=1))
    attrs = feats[0].get("properties", {})
    (out / "private_notes.md").write_text(f"# {a.folder} (PRIVATE: do not share)\n\nAddress searched: {a.address or '-'}\nLot on plan: {lp or attrs.get('lotplan', '-')}\nArea (cadastre): {attrs.get('lot_area', attrs.get('shape_area', '?'))}\n")
    print(f"  found {len(feats)} parcel(s); window MGA{zone} E{E0} N{N0}")
    bbox = f"{E0},{N0 - SIZE},{E0 + SIZE},{N0}"

    print("2/4 Downloading elevation")
    got = False
    for px, name, url in elevation_services():
        if px > 30: continue
        n = min(4000, int(SIZE / max(px, 1)))
        data = get(url + "/exportImage", {"bbox": bbox, "bboxSR": win["epsg"], "imageSR": win["epsg"], "size": f"{n},{n}", "format": "tiff", "pixelType": "F32", "noDataInterpretation": "esriNoDataMatchAny", "interpolation": "RSP_BilinearInterpolation", "f": "image"}, f"elevation {name}", binary=True)
        if data and len(data) > 50000:
            (out / f"dem_{name}.tif").write_bytes(data); print(f"  saved dem_{name}.tif ({px:g} m model, {len(data)//1024} kB)"); got = True
            if px <= 2: break
    if not got:
        print("  No elevation came back (the state image server may be down). Run this again later, or download 1 m LiDAR from ELVIS.")

    print("3/4 Downloading the latest aerial photo")
    tiles = []
    for r in range(2):
        for c in range(2):
            b = f"{E0 + c*1000},{N0 - (r+1)*1000},{E0 + (c+1)*1000},{N0 - r*1000}"
            d = get(IMG, {"bbox": b, "bboxSR": win["epsg"], "imageSR": win["epsg"], "size": "2000,2000", "format": "jpg", "compression": "JPEG", "compressionQuality": 85, "f": "image"}, f"aerial tile {r}{c}", binary=True)
            if d: (out / f"aerial_r{r}c{c}.jpg").write_bytes(d); tiles.append((r, c))
    try:
        from PIL import Image
        if len(tiles) == 4:
            im = Image.new("RGB", (4000, 4000))
            for r, c in tiles: im.paste(Image.open(out / f"aerial_r{r}c{c}.jpg").convert("RGB"), (c * 2000, r * 2000))
            im.save(out / "aerial.jpg", quality=85); print("  saved aerial.jpg")
    except ImportError:
        print("  Pillow not installed: kept the four aerial tiles (Claude can stitch them)")

    print("4/4 Downloading 30 years of rainfall (SILO)")
    j = get(SILO, {"lat": round(clat, 4), "lon": round(clon, 4), "start": "19950101", "finish": "20251231", "format": "json", "comment": "RN", "username": EMAIL}, "SILO")
    if j: (out / "silo_daily.json").write_text(json.dumps(j)); print("  saved silo_daily.json")
    print(f"\nDone. Tell Claude: \"{a.folder} site data is ready\".")


if __name__ == "__main__":
    main()

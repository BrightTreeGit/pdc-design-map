#!/usr/bin/env python3
"""
fetch_nsw_site.py: stop-gap site pack for NSW properties while the ELVIS / 1 m LiDAR downloads are unreliable.

Pulls, straight from NSW Spatial Services and SILO (all public, CC BY 4.0):
  boundary.geojson   the property outline (all its lots) from the NSW property register
  dem_5m.tif         5 m statewide elevation (NSW_5M_Elevation), for a square window around the property
  aerial_<name>.jpg  NSW Imagery for the same window (needs Pillow to stitch; tiles kept otherwise)
  silo_daily.json    30 years of daily rain and min temperature at the property (SILO gridded)
  window.json        the window corners, so Claude can line everything up
  private_notes.md   lot ids and address (keep private)

Usage (Windows, from this folder): double-click the matching .bat, or
  py fetch_nsw_site.py nimbin --address "312 GUNGAS ROAD NIMBIN"
  py fetch_nsw_site.py willow-vale --lotdp "12//DP123456"
  py fetch_nsw_site.py willow-vale --pin -32.12345,151.98765        (a point inside the property)
Gentle on the servers: a handful of requests, two seconds apart, with retries.
"""
import argparse, json, math, os, sys, time
from pathlib import Path
import requests

SIX = "https://maps.six.nsw.gov.au/arcgis/rest/services/public"
PROP = SIX + "/NSW_Property/MapServer/{layer}/query"        # 1 large rural, 2 rural, 3 semi-rural, 4 urban; 5 = PropertyLot table
LOT = SIX + "/NSW_Cadastre/MapServer/9/query"               # Lot polygons
DEM = SIX + "/NSW_5M_Elevation/ImageServer/exportImage"
IMG = SIX + "/NSW_Imagery/MapServer/export"
TILE = SIX + "/NSW_Imagery/MapServer/tile/{z}/{y}/{x}"
DATES = SIX + "/NSW_Imagery_Dates/MapServer/0/query"         # capture date of the current NSW imagery
SILO = "https://www.longpaddock.qld.gov.au/cgi-bin/silo/DataDrillDataset.php"
HEADERS = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
EMAIL = os.environ.get("SILO_EMAIL", "brighttreewellness@gmail.com")

def get(url, params, what, binary=False):
    for wait in (0, 10, 30):
        if wait:
            print(f"  retrying {what} in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=180)
        except Exception as e:
            print(f"  {what}: request failed: {e}"); continue
        if not r.ok:
            print(f"  {what}: status {r.status_code}: {r.text[:200]!r}"); continue
        if binary:
            if r.headers.get("content-type", "").startswith(("image", "application/octet")) or r.content[:2] in (b"II", b"MM"):
                return r.content
            print(f"  {what}: not an image: {r.text[:200]!r}"); continue
        try:
            j = r.json()
        except Exception:
            print(f"  {what}: not JSON: {r.text[:200]!r}"); continue
        if isinstance(j, dict) and j.get("error"):
            print(f"  {what}: server error {j['error']}"); continue
        time.sleep(2)
        return j
    return None

# ---- GRS80 / MGA (Krueger series), good to millimetres
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


# ---- Plus Codes (Open Location Code, open standard) and free geocoding, so a Google-style address or a Plus Code works
_OLC = "23456789CFGHJMPQRVWX"
def _olc_encode(lat, lng):
    lat += 90; lng += 180; s = ""; r = 20.0
    for _ in range(5):
        dl = int(lat // r); dg = int(lng // r); s += _OLC[dl] + _OLC[dg]; lat -= dl * r; lng -= dg * r; r /= 20
    return s
def _olc_decode(code):
    c = code.replace("+", "").upper(); lat = lng = 0.0; r = 20.0
    for i in range(0, 10, 2):
        lat += _OLC.index(c[i]) * r; lng += _OLC.index(c[i + 1]) * r; r /= 20
    r *= 20
    return lat - 90 + r / 2, lng - 180 + r / 2

def geocode(text):
    """Free address lookup (OpenStreetMap Nominatim; no key; one request). Returns (lat, lon, label) or None."""
    j = None
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search", params={"q": text, "format": "json", "limit": 1, "countrycodes": "au"},
                         headers={"User-Agent": "PDC-Design-Map/1.0 (permaculture course; brighttreewellness@gmail.com)"}, timeout=60)
        j = r.json() if r.ok else None
    except Exception as e:
        print(f"  address lookup failed: {e}")
    time.sleep(1.1)
    if j: return float(j[0]["lat"]), float(j[0]["lon"]), j[0].get("display_name", "")
    return None

def pluscode_to_latlon(text):
    """'HW9Q+JM Mongarlowe' (short code + place) or '4RPFHW9Q+JM' (full code)."""
    parts = text.strip().split(None, 1); code = parts[0].upper()
    if len(code.replace("+", "")) >= 10: return _olc_decode(code)
    if len(parts) < 2: sys.exit("A short Plus Code needs the place after it, e.g. 'HW9Q+JM Mongarlowe NSW'")
    ref = geocode(parts[1] + ", Australia")
    if not ref: sys.exit(f"Couldn't find the place '{parts[1]}' to complete the Plus Code; use the full code or --pin")
    short = code.replace("+", "")
    full = _olc_encode(ref[0], ref[1])[:10 - len(short)] + short
    lat, lng = _olc_decode(full)
    # pick the neighbouring 1-degree cell if that brings the point nearer the place (the standard 'recover nearest' rule)
    best = (abs(lat - ref[0]) + abs(lng - ref[1]), lat, lng)
    for dla in (-1, 0, 1):
        for dlo in (-1, 0, 1):
            c = (abs(lat + dla - ref[0]) + abs(lng + dlo - ref[1]), lat + dla, lng + dlo)
            if c[0] < best[0]: best = c
    return best[1], best[2]

def find_property(a):
    """Exact address first; if the register spells the road or locality differently, retry with looser matches
    (number + road, then road + locality, then road alone) and say which one matched."""
    if a.pin and not a.propid:
        # a point wins; the address (if given) is only a hint to check the right block was found
        feats = _find_property_where(None, a)
        want = a.address.split()[0] if a.address else None
        if feats and want and want[:1].isdigit():
            got = str(feats[0]["properties"].get("address", "")).split()[:1]
            if got != [want]:
                print(f"  the point is inside {feats[0]['properties'].get('address')}, not number {want}; looking at the properties around it")
                near = nearby_properties(a)
                if near and str(near[0]["properties"].get("address", "")).split()[:1] == [want]: return near
                print("  keeping the property under the point")
        return feats
    if a.address and not a.propid:
        words = a.address.upper().replace("'", "''").split()
        num = words[0] if words and words[0][:1].isdigit() else None
        rest = words[1:] if num else words
        road_i = next((i for i, w in enumerate(rest) if w in ("ROAD", "RD", "STREET", "ST", "LANE", "LN", "DRIVE", "DR", "WAY", "AVENUE", "AVE", "CIRCUIT", "CCT", "BOULEVARD", "BLVD", "PLACE", "PL", "COURT", "CT", "CLOSE", "TRACK", "TRAIL")), None)
        road = " ".join(rest[:road_i + 1]) if road_i is not None else " ".join(rest[:2])
        name = rest[0] if rest else ""
        tries = [" ".join(words) + "%"]
        if num and road: tries.append(f"{num} {road}%")
        if num and name: tries.append(f"{num} {name}%")          # road type spelt differently (RD vs ROAD)
        if road: tries.append(f"%{road}%")
        for i, pat in enumerate(tries):
            feats = _find_property_where(f"address LIKE '{pat}'")
            if feats:
                if i: print(f"  matched the register with '{pat.strip('%')}' (the full address is spelt differently there)")
                if len(feats) > 1 and not num:
                    print("  several properties on that road; rerun with --pin lat,lon of a point inside the block")
                return feats
            print(f"  no match for '{pat.strip('%')}'")
        g = geocode(a.address + ", NSW, Australia")
        if g:
            print(f"  the register has no match, but the address lookup found it at {g[0]:.6f},{g[1]:.6f} ({g[2][:80]}); using the property at that point")
            a.pin = f"{g[0]},{g[1]}"
            return _find_property_where(None, a)
        return []
    return _find_property_where(None, a)


def _find_property_where(where, a=None):
    q = {"outFields": "propid,address,housenumber", "returnGeometry": "true", "outSR": "4326", "f": "geojson"}
    if where is None and a is not None and a.propid:
        where = f"propid={int(a.propid)}"
    feats = []
    for layer in (1, 2, 3, 4):
        p = dict(q)
        if where:
            p["where"] = where
        else:
            lat, lon = [float(v) for v in a.pin.split(",")]
            p.update({"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "where": "1=1"})
        j = get(PROP.format(layer=layer), p, f"property layer {layer}")
        if j is None:   # older servers: fall back to Esri JSON and convert the rings
            p["f"] = "json"; jj = get(PROP.format(layer=layer), p, f"property layer {layer} (json)")
            j = {"features": [{"type": "Feature", "properties": f.get("attributes", {}), "geometry": {"type": "MultiPolygon", "coordinates": [[r] for r in f["geometry"]["rings"]]}} for f in (jj or {}).get("features", []) if f.get("geometry")]}
        if j and j.get("features"):
            feats += j["features"]
    return feats

def nearby_properties(a, radius_m=300):
    """The point missed every property (Google often puts an address's Plus Code on the road). List the properties within
    radius_m of it and pick: the one whose house number matches --address if given, else the nearest."""
    lat, lon = [float(v) for v in a.pin.split(",")]
    dlat = radius_m / 111320.0; dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    env = f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}"
    found = []
    for layer in (1, 2, 3, 4):
        j = get(PROP.format(layer=layer), {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
                                           "where": "1=1", "outFields": "propid,address,housenumber", "returnGeometry": "true", "outSR": "4326", "f": "geojson"}, f"properties near the point (layer {layer})")
        for f in (j or {}).get("features", []):
            if all(f["properties"].get("propid") != g["properties"].get("propid") for g in found): found.append(f)
    if not found:
        print(f"  no properties within {radius_m} m of the point either"); return []
    def centre(f):
        g = f["geometry"]; rings = g["coordinates"] if g["type"] == "Polygon" else [r for poly in g["coordinates"] for r in poly]
        pts = [p for r in rings for p in r]; return sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)
    def dist(f):
        c = centre(f); return math.hypot((c[0] - lat) * 111320, (c[1] - lon) * 111320 * math.cos(math.radians(lat)))
    found.sort(key=dist)
    print(f"  the point is not inside a property; {len(found)} within {radius_m} m:")
    for f in found[:12]:
        print(f"    {f['properties'].get('propid')}  {f['properties'].get('address')}  ({dist(f):.0f} m away)")
    want = (a.address or "").split()[0] if a.address else None
    if want and want[:1].isdigit():
        hit = [f for f in found if str(f["properties"].get("address", "")).split()[:1] == [want]]
        if hit:
            print(f"  using the one numbered {want}"); return [hit[0]]
    print("  using the nearest; if that's the wrong block, re-run with --propid <id> from the list above")
    return [found[0]]


def find_lots(lotdp):
    lots = [s.strip() for s in lotdp.split(",") if s.strip()]
    where = " OR ".join(f"lotidstring='{l}'" for l in lots)
    j = get(LOT, {"where": where, "outFields": "lotidstring,planlotarea", "returnGeometry": "true", "outSR": "4326", "f": "geojson"}, "lots by Lot/DP")
    return (j or {}).get("features", [])

def lots_of(propid):
    j = get(PROP.format(layer=5), {"where": f"propid={propid}", "outFields": "*", "f": "json"}, "lots of the property")
    return [f.get("attributes", {}) for f in (j or {}).get("features", [])]

def aerial_tiles(out, name, win, z=17, half_m=None, folder="aerial_tiles"):
    """Download the cached Web Mercator tiles covering the window (like scrolling a web map). Claude re-projects them."""
    from math import pi, log, tan, radians, floor
    zone = win["zone"]; E0, N0, S = win["E0"], win["N0"], win["size"]
    # window corners -> lon/lat (rough inverse is enough: pad by one tile)
    c = (win["centre_lon"], win["centre_lat"])
    h = half_m if half_m else S / 2 * 1.15
    dlat = h / 111320; dlon = h / (111320 * math.cos(radians(c[1])))
    lon0, lon1, lat0, lat1 = c[0] - dlon, c[0] + dlon, c[1] - dlat, c[1] + dlat
    n = 2 ** z
    tx = lambda lon: floor((lon + 180) / 360 * n)
    ty = lambda lat: floor((1 - log(tan(radians(lat)) + 1 / math.cos(radians(lat))) / pi) / 2 * n)
    x0, x1, y0, y1 = tx(lon0), tx(lon1), ty(lat1), ty(lat0)
    total = (x1 - x0 + 1) * (y1 - y0 + 1)
    print(f"  {total} tiles at zoom {z}")
    td = out / folder; td.mkdir(exist_ok=True); got = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = td / f"{z}_{x}_{y}.jpg"
            if p.exists() and p.stat().st_size > 500:
                got += 1; continue
            try:
                r = requests.get(TILE.format(z=z, y=y, x=x), headers=HEADERS, timeout=60)
                if r.ok and r.content[:2] in (b"\xff\xd8", b"\x89P"):
                    p.write_bytes(r.content); got += 1
            except Exception as e:
                print("   tile failed:", e)
            time.sleep(0.4)
    (td / "index.json").write_text(json.dumps({"z": z, "x0": x0, "x1": x1, "y0": y0, "y1": y1}))
    print(f"  saved {got} of {total} tiles in {folder} (Claude stitches and lines them up)")

def rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    return [p[0] for p in geom["coordinates"]]

def imagery_dates(out, win):
    """Capture date of the NSW imagery over the property (centre and four quarter points)."""
    import datetime
    pts = [(0, 0), (-.25, -.25), (.25, -.25), (-.25, .25), (.25, .25)]
    dl = win["size"] / 111320; seen = {}
    for fx, fy in pts:
        lon = win["centre_lon"] + fx * dl / math.cos(math.radians(win["centre_lat"])); lat = win["centre_lat"] + fy * dl
        j = get(DATES, {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "BlockName,BlockStartDate,Resolution_cm", "returnGeometry": "false", "f": "json"}, "imagery date")
        for f in (j or {}).get("features", []):
            at = f.get("attributes", {}); ms = at.get("BlockStartDate")
            d = datetime.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d") if ms else None
            seen[at.get("BlockName")] = {"block": at.get("BlockName"), "captured": d, "resolution_cm": at.get("Resolution_cm")}
    res = {"source": "NSW Spatial Services, NSW Imagery Dates", "checked": datetime.date.today().isoformat(), "blocks": sorted(seen.values(), key=lambda x: x["captured"] or "")}
    (out / "imagery_dates.json").write_text(json.dumps(res, indent=1))
    for b in res["blocks"]:
        print(f"  imagery captured {b['captured']} ({b['resolution_cm']} cm, {b['block']})")
    if not res["blocks"]:
        print("  no capture date found for this spot")

def catchment_dem(out, win, size=8000, res=10):
    """A wider, coarser elevation grid (default 8 km at 10 m) so Claude can trace the full upstream catchment
    even where it runs outside the 2 km map window."""
    zone = win["zone"]; cx = win["E0"] + win["size"] / 2; cy = win["N0"] - win["size"] / 2
    E0 = round(cx - size / 2); N0 = round(cy + size / 2); px = int(size / res)
    for sr in (7800 + zone, 28300 + zone):
        data = get(DEM, {"bbox": f"{E0},{N0 - size},{E0 + size},{N0}", "bboxSR": sr, "imageSR": sr, "size": f"{px},{px}", "format": "tiff",
                         "pixelType": "F32", "noData": -9999, "interpolation": "RSP_BilinearInterpolation", "f": "image"}, f"catchment elevation (EPSG {sr})", binary=True)
        if data:
            (out / "dem_catchment_10m.tif").write_bytes(data)
            (out / "catchment_window.json").write_text(json.dumps({"E0": E0, "N0": N0, "size": size, "res": res, "epsg": sr}, indent=1))
            print(f"  saved dem_catchment_10m.tif ({size/1000:.0f} km square, {res} m)"); return True
    print("  catchment elevation download failed; try again later with --catchment-only"); return False

def inset(out, name, win):
    """Small blocks: a close-up aerial (about 0.15-0.3 m per pixel) over the property plus a margin."""
    half = max(80, win.get("span_m", 200) / 2 + 60)
    for z in (20, 19):
        print(f"  close-up aerial at zoom {z}, {2*half:.0f} m across")
        aerial_tiles(out, name, win, z, half_m=half, folder=f"inset_tiles_z{z}")
        td = out / f"inset_tiles_z{z}"
        if len([p for p in td.glob("*.jpg")]) > 4:
            return
        print("  not available at that zoom; trying one level coarser")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="short site name, e.g. nimbin or willow-vale")
    ap.add_argument("--address", help="as in the NSW register, e.g. '312 GUNGAS ROAD NIMBIN'")
    ap.add_argument("--propid", help="NSW property id")
    ap.add_argument("--lotdp", help="one or more Lot/DP ids, e.g. '1//DP123456,2//DP123456'")
    ap.add_argument("--pin", help="lat,lon of a point inside the property")
    ap.add_argument("--pluscode", help="Google Plus Code of a point inside the property, e.g. 'HW9Q+JM Mongarlowe NSW'")
    ap.add_argument("--rain-only", action="store_true", help="only (re)fetch the SILO rainfall, using the saved window.json")
    ap.add_argument("--catchment-only", action="store_true", help="only fetch the wide 10 m elevation for the full catchment")
    ap.add_argument("--inset-only", action="store_true", help="only fetch the close-up aerial of the property (small blocks)")
    ap.add_argument("--dates-only", action="store_true", help="only look up the capture date of the aerial photo, using the saved window.json")
    ap.add_argument("--aerial-only", action="store_true", help="only (re)fetch the aerial photo, using the saved window.json")
    ap.add_argument("--zoom", type=int, default=17, help="tile zoom for the aerial fallback (17 is about 1.2 m per pixel)")
    ap.add_argument("--out", default=None, help="output folder (default: NSW site pack <name> next to this script)")
    a = ap.parse_args()
    out = Path(a.out or Path(__file__).resolve().parent / f"NSW site pack {a.name}"); out.mkdir(parents=True, exist_ok=True)
    print(f"Site pack folder: {out}")
    if a.catchment_only:
        catchment_dem(out, json.loads((out / "window.json").read_text())); return
    if a.inset_only:
        win = json.loads((out / "window.json").read_text()); inset(out, a.name, win); return
    if a.dates_only:
        imagery_dates(out, json.loads((out / "window.json").read_text())); return
    if a.aerial_only:
        win = json.loads((out / "window.json").read_text()); aerial_tiles(out, a.name, win, a.zoom); return
    if a.rain_only:
        win = json.loads((out / "window.json").read_text())
        j = get(SILO, {"lat": round(win["centre_lat"], 4), "lon": round(win["centre_lon"], 4), "start": "19950101", "finish": "20251231", "format": "json", "comment": "RN", "username": EMAIL}, "SILO")
        if j:
            (out / "silo_daily.json").write_text(json.dumps(j)); print("  saved silo_daily.json")
        else:
            print("  SILO did not answer; try again in a few minutes")
        return
    if a.pluscode:
        lat, lon = pluscode_to_latlon(a.pluscode); a.pin = f"{lat:.6f},{lon:.6f}"; print(f"  Plus Code {a.pluscode} is {a.pin}")
    if not (a.address or a.propid or a.lotdp or a.pin):
        sys.exit("Give --address, --propid, --lotdp or --pin")

    # 1. boundary
    print("1/4 Finding the property boundary")
    if a.lotdp:
        feats = find_lots(a.lotdp); src = "NSW cadastre lots " + a.lotdp
    else:
        feats = find_property(a); src = "NSW property register"
    if not feats and a.pin:
        feats = nearby_properties(a)
    if not feats:
        sys.exit("No property found. Check the address spelling as it appears on the NSW register, or use --lotdp or --pin.")
    if len(feats) > 1 and not a.lotdp:
        print("  More than one property matched:")
        for f in feats:
            print("   ", f["properties"].get("propid"), f["properties"].get("address"))
        print("  Using the first. Re-run with --propid to choose another.")
        feats = feats[:1]
    allr = [r for f in feats for r in rings(f["geometry"])]
    lons = [p[0] for r in allr for p in r]; lats = [p[1] for r in allr for p in r]
    clon, clat = sum(lons) / len(lons), sum(lats) / len(lats)
    zone = int((clon + 180) // 6) + 1
    E = [ll2mga(p[0], p[1], zone) for r in allr for p in r]
    xs = [e[0] for e in E]; ys = [e[1] for e in E]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    size = max(2000, int(math.ceil((span + 800) / 500) * 500))   # keep 2 km so the upslope catchment is in view, even for small blocks
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    E0 = round(cx - size / 2); N0 = round(cy + size / 2)
    gj = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"source": src}, "geometry": f["geometry"]} for f in feats]}
    (out / "boundary.geojson").write_text(json.dumps(gj))
    props = feats[0]["properties"]
    note = [f"# Private notes: {a.name}", "", f"Source: {src}", f"Address on register: {props.get('address', '')}", f"Property id: {props.get('propid', '')}"]
    if props.get("propid"):
        note.append("Lots: " + ", ".join(str(l.get("lotidstring") or l) for l in lots_of(props["propid"])))
    (out / "private_notes.md").write_text("\n".join(note) + "\n")
    win = {"E0": E0, "N0": N0, "size": size, "zone": zone, "centre_lat": clat, "centre_lon": clon, "span_m": round(span)}
    (out / "window.json").write_text(json.dumps(win, indent=1))
    print(f"  property spans about {span:.0f} m; map window {size} m square, MGA zone {zone}")

    # 2. elevation 5 m
    print("2/4 Downloading 5 m elevation")
    px = int(size / 5)
    ok = False
    for sr in (7800 + zone, 28300 + zone):
        data = get(DEM, {"bbox": f"{E0},{N0 - size},{E0 + size},{N0}", "bboxSR": sr, "imageSR": sr, "size": f"{px},{px}", "format": "tiff",
                         "pixelType": "F32", "noData": -9999, "interpolation": "RSP_BilinearInterpolation", "f": "image"}, f"elevation (EPSG {sr})", binary=True)
        if data:
            (out / "dem_5m.tif").write_bytes(data); win["dem_epsg"] = sr; ok = True
            print(f"  saved dem_5m.tif ({len(data)//1024} KB)"); break
    if not ok:
        print("  Elevation download failed; try again later.")
    (out / "window.json").write_text(json.dumps(win, indent=1))
    print("  wider elevation for the full upstream catchment")
    catchment_dem(out, win)

    # 3. aerial
    print("3/4 Downloading the aerial photo")
    half = size / 2; tpx = 2000; tiles = []
    for row in range(2):
        for col in range(2):
            x0 = E0 + col * half; y1 = N0 - row * half
            data = None
            for sr in (7800 + zone, 28300 + zone):
                data = get(IMG, {"bbox": f"{x0},{y1 - half},{x0 + half},{y1}", "bboxSR": sr, "imageSR": sr, "size": f"{tpx},{tpx}", "format": "jpg", "dpi": 96, "transparent": "false", "f": "image"}, f"aerial tile {row}{col}", binary=True)
                if data:
                    break
            if data:
                p = out / f"aerial_{a.name}_r{row}c{col}.jpg"; p.write_bytes(data); tiles.append((row, col, p))
    if len(tiles) == 4:
        try:
            from PIL import Image
            full = Image.new("RGB", (tpx * 2, tpx * 2))
            for row, col, p in tiles:
                full.paste(Image.open(p).convert("RGB"), (col * tpx, row * tpx))
            full.save(out / f"aerial_{a.name}.jpg", quality=82)
            for _, _, p in tiles:
                p.unlink()
            print(f"  saved aerial_{a.name}.jpg")
        except ImportError:
            print("  kept 4 tiles (install Pillow to stitch: py -m pip install pillow)")
    else:
        for _, _, p in tiles:
            p.unlink()
        print("  the imagery server refused custom-size images; fetching its standard map tiles instead")
        aerial_tiles(out, a.name, win, a.zoom)

    if span < 400:
        print("  small property: also fetching a close-up aerial")
        try:
            inset(out, a.name, win)
        except Exception as e:
            print("  close-up aerial failed:", e)
    try:
        imagery_dates(out, win)
    except Exception as e:
        print("  imagery date lookup failed:", e)

    # 4. rainfall
    print("4/4 Downloading 30 years of rainfall (SILO)")
    j = get(SILO, {"lat": round(clat, 4), "lon": round(clon, 4), "start": "19950101", "finish": "20251231", "format": "json", "comment": "RN", "username": EMAIL}, "SILO")
    if j:
        (out / "silo_daily.json").write_text(json.dumps(j)); print("  saved silo_daily.json")
    print(f"\nDone. Tell Claude the NSW pack for {a.name} is ready (folder: {out}).")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
fetch_site_extras.py: three public data pulls for every design-map site, in one run.

  1. SILO daily rainfall and minimum temperature, 1995 to now (CC BY 4.0) -> the 30-year tank test on every site
  2. Queensland Regional Ecosystems (Qld Herbarium, CC BY) -> the natural vegetation type of each Queensland block
  3. Atlas of Living Australia species records within about 1 km of each block (CC BY / CC0 mixed) -> koalas, birds, frogs, weeds
  4. Soil and Landscape Grid of Australia (CSIRO/TERN, CC BY 4.0): clay, sand, silt, pH, organic carbon, water-holding capacity,
     bulk density and soil depth by depth layer, at the block centre and on a 5 x 5 grid across the window -> real soil numbers
  5. Bureau of Meteorology design rainfall (IFD, ARR 2019) at the block centre -> the 1-in-10 and 1-in-100 year storms that size swale
     spillways, dam bywashes and rain gardens
  6. SILO full daily weather 1995 to now: rain, max and min temperature, solar radiation, pan evaporation and FAO56 reference ETo
     -> a better tank and garden water balance than fixed monthly evaporation
  7. Surface geology (Geological Survey of Queensland detailed geology; NSW Seamless Geology) -> parent rock of each patch, so
     basalt caps, sandstone and alluvium show on the map and explain the soils and springs
  8. Hazard and rules mapping: Queensland bushfire prone area (State Planning Policy classes; statewide service not queryable, so
     council overlays are used where one covers the block) and the Regulated Vegetation Management map categories; NSW Bush Fire
     Prone Land -> the official classes that set building, asset-protection and clearing rules

Files are skipped when they already exist, except silo_full.json (re-fetched if it has no ETo column) and geology.json (re-fetched
if it has no rock-unit names), which earlier versions of this script saved incomplete.

Also probes whether the Queensland elevation (LiDAR) server is back, so Annwn's real ground can be fetched.

  py fetch_site_extras.py              (all sites)
  py fetch_site_extras.py annwn nac    (some sites)

Saves to "<this folder>/../Site extras/<site>/". Gentle on the servers: a pause between requests, retries on failure.
Nothing here is private: SILO is gridded climate, the ecosystems are mapped statewide, the species records are public sightings.
"""
import json, sys, time, os
from pathlib import Path
import requests

H = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
EMAIL = os.environ.get("SILO_EMAIL", "brighttreewellness@gmail.com")
# site id: (lat, lon, state, E0, N0 of the map's 2 km window, MGA zone)
SITES = {
    "bright-tree": (-26.7434, 152.92886, "QLD", 492000.0, 7043000.0, 56),
    "bellbunya": (-26.49107, 152.85225, "QLD", 484159.0, 7071282.0, 56),
    "noosa-forest-retreat": (-26.25641, 152.84421, "QLD", 483394.0, 7096927.0, 56),
    "annwn": (-27.53861, 153.19329, "QLD", 518086.0, 6954895.0, 56),
    "willow-vale": (-31.91075, 151.7787, "NSW", 383492.0, 6469820.0, 56),
    "nimbin": (-28.5654, 153.25403, "NSW", 523889.0, 6841186.0, 56),
    "nac": (-32.67477, 152.04486, "NSW", 409432.0, 6385368.0, 56),
}
SILO = "https://www.longpaddock.qld.gov.au/cgi-bin/silo/DataDrillDataset.php"
RE = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Biota/VegetationManagement/MapServer"
# The Atlas's public occurrence service (no key needed). api.ala.org.au answered 503 for days in Oct 2026, so it is now the fallback.
ALA_HOSTS = ["https://biocache-ws.ala.org.au/ws/occurrences/search", "https://api.ala.org.au/occurrences/occurrences/search"]
QLD_ELEV = "https://spatial-img.information.qld.gov.au/arcgis/rest/services/Elevation"


def get(url, params, what, tries=(0, 8, 30)):
    for wait in tries:
        if wait: print(f"    retrying {what} in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=H, timeout=180)
            if r.status_code == 404 and "Service not found" in r.text:
                print(f"    {what}: the state server says this service is offline"); return None
            if not r.ok: print(f"    {what}: status {r.status_code}"); continue
            try: return r.json()
            except Exception: print(f"    {what}: not JSON: {r.text[:120]!r}")
        except Exception as e:
            print(f"    {what}: {e}")
    return None


def silo(out, lat, lon):
    if (out / "rain_daily.json").exists(): print("  SILO daily: already have it"); return
    print("  SILO daily rain and minimum temperature 1995 to now")
    j = get(SILO, {"lat": round(lat, 4), "lon": round(lon, 4), "start": "19950101", "finish": time.strftime("%Y%m%d"), "format": "json", "comment": "RN", "username": EMAIL}, "SILO")
    if not j or "data" not in j: print("    no SILO data"); return
    d = j["data"]; val = lambda e, c: next((x["value"] for x in e["variables"] if x["variable_code"] == c), None)
    rain = [round((val(e, "daily_rain") or 0) * 10) for e in d]
    tmin = [round((val(e, "min_temp") if val(e, "min_temp") is not None else -99) * 10) for e in d]
    (out / "rain_daily.json").write_text(json.dumps({"source": "SILO gridded daily rainfall at the property (Queensland Government, CC BY 4.0)", "start": d[0]["date"], "end": d[-1]["date"], "rain10": rain, "tmin10": tmin}, separators=(",", ":")))
    print(f"    saved {len(d)} days, {d[0]['date']} to {d[-1]['date']}")
    time.sleep(2)


# Layer ids in the VegetationManagement service (checked 24 Oct 2026 from the service's own layer list):
#   109 "RVM - all"  = the regulated vegetation management map, categories A/B/C/R/X in the field rvm_cat
#   134 "Vegetation management regional ecosystem - all" = the RE polygons (fields re, re_label, vm_status, pc1..)
# They are hard-coded so one request does the job; if the id has moved, the name scan below finds it again.
RE_LAYER = (134, "Vegetation management regional ecosystem - all")
RVM_LAYER = (109, "RVM - all")


def pick_layer(url, hard, pattern, exclude=()):
    """Use the known layer id if the service still has that name there; otherwise scan the layer names for the pattern."""
    j = get(f"{url}/{hard[0]}", {"f": "json"}, "layer check", tries=(0, 5)) or {}
    if j.get("name") == hard[1] and j.get("type") == "Feature Layer": return hard
    found = find_layers(url, pattern, exclude)
    if found: print(f"    (layer {hard[0]} has changed; using layer {found[0][0]} '{found[0][1]}' instead)")
    return found[0] if found else None


def regional_ecosystems(out, E0, N0, zone):
    if (out / "regional_ecosystems.json").exists(): print("  Regional ecosystems: already have it"); return
    print("  Queensland regional ecosystems inside the 2 km window")
    pick = pick_layer(RE, RE_LAYER, r"regional ecosystem - all|regional ecosystem map$", exclude=(r"label", r"pre-?clear"))
    if not pick: print("    no regional-ecosystem layer found in the vegetation service; skipping"); return
    lid, lname = pick; print(f"    layer: {lname}")
    cands = [{"name": lname}]
    env = {"xmin": E0, "ymin": N0 - 2000, "xmax": E0 + 2000, "ymax": N0, "spatialReference": {"wkid": 7800 + zone}}
    j = get(f"{RE}/{lid}/query", {"where": "1=1", "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 7800 + zone, "outSR": 7800 + zone,
                                 "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "true", "f": "json", "resultRecordCount": 500}, "regional ecosystems")
    if not j or "features" not in j: return
    feats = []
    for f in j["features"]:
        a = f.get("attributes", {}); g = f.get("geometry", {})
        rings = [[[round(x - E0, 1), round(N0 - y, 1)] for x, y in r] for r in g.get("rings", [])]
        keep = {k: v for k, v in a.items() if any(s in k.lower() for s in ("re", "status", "vm", "desc", "pc", "bioregion"))}
        feats.append({"attrs": keep, "rings": rings})
    (out / "regional_ecosystems.json").write_text(json.dumps({"source": "Queensland Regional Ecosystem mapping (Queensland Herbarium, CC BY 4.0)", "layer": cands[0]["name"], "fetched": time.strftime("%Y-%m-%d"), "features": feats}, separators=(",", ":")))
    print(f"    saved {len(feats)} polygons")
    time.sleep(2)


def ala(out, lat, lon):
    """Species seen within about 1 km. Two questions per site: (1) every species name with its record count (facets, so nothing is
    missed when there are thousands of records), and (2) a page of records for common names, groups, conservation status and dates."""
    if (out / "ala_species.json").exists(): print("  Atlas of Living Australia: already have it"); return
    print("  Atlas of Living Australia records within about 1 km")
    area = {"q": "*:*", "lat": round(lat, 5), "lon": round(lon, 5), "radius": 1.0}
    counts = recs = None; used = None
    for url in ALA_HOSTS:
        counts = get(url, dict(area, pageSize=0, facets="species,species_group", flimit=-1), "ALA species counts", tries=(0, 10))
        if counts and "totalRecords" in counts:
            used = url
            recs = get(url, dict(area, pageSize=1000, sort="eventDate", dir="desc",
                                 fl="scientificName,vernacularName,eventDate,speciesGroup,stateConservation,countryConservation,dataResourceName,species"), "ALA records", tries=(0, 10))
            break
    if not used: print("    the Atlas did not answer on either address; try again another day"); return
    by = {}
    for f in counts.get("facetResults", []):
        if f.get("fieldName") == "species":
            for r in f.get("fieldResult", []):
                name = r.get("label") or r.get("fq", "").split(":", 1)[-1].strip('"')
                if name and name not in ("Not supplied",): by[name] = {"common": None, "group": None, "n": r.get("count", 0), "last": "", "status": None}
    groups = {r.get("label"): r.get("count") for f in counts.get("facetResults", []) if f.get("fieldName") == "species_group" for r in f.get("fieldResult", [])}
    for o in (recs or {}).get("occurrences", []):
        k = o.get("species") or o.get("scientificName") or "?"
        e = by.setdefault(k, {"common": None, "group": None, "n": 0, "last": "", "status": None})
        e["common"] = e["common"] or o.get("vernacularName"); g = o.get("speciesGroup"); e["group"] = e["group"] or (g[0] if isinstance(g, list) and g else g)
        e["status"] = e["status"] or o.get("stateConservation") or o.get("countryConservation")
        e["last"] = max(e["last"], (o.get("eventDate") and time.strftime("%Y-%m-%d", time.gmtime(o["eventDate"] / 1000)) if isinstance(o.get("eventDate"), (int, float)) else str(o.get("eventDate") or ""))[:10])
        if not by.get(k, {}).get("n"): e["n"] += 1
    (out / "ala_species.json").write_text(json.dumps({"source": "Atlas of Living Australia occurrence records within 1 km (CC BY / CC0, see each record); " + used.split("/")[2],
                                                     "fetched": time.strftime("%Y-%m-%d"), "total": counts.get("totalRecords"), "groups": groups, "species": by}, indent=0))
    print(f"    {counts.get('totalRecords')} records, {len(by)} species ({used.split('/')[2]})")
    time.sleep(2)


# ---- MGA (GDA2020) to longitude/latitude, so grid points can be sent to services that only speak lon/lat
import math
_a = 6378137.0; _f = 1 / 298.257222101; _k0 = 0.9996; _n = _f / (2 - _f); _A = _a / (1 + _n) * (1 + _n ** 2 / 4 + _n ** 4 / 64)
_be = [_n / 2 - 2 * _n ** 2 / 3 + 37 * _n ** 3 / 96, _n ** 2 / 48 + _n ** 3 / 15, 17 * _n ** 3 / 480]; _e = math.sqrt(_f * (2 - _f))


def mga2ll(E, N, zone):
    xi = (N - 10000000.0) / (_k0 * _A); eta = (E - 500000.0) / (_k0 * _A)
    xp = xi - sum(_be[j] * math.sin(2 * (j + 1) * xi) * math.cosh(2 * (j + 1) * eta) for j in range(3))
    ep = eta - sum(_be[j] * math.cos(2 * (j + 1) * xi) * math.sinh(2 * (j + 1) * eta) for j in range(3))
    chi = math.asin(math.sin(xp) / math.cosh(ep)); lat = chi
    for _ in range(6): lat = math.asin(math.tanh(math.atanh(math.sin(chi)) + _e * math.atanh(_e * math.sin(lat))))
    return math.degrees(math.radians(zone * 6 - 183) + math.atan2(math.sinh(ep), math.cos(xp))), math.degrees(lat)


def _arcgis_query(url, layer_id, env, zone, what, where, extra=None):
    p = {"where": where, "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 7800 + zone, "outSR": 7800 + zone,
         "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "true", "f": "json", "resultRecordCount": 1000}
    p.update(extra or {})
    j = get(f"{url}/{layer_id}/query", p, what)
    if j and j.get("error"): print(f"    {what}: server error {j['error'].get('message', '')[:100]}"); return None
    return j.get("features") if j and "features" in j else None


def arcgis_polys(url, layer_id, E0, N0, zone, keep_keys, what, where="1=1"):
    """Query one ArcGIS feature layer for every polygon touching the 2 km window; return features in map coordinates (x east, y south of N0).
    If the server chokes on the request ("Error performing query operation", as it did for Nimbin's bushfire layer, usually because
    the polygons are huge), it is asked again with simplified outlines, and then in four 1 km quarters."""
    env = {"xmin": E0, "ymin": N0 - 2000, "xmax": E0 + 2000, "ymax": N0, "spatialReference": {"wkid": 7800 + zone}}
    raw = _arcgis_query(url, layer_id, env, zone, what, where)
    if raw is None:
        print(f"    {what}: asking again with simplified outlines (2 m)")
        raw = _arcgis_query(url, layer_id, env, zone, what, where, {"maxAllowableOffset": 2})
    if raw is None:
        print(f"    {what}: asking again in four 1 km quarters")
        raw, seen = [], set()
        for qx in (0, 1000):
            for qy in (0, 1000):
                q = {"xmin": E0 + qx, "ymin": N0 - 2000 + qy, "xmax": E0 + qx + 1000, "ymax": N0 - 1000 + qy, "spatialReference": {"wkid": 7800 + zone}}
                part = _arcgis_query(url, layer_id, q, zone, what, where, {"maxAllowableOffset": 2})
                if part is None: return None
                for f in part:   # the same polygon can touch several quarters: keep it once
                    oid = next((v for k, v in f.get("attributes", {}).items() if k.lower() in ("objectid", "fid", "oid")), None)
                    if oid is not None and oid in seen: continue
                    seen.add(oid); raw.append(f)
    feats = []
    for f in raw:
        a = f.get("attributes", {}); g = f.get("geometry", {})
        rings = [[[round(x - E0, 1), round(N0 - y, 1)] for x, y in r] for r in g.get("rings", [])]
        keep = {k: v for k, v in a.items() if any(s in k.lower() for s in keep_keys) and not k.lower().startswith(("shape", "objectid"))}
        feats.append({"attrs": keep, "rings": rings})
    return feats


def find_layers(url, pattern, exclude=()):
    """List a MapServer's layers and return (id, name) for those whose name matches the pattern (case-insensitive) and none of the exclude words."""
    import re
    j = get(url, {"f": "json"}, "service listing", tries=(0, 5))
    if not j: return []
    out = []
    for l in j.get("layers", []):
        n = l.get("name", "")
        if re.search(pattern, n, re.I) and not any(re.search(x, n, re.I) for x in exclude) and l.get("subLayerIds") is None: out.append((l["id"], n))
    return out


def find_services(root, folders, pattern):
    """Walk ArcGIS folders and return MapServer URLs whose name matches the pattern (so we don't hard-code names that may change)."""
    import re
    urls = []
    for fo in folders:
        j = get(f"{root}/{fo}", {"f": "json"}, f"folder {fo}", tries=(0, 5)) or {}
        for sv in j.get("services", []):
            if sv.get("type") in ("MapServer", "FeatureServer") and re.search(pattern, sv["name"], re.I): urls.append(f"{root}/{sv['name']}/{sv['type']}")
    return urls


QLD_GIS = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services"
# The Soil and Landscape Grid lives on CSIRO's ArcGIS server under the TERN folder. Two host names answer for the same server;
# soils.csiro.au is tried first because the asris.csiro.au address gave "HTTP 500" on every identify on 24 Oct 2026.
SLGA_HOSTS = ["https://soils.csiro.au/arcgis/rest/services/TERN", "https://www.asris.csiro.au/arcgis/rest/services/TERN"]
# attribute code -> what it is and its unit (Soil and Landscape Grid of Australia, 90 m, version 2 where available)
SLGA_ATTRS = {"CLY": ("Clay", "%"), "SND": ("Sand", "%"), "SLT": ("Silt", "%"), "PHC": ("pH (CaCl2)", ""), "SOC": ("Organic carbon", "%"),
              "AWC": ("Available water capacity", "%"), "BDW": ("Bulk density (whole earth)", "g/cm3"), "DER": ("Depth of regolith", "m"), "DES": ("Depth of soil", "m")}
# Service names per attribute, best first (checked against the TERN folder listing on 24 Oct 2026). "TRN_N" is version 2 of the grid;
# "NAT_C" is version 1. The old names SOC_ACLEP_AU_NAT_C and DES_ACLEP_AU_NAT_C no longer exist (they became ..._NAT_C_V1), which is
# why those requests failed. Depth of regolith (DER) only exists as version 1.
SLGA_SERVICES = {a: [f"{a}_ACLEP_AU_TRN_N", f"{a}_ACLEP_AU_NAT_C", f"{a}_ACLEP_AU_NAT_C_V1"] for a in SLGA_ATTRS}
SLGA_SERVICES["DER"] = ["DER_ACLEP_AU_NAT_C"]
GRID_ATTRS = ("CLY", "AWC", "SOC")   # sampled on the 5 x 5 grid as well as the centre (the rest: centre only, to keep requests down)
_slga_cache = {}
_slga_diag = {}   # attr -> True once an empty reply has been printed, so the log shows it once not 25 times


def slga_service(attr):
    """Find the first host + service that exists for this attribute and list its estimated-value (EV) layers, one per depth.
    Asking identify for just those layer ids keeps each request small (the 5th/95th percentile layers are not needed)."""
    if attr in _slga_cache: return _slga_cache[attr]
    for host in SLGA_HOSTS:
        for svc in SLGA_SERVICES[attr]:
            j = get(f"{host}/{svc}/MapServer", {"f": "json"}, f"soil grid {attr} service", tries=(0,))
            if not j or j.get("error") or "layers" not in j: continue
            ev = [l["id"] for l in j["layers"] if "_EV_" in l.get("name", "").upper()]
            layers = "all:" + ",".join(str(i) for i in ev) if ev else "all"
            print(f"    {attr}: using {svc} on {host.split('/')[2]} ({len(ev) or 'all'} depth layers)")
            _slga_cache[attr] = (f"{host}/{svc}/MapServer/identify", layers); return _slga_cache[attr]
    print(f"    {attr}: no Soil and Landscape Grid service found for it (tried {', '.join(SLGA_SERVICES[attr])})")
    _slga_cache[attr] = None; return None


def slga_point(attr, lon, lat):
    """One 'identify' call returns every depth layer of one attribute at a point. Returns {depth_cm: value} from the estimated-value layers."""
    import re
    svc = slga_service(attr)
    if not svc: return {}
    url, layers = svc
    base = {"geometryType": "esriGeometryPoint", "sr": 4326, "tolerance": 2, "mapExtent": f"{lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}",
            "imageDisplay": "400,400,96", "returnGeometry": "false", "f": "json"}
    # Three shapes of the same question, because ArcGIS servers differ in what they accept for a raster identify
    attempts = [dict(base, geometry=f"{lon},{lat}", layers=layers),
                dict(base, geometry=json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}), layers="all"),
                dict(base, geometry=f"{lon},{lat}", layers="visible", tolerance=5)]
    j = None
    for k, params in enumerate(attempts):
        j = get(url, params, f"soil grid {attr}", tries=(0,) if k < 2 else (0, 6))
        if j and j.get("error"):
            print(f"    soil grid {attr}: server said {str(j['error'].get('message', j['error']))[:120]}"); j = None; continue
        if j and j.get("results"): break
        if j is not None and k == 0: print(f"    soil grid {attr}: identify returned no results with layer list {layers}; trying other request shapes")
    out = {}
    if j and not j.get("results") and not _slga_diag.get(attr):
        _slga_diag[attr] = True; print(f"    soil grid {attr}: empty reply {json.dumps(j)[:160]}")
    shown = _slga_diag.get("sample")
    for r in (j or {}).get("results", []):
        name = r.get("layerName", ""); at = r.get("attributes", {}) or {}
        v = at.get("Pixel Value")
        if v is None:   # some services name it differently ("Pixel value", "Stretch.Pixel Value", or just the value)
            for k2, v2 in at.items():
                if "pixel" in k2.lower() or "value" in k2.lower(): v = v2; break
        if v is None and not shown:
            _slga_diag["sample"] = shown = True; print(f"    soil grid {attr}: a reply came back but no value field was recognised; sample: {json.dumps(r)[:200]}")
        if v in (None, "NoData", "", "null"): continue
        if "_EV_" not in name.upper() and re.search(r"_(05|95)_", name): continue   # skip the 5th / 95th percentile layers
        m = re.search(r"(\d{3})_(\d{3})", name); depth = f"{int(m.group(1))}-{int(m.group(2))}" if m else "all"
        try: out[depth] = round(float(v), 2)
        except ValueError: pass
    return out


def soil_grid(out, E0, N0, zone):
    if (out / "soil_grid.json").exists(): print("  Soil grid: already have it"); return
    print("  Soil and Landscape Grid of Australia (clay, sand, silt, pH, carbon, water capacity, density, depth)")
    clon, clat = mga2ll(E0 + 1000, N0 - 1000, zone)
    centre = {}
    for attr in SLGA_ATTRS:
        v = slga_point(attr, clon, clat)
        if v: centre[attr] = v
        time.sleep(0.4)
    if not centre: print("    no soil grid data came back (the CSIRO server may be down); skipping"); return
    grid = []
    for i in range(5):
        for k in range(5):
            x, y = (i + 0.5) * 400, (k + 0.5) * 400
            lon, lat = mga2ll(E0 + x, N0 - y, zone); cell = {"x": x, "y": y}
            for attr in GRID_ATTRS:
                v = slga_point(attr, lon, lat)
                if v: cell[attr] = v
                time.sleep(0.3)
            grid.append(cell)
    (out / "soil_grid.json").write_text(json.dumps({"source": "Soil and Landscape Grid of Australia (CSIRO / TERN), 90 m national modelled soil attributes, CC BY 4.0",
                                                   "fetched": time.strftime("%Y-%m-%d"), "attrs": {k: {"name": a, "unit": u} for k, (a, u) in SLGA_ATTRS.items()},
                                                   "depths_cm": ["0-5", "5-15", "15-30", "30-60", "60-100", "100-200"], "centre": centre, "grid_step_m": 400, "grid": grid}, separators=(",", ":")))
    print(f"    saved: {len(centre)} attributes at the centre, {len(grid)} grid points for {', '.join(GRID_ATTRS)}")
    time.sleep(2)


IFD = "https://www.bom.gov.au/water/designRainfalls/revised-ifd/"
# The Bureau's web firewall answers plain scripts with an HTML page. Looking like a browser that came from the IFD page itself
# (full browser User-Agent, Referer, Accept-Language) is what the page's own "download" buttons send. No separate JSON API is
# documented (checked 24 Oct 2026), so if this still comes back as HTML the browser fallback below is the way.
IFD_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
               "Accept": "application/json,text/csv,text/plain,text/html;q=0.8,*/*;q=0.5", "Accept-Language": "en-AU,en;q=0.9",
               "Referer": IFD + "?year=2016", "Connection": "keep-alive"}


def _ifd_csv(text):
    """Turn the Bureau's CSV download (comment lines, then a header row of AEPs and one row per duration) into {"columns": [...], "rows": [...]}."""
    import csv, io
    rows = [r for r in csv.reader(io.StringIO(text)) if r and not r[0].startswith("#")]
    head = next((i for i, r in enumerate(rows) if len(r) > 3 and r[0].strip().lower().startswith("duration")), None)
    if head is None: return None
    return {"columns": rows[head], "rows": [r for r in rows[head + 1:] if len(r) == len(rows[head])]}


def ifd(out, lat, lon):
    """Design rainfall depths (mm) for standard durations and annual exceedance probabilities, ARR 2019 (BoM, CC BY 4.0).
    The Bureau sometimes refuses automated requests: if nothing is saved, open the same page in a browser, choose "JSON" under output,
    and save the result as "Site extras/<site>/ifd.json"."""
    if (out / "ifd.json").exists(): print("  Design rainfall (IFD): already have it"); return
    print("  Bureau of Meteorology design rainfall (IFD, ARR 2019)")
    params = {"year": "2016", "coordinate_type": "dd", "latitude": round(lat, 4), "longitude": round(lon, 4), "sdmin": "true", "sdhr": "true", "sdday": "true",
              "user_label": "", "values": "depths", "update": "", "season": "", "output_type": "json"}
    j = None
    s = requests.Session(); s.headers.update(IFD_HEADERS)
    try: s.get(IFD, params={"year": "2016"}, timeout=60)   # visit the page first, as a browser would (sets the Bureau's cookies)
    except Exception: pass
    for fmt in ("json", "csv"):
        for wait in (0, 10):
            if wait: time.sleep(wait)
            try:
                r = s.get(IFD, params={**params, "output_type": fmt}, timeout=120)
                body = r.text.lstrip()
                if r.ok and fmt == "json" and body.startswith(("{", "[")): j = r.json(); break
                if r.ok and fmt == "csv" and not body.lower().startswith(("<!doctype", "<html")):
                    j = _ifd_csv(r.text)
                    if j: break
                print(f"    IFD ({fmt}): status {r.status_code}, {'came back as a web page, not data' if r.ok else 'refused'}")
            except Exception as e: print(f"    IFD: {e}")
        if j is not None: break
    if j is None:
        print("    The Bureau did not return data. In a browser open:\n      " + IFD + "?" + "&".join(f"{k}={v}" for k, v in params.items()) + "\n    and save the JSON shown as ifd.json in this site's Site extras folder.")
        return
    (out / "ifd.json").write_text(json.dumps({"source": "Bureau of Meteorology design rainfall (IFD), Australian Rainfall and Runoff 2019 data, CC BY 4.0",
                                             "fetched": time.strftime("%Y-%m-%d"), "lat": lat, "lon": lon, "data": j}, separators=(",", ":")))
    print("    saved the IFD table")
    time.sleep(2)


def silo_full(out, lat, lon):
    f = out / "silo_full.json"
    if f.exists():
        try: old = json.loads(f.read_text())
        except Exception: old = {}
        if any(v != -999 for v in old.get("eto10", [])): print("  SILO full weather: already have it"); return
        print("  SILO full weather: the saved file has no evapotranspiration values (old request code); fetching again")
    print("  SILO daily weather 1995 to now: rain, max/min temperature, radiation, pan evaporation, FAO56 ETo")
    # SILO comment letters: R rain, X max temp, N min temp, E class-A pan evaporation, J solar radiation, F FAO56 short-crop ET
    # (T is the ASCE tall-crop ET, which is why the earlier "RXNEJT" request came back with no et_short_crop column)
    j = get(SILO, {"lat": round(lat, 4), "lon": round(lon, 4), "start": "19950101", "finish": time.strftime("%Y%m%d"), "format": "json", "comment": "RXNEJF", "username": EMAIL}, "SILO full")
    if not j or "data" not in j: print("    no SILO data"); return
    d = j["data"]
    def col(code):
        vals = []
        for e in d:
            v = next((x["value"] for x in e["variables"] if x["variable_code"] == code), None)
            vals.append(-999 if v is None else round(v * 10))
        return vals
    (out / "silo_full.json").write_text(json.dumps({"source": "SILO gridded daily climate at the property (Queensland Government, CC BY 4.0): rain, temperature, radiation, pan evaporation and FAO56 reference evapotranspiration",
                                                   "start": d[0]["date"], "end": d[-1]["date"], "units": "tenths (mm, degC, MJ/m2, mm); -999 = missing",
                                                   "rain10": col("daily_rain"), "tmax10": col("max_temp"), "tmin10": col("min_temp"), "rad10": col("radiation"), "evap10": col("evap_pan"), "eto10": col("et_short_crop")}, separators=(",", ":")))
    print(f"    saved {len(d)} days")
    time.sleep(2)


# NSW Seamless Geology (Geological Survey of NSW), two doors to the same data:
#  1. ArcGIS, one MapServer per geological province for MGA zone 56 (all our NSW sites are in zone 56). Each has a polygon layer
#     called RockUnits_<province>; the line and pattern layers are skipped. Listed youngest first so the surface unit comes first
#     where provinces overlap: CSP Cenozoic sediments, CIP Cenozoic volcanics, MIP Mesozoic igneous, GAB Great Australian Basin,
#     PTB Permian-Triassic basins, NEO New England Orogen, LAO Lachlan Orogen. (Service list checked 24 Oct 2026.)
#  2. The WFS. Its host is gs-seamless.geoscience.nsw.gov.au (the old gs.geoscience... address was the bug); the feature type
#     name is read from GetCapabilities because it could not be confirmed from here.
NSW_GEO_ARCGIS = "https://spatial.industry.nsw.gov.au/arcgis/rest/services/Minerals"
NSW_GEO_PROVINCES = ["CSP", "CIP", "MIP", "GAB", "PTB", "NEO", "LAO"]
NSW_GEO_WFS = "https://gs-seamless.geoscience.nsw.gov.au/geoserver/ows"


# Geological Survey of Queensland detailed geology service. Layer 15 "Detailed Surface geology" is the rock-unit polygons;
# 17 "Detailed Solid geology" is the same with the thin cover stripped off. Layer 3 "Detailed Geological Boundaries" is only the
# contact LINES (no unit names), which is what the first run saved by mistake. (Layer list checked 24 Oct 2026.)
QLD_GEO = f"{QLD_GIS}/GeoscientificInformation/GeologyDetailed/MapServer"
QLD_GEO_LAYERS = [(15, "Detailed Surface geology"), (17, "Detailed Solid geology")]
_GEO_LINE_WORDS = (r"boundar", r"extent", r"fault", r"structure", r"line", r"point", r"site", r"fold", r"dyke", r"marker", r"lineament", r"joint", r"trend", r"feature", r"label", r"annotation")


def silo_long(out, lat, lon):
    """The whole SILO record, 1889 to now: daily rain, max and min temperature. For the climate-trend and worst-drought tests.
    Before about 1910 the gauge network was thin and temperatures before 1957 are interpolated from far away: use those years as indicative."""
    if (out / "silo_long.json").exists(): print("  SILO 1889 to now: already have it"); return
    print("  SILO daily rain and temperature 1889 to now (the full record, for climate trends and the worst historic droughts)")
    j = get(SILO, {"lat": round(lat, 4), "lon": round(lon, 4), "start": "18890101", "finish": time.strftime("%Y%m%d"), "format": "json", "comment": "RXN", "username": EMAIL}, "SILO long", tries=(0, 20, 60))
    if not j or "data" not in j: print("    no SILO data"); return
    d = j["data"]
    def col(code):
        o = []
        for e in d:
            v = next((x["value"] for x in e["variables"] if x["variable_code"] == code), None)
            o.append(-999 if v is None else round(v * 10))
        return o
    (out / "silo_long.json").write_text(json.dumps({"source": "SILO gridded daily climate at the property, 1889 to now (Queensland Government, CC BY 4.0); pre-1910 rain and pre-1957 temperature are interpolated from sparse stations",
                                                   "start": d[0]["date"], "end": d[-1]["date"], "units": "tenths (mm, degC); -999 = missing",
                                                   "rain10": col("daily_rain"), "tmax10": col("max_temp"), "tmin10": col("min_temp")}, separators=(",", ":")))
    print(f"    saved {len(d)} days, {d[0]['date']} to {d[-1]['date']}")
    time.sleep(3)


def _has_unit_names(feats):
    return any(any(("name" in k.lower() or "unit" in k.lower() or "lith" in k.lower()) and v not in (None, "", " ") for k, v in f.get("attrs", {}).items()) for f in feats or [])


def geology(out, state, E0, N0, zone):
    f = out / "geology.json"
    if f.exists():
        try: old = json.loads(f.read_text())
        except Exception: old = {}
        if _has_unit_names(old.get("features")): print("  Geology: already have it"); return
        print("  Geology: the saved file has no rock-unit names (it was the boundary lines); fetching again")
    print("  Surface geology inside the 2 km window")
    keep = ("name", "lith", "age", "rock", "desc", "unit", "period", "era", "symbol", "type")
    if state == "QLD":
        feats, used = None, None
        for lid, lname in QLD_GEO_LAYERS:
            pick = pick_layer(QLD_GEO, (lid, lname), r"surface geology$|solid geology$|rock unit|geological units", exclude=_GEO_LINE_WORDS)
            if not pick: continue
            feats = arcgis_polys(QLD_GEO, pick[0], E0, N0, zone, keep, f"geology ({pick[1]})")
            if feats and _has_unit_names(feats): used = f"{QLD_GEO} layer {pick[0]} ({pick[1]})"; break
            feats = None
        if not feats:   # the service itself may have moved: look for any geology service with a polygon rock-unit layer
            for u in find_services(QLD_GIS, ["GeoscientificInformation"], r"geolog"):
                for lid, lname in find_layers(u, r"surface geology$|solid geology$|rock unit|geological units", exclude=_GEO_LINE_WORDS):
                    feats = arcgis_polys(u, lid, E0, N0, zone, keep, f"geology ({lname})")
                    if feats and _has_unit_names(feats): used = f"{u} layer {lid} ({lname})"; break
                    feats = None
                if feats: break
        if not feats: print("    no geology polygons with unit names came back; skipping"); return
        src = "Detailed surface geology, Geological Survey of Queensland (State of Queensland), CC BY 4.0"
    else:
        keep = keep + ("litholog", "surface", "code", "strat", "formation", "group", "province")
        feats, used = [], []
        # Door 1: the ArcGIS province services (a province that does not reach the window simply returns no polygons)
        for prov in NSW_GEO_PROVINCES:
            u = f"{NSW_GEO_ARCGIS}/NSW_SeamlessGeology_Zone{zone}_{prov}/MapServer"
            lays = find_layers(u, rf"^RockUnits?_{prov}(_Solid)?$", exclude=(r"pattern", r"bndy", r"fault", r"line", r"point"))
            if not lays: continue
            got = arcgis_polys(u, lays[0][0], E0, N0, zone, keep, f"geology ({prov} {lays[0][1]})")
            if got:
                for f in got: f["attrs"]["province"] = prov
                feats += got; used.append(f"{prov} layer {lays[0][0]}")
            time.sleep(0.5)
        if feats:
            used = f"{NSW_GEO_ARCGIS} ({', '.join(used)})"
        else:
            # Door 2: the GeoServer WFS. The feature type name is found from GetCapabilities, so a renamed layer only costs a message.
            print("    no polygons from the ArcGIS province services; trying the Seamless Geology WFS")
            try:
                caps = requests.get(NSW_GEO_WFS, params={"service": "WFS", "acceptversions": "2.0.0", "request": "GetCapabilities"}, headers=H, timeout=120).text
            except Exception as e: print(f"    NSW geology: {e}; skipping"); return
            import re
            names = re.findall(r"<(?:wfs:)?Name>([^<]+)</(?:wfs:)?Name>", caps)
            cand = ([n for n in names if re.search(r"rock.?unit", n, re.I) and not re.search(r"fault|bndy|boundar|line|point|struct|pattern|label", n, re.I)]
                    or [n for n in names if re.search(r"geol|unit|poly|lith", n, re.I) and not re.search(r"fault|bndy|boundar|line|point|struct|pattern|label", n, re.I)])
            if not cand:
                print("    NSW Seamless Geology layer not found in the WFS listing; feature types seen: " + ", ".join(names[:15]) + "; skipping"); return
            lon0, lat0 = mga2ll(E0, N0 - 2000, zone); lon1, lat1 = mga2ll(E0 + 2000, N0, zone)
            j = get(NSW_GEO_WFS, {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": cand[0], "outputFormat": "application/json",
                                  "srsName": f"EPSG:{7800 + zone}", "bbox": f"{lat0},{lon0},{lat1},{lon1},EPSG:4326", "count": 500}, "NSW geology")
            if not j or "features" not in j: print("    no NSW geology polygons came back; skipping"); return
            for f in j["features"]:
                g = f.get("geometry") or {}; a = f.get("properties", {})
                polys = [g["coordinates"]] if g.get("type") == "Polygon" else g.get("coordinates", []) if g.get("type") == "MultiPolygon" else []
                rings = [[[round(x - E0, 1), round(N0 - y, 1)] for x, y in r] for poly in polys for r in poly]
                feats.append({"attrs": {k: v for k, v in a.items() if any(s in k.lower() for s in keep)}, "rings": rings})
            used = f"{NSW_GEO_WFS} {cand[0]}"
        src = "NSW Seamless Geology, Geological Survey of NSW (State of New South Wales), CC BY 4.0"
    (out / "geology.json").write_text(json.dumps({"source": src, "layer": used, "fetched": time.strftime("%Y-%m-%d"), "features": feats}, separators=(",", ":")))
    print(f"    saved {len(feats)} polygons from {used}")
    time.sleep(2)


# NSW Bush Fire Prone Land: (service, known layer id, layer name), tried in order. Both are NSW Planning servers (checked 24 Oct 2026):
#  - ePlanning Planning_Portal_Hazard layer 229 "Bushfire Prone Land" (fields Category, d_Category) is the one that answered for
#    Willow Vale and NAC, so it stays first;
#  - Fire/BFPL layer 0 "NSW Bush Fire Prone Lands" is the statewide RFS-certified map listed on data.nsw.gov.au, as the backup.
# The old portal.spatial.nsw.gov.au/.../NSW_Bushfire_Prone_Land/MapServer address does not exist (there is a Hosted FeatureServer there instead).
NSW_BFPL = [("https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/ePlanning/Planning_Portal_Hazard/MapServer", 229, "Bushfire Prone Land"),
            ("https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Fire/BFPL/MapServer", 0, "NSW Bush Fire Prone Lands"),
            ("https://portal.spatial.nsw.gov.au/server/rest/services/Hosted/NSW_BushFire_Prone_Land/FeatureServer", 0, None)]

# Queensland bushfire prone area. The statewide "Bushfire prone area - Queensland series" (QFES/CSIRO, CC BY) is only published as
# downloads from QSpatial and as a tiles-only picture service (tiles.arcgis.com/.../Bushfire_Prone_Areas), neither of which can be
# queried for polygons; no queryable statewide service was found on 24 Oct 2026 (PlanningCadastre/StatePlanning has no bushfire layer).
# So: scan the state and QFES servers in case one appears, then fall back to the council planning-scheme overlays, which carry
# the same SPP hazard classes for their own area (a council service outside the window just returns nothing).
QFES_GIS = "https://gisext.qfes.qld.gov.au/arcgis/rest/services"
QLD_BUSHFIRE_COUNCIL = [("https://geoimage.scc.qld.gov.au/arcgis/rest/services/PlanningCadastre/PlanningScheme_SunshineCoast_Overlays_SCC/MapServer",
                         r"bushfire hazard area", "Sunshine Coast Council planning scheme bushfire hazard overlay (SPP classes)")]
QLD_BUSHFIRE_DOWNLOAD = "https://qldspatial.information.qld.gov.au/catalogue/custom/search.page?q=%22Bushfire%20prone%20area%20-%20South%20East%20Queensland%22"


def hazard(out, state, E0, N0, zone):
    if (out / "hazard.json").exists(): print("  Hazard mapping: already have it"); return
    print("  Bushfire hazard and vegetation-clearing rule mapping inside the 2 km window")
    layers_out = []
    bf_keys = ("haz", "class", "cat", "desc", "type", "name", "potential", "intensity")
    if state == "QLD":
        got = False
        # 1. a statewide service, if one has appeared
        urls = find_services(QLD_GIS, ["PlanningCadastre", "Boundaries", "Environment", "Society"], r"bushfire|planningpolicy|hazard")   # (QFES's own server is tiles-only and its certificate has expired, so it is not scanned)
        for u in urls:
            for lid, lname in find_layers(u, r"bushfire", exclude=(r"label", r"line", r"tile", r"building")):
                feats = arcgis_polys(u, lid, E0, N0, zone, bf_keys, f"bushfire hazard ({lname})")
                if feats is not None:
                    layers_out.append({"kind": "bushfire", "name": lname, "source": "Queensland bushfire prone area mapping (State Planning Policy), State of Queensland (QFES), CC BY 4.0", "features": feats}); got = True; break
            if got: break
        # 2. council planning-scheme overlays (several layers: high / medium / buffers)
        if not got:
            for u, pat, src in QLD_BUSHFIRE_COUNCIL:
                feats = []
                for lid, lname in find_layers(u, pat, exclude=(r"label",)):
                    part = arcgis_polys(u, lid, E0, N0, zone, bf_keys, f"bushfire hazard ({lname})")
                    for p in part or []: p["attrs"]["class"] = lname; feats.append(p)
                if feats:
                    layers_out.append({"kind": "bushfire", "name": "Bushfire hazard overlay", "source": src + ", CC BY 4.0", "features": feats}); got = True; break
        if not got: print("    no queryable bushfire prone area service covers this block. The statewide map is download-only:\n      " + QLD_BUSHFIRE_DOWNLOAD + "\n    continuing")
        # Regulated vegetation management map (categories A, B, C, R, X in the field rvm_cat)
        pick = pick_layer(RE, RVM_LAYER, r"^RVM - all$|regulated vegetation management map", exclude=(r"label", r"pre-?clear", r"essential", r"watercourse", r"wetland"))
        if pick:
            feats = arcgis_polys(RE, pick[0], E0, N0, zone, ("cat", "class", "rvm", "desc", "type", "name", "status", "map_no", "override", "version"), f"regulated vegetation ({pick[1]})")
            if feats is not None:
                layers_out.append({"kind": "regulated_vegetation", "name": pick[1], "source": "Regulated vegetation management map (Vegetation Management Act 1999), State of Queensland, CC BY 4.0", "features": feats})
        else: print("    regulated vegetation management layer not found in the vegetation service; continuing")
    else:
        got = False
        for u, lid, lname in NSW_BFPL:
            pick = pick_layer(u, (lid, lname), r"bush ?fire prone", exclude=(r"label",)) if lname else (find_layers(u, r"bush ?fire prone", exclude=(r"label",)) or [None])[0]
            if not pick: continue
            feats = arcgis_polys(u, pick[0], E0, N0, zone, ("cat", "class", "desc", "type", "name", "veg", "guideline"), f"NSW bush fire prone land ({pick[1]})")
            if feats is not None:
                layers_out.append({"kind": "bushfire", "name": pick[1], "source": "NSW Bush Fire Prone Land map (NSW Rural Fire Service / Planning), CC BY 4.0", "features": feats}); got = True; break
        if not got: print("    NSW Bush Fire Prone Land: none of the known services answered for this block; continuing")
    if not layers_out: print("    nothing saved"); return
    (out / "hazard.json").write_text(json.dumps({"fetched": time.strftime("%Y-%m-%d"), "layers": layers_out}, separators=(",", ":")))
    print("    saved: " + ", ".join(f"{l['kind']} ({len(l['features'])} polygons)" for l in layers_out))
    time.sleep(2)


def probe_qld_elevation():
    print("\nChecking the Queensland elevation (LiDAR) server ...")
    j = get(QLD_ELEV, {"f": "json"}, "elevation", tries=(0,))
    if j and j.get("services"):
        print("  It is BACK ONLINE. Run \"Annwn - get site data.bat\" again to replace Annwn's placeholder ground with real LiDAR.")
    else:
        print("  Still offline. Annwn stays on placeholder ground for now.")


def main():
    want = sys.argv[1:] or list(SITES)
    root = Path(__file__).resolve().parents[1] / "Site extras"
    for site in want:
        lat, lon, state, E0, N0, zone = SITES[site]
        out = root / site; out.mkdir(parents=True, exist_ok=True)
        print(f"\n{site}")
        silo(out, lat, lon)
        if state == "QLD": regional_ecosystems(out, E0, N0, zone)
        ala(out, lat, lon)
        soil_grid(out, E0, N0, zone)
        ifd(out, lat, lon)
        silo_full(out, lat, lon)
        silo_long(out, lat, lon)
        geology(out, state, E0, N0, zone)
        hazard(out, state, E0, N0, zone)
    print('\nDone. Tell Claude: "site extras are ready".')


if __name__ == "__main__":
    main()

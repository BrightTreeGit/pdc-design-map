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
  8. Hazard and rules mapping: Queensland bushfire hazard area (State Planning Policy) and the Regulated Vegetation Management map
     categories; NSW Bush Fire Prone Land -> the official classes that set building, asset-protection and clearing rules

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
ALA = "https://api.ala.org.au/occurrences/occurrences/search"
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


def regional_ecosystems(out, E0, N0, zone):
    if (out / "regional_ecosystems.json").exists(): print("  Regional ecosystems: already have it"); return
    print("  Queensland regional ecosystems inside the 2 km window")
    layers = get(RE, {"f": "json"}, "vegetation service")
    if not layers: return
    cands = [l for l in layers.get("layers", []) if "regional ecosystem" in l["name"].lower() and "pre" not in l["name"].lower()]
    if not cands: print("    no regional-ecosystem layer found in the service; layers: " + ", ".join(l["name"] for l in layers.get("layers", [])[:12])); return
    lid = cands[0]["id"]; print(f"    layer: {cands[0]['name']}")
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
    if (out / "ala_species.json").exists(): print("  Atlas of Living Australia: already have it"); return
    print("  Atlas of Living Australia records within about 1 km")
    j = get(ALA, {"q": "*:*", "lat": lat, "lon": lon, "radius": 1.0, "pageSize": 500, "fl": "scientificName,vernacularName,eventDate,decimalLatitude,decimalLongitude,speciesGroup,stateConservation,dataResourceName"}, "ALA")
    if not j or "occurrences" not in j: return
    occ = j["occurrences"]; by = {}
    for o in occ:
        k = o.get("scientificName") or "?"; e = by.setdefault(k, {"common": o.get("vernacularName"), "group": o.get("speciesGroup"), "n": 0, "last": "", "status": o.get("stateConservation")})
        e["n"] += 1; e["last"] = max(e["last"], (o.get("eventDate") or "")[:10])
    (out / "ala_species.json").write_text(json.dumps({"source": "Atlas of Living Australia occurrence records within 1 km (CC BY / CC0, see each record)", "fetched": time.strftime("%Y-%m-%d"), "total": j.get("totalRecords"), "species": by}, indent=0))
    print(f"    {j.get('totalRecords')} records, {len(by)} species")
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


def arcgis_polys(url, layer_id, E0, N0, zone, keep_keys, what, where="1=1"):
    """Query one ArcGIS feature layer for every polygon touching the 2 km window; return features in map coordinates (x east, y south of N0)."""
    env = {"xmin": E0, "ymin": N0 - 2000, "xmax": E0 + 2000, "ymax": N0, "spatialReference": {"wkid": 7800 + zone}}
    j = get(f"{url}/{layer_id}/query", {"where": where, "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": 7800 + zone, "outSR": 7800 + zone,
                                         "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "true", "f": "json", "resultRecordCount": 1000}, what)
    if not j or "features" not in j:
        if j and j.get("error"): print(f"    {what}: server error {j['error'].get('message', '')[:100]}")
        return None
    feats = []
    for f in j["features"]:
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
SLGA = "https://www.asris.csiro.au/arcgis/rest/services/TERN"
# attribute code -> what it is and its unit (Soil and Landscape Grid of Australia, 90 m, version 2 where available)
SLGA_ATTRS = {"CLY": ("Clay", "%"), "SND": ("Sand", "%"), "SLT": ("Silt", "%"), "PHC": ("pH (CaCl2)", ""), "SOC": ("Organic carbon", "%"),
              "AWC": ("Available water capacity", "%"), "BDW": ("Bulk density (whole earth)", "g/cm3"), "DER": ("Depth of regolith", "m"), "DES": ("Depth of soil", "m")}
GRID_ATTRS = ("CLY", "AWC", "SOC")   # sampled on the 5 x 5 grid as well as the centre (the rest: centre only, to keep requests down)


def slga_point(attr, lon, lat):
    """One 'identify' call returns every depth layer of one attribute at a point. Returns {depth_code: value} using the estimated-value layers."""
    import re
    url = f"{SLGA}/{attr}_ACLEP_AU_NAT_C/MapServer/identify"
    j = get(url, {"geometry": json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}), "geometryType": "esriGeometryPoint", "sr": 4326, "layers": "all",
                  "tolerance": 1, "mapExtent": f"{lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}", "imageDisplay": "100,100,96", "returnGeometry": "false", "f": "json"},
            f"soil grid {attr}", tries=(0, 6))
    out = {}
    for r in (j or {}).get("results", []):
        name = r.get("layerName", ""); v = r.get("attributes", {}).get("Pixel Value")
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


IFD = "http://www.bom.gov.au/water/designRainfalls/revised-ifd/"


def ifd(out, lat, lon):
    """Design rainfall depths (mm) for standard durations and annual exceedance probabilities, ARR 2019 (BoM, CC BY 4.0).
    The Bureau sometimes refuses automated requests: if nothing is saved, open the same page in a browser, choose "JSON" under output,
    and save the result as "Site extras/<site>/ifd.json"."""
    if (out / "ifd.json").exists(): print("  Design rainfall (IFD): already have it"); return
    print("  Bureau of Meteorology design rainfall (IFD, ARR 2019)")
    params = {"year": "2016", "coordinate_type": "dd", "latitude": round(lat, 4), "longitude": round(lon, 4), "sdmin": "true", "sdhr": "true", "sdday": "true",
              "user_label": "", "values": "depths", "update": "", "season": "", "output_type": "json"}
    j = None
    for wait in (0, 10):
        if wait: time.sleep(wait)
        try:
            r = requests.get(IFD, params=params, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) design-map", "Accept": "application/json,text/html"}, timeout=120)
            if r.ok and r.text.lstrip().startswith(("{", "[")): j = r.json(); break
            print(f"    IFD: status {r.status_code}, {'not JSON' if r.ok else 'refused'}")
        except Exception as e: print(f"    IFD: {e}")
    if j is None:
        print("    The Bureau did not return data. In a browser open:\n      " + IFD + "?" + "&".join(f"{k}={v}" for k, v in params.items()) + "\n    and save the JSON shown as ifd.json in this site's Site extras folder.")
        return
    (out / "ifd.json").write_text(json.dumps({"source": "Bureau of Meteorology design rainfall (IFD), Australian Rainfall and Runoff 2019 data, CC BY 4.0",
                                             "fetched": time.strftime("%Y-%m-%d"), "lat": lat, "lon": lon, "data": j}, separators=(",", ":")))
    print("    saved the IFD table")
    time.sleep(2)


def silo_full(out, lat, lon):
    if (out / "silo_full.json").exists(): print("  SILO full weather: already have it"); return
    print("  SILO daily weather 1995 to now: rain, max/min temperature, radiation, pan evaporation, FAO56 ETo")
    # SILO comment letters: R rain, X max temp, N min temp, E class-A pan evaporation, J solar radiation, T FAO56 short-crop ET
    j = get(SILO, {"lat": round(lat, 4), "lon": round(lon, 4), "start": "19950101", "finish": time.strftime("%Y%m%d"), "format": "json", "comment": "RXNEJT", "username": EMAIL}, "SILO full")
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


NSW_GEO_WFS = "https://gs.geoscience.nsw.gov.au/geoserver/ows"


def geology(out, state, E0, N0, zone):
    if (out / "geology.json").exists(): print("  Geology: already have it"); return
    print("  Surface geology inside the 2 km window")
    keep = ("name", "lith", "age", "rock", "desc", "unit", "period", "era", "symbol", "type")
    if state == "QLD":
        urls = find_services(QLD_GIS, ["GeoscientificInformation"], r"geolog")
        if not urls: print("    no geology service found under GeoscientificInformation; skipping"); return
        feats, used = None, None
        for u in urls:
            for lid, lname in find_layers(u, r"detailed|surface geology|rock unit|geolog", exclude=(r"label", r"annotation", r"fault", r"structure", r"line", r"point")):
                feats = arcgis_polys(u, lid, E0, N0, zone, keep, f"geology ({lname})")
                if feats: used = f"{u} layer {lid} ({lname})"; break
            if feats: break
        if not feats: print("    no geology polygons came back; skipping"); return
        src = "Detailed surface geology, Geological Survey of Queensland (State of Queensland), CC BY 4.0"
    else:
        # NSW Seamless Geology (Geological Survey of NSW) through its GeoServer WFS. The feature type name is found from GetCapabilities,
        # so a renamed layer only costs a message rather than a crash.
        try:
            caps = requests.get(NSW_GEO_WFS, params={"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"}, headers=H, timeout=120).text
        except Exception as e: print(f"    NSW geology: {e}; skipping"); return
        import re
        names = re.findall(r"<(?:wfs:)?Name>([^<]+)</(?:wfs:)?Name>", caps)
        cand = [n for n in names if re.search(r"seamless", n, re.I) and re.search(r"rock|geol|unit|poly", n, re.I) and not re.search(r"fault|line|point|struct", n, re.I)]
        if not cand: print("    NSW Seamless Geology layer not found in the WFS listing (TODO: check gs.geoscience.nsw.gov.au); skipping"); return
        lon0, lat0 = mga2ll(E0, N0 - 2000, zone); lon1, lat1 = mga2ll(E0 + 2000, N0, zone)
        j = get(NSW_GEO_WFS, {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": cand[0], "outputFormat": "application/json",
                              "srsName": f"EPSG:{7800 + zone}", "bbox": f"{lat0},{lon0},{lat1},{lon1},EPSG:4326", "count": 500}, "NSW geology")
        if not j or "features" not in j: print("    no NSW geology polygons came back; skipping"); return
        feats = []
        for f in j["features"]:
            g = f.get("geometry") or {}; a = f.get("properties", {})
            polys = [g["coordinates"]] if g.get("type") == "Polygon" else g.get("coordinates", []) if g.get("type") == "MultiPolygon" else []
            rings = [[[round(x - E0, 1), round(N0 - y, 1)] for x, y in r] for poly in polys for r in poly]
            feats.append({"attrs": {k: v for k, v in a.items() if any(s in k.lower() for s in keep)}, "rings": rings})
        used = cand[0]; src = "NSW Seamless Geology, Geological Survey of NSW (State of New South Wales), CC BY 4.0"
    (out / "geology.json").write_text(json.dumps({"source": src, "layer": used, "fetched": time.strftime("%Y-%m-%d"), "features": feats}, separators=(",", ":")))
    print(f"    saved {len(feats)} polygons from {used}")
    time.sleep(2)


# Candidate NSW services for Bush Fire Prone Land (tried in order; the first that answers with a matching layer wins)
NSW_BFPL = ["https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/ePlanning/Planning_Portal_Hazard/MapServer",
            "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/EPI_Primary_Planning_Layers/MapServer",
            "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Bushfire_Prone_Land/MapServer"]


def hazard(out, state, E0, N0, zone):
    if (out / "hazard.json").exists(): print("  Hazard mapping: already have it"); return
    print("  Bushfire hazard and vegetation-clearing rule mapping inside the 2 km window")
    layers_out = []
    if state == "QLD":
        # Bushfire hazard area (State Planning Policy natural hazards mapping)
        urls = find_services(QLD_GIS, ["PlanningCadastre", "Boundaries", "Environment"], r"bushfire|planningpolicy|hazard")
        got = False
        for u in urls:
            for lid, lname in find_layers(u, r"bushfire", exclude=(r"label", r"line")):
                feats = arcgis_polys(u, lid, E0, N0, zone, ("haz", "class", "cat", "desc", "type", "name", "potential", "intensity"), f"bushfire hazard ({lname})")
                if feats is not None:
                    layers_out.append({"kind": "bushfire", "name": lname, "source": "Queensland bushfire hazard area mapping (State Planning Policy), State of Queensland, CC BY 4.0", "features": feats}); got = True; break
            if got: break
        if not got: print("    bushfire hazard layer not found (TODO: check the SPP mapping service name); continuing")
        # Regulated vegetation management map (categories A, B, C, R, X)
        for lid, lname in find_layers(RE, r"regulated vegetation management map", exclude=(r"label", r"pre-?clear", r"essential", r"watercourse", r"wetland")):
            feats = arcgis_polys(RE, lid, E0, N0, zone, ("cat", "class", "rvm", "desc", "type", "name", "status"), f"regulated vegetation ({lname})")
            if feats is not None:
                layers_out.append({"kind": "regulated_vegetation", "name": lname, "source": "Regulated vegetation management map (Vegetation Management Act 1999), State of Queensland, CC BY 4.0", "features": feats}); break
    else:
        got = False
        for u in NSW_BFPL:
            for lid, lname in find_layers(u, r"bush ?fire prone", exclude=(r"label",)):
                feats = arcgis_polys(u, lid, E0, N0, zone, ("cat", "class", "desc", "type", "name", "veg"), f"NSW bush fire prone land ({lname})")
                if feats is not None:
                    layers_out.append({"kind": "bushfire", "name": lname, "source": "NSW Bush Fire Prone Land map (NSW Rural Fire Service / Planning), CC BY 4.0", "features": feats}); got = True; break
            if got: break
        if not got: print("    NSW Bush Fire Prone Land layer not found at the known addresses (TODO: confirm the service on SEED); continuing")
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
        geology(out, state, E0, N0, zone)
        hazard(out, state, E0, N0, zone)
    probe_qld_elevation()
    print('\nDone. Tell Claude: "site extras are ready".')


if __name__ == "__main__":
    main()

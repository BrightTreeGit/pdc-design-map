#!/usr/bin/env python3
"""
fetch_site_extras.py: three public data pulls for every design-map site, in one run.

  1. SILO daily rainfall and minimum temperature, 1995 to now (CC BY 4.0) -> the 30-year tank test on every site
  2. Queensland Regional Ecosystems (Qld Herbarium, CC BY) -> the natural vegetation type of each Queensland block
  3. Atlas of Living Australia species records within about 1 km of each block (CC BY / CC0 mixed) -> koalas, birds, frogs, weeds

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
    probe_qld_elevation()
    print('\nDone. Tell Claude: "site extras are ready".')


if __name__ == "__main__":
    main()

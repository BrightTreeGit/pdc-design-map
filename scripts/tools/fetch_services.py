#!/usr/bin/env python3
"""
fetch_services.py: public power network (Energex open data extract, Sep 2022) for the Queensland design-map sites.

Downloads poles, pillars, substations and overhead/underground lines (low voltage to 132 kV) inside each site's
map window and saves them in the map's own coordinates, ready to drop into map/sites/<site>/services.json.
Only public, indicative street-level data: house connections inside a block are not in it.

  py fetch_services.py                 (all Queensland sites)
  py fetch_services.py annwn           (one site)

Saves to "<this folder>/../Services data/<site>/services.json". Gentle on the server: small pages, a pause between.
"""
import json, sys, time
from pathlib import Path
import requests

URL = "https://services.arcgis.com/bfVzktoY0OhzQCDj/ArcGIS/rest/services/Network_Energex/FeatureServer"
H = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
# site id: (E0, N0 of the map's 2 km window in MGA zone 56, half-width in m of the area to fetch around the centre)
SITES = {
    "annwn": (518086.0, 6954895.0, 400),           # small suburban block: 800 m square is plenty
    "bright-tree": (492000.0, 7043000.0, 1000),
    "bellbunya": (484159.0, 7071282.0, 1000),
    "noosa-forest-retreat": (483394.0, 7096927.0, 1000),
}
LAYERS = {0: ("subs", None), 1: ("subs", None), 2: ("poles", None), 3: ("pillars", None),
          4: ("lines", ("132kV", 0)), 5: ("lines", ("132kV", 1)), 6: ("lines", ("110kV", 0)), 7: ("lines", ("110kV", 1)),
          8: ("lines", ("33kV", 0)), 9: ("lines", ("33kV", 1)), 10: ("lines", ("11kV", 0)), 11: ("lines", ("11kV", 1)),
          12: ("lines", ("LV", 0)), 13: ("lines", ("LV", 1))}


def query(layer, env, sr):
    feats, off = [], 0
    while True:
        p = {"where": "1=1", "geometry": json.dumps(env), "geometryType": "esriGeometryEnvelope", "inSR": sr, "outSR": sr,
             "spatialRel": "esriSpatialRelIntersects", "outFields": "OBJECTID", "returnGeometry": "true", "f": "json",
             "resultOffset": off, "resultRecordCount": 1000}
        j = None
        for wait in (0, 5, 20, 60):
            if wait: time.sleep(wait)
            try:
                r = requests.get(f"{URL}/{layer}/query", params=p, headers=H, timeout=120)
                j = r.json()
                if "error" in j: print(f"    layer {layer}: {j['error'].get('message')}"); j = None; break
                break
            except Exception as e:
                print(f"    layer {layer}: {e}")
        if not j: return None
        fs = j.get("features", []); feats += fs; time.sleep(1)
        if not j.get("exceededTransferLimit") or not fs: return feats
        off += len(fs)


def main():
    want = sys.argv[1:] or list(SITES)
    root = Path(__file__).resolve().parents[1] / "Services data"
    for site in want:
        E0, N0, half = SITES[site]
        cx, cy = E0 + 1000, N0 - 1000
        env = {"xmin": cx - half, "ymin": cy - half, "xmax": cx + half, "ymax": cy + half}
        print(f"{site}: fetching the power network within {half} m of the centre")
        out = {"lines": [], "poles": [], "pillars": [], "subs": []}
        sr_used = None
        for layer, (key, kind) in LAYERS.items():
            feats = None
            for sr in (7856, 28356):            # GDA2020 first, then GDA94 (about 1.8 m apart)
                feats = query(layer, dict(env, spatialReference={"wkid": sr}), sr)
                if feats is not None: sr_used = sr_used or sr; break
            if feats is None: print(f"  layer {layer} failed"); continue
            for f in feats:
                g = f.get("geometry") or {}
                if key == "lines":
                    for path in g.get("paths", []):
                        out["lines"].append({"v": kind[0], "u": kind[1], "p": [[round(x - E0, 1), round(N0 - y, 1)] for x, y in path]})
                elif "x" in g:
                    out[key].append([round(g["x"] - E0, 1), round(N0 - g["y"], 1)])
                elif "rings" in g:                # substations drawn as areas: keep the centre
                    r = g["rings"][0]; x = sum(q[0] for q in r) / len(r); y = sum(q[1] for q in r) / len(r)
                    out[key].append([round(x - E0, 1), round(N0 - y, 1)])
            print(f"  layer {layer:2d} {key:7s} {len(feats)}")
        res = {"source": "Energex distribution network, open data extract of Sep 2022 (indicative)", "fetched": time.strftime("%Y-%m-%d"),
               "srid": sr_used, "power": out}
        d = root / site; d.mkdir(parents=True, exist_ok=True)
        (d / "services.json").write_text(json.dumps(res))
        print(f"  saved {d / 'services.json'}: {len(out['lines'])} line sections, {len(out['poles'])} poles, {len(out['pillars'])} pillars\n")
    print('Done. Tell Claude: "services data is ready".')


if __name__ == "__main__":
    main()

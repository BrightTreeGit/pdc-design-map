"""Download NSW's free scanned historical aerial photos (one best frame per flight date) for our NSW sites.
Usage:  py get_nsw_scans.py            (all three sites)
        py get_nsw_scans.py regenify   (one site)
Photos land in history_nsw/<site>/scans/ next to this script, named <year>_<frame>.jpg. About 7 MB each.
Licence: CC-BY, NSW Spatial Services. Already-downloaded photos are skipped, so it is safe to run again."""
import json, sys, time, pathlib, urllib.request
HERE = pathlib.Path(__file__).resolve().parent
F = json.loads((HERE / "nsw_scans_frames.json").read_text())
URL = F["download"]
sites = sys.argv[1:] or list(F["best_per_date"])
for site in sites:
    out = HERE / "history_nsw" / site / "scans"; out.mkdir(parents=True, exist_ok=True)
    print(f"\n{site}: {len(F['best_per_date'][site])} photos")
    for date, scale, film, img in F["best_per_date"][site]:
        dest = out / f"{date[:4]}_{img}.jpg"
        if dest.exists() and dest.stat().st_size > 100000:
            print(f"  {date} already here"); continue
        for wait in (0, 10, 30):
            if wait: print(f"   trying again in {wait} s"); time.sleep(wait)
            try:
                req = urllib.request.Request(URL.format(film=film, image=img), headers={"User-Agent": "pdc-design-map"})
                with urllib.request.urlopen(req, timeout=180) as r: data = r.read()
                if data[:2] == b"\xff\xd8":
                    dest.write_bytes(data); print(f"  {date} ({scale}): {len(data)/1e6:.1f} MB"); break
                print(f"   {img}: not a photo came back")
            except Exception as e:
                print(f"   {img}: {e}")
print("\nDone. Tell Claude the NSW scans are downloaded.")

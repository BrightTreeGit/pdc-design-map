#!/usr/bin/env python3
"""
fetch_outlook.py: the seasonal weather picture for every design-map site, in one run. Run it once a month.

What it collects (nothing here is private: these are national and world climate feeds, read at each site's grid point):

  1. Climate drivers, shared by all sites -> "Site extras/_drivers/drivers.json"
       - Southern Oscillation Index (SOI): the monthly series and the current SOI phase (1-5) from Long Paddock
         (Queensland Government, CC BY 4.0). The 30-day average SOI is also read when the "latest" file answers.
       - ENSO (El Nino / La Nina), Indian Ocean Dipole and other driver status: the key sentences of the Bureau of
         Meteorology's Climate Driver Update page. The Bureau's website sometimes refuses scripts; then the file
         says "see page" with the address.
       - Nino 3.4 sea-surface temperature anomaly and the Oceanic Nino Index from NOAA (USA) as a dependable
         second opinion on the ENSO state. These are plain text files that have been at the same address for years.
  2. Bureau of Meteorology long-range (seasonal) outlook -> "Site extras/<site>/outlook.json"
       - The Bureau's written outlook (issued fortnightly): headline, issue date and the rainfall and temperature
         sentences that mention the site's state. This comes from the Bureau's ordinary web pages.
       - The per-point numbers (chance of above-median rain for the next month and next three months, chance of
         above-median maximum and minimum temperature) live behind the Bureau's interactive map
         (https://www.bom.gov.au/climate/outlooks/). No documented data feed for that map was found when this tool was
         written (24 Oct 2026), so the tool looks for one each run (it scans the page for JSON addresses and saves any
         that answer) and otherwise leaves a small template in outlook.json that Brett can fill in by hand: open the
         map, click the site, and type the four percentages and the issue date. Hand-typed numbers are kept on later
         runs until their issue date is older than the Bureau's current outlook.
  3. Ten-day forecast at the site -> the "short_range" part of outlook.json
       - Open-Meteo (free, no key): daily rain total, maximum and minimum temperature for the next 10 days, from a
         blend of the best models for the point (the Bureau's ACCESS-G among them). Labelled with its issue time.
       - Optionally the Bureau's own 7-day town forecast (the "precis" XML on the Bureau's FTP server) for the nearest
         forecast town, when the FTP server answers. Many home networks block FTP; the tool just notes it and moves on.

Every run overwrites outlook.json and also appends one line to "Site extras/<site>/outlook_history.jsonl"
(JSON Lines: one complete record per line, never rewritten), so the forecasts can be scored against the rain that
actually fell, later.

  py fetch_outlook.py              (all sites)
  py fetch_outlook.py bright-tree  (one or more sites)

Gentle on the servers: a short pause between requests and three tries on failure. If a source does not answer, the
tool says so in plain words, records what it could, and carries on. The sites and their coordinates come from
fetch_site_extras.py in this folder (SITES), so one list serves every tool.
"""
import json, os, re, sys, time, html as htmlmod
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("The 'requests' package is missing. Double-click '0 - Setup' once, then run this again."); sys.exit(1)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    from fetch_site_extras import SITES, get      # site id: (lat, lon, state, E0, N0, zone); get() = polite JSON fetch with retries
except Exception as e:                            # keep working even if that file is missing or broken
    print(f"(could not read SITES from fetch_site_extras.py: {e}; using the built-in copy)")
    SITES = {
        "bright-tree": (-26.7434, 152.92886, "QLD", 492000.0, 7043000.0, 56),
        "bellbunya": (-26.49107, 152.85225, "QLD", 484159.0, 7071282.0, 56),
        "noosa-forest-retreat": (-26.25641, 152.84421, "QLD", 483394.0, 7096927.0, 56),
        "annwn": (-27.53861, 153.19329, "QLD", 518086.0, 6954895.0, 56),
        "willow-vale": (-31.91075, 151.7787, "NSW", 383492.0, 6469820.0, 56),
        "nimbin": (-28.5654, 153.25403, "NSW", 523889.0, 6841186.0, 56),
        "nac": (-32.67477, 152.04486, "NSW", 409432.0, 6385368.0, 56),
        "regenify": (-28.53412, 153.41612, "NSW", 539619.0, 6844643.0, 56),
    }
    get = None

H = {"User-Agent": "PDC-Design-Map/1.0 (permaculture course)"}
# The Bureau's web firewall answers plain scripts with an HTML page or a refusal; looking like a browser usually gets the page.
BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
           "Accept": "text/html,application/json,text/plain,*/*;q=0.8", "Accept-Language": "en-AU,en;q=0.9"}
TODAY = time.strftime("%Y-%m-%d")
NOW = datetime.now(timezone.utc).astimezone().isoformat(timespec="minutes")

# ---- Addresses (checked 24 Oct 2026; see the note next to each)
# Long Paddock lists these six plain-text files on https://www.longpaddock.qld.gov.au/soi/soi-data-files/ (checked 24 Oct 2026).
LP = "https://data.longpaddock.qld.gov.au/SeasonalClimateOutlook/SouthernOscillationIndex/SOIDataFiles/"
SOI_MONTHLY = LP + "MonthlySOI1887-1989Base.txt"         # monthly SOI, 1887-1989 base (the base Long Paddock's phase system uses)
SOI_PHASE = LP + "MonthlySOIPhase1887-1989Base.txt"      # monthly SOI with the phase number 1-5 for each month
SOI_LATEST = LP + "LatestSOI1887-1989Base.txt"           # yesterday's daily SOI, 30- and 90-day means, last three monthly means
SOI_PHASE_NAMES = {1: "consistently negative", 2: "consistently positive", 3: "rapidly falling", 4: "rapidly rising", 5: "consistently near zero"}
# NOAA Climate Prediction Center index files (listed on https://www.cpc.ncep.noaa.gov/data/indices/, both read live on 24 Oct 2026):
NINO34 = "https://www.cpc.ncep.noaa.gov/data/indices/detrend.nino34.ascii.txt"   # columns: YR MON TOTAL ClimAdjust ANOM (monthly, ERSST)
ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"                   # columns: SEAS YR TOTAL ANOM (3-month running, e.g. JAS 2026)
# Bureau of Meteorology pages (HTML). The long-range forecast text is republished fortnightly; the archive index lists every issue.
BOM_ENSO = "https://www.bom.gov.au/climate/enso/"                                   # Climate Driver Update (current)
BOM_OUTLOOK = "https://www.bom.gov.au/climate/ahead/outlooks/"                      # current written long-range forecast
BOM_OUTLOOK_ARCHIVE = "https://www.bom.gov.au/climate/ahead/outlooks/archive.shtml"  # links like .../archive/20261015-outlook.shtml (read 24 Oct 2026)
BOM_MAP = "https://www.bom.gov.au/climate/outlooks/"                                 # interactive point outlook (no documented data feed found)
BOM_MAP_RAIN = BOM_MAP + "#/rainfall/median"
# Open-Meteo forecast API (https://open-meteo.com/en/docs): no key, daily arrays, forecast_days up to 16, timezone required with daily.
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
# Bureau precis (7-day town) forecasts, state-wide XML on the Bureau's public FTP server (product ids used by the weatherOz package).
PRECIS = {"QLD": "IDQ11295", "NSW": "IDN11060"}
PRECIS_FTP = "ftp.bom.gov.au"; PRECIS_DIR = "/anon/gen/fwo/"
# Nearest Bureau forecast towns to try, in order (the first one found in the state file is used).
PRECIS_TOWNS = {"bright-tree": ["Maleny", "Nambour", "Sunshine Coast"], "bellbunya": ["Eumundi", "Cooroy", "Nambour", "Sunshine Coast"],
                "noosa-forest-retreat": ["Pomona", "Cooroy", "Tewantin", "Noosa Heads", "Sunshine Coast"], "annwn": ["Cleveland", "Redland Bay", "Brisbane"],
                "willow-vale": ["Gloucester", "Dungog", "Taree"], "nimbin": ["Nimbin", "Lismore", "Kyogle"], "nac": ["Bulahdelah", "Tea Gardens", "Nelson Bay", "Newcastle"], "regenify": ["Mullumbimby", "Byron Bay", "Lismore"]}
STATE_WORDS = {"QLD": ["queensland", "sunshine coast", "south-east queensland", "southeast queensland", "eastern australia", "east coast", "the east"],
               "NSW": ["new south wales", "nsw", "eastern australia", "east coast", "the east", "south-east", "southeast"]}


# ---------------------------------------------------------------- small helpers
def fetch_text(url, what, headers=H, tries=(0, 8, 30), timeout=90, params=None):
    """Plain GET with retries; returns the body text or None. Says what went wrong in plain words."""
    for wait in tries:
        if wait: print(f"    retrying {what} in {wait} s"); time.sleep(wait)
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (403, 429):
                print(f"    {what}: the server refused the request (status {r.status_code})"); continue
            if not r.ok: print(f"    {what}: status {r.status_code}"); continue
            return r.text
        except requests.exceptions.ConnectTimeout: print(f"    {what}: no answer (connection timed out)")
        except requests.exceptions.ConnectionError as e: print(f"    {what}: could not connect ({str(e)[:80]})")
        except Exception as e: print(f"    {what}: {str(e)[:120]}")
    return None


def fetch_json(url, params, what):
    if get: return get(url, params, what)
    t = fetch_text(url, what, params=params)
    try: return json.loads(t) if t else None
    except Exception: print(f"    {what}: not JSON"); return None


def save_raw(folder, name, text):
    """Keep a copy of whatever a server sent, so nothing is lost even if the parser below misreads it."""
    try: (folder / name).write_text(text, encoding="utf-8")
    except Exception as e: print(f"    could not save {name}: {e}")


def strip_html(s):
    s = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?is)</(p|h\d|li|div|td|tr|section)>|<br\s*/?>", " | ", s)   # keep paragraph breaks so headings do not run into sentences
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = htmlmod.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"(\s*\|\s*)+", " | ", s).strip(" |")


def sentences(text):
    out = []
    for block in text.split(" | "):
        out += [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z])", block) if len(x.strip()) > 20 and re.search(r"[.!?]$", x.strip())]
    return out


def issued_date(text):
    m = re.search(r"[Ii]ssued(?: on)?\s+(\d{1,2}\s+\w+\s+\d{4})", text)
    if not m: return None
    try: return datetime.strptime(m.group(1), "%d %B %Y").strftime("%Y-%m-%d")
    except ValueError: return m.group(1)


def nums(tokens):
    out = []
    for t in tokens:
        try: out.append(float(t))
        except ValueError: return None
    return out


# ---------------------------------------------------------------- 1. climate drivers (shared)
def parse_soi_rows(text):
    """Long Paddock's monthly files come as rows of numbers. Two layouts are handled: 'Year Jan ... Dec' (13 numbers)
    and 'Year Month Value [Phase]' (3 or 4 numbers). Missing values (-99.9 or blank) are dropped.
    Returns {(year, month): (value, phase or None)} without having to know which layout arrived."""
    rows = {}
    for line in text.splitlines():
        v = nums(line.replace(",", " ").split())
        if not v: continue
        if len(v) >= 13 and 1800 < v[0] < 2200:
            for m, x in enumerate(v[1:13], 1):
                if -90 < x < 90: rows[(int(v[0]), m)] = (x, None)
        elif len(v) in (3, 4) and 1800 < v[0] < 2200 and 1 <= v[1] <= 12:
            if -90 < v[2] < 90: rows[(int(v[0]), int(v[1]))] = (v[2], int(v[3]) if len(v) == 4 and 1 <= v[3] <= 5 else None)
        elif len(v) in (2, 3) and 180000 < v[0] < 220000:          # YYYYMM value [phase]
            y, m = divmod(int(v[0]), 100)
            if 1 <= m <= 12 and -90 < v[1] < 90: rows[(y, m)] = (v[1], int(v[2]) if len(v) == 3 and 1 <= v[2] <= 5 else None)
    return rows


def soi(drv):
    print("  Southern Oscillation Index (Long Paddock)")
    out = {"source": "Southern Oscillation Index, Long Paddock, Queensland Government (CC BY 4.0), 1887-1989 base", "files": [SOI_MONTHLY, SOI_PHASE, SOI_LATEST]}
    series, phases = {}, {}
    t = fetch_text(SOI_MONTHLY, "SOI monthly")
    if t: save_raw(drv, "soi_monthly.txt", t); series = parse_soi_rows(t)
    t = fetch_text(SOI_PHASE, "SOI phase")
    if t:
        save_raw(drv, "soi_phase.txt", t)
        for k, (val, ph) in parse_soi_rows(t).items():
            if ph: phases[k] = ph
            series.setdefault(k, (val, ph))
    if series:
        keys = sorted(series)
        last = keys[-1]
        recent = [{"month": f"{y:04d}-{m:02d}", "soi": round(series[(y, m)][0], 1), "phase": phases.get((y, m))} for y, m in keys[-24:]]
        ph = phases.get(last)
        out.update({"latest_month": f"{last[0]:04d}-{last[1]:02d}", "latest_soi": round(series[last][0], 1), "phase": ph,
                    "phase_name": SOI_PHASE_NAMES.get(ph), "last_24_months": recent, "months_in_series": len(keys)})
        print(f"    latest month {out['latest_month']}: SOI {out['latest_soi']}" + (f", phase {ph} ({SOI_PHASE_NAMES.get(ph)})" if ph else ""))
    else:
        out["note"] = "Long Paddock did not answer; see " + SOI_MONTHLY
        print("    no SOI data this run")
    t = fetch_text(SOI_LATEST, "SOI latest", tries=(0, 8))
    if t:
        save_raw(drv, "soi_latest.txt", t)
        out["latest_text"] = t.strip()[:600]
        m = re.search(r"30[- ]day[^-\d]*(-?\d+\.\d+)", t, re.I)
        if m: out["soi_30_day_mean"] = float(m.group(1)); print(f"    30-day mean SOI {m.group(1)}")
    time.sleep(2)
    return out


def noaa(drv):
    print("  Nino 3.4 and Oceanic Nino Index (NOAA Climate Prediction Center)")
    out = {"source": "NOAA Climate Prediction Center, ERSST Nino 3.4 monthly anomaly and Oceanic Nino Index (public domain)", "files": [NINO34, ONI]}
    t = fetch_text(NINO34, "Nino 3.4")
    if t:
        save_raw(drv, "nino34.txt", t)
        rows = [nums(l.split()) for l in t.splitlines()]
        rows = [r for r in rows if r and len(r) >= 5 and 1900 < r[0] < 2200]
        if rows:
            out["nino34_last_12"] = [{"month": f"{int(r[0]):04d}-{int(r[1]):02d}", "anomaly_c": round(r[4], 2)} for r in rows[-12:]]
            r = rows[-1]; out["nino34_latest_month"] = f"{int(r[0]):04d}-{int(r[1]):02d}"; out["nino34_latest_anomaly_c"] = round(r[4], 2)
            print(f"    Nino 3.4 {out['nino34_latest_month']}: {r[4]:+.2f} C")
    t = fetch_text(ONI, "ONI")
    if t:
        save_raw(drv, "oni.txt", t)
        oni = []
        for l in t.splitlines():
            p = l.split()
            if len(p) == 4 and p[1].isdigit():
                try: oni.append({"season": p[0], "year": int(p[1]), "anomaly_c": float(p[3])})
                except ValueError: pass
        if oni:
            out["oni_last_8"] = oni[-8:]; a = oni[-1]["anomaly_c"]
            out["oni_latest"] = oni[-1]
            out["enso_state_from_oni"] = "El Nino range (+0.5 C or more)" if a >= 0.5 else "La Nina range (-0.5 C or less)" if a <= -0.5 else "neutral range"
            print(f"    ONI {oni[-1]['season']} {oni[-1]['year']}: {a:+.2f} C -> {out['enso_state_from_oni']}")
    if "oni_latest" not in out and "nino34_latest_month" not in out: out["note"] = "NOAA did not answer this run"
    time.sleep(2)
    return out


KEY_DRIVER = re.compile(r"(ENSO|El Niño|El Nino|La Niña|La Nina|Indian Ocean Dipole|IOD|Southern Annular Mode|SAM\b|Madden|MJO|neutral|Watch|Alert|sea surface temperature)", re.I)


def bom_enso(drv):
    print("  Bureau of Meteorology Climate Driver Update (ENSO, IOD, SAM)")
    out = {"source": "Bureau of Meteorology Climate Driver Update", "url": BOM_ENSO}
    t = fetch_text(BOM_ENSO, "Climate Driver Update", headers=BROWSER, tries=(0, 10))
    if not t or "<html" not in t.lower():
        out["status"] = "see page"; out["note"] = "The Bureau's site did not give the page to this tool. Open the address in a browser for the current ENSO and IOD status."
        print("    the Bureau did not give the page; recorded 'see page' with the address"); return out
    save_raw(drv, "bom_climate_driver_update.html", t)
    text = strip_html(t)
    out["issued"] = issued_date(text)
    picks = [s for s in sentences(text) if KEY_DRIVER.search(s)]
    seen, keep = set(), []
    for s in picks:
        k = s[:80]
        if k not in seen and not s.lower().startswith(("the bureau", "subscribe", "this page")): seen.add(k); keep.append(s)
    out["key_sentences"] = keep[:14]
    out["status"] = "ok" if keep else "see page"
    print(f"    issued {out['issued'] or '?'}; kept {len(out['key_sentences'])} key sentences")
    time.sleep(2)
    return out


def latest_outlook_page():
    """The Bureau's current written outlook, with its dated archive copy as the fallback (the archive index links every issue
    as .../archive/YYYYMMDD-outlook.shtml; the newest date wins)."""
    t = fetch_text(BOM_OUTLOOK, "long-range forecast page", headers=BROWSER, tries=(0, 10))
    if t and "issued" in t.lower(): return BOM_OUTLOOK, t
    idx = fetch_text(BOM_OUTLOOK_ARCHIVE, "long-range forecast archive", headers=BROWSER, tries=(0, 10))
    if idx:
        dates = sorted(set(re.findall(r"(\d{8})-outlook\.shtml", idx)))
        if dates:
            url = f"{BOM_OUTLOOK}archive/{dates[-1]}-outlook.shtml"
            t = fetch_text(url, "latest archived outlook", headers=BROWSER, tries=(0, 10))
            if t: return url, t
    return None, None


def bom_outlook_text(drv):
    print("  Bureau of Meteorology written long-range forecast")
    out = {"source": "Bureau of Meteorology long-range forecast (ACCESS-S), written summary", "url": BOM_OUTLOOK}
    url, t = latest_outlook_page()
    if not t:
        out["status"] = "see page"; out["note"] = "The Bureau's site did not give the page to this tool; read it in a browser."
        print("    the Bureau did not give the page; recorded 'see page'"); return out
    save_raw(drv, "bom_long_range_forecast.html", t)
    out["url"] = url
    text = strip_html(t)
    out["issued"] = issued_date(text)
    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", t); out["headline"] = strip_html(m.group(1)) if m else None
    # The page is laid out as h2 "Rainfall—Summary" / h3 one-line verdict / paragraphs, then h2 "Temperature—Summary" (seen 24 Oct 2026).
    parts = re.split(r"(?is)<h2[^>]*>", t)
    for p in parts[1:]:
        title = strip_html(p.split("</h2>", 1)[0]).lower()
        body = strip_html(p.split("</h2>", 1)[1] if "</h2>" in p else p)
        sub = re.search(r"(?is)<h3[^>]*>(.*?)</h3>", p)
        key = "rainfall" if title.startswith("rainfall") else "temperature" if title.startswith("temperature") else None
        if key:
            out[key + "_verdict"] = strip_html(sub.group(1)) if sub else None
            out[key + "_sentences"] = sentences(body)[:12]
    out["status"] = "ok" if out.get("rainfall_sentences") else "page read but sections not recognised"
    print(f"    {out.get('headline') or '?'} (issued {out.get('issued') or '?'})")
    time.sleep(2)
    return out


def bom_point_feed_probe(drv):
    """Look for a data feed behind the Bureau's interactive outlook map. No documented one was found (24 Oct 2026), so this scans
    the page and its scripts for JSON addresses and saves any that answer with JSON, to be read by hand next time Claude looks."""
    print("  Looking for a data feed behind the Bureau's interactive outlook map")
    found = {}
    page = fetch_text(BOM_MAP, "interactive outlook page", headers=BROWSER, tries=(0,))
    if not page: print("    the page did not come through; skipping"); return found
    save_raw(drv, "bom_outlook_map_page.html", page)
    srcs = re.findall(r"""(?i)src=["']([^"']+\.js[^"']*)["']""", page)
    urls = set(re.findall(r"""https?://[^\s"'<>]+\.json[^\s"'<>]*""", page))
    for s in srcs[:6]:
        s = s if s.startswith("http") else requests.compat.urljoin(BOM_MAP, s)
        js = fetch_text(s, "map script", headers=BROWSER, tries=(0,), timeout=60)
        if not js: continue
        for u in re.findall(r"""["']((?:https?:)?/?[^"'\s]*(?:\.json|/data/|/api/)[^"'\s]*)["']""", js):
            urls.add(u if u.startswith("http") else requests.compat.urljoin(BOM_MAP, u))
    urls = sorted(u for u in urls if "bom.gov.au" in u and "{" not in u)[:15]
    for u in urls:
        t = fetch_text(u, "candidate feed", headers=BROWSER, tries=(0,), timeout=60)
        if t and t.lstrip().startswith(("{", "[")):
            name = "bom_feed_" + re.sub(r"[^A-Za-z0-9]+", "_", u.split("bom.gov.au", 1)[1])[:60] + ".json"
            save_raw(drv, name, t); found[u] = name
    print(f"    {len(urls)} candidate addresses looked at, {len(found)} answered with JSON" + (" (saved in _drivers for a look)" if found else ""))
    return found


# ---------------------------------------------------------------- 2. per-site outlook
HAND_TEMPLATE = {"issued": None, "rain_next_month_pct_above_median": None, "rain_next_3_months_pct_above_median": None,
                 "tmax_next_3_months_pct_above_median": None, "tmin_next_3_months_pct_above_median": None, "entered_by_hand": True}


def bom_for_site(site, state, national, old):
    """The Bureau's outlook as it applies to one site: the state-relevant sentences from the written forecast, plus the
    point percentages (typed by hand from the interactive map until a feed is found)."""
    words = STATE_WORDS[state]
    pick = lambda ss: [s for s in (ss or []) if any(w in s.lower() for w in words)] or (ss or [])[:3]
    b = {"source": national.get("source"), "url": national.get("url"), "status": national.get("status"), "note": national.get("note"),
         "issued": national.get("issued"), "headline": national.get("headline"),
         "rainfall_verdict": national.get("rainfall_verdict"), "rainfall_for_state": pick(national.get("rainfall_sentences")),
         "temperature_verdict": national.get("temperature_verdict"), "temperature_for_state": pick(national.get("temperature_sentences"))}
    prev = (old or {}).get("bom_outlook", {}).get("point", {})
    keep = prev if prev.get("issued") and prev.get("rain_next_3_months_pct_above_median") is not None and \
        (not national.get("issued") or str(prev["issued"]) >= str(national["issued"])) else None
    b["point"] = keep or dict(HAND_TEMPLATE)
    b["point_how_to"] = (f"Open {BOM_MAP_RAIN}, click the property on the map, and type the four 'chance of above median' percentages "
                         f"and the issue date into 'point' above (a number like 65 means 65%). They stay until the Bureau's next issue.")
    if keep: print(f"    point numbers typed by hand on {prev['issued']} kept (still current)")
    elif prev.get("issued"): print(f"    hand-typed point numbers from {prev['issued']} are older than the Bureau's {national.get('issued')} issue; cleared for retyping")
    else: print("    no point numbers yet: see point_how_to in outlook.json")
    return b


def open_meteo(lat, lon):
    print("  Open-Meteo 10-day forecast at the site")
    j = fetch_json(OPEN_METEO, {"latitude": round(lat, 4), "longitude": round(lon, 4), "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                                "forecast_days": 10, "timezone": "Australia/Brisbane"}, "Open-Meteo")
    if not j or "daily" not in j:
        print("    no forecast this run"); return {"source": "Open-Meteo (ECMWF/BoM blend)", "status": "no answer", "url": OPEN_METEO}
    d = j["daily"]
    days = [{"date": t, "rain_mm": r, "tmax_c": hi, "tmin_c": lo} for t, r, hi, lo in
            zip(d.get("time", []), d.get("precipitation_sum", []), d.get("temperature_2m_max", []), d.get("temperature_2m_min", []))]
    rain = [x["rain_mm"] for x in days if x["rain_mm"] is not None]
    out = {"source": f"Open-Meteo (ECMWF/BoM blend), issued {NOW}", "issued": NOW, "url": OPEN_METEO, "grid_point": [j.get("latitude"), j.get("longitude")],
           "days": days, "total_rain_mm_10_days": round(sum(rain), 1) if rain else None,
           "total_rain_mm_7_days": round(sum(rain[:7]), 1) if rain else None, "status": "ok"}
    print(f"    {len(days)} days, {out['total_rain_mm_10_days']} mm over 10 days")
    time.sleep(1)
    return out


_precis_cache = {}


def precis_xml(state):
    """State-wide 7-day town forecasts from the Bureau's FTP server (one download per state per run). Returns the XML text or None."""
    if state in _precis_cache: return _precis_cache[state]
    pid = PRECIS[state]; text = None
    try:
        import ftplib, io
        ftp = ftplib.FTP(PRECIS_FTP, timeout=30); ftp.login(); ftp.cwd(PRECIS_DIR)
        buf = io.BytesIO(); ftp.retrbinary(f"RETR {pid}.xml", buf.write); ftp.quit()
        text = buf.getvalue().decode("utf-8", "replace")
    except Exception as e:
        print(f"    Bureau FTP ({pid}.xml): {str(e)[:80]} (FTP is often blocked on home networks; not a problem)")
        t = fetch_text(f"https://www.bom.gov.au/fwo/{pid}.xml", f"Bureau {pid}.xml over the web", headers=BROWSER, tries=(0,), timeout=60)
        if t and t.lstrip().startswith("<?xml"): text = t
    _precis_cache[state] = text
    return text


def bom_precis(site, state, out_dir):
    print("  Bureau 7-day town forecast (optional)")
    xml = precis_xml(state)
    if not xml: return {"source": f"Bureau of Meteorology precis forecast {PRECIS[state]}", "status": "not available this run"}
    save_raw(out_dir.parent / "_drivers", f"bom_precis_{PRECIS[state]}.xml", xml)
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
    except Exception as e:
        print(f"    could not read the XML: {e}"); return {"source": f"Bureau of Meteorology precis forecast {PRECIS[state]}", "status": "unreadable"}
    issued = (root.find(".//issue-time-local").text if root.find(".//issue-time-local") is not None else None)
    areas = {a.get("description"): a for a in root.iter("area") if a.get("type") == "location"}
    town = next((t for t in PRECIS_TOWNS.get(site, []) if t in areas), None)
    if not town:
        print(f"    none of {PRECIS_TOWNS.get(site)} is in the {state} town list"); return {"source": f"Bureau of Meteorology precis forecast {PRECIS[state]}", "status": "town not found"}
    days = []
    for p in areas[town].findall("forecast-period"):
        e = {el.get("type"): (el.text or "").strip() for el in p}
        days.append({"date": (p.get("start-time-local") or "")[:10], "precis": e.get("precis"), "tmin_c": e.get("air_temperature_minimum"),
                     "tmax_c": e.get("air_temperature_maximum"), "rain_range_mm": e.get("precipitation_range"), "chance_of_rain": e.get("probability_of_precipitation")})
    print(f"    {town}: {len(days)} days, issued {issued}")
    return {"source": f"Bureau of Meteorology 7-day forecast for {town} ({PRECIS[state]}), issued {issued}", "issued": issued, "town": town, "days": days, "status": "ok"}


# ---------------------------------------------------------------- main
def main():
    want = sys.argv[1:] or list(SITES)
    bad = [s for s in want if s not in SITES]
    if bad: print(f"Unknown site(s): {', '.join(bad)}. Known: {', '.join(SITES)}"); sys.exit(1)
    root = HERE.parent / "Site extras"
    drv = root / "_drivers"; drv.mkdir(parents=True, exist_ok=True)

    print("\nClimate drivers (shared by every site)")
    drivers = {"fetched": NOW, "soi": soi(drv), "noaa": noaa(drv), "bom_climate_driver_update": bom_enso(drv), "bom_long_range_forecast": bom_outlook_text(drv)}
    feeds = bom_point_feed_probe(drv)
    if feeds: drivers["bom_point_feeds_found"] = feeds
    (drv / "drivers.json").write_text(json.dumps(drivers, indent=1), encoding="utf-8")
    print(f"  saved {drv / 'drivers.json'}")

    for site in want:
        lat, lon, state = SITES[site][:3]
        out = root / site; out.mkdir(parents=True, exist_ok=True)
        print(f"\n{site}")
        old = None
        try: old = json.loads((out / "outlook.json").read_text(encoding="utf-8"))
        except Exception: pass
        rec = {"site": site, "lat": lat, "lon": lon, "state": state, "fetched": NOW,
               "drivers": {"soi_latest_month": drivers["soi"].get("latest_month"), "soi": drivers["soi"].get("latest_soi"), "soi_phase": drivers["soi"].get("phase_name"),
                           "nino34_anomaly_c": drivers["noaa"].get("nino34_latest_anomaly_c"), "enso_state_from_oni": drivers["noaa"].get("enso_state_from_oni"),
                           "bom_driver_update_issued": drivers["bom_climate_driver_update"].get("issued"), "bom_driver_update_status": drivers["bom_climate_driver_update"].get("status"),
                           "bom_driver_update_url": BOM_ENSO, "details": "Site extras/_drivers/drivers.json"},
               "bom_outlook": bom_for_site(site, state, drivers["bom_long_range_forecast"], old),
               "short_range": open_meteo(lat, lon)}
        rec["bom_precis"] = bom_precis(site, state, out)
        (out / "outlook.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
        with (out / "outlook_history.jsonl").open("a", encoding="utf-8") as f: f.write(json.dumps(rec, separators=(",", ":")) + "\n")
        print(f"  saved outlook.json and added a line to outlook_history.jsonl")

    print("\nDone. Tell Claude \"seasonal outlook is ready\" and the drivers and forecasts go into the map.")
    print("If outlook.json says 'see page' for the Bureau, open the address it gives and read the current outlook there.")


if __name__ == "__main__":
    main()

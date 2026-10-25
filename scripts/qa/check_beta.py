"""Smoke-test the group beta maps before publishing: loads each beta/<site>/index.html (the minified page
that gets published) in headless Chromium, with no artifact runtime, so drawings save in the browser.

Checks: no JavaScript errors; terrain loads; only Layers, Draw and Features tabs; the beta terms show once
and stay dismissed; an analysis layer shows its source in the legend; the boundary layer toggles the map;
a tank can be drawn and appears in Features and in local storage; the site's exported drawings
(data-snapshots/<snap>/<site>_features) load and list; no other site's name, and no street address,
lot/plan number or email, anywhere in the page or its data files.

usage: python3 scripts/qa/check_beta.py [site-folder ...]      exit code 1 if anything fails
"""
import subprocess, sys, time, json, os, re, glob
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'beta'))
import build_beta as B  # noqa: E402

SNAP = ROOT / 'data-snapshots' / '2026-10-25_trial-v37'
NAMES = {'nimbin-group': ['Firefly', 'Nimbin'], 'bellbunya': ['Bellbunya', 'Belli Park'], 'willow-vale-team': ['Willow Vale', 'Bowman'],
         'noosa-forest-retreat': ['Noosa Forest', 'Kin Kin'], 'nac': ['NAC', 'North Arm'], 'annwn': ['Annwn', 'Capalaba'],
         'regenify': ['Regenify', 'Koonyum']}
OTHER = ['Bright Tree Village', 'Diamond Valley', 'Mangiri', 'Gemini']
PRIV = re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s(?:Road|Rd|Street|Lane|Drive|Avenue|Court|Crescent|Parade)\b|\b[A-Z][a-z]+\s(?:Road|Rd)\b|"
                  r"\bLot\s?\d+\b|\b(?:RP|SP|DP)\s?\d{4,}\b|[\w.+-]+@[\w-]+\.(?:com|net|org|au)\b")


def text_hits(path, words):
    s = Path(path).read_text(errors='ignore')
    s = re.sub(r'"[A-Za-z0-9+/=]{400,}"', '""', s)   # skip base64 rasters
    s = re.sub(r'(Kin Kin|Nimbin) (beds|Rhyolite|Phyllite|Basalt)', '', s)   # official rock-unit names in geology mapping
    return [w for w in words if w in s], sorted(set(PRIV.findall(s)))[:5]


def main():
    want = sys.argv[1:] or list(B.GROUPS.values())
    bad = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
        for sid, folder in B.GROUPS.items():
            if folder not in want:
                continue
            d = ROOT / 'beta' / folder
            srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8766'], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.8)
            res, errs = {}, []
            try:
                # bundle and data: no other site, no addresses
                others = [w for k, ws in NAMES.items() if k != sid for w in ws] + OTHER
                leaks = {}
                for f in [d / 'index.html'] + [Path(p) for p in glob.glob(str(d / '**/*.json'), recursive=True)]:
                    w, pv = text_hits(f, others)
                    if w or pv:
                        leaks[str(f.relative_to(d))] = w + pv
                res['clean'] = not leaks
                if leaks:
                    errs.append('leaks: ' + json.dumps(leaks)[:300])
                ctx = br.new_context(viewport={'width': 1400, 'height': 900})
                p = ctx.new_page()
                p.on('pageerror', lambda e: errs.append('JS: ' + str(e)[:200]))
                p.goto('http://localhost:8766/index.html')
                p.wait_for_function("document.querySelector('#loading').hidden", timeout=30000)
                p.wait_for_timeout(800)
                res['terms_first'] = p.is_visible('#betaTerms')
                p.click('#btOk')
                res['tabs'] = p.eval_on_selector_all('nav.tabs button', 'b=>b.map(x=>x.dataset.tab)')
                res['footer'] = 'Beta access for' in p.inner_text('#betaFoot')
                res['title'] = p.title()
                # an analysis layer shows its source
                p.click('#tab-layers .ovs button[data-v="slope"]')
                res['legend_source'] = 'Source:' in p.inner_text('#ovLegend')
                res['wildlife'] = p.locator('details[data-sec="wild"]').count() == (1 if (d / 'species.json').exists() else 0)
                # boundary layer toggles pixels
                p.click('#tab-layers .ovs button[data-v="none"]')
                shot = lambda: p.locator('#map').screenshot()
                a = shot(); p.click('#zLot'); p.wait_for_timeout(300); b = shot(); p.click('#zLot')
                res['layer_toggle'] = a != b
                # draw a tank at the centre of the map
                p.click('#t-draw')
                p.fill('#drawFind', 'tank')
                p.click('#tab-draw .tool[data-k="tank"]')
                box = p.locator('#map').bounding_box()
                p.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                p.wait_for_timeout(500)
                key = f'bt.{sid}.features'
                stored = p.evaluate(f"JSON.parse(localStorage.getItem('{key}')||'{{}}')")
                res['drawn'] = any(v.get('kind') == 'tank' for v in stored.values())
                res['feat_panel'] = 'Tank' in p.inner_text('#tab-feat')
                # removed panels empty and unreachable
                res['removed_empty'] = p.evaluate("['plan','notes','tools','site'].every(t=>{const e=document.querySelector('#tab-'+t);return !e||(e.hidden&&!e.innerText.trim())})")
                # load the site's exported drawings
                docs = {Path(f).stem: json.load(open(f)) for f in glob.glob(str(SNAP / f'{sid}_features' / '*.json'))}
                p.evaluate(f"localStorage.setItem('{key}', {json.dumps(json.dumps(docs))})")
                p.reload(); p.wait_for_function("document.querySelector('#loading').hidden", timeout=30000); p.wait_for_timeout(800)
                res['terms_remembered'] = not p.is_visible('#betaTerms')
                p.click('#t-feat')
                n = p.locator('#tab-feat .flist button').count()
                res['snapshot_listed'] = f'{n}/{len(docs)}'
                res['snapshot_ok'] = n == len(docs)
                # phone layout loads too
                ph = ctx.new_page(); ph.set_viewport_size({'width': 390, 'height': 800})
                ph.on('pageerror', lambda e: errs.append('JS(phone): ' + str(e)[:200]))
                ph.goto('http://localhost:8766/index.html'); ph.wait_for_function("document.querySelector('#loading').hidden", timeout=30000)
                res['phone_noscroll'] = ph.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                ctx.close()
            except Exception as e:
                errs.append('QA: ' + str(e)[:300])
            finally:
                srv.terminate(); srv.wait()
            ok = not errs and res.get('terms_first') and res.get('tabs') == ['layers', 'draw', 'feat'] and all(
                res.get(k) for k in ['clean', 'footer', 'legend_source', 'wildlife', 'layer_toggle', 'drawn', 'feat_panel', 'removed_empty', 'terms_remembered', 'snapshot_ok', 'phone_noscroll'])
            bad += not ok
            print('OK  ' if ok else 'FAIL', folder, json.dumps(res), errs[:4])
        br.close()
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()

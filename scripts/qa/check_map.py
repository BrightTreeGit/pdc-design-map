"""Smoke-test the design map before publishing: loads every site in headless Chromium and checks
that terrain loads, every tab renders, no JavaScript errors occur, and drawn shapes actually draw.

usage: python3 scripts/qa/check_map.py            (serves map/ on port 8765 itself)
Exit code 1 if anything fails. Run it before every publish (see CLAUDE.md)."""
import subprocess, sys, time, json, os
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, '..', '..', 'map')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
SITES = ['bright-tree', 'bright-tree-gemini', 'bellbunya', 'nimbin', 'willow-vale', 'noosa-forest-retreat', 'nac'] + [s for s in ('willow-vale-team', 'nimbin-group') if "id:'" + s + "'" in open(os.path.join(root, 'index.html')).read()]
TEST = {'t1': {'kind': 'shed', 'name': 'QA shed', 'geom': {'g': 'polygon', 'pts': [[900, 1000], [930, 1000], [930, 1020], [900, 1020]]}, 'status': 'built', 'stage': 'existing'}}
bad = 0
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
        for s in SITES:
            p = b.new_page(viewport={'width': 1400, 'height': 900}); errs = []
            p.on('pageerror', lambda e: errs.append('JS: ' + str(e)[:200]))
            p.goto('http://localhost:8765/index.html')
            key = 'bt.features' if s == 'bright-tree' else f'bt.{s}.features'
            p.evaluate(f"localStorage.setItem('{key}', {json.dumps(json.dumps(TEST))})")
            p.goto(f'http://localhost:8765/index.html#site={s}'); p.reload(); p.wait_for_timeout(9000)
            r = p.evaluate("""async ()=>{const fr=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const o={terrain:!!T&&!!dem2,hydro:!!IMG.wet&&!!IMG.erosion,tabs:{}};for(const t of ['site','layers','draw','feat','plan','tools','notes']){try{showTab(t);o.tabs[t]=(document.querySelector('#tab-'+t)||{innerText:''}).innerText.length>50}catch(e){o.tabs[t]=false}}
              showTab('layers');fitBox(880,980,950,1040);draw();const c=w2s(915,1010);const px=()=>Array.from(cv.getContext('2d').getImageData(Math.round(c[0]*devicePixelRatio),Math.round(c[1]*devicePixelRatio),1,1).data).join(',');const was=layers.design;layers.design=true;draw();await fr();const on=px();layers.design=false;draw();await fr();const off=px();layers.design=was;draw();o.shapeDrawn=on!==off;o.n=features.size;return o}""")
            ok = r['terrain'] and r['hydro'] and all(r['tabs'].values()) and r['shapeDrawn'] and not errs
            bad += not ok
            print(('OK  ' if ok else 'FAIL'), s, json.dumps(r), errs[:3]); p.close()
        b.close()
finally:
    srv.terminate()
sys.exit(1 if bad else 0)

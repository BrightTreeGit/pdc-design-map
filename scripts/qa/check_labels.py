"""Label placement check for the 2D design map: loads Bright Tree with the trial map's drawings (fixture, local mode),
renders the whole lot and the house cluster at three zoom levels, and checks that no two drawn labels overlap.

usage: python3 scripts/qa/check_labels.py [--shot out.png] [--no-assert]
  --shot      save a screenshot of the house cluster (closest zoom) to this path
  --no-assert only take the screenshot (for a 'before' picture of older code that has no window.__labelBoxes)
The map exposes the boxes it drew as window.__labelBoxes = [{x0,y0,x1,y1,t,cls}] (screen pixels).
Exit code 1 if any two boxes overlap or a label runs off the map."""
import subprocess, sys, time, json, os
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, '..', '..', 'map')
FEATS = json.load(open(os.path.join(here, 'fixtures', 'bright_tree_features.json')))
args = sys.argv[1:]
shot = args[args.index('--shot') + 1] if '--shot' in args else None
check = '--no-assert' not in args
PORT = 8766
VIEWS = [('whole lot', None), ('house area', (820, 870, 1010, 1030)), ('house cluster', (862, 905, 948, 985)), ('house close', (880, 925, 925, 962))]
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
bad = 0


def overlaps(B):
    out = []
    for i in range(len(B)):
        for j in range(i + 1, len(B)):
            a, b = B[i], B[j]
            if a['x0'] < b['x1'] - .5 and a['x1'] > b['x0'] + .5 and a['y0'] < b['y1'] - .5 and a['y1'] > b['y0'] + .5:
                out.append((a['t'], b['t']))
    return out


try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
        p = br.new_page(viewport={'width': 1400, 'height': 900}); errs = []
        p.on('pageerror', lambda e: errs.append('JS: ' + str(e)[:200]))
        p.goto(f'http://localhost:{PORT}/index.html')
        p.evaluate(f"localStorage.clear();localStorage.setItem('bt.features', {json.dumps(json.dumps(FEATS))})")
        p.goto(f'http://localhost:{PORT}/index.html#site=bright-tree'); p.reload(); p.wait_for_timeout(9000)
        print('features loaded:', p.evaluate('features.size'))
        for flab in ([True, False] if check else [True]):
            for name, box in VIEWS:
                r = p.evaluate("""async ([box,flab])=>{const fr=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                  selected=null;hoverId=null;layers.flabels=flab;layers.labels=true;layers.design=true;if(box)fitBox(...box);else fitLot();draw();await fr();
                  const r=cv.getBoundingClientRect();return {s:view.s,boxes:window.__labelBoxes||null,W,H}}""", [box, flab])
                if not check:
                    continue
                B = r['boxes']
                if B is None:
                    print('FAIL', name, 'window.__labelBoxes missing'); bad += 1; continue
                ov = overlaps(B)
                off = [b['t'] for b in B if b['x0'] < -1 or b['y0'] < -1 or b['x1'] > r['W'] + 1 or b['y1'] > r['H'] + 1]
                ok = not ov and not off
                bad += not ok
                cls = {}
                for b in B: cls[b['cls']] = cls.get(b['cls'], 0) + 1
                print('OK  ' if ok else 'FAIL', f"{name:14s} names-on={flab!s:5s} zoom {r['s']:.2f} px/m  {len(B)} labels {cls}",
                      ('overlaps: ' + str(ov[:4])) if ov else '', ('off map: ' + str(off[:4])) if off else '')
        # selection: the selected feature's label always shows and nothing sits on its handles
        if check:
            r = p.evaluate("""async ()=>{const fr=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));layers.flabels=true;fitBox(862,905,948,985);
              const id=[...features.entries()].find(([i,f])=>f.kind==='building')[0];selected=id;draw();await fr();const B=window.__labelBoxes||[];
              const f=features.get(id);const sel=B.find(b=>b.id===id);const hs=(window.__handleBoxes||[]);
              const onH=B.filter(b=>hs.some(h=>b.x0<h.x1&&b.x1>h.x0&&b.y0<h.y1&&b.y1>h.y0)).map(b=>b.t);selected=null;draw();return {name:f.name,shown:!!sel,onHandles:onH,handles:hs.length}}""")
            ok = r['shown'] and not r['onHandles'] and r['handles'] > 0
            bad += not ok
            print('OK  ' if ok else 'FAIL', 'selected label', json.dumps(r))
        # per-feature colour: pick a swatch in the feature panel, the map redraws in that colour, undo puts it back, and the
        # new "Custom building / marker" type takes a colour too
        if check:
            r = p.evaluate("""async ()=>{const fr=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));layers.flabels=true;fitBox(900,935,925,958);
              const id=[...features.entries()].find(([i,f])=>f.kind==='building')[0];const f=features.get(id);const c=centroid(f);
              const px=()=>{const [x,y]=w2s(...c);return Array.from(cv.getContext('2d').getImageData(Math.round(x*devicePixelRatio),Math.round(y*devicePixelRatio),1,1).data).slice(0,3)};
              selected=id;showTab('feat');renderFeatures();draw();await fr();const before=px();const sw=[...document.querySelectorAll('.csw')];const blue=sw.find(b=>b.dataset.col==='#1c64d8');
              blue.click();await new Promise(r=>setTimeout(r,300));draw();await fr();const after=px();const saved=features.get(id).color;
              const stored=JSON.parse(localStorage.getItem('bt.features'))[id].color;await undo();await new Promise(r=>setTimeout(r,300));const undone=features.get(id).color||null;
              draft={kind:'marker',pts:[]};await commit({g:'point',pts:[[912,940]]});const mid=selected;renderFeatures();const mk=features.get(mid);const open=!!document.querySelector('details.mini[open] .csw');
              await saveFields(mid,{color:'#e0218a'});draw();await fr();const [mx,my]=w2s(912,940);const mp=Array.from(cv.getContext('2d').getImageData(Math.round(mx*devicePixelRatio),Math.round(my*devicePixelRatio),1,1).data).slice(0,3);
              const listSw=(()=>{selected=null;renderFeatures();const b=document.querySelector(`#tab-feat [data-id="${mid}"] .swatch`);return b?b.style.background:''})();
              features.delete(mid);saveLocal();selected=null;showTab('layers');draw();
              return {swatches:sw.length,before,after,saved,stored,undone,markerKind:mk.kind,markerPanelOpen:open,markerPixel:mp,listSwatch:listSw}}""")
            ok = (r['swatches'] == 11 and r['saved'] == '#1c64d8' and r['stored'] == '#1c64d8' and r['undone'] is None
                  and r['after'][2] > r['after'][0] and r['after'] != r['before'] and r['markerKind'] == 'marker' and r['markerPanelOpen']
                  and r['markerPixel'][0] > 180 and r['markerPixel'][1] < 120 and '224, 33, 138' in r['listSwatch'])
            bad += not ok
            print('OK  ' if ok else 'FAIL', 'feature colour', json.dumps(r))
        if shot:
            p.evaluate("""async ()=>{$('#toast').classList.remove('show','act');layers.flabels=true;selected=null;fitBox(862,905,948,985);draw();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}""")
            p.screenshot(path=shot)
            base, ext = os.path.splitext(shot)
            for nm, box in (('lot', None), ('area', (820, 870, 1010, 1030))):
                p.evaluate("""async (box)=>{if(box)fitBox(...box);else fitLot();draw();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))}""", box)
                p.screenshot(path=f'{base}-{nm}{ext}')
            print('saved', shot)
        if errs:
            print('FAIL JS errors', errs[:3]); bad += 1
        br.close()
finally:
    srv.terminate()
sys.exit(1 if bad else 0)

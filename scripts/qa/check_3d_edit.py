"""3D drawing and editing test: opens the 3D view on one site in local mode (no database), draws a zone by
clicking the terrain, selects it, drags the whole shape and then one corner, undoes, and checks the geometry
changed (and saved to local storage) at each step, with no JavaScript errors.

usage: python3 scripts/qa/check_3d_edit.py [site] [screenshot.png]     (default site bright-tree)
       QA_ROOT=beta/willow-vale python3 scripts/qa/check_3d_edit.py willow-vale-team    (test a built beta page;
       add QA_PAGE=index.debug.html after build_beta.py <site> --debug)
Exit code 1 if anything fails."""
import subprocess, sys, time, json, os
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.environ.get('QA_ROOT') or os.path.join(here, '..', '..', 'map')
SITE = sys.argv[1] if len(sys.argv) > 1 else 'bright-tree'
SHOT = sys.argv[2] if len(sys.argv) > 2 else None
PAGE = os.environ.get('QA_PAGE', 'index.html')   # beta pages: build with --debug and use index.debug.html (the minified one renames functions)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8771'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
fails = []
def check(ok, what):
    print(('OK  ' if ok else 'FAIL'), what)
    if not ok: fails.append(what)
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'), args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        p = b.new_page(viewport={'width': 1400, 'height': 900}); errs = []
        p.on('pageerror', lambda e: errs.append('JS: ' + str(e)[:300]))
        p.goto(f'http://localhost:8771/{PAGE}')
        key = 'bt.features' if SITE == 'bright-tree' else f'bt.{SITE}.features'
        p.evaluate(f"localStorage.setItem('{key}', '{{}}')")
        p.evaluate("try{localStorage.setItem(LSK('bt.betaTerms.v1'),'1')}catch(e){}")   # beta pages: terms already accepted
        p.goto(f'http://localhost:8771/{PAGE}#site={SITE}'); p.reload(); p.wait_for_timeout(9000)
        p.evaluate("fitLot();draw();open3D()"); p.wait_for_timeout(4000)
        check(p.evaluate("V3.on&&!!V3.buf&&!!V3.cam"), '3D view opened')
        box = p.evaluate("(()=>{const r=$('#gl').getBoundingClientRect();return [r.left,r.top,r.width,r.height]})()")
        L, T0, Wd, Ht = box; cx, cy = L + Wd / 2, T0 + Ht / 2
        # terrain picking
        w = p.evaluate(f"v3Pick({Wd/2},{Ht/2})")
        check(w is not None and 0 < w[0] < 2000, f'v3Pick hits the terrain at the centre: {w}')
        back = p.evaluate(f"(()=>{{const w=v3Pick({Wd/2},{Ht/2});const s=v3Scr(w[0],w[1],0);return [s[0],s[1]]}})()")
        check(abs(back[0] - Wd / 2) < 1.5 and abs(back[1] - Ht / 2) < 1.5, f'pick then project returns to the same pixel: {back}')
        # draw a zone by clicking four points on the ground
        p.evaluate("showTab('draw');startTool('zone2')"); p.wait_for_timeout(200)
        pts = [(-90, -50), (90, -50), (90, 60), (-90, 60)]
        for dx, dy in pts:
            p.mouse.move(cx + dx, cy + dy); p.wait_for_timeout(60); p.mouse.click(cx + dx, cy + dy); p.wait_for_timeout(120)
        check(p.evaluate("!!draft&&draft.pts.length===4"), 'four corners placed by clicking the terrain')
        p.wait_for_timeout(200); p.keyboard.press('Enter'); p.wait_for_timeout(600)
        r = p.evaluate("(()=>{const a=[...features.entries()];return {n:a.length,id:a[0]&&a[0][0],g:a[0]&&a[0][1].geom,sel:selected}})()")
        check(r['n'] == 1 and r['g']['g'] == 'polygon' and len(r['g']['pts']) == 4, f"zone saved as a 4-corner polygon: {r['g']}")
        fid = r['id']; g0 = r['g']['pts']
        # select: click empty ground far away, then the shape
        p.mouse.click(L + 40, T0 + Ht - 60); p.wait_for_timeout(300)
        check(p.evaluate("selected===null"), 'clicking empty ground clears the selection')
        p.mouse.click(cx, cy + 5); p.wait_for_timeout(300)
        check(p.evaluate(f"selected==='{fid}'"), 'clicking the draped shape selects it')
        # orbit still works (drag on empty ground)
        y0 = p.evaluate("V3.yaw"); p.mouse.move(L + 60, T0 + Ht - 80); p.mouse.down(); p.mouse.move(L + 160, T0 + Ht - 80, steps=6); p.mouse.up(); p.wait_for_timeout(200)
        check(abs(p.evaluate("V3.yaw") - y0) > 0.2 and p.evaluate(f"selected==='{fid}'"), 'dragging empty ground orbits and keeps the selection')
        p.evaluate("V3.yaw=0;v3Draw()"); p.wait_for_timeout(200)
        # move: drag the body
        ip = p.evaluate(f"(()=>{{const f=features.get('{fid}');const q=interiorPoint(f.geom).p;const s=v3Scr(q[0],q[1]);return [s[0],s[1]]}})()")
        p.mouse.move(L + ip[0], T0 + ip[1]); p.mouse.down(); p.mouse.move(L + ip[0] + 70, T0 + ip[1] + 25, steps=8); p.mouse.up(); p.wait_for_timeout(500)
        g1 = p.evaluate(f"features.get('{fid}').geom.pts")
        d = [(g1[i][0] - g0[i][0], g1[i][1] - g0[i][1]) for i in range(4)]
        same = all(abs(d[i][0] - d[0][0]) < .25 and abs(d[i][1] - d[0][1]) < .25 for i in range(4))
        check(same and abs(d[0][0]) + abs(d[0][1]) > 3, f'dragging the body moved the whole shape by {d[0]}')
        # reshape: drag corner 0
        vp = p.evaluate(f"(()=>{{const q=features.get('{fid}').geom.pts[0];const s=v3Scr(q[0],q[1]);return [s[0],s[1]]}})()")
        p.mouse.move(L + vp[0], T0 + vp[1]); p.mouse.down(); p.mouse.move(L + vp[0] - 40, T0 + vp[1] - 30, steps=8); p.mouse.up(); p.wait_for_timeout(500)
        g2 = p.evaluate(f"features.get('{fid}').geom.pts")
        check(g2[0] != g1[0] and g2[1:] == g1[1:], f'dragging a corner moved only that corner: {g1[0]} -> {g2[0]}')
        saved = p.evaluate(f"JSON.parse(localStorage.getItem('{key}')||'{{}}')")
        check(saved.get(fid, {}).get('geom', {}).get('pts') == g2, 'the reshaped geometry was saved (persist / saveGeom)')
        hist = p.evaluate("HIST.map(h=>h.label)")
        check(len(hist) >= 3 and hist[-1].startswith('reshape') and hist[-2].startswith('move'), f'undo history: {hist}')
        # screenshot of the selected shape with handles and the upright label
        if SHOT:
            p.screenshot(path=SHOT)
        # labels are drawn on the overlay
        ink = p.evaluate("(()=>{const c=$('#gl2');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n})()")
        check(ink > 500, f'overlay draws the selection, handles and labels ({ink} px)')
        # undo twice: corner back, then position back
        p.mouse.click(L + 40, T0 + Ht - 60); p.wait_for_timeout(200)
        p.keyboard.press('Control+z'); p.wait_for_timeout(400)
        check(p.evaluate(f"features.get('{fid}').geom.pts") == g1, 'undo puts the corner back')
        p.keyboard.press('Control+z'); p.wait_for_timeout(400)
        check(p.evaluate(f"features.get('{fid}').geom.pts") == g0, 'undo again puts the shape back where it was drawn')
        p.keyboard.press('Control+Shift+z'); p.wait_for_timeout(400)
        check(p.evaluate(f"features.get('{fid}').geom.pts") == g1, 'redo moves it again')
        # a point feature (tank) by one click, then drag it
        p.evaluate("startTool('tank')"); p.wait_for_timeout(100)
        p.mouse.click(cx + 200, cy - 100); p.wait_for_timeout(500)
        tk = p.evaluate("(()=>{const f=[...features.values()].find(f=>f.kind==='tank');return f&&f.geom.pts[0]})()")
        check(tk is not None, f'a tank placed with one click: {tk}')
        # a green firebreak strip (line drawn as a 10 m band): draw in 3D, then select it by clicking inside the band
        if p.evaluate("!!KINDS.greenstrip"):
            p.evaluate("pickSel(null);startTool('greenstrip')"); p.wait_for_timeout(100)
            for dx, dy in [(-150, 120), (-20, 140), (110, 120)]:
                p.mouse.move(cx + dx, cy + dy); p.mouse.click(cx + dx, cy + dy); p.wait_for_timeout(120)
            p.keyboard.press('Enter'); p.wait_for_timeout(600)
            st = p.evaluate("(()=>{const e=[...features].find(([i,f])=>f.kind==='greenstrip');return e&&{id:e[0],w:e[1].width,n:e[1].geom.pts.length,notes:(e[1].notes||'').startsWith('Planting layers')}})()")
            check(st and st['w'] == 10 and st['n'] == 3 and st['notes'], f'firebreak strip drawn in 3D, 10 m wide, planting notes filled in: {st}')
            inside = p.evaluate(f"""(()=>{{const f=features.get('{st['id']}');const b=stripOf(f);const r=bandRings(b)[0];const q=[(r[1][0]+r[r.length-2][0])/2*.6+f.geom.pts[1][0]*.4,(r[1][1]+r[r.length-2][1])/2*.6+f.geom.pts[1][1]*.4];const s=v3Scr(q[0],q[1]);const g=$('#gl').getBoundingClientRect();return [g.left+s[0],g.top+s[1]]}})()""")
            p.evaluate("pickSel(null)"); p.mouse.click(*inside); p.wait_for_timeout(300)
            check(p.evaluate(f"selected==='{st['id']}'"), 'clicking inside the band (off the centre line) selects the strip')
        # texture refresh timing
        ms = p.evaluate("(()=>{const t=performance.now();v3Texture(V3.box);return performance.now()-t})()")
        print(f'     painting the drape texture takes {ms:.0f} ms (done once when a drag starts and once when it ends)')
        p.evaluate("close3D()"); p.wait_for_timeout(300)
        # touch: a tap places a corner, a tap on a drawing selects it
        ctx = b.new_context(viewport={'width': 900, 'height': 800}, has_touch=True); t = ctx.new_page()
        t.on('pageerror', lambda e: errs.append('JS (touch): ' + str(e)[:300]))
        t.goto(f'http://localhost:8771/{PAGE}'); t.evaluate("try{localStorage.setItem(LSK('bt.betaTerms.v1'),'1')}catch(e){}")
        t.goto(f'http://localhost:8771/{PAGE}#site={SITE}'); t.reload(); t.wait_for_timeout(9000)
        t.evaluate("fitLot();draw();open3D()"); t.wait_for_timeout(4000)
        bx = t.evaluate("(()=>{const r=$('#gl').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
        t.evaluate("startTool('tank')"); t.touchscreen.tap(bx[0], bx[1]); t.wait_for_timeout(500)
        n = t.evaluate("[...features.values()].filter(f=>f.kind==='tank').length")
        t.evaluate("cancelDraft();selected=null;draw()"); t.wait_for_timeout(200)
        t.touchscreen.tap(bx[0], bx[1]); t.wait_for_timeout(400)
        check(n >= 1 and t.evaluate("!!selected&&features.get(selected).kind==='tank'"), 'touch: tap places a tank and a tap on it selects it')
        ctx.close()
        check(not errs, f'no JavaScript errors {errs[:3]}')
        b.close()
finally:
    srv.terminate()
sys.exit(1 if fails else 0)

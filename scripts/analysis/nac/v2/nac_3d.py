"""NAC 3D view: screenshots of the map's 3D terrain view (local copy of map/, features from feats2.json) from three angles, into 'NAC 3D view.pdf'.
usage: python3 nac_3d.py [outdir]"""
import subprocess, sys, time, json, os
from playwright.sync_api import sync_playwright
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '../../../../map')
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/nac_out'
os.makedirs(OUTDIR, exist_ok=True)
F = json.load(open(os.path.join(HERE, 'feats2.json')))
PORT = 8771
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
VIEWS = [('from the south: the street verge in front, the house and vegie beds beyond', 0, .9, .5), ('from the south-east over the gum cluster', 330, .62, .52), ('from the south-west over the ironbarks and the garage', 30, .62, .52)]
shots = []
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'), args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        p = b.new_page(viewport={'width': 1400, 'height': 900}, device_scale_factor=2); errs = []
        p.on('pageerror', lambda e: errs.append(str(e)[:200]))
        p.goto(f'http://localhost:{PORT}/index.html'); p.evaluate(f"localStorage.setItem('bt.nac.features', {json.dumps(json.dumps(F))})")
        p.goto(f'http://localhost:{PORT}/index.html#site=nac'); p.reload(); p.wait_for_timeout(9000)
        ok = p.evaluate("""async()=>{layers.base='aerial';fitLot();draw();await open3D();await new Promise(r=>setTimeout(r,800));return {dem:!!dem2,on:V3.on,gl:!!V3.gl,msg:document.querySelector('#v3msg').textContent,L:V3.L}}""")
        print('3D', ok, errs[:2])
        for i, (cap, yaw, pitch, dist) in enumerate(VIEWS):
            p.evaluate(f"""()=>{{V3.yaw={yaw}*Math.PI/180;V3.pitch={pitch};V3.dist=V3.L*{dist};V3.tgt=[0,0,0];document.querySelectorAll('#v3d .v3bar, #v3d .v3hint').forEach(e=>e.style.display='none');v3Draw()}}""")
            p.wait_for_timeout(600)
            f = os.path.join(OUTDIR, f'nac3d_{i}.png'); p.locator('#v3d').screenshot(path=f); shots.append((f, cap))
        b.close()
finally:
    srv.terminate()
import textwrap, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
pdf = PdfPages(os.path.join(OUTDIR, 'NAC 3D view.pdf'))
for f, cap in shots:
    im = Image.open(f); im = im.crop((0, int(im.height * .1), im.width, int(im.height * .78))); fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(.06, .94, "NAC in 3D: Ange's plan on the terrain", fontsize=17, weight='bold', color='#222')
    fig.text(.06, .91, textwrap.fill(f'Looking {cap}. Heights from the NSW 5 m elevation model, so the block reads as a smooth slope; features from Ange\'s plan (Oct 2026).', 150), fontsize=9.5, color='#666', va='top', linespacing=1.3)
    ax = fig.add_axes([.04, .1, .92, .77]); ax.imshow(im); ax.axis('off')
    fig.text(.06, .04, 'Source: design map 3D view (trial v33). Elevation: NSW 5 m DEM (DCS Spatial Services). Aerial: NSW imagery, 1 Sep 2021. Features: Ange\'s plan, fitted ±1 m. First names only.', fontsize=7.5, color='#888')
    pdf.savefig(fig); plt.close(fig)
pdf.close(); print('saved', len(shots), 'views')

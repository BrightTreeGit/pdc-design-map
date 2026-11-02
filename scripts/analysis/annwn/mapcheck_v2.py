import subprocess,sys,time,json,os,glob
from playwright.sync_api import sync_playwright
D='/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
F={}
for f in glob.glob(D+'annwn_db_now/annwn_features/*.json'):F[f.split('/')[-1][:-5]]=json.load(open(f))
for f in glob.glob(D+'annwn_new/*.json'):F[f.split('/')[-1][:-5]]=json.load(open(f))
F['an33']['geom']={'g':'point','pts':[[1009,981.3]]}
root='/home/claude/pdc-design-map/map'
srv=subprocess.Popen([sys.executable,'-m','http.server','8767'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium'))
    p=b.new_page(viewport={'width':1400,'height':1000});errs=[]
    p.on('pageerror',lambda e:errs.append(str(e)[:200]))
    p.goto('http://localhost:8767/index.html')
    p.evaluate("v=>localStorage.setItem('bt.annwn.features',v)",json.dumps(F))
    p.goto('http://localhost:8767/index.html#site=annwn');p.reload();p.wait_for_timeout(9000)
    n=p.evaluate("()=>{showTab('feat');layers.design=true;fitBox(980,975,1013,1016);draw();return features.size}")
    p.wait_for_timeout(1500)
    p.screenshot(path=D+'bron2/map_annwn.png')
    print(n,errs)
    b.close()
finally: srv.terminate()

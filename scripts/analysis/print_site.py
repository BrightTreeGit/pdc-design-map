import subprocess,sys,time,json,os,glob,base64
from playwright.sync_api import sync_playwright
root='/home/claude/pdc-design-map/map'; SP=sys.argv[1]; col=sys.argv[2]; out=sys.argv[3]
snap='/home/claude/pdc-design-map/data-snapshots/2026-11-02_trial/'+col
F={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(snap+'/*.json')}
key='bt.' if SP=='bright-tree' else f'bt.{SP}.'
srv=subprocess.Popen([sys.executable,'-m','http.server','8768'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
  with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM','/opt/pw-browsers/chromium'))
    p=b.new_page(viewport={'width':1400,'height':900});errs=[]
    p.on('pageerror',lambda e:errs.append(str(e)[:200]))
    p.goto('http://localhost:8768/index.html')
    cfg={'scheme':'economy','cmode':'zone','cex':0.5,'detail':'xfine','creeks':'main','minPatch':500,'extend':'none','canopy':True,'size':float(os.environ.get('PSIZE','180')),'area':'lot','fill':'terrain','v46':1,'v47':1,'swid':float(os.environ.get('SWID','1')),**json.loads(os.environ.get('P3EXTRA','{}'))}
    p.evaluate("([k,c,f])=>{localStorage.setItem(k+'p3',JSON.stringify(c));localStorage.setItem(k+'features',f)}",[key,cfg,json.dumps(F)])
    p.goto(f'http://localhost:8768/index.html#site={SP}');p.reload();p.wait_for_timeout(12000)
    r=p.evaluate("""async()=>{await loadCG();await loadGrass();const r=build3D();const se=swapEst(r);return {w:r.wmm,h:r.hmm,z:r.zmm,parts:r.meshes.map(m=>[m.name,m.color,m.t.length/3]),se,n:features.size}}""")
    print(json.dumps(r)[:1500]);print('errs',errs)
    d=p.evaluate("async()=>{const r=build3D();const b=await to3MF(r);const u=new Uint8Array(await b.arrayBuffer());let s='';for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return btoa(s)}")
    open(out,'wb').write(base64.b64decode(d))
    b.close()
finally: srv.terminate()

import json,time
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='/opt/pw-browsers/chromium'); p=b.new_page(viewport={'width':1400,'height':1000})
    errs=[]; p.on('pageerror',lambda e:errs.append(str(e)[:300]))
    p.goto('http://localhost:8766/index.html#site=bright-tree'); p.wait_for_timeout(9000)
    p.evaluate("async()=>{showTab('tools');await enAddHouse()}"); p.wait_for_timeout(500)
    out={}
    for mode in ['survey','today']:
        p.evaluate(f"async()=>{{ENS.trees='{mode}';await enRun({ 'true' if mode=='today' else 'false'})}}")
        out[mode]=p.evaluate("()=>({mean:ENR.S.mean,jun:ENR.S.mon[5],edits:ENR.edits,arr:ENR.arrs.map(a=>[a.f.name,a.stats.mean,a.stats.mon[5],a.loss,a.lossJun,a.sh.svf,a.yieldKw])})")
    # breakdown for today's trees: unshaded, beam-only shade, full
    out['brk']=p.evaluate("""()=>ENR.arrs.filter(a=>a.batt).map(a=>{const o={derate:ENS.derate,albedo:ENS.albedo};const s=d=>{let t=0,j=0,n=0,nj=0;const t0=Date.parse(SFULL.start+'T00:00:00Z');for(let i=0;i<d.length;i++){if(!isFinite(d[i]))continue;t+=d[i];n++;if(new Date(t0+i*864e5).getUTCMonth()===5){j+=d[i];nj++}}return [t/n*a.kw,j/nj*a.kw]};
      const un=s(enDays(a.p,null,o)),beam=s(enDays(a.p,{T:a.sh.T,svf:1},o)),full=s(a.day1),noLoss=s(enDays(a.p,null,{derate:100,albedo:.2}));
      return {n:a.f.name,unshaded:un,beamShadeOnly:beam,full,noSystemLoss:noLoss}})""")
    out['trees']=p.evaluate("()=>ENR.trees.map(t=>({x:t.x,y:t.y,h:Math.round(t.h),gain:Math.round(t.gain)}))")
    out['B']=p.evaluate("()=>({flat:ENR.B.flat,yrs:ENR.B.years,L:ENR.B.L,un:ENR.B.un,worst:ENR.B.worst,need1:ENR.B.need1,need:ENR.B.needMult,longest:ENR.B.longest,runs:ENR.B.runs.slice().sort((a,b)=>b[0]-a[0]).slice(0,5)})")
    out['S']=p.evaluate("()=>{const S=ENR.S;return {r3:[S.r3.mean,S.r3.from],r7:[S.r7.mean,S.r7.from],r14:[S.r14.mean,S.r14.from],p10:S.p10,worstMonth:S.worstMonth,lowY:S.lowY,hiY:S.hiY,dry:S.dry,wet:S.wet,winter:S.winter,wetSummer:S.wetSummer,summer:S.summer,wetS:S.wetS,mon:S.mon,annual:S.annual}}")
    p.evaluate("()=>{const s=document.querySelector('[data-sec=\"t-energy\"]');s.open=true;s.scrollIntoView()}"); p.wait_for_timeout(500)
    p.screenshot(path='tools.png',full_page=False)
    p.evaluate("()=>enReport()"); p.wait_for_timeout(800); p.screenshot(path='report.png',full_page=True)
    p.emulate_media(media='print'); p.pdf(path='report.pdf',format='A4',print_background=True); 
    print(json.dumps(out,default=str,indent=0)[:6000]); print('errs',errs[:5])
    json.dump(out,open('r2.json','w'),default=str)
    b.close()

import asyncio,base64,json,sys
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/work/bellprint/out/'
SHEETS=json.loads(open('/tmp/claude-0/work/bellprint/sheets.json').read())
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'])
        pg=await b.new_page(viewport={'width':1600,'height':1000})
        logs=[];pg.on('pageerror',lambda e:logs.append('ERR '+str(e)));pg.on('console',lambda m:logs.append(m.text) if m.type=='error' else None)
        await pg.goto('http://localhost:8765/_test.html#site=bellbunya');await pg.wait_for_timeout(5000)
        await pg.evaluate("""async()=>{const F=await (await fetch('/tmp_feats.json')).json();window.__ALLF=F;features.clear();for(const [k,v] of Object.entries(F))features.set(k,v);
          const im={name:'Site plan DD1-01 D',src:'/tmp_siteplan.png',w:1614,h:1144,a:.5,b:0,c:709,d:1085,op:.75,on:true,design:true};imagery.set('sp',im);loadImageryEl('sp',im);
          window.__out=[];downloads={save:async({filename,data})=>{const r=await new Promise(res=>{const fr=new FileReader();fr.onload=()=>res(fr.result);fr.readAsDataURL(data)});window.__out.push([filename,r])}};
          showTab('tools');renderTools();draw()}""")
        await pg.wait_for_timeout(1500)
        for sh in SHEETS:
            await pg.evaluate("""(sh)=>{features.clear();for(const [k,v] of Object.entries(window.__ALLF)){if(sh.noZones&&(KINDS[v.kind]||{}).g==='Zones')continue;features.set(k,v)}
              imagery.get('sp').on=!!sh.siteplan;layers.base=sh.base||'aerial';layers.baseOp=1;layers.overlay='none';layers.design=true;layers.flabels=true;layers.zlabels=true;layers.lot=true;
              Object.assign(SO,SHEET_DEF,sh.so);SO.v3=Object.assign({},SHEET_DEF.v3,sh.so.v3||{});SO.fmt='png';
              let t=document.querySelector('#shTitle');if(!t){t=document.createElement('input');t.id='shTitle';t.hidden=true;document.body.appendChild(t)}t.value=sh.title;
              let bx=sh.box;if(bx==='lot'){const P=flat(T.lot);let a=Math.min(...P.map(p=>p[0])),c=Math.max(...P.map(p=>p[0])),bb=Math.min(...P.map(p=>p[1])),d=Math.max(...P.map(p=>p[1]));const pd=Math.max(c-a,d-bb)*.06;bx=[a-pd,bb-pd,c+pd,d+pd]}const [x0,y0,x1,y1]=bx;fitBox(x0,y0,x1,y1,10);draw();window.__out=[];
              let btn=document.querySelector('#tSheet');if(!btn){btn=document.createElement('button');btn.id='tSheet';btn.hidden=true;document.body.appendChild(btn)}}""",sh)
            await pg.wait_for_timeout(600)
            await pg.evaluate("exportSheet()")
            for i in range(120):
                await pg.wait_for_timeout(500)
                n=await pg.evaluate("window.__out.length")
                if n>=len(sh['so'].get('bases',['current'])):break
            outs=await pg.evaluate("window.__out")
            for i,(fn,du) in enumerate(outs):
                open(OUT+f"{sh['id']}_{i}.png",'wb').write(base64.b64decode(du.split(',',1)[1]))
            print(sh['id'],len(outs))
        print(logs[:10]);await b.close()
asyncio.run(main())

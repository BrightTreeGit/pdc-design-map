import json,base64
b64=lambda f,m:f'data:{m};base64,'+base64.b64encode(open(f,'rb').read()).decode()
t=json.load(open('/home/claude/pdc-design-map/map/terrain.json'))
X0=1100
lot=[[round(x-X0,1),y] for x,y in zip(t['lot'][0::2],t['lot'][1::2])]
bt=t['catch'][0]['p'];btc=[[round(x-X0,1),y] for x,y in zip(bt[0::2],bt[1::2])]
D={'basins':json.load(open('basins.json')),'majors':json.load(open('majors.json')),'streams':json.load(open('streams.json')),'lot':lot,'btc':btc,'btha':t['catch'][0]['ha'],'x0':X0}
for s in D['streams'].values():
    for pl in s:
        for i in range(0,len(pl),2): pl[i]-=X0
for b in D['basins']: b['out'][0]-=X0
for m in D['majors']: m['out'][0]-=X0
html=open('template.html').read()
html=html.replace('__DATA__',json.dumps(D,separators=(',',':')))
for k,f,m in [('__HILL__','hill.jpg','image/jpeg'),('__AER__','aerial.jpg','image/jpeg'),('__CON__','contours_a.png','image/png'),('__PACK__','pack.png','image/png')]:
    html=html.replace(k,b64(f,m))
open('/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/east-catchments.html','w').write(html)
print(len(html)//1024,'KB')

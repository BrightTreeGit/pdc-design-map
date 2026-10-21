import json,numpy as np,cv2,os
H=np.array(json.load(open('planH.json'))['H'])
def T(pts):return [[round(float(x),1),round(float(y),1)] for x,y in cv2.perspectiveTransform(np.float32([pts]),H)[0]]
F=[];n=[0]
def add(kind,name,g,pts,stage='now',r=None,notes='',**kw):
    n[0]+=1;geom={'g':g,'pts':T(pts)}
    if r:geom['r']=r
    d={'status':'idea','stage':stage,'createdBy':None,'createdAt':'2026-10-20T05:30:00.000Z','updatedAt':'2026-10-20T05:30:00.000Z','source':"Ange's plan",'kind':kind,'name':name,'geom':geom,'notes':notes};d.update(kw);F.append((f'ap{n[0]:02d}',d))
S="From Ange's landscaping sketch, fitted to the property boundary (positions about ±1–2 m)."
add('building','Home','polygon',[(497,1175),(815,1197),(800,1600),(450,1597)],'now',notes=S+' Roof collects for the tanks.',roof=True)
add('solar','Solar','polygon',[(665,1210),(760,1212),(758,1372),(665,1370)],'now',notes=S)
add('shed','Garage','polygon',[(810,820),(920,822),(918,960),(808,958)],'now',notes=S,roof=True)
add('carport','Carport','polygon',[(735,820),(810,820),(808,958),(735,956)],'now',notes=S)
add('driveway','Driveway','polygon',[(868,370),(945,375),(940,820),(735,820),(745,700),(790,630),(850,580),(868,480)],'now',notes=S)
add('tank','Water tank 30,000 L','point',[(870,1035)],'now',notes=S,vol=30000)
add('tank','Slimline tank 5,000 L','point',[(855,968)],'now',notes=S+' Along the garage wall.',vol=5000)
add('structure','Septic','point',[(760,1005)],'now',notes=S)
add('structure','Septic tank','point',[(775,1070)],'now',notes=S)
add('zone1','Zone 1 · Mixed garden beds','polygon',[(800,1283),(920,1285),(918,1520),(800,1518)],'now',notes=S)
for i,y in enumerate([1320,1365,1410,1455]):add('raisedbed',f'Garden bed {i+1}','polygon',[(822,y),(892,y),(892,y+30),(822,y+30)],'now',notes=S)
add('zone1','Zone 1 · Herbs','polygon',[(435,1325),(475,1325),(472,1500),(432,1500)],'now',notes=S)
add('herbs','Herbs','polygon',[(438,1330),(472,1330),(470,1496),(436,1496)],'now',notes=S)
add('path','Path','line',[(485,1180),(478,1600)],'now',notes=S)
add('steps','Steps (west)','line',[(670,1172),(700,1172)],'now',notes=S)
add('steps','Steps (east)','line',[(625,1690),(655,1690)],'now',notes=S)
add('rockgarden' if False else 'bed','Rock garden','polygon',[(655,1860),(705,1860),(705,1910),(655,1910)],'y2',notes=S)
fr=[('Plum',830,1525),('Plum',830,1665),('Dwarf mulberry',830,1720),('Mandarin',700,1725),('Orange',552,1715),('Yuzu',423,1810),('Cumquat',478,1857)]
for nm,x,y in fr:add('fruittree',nm,'point',[(x,y)],'y2',r=2,notes=S)
add('fruittree','Lemon myrtle','point',[(460,1760)],'y2',r=2,notes=S+' Bush food.')
add('fruittree','Bush food tree (red, unlabelled)','point',[(453,1698)],'y2',r=1.5,notes=S+' Red on the sketch like the lemon myrtle; name to confirm with Ange.')
add('shrub','Leucadendron','point',[(655,1990)],'y2',r=1,notes=S)
add('shrub','Banksia ‘Bird Song’','point',[(698,1998)],'y2',r=1,notes=S)
for i,(x,y) in enumerate([(455,1265),(437,1532)]):add('shrub',f'Flowering shrub {i+1}','point',[(x,y)],'y2',r=1,notes=S+' Yellow on the sketch, like the banksia and leucadendron.')
gums=[(570,318),(675,385),(573,415),(540,462),(612,557),(740,624),(525,765),(525,860),(407,1580),(330,1590),(336,1658),(363,1700),(335,1755),(372,1790),(350,1830),(385,1860)]
for i,(x,y) in enumerate(gums):add('nativetree','Gum' if i!=8 else 'Gum (by house)','point',[(x,y)],'existing',r=3,notes=S+' Native gum on the sketch: confirm on site whether it is an existing tree to keep or a new planting.')
add('nativetree','Ironbark','point',[(830,1860)],'existing',r=4,notes=S+' Large ironbark on the sketch.')
small=[(469,432),(460,530),(450,653),(441,768),(416,868),(711,666),(707,710),(770,561),(805,540),(810,492),(405,1115),(737,1855),(543,1918),(603,1943),(482,1907),(432,1882)]
for i,(x,y) in enumerate(small):add('shrub',f'Small native {i+1}','point',[(x,y)],'y2',r=.8,notes=S+' Small circle on the sketch: understorey native or shrub.')
os.makedirs('docs',exist_ok=True);W=[]
for i,d in F:
    json.dump(d,open(f'docs/{i}.json','w'));W.append({'op':'set','collection':'nac_features','doc_id':i,'file_path':f'/tmp/claude-0/work/nac/docs/{i}.json'})
json.dump(W[:50],open('w1.json','w'));json.dump(W[50:],open('w2.json','w'));print(len(F))
# check plot
from PIL import Image,ImageDraw
ins=json.load(open('inset.json'));im=Image.open('nac_closeup_2021.jpg').convert('RGB');d=ImageDraw.Draw(im)
P=lambda p:((p[0]-ins['x0'])/ins['res'],(p[1]-ins['y0'])/ins['res'])
for i,f in F:
    g=f['geom'];c={'nativetree':(60,200,60),'fruittree':(200,60,180),'shrub':(240,200,40)}.get(f['kind'],(255,255,255))
    if g['g']=='point':x,y=P(g['pts'][0]);r=g.get('r',1)/ins['res'];d.ellipse((x-r,y-r,x+r,y+r),outline=c,width=2)
    else:d.line([P(p) for p in g['pts']+([g['pts'][0]] if g['g']=='polygon' else [])],fill=c,width=2)
im.crop((380,520,1200,920)).save('feat_chk.jpg')

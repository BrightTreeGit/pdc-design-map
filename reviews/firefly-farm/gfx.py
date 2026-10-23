import json,zlib,base64,math,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon,Rectangle,Wedge,Circle
from PIL import Image
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#888','axes.labelcolor':'#333','xtick.color':'#444','ytick.color':'#444'})
GREY='#b9bcb3';ACC='#2a6fc9';INK='#1d2621';MUT='#6b6f73'
B='/home/claude/pdc-design-map/map/sites/nimbin/'
t=json.load(open(B+'terrain.json'));m=t['meta'];R=m['site']['rain']
MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];DAYS=[31,28,31,30,31,30,31,31,30,31,30,31]
feats=json.load(open('/home/claude/pdc-design-map/data-snapshots/trial-firefly/nimbin-combined_features.json'))
A4=(11.69,8.27)
def page(title,sub=None):
    f=plt.figure(figsize=A4);f.text(0.05,0.93,title,fontsize=22,color=INK,weight='bold')
    if sub:f.text(0.05,0.885,sub,fontsize=12.5,color=MUT)
    f.text(0.05,0.03,'Firefly Farm · PDC Group 1 design review graphics · 23 Oct 2026',fontsize=9,color=MUT)
    return f
def src(f,s):f.text(0.95,0.03,s,fontsize=9,color=MUT,ha='right')
pp=PdfPages('/tmp/ffw/Firefly_Farm_design_graphics.pdf')
# 1 cover
f=page('Firefly Farm: design review graphics','Group 1 · Nimbin, Northern Rivers NSW · one graphic per page, for slides or printing')
tiles=[('about 36 ha','property (main block + house parcel)'),('90–430 m','height range; house about 117 m'),('36%','of the land steeper than 50%'),('1,757 mm','mean rain a year (SILO 1995–2025)'),('11%','of the rain falls Jul–Sep'),('8.8 h','winter-solstice sun on the house bench'),('7.8 °C','mean July minimum'),('40,000 L','existing tank storage')]
for i,(v,l) in enumerate(tiles):
    x=0.05+(i%4)*0.235;y=0.58-(i//4)*0.27
    ax=f.add_axes([x,y,0.215,0.22]);ax.axis('off');ax.add_patch(Rectangle((0,0),1,1,fc='#f1f2ee',ec='none',transform=ax.transAxes))
    ax.text(0.08,0.55,v,fontsize=26,color=ACC if i in (2,4) else INK,weight='bold',transform=ax.transAxes);import textwrap;ax.text(0.08,0.3,textwrap.fill(l,24),fontsize=10.5,color=MUT,transform=ax.transAxes,va='top')
f.text(0.05,0.2,'Contents: 2 whole property · 3 house area · 4 rain · 5 temperature · 6 sun and sectors · 7 slope\n8 creek-to-ridge profile · 9 water · 10 harvest calendar · 11 phasing · 12 weekly hours',fontsize=11,color=INK,linespacing=1.6)
src(f,'Sources: map data (NSW 5 m elevation, 2019 aerial), SILO, group draft');pp.savefig(f);plt.close(f)
# helpers for maps
img=Image.open(B+'aerial.jpg');S=1.5
L=np.array(t['lot']).reshape(-1,2)
COL={'zone3':'#d9b81f','zone4':'#7cab3a','zone5':'#2f7a46','customzone':'#3f8fbf','zone1':'#d6453d','zone2':'#e8862a','zone0':'#7d5aa6'}
def drawmap(ax,x0,y0,x1,y1,kinds,labels=True,fs=8):
    crop=img.crop((int(x0*S),int(y0*S),int(x1*S),int(y1*S)));ax.imshow(crop,extent=(x0,x1,y1,y0),alpha=0.85)
    ax.plot(L[:,0],L[:,1],color='white',lw=2.4);ax.plot(L[:,0],L[:,1],color='#c0392b',lw=1.2)
    for st in t['streams']:
        if st['k']>=1:
            p=np.array(st['p']).reshape(-1,2);ax.plot(p[:,0],p[:,1],color='#3a8fe0',lw=0.6+0.5*st['k'])
    for fid,fe in feats.items():
        if fe['kind'] not in kinds:continue
        g=fe['geom'];c=COL.get(fe['kind'],{'swale':'#1aa3c7','flow':'#2878c8','pipe':'#5c6f80','road':'#6b4a2b','screen':'#3b7a3a','path':'#a8794a'}.get(fe['kind'],'#444'))
        if g['g']=='polygon':
            ax.add_patch(Polygon(g['pts'],closed=True,fc=c,ec=c,alpha=0.28,lw=1.5));ax.add_patch(Polygon(g['pts'],closed=True,fc='none',ec=c,lw=1.6))
            if labels:
                p=np.array(g['pts']);ax.text(p[:,0].mean(),p[:,1].mean(),fe['name'].split(' (')[0],fontsize=fs,ha='center',va='center',color=INK,bbox=dict(fc='white',ec='none',alpha=0.75,pad=1.5))
        elif g['g']=='line':
            p=np.array(g['pts']);ax.plot(p[:,0],p[:,1],color=c,lw=2.6,ls='--' if fe['kind'] in ('pipe','path') else '-')
        elif g['g']=='point':
            p=g['pts'][0];ax.plot(p[0],p[1],'o',ms=6,mfc=c,mec='white')
            if labels:ax.annotate(fe['name'].split(' (')[0],p,xytext=(5,4),textcoords='offset points',fontsize=fs-1,color=INK,bbox=dict(fc='white',ec='none',alpha=0.7,pad=1))
    ax.set_xlim(x0,x1);ax.set_ylim(y1,y0);ax.set_xticks([]);ax.set_yticks([]);ax.set_aspect('equal')
def scalebar(ax,x,y,l,lab):ax.plot([x,x+l],[y,y],color='white',lw=4);ax.plot([x,x+l],[y,y],color=INK,lw=2);ax.text(x+l/2,y-6*l/100,lab,ha='center',fontsize=9,color=INK,bbox=dict(fc='white',ec='none',alpha=.8,pad=1))
# 2 whole property
f=page('The whole property: steep bush above a small house bench','Suggested zones over the 2019 aerial. Red = property outline; blue = creeks; dashed box = the group\'s house-area boundary')
ax=f.add_axes([0.05,0.08,0.9,0.78]);drawmap(ax,360,700,1650,1300,['zone3','zone4','zone5','customzone'],labels=False)
for lab,(x,y) in {'Zone 5 · upper bush':(1150,1000),'Zone 4 · lower forested slopes':(680,1020),'Zone 3 · creek flats':(470,960),'Creek riparian buffer':(380,760)}.items():ax.text(x,y,lab,fontsize=10,ha='center',color=INK,bbox=dict(fc='white',ec='none',alpha=.8,pad=2))
ax.add_patch(Rectangle((528,816),103,72,fc='none',ec='white',lw=2.2,ls='--'));ax.text(531,812,'House area (detail on page 3)',fontsize=9,color='white',weight='bold')
scalebar(ax,1450,1270,100,'100 m');ax.annotate('N',(1620,740),xytext=(1620,790),arrowprops=dict(arrowstyle='->',color='white',lw=2),color='white',ha='center',fontsize=12,weight='bold')
src(f,'Map data: NSW 5 m elevation, 2019 aerial; zones are suggestions');pp.savefig(f);plt.close(f)
# 3 house area
f=page('House area: the group plan plus suggestions','Existing buildings and orchard, the group\'s plan (garden, chickens, swale, screen) and suggested additions, over 1 m contours')
ax=f.add_axes([0.05,0.08,0.62,0.78])
hk=['zone1','building','shed','cabin','road','foodforest','bed','raisedbed','chickens','swale','flow','raingarden','screen','pipe','greywater','tank','herbspiral','compost','structure','guild','hives']
x0,y0,x1,y1=520,812,640,912
crop=img.crop((int(x0*S),int(y0*S),int(x1*S),int(y1*S)));ax.imshow(crop,extent=(x0,x1,y1,y0),alpha=0.7)
for c in t['c1']:
    p=np.array(c['p']).reshape(-1,2)
    if p[:,0].max()<x0 or p[:,0].min()>x1 or p[:,1].max()<y0 or p[:,1].min()>y1:continue
    ax.plot(p[:,0],p[:,1],color='#f4e04d' if c['z']%5==0 else '#fff6b0',lw=1.1 if c['z']%5==0 else 0.5,alpha=0.9)
    if c['z']%5==0:
        k=len(p)//2;ax.text(p[k,0],p[k,1],f"{c['z']} m",fontsize=7,color='#5a4d00',bbox=dict(fc='#fff6b0',ec='none',alpha=.8,pad=.5))
saved=img
drawmap.__defaults__=None
def dm2(ax):
    for fid,fe in feats.items():
        if fe['kind'] not in hk:continue
        g=fe['geom'];sug=fe['source'].startswith('Review')
        c={'building':'#575757','shed':'#7a6a58','cabin':'#8a6d3b','road':'#6b4a2b','foodforest':'#5f9e2f','bed':'#9a7420','raisedbed':'#b07a2a','chickens':'#c98a3a','swale':'#1aa3c7','flow':'#2878c8','raingarden':'#4aa3c0','screen':'#3b7a3a','pipe':'#5c6f80','greywater':'#7fa7c9','tank':'#1d6fb8','herbspiral':'#6b9e3a','compost':'#7a5c2e','structure':'#444','guild':'#3f8f3a','hives':'#e0a400','zone1':'#d6453d'}[fe['kind']]
        if g['g']=='polygon':
            ax.add_patch(Polygon(g['pts'],closed=True,fc=c,alpha=0.12 if fe['kind']=='zone1' else 0.35,ec='none'));ax.add_patch(Polygon(g['pts'],closed=True,fc='none',ec=c,lw=1.6,ls='--' if sug else '-'))
        elif g['g']=='line':
            p=np.array(g['pts']);ax.plot(p[:,0],p[:,1],color=c,lw=2.8,ls='--' if (sug or fe['kind']=='pipe') else '-')
        else:
            p=g['pts'][0];ax.plot(p[0],p[1],'s' if sug else 'o',ms=7,mfc=c,mec='white')
dm2(ax)
labs={'Main house':(575,864),'Shed':(580,832),'Cabin':(595,866),'Orchard':(546,843),'Veg beds':(583,879),'Chickens':(560,887),'Swale (level line)':(600,846),'Rain garden':(580,901),'Garden tank':(612,856),'Greywater bananas':(553,879),'Food forest extension':(543,895),'Herb spiral':(575,846),'Compost':(565,840)}
for k,(x,y) in labs.items():ax.text(x,y,k,fontsize=8.5,ha='center',va='center',color=INK,bbox=dict(fc='white',ec='none',alpha=0.8,pad=1.2))
ax.set_xlim(x0,x1);ax.set_ylim(y1,y0);ax.set_xticks([]);ax.set_yticks([]);ax.set_aspect('equal');scalebar(ax,612,905,20,'20 m')
ax2=f.add_axes([0.7,0.1,0.27,0.74]);ax2.axis('off')
txt=['Solid lines: existing and the group plan','Dashed lines, square dots: suggestions','',
'Suggested','• Swale on the level line (about 119 m),','  spillway south to a rain garden','• Privacy screen under 2 m on the berm','• Garden tank on the high side (about 121 m),','  gravity to the beds (about 30 kPa)','• Raised or wicking beds after a soil test','  (arsenic and organochlorines: old banana land)','• Greywater to a banana circle','• Mango guild; native shrubs and macadamia','• Low-fuel zone round the house and cabin','','Contours: 1 m (yellow), 5 m labelled','Positions indicative: check on site']
for i,s in enumerate(txt):ax2.text(0,1-i*0.055,s,fontsize=10.5,color=ACC if s=='Suggested' else INK,weight='bold' if s=='Suggested' else 'normal',va='top')
src(f,'Map data: NSW 5 m elevation, 2019 aerial; group draft 23 Oct 2026');pp.savefig(f);plt.close(f)
# 4 rain
mean=np.array(R['mean']);med=np.array(R['median']);days=np.array(R['days'])
f=page('Only about a tenth of the year\'s rain falls in July to September',f'Mean {mean.sum():,.0f} mm a year (median year {med.sum():,.0f} mm). Bars = mean, dots = median, numbers = rain days')
ax=f.add_axes([0.08,0.12,0.86,0.68]);cols=[ACC if i in (6,7,8) else GREY for i in range(12)]
ax.bar(MON,mean,color=cols,width=0.65);ax.plot(MON,med,'o',color=INK,ms=7)
for i in range(12):ax.text(i,mean[i]+6,f'{days[i]:.0f} d',ha='center',fontsize=9.5,color=MUT)
ax.set_ylabel('Rain (mm)');ax.grid(axis='y',color='#e3e3e3');ax.set_axisbelow(True)
ax.text(7,175,f'Jul–Sep: {mean[6:9].sum():.0f} mm\n({mean[6:9].sum()/mean.sum()*100:.0f}% of the year)',ha='center',color=ACC,fontsize=12,weight='bold')
src(f,'SILO gridded data at the property (Bureau of Meteorology), 1995–2025');pp.savefig(f);plt.close(f)
# 5 temperature
tmin=np.array(R['tmin'])
f=page('Mild nights: the coldest month averages 7.8 °C','Mean daily minimum temperature. Frost is rare on the house bench; cold air drains to the creek flats')
ax=f.add_axes([0.08,0.12,0.86,0.68]);ax.plot(MON,tmin,'-o',color=ACC,lw=2.5,ms=7)
for i,v in enumerate(tmin):ax.text(i,v+0.6,f'{v:.1f}',ha='center',fontsize=10,color=INK)
ax.axhline(2,color='#c0392b',lw=1,ls='--');ax.text(11.4,2.4,'frost likely below about 2 °C on clear nights',ha='right',fontsize=10,color='#c0392b')
ax.set_ylim(0,22);ax.set_ylabel('°C');ax.grid(axis='y',color='#e3e3e3')
ax.text(0.2,20.5,'Brief: summer extremes of 40–44 °C; winter lows to about −3 to 0 °C in hollows',fontsize=10.5,color=MUT)
src(f,'SILO gridded mean minimum temperature, 1995–2025');pp.savefig(f);plt.close(f)
# 6 sun & sectors
f=page('Sun and sectors at the house','Corrected sun bearings for about 28.6° S (the draft has winter and summer swapped), with wind, fire and view wedges')
ax=f.add_axes([0.03,0.07,0.55,0.8]);ax.set_aspect('equal');ax.axis('off')
def wedge(a0,a1,r,c,al,lab=None,lr=None):
    # bearings clockwise from north -> matplotlib angle
    th1=90-a1;th2=90-a0
    ax.add_patch(Wedge((0,0),r,th1,th2,fc=c,alpha=al,ec=c))
    if lab:
        mid=math.radians(90-((a0+a1)/2 if a1>a0 else (a0+a1+360)/2));rr=lr or r*0.75;ax.text(rr*math.cos(mid),rr*math.sin(mid),lab,ha='center',va='center',fontsize=9.5,color=INK,bbox=dict(fc='white',ec='none',alpha=.7,pad=1))
wedge(297,63+360,1.0,'#e0a400',0.18) ;wedge(243,117+360,0.85,'#e2572b',0.12)
for b,lab,c in [(63,'Winter sunrise 63°','#b07d00'),(297,'Winter sunset 297°','#b07d00'),(117,'Summer sunrise 117°','#c0441e'),(243,'Summer sunset 243°','#c0441e')]:
    a=math.radians(90-b);ax.plot([0,1.1*math.cos(a)],[0,1.1*math.sin(a)],color=c,lw=1.5);ax.text(1.22*math.cos(a),1.22*math.sin(a),lab,ha='center',va='center',fontsize=9.5,color=c)
wedge(250,330,0.62,'#c0311f',0.25,'Fire: W–NW,\nupslope from creek')
wedge(100,200,0.55,'#4f86b8',0.22,'Winds S–SE–E\n(group)')
wedge(195,235,0.9,'#8a6fb0',0.18,'View',0.8)
wedge(330,390,0.45,'#4f86b8',0.15,'N winds')
wedge(15,60,0.35,'#8a6fb0',0.25)
ax.plot(0,0,'o',color=INK,ms=8);ax.text(0,-0.08,'House',ha='center',fontsize=10)
ax.annotate('N',(0,1.38),xytext=(0,1.25),arrowprops=dict(arrowstyle='->',lw=2),ha='center',fontsize=13,weight='bold');ax.set_xlim(-1.45,1.45);ax.set_ylim(-1.3,1.45)
ax2=f.add_axes([0.62,0.15,0.34,0.62]);v=[8.8,11.0,12.3]
ax2.bar(['Winter\nsolstice','Equinox','Summer\nsolstice'],v,color=[ACC,GREY,GREY],width=.6)
for i,x in enumerate(v):ax2.text(i,x+0.2,f'{x} h',ha='center',fontsize=12,weight='bold' if i==0 else 'normal')
ax2.set_title('Hours of direct sun on the house bench\n(terrain only; trees not counted)',fontsize=11,color=INK,loc='left');ax2.set_ylim(0,14);ax2.set_yticks([])
ax2.text(-0.4,13.3,'Noon sun height: about 38° in June, 85° in December',fontsize=9.5,color=MUT)
src(f,'Sun angles calculated for 28.57° S; sun hours from the map (NSW 5 m elevation)');pp.savefig(f);plt.close(f)
# 7 slope
sh=m['lotSlopeShare'];labels=['0–10%','10–18%','18–25%','25–33%','33–50%','over 50%'];vals=[s[2]*100 for s in sh]
f=page('Over a third of the property is steeper than 50%','Share of the property in each slope class. Productive use belongs on the gentle ground: the house bench and creek flats')
ax=f.add_axes([0.08,0.18,0.86,0.62]);ax.bar(labels,vals,color=[GREY]*5+[ACC],width=.6)
for i,x in enumerate(vals):ax.text(i,x+0.8,f'{x:.0f}%',ha='center',fontsize=13)
ax.set_ylabel('Share of property (%)');ax.set_xlabel('Slope');ax.set_ylim(0,42)
for i,s in enumerate(['gardens, buildings','gentle tracks, pasture','orchards on contour','tree crops, care','forest, trails only','forest (Zone 5)']):ax.text(i,-6.0,s,ha='center',fontsize=9,color=MUT)
src(f,'Map data: NSW 5 m elevation (2 m analysis)');pp.savefig(f);plt.close(f)
# 8 profile
D1=t['meta']['dem1'];arr=np.frombuffer(zlib.decompress(base64.b64decode(D1['b64'])),np.int16).reshape(D1['h'],D1['w'])/10
xs=np.arange(425,760);zs=[arr[863-D1['y0'],x-D1['x0']] for x in xs]
f=page('Creek to ridge: the house sits on a bench at about 117 m','West–east profile through the house (vertical scale exaggerated about 3 times)')
ax=f.add_axes([0.08,0.14,0.86,0.66]);ax.fill_between(xs-425,zs,85,color='#e6e2d6');ax.plot(xs-425,zs,color=INK,lw=2)
for x,lab in [(431,'Creek\n~93 m'),(574,'House\n~117 m'),(595,'Cabin\n~120 m'),(588,''),(700,'Ridge\n~142 m')]:
    if lab:
        z=arr[863-D1['y0'],x-D1['x0']];ax.plot(x-425,z,'o',color=ACC,ms=7);ax.text(x-425,z+4,lab,ha='center',fontsize=10)
ax.annotate('swale on the\nlevel line (~119 m)',(588-425,arr[863-D1['y0'],588-D1['x0']]),xytext=(150,100),arrowprops=dict(arrowstyle='->',color=MUT),fontsize=10,color=MUT)
ax.set_xlabel('Distance east from the creek (m)');ax.set_ylabel('Height (m)');ax.set_ylim(85,155);ax.grid(color='#eee')
src(f,'Map data: NSW 5 m elevation');pp.savefig(f);plt.close(f)
# 9 water
roofE=0.85;house=300;shed=160
sup_h=np.array(med)*house*roofE/1000;sup_s=np.array(med)*shed*roofE/1000
use_house=np.array(DAYS)*390/1000;garden=np.array([0,0,0,0,0,0,0,2.5,2.5,2.5,2.5,0])*np.array(DAYS)/7*1.0
f=page('Roofs out-catch household use, except in the dry spring','Typical (median) year, kL a month. Supply: house and shed roofs. Use: main house plus a 100 m² vegetable patch')
ax=f.add_axes([0.08,0.12,0.86,0.66]);x=np.arange(12);w=0.38
ax.bar(x-w/2,sup_h,w,color=GREY,label='House roof (about 300 m²)');ax.bar(x-w/2,sup_s,w,bottom=sup_h,color='#d9dbd3',label='Shed roof (about 160 m²)')
ax.bar(x+w/2,use_house,w,color=ACC,label='Main house (about 2.6 people at 150 L a day)');ax.bar(x+w/2,garden,w,bottom=use_house,color='#8fb5e8',label='Veg patch, dry spring (2,500 L a week per 100 m²)')
ax.set_xticks(x,MON);ax.set_ylabel('kL a month');ax.legend(frameon=False,fontsize=10,loc='upper right');ax.grid(axis='y',color='#eee');ax.set_axisbelow(True)
ax.text(7.5,max(sup_h+sup_s)*0.62,'Aug–Sep: use exceeds\nroof catch; the 40 kL\nof tanks fills the gap',ha='center',fontsize=11,color=ACC,weight='bold')
src(f,'Rain: SILO median 1995–2025; roof sizes approximate; 85% capture');pp.savefig(f);plt.close(f)
# 10 harvest calendar
cal=[('Lemon (Eureka/Lisbon)',[6,7,8,9]),('Bush lemon / Meyer',[5,6,7,8]),('Pink grapefruit',[6,7,8,9,10]),('Valencia orange',[10,11,12,1,2]),('Quince',[3,4,5]),('Jaboticaba (flushes)',[3,4,5,9,10,11]),('Grumichama',[11,12]),('Panama berry',list(range(1,13))),('Low-chill peach',[10,11]),('Low-chill nectarine',[11,12]),('Custard apple / atemoya',[4,5,6,7]),('Subtropical blueberry',[8,9,10,11,12,1]),('Midyim',[2,3,4]),('Acerola',[12,1,2,3,4,5]),('Pitomba',[1,2,3]),('Lychee',[12,1,2])]
exist=6
f=page('Fruit in every month: the harvest calendar','From the group\'s species list. Dark = existing trees; light = possible additions')
ax=f.add_axes([0.25,0.1,0.7,0.74])
for i,(n,ms) in enumerate(cal):
    for mo in ms:ax.add_patch(Rectangle((mo-1+0.05,i+0.15),0.9,0.7,fc=ACC if i<exist else '#9fc0ea',ec='none'))
ax.set_xlim(0,12);ax.set_ylim(len(cal),0);ax.set_xticks(np.arange(12)+0.5,MON);ax.set_yticks(np.arange(len(cal))+0.5,[c[0] for c in cal]);ax.tick_params(length=0)
for s in ax.spines.values():s.set_visible(False)
ax.axhline(exist,color=MUT,lw=0.8);ax.xaxis.tick_top()
src(f,'Group draft species list; months as given by the group');pp.savefig(f);plt.close(f)
# 11 phasing
f=page('Phasing: water, soil and approvals first','A staged plan that fits about 20–30 hours a week')
ax=f.add_axes([0.05,0.1,0.9,0.74]);ax.axis('off')
ph=[('First 3 months','Watch water in heavy rain\nSoil tests (+ arsenic, organochlorines)\nCouncil and RFS: cabins, stall\nGutters, first flush, garden tank\nHerb spiral, compost, 3–4 beds'),('Year 1','Chickens and deep-litter run\nOrchard understorey (Mar–May)\nSwale + spillway + screen\nLantana from the good bush out\nFirst guest income if approved'),('Years 2–5','Food forest + natives, netting\nCabins if approved\nBees; a few sheep if time allows\nPond site from observed flows\nWater-powered creek pump?'),('Long term','Syntropic rows on lower slopes\nBush-food enterprise\nConservation agreement\nChosen recreation features')]
for i,(h,b) in enumerate(ph):
    x=i*0.25;ax.add_patch(Rectangle((x+0.005,0.62),0.235,0.12,fc=ACC if i==0 else GREY,ec='none',transform=ax.transAxes))
    ax.text(x+0.02,0.68,h,fontsize=15,weight='bold',color='white' if i==0 else INK,va='center',transform=ax.transAxes)
    ax.text(x+0.015,0.57,b,fontsize=9.6,va='top',color=INK,transform=ax.transAxes,linespacing=1.8)
    if i<3:ax.annotate('',(x+0.25,0.68),(x+0.235,0.68),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',lw=2,color=MUT))
src(f,'Design review, 23 Oct 2026');pp.savefig(f);plt.close(f)
# 12 hours
hrs=[('Mowing and whipper-snipping (now)',4.5),('Vegetable beds (30–50 m²)',3),('Chickens (5–8 birds)',1),('Orchard and food forest care',2.5),('Compost and mulch',1),('Water checks, gutters, pumps',0.5),('Lantana and weeds',2),('Bees (native hive)',0.2)]
f=page('A weekly hours guide: about 15 hours for the core systems','A rough guide to stay inside the brief\'s 20–30 hours a week. Mulched beds and grazing cut the mowing')
ax=f.add_axes([0.38,0.12,0.56,0.7]);names=[h[0] for h in hrs][::-1];v=[h[1] for h in hrs][::-1]
ax.barh(names,v,color=[ACC if n.startswith('Mowing') else GREY for n in names],height=.6)
for i,x in enumerate(v):ax.text(x+0.08,i,f'{x:g} h',va='center',fontsize=11)
ax.set_xlabel('Hours a week (rough guide)');ax.set_xlim(0,6);ax.text(3.2,0.3,f'Total about {sum(v):.0f} h a week',fontsize=13,color=ACC,weight='bold')
src(f,'Estimates for discussion; the brief gives 4–5 h of mowing now');pp.savefig(f);plt.close(f)
pp.close();print('ok')

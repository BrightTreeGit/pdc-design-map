import numpy as np, json, base64, io, math
from scipy import ndimage
from PIL import Image
W='/tmp/claude-0/work/'
dem1=np.load(W+'dem2022.npy').astype(np.float32)          # 1 m, x=E-492000, y=7043000-N
rec=np.load(W+'rec.npy'); acc=np.load(W+'acc.npy'); catchBT=np.load(W+'catch.npy')   # 2 m grid
X0,X1=1100,2000   # region in metres
c0,c1=X0//2,X1//2
n=1000; dem2=dem1.reshape(1000,2,1000,2).mean(axis=(1,3))
inR=np.zeros((n,n),bool); inR[:,c0:c1]=True
idx=np.arange(n*n).reshape(n,n)
recf=rec.ravel(); accf=acc.ravel(); inRf=inR.ravel()
STREAM=30000.0   # m2: a stream starts at 3 ha of catchment
st=accf>=STREAM
# count stream inflows
inflow=np.zeros(n*n,int)
srcs=np.nonzero(st&(recf!=np.arange(n*n)))[0]
np.add.at(inflow,recf[srcs],1)
leaves=(~inRf[recf])|(recf==np.arange(n*n))
node=(st&(inflow>=2))|(inRf&leaves)
node&=inRf
order=np.argsort(-accf)
lab=np.full(n*n,-1,int)
for c in order:
    if not inRf[c]: continue
    if node[c]: lab[c]=c
    else:
        r=recf[c]; lab[c]=lab[r] if inRf[r] else c
# merge small basins (<1 ha) into the basin downstream
def area(L):
    u,cnt=np.unique(L[L>=0],return_counts=True);return dict(zip(u,cnt*4.0))
for it in range(6):
    A=area(lab);changed=0
    for b,a in sorted(A.items(),key=lambda t:t[1]):
        if a>=10000: continue
        r=recf[b]
        if inRf[r] and r!=b and lab[r]!=b:
            lab[lab==b]=lab[r];changed+=1
    if not changed: break
A=area(lab)
# drop tiny edge slivers (<0.3 ha) to 'edge'
ids=[b for b,a in sorted(A.items(),key=lambda t:-t[1]) if a>=3000]
remap={b:i+1 for i,b in enumerate(ids)}
L=np.array([remap.get(v,0) for v in lab]).reshape(n,n)
print('basins',len(ids))
# where each outlet goes: follow downstream for up to 4000 steps
lot=json.load(open('/home/claude/pdc-design-map/map/terrain.json'))
from matplotlib.path import Path as MP
lotP=np.array(lot['lot']).reshape(-1,2)/2
yy,xx=np.mgrid[0:n,0:n]; lotM=MP(lotP).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(n,n).ravel()
info=[]
for b in ids:
    cells=np.nonzero(lab==b)[0];a=len(cells)*4/1e4
    zz=dem2.ravel()[cells];oy,ox=divmod(b,n)
    c=b;toBT=False;toLot=False;steps=0
    while steps<5000:
        if catchBT.ravel()[c]: toBT=True
        if lotM[c]: toLot=True;break
        r=recf[c]
        if r==c: break
        c=r;steps+=1
    gy,gx=np.gradient(dem2,2.0);sl=np.degrees(np.arctan(np.hypot(gx,gy))).ravel()[cells]
    ey,ex=divmod(c,n)
    side='west' if ex<c0 else 'east' if ex>=c1-1 else 'north' if ey<=1 else 'south' if ey>=n-2 else 'within'
    exitd=('west' if ox<=c0 else 'east' if ox>=c1-1 else 'north' if oy<=0 else 'south' if oy>=n-1 else 'a stream junction')
    info.append({'id':int(remap[b]),'ha':round(a,2),'zmax':round(float(zz.max()),1),'zmin':round(float(zz.min()),1),'slope':round(float(np.mean(sl)),1),
      'out':[int(ox*2+1),int(oy*2+1)],'outz':round(float(dem2.ravel()[b]),1),'acc_ha':round(float(accf[b])/1e4,1),'toLot':bool(toLot),'toBT':bool(toBT),'exit':exitd})
json.dump(info,open('basins.json','w'))
# streams as polylines (2 m grid -> metres), width by catchment
seg=[]
sel=np.nonzero(st&inRf)[0]
for c in sel:
    r=recf[c]
    if r==c: continue
    y0,x0=divmod(c,n);y1,x1=divmod(r,n)
    seg.append([int(x0*2+1),int(y0*2+1),int(x1*2+1),int(y1*2+1),round(float(accf[c])/1e4,1)])
# chain segments into polylines per class
cls=lambda a:0 if a<10 else 1 if a<50 else 2 if a<200 else 3
from collections import defaultdict
nxt={};
for s in seg: nxt[(s[0],s[1])]=s
heads=[s for s in seg if not any(True for _ in [0])]
# simple: output segments grouped by class with merged consecutive pieces
lines=defaultdict(list)
used=set()
inc=defaultdict(int)
for s in seg: inc[(s[2],s[3])]+=1
starts=[s for s in seg if inc[(s[0],s[1])]!=1]
for s in starts:
    k=cls(s[4]);pl=[s[0],s[1],s[2],s[3]];cur=s;used.add((s[0],s[1]))
    while True:
        p=(cur[2],cur[3]);nx=nxt.get(p)
        if nx is None or inc[p]!=1 or cls(nx[4])!=k or p in used: break
        used.add(p);pl+= [nx[2],nx[3]];cur=nx
    lines[k].append(pl)
    # continue next piece starting at p as a new start if different class
for s in seg:
    if (s[0],s[1]) not in used:
        lines[cls(s[4])].append([s[0],s[1],s[2],s[3]])
streams={str(k):v for k,v in lines.items()}
json.dump(streams,open('streams.json','w'))
print({k:len(v) for k,v in streams.items()})
# DEM + labels packed PNG at 2 m: R,G = z*10 (16 bit), B = basin id
R=dem2[:,c0:c1];Z=np.clip(np.round(R*10),0,65535).astype(np.uint16)
img=np.dstack([(Z>>8).astype(np.uint8),(Z&255).astype(np.uint8),np.clip(L[:,c0:c1],0,255).astype(np.uint8)])
Image.fromarray(img,'RGB').save('pack.png',optimize=True)
# hillshade 1 m
D=dem1[:,X0:X1];gy,gx=np.gradient(ndimage.gaussian_filter(D,0.8));az,alt=np.radians(315),np.radians(40)
slope=np.arctan(np.hypot(gx,gy));aspect=np.arctan2(-gx,gy)
hs=np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-aspect)
hs=np.clip(hs,0,1)
Image.fromarray((hs*255).astype(np.uint8)).save('hill.jpg',quality=72)
# contours raster 1 m: 2 m minor, 10 m major
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
Ds=ndimage.gaussian_filter(D,1.5)
fig=plt.figure(figsize=(9,20),dpi=100);ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,900);ax.set_ylim(2000,0);ax.axis('off')
lv=np.arange(40,250,2);mj=[l for l in lv if l%10==0];mn=[l for l in lv if l%10]
ax.contour(np.arange(900)+.5,np.arange(2000)+.5,Ds,levels=mn,colors='#000',linewidths=0.35,alpha=.55)
cs=ax.contour(np.arange(900)+.5,np.arange(2000)+.5,Ds,levels=mj,colors='#000',linewidths=0.9,alpha=.85)
ax.clabel(cs,fmt='%d',fontsize=6.5,inline=True,inline_spacing=2)
fig.savefig('contours.png',transparent=True);plt.close(fig)
im=Image.open('contours.png').convert('LA');a=np.array(im)[...,1];Image.fromarray(a).save('contours_a.png',optimize=True)
# aerial crop
A_=Image.open('/home/claude/pdc-design-map/map/aerial.jpg');s=A_.width/2000
A_.crop((int(X0*s),0,int(X1*s),A_.height)).resize((900,2000)).save('aerial.jpg',quality=68)
import os
for f in ['pack.png','hill.jpg','contours_a.png','aerial.jpg','streams.json','basins.json']:print(f,os.path.getsize(f)//1024,'KB')
# major catchments: where the water finally leaves the mapped area
term={}
for b in ids:
    c=b
    while True:
        r=recf[c]
        if r==c or not inRf[r]: break
        c=r
    term[b]=c
T=sorted(set(term.values()),key=lambda t:-sum(len(np.nonzero(lab==b)[0]) for b in ids if term[b]==t))
maj=[]
for k,t in enumerate(T):
    bs=[b for b in ids if term[b]==t];ha=sum(len(np.nonzero(lab==b)[0]) for b in bs)*4/1e4
    ty,tx=divmod(t,n);r=recf[t];ry,rx=divmod(r,n)
    if r==t: side='east' if tx>=c1-2 else 'north' if ty<=1 else 'south' if ty>=n-2 else 'a low spot (sink)'
    else: side='west' if rx<c0 else 'east' if rx>=c1 else 'north' if ry<ty else 'south'
    # does it reach the lot / BT catchment
    c=t;toBT=False;toLot=False
    for _ in range(6000):
        if catchBT.ravel()[c]: toBT=True
        if lotM[c]: toLot=True;break
        r=recf[c]
        if r==c: break
        c=r
    maj.append({'id':k+1,'ha':round(ha,1),'side':side,'out':[int(tx*2+1),int(ty*2+1)],'outz':round(float(dem2.ravel()[t]),1),'toBT':bool(toBT),'toLot':bool(toLot),'basins':[int(remap[b]) for b in bs],'acc_ha':round(float(accf[t])/1e4,1)})
for x in info:
    for m in maj:
        if x['id'] in m['basins']: x['major']=m['id']
json.dump(info,open('basins.json','w'));json.dump(maj,open('majors.json','w'))
for m in maj: print(m['id'],m['ha'],m['side'],m['outz'],'BT' if m['toBT'] else '','LOT' if m['toLot'] else '',m['acc_ha'],len(m['basins']))

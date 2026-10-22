import numpy as np, json, math, os
from scipy import ndimage
from PIL import Image
from proj import ll2mga
Z=np.load('dem15.npy').astype(np.float32);Z[Z<-1000]=0
filled=np.load('filled.npy');rec=np.load('rec.npy');acc=np.load('acc.npy');sea=np.load('sea.npy');term=np.load('term.npy')
H,W=Z.shape;R=15;E0=480000;N1=7066000
A=json.load(open('anal.json'))
# relief: hypsometric tint * hillshade, sea blue
Zs=ndimage.gaussian_filter(Z,0.8);gy,gx=np.gradient(Zs,R);dzdx,dzdy=gx,-gy
def hs(az,alt):
    az=math.radians(az);alt=math.radians(alt);lx,ly,lz=math.sin(az)*math.cos(alt),math.cos(az)*math.cos(alt),math.sin(alt)
    return (-dzdx*lx-dzdy*ly+lz)/np.sqrt(dzdx**2+dzdy**2+1)
Hs=np.clip(0.55*hs(315,35)+0.25*hs(270,40)+0.2*hs(0,45),0,1)
t=np.clip(Z/560,0,1)**0.6
stops=np.array([[0,92,140,96],[0.25,140,168,104],[0.5,190,180,122],[0.75,176,146,104],[1,236,228,214]],float)
tint=np.stack([np.interp(t,stops[:,0],stops[:,c]) for c in (1,2,3)],-1)
rgb=np.clip(tint*(0.3+0.85*Hs)[...,None],0,255)
rgb[sea]=(170,200,222)
Image.fromarray(rgb.astype(np.uint8)).save('relief.jpg',quality=76)
g=(np.clip(0.2+0.85*Hs,0,1)*255);g=np.dstack([g,g,g]);g[sea]=(205,220,232)
Image.fromarray(g.astype(np.uint8)).save('hill.jpg',quality=74)
# contours alpha 20 m minor, 100 m major
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
Zc=ndimage.gaussian_filter(Z,1.2);Zc[sea]=np.nan
fig=plt.figure(figsize=(W/100,H/100),dpi=100);ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,W);ax.set_ylim(H,0);ax.axis('off')
xs=np.arange(W)+.5;ys=np.arange(H)+.5
ax.contour(xs,ys,Zc,levels=[l for l in range(20,600,20) if l%100],colors='#000',linewidths=0.3,alpha=.5)
cs=ax.contour(xs,ys,Zc,levels=list(range(100,600,100)),colors='#000',linewidths=0.8,alpha=.85)
ax.clabel(cs,fmt='%d m',fontsize=6,inline=True)
fig.savefig('con.png',transparent=True);plt.close(fig)
a=np.array(Image.open('con.png').convert('LA'))[...,1];Image.fromarray(a).save('con_a.png',optimize=True)
# majors and labels at 30 m
majors=A['majors'];mid={m:i+1 for i,m in enumerate(majors)}
L=np.array([mid.get(v,0) for v in term]).reshape(H,W);L[sea]=0
L2=L[::2,::2];Z2=Z.reshape(H//2,2,W//2,2).mean((1,3)) if W%2==0 else Z[::2,::2]
Z2=Z[::2,::2];Zq=np.clip(np.round(Z2*10),0,65535).astype(np.uint16)
seaq=sea[::2,::2]
pack=np.dstack([(Zq>>8).astype(np.uint8),(Zq&255).astype(np.uint8),np.where(seaq,255,L2).astype(np.uint8)])
Image.fromarray(pack,'RGB').save('pack.png',optimize=True)
# major info: where each reaches the sea / edge
mouths={'Maroochy River mouth, Maroochydore':(153.0950,-26.6435),'Mooloolah River mouth, Mooloolaba':(153.1325,-26.6855),'Currimundi Lake':(153.1380,-26.7650),'Pumicestone Passage, Caloundra':(153.1500,-26.8020)}
MM={k:ll2mga(*v) for k,v in mouths.items()}
info=[]
for m in majors:
    r,c=divmod(m,W);E,N=E0+(c+.5)*R,N1-(r+.5)*R
    # find nearest land cell upstream with max acc draining to it
    cells=np.nonzero(term==m)[0]
    if sea.ravel()[m]:
        kind='sea'
        near=min(MM,key=lambda k:math.hypot(MM[k][0]-E,MM[k][1]-N));dk=math.hypot(MM[near][0]-E,MM[near][1]-N)
    else: kind='edge';near=None;dk=None
    side='north' if r<=1 else 'south' if r>=H-2 else 'west' if c<=1 else 'east' if c>=W-2 else ''
    info.append({'id':mid[m],'km2':A['area'][str(m)],'kind':kind,'at':[round((E-E0)/R,1),round((N1-N)/R,1)],'near':near if dk is not None and dk<9000 else None,'side':side})
# streams >= 1 km2 as polylines (grid units)
thr=1e6;st=(acc>=thr)&~sea.ravel()
idx=np.nonzero(st)[0];inc=np.zeros(H*W,np.int32);np.add.at(inc,rec[idx],1)
segs=[]
used=np.zeros(H*W,bool)
starts=[k for k in idx if inc[k]!=1]
def cls(a):return 0 if a<5e6 else 1 if a<25e6 else 2 if a<100e6 else 3
lines={0:[],1:[],2:[],3:[]}
for s in starts:
    k=s;cl=cls(acc[k]);pl=[]
    r,c=divmod(int(k),W);pl+=[c,r]
    while True:
        n=rec[k]
        if n==k: break
        r,c=divmod(int(n),W);pl+=[c,r]
        if not st[n] or inc[n]!=1 or cls(acc[n])!=cl: break
        k=n
    lines[cl].append(pl)
streams={str(k):v for k,v in lines.items() if v}
print({k:len(v) for k,v in streams.items()},sum(len(p) for v in streams.values() for p in v)//2,'pts')
# places (approximate, for orientation)
P={'Maroochydore':(153.095,-26.655),'Mooloolaba':(153.119,-26.682),'Buderim':(153.052,-26.684),'Caloundra':(153.130,-26.800),'Nambour':(152.959,-26.627),'Palmwoods':(152.961,-26.687),'Eudlo':(152.958,-26.729),'Mooloolah':(152.963,-26.762),'Landsborough':(152.966,-26.809),'Maleny':(152.851,-26.759),'Sippy Downs':(153.062,-26.717),'Kawana':(153.125,-26.720)}
places=[[k,round((ll2mga(*v)[0]-E0)/R,1),round((N1-ll2mga(*v)[1])/R,1)] for k,v in P.items()]
t=json.load(open('/home/claude/pdc-design-map/map/terrain.json'))
loc=lambda x,y:[round((492000+x-E0)/R-.5,2),round((N1-(7043000-y))/R-.5,2)]
lot=[loc(x,y) for x,y in zip(t['lot'][0::2],t['lot'][1::2])];bc=t['catch'][0]['p'];btc=[loc(x,y) for x,y in zip(bc[0::2],bc[1::2])]
D={'W':W,'H':H,'R':R,'majors':info,'streams':streams,'path':A['path'],'dist':A['dist'],'z':A['z'],'est':A['estuary'],'edist':A['edist'],'mouth':A['mouth'],'places':places,'lot':lot,'btc':btc,'btha':t['catch'][0]['ha']}
json.dump(D,open('data.json','w'),separators=(',',':'))
for f in ['relief.jpg','hill.jpg','con_a.png','pack.png','data.json']:print(f,os.path.getsize(f)//1024,'KB')

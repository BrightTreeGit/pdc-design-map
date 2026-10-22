import numpy as np, json, base64, zlib
from scipy import ndimage
from PIL import Image
from matplotlib.path import Path as MP
W=np.load('/tmp/claude-0/work/canopy/eff_winter.npy'); E=np.load('/tmp/claude-0/work/canopy/eff_equinox.npy')
acc=np.load('/tmp/claude-0/work/acc.npy')
dem=np.load('/tmp/claude-0/work/dem2022.npy').astype(np.float32)
d2=dem.reshape(1000,2,1000,2).mean(axis=(1,3))
gy,gx=np.gradient(ndimage.gaussian_filter(d2,1.0),2.0); slope=np.hypot(gx,gy)  # rise/run
twi=np.log((acc/2.0+1)/np.maximum(slope,0.02))
M='/home/claude/pdc-design-map/map/'
t=json.load(open(M+'terrain.json')); ex=json.load(open(M+'extra.json'))
cold=np.frombuffer(zlib.decompress(base64.b64decode(ex['cold'])),dtype=np.uint8); n=int(np.sqrt(cold.size)); cold=cold.reshape(n,n).astype(float)
if n!=1000: cold=ndimage.zoom(cold,1000/n,order=1)
yy,xx=np.mgrid[0:1000,0:1000]; L=np.array(t['lot']).reshape(-1,2)/2
lot=MP(L).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(1000,1000)
# productivity residual (4 m grid) from canopy npz
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/'
z=np.load(D+'canopy_bright-tree_2022.npz'); z8=np.load(D+'canopy_bright-tree_2008.npz')
def blk(h,b=4):
    a=h.reshape(2000//b,b,2000//b,b).transpose(0,2,1,3).reshape(2000//b,2000//b,b*b);return np.nanpercentile(a,95,axis=2)
def chmf(zz,s):
    top=zz['top'].astype(np.float32);h=np.clip(top-dem,0,85);f=np.where(np.isfinite(h),h,-1);f=ndimage.grey_dilation(f,size=(s,s));f[f<0]=np.nan;return np.where(np.isfinite(h),h,f)
import warnings;warnings.filterwarnings('ignore')
B22=blk(chmf(z,3));B08=blk(chmf(z8,5));g=B22-B08;ok=np.isfinite(g)&np.isfinite(B08)&(B08>=3)&(B08<=45)
bins=np.arange(3,46,3);idx=np.digitize(B08,bins);med=np.full(g.shape,np.nan)
for i in range(1,len(bins)):
    m=ok&(idx==i)
    if m.sum()>50: med[m]=np.median(g[m])
res=np.where(ok,g-med,0); prod=ndimage.zoom(ndimage.uniform_filter(np.nan_to_num(res),3),2,order=1)
# classes
twl=twi[lot]; t85,t60=np.percentile(twl,[85,60])
wet=twi>=t85; moist=(twi>=t60)&~wet
# wet spots marked on the map (rock pools, ponds, water/drainage observations): 10 m buffer
import os
WS=json.load(open('wetspots.json')) if os.path.exists('wetspots.json') else []
ws=np.zeros_like(wet)
for p in WS:
    P=np.array(p)/2; ws|=MP(P).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(1000,1000) if len(P)>2 else ws
    if len(P)<=2: ws[int(P[0][1]),int(P[0][0])]=True
ws=ndimage.binary_dilation(ws,iterations=5); wet|=ws; moist&=~wet
frost=cold>60
deg=np.degrees(np.arctan(slope))
sun=np.select([W>=4, (W>=2)|(E>=5), (W>=0.5)&(E>=2)],[3,2,1],0)   # 3 full,2 part,1 dappled,0 deep
cls=np.zeros((1000,1000),np.uint8)
# 1 full-sun food, 2 part-sun food, 3 dappled shade crops, 4 deep moist shade, 5 forest only (steep or deep dry shade), 9 frost pocket overrides tender
cls[sun==3]=1; cls[sun==2]=2; cls[sun==1]=3
cls[(sun==0)&(wet|moist)]=4; cls[(sun==0)&~(wet|moist)]=5
cls[deg>27]=5   # >50% slope stays forest (LFW advice)
cls[~lot]=0
# 6 openable: good growing ground near the house that lopping could open
open_=lot&(cls>=4)&(deg<=27)&(prod>1.0)&(np.hypot(xx+.5-450,yy+.5-467.5)*2<=120)
cls[open_]=6
frostp=frost&np.isin(cls,[1,2,3,6])
names={6:'Openable with lopping: fast-growing ground near the house, shaded now',1:'Full sun: citrus, mango, dragon fruit, pineapple, chilli',2:'Part sun: avocado, banana, macadamia, sapotes, papaya',3:'Dappled shade: coffee, cacao, ginger, turmeric, native ginger',4:'Deep moist shade: vanilla, ferns, mushrooms, native understorey',5:'Forest only: steep (over 27°) or deep dry shade'}
area={k:round(float((cls==k).sum()*4/1e4),3) for k in names}
print(area,'frost-flag ha',round(float(frostp.sum()*4/1e4),3),'wet ha in lot',round(float((wet&lot).sum()*4/1e4),2))
# focus: within 80 m of house (900,935) map coords -> grid (450,467)
hx,hy=450,467.5; R=np.hypot(xx+.5-hx,yy+.5-hy)*2
foc=(R<=80)&lot
print('near house',{k:round(float(((cls==k)&foc).sum()*4),0) for k in names})
# best patches near house: label connected sunny/part cells
best=[]
for k in (1,2,3,6):
    lab,nl=ndimage.label((cls==k)&foc)
    for i in range(1,nl+1):
        m=lab==i; a=m.sum()*4
        if a<40: continue
        cy,cx=ndimage.center_of_mass(m)
        best.append(dict(cls=int(k),area=int(a),x=round(cx*2+1),y=round(cy*2+1),winter=round(float(W[m].mean()),1),equinox=round(float(E[m].mean()),1),slope=round(float(deg[m].mean())),wet=round(float((wet[m]|moist[m]).mean()*100)),frost=bool(frostp[m].mean()>0.3),grow=round(float(prod[m].mean()),1)))
best.sort(key=lambda b:(b['cls'],-b['area']))
for b in best: print(b)
np.save('cls.npy',cls); np.save('frost.npy',frostp); np.save('wet.npy',wet)
json.dump(dict(area=area,frostHa=round(float(frostp.sum()*4/1e4),3),near=best,names=names),open('niche.json','w'))

col={1:(250,200,60,210),2:(240,140,60,200),3:(120,190,90,190),4:(40,140,150,170),5:(70,90,70,35),6:(170,110,210,190)}
img=np.zeros((1000,1000,4),np.uint8)
for k,c in col.items(): img[cls==k]=c
yy2,xx2=np.mgrid[0:1000,0:1000]; dots=frostp&((yy2%4==0)&(xx2%4==0))
img[dots]=(30,80,220,255)
Image.fromarray(img,'RGBA').resize((2000,2000),Image.NEAREST).save('niche.png',optimize=True)
HP=np.array([[874.9,949.8],[879.9,944.6],[865.1,931.2],[860.6,941.4]])
hm=MP(HP/2).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(1000,1000)
hb=ndimage.binary_dilation(hm,iterations=10)
J=json.load(open('niche.json'))
J['hairpin']=dict(areaM2=int(hm.sum()*4),mix={str(k):int(((cls==k)&hm).sum()*4) for k in (1,2,3,4,5,6)},winter=round(float(W[hm].mean()),1),winterMax=round(float(W[hm].max()),1),buffer20={str(k):int(((cls==k)&hb).sum()*4) for k in (1,2,3,4,5,6)},cx=870,cy=941)
json.dump(J,open('niche.json','w'));print(J['hairpin'])

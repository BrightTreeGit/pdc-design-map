"""Trees tall enough to reach a building if they fell (2022 LiDAR), for the arborist.
Tree tops = local maxima of the canopy height model; reach = height - distance to the nearest roof edge."""
import json,math,numpy as np,glob,sys
from scipy import ndimage
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/canopy_bright-tree_2022.npz'
OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp/claude-0/al/arb'
z=np.load(D);g=z['ground'].astype(float);t=z['top'].astype(float)
bad=~np.isfinite(g);idx=ndimage.distance_transform_edt(bad,return_distances=False,return_indices=True);g=g[tuple(idx)]
chm=np.clip(np.nan_to_num(t-g,nan=0),0,90)
T=json.load(open('map/terrain.json'));E0,N0=T['E0'],T['N0']
home=np.array([906,947])
yy,xx=np.mgrid[0:2000,0:2000];near=np.hypot(xx-home[0],yy-home[1])<260
# buildings: LiDAR building class (roofs), plus drawn existing structures
bb=z['bldg']>0
if bb.shape[0]==1000: bb=bb.repeat(2,0).repeat(2,1)
B=bb&near
B=ndimage.binary_closing(B,iterations=1);lab,n=ndimage.label(B);sz=ndimage.sum(B,lab,range(1,n+1));B=np.isin(lab,1+np.where(sz>=12)[0])
F=[json.load(open(f)) for f in glob.glob('data-snapshots/2026-11-02_trial/features/*.json')]
from matplotlib.path import Path
named=[]
for x in F:
  d=x.get('data',x);gg=d.get('geom') or {}
  if d.get('kind') in('building','cabin','greenhouse') and gg.get('g')=='polygon' and d.get('stage') in('existing','now'):
    P=np.array(gg['pts'],float);m=Path(P).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(2000,2000);B|=m;named.append((d.get('name'),P.mean(0)))
lab,n=ndimage.label(B);cent=ndimage.center_of_mass(B,lab,range(1,n+1));area=ndimage.sum(B,lab,range(1,n+1))
def bname(k):
  c=np.array(cent[k-1])[::-1];best=None
  for nm,p in named:
    dd=np.hypot(*(p-c))
    if dd<15 and (best is None or dd<best[0]): best=(dd,nm)
  if best: return best[1]
  if np.hypot(*(c-home))<25: return 'House'
  return f'Roof {k} ({int(area[k-1])} m²)'
names={k:bname(k) for k in range(1,n+1)}
Tl=Path(np.array(T['lot'],float).reshape(-1,2))
keep=np.zeros(n+1,bool)
for k in range(1,n+1):
  c=np.array(cent[k-1])[::-1]
  if Tl.contains_point(c) and 'retreat' not in names[k].lower(): keep[k]=True
  if np.hypot(*(c-home))<25 or names[k]=='Greenhouse / zome 1': names[k]='House'
B=keep[lab]; lab=np.where(B,lab,0)
dist,ind=ndimage.distance_transform_edt(~B,return_indices=True)
# tree tops
mx=ndimage.maximum_filter(chm,size=7);tops=(chm==mx)&(chm>=10)&near&~B
ys,xs=np.where(tops)
print('buildings kept:',sorted({names[k] for k in range(1,n+1) if keep[k]}))
def toLL(E,N,ZONE=56):
  a=6378137;f=1/298.257222101;k0=.9996;FE=5e5;FN=1e7;n_=f/(2-f);A=a/(1+n_)*(1+n_*n_/4+n_**4/64);e=math.sqrt(f*(2-f))
  be=[n_/2-2*n_*n_/3+37*n_**3/96,n_*n_/48+n_**3/15,17*n_**3/480];xi=(N-FN)/(k0*A);eta=(E-FE)/(k0*A);xp,ep=xi,eta
  for j in range(3):
    k=2*(j+1);xp-=be[j]*math.sin(k*xi)*math.cosh(k*eta);ep-=be[j]*math.cos(k*xi)*math.sinh(k*eta)
  chi=math.asin(math.sin(xp)/math.cosh(ep));lat=chi
  for i in range(6):lat=math.asin(math.tanh(math.atanh(math.sin(chi))+e*math.atanh(e*math.sin(lat))))
  return math.degrees((ZONE*6-183)*math.pi/180+math.atan2(math.sinh(ep),math.cos(xp))),math.degrees(lat)
rows=[]
for y,x in zip(ys,xs):
  H=float(chm[y,x]);Dd=float(dist[y,x])
  if Dd>H or Dd>90: continue
  by,bx=ind[0][y,x],ind[1][y,x];k=lab[by,bx]
  dx,dy=bx-x,by-y;brg=(math.degrees(math.atan2(dx,-dy))+360)%360   # bearing from tree to building (y is south)
  dz=float(g[y,x]-g[by,bx])   # tree base above (+) or below (-) the building
  lo,la=toLL(E0+x,N0-y)
  rows.append({'x':int(x),'y':int(y),'h':round(H,1),'d':round(Dd,1),'reach':round(H-Dd,1),'bldg':names[k],'bearing_to_bldg':round(brg),'base_above_bldg_m':round(dz,1),'lat':round(la,6),'lon':round(lo,6)})
rows.sort(key=lambda r:(-r['reach'],-r['h']))
for i,r in enumerate(rows):
  r['id']=f'T{i+1:02d}'
  r['tier']=1 if (r['reach']>=15 and r['d']<=25) else 2 if r['reach']>=5 else 3
json.dump({'source':'Sunshine Coast 2022 LiDAR, canopy height model 1 m; tree tops = local maxima >=10 m','buildings':[names[k] for k in range(1,n+1)],'trees':rows},open(OUT+'/tree_risk_2022.json','w'),indent=1)
np.save(OUT+'/bldg_mask.npy',B)
print(len(rows),'tree tops could reach a building (height >= distance)')
print('buildings:',[names[k] for k in range(1,n+1)])
for r in rows[:25]: print(r['id'],r['h'],'m tall,',r['d'],'m away, reach',r['reach'],'->',r['bldg'],'| base',r['base_above_bldg_m'],'m above')

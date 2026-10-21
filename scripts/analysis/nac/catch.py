import json,sys,numpy as np,tifffile
sys.path.insert(0,'/tmp/claude-0/scripts'); from build_site import ll2mga
from scipy import ndimage
from matplotlib.path import Path as MP
D='/mnt/user-data/uploads/Permiculture Noosa PDC/NAC/Lidar-survey data/NSW site pack nac/'
cw=json.load(open(D+'catchment_window.json'));z=tifffile.imread(D+'dem_catchment_10m.tif').astype(float)
print(z.shape,np.nanmin(z),np.nanmax(z),(z<=-9000).mean())
z[z<=-9000]=np.nan;n=z.shape[0];res=cw['res']
c=json.load(open(D+'boundary.geojson'))['features'][0]['geometry']['coordinates'][0]
E,N=ll2mga([p[0] for p in c],[p[1] for p in c],56)
col=(np.array(E)-cw['E0'])/res;row=(cw['N0']-np.array(N))/res
rr,cc=np.mgrid[0:n,0:n];lot=MP(np.c_[col,row]).contains_points(np.c_[cc.ravel()+.5,rr.ravel()+.5],radius=1).reshape(n,n)
if lot.sum()==0: lot[int(row.mean()),int(col.mean())]=1
print('lot cells',lot.sum(),'elev', np.nanmean(z[lot]))
# priority-flood fill then D8 upstream of lot
import heapq
zf=np.where(np.isnan(z),-1e9,z).copy();done=np.zeros_like(lot);h=[]
for i in range(n):
  for j in (0,n-1):
    for (a,b) in ((i,j),(j,i)): heapq.heappush(h,(zf[a,b],a,b));done[a,b]=1
sea=np.isnan(z)
for a,b in zip(*np.nonzero(sea)): 
  if not done[a,b]: heapq.heappush(h,(-1e9,a,b));done[a,b]=1
while h:
  v,a,b=heapq.heappop(h)
  for da in(-1,0,1):
    for db in(-1,0,1):
      x,y=a+da,b+db
      if 0<=x<n and 0<=y<n and not done[x,y]:
        done[x,y]=1;zf[x,y]=max(zf[x,y],v+1e-4);heapq.heappush(h,(zf[x,y],x,y))
# D8 receivers
P=np.pad(zf,1,constant_values=-1e12);best=np.zeros((n,n));rec=np.full((n,n,2),-1)
for da in(-1,0,1):
  for db in(-1,0,1):
    if da==db==0:continue
    d=(zf-P[1+da:1+da+n,1+db:1+db+n])/np.hypot(da,db)
    m=d>best;best[m]=d[m];rec[m]=(da,db)
# upstream: iterate - cells whose receiver is in set
up=lot.copy()
for it in range(3000):
  R=rec;tgt_r=np.clip(rr+R[...,0],0,n-1);tgt_c=np.clip(cc+R[...,1],0,n-1)
  new=up|(up[tgt_r,tgt_c]&(best>0))
  if new.sum()==up.sum():break
  up=new
ha=up.sum()*res*res/1e4;edge=up[0].any()|up[-1].any()|up[:,0].any()|up[:,-1].any()
print('catchment ha',round(ha,2),'touches edge',edge,'iters',it)
from skimage import measure
cs=max(measure.find_contours(np.pad(up,1).astype(float),.5),key=len);cs=measure.approximate_polygon(cs,0.8)
X=cw['E0']+(cs[:,1]-.5)*res;Y=cw['N0']-(cs[:,0]-.5)*res
w=json.load(open(D+'window.json'));loc=[[round(x-w['E0'],1),round(w['N0']-y,1)] for x,y in zip(X,Y)]
xs=[p[0] for p in loc];ys=[p[1] for p in loc];print('local bbox',min(xs),max(xs),min(ys),max(ys))
json.dump({'ha':ha,'pts':loc,'edge':bool(edge)},open('catch.json','w'))

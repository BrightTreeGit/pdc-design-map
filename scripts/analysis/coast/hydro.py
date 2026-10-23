import numpy as np, heapq, math, time
from scipy import ndimage
t0=time.time()
Z=np.load('dem15.npy').astype(np.float64)
H,W=Z.shape;R=15.0
nod=Z<-1000
# ocean: low cells (<=0.5 m) connected to the east edge or nodata
low=(Z<=0.5)|nod
lab,n=ndimage.label(low)
sea_ids=set(np.unique(lab[:,-1]))|set(np.unique(lab[nod]))
sea_ids.discard(0)
sea=np.isin(lab,list(sea_ids))
Z[nod]=0
print('sea share',sea.mean(),time.time()-t0)
filled=Z.copy();closed=np.zeros((H,W),bool);pq=[]
# seeds: sea cells next to land, plus map edges
edge=np.zeros((H,W),bool);edge[0,:]=edge[-1,:]=edge[:,0]=edge[:,-1]=True
seed=(edge|sea)
closed[sea]=True
sb=seed&~(sea&~ndimage.binary_dilation(~sea))   # sea cells touching land, and edges
rs,cs=np.nonzero(sb)
pq=[(filled[r,c],r,c) for r,c in zip(rs,cs)];closed[rs,cs]=True
heapq.heapify(pq)
nb=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
fl=filled;cl=closed
while pq:
    z,r,c=heapq.heappop(pq)
    for dr,dc in nb:
        rr=r+dr;cc=c+dc
        if 0<=rr<H and 0<=cc<W and not cl[rr,cc]:
            cl[rr,cc]=True
            if fl[rr,cc]<=z: fl[rr,cc]=z+1e-4
            heapq.heappush(pq,(fl[rr,cc],rr,cc))
print('filled',time.time()-t0)
pad=np.pad(filled,1,constant_values=-1e9);best=np.zeros_like(filled);rec=np.arange(H*W).reshape(H,W)
for dr,dc in nb:
    d=math.hypot(dr,dc)*R;nz=pad[1+dr:1+dr+H,1+dc:1+dc+W];drop=(filled-nz)/d
    rr=np.clip(np.arange(H)[:,None]+dr,0,H-1);cc=np.clip(np.arange(W)[None,:]+dc,0,W-1)
    better=drop>best;best=np.where(better,drop,best);rec=np.where(better,rr*W+cc,rec)
rec=rec.ravel();rec[sea.ravel()]=np.nonzero(sea.ravel())[0]   # sea cells are sinks
order=np.argsort(-filled.ravel(),kind='stable')
acc=np.full(H*W,R*R)
rf=rec
for i in order:
    j=rf[i]
    if j!=i: acc[j]+=acc[i]
np.save('filled.npy',filled.astype(np.float32));np.save('rec.npy',rec);np.save('acc.npy',acc.astype(np.float32));np.save('sea.npy',sea);np.save('order.npy',order)
print('done',time.time()-t0)

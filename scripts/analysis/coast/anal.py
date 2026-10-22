import numpy as np, json, math
from proj import ll2mga
from matplotlib.path import Path as MP
filled=np.load('filled.npy');rec=np.load('rec.npy');acc=np.load('acc.npy');sea=np.load('sea.npy');order=np.load('order.npy')
H,W=filled.shape;R=15;E0=480000;N1=7066000
def g2m(c,r):return E0+(c+.5)*R,N1-(r+.5)*R
def m2g(E,N):return (E-E0)/R-.5,(N1-N)/R-.5
t=json.load(open('/home/claude/pdc-design-map/map/terrain.json'))
loc2g=lambda x,y:m2g(492000+x,7043000-y)
lot=np.array([loc2g(x,y) for x,y in zip(t['lot'][0::2],t['lot'][1::2])])
btc=t['catch'][0]['p'];btc=np.array([loc2g(x,y) for x,y in zip(btc[0::2],btc[1::2])])
yy,xx=np.mgrid[0:H,0:W]
inlot=MP(lot).contains_points(np.c_[xx.ravel(),yy.ravel()])
seaf=sea.ravel()
# terminal outlet for every cell
term=np.full(H*W,-1,np.int64)
for c in order[::-1]:   # low to high: downstream first
    r=rec[c]
    term[c]=c if r==c else term[r]
# the outlet cell (last land cell) of each path: recompute: for sea-terminal paths, term is a sea cell
cells=np.nonzero(~seaf)[0]
T=term[cells];u,cnt=np.unique(T,return_counts=True)
area_km2=dict(zip(u,cnt*R*R/1e6))
majors=[k for k,a in sorted(area_km2.items(),key=lambda t:-t[1]) if a>=4]
print('majors',len(majors),[round(area_km2[k],1) for k in majors[:15]])
# Bright Tree path
start=np.nonzero(inlot)[0];s=start[np.argmax(acc[start])]
path=[s];c=s
while rec[c]!=c: c=rec[c];path.append(c)
pr=[divmod(p,W) for p in path]
dist=[0.0]
for (r0,c0),(r1,c1) in zip(pr,pr[1:]): dist.append(dist[-1]+math.hypot(r1-r0,c1-c0)*R)
z=[float(filled.ravel()[p]) for p in path]
endE,endN=g2m(pr[-1][1],pr[-1][0])
print('BT path km',round(dist[-1]/1000,1),'end',endE,endN,'acc at end km2',acc[path[-2]]/1e6,'terminal major idx',majors.index(term[s]) if term[s] in majors else None)
mouths={'Mooloolah River (Mooloolaba)':(153.1325,-26.6855),'Maroochy River (Maroochydore)':(153.0950,-26.6435),'Currimundi Lake':(153.1380,-26.7650),'Pumicestone Passage (Caloundra)':(153.1500,-26.8020),'Mooloolah River (upper)':(152.99,-26.72)}
for k,(lo,la) in mouths.items():
    E,N=ll2mga(lo,la);print(k,round(E),round(N),'dist from BT end km',round(math.hypot(E-endE,N-endN)/1000,1))
np.save('term.npy',term)
json.dump({'path':[[int(c),int(r)] for r,c in pr],'dist':[round(d) for d in dist],'z':[round(v,1) for v in z],'majors':[int(k) for k in majors],'area':{str(int(k)):round(area_km2[k],2) for k in majors}},open('anal.json','w'))

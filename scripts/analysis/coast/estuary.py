import numpy as np, json, math
from collections import deque
from proj import ll2mga
sea=np.load('sea.npy');H,W=sea.shape;R=15;E0=480000;N1=7066000
A=json.load(open('anal.json'));c0,r0=A['path'][-1]
# open ocean = sea cells in the east-most 3 columns
prev=-np.ones(H*W,np.int64);seen=np.zeros(H*W,bool);q=deque([r0*W+c0]);seen[r0*W+c0]=True;goal=None
while q:
    k=q.popleft();r,c=divmod(k,W)
    if c>=W-3: goal=k;break
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            rr,cc=r+dr,c+dc
            if 0<=rr<H and 0<=cc<W:
                kk=rr*W+cc
                if sea[rr,cc] and not seen[kk]: seen[kk]=True;prev[kk]=k;q.append(kk)
p=[];k=goal
while k!=-1: p.append(k);k=prev[k]
p=p[::-1]
# keep only until it reaches the open coast: first cell east of which all is sea along the row for 40 cells
cut=len(p)
for i,k in enumerate(p):
    r,c=divmod(k,W)
    if sea[r,c:min(W,c+60)].all() and c>W*0.7: cut=i;break
p=p[:cut+1];pr=[divmod(k,W) for k in p]
d=[A['dist'][-1]]
for (a,b),(e,f) in zip(pr,pr[1:]): d.append(d[-1]+math.hypot(e-a,f-b)*R)
cE,cN=E0+(pr[-1][1]+.5)*R,N1-(pr[-1][0]+.5)*R
print('estuary km',round((d[-1]-d[0])/1000,1),'coast at',round(cE),round(cN))
mouths={'Mooloolah River mouth, Mooloolaba':(153.1325,-26.6855),'Maroochy River mouth, Maroochydore':(153.0950,-26.6435),'Currimundi Lake':(153.1380,-26.7650),'Pumicestone Passage, Caloundra':(153.1500,-26.8020)}
best=min(mouths,key=lambda k:math.hypot(ll2mga(*mouths[k])[0]-cE,ll2mga(*mouths[k])[1]-cN))
print('nearest mouth',best,round(math.hypot(ll2mga(*mouths[best])[0]-cE,ll2mga(*mouths[best])[1]-cN)))
A['estuary']=[[int(c),int(r)] for r,c in pr];A['edist']=[round(x) for x in d];A['mouth']=best;A['coast']=[round(cE),round(cN)]
json.dump(A,open('anal.json','w'))

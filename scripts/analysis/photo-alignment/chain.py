import cv2, numpy as np, pickle, json
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
names,R=pickle.load(open('pairs.pkl','rb'))
def M3(A): return np.vstack([A,[0,0,1]])
# edges: transform from a-coords to b-coords (half-res)
E={}
for (a,b),(n,A,s) in R.items():
    if n<15 or not (0.5<s<2): continue
    E.setdefault(a,[]).append((b,M3(A),n)); E.setdefault(b,[]).append((a,np.linalg.inv(M3(A)),n))
# best-path (max min inliers) from ref_1994: T[n] maps n-coords -> ref coords
T={'ref_1994':np.eye(3)};Q=['ref_1994'];W={'ref_1994':9999}
import heapq
h=[(-9999,'ref_1994')];done=set()
while h:
    w,n=heapq.heappop(h);w=-w
    if n in done: continue
    done.add(n)
    for m,Mnm,k in E.get(n,[]):
        # Mnm maps n->m ; T[m] = T[n] @ inv(Mnm)
        if m in done: continue
        cand=min(w,k)
        if cand>W.get(m,0):
            W[m]=cand;T[m]=T[n]@np.linalg.inv(Mnm);heapq.heappush(h,(-cand,m))
for n in names: print(n, W.get(n,'-'))
pickle.dump(T,open('T.pkl','wb'))

import cv2,numpy as np,json,sys
G=np.float32([[1670,215],[2235,200],[2140,435],[1900,705],[2262,1000]])
Cc=np.float32([[905,450],[1160,452],[1127,557],[1000,679],[1192,779]])
use=[0,1,2]
M,_=cv2.estimateAffinePartial2D(G[use],Cc[use],method=cv2.LMEDS)
print(M,'scale',np.hypot(M[0,0],M[1,0]),'rot',np.degrees(np.arctan2(M[1,0],M[0,0])))
pr=(M[:,:2]@G.T).T+M[:,2];print('resid px',np.hypot(*(pr-Cc).T).round(1))
g=cv2.imread('google.png')[:1095];c=cv2.imread('nac_closeup_2021.jpg')
w=cv2.warpAffine(g,M,(c.shape[1],c.shape[0]),flags=cv2.INTER_AREA)
mask=cv2.warpAffine(np.full(g.shape[:2],255,np.uint8),M,(c.shape[1],c.shape[0]))
# checkerboard blend
cb=((np.indices(c.shape[:2])//60).sum(0)%2==0)&(mask>0)
out=c.copy();out[cb]=w[cb]
cv2.imwrite('gchk.jpg',out[300:1100,300:1300])
np.save('gM.npy',M)

import cv2, numpy as np, pickle, sys
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
R=pickle.load(open('Tecc.pkl','rb'))
def run(mov,tgt,crop=None):
    sift=cv2.SIFT_create(40000);cl=cv2.createCLAHE(2,(16,16))
    A=cv2.imread(D+mov+'.jpg',0);
    B=cv2.warpPerspective(cv2.imread(D+tgt+'.jpg',0),R[tgt][0],(4000,4000)) if tgt in R else cv2.imread(D+tgt+'.jpg',0)
    mb=np.zeros_like(B);mb[1000:3000,1000:3000]=255;mb&=((B>8)*255).astype(np.uint8)
    ka,da=sift.detectAndCompute(cl.apply(A),((A>8)*255).astype(np.uint8));kb,db=sift.detectAndCompute(cl.apply(B),mb)
    m=cv2.FlannBasedMatcher(dict(algorithm=1,trees=5),dict(checks=100)).knnMatch(da,db,k=2)
    g=[x for x,y in m if x.distance<0.75*y.distance]
    pa=np.float32([ka[x.queryIdx].pt for x in g]);pb=np.float32([kb[x.trainIdx].pt for x in g])
    H,mk=cv2.findHomography(pa,pb,cv2.RANSAC,5.0,maxIters=50000)
    n=int(mk.sum()) if mk is not None else 0
    print(mov,'->',tgt,'matches',len(g),'inliers',n)
    return H,n
mov,tgt=sys.argv[1],sys.argv[2]
H,n=run(mov,tgt)
if n>=25:
    R[mov]=(H,n/100);pickle.dump(R,open('Tecc.pkl','wb'));print('saved')

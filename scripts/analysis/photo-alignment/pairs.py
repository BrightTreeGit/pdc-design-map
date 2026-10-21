import cv2, numpy as np, glob, pickle
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
names=['ref_2008','ref_1994']+sorted(f.split('/')[-1][:-4] for f in glob.glob(D+'wide_*.jpg'))
sift=cv2.SIFT_create(15000)
F={}
for n in names:
    im=cv2.imread(D+n+'.jpg',0); im=cv2.resize(im,None,fx=0.5,fy=0.5,interpolation=cv2.INTER_AREA)
    mask=(cv2.erode((im>8).astype(np.uint8),np.ones((25,25)))*255)
    im=cv2.createCLAHE(2.5,(16,16)).apply(im)
    k,d=sift.detectAndCompute(im,mask); F[n]=(np.float32([p.pt for p in k]),d)
fl=cv2.FlannBasedMatcher(dict(algorithm=1,trees=5),dict(checks=64))
R={}
for i,a in enumerate(names):
    for b in names[i+1:]:
        pa,da=F[a];pb,db=F[b]
        m=fl.knnMatch(da,db,k=2); g=[x for x,y in m if x.distance<0.8*y.distance]
        if len(g)<10: continue
        A,mk=cv2.estimateAffinePartial2D(pa[[x.queryIdx for x in g]],pb[[x.trainIdx for x in g]],method=cv2.RANSAC,ransacReprojThreshold=8,maxIters=20000)
        if A is None: continue
        s=np.hypot(A[0,0],A[1,0]); R[(a,b)]=(int(mk.sum()),A,s)
pickle.dump((names,R),open('pairs.pkl','wb'))
for (a,b),(n,A,s) in sorted(R.items(),key=lambda z:-z[1][0])[:45]:
    print(f'{a[:9]:10s}{b[:9]:10s} inl {n:4d} scale {s:.2f} shift {A[0,2]:7.0f} {A[1,2]:7.0f}')

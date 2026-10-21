import cv2, numpy as np, glob, json, sys
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
def load(f, s=0.5):
    im=cv2.imread(D+f,0); im=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
    return cv2.createCLAHE(3,(8,8)).apply(im)
sift=cv2.SIFT_create(8000)
def match(a,b):
    ka,da=sift.detectAndCompute(a,None); kb,db=sift.detectAndCompute(b,None)
    m=cv2.BFMatcher().knnMatch(da,db,k=2); g=[x for x,y in m if x.distance<0.8*y.distance]
    if len(g)<8: return None,0,len(g)
    pa=np.float32([ka[x.queryIdx].pt for x in g]); pb=np.float32([kb[x.trainIdx].pt for x in g])
    H,mask=cv2.findHomography(pa,pb,cv2.RANSAC,6.0)
    return H,int(mask.sum()) if mask is not None else 0,len(g)
ref=load('ref_1994.jpg')
for f in sorted(glob.glob(D+'wide_*.jpg')):
    f=f.split('/')[-1]; a=load(f)
    H,inl,ng=match(a,ref)
    if H is None: print(f,'none',ng);continue
    c=H@np.array([1000,1000,1.]);c=c[:2]/c[2]
    print(f,'inliers',inl,'of',ng,'centre->',np.round(c-1000,1),'scale',round(np.sqrt(abs(np.linalg.det(H[:2,:2]))),3))

import cv2, numpy as np, pickle, sys
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
T=pickle.load(open('T.pkl','rb'))
S=np.diag([2,2,1.]); Si=np.linalg.inv(S)  # half->full
refc=cv2.imread(D+'ref_1994.jpg'); ref=cv2.cvtColor(refc,cv2.COLOR_BGR2GRAY)
cl=cv2.createCLAHE(2.5,(8,8))
sift=cv2.SIFT_create(20000)
U0,U1=1100,2900  # 2.25 km region around block, full res
def feats(im):
    sub=im[U0:U1,U0:U1]; m=(cv2.erode((sub>8).astype(np.uint8),np.ones((15,15)))*255)
    k,d=sift.detectAndCompute(cl.apply(sub),m); return np.float32([p.pt for p in k])+U0,d
rk,rd=feats(ref)
out={}
for n,Th in T.items():
    if n.startswith('ref'): continue
    Tf=S@Th@Si  # full-res old -> full-res ref
    im=cv2.imread(D+n+'.jpg'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    w=cv2.warpPerspective(g,Tf,(4000,4000))
    k,d=feats(w)
    m=cv2.FlannBasedMatcher(dict(algorithm=1,trees=5),dict(checks=64)).knnMatch(d,rd,k=2)
    gm=[x for x,y in m if x.distance<0.8*y.distance]
    pa=k[[x.queryIdx for x in gm]];pb=rk[[x.trainIdx for x in gm]]
    near=np.linalg.norm(pa-pb,axis=1)<120
    pa,pb=pa[near],pb[near]
    Hc=np.eye(3);inl=0
    if len(pa)>=12:
        H,mk=cv2.findHomography(pa,pb,cv2.RANSAC,4.0,maxIters=20000)
        if H is not None and mk.sum()>=12: Hc=H;inl=int(mk.sum())
    c=Hc@np.array([2000,2000,1.]);sh=c[:2]/c[2]-2000
    print(n,'local matches',len(pa),'inliers',inl,'correction m',np.round(sh*1.25,1))
    out[n]=(Hc@Tf,inl)
pickle.dump(out,open('Tfull.pkl','wb'))

import cv2, numpy as np, pickle
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
O=pickle.load(open('Tfull.pkl','rb'))
A0,A1=1300,2700   # 1.75 km region, full-res ref coords
def grad(g):
    g=cv2.GaussianBlur(g.astype(np.float32),(0,0),2.5)
    gx=cv2.Sobel(g,cv2.CV_32F,1,0);gy=cv2.Sobel(g,cv2.CV_32F,0,1);m=cv2.magnitude(gx,gy)
    return cv2.normalize(m,None,0,1,cv2.NORM_MINMAX)
def smooth(g): 
    g=cv2.GaussianBlur(g.astype(np.float32),(0,0),4); return (g-g.mean())/(g.std()+1e-6)
ref=cv2.imread(D+'ref_1994.jpg',0)
def ecc(mov_full, tgt_full, Tf, sc=0.5):
    # warp mov into ref frame, then ECC on region at reduced scale
    w=cv2.warpPerspective(mov_full,Tf,(4000,4000))
    a=w[A0:A1,A0:A1];b=tgt_full[A0:A1,A0:A1]
    a=cv2.resize(a,None,fx=sc,fy=sc,interpolation=cv2.INTER_AREA);b=cv2.resize(b,None,fx=sc,fy=sc,interpolation=cv2.INTER_AREA)
    mask=(a>5).astype(np.uint8)
    best=None
    for f in (smooth,grad):
        W=np.eye(3,dtype=np.float32)
        try:
            cc,W=cv2.findTransformECC(f(b),f(a),W,cv2.MOTION_HOMOGRAPHY,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-6),mask,5)
        except cv2.error as e:
            continue
        if best is None or cc>best[0]: best=(cc,W,f.__name__)
    if best is None: return Tf,0,'fail'
    cc,W,fn=best
    # W maps tgt-region coords -> mov-region coords (scaled); build full correction
    P=np.array([[1/sc,0,A0],[0,1/sc,A0],[0,0,1]])  # region-scaled -> full
    Winv=np.linalg.inv(W.astype(np.float64))
    C=P@Winv@np.linalg.inv(P)   # mov(full ref frame)->ref
    return C@Tf,cc,fn
res={}
order=[('wide_1997_369968','ref'),('wide_1991_464150','ref'),('wide_1988_576368','ref'),('wide_1995_719593','ref'),('wide_2003_890582','ref'),('wide_1981_496095','wide_1988_576368'),('wide_1979_421488','wide_1981_496095'),('wide_1992_133369','ref')]
aligned={'ref':ref}
for n,t in order:
    g=cv2.imread(D+n+'.jpg',0)
    Tf,cc,fn=ecc(g,aligned[t],O[n][0])
    c=Tf@np.array([2000,2000,1.]);c0=O[n][0]@np.array([2000,2000,1.])
    d=(c[:2]/c[2]-c0[:2]/c0[2])
    print(n,'vs',t[:9],'cc %.3f'%cc,fn,'moved %.0f m'%(np.linalg.norm(d)*1.25))
    res[n]=(Tf,cc); aligned[n]=cv2.warpPerspective(g,Tf,(4000,4000))
pickle.dump(res,open('Tecc.pkl','wb'))

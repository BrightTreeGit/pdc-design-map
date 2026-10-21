import cv2, numpy as np, pickle, sys
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
R=pickle.load(open('Tecc.pkl','rb'))
SC=0.4  # 3.125 m/px
def prep(g,s=1.5):
    g=g.astype(np.float32); g=cv2.GaussianBlur(g,(0,0),s); 
    hp=g-cv2.GaussianBlur(g,(0,0),25)   # remove brightness trends (pasture vs forest tones change)
    return hp
def aligned(n): 
    g=cv2.imread(D+n+'.jpg',0); return cv2.warpPerspective(g,R[n][0],(4000,4000)) if n in R else g
def find(mov,tgt,half=700):
    T=aligned(tgt); T=cv2.resize(T,None,fx=SC,fy=SC,interpolation=cv2.INTER_AREA)
    c=int(2000*SC);h=int(half*SC); tpl=prep(T[c-h:c+h,c-h:c+h])
    M=cv2.imread(D+mov+'.jpg',0); M=cv2.resize(M,None,fx=SC,fy=SC,interpolation=cv2.INTER_AREA)
    best=(-1,)
    for s in (0.85,0.9,0.95,1.0,1.05,1.1,1.15,1.2):
        for a in np.arange(-8,8.1,1.0):
            Rm=cv2.getRotationMatrix2D((c,c),a,s)
            Mw=cv2.warpAffine(M,Rm,(M.shape[1],M.shape[0]))
            res=cv2.matchTemplate(prep(Mw),tpl,cv2.TM_CCOEFF_NORMED)
            _,mx,_,loc=cv2.minMaxLoc(res)
            if mx>best[0]: best=(mx,s,a,loc)
    mx,s,a,(lx,ly)=best
    # mov(scaled) -> rotated/scaled -> template coords; template top-left in T scaled coords is (c-h,c-h)
    Rm=np.vstack([cv2.getRotationMatrix2D((c,c),a,s),[0,0,1]])
    Tr=np.array([[1,0,(c-h)-lx],[0,1,(c-h)-ly],[0,0,1.]])
    S=np.diag([SC,SC,1]);Si=np.linalg.inv(S)
    Hf=Si@Tr@Rm@S   # full-res mov -> full-res target(ref frame)
    return Hf,mx,s,a
mov,tgt=sys.argv[1],sys.argv[2]
Hf,mx,s,a=find(mov,tgt)
print(mov,'->',tgt,'ncc %.3f scale %.2f rot %.0f'%(mx,s,a))
if len(sys.argv)>3: R[mov]=(Hf,mx);pickle.dump(R,open('Tecc.pkl','wb'));print('saved')

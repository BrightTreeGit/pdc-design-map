exec(open('tmatch.py').read().split('def find')[0])
exec('def find'+open('tmatch.py').read().split('def find')[1].split('mov,tgt=sys.argv')[0])
exec(open('ecc.py').read().split('res={}')[0])
import sys
def find_fine(mov,tgt,s0,a0):
    T=aligned(tgt); Ts=cv2.resize(T,None,fx=SC,fy=SC,interpolation=cv2.INTER_AREA)
    c=int(2000*SC);h=int(700*SC); tpl=prep(Ts[c-h:c+h,c-h:c+h])
    M=cv2.imread(D+mov+'.jpg',0); M=cv2.resize(M,None,fx=SC,fy=SC,interpolation=cv2.INTER_AREA)
    best=(-1,)
    for s in np.arange(s0-0.06,s0+0.061,0.02):
        for a in np.arange(a0-2.5,a0+2.51,0.5):
            Rm=cv2.getRotationMatrix2D((c,c),a,s); Mw=cv2.warpAffine(M,Rm,(M.shape[1],M.shape[0]))
            res=cv2.matchTemplate(prep(Mw),tpl,cv2.TM_CCOEFF_NORMED); _,mx,_,loc=cv2.minMaxLoc(res)
            if mx>best[0]: best=(mx,s,a,loc)
    mx,s,a,(lx,ly)=best
    Rm=np.vstack([cv2.getRotationMatrix2D((c,c),a,s),[0,0,1]]);Tr=np.array([[1,0,(c-h)-lx],[0,1,(c-h)-ly],[0,0,1.]])
    S=np.diag([SC,SC,1]);return np.linalg.inv(S)@Tr@Rm@S,mx,s,a,T
mov,tgt,s0,a0=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
Hf,mx,s,a,T=find_fine(mov,tgt,s0,a0)
g=cv2.imread(D+mov+'.jpg',0)
H2,cc,fn=ecc(g,T,Hf)
c1=Hf@np.array([2000,2000,1.]);c2=H2@np.array([2000,2000,1.])
print(mov,'ncc %.3f s %.2f a %.1f'%(mx,s,a),'ecc %.3f'%cc,fn,'ecc moved %.0f m'%(np.linalg.norm(c1[:2]/c1[2]-c2[:2]/c2[2])*1.25))
use=H2 if cc>0.3 and np.linalg.norm(c1[:2]/c1[2]-c2[:2]/c2[2])*1.25<60 else Hf
R[mov]=(use,mx);pickle.dump(R,open('Tecc.pkl','wb'))

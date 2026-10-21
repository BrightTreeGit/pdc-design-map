import numpy as np,json,warnings;warnings.filterwarnings('ignore')
from scipy import ndimage
from PIL import Image
from matplotlib.path import Path as MP
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/'
z=np.load(D+'canopy_bright-tree_2022.npz');dem=np.load('/tmp/claude-0/work/dem2022.npy').astype(np.float32)
chm=np.clip(np.nan_to_num(z['top'].astype(np.float32)-dem,nan=0),0,85)
chm2=chm.reshape(1000,2,1000,2).max(axis=(1,3))
fr=z['first'].astype(np.float32);hi=z['first_hi'].astype(np.float32);k=np.ones((3,3))
gap=np.where(ndimage.convolve(fr,k)>=6,1-ndimage.convolve(hi,k)/np.maximum(ndimage.convolve(fr,k),1),np.nan);gap=np.nan_to_num(gap,nan=float(np.nanmedian(gap)))
gap[chm2<2]=1.0
img=np.zeros((1000,1000,4),np.uint8);img[...,0]=np.clip(chm2*3,0,255).astype(np.uint8);img[...,1]=np.clip(gap*255,0,255).astype(np.uint8);img[...,3]=255
Image.fromarray(img,'RGBA').save('out/canopy_grid.png',optimize=True)
# ---------- productivity: canopy growth 2008->2022 vs what is typical for the starting height
z8=np.load(D+'canopy_bright-tree_2008.npz')
def blk(h,b=4):
    a=h.reshape(2000//b,b,2000//b,b).transpose(0,2,1,3).reshape(2000//b,2000//b,b*b);return np.nanpercentile(a,95,axis=2)
def chmf(zz,s):
    top=zz['top'].astype(np.float32);h=np.clip(top-dem,0,85);f=np.where(np.isfinite(h),h,-1);f=ndimage.grey_dilation(f,size=(s,s));f[f<0]=np.nan;return np.where(np.isfinite(h),h,f)
B22=blk(chmf(z,3));B08=blk(chmf(z8,5))
g=B22-B08;ok=np.isfinite(g)&np.isfinite(B08)&(B08>=3)&(B08<=45)
bins=np.arange(3,46,3);idx=np.digitize(B08,bins);med=np.full(g.shape,np.nan)
for i in range(1,len(bins)):
    m=ok&(idx==i)
    if m.sum()>50:med[m]=np.median(g[m])
res=np.where(ok,g-med,np.nan)
r=ndimage.generic_filter(np.nan_to_num(res,nan=0),np.mean,size=3);cnt=ndimage.generic_filter(np.isfinite(res).astype(float),np.mean,size=3)
r=np.where(cnt>0.4,r/np.maximum(cnt,1e-3),np.nan)
t=np.clip(r/6,-1,1)
out=np.zeros(r.shape+(4,),np.uint8)
pos=t>0.15;neg=t<-0.15
out[pos]=np.stack([60-40*t[pos],150+60*t[pos],80+0*t[pos],90+150*t[pos]],-1).astype(np.uint8)
out[neg]=np.stack([200+40*(-t[neg]),170-90*(-t[neg]),60+0*t[neg],90+150*(-t[neg])],-1).astype(np.uint8)
Image.fromarray(out,'RGBA').resize((2000,2000),Image.NEAREST).save('out/productivity.png',optimize=True)
tj=json.load(open('/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/brighttree-map/terrain.json'))
L=np.array(tj['lot']).reshape(-1,2)/4;yy,xx=np.mgrid[0:500,0:500];lot=MP(L).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(500,500)
p={'aboveHa':round(float(np.nansum((r>1.5)&lot)*16/1e4),2),'belowHa':round(float(np.nansum((r<-1.5)&lot)*16/1e4),2),'medianGrowth':{f'{bins[i-1]}-{bins[i]}':round(float(np.nanmedian(g[ok&(idx==i)])),1) for i in range(1,len(bins)) if (ok&(idx==i)).sum()>50}}
print(p);json.dump(p,open('out/productivity.json','w'))

import numpy as np,json
from scipy import ndimage
from PIL import Image,ImageDraw
from matplotlib.path import Path as MP
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/'
O='/tmp/claude-0/work/canopy/out/'
Z={y:np.load(D+f'canopy_bright-tree_{y}.npz') for y in (2008,2014,2022)}
dem=np.load('/tmp/claude-0/work/dem2022.npy').astype(np.float32)   # 1 m bare earth, map grid
dem[~np.isfinite(dem)]=np.nan
t=json.load(open('/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/brighttree-map/terrain.json'))
L=np.array(t['lot']).reshape(-1,2)
yy,xx=np.mgrid[0:2000,0:2000];lot=MP(L).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(2000,2000)
lot2=lot[::2,::2]
def chm(y):
    top=Z[y]['top'].astype(np.float32);h=top-dem
    h[~np.isfinite(h)]=np.nan;h=np.clip(h,0,70)
    # fill pits/holes with 3x3 max (first returns are sparse in old surveys)
    f=np.where(np.isfinite(h),h,-1);f=ndimage.grey_dilation(f,size=(3,3) if y==2022 else (5,5));f[f<0]=np.nan
    return np.where(np.isfinite(h),np.maximum(h,ndimage.median_filter(np.nan_to_num(h),3)),f)
H={y:chm(y) for y in Z}
# 4 m block 95th percentile for change (reduces sampling noise between surveys)
def blk(h,b=4):
    a=h.reshape(2000//b,b,2000//b,b).transpose(0,2,1,3).reshape(2000//b,2000//b,b*b);return np.nanpercentile(a,95,axis=2)
import warnings;warnings.filterwarnings('ignore')
B={y:blk(H[y]) for y in H}
lot4=lot[::4,::4]
st={}
for y in H:
    h=H[y][lot];st[y]={'meanH':float(np.nanmean(h)),'cover2':float(np.nanmean(h>2)),'cover10':float(np.nanmean(h>10)),'p95':float(np.nanpercentile(h,95))}
print(json.dumps(st,indent=0))
# ---------- 1. canopy height 2022 image (2000x2000 RGBA)
h=H[2022];stops=[(0,(240,235,200,0)),(2,(220,215,150,110)),(5,(180,200,90,170)),(10,(110,170,60,190)),(20,(40,130,60,205)),(30,(20,90,60,215)),(40,(60,40,110,225))]
def ramp(v,stops):
    out=np.zeros(v.shape+(4,),np.float32);v=np.nan_to_num(v,nan=-1)
    for (a,ca),(b,cb) in zip(stops,stops[1:]):
        m=(v>=a)&(v<b);f=((v-a)/(b-a))[m][:,None];out[m]=np.array(ca)*(1-f)+np.array(cb)*f
    out[v>=stops[-1][0]]=stops[-1][1];return out.astype(np.uint8)
img=ramp(h,stops)
# emergent / habitat-candidate trees: local maxima >=30 m in smoothed CHM, 9 m window
hs=ndimage.gaussian_filter(np.nan_to_num(h),1.2)
mx=(hs==ndimage.maximum_filter(hs,size=9))&(hs>=30)
lab,n=ndimage.label(mx);cents=ndimage.center_of_mass(mx,lab,range(1,n+1))
trees=[(round(c[1],1),round(c[0],1),round(float(hs[int(c[0]),int(c[1])]),1)) for c in cents]
trees.sort(key=lambda x:-x[2])
lot_trees=[tr for tr in trees if lot[int(tr[1]),int(tr[0])]]
print('tall trees >=30m window',len(trees),'in lot',len(lot_trees),'>=40 in lot',sum(1 for t in lot_trees if t[2]>=40),'tallest',lot_trees[:5])
im=Image.fromarray(img,'RGBA');d=ImageDraw.Draw(im)
for x,y,hh in trees:
    continue
    r=4;d.ellipse((x-r-1,y-r-1,x+r+1,y+r+1),fill=(255,255,255,235));d.ellipse((x-r,y-r,x+r,y+r),fill=(150,40,140,255) if hh>=40 else (40,40,40,255))
im.save(O+'canopy_h.png',optimize=True)
# ---------- 2. canopy change 2008 -> 2022 (4 m blocks, upsampled)
dch=B[2022]-B[2008]
both=np.isfinite(B[2022])&np.isfinite(B[2008])
c=np.zeros(dch.shape+(4,),np.uint8)
gain=both&(dch>3);loss=both&(dch<-5)
g=np.clip((dch-3)/12,0,1);l=np.clip((-dch-5)/15,0,1)
c[gain]=np.stack([40+0*g[gain],150-60*g[gain],60+0*g[gain],110+120*g[gain]],-1).astype(np.uint8)
c[loss]=np.stack([220-40*l[loss],70+0*l[loss],40+0*l[loss],120+120*l[loss]],-1).astype(np.uint8)
Image.fromarray(c,'RGBA').resize((2000,2000),Image.NEAREST).save(O+'canopy_change.png',optimize=True)
cell=16 # m2 per 4 m block
chg={'gainHa':round(float((gain&lot4).sum()*cell/1e4),2),'lossHa':round(float((loss&lot4).sum()*cell/1e4),2),'meanGrowthM':round(float(np.nanmean(dch[lot4&both])),1)}
print('change',chg)
# ---------- 3. understorey density 2022 (2 m grid): share of returns 0.5-5 m among returns below 5 m
b=Z[2022]['bands'].astype(np.float32);low=b[0]+b[1]+b[2];us=b[1]+b[2]
k=np.ones((3,3));usS=ndimage.convolve(us,k);lowS=ndimage.convolve(low,k)
dens=np.where(lowS>=6,usS/np.maximum(lowS,1),np.nan)
q=np.nanpercentile(dens,[70,85,95]);print('dens q',q)
dcls=np.digitize(np.nan_to_num(dens,nan=-1),q);ucol=np.array([(0,0,0,0),(240,200,60,120),(230,130,30,180),(170,40,30,220)],np.uint8);uimg=ucol[dcls];Image.fromarray(uimg,'RGBA').resize((2000,2000),Image.NEAREST).save(O+'understorey.png',optimize=True)
dl=dens[lot2];uss={'denseHa':round(float(np.nansum(dl>q[1])*4/1e4),2),'veryDenseHa':round(float(np.nansum(dl>q[2])*4/1e4),2)}
print('understorey',uss)
# ---------- 4. indicative fuel structure: near-surface/elevated density + ladder fuels + canopy cover
mid=b[2]+b[3];hi=b[4]+b[5]+b[6];tot=b.sum(0)
ladder=np.where(tot>=10,ndimage.convolve(mid,k)/np.maximum(ndimage.convolve(tot,k),1),np.nan)
cov=Z[2022]['first_hi'].astype(np.float32);fr=Z[2022]['first'].astype(np.float32);cover=np.where(ndimage.convolve(fr,k)>=6,ndimage.convolve(cov,k)/np.maximum(ndimage.convolve(fr,k),1),np.nan)
score=np.nan_to_num(np.clip((dens-0.2)/0.5,0,1))*0.5+np.nan_to_num(np.clip((ladder-0.05)/0.25,0,1))*0.3+np.nan_to_num(cover)*0.2
fq=np.percentile(score[np.isfinite(dens)|np.isfinite(ladder)],[60,85,95]);cls=np.digitize(score,fq)  # 0 low,1 moderate,2 high,3 very high
fcol=np.array([(0,0,0,0),(250,200,80,130),(235,120,40,180),(170,30,30,215)],np.uint8)
fimg=fcol[cls];fimg[~np.isfinite(dens)&~np.isfinite(ladder)]=0
Image.fromarray(fimg,'RGBA').resize((2000,2000),Image.NEAREST).save(O+'fuel.png',optimize=True)
fl=cls[lot2];fuel={k:round(float((fl==i).sum()*4/1e4),2) for i,k in enumerate(['lowHa','modHa','highHa','vhighHa'])}
print('fuel',fuel)
# ---------- 5. gaps (sunny openings) 2022: CHM<2 m patches >=100 m2 inside the lot
gapm=(np.nan_to_num(H[2022])<2)&lot;gl,gn=ndimage.label(gapm);sz=ndimage.sum(gapm,gl,range(1,gn+1))
gaps=[(i+1,int(s)) for i,s in enumerate(sz) if s>=100];gapsHa=round(sum(s for _,s in gaps)/1e4,2)
print('gaps',len(gaps),gapsHa)
json.dump({'years':st,'trees':[list(t) for t in lot_trees],'treesWindow':len(trees),'change':chg,'understorey':uss,'fuel':fuel,'gaps':{'n':len(gaps),'ha':gapsHa},'lotHa':round(float(lot.sum())/1e4,2)},open(O+'canopy.json','w'))

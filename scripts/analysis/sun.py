import numpy as np,json,math,time
from scipy import ndimage
from PIL import Image
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/'
z=np.load(D+'canopy_bright-tree_2022.npz')
dem=np.load('/tmp/claude-0/work/dem2022.npy').astype(np.float32)
top=z['top'].astype(np.float32)
chm=np.clip(np.nan_to_num(top-dem,nan=0),0,70)
chm=ndimage.grey_dilation(chm,size=(2,2))
dem2=ndimage.zoom(np.nan_to_num(dem,nan=np.nanmean(dem)),0.5,order=1)  # 2 m
dsm2=dem2+chm.reshape(1000,2,1000,2).max(axis=(1,3))
recv=dem2+1.0
lat=math.radians(-26.743);N=1000;res=2.0
def sunpos(doy,hour):
    decl=math.radians(23.44)*math.sin(2*math.pi*(284+doy)/365)
    ha=math.radians(15*(hour-12))
    alt=math.asin(math.sin(lat)*math.sin(decl)+math.cos(lat)*math.cos(decl)*math.cos(ha))
    az=math.atan2(-math.sin(ha),math.tan(decl)*math.cos(lat)-math.sin(lat)*math.cos(ha))  # from north, clockwise
    return alt,az
def hours(doy,step=1/3):
    lit=np.zeros((N,N),np.float32);t0=time.time()
    for hr in np.arange(5,19.0001,step):
        alt,az=sunpos(doy,hr)
        if alt<math.radians(5):continue
        dx=math.sin(az);dy=-math.cos(az);tn=math.tan(alt)
        shade=np.zeros((N,N),bool)
        maxd=min(300,70/tn)
        for d in np.arange(res,maxd,res):
            ox=int(round(dx*d/res));oy=int(round(dy*d/res))
            sh=np.full((N,N),-1e9,np.float32)
            ys=slice(max(0,-oy),N-max(0,oy));xs=slice(max(0,-ox),N-max(0,ox))
            yt=slice(max(0,oy),N-max(0,-oy));xt=slice(max(0,ox),N-max(0,-ox))
            sh[ys,xs]=dsm2[yt,xt]
            shade|=sh>recv+d*tn
        lit+=(~shade)*step
    print('doy',doy,round(time.time()-t0),'s');return lit
W=hours(172);E=hours(80)
np.save('sunW_trees.npy',W);np.save('sunE_trees.npy',E)
def img(h,mx,fn):
    t=np.clip(h/mx,0,1)
    stops=[(0,(30,40,110)),(.35,(90,70,150)),(.6,(220,110,70)),(.85,(250,200,70)),(1,(255,245,170))]
    out=np.zeros((N,N,4),np.uint8)
    for (a,ca),(b,cb) in zip(stops,stops[1:]):
        m=(t>=a)&(t<=b);f=((t-a)/(b-a))[m][:,None];out[m,:3]=(np.array(ca)*(1-f)+np.array(cb)*f).astype(np.uint8)
    out[...,3]=200;Image.fromarray(out,'RGBA').save(fn,optimize=True)
img(W,8,'out/sun_winter_trees.png');img(E,11,'out/sun_equinox_trees.png')
t=json.load(open('/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/brighttree-map/terrain.json'))
from matplotlib.path import Path as MP
L=np.array(t['lot']).reshape(-1,2)/2;yy,xx=np.mgrid[0:N,0:N];lot=MP(L).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(N,N)
res_={'winterMean':float(W[lot].mean()),'equinoxMean':float(E[lot].mean()),'winter4hHa':float((W[lot]>=4).sum()*4/1e4),'winter6hHa':float((W[lot]>=6).sum()*4/1e4),'equinox6hHa':float((E[lot]>=6).sum()*4/1e4)}
print(res_);json.dump(res_,open('out/sun_trees.json','w'))

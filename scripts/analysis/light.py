import numpy as np,json
from scipy import ndimage
from PIL import Image
from matplotlib.path import Path as MP
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/'
z=np.load(D+'canopy_bright-tree_2022.npz')
fr=z['first'].astype(np.float32);hi=z['first_hi'].astype(np.float32)
k=np.ones((3,3));frS=ndimage.convolve(fr,k);hiS=ndimage.convolve(hi,k)
gap=np.where(frS>=6,1-hiS/np.maximum(frS,1),np.nan)
gap=np.nan_to_num(gap,nan=np.nanmedian(gap))
out={}
t=json.load(open('/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/brighttree-map/terrain.json'))
L=np.array(t['lot']).reshape(-1,2)/2;yy,xx=np.mgrid[0:1000,0:1000];lot=MP(L).contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(1000,1000)
def make(season,f,mx,noon_alt):
    s=np.load(f'/tmp/claude-0/work/sun_{season}.npy').astype(np.float32)
    if s.shape!=(1000,1000):s=ndimage.zoom(s,1000/s.shape[0],order=1)
    T=np.clip(gap,0,1)**(1/np.sin(np.radians(noon_alt)))
    eff=s*T
    t_=np.clip(eff/mx,0,1)
    stops=[(0,(25,30,70,170)),(.15,(70,60,140,150)),(.35,(200,100,70,170)),(.6,(250,190,70,190)),(1,(255,245,170,210))]
    img=np.zeros((1000,1000,4),np.uint8)
    for (a,ca),(b,cb) in zip(stops,stops[1:]):
        m=(t_>=a)&(t_<=b);g=((t_-a)/(b-a))[m][:,None];img[m]=(np.array(ca)*(1-g)+np.array(cb)*g).astype(np.uint8)
    Image.fromarray(img,'RGBA').save(f'out/{f}.png',optimize=True)
    e=eff[lot];out[season]={'mean':round(float(e.mean()),2),'ha2h':round(float((e>=2).sum()*4/1e4),2),'ha4h':round(float((e>=4).sum()*4/1e4),2),'ha6h':round(float((e>=6).sum()*4/1e4),2)}
    np.save(f'eff_{season}.npy',eff)
make('winter','light_winter',6,40);make('equinox','light_equinox',8,63)
out['gapMean']=round(float(gap[lot].mean()),3)
print(out);json.dump(out,open('out/light.json','w'))

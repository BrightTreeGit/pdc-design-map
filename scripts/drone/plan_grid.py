"""Plan a terrain-aware mapping grid for a DJI Mini 4/5 Pro over Bright Tree.
Lines run parallel to the south boundary; each waypoint sits CLEAR m above the tallest
tree top (2022 LiDAR) in the strip it photographs. Heights are relative to the take-off spot.
Outputs mission JSON (consumed by make_kmz.py), a Google Earth KML and a preview PNG."""
import numpy as np, json, sys, math
from scipy import ndimage
from matplotlib.path import Path
W='/tmp/claude-0/work/'; D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/'
OUT=sys.argv[1] if len(sys.argv)>1 else '.'
CROSS=len(sys.argv)>2 and sys.argv[2]=='cross'   # second pass at right angles
CLEAR=45.0      # m above the tallest crown under each stretch
MINCLEAR=30.0   # never less than this anywhere on the path
SPACING=20.0 if CROSS else 16.0    # m between lines (75% side overlap at 45 m above crowns, 24 mm lens, 4:3)
SPEED=4.5       # m/s; with a 2 s timed shot = photo every 9 m (~80% front overlap)
BUF=30.0        # m beyond the boundary so the edges are fully covered
STEP=40.0       # m between waypoints along a line (height can change at each)
MAXWP=95        # waypoints per mission
MAXAGL=117.0    # legal limit is 120 m above the ground directly below
dem=np.load(W+'dem2022.npy'); z=np.load(D+'canopy_bright-tree_2022.npz'); top=z['top'].astype(float)
surf=np.where(np.isfinite(top),np.maximum(top,dem),dem)
surf=ndimage.grey_dilation(np.nan_to_num(surf,nan=0),size=(5,5))   # crowns spread + margin
t=json.load(open('/home/claude/pdc-design-map/map/terrain.json')); E0,N0=t['E0'],t['N0']
L=np.array(t['lot']).reshape(-1,2)
TAKEOFF={'SW':(711,1209),'SE':(1091,1155)}
ang=math.atan2(L[1][1]-L[0][1],L[1][0]-L[0][0])           # direction of the south boundary
if CROSS: ang+=math.pi/2
ux,uy=math.cos(ang),math.sin(ang); vx,vy=-uy,ux           # u along lines, v across
P=Path(L); yy,xx=np.mgrid[0:2000,0:2000]
lot=P.contains_points(np.c_[xx.ravel()+.5,yy.ravel()+.5]).reshape(2000,2000)
cover=ndimage.distance_transform_edt(~lot)<=BUF
U=(xx+.5)*ux+(yy+.5)*uy; V=(xx+.5)*vx+(yy+.5)*vy
uc,vc=U[cover],V[cover]
lines=[]; v=vc.max()-SPACING/2   # first pass starts at the south edge; cross pass at the west edge
while v>=vc.min()-SPACING/2+1e-6:
    m=np.abs(vc-v)<=SPACING/2
    if m.sum()>0:
        u0,u1=uc[m].min(),uc[m].max(); lines.append((v,u0,u1))
    v-=SPACING
def xy(u,v): return (u*ux+v*vx, u*uy+v*vy)
def need(u,v):  # required absolute altitude to sit CLEAR above crowns in a window around (u,v)
    x,y=xy(u,v); r=int(SPACING); i,j=int(round(x)),int(round(y))
    win=surf[max(0,j-r):j+r+1,max(0,i-r):i+r+1]; return float(win.max())+CLEAR
def toLL(E,N,ZONE=56):  # MGA (GRS80) to lon/lat, Kruger series (same as the map)
    a=6378137;f=1/298.257222101;k0=.9996;FE=5e5;FN=1e7;n=f/(2-f);A=a/(1+n)*(1+n*n/4+n**4/64);e=math.sqrt(f*(2-f))
    be=[n/2-2*n*n/3+37*n**3/96,n*n/48+n**3/15,17*n**3/480];xi=(N-FN)/(k0*A);eta=(E-FE)/(k0*A);xp,ep=xi,eta
    for j in range(3):
        k=2*(j+1);xp-=be[j]*math.sin(k*xi)*math.cosh(k*eta);ep-=be[j]*math.cos(k*xi)*math.sinh(k*eta)
    chi=math.asin(math.sin(xp)/math.cosh(ep));lat=chi
    for i in range(6):lat=math.asin(math.tanh(math.atanh(math.sin(chi))+e*math.atanh(e*math.sin(lat))))
    return math.degrees((ZONE*6-183)*math.pi/180+math.atan2(math.sinh(ep),math.cos(xp))),math.degrees(lat)
def ll(x,y): lo,la=toLL(E0+x,N0-y); return [round(lo,7),round(la,7)]
def plan(corner):
    tx,ty=TAKEOFF[corner]; z0=float(dem[ty,tx])
    ls=list(lines)
    # serpentine, first line starts at the end nearest the take-off corner
    tu=tx*ux+ty*uy; start_low=abs(ls[0][1]-tu)<abs(ls[0][2]-tu)
    pts=[]
    for k,(v,u0,u1) in enumerate(ls):
        n=max(1,int(math.ceil((u1-u0)/STEP))); us=[u0+(u1-u0)*i/n for i in range(n+1)]
        if (k%2==0)!=start_low: us=us[::-1]
        hs=[need(u,v) for u in us]
        hs=[max(hs[max(0,i-1):i+2]) for i in range(len(hs))]   # straight legs stay above the envelope
        for i,(u,h) in enumerate(zip(us,hs)):
            x,y=xy(u,v); pts.append({'x':x,'y':y,'abs':h,'line':k,'end':i in (0,len(us)-1)})
    # make sure the turn between lines is safe: both ends of a connector at the higher of the two
    for a,b in zip(pts,pts[1:]):
        if a['line']!=b['line']:
            m=max(a['abs'],b['abs']); a['abs']=b['abs']=m
    # stay under 120 m above the ground below: cap each waypoint by the lowest ground on its two legs,
    # but never closer than MINCLEAR to the crowns there
    def legs(i):
        out=[]
        for j in (i-1,i+1):
            if 0<=j<len(pts):
                a,b=pts[i],pts[j];n=max(2,int(math.hypot(b['x']-a['x'],b['y']-a['y'])/2))
                out+=[(a['x']+(b['x']-a['x'])*s,a['y']+(b['y']-a['y'])*s) for s in np.linspace(0,1,n)]
        return out
    for _ in range(3):
        for i,p in enumerate(pts):
            q=legs(i);g=min(dem[int(y),int(x)] for x,y in q);c=max(surf[int(y),int(x)] for x,y in q)
            p['abs']=float(max(min(p['abs'],g+MAXAGL),c+MINCLEAR))
    for p in pts:
        p['rel']=max(5.0,round(p['abs']-z0,1)); p['abs']=p['rel']+z0; p['ll']=ll(p['x'],p['y'])
    # split into missions by whole lines
    missions=[];cur=[];curlines=set()
    for k in range(len(ls)):
        lp=[p for p in pts if p['line']==k]
        if len(cur)+len(lp)>MAXWP: missions.append(cur);cur=[]
        cur+=lp
    if cur: missions.append(cur)
    # safe transit: climb over the take-off spot, cross to the first line high, drop in; reverse at the end
    def pathmax(ax,ay,bx,by):
        n=int(math.hypot(bx-ax,by-ay)/2)+2;xs=np.linspace(ax,bx,n);ys=np.linspace(ay,by,n);return float(surf[ys.astype(int),xs.astype(int)].max())
    out=[]
    for m in missions:
        f,l=m[0],m[-1]
        T=max(pathmax(tx,ty,f['x'],f['y']),pathmax(l['x'],l['y'],tx,ty))+MINCLEAR-z0
        T=max(T,f['rel'],l['rel']);T=round(T+0.4)
        mk=lambda x,y:{'x':x,'y':y,'rel':float(T),'abs':z0+T,'ll':ll(x,y),'line':-1,'end':True,'transit':True}
        out.append([mk(tx,ty),mk(f['x'],f['y'])]+m+[mk(l['x'],l['y']),mk(tx,ty)])
    # straight-line return-to-home altitude that clears every crown between the lot and home
    rth=0
    for yy_ in range(800,1260,10):
        for xx_ in range(680,1160,10):
            if cover[yy_,xx_]: rth=max(rth,pathmax(xx_,yy_,tx,ty))
    return z0,pts,out,round(rth-z0+MINCLEAR)
def check(z0,path):
    """sample every 2 m: clearance over crowns and height above the ground directly below"""
    cl=[];agl=[];dist=0
    for a,b in zip(path,path[1:]):
        d=math.hypot(b['x']-a['x'],b['y']-a['y']);dist+=d;n=max(2,int(d/2))
        for s in np.linspace(0,1,n):
            x=a['x']+(b['x']-a['x'])*s;y=a['y']+(b['y']-a['y'])*s;h=a['abs']+(b['abs']-a['abs'])*s
            i,j=int(x),int(y);cl.append(h-np.nanmax([top[j,i] if np.isfinite(top[j,i]) else dem[j,i],dem[j,i]]));agl.append(h-dem[j,i])
    return min(cl),max(agl),dist
res={}
for c in TAKEOFF:
    z0,pts,ms,rth=plan(c);tx,ty=TAKEOFF[c]
    out=[]
    for mi,m in enumerate(ms):
        home={'x':tx,'y':ty,'abs':z0}
        g=[p for p in m if not p.get('transit')];cmin,_,_=check(z0,m);_,amax,dist=check(z0,g);tdist=check(z0,m)[2]-dist
        far=max(math.hypot(p['x']-tx,p['y']-ty) for p in m)
        mins=(dist/SPEED+tdist/8+len([p for p in m if p['end']])*4+60)/60
        out.append({'n':len(m),'lines':len({p['line'] for p in m}),'km':round(dist/1000,2),'minutes':round(mins,1),'photos':int(dist/(SPEED*2)),'transit_rel':m[0]['rel'],
                    'min_clear_m':round(float(cmin),1),'max_agl_m':round(float(amax),1),'rel_min':min(p['rel'] for p in m),'rel_max':max(p['rel'] for p in m),'farthest_m':round(far),
                    'first_rel':m[0]['rel'],'wps':[{'ll':p['ll'],'rel':p['rel'],'x':round(p['x'],1),'y':round(p['y'],1),'transit':bool(p.get('transit'))} for p in m]})
    res[c]={'rth_rel':rth,'takeoff_xy':[tx,ty],'takeoff_ll':ll(tx,ty),'takeoff_elev':round(z0,1),'missions':out}
meta={'clear':CLEAR,'spacing':SPACING,'speed':SPEED,'interval_s':2,'buffer':BUF,'lines':len(lines),'source':'2022 LiDAR (QLD), crowns dilated 2 m'}
meta['pass']='cross' if CROSS else 'main'
json.dump({'meta':meta,'plans':res},open(OUT+('/mission_plan_cross.json' if CROSS else '/mission_plan.json'),'w'))
for c,r in res.items():
    print(c,r['takeoff_elev'],'RTH',r['rth_rel'],[{k:v for k,v in m.items() if k!='wps'} for m in r['missions']])

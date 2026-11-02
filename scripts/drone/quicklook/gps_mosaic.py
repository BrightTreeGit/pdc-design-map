import json,numpy as np,math,sys
from PIL import Image
D='/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
P='/mnt/user-data/uploads/Claude Access--Permiculture Noosa PDC/Noosa Forest Retreat/Drone/'
rows=[r for r in json.load(open(D+'nfr_exif.json')) if r['gp']<-85]
G=float(sys.argv[1]) if len(sys.argv)>1 else 45.0; K=1.394   # footprint width = K * AGL (DJI Mini 4 Pro, 82.1 deg diagonal, 4:3)
PPM=float(sys.argv[2]) if len(sys.argv)>2 else 1.5
if len(sys.argv)>6: OX,OY,SW,SH=float(sys.argv[3]),float(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6])
else: OX,OY=(0,0) if PPM<=1.5 else (840,620); SW,SH=(3000,3000) if PPM<=1.5 else (int(260*PPM),int(520*PPM))
OUT=sys.argv[7] if len(sys.argv)>7 else None
S=max(SW,SH); acc=np.zeros((SH,SW,3),float); wsum=np.zeros((SH,SW),float)
seen=set()
for r in rows:
    key=(round(r['x']/8),round(r['y']/8))
    if key in seen: continue
    seen.add(key)
    agl=r['abs']-G-r['ground']
    if agl<30: continue
    wm=K*agl; wpx=wm*PPM            # photo width in output px
    im=Image.open(P+r['f']).convert('RGB'); im=im.resize((int(wpx),int(wpx*3/4)),Image.LANCZOS)
    # feather mask: cosine from centre, strongest in the middle
    h,w=im.size[1],im.size[0]; yy,xx=np.mgrid[0:h,0:w]; m=np.cos(np.pi/2*np.abs((xx-w/2)/(w/2)))*np.cos(np.pi/2*np.abs((yy-h/2)/(h/2)))
    mk=Image.fromarray((np.clip(m,0,1)**6*255).astype('uint8'))
    im=im.rotate(r['gy'],expand=True,resample=Image.BICUBIC); mk=mk.rotate(r['gy'],expand=True,resample=Image.BILINEAR)
    a=np.asarray(im,float); wgt=np.asarray(mk,float)/255
    cx,cy=(r['x']-OX)*PPM,(r['y']-OY)*PPM; x0=int(round(cx-im.size[0]/2)); y0=int(round(cy-im.size[1]/2))
    xs0,ys0=max(0,x0),max(0,y0); xs1,ys1=min(SW,x0+im.size[0]),min(SH,y0+im.size[1])
    if xs1<=xs0 or ys1<=ys0: continue
    sub=a[ys0-y0:ys1-y0, xs0-x0:xs1-x0]; wg=wgt[ys0-y0:ys1-y0, xs0-x0:xs1-x0]
    acc[ys0:ys1,xs0:xs1]+=sub*wg[...,None]; wsum[ys0:ys1,xs0:xs1]+=wg
out=np.where(wsum[...,None]>0.002, acc/np.maximum(wsum,1e-6)[...,None], 0).astype('uint8')
alpha=(np.clip(wsum/0.02,0,1)*255).astype('uint8')
img=Image.fromarray(out); img.putalpha(Image.fromarray(alpha))
if OUT: img.save(OUT); print('photos used',len(seen)); sys.exit()
img.save(D+('nfr/drone_mosaic.png' if PPM<=1.5 else 'nfr/drone_mosaic_hi.png')); print('photos used',len(seen))
if PPM>1.5: img.convert('RGB').save(D+'nfr/drone_mosaic_hi.jpg',quality=88); sys.exit()
# alignment check: blend over the map aerial, crop to coverage
ae=Image.open('/home/claude/pdc-design-map/map/sites/noosa-forest-retreat/aerial.jpg').convert('RGBA')
ys,xs=np.where(wsum>0.05); box=(xs.min()-30,ys.min()-30,xs.max()+30,ys.max()+30)
over=Image.alpha_composite(ae,img).crop(box).convert('RGB'); over.save(D+'nfr/check_overlay.jpg')
side=Image.new('RGB',(over.size[0]*2,over.size[1])); side.paste(ae.crop(box).convert('RGB'),(0,0)); side.paste(over.convert('RGB'),(over.size[0],0)); side.save(D+'nfr/check_side.jpg'); print(box)

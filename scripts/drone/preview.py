import json,sys,numpy as np
from PIL import Image,ImageDraw,ImageFont
d=json.load(open(sys.argv[1]));out=sys.argv[2]
A=Image.open('/home/claude/pdc-design-map/map/aerial.jpg').convert('RGB');s=A.width/2000
x0,y0,x1,y1=640,800,1200,1290;A=A.crop((int(x0*s),int(y0*s),int(x1*s),int(y1*s))).resize((int((x1-x0)*2),int((y1-y0)*2)))
k=2;P=lambda x,y:((x-x0)*k,(y-y0)*k)
im=A.copy();dr=ImageDraw.Draw(im,'RGBA')
try: F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22);f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
except: F=f=ImageFont.load_default()
t=json.load(open('/home/claude/pdc-design-map/map/terrain.json'));L=np.array(t['lot']).reshape(-1,2)
dr.line([P(*q) for q in L]+[P(*L[0])],fill=(0,255,255,255),width=3)
cols=[(255,165,0,255),(50,220,50,255),(80,160,255,255)]
SW=d['plans']['SW']
for k_,m in enumerate(SW['missions']):
    g=[w for w in m['wps'] if not w['transit']]
    dr.line([P(w['x'],w['y']) for w in g],fill=cols[k_],width=3)
    lx=min(w['x'] for w in g);ly=np.mean([w['y'] for w in g])
for c,(tx,ty) in [('SW',SW['takeoff_xy']),('SE',d['plans']['SE']['takeoff_xy'])]:
    X,Y=P(tx,ty);dr.ellipse([X-12,Y-12,X+12,Y+12],fill=(255,255,255,255),outline=(0,0,0,255),width=3);dr.text((X+16,Y-30),'Take-off '+c,font=F,fill=(255,255,255,255),stroke_width=3,stroke_fill=(0,0,0,255))
dr.rectangle([0,0,1000,126],fill=(0,0,0,150));y=12
for k_,m in enumerate(SW['missions']):
    dr.rectangle([12,y+4,40,y+20],fill=cols[k_]);dr.text((48,y),f"{'Cross ' if d['meta'].get('pass')=='cross' else 'Mission '}{k_+1}: {m['minutes']:.0f} min, ~{m['photos']} photos",font=f,fill=(255,255,255,255),stroke_width=3,stroke_fill=(0,0,0,255));y+=28
dr.text((12,y),("Inside the boundary · " if d["meta"]["buffer"]==0 else f"{d['meta']['buffer']:.0f} m past the boundary · ")+f"Lines {d['meta']['spacing']:.0f} m apart · {d['meta']['clear']:.0f} m above the tallest crown · {d['meta']['speed']} m/s · photo every 2 s",font=f,fill=(255,255,255,255),stroke_width=3,stroke_fill=(0,0,0,255))
im.save(out,quality=88);print(im.size)

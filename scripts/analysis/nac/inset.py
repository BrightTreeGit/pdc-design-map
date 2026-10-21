import json,sys,numpy as np,math
sys.path.insert(0,'/tmp/claude-0/scripts'); from build_site import mga2ll,ll2mga
from PIL import Image; from scipy import ndimage
D='/mnt/user-data/uploads/Permiculture Noosa PDC/NAC/Lidar-survey data/NSW site pack nac/'
T=D+'inset_tiles_z20/';idx=json.load(open(T+'index.json'));z=idx['z'];nx=idx['x1']-idx['x0']+1;ny=idx['y1']-idx['y0']+1
mos=Image.new('RGB',(nx*256,ny*256))
for x in range(idx['x0'],idx['x1']+1):
  for y in range(idx['y0'],idx['y1']+1):
    mos.paste(Image.open(T+f'{z}_{x}_{y}.jpg').convert('RGB'),((x-idx['x0'])*256,(y-idx['y0'])*256))
M=np.asarray(mos).astype(np.float32);n=2**z
w=json.load(open(D+'window.json'));E0,N0=w['E0'],w['N0']
# tile extent corners -> MGA
def t2ll(px,py):
  lon=px/(n*256)*360-180;lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*py/(n*256)))));return lon,lat
corners=[t2ll(idx['x0']*256,idx['y0']*256),t2ll((idx['x1']+1)*256,(idx['y1']+1)*256)]
(e1,n1)=ll2mga(*corners[0],56);(e2,n2)=ll2mga(*corners[1],56)
e1,n1,e2,n2=float(e1),float(n1),float(e2),float(n2);m=3
x0=math.ceil(e1-E0)+m;x1=math.floor(e2-E0)-m;y0=math.ceil(N0-n1)+m;y1=math.floor(N0-n2)-m
res=0.15;W=int((x1-x0)/res);H=int((y1-y0)/res);print('local',x0,x1,y0,y1,W,H)
uu=x0+(np.arange(W)+.5)*res;vv=y0+(np.arange(H)+.5)*res;XX,YY=np.meshgrid(uu,vv)
lon,lat=mga2ll(E0+XX,N0-YY,56)
X=(lon+180)/360*n*256-idx['x0']*256;la=np.radians(lat);Y=(1-np.log(np.tan(la)+1/np.cos(la))/math.pi)/2*n*256-idx['y0']*256
out=np.dstack([ndimage.map_coordinates(M[...,c],[Y,X],order=1,mode='nearest') for c in range(3)]).astype(np.uint8)
Image.fromarray(out).save('nac_closeup_2021.jpg',quality=86)
json.dump({'x0':x0,'y0':y0,'res':res,'w':W,'h':H},open('inset.json','w'))
# check overlay with boundary
from PIL import ImageDraw
g=json.load(open(D+'boundary.geojson'))['features'][0]['geometry']['coordinates'][0]
E,N=ll2mga([p[0] for p in g],[p[1] for p in g],56)
im=Image.fromarray(out);d=ImageDraw.Draw(im)
d.line([(((e-E0)-x0)/res,((N0-nn)-y0)/res) for e,nn in zip(E,N)],fill=(0,220,200),width=4)
im.resize((W//2,H//2)).save('chk.jpg')

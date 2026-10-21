import json,sys,numpy as np,cv2
sys.path.insert(0,'/tmp/claude-0/scripts'); from build_site import ll2mga
D='/mnt/user-data/uploads/Permiculture Noosa PDC/NAC/Lidar-survey data/NSW site pack nac/'
w=json.load(open(D+'window.json'));E0,N0=w['E0'],w['N0']
c=json.load(open(D+'boundary.geojson'))['features'][0]['geometry']['coordinates'][0]
E,N=ll2mga([p[0] for p in c],[p[1] for p in c],56);L=np.c_[np.array(E)-E0,N0-np.array(N)]
for i,p in enumerate(L):print(i,p.round(1))
src=np.float32([[545,300],[450,392],[945,372],[258,1985],[715,2030],[885,1895]])
dst=np.float32([L[11],L[12],L[10],L[13],L[3],L[9]])
H,_=cv2.findHomography(src,dst,0)
pr=cv2.perspectiveTransform(src[None],H)[0];print('resid m',np.hypot(*(pr-dst).T).round(2))
json.dump({'H':H.tolist()},open('planH.json','w'))
im=cv2.imread('plan_photo.jpg')
x0,y0=L[:,0].min()-6,L[:,1].min()-6;x1,y1=L[:,0].max()+6,L[:,1].max()+6;res=0.05
W,Hh=int((x1-x0)/res),int((y1-y0)/res)
T=np.array([[1/res,0,-x0/res],[0,1/res,-y0/res],[0,0,1]])
out=cv2.warpPerspective(im,T@H,(W,Hh),flags=cv2.INTER_AREA,borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255))
# make paper white transparent-ish: convert to RGBA, alpha by darkness/colour
o=cv2.cvtColor(out,cv2.COLOR_BGR2RGB).astype(np.float32)
bg=cv2.GaussianBlur(o,(0,0),25)  # remove paper shading
n=np.clip(o/np.maximum(bg,1)*235,0,255)
dark=255-n.min(axis=2);sat=n.max(axis=2)-n.min(axis=2)
a=np.clip((np.maximum(dark-10,0)*7+sat*5),0,255)
st=np.clip(n-(255-n)*1.2,0,255)  # darken strokes
a=np.maximum(a,95)
rgba=np.dstack([st,a]).astype(np.uint8)
mask=cv2.warpPerspective(np.full(im.shape[:2],255,np.uint8),T@H,(W,Hh));rgba[...,3]=np.minimum(rgba[...,3],mask)
lm=np.zeros((Hh,W),np.uint8);cv2.fillPoly(lm,[((L-[x0,y0])/res).astype(np.int32)],255);lm=cv2.dilate(lm,np.ones((3,3),np.uint8),iterations=int(3/res));lm=cv2.GaussianBlur(lm,(0,0),6)
rgba[...,3]=(rgba[...,3].astype(np.float32)*lm/255).astype(np.uint8)
cv2.imwrite('ange_plan.png',cv2.cvtColor(rgba,cv2.COLOR_RGBA2BGRA))
json.dump({'x0':float(x0),'y0':float(y0),'res':res,'w':W,'h':Hh},open('ange_plan.json','w'))
# check over closeup
from PIL import Image
cl=Image.open('nac_closeup_2021.jpg').convert('RGBA');ins=json.load(open('inset.json'))
pl=Image.open('ange_plan.png').resize((int(W*res/ins['res']),int(Hh*res/ins['res'])))
cl.alpha_composite(pl,(int((x0-ins['x0'])/ins['res']),int((y0-ins['y0'])/ins['res'])))
from PIL import ImageDraw
d=ImageDraw.Draw(cl);d.line([((p[0]-ins['x0'])/ins['res'],(p[1]-ins['y0'])/ins['res']) for p in L],fill=(0,230,210),width=3)
cl.crop((350,400,1250,1000)).save('plan_chk.png')
print(W,Hh,os.path.getsize('ange_plan.png') if False else '')

import cv2, numpy as np, pickle
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
O=pickle.load(open('Tfull.pkl','rb'))
ref=cv2.imread(D+'ref_1994.jpg')
tiles=[]
def crop(im): return cv2.resize(im[1500:2500,1500:2500],(330,330))
r=crop(ref); cv2.putText(r,'1994 ref',(5,20),0,.6,(0,0,255),2); tiles.append(r)
for n,(Tf,inl) in sorted(O.items()):
    im=cv2.imread(D+n+'.jpg'); w=cv2.warpPerspective(im,Tf,(4000,4000))
    t=crop(w); cv2.putText(t,n[5:9],(5,20),0,.6,(0,0,255),2); tiles.append(t)
while len(tiles)%4: tiles.append(np.zeros_like(tiles[0]))
rows=[np.hstack(tiles[i:i+4]) for i in range(0,len(tiles),4)]
g=np.vstack(rows)
# grid lines for comparison
for x in range(0,g.shape[1],110): g[:,x]=(0,255,255)
for y in range(0,g.shape[0],110): g[y,:]=(0,255,255)
cv2.imwrite('viz.jpg',g,[cv2.IMWRITE_JPEG_QUALITY,80])

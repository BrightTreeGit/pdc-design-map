import cv2, numpy as np, pickle
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/wide/'
O=pickle.load(open('Tecc.pkl','rb'))
ref=cv2.imread(D+'ref_1994.jpg')
def crop(im): return cv2.resize(im[1550:2450,1550:2450],(440,440))
tiles=[]
for n,(Tf,cc) in sorted(O.items()):
    im=cv2.imread(D+n+'.jpg'); w=cv2.warpPerspective(im,Tf,(4000,4000))
    a=crop(w);b=crop(ref)
    # checkerboard 4x4
    m=np.zeros((440,440),bool)
    for i in range(4):
        for j in range(4):
            if (i+j)%2: m[i*110:(i+1)*110,j*110:(j+1)*110]=True
    t=np.where(m[...,None],b,a).copy(); cv2.putText(t,n[5:9]+' / 1994 checker',(5,22),0,.65,(0,0,255),2); tiles.append(t)
while len(tiles)%4: tiles.append(np.zeros_like(tiles[0]))
g=np.vstack([np.hstack(tiles[i:i+4]) for i in range(0,len(tiles),4)])
cv2.imwrite('viz2.jpg',g,[cv2.IMWRITE_JPEG_QUALITY,82])

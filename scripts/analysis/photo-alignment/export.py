import cv2, numpy as np, pickle, json, sys
D='/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Aerial and Google Maps/old_photos/'
R=pickle.load(open('Tecc.pkl','rb'))
meta={r['id']:r for r in json.load(open(D+'old_photos.json'))['runs']}
O=np.array([[2,0,-3200],[0,2,-3200],[0,0,1.]])
out=json.load(open('old_out.json')) if len(sys.argv)>2 else {}
for n in sys.argv[1].split(','):
    oid=int(n.split('_')[2]); y=int(n.split('_')[1])
    im=cv2.imread(D+'wide/'+n+'.jpg')
    w=cv2.warpPerspective(im,O@R[n][0],(1600,1600),flags=cv2.INTER_CUBIC)
    cover=float((w.max(2)>8).mean())
    fn=f'o{y}_{oid}.jpg'; cv2.imwrite('/tmp/claude-0/work/reg/out/'+fn,w,[cv2.IMWRITE_JPEG_QUALITY,80])
    r=meta[oid]; out[n]={'y':y,'id':oid,'from':r['date'],'to':r['date'],'res':float(r['scan_res_m'] or 0),'f':fn,'name':r['frame'],'old':True,'cover':round(cover,2)}
    print(fn,cover)
json.dump(out,open('old_out.json','w'),indent=1)

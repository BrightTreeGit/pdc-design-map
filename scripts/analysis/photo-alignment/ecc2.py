exec(open('ecc.py').read().split('res={}')[0])
import pickle
R=pickle.load(open('Tecc.pkl','rb'))
g97=cv2.warpPerspective(cv2.imread(D+'wide_1997_369968.jpg',0),R['wide_1997_369968'][0],(4000,4000))
g=cv2.imread(D+'wide_1995_719593.jpg',0)
for init in (O['wide_1995_719593'][0],):
    Tf,cc,fn=ecc(g,g97,init)
    c=Tf@np.array([2000,2000,1.]);c0=init@np.array([2000,2000,1.]);print('1995 vs 1997',cc,fn,np.linalg.norm(c[:2]/c[2]-c0[:2]/c0[2])*1.25)
R['wide_1995_719593']=(Tf,cc);pickle.dump(R,open('Tecc.pkl','wb'))

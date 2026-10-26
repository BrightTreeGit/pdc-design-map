import json
FF=dict(k=26.4,off=(548.26,830.5),polys={
 'ff02':('shed','Four-bay shed',[(657,32),(1190,148),(1165,300),(622,215)]),
 'ff01':('building','Main house',[(432,672),(698,712),(690,792),(812,806),(855,1150),(640,1142),(632,1200),(522,1195),(526,1142),(418,1128),(392,1040),(405,862),(425,858)]),
 'ff03':('cabin','Cabin (family member)',[(1158,966),(1335,985),(1398,1045),(1382,1150),(1265,1140),(1215,1175),(1195,1240),(1108,1232),(1115,1110),(1140,1100)])})
WV=dict(k=32.4,off=(1071.25,1091.2),polys={
 'wvb1':('building','House',[(865,455),(1365,780),(1200,1015),(890,800),(905,690),(800,575)]),
 'wvb2':('shed','Shed / garage (two round tanks on its east side)',[(1130,160),(1565,200),(1550,495),(1120,455)]),
 'wvb3':('shed','Small shed (west of the house)',[(140,212),(285,185),(300,310),(160,332)])})
def conv(S):
    out={}
    for k,(kind,name,P) in S['polys'].items():
        out[k]=(kind,name,[[round(S['off'][0]+x/S['k'],1),round(S['off'][1]+y/S['k'],1)] for x,y in P])
    return out
if __name__=='__main__':
    json.dump({'ff':conv(FF),'wv':conv(WV)},open('traced.json','w'),indent=1)
    from PIL import Image,ImageDraw
    for s,site,box in [('ff','nimbin',(540,815,625,895)),('wv','willow-vale',(1070,1085,1130,1130))]:
        T=conv(FF if s=='ff' else WV)
        aer=Image.open(f'/home/claude/pdc-design-map/map/sites/{site}/aerial.jpg');kk=aer.size[0]/2000;Z=10
        c=aer.crop(tuple(int(v*kk) for v in box)).resize(((box[2]-box[0])*Z,(box[3]-box[1])*Z),Image.LANCZOS);d=ImageDraw.Draw(c)
        for kind,name,P in T.values():
            d.line([((x-box[0])*Z,(y-box[1])*Z) for x,y in P+[P[0]]],fill=(255,0,0),width=3)
        c.save(f'ov_{s}.png')

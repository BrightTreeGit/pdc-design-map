import json,glob,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import Polygon, Patch
from matplotlib.lines import Line2D
from matplotlib.colors import ListedColormap
D='/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
T=json.load(open('/home/claude/pdc-design-map/map/sites/annwn/terrain.json'));lot=np.array(T['lot'],float).reshape(-1,2)
F={}
for f in glob.glob(D+'annwn_db_now/annwn_features/*.json'):F[f.split('/')[-1][:-5]]=json.load(open(f))
for f in glob.glob(D+'annwn_new/*.json'):F[f.split('/')[-1][:-5]]=json.load(open(f))
F['an33']['geom']={'g':'point','pts':[[1009,981.3]]}
X=lambda p:(p[0],-p[1])
main=np.array(F['an42']['geom']['pts']);drain=np.array(F['an43']['geom']['pts'])
def segd(P,A,B):
    AB=B-A;t=np.clip(((P-A)@AB)/(AB@AB),0,1);return np.linalg.norm(P-(A+t[:,None]*AB),axis=1)
xs=np.arange(980,1014,.1);ys=np.arange(974,1018,.1);gx,gy=np.meshgrid(xs,ys);P=np.c_[gx.ravel(),gy.ravel()]
d=np.minimum.reduce([segd(P,L[i],L[i+1]) for L in (main,drain) for i in range(len(L)-1)]).reshape(gx.shape)
inside=Path(lot).contains_points(P).reshape(gx.shape)
band=np.full(gx.shape,np.nan);band[inside&(d<2)]=0;band[inside&(d>=2)&(d<5)]=1;band[inside&(d>=5)]=2
fig,ax=plt.subplots(figsize=(8.3,9.8),dpi=170)
ax.imshow(band,extent=(xs[0],xs[-1],-ys[-1],-ys[0]),origin='upper',cmap=ListedColormap(['#f0c4bf','#f6e2a8','#dcecc8']),vmin=0,vmax=2,alpha=.9,interpolation='nearest')
ax.add_patch(Polygon([X(p) for p in lot],closed=True,fill=False,ec='#444',lw=1.6))
C={'building':('#b9b1a6','#6d655c'),'shed':('#c9c1b6','#6d655c'),'futurebuilding':('none','#555'),'herbs':('#9cc77a','#4e8a2e'),'raisedbed':('#c89a55','#7a5418'),'pond':('#6fb3e6','#1d6fb8'),'pergola':('#c9a46a','#8a6a3a')}
for k,f in sorted(F.items()):
    g=f['geom'];pts=[X(p) for p in g['pts']];kd=f['kind']
    if g['g']=='polygon':
        fc,ec=C.get(kd,('#b07a2a','#7a5418'))
        ax.add_patch(Polygon(pts,closed=True,fc=fc,ec=ec,lw=1.1,ls='--' if kd=='futurebuilding' else '-',alpha=.95,zorder=3 if kd in('building','shed') else 4))
    elif g['g']=='line':
        sty={'sewer':dict(color='#7a3b9a',lw=2.4,ls=(0,(6,3))),'service':dict(color='#c2571a',lw=1.8,ls=(0,(2,2))),'diversion':dict(color='#3b7fd9',lw=3),'pipe':dict(color='#5c6f80',lw=1.4,ls=(0,(4,3))),'flow':dict(color='#1d6fb8',lw=3.5),'screen':dict(color='#2f6b2a',lw=5),'hedge':dict(color='#3b7a3a',lw=4)}.get(kd,dict(color='#3b7a3a',lw=3))
        ax.plot(*zip(*pts),zorder=5,solid_capstyle='round',**sty)
    else:
        p=pts[0]
        if kd in('fruittree','tree'): ax.add_patch(plt.Circle(p,.7,fc='#2f7d32' if kd=='fruittree' else ('#b23a2e' if 'Callistemon' in f['name'] else ('#1f8a6a' if 'myrtle' in f['name'].lower() else '#55704b')),ec='white',lw=.8,zorder=6))
        elif kd=='tank': ax.add_patch(plt.Circle(p,.55 if f.get('litres',0)<4000 else .75,fc='#3a8fd6' if f['stage']=='existing' else 'white',ec='#1d5b91',lw=1.6,zorder=7))
        elif kd=='structure': ax.add_patch(plt.Circle(p,.5,fc='white',ec='#7a3b9a' if 'manhole' in f['name'].lower() else '#c2571a',lw=1.8,zorder=7))
        elif kd=='seating': ax.add_patch(plt.Circle(p,.45,fc='#9a6aa0',ec='white',lw=.8,zorder=7))
        elif kd=='worms': ax.add_patch(plt.Circle(p,.4,fc='#8a5a2b',ec='white',lw=.8,zorder=7))
        elif kd=='obs': ax.plot(*p,marker='v',ms=8,color='#3b7fd9',zorder=7)
        elif kd=='clothesline': ax.plot(*p,marker='s',ms=5,color='#777',zorder=6)
        else: ax.add_patch(plt.Circle(p,.33,fc='#7aa35a',ec='white',lw=.5,zorder=6))
B=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=.75)
lab=lambda x,y,s,**k: ax.text(x,-y,s,fontsize=k.pop('fs',7),zorder=9,**k)
lab(993,997,'House',ha='center',va='center',fs=10,color='#3d362f',weight='bold')
lab(998.85,1002.6,'Carport',ha='center',va='center',fs=6.5,color='#3d362f',rotation=90)
lab(998.6,984.8,'Big\nshed',ha='center',va='center',fs=8,color='#3d362f')
lab(990.5,987.1,'Small\nshed',ha='center',va='center',fs=6,color='#3d362f')
lab(1000.0,979.9,'Main vegetable garden (full sun)',ha='center',va='center',fs=7,color='#22501a',weight='bold',rotation=-8.5)
lab(1000.65,994.1,'Frog\npond',ha='center',va='center',fs=6.5,color='#0d3e6a',weight='bold')
lab(1001.3,991.3,'creek',ha='left',fs=6.5,color='#1d6fb8',style='italic')
lab(1000.0,998.6,'shaded seat (grape pergola)',ha='center',va='top',fs=6,color='#6a3a70',bbox=B)
lab(992.6,989.1,'New 5,000 L tank',ha='center',va='top',fs=6.3,color='#1d5b91',bbox=B)
lab(1001.5,1006.9,'3,000 L (old)',ha='left',va='top',fs=6.3,color='#1d5b91')
lab(1008.3,982.6,'Manhole',ha='right',va='top',fs=6.5,color='#5d2a78')
lab(1004.6,986.9,'House drain\n(approx.)',ha='left',fs=6,color='#5d2a78',style='italic')
lab(989.0,999,'Rain-garden trench',rotation=86,ha='center',va='center',fs=6.3,color='#1d4f9a')
lab(986.8,1009.0,'Future carport',ha='center',va='center',fs=6.5,color='#444')
lab(984.9,1011.3,'meter',ha='left',va='top',fs=5.8,color='#a04512')
lab(1002.7,1010.8,'Lemon myrtle\n+ wind screen',ha='right',va='center',fs=6.3,color='#1f5a22')
lab(1004.2,996.5,'citrus &\njaboticaba',ha='left',va='center',fs=6.2,color='#1f5a22')
lab(993.6,1010.5,'Front garden (shaded in winter)',ha='center',fs=6.8,color='#4a4a4a')
ax.annotate('',xy=(1012,-976),xytext=(1012,-979.5),arrowprops=dict(arrowstyle='-|>',color='#333',lw=1.2));ax.text(1012,-975.6,'N',ha='center',fontsize=9,weight='bold')
ax.annotate('SE wind\nmost of the year',xy=(1005.3,-1012.2),xytext=(1009.5,-1016.2),fontsize=6.3,color='#3c5f86',ha='center',arrowprops=dict(arrowstyle='-|>',color='#4f86b8',lw=1.4))
ax.plot([982,987],[-1016.3,-1016.3],color='#333',lw=2);ax.text(984.5,-1015.9,'5 m',ha='center',fontsize=7)
ax.set_xlim(980.5,1013.5);ax.set_ylim(-1017.5,-974.5);ax.set_aspect('equal');ax.axis('off')
h=[Patch(fc='#f0c4bf',label='Within 2 m of a sewer: veg, herbs, beds, pots'),Patch(fc='#f6e2a8',label='2–5 m: small shrubs and dwarf fruit under 2.5 m'),Patch(fc='#dcecc8',label='5 m+: avocado, custard apple, larger fruit'),
   Line2D([],[],color='#7a3b9a',ls=(0,(6,3)),lw=2,label='Sewer main and house drain (1983 plan)'),Line2D([],[],color='#1d6fb8',lw=3,label='Creek and rain-garden trench'),Line2D([],[],color='#c2571a',ls=(0,(2,2)),lw=2,label='Water service (approx.)'),
   Line2D([],[],marker='o',ls='',mfc='white',mec='#1d5b91',ms=8,label='Tank: new (open) / existing (filled)'),Line2D([],[],marker='v',ls='',color='#3b7fd9',ms=7,label='Soggy after heavy rain')]
ax.legend(handles=h,loc='lower center',bbox_to_anchor=(.5,-.17),ncol=2,fontsize=6.8,frameon=False)
ax.set_title('Annwn: updated design plan',fontsize=13,loc='left',weight='bold',color='#222',pad=16)
ax.text(0,1.0,"From Bronwen's answers (27 Oct 2026) and the 1983 council house-drainage plan. Positions approximate.",fontsize=7.5,color='#555',transform=ax.transAxes,va='bottom')
fig.savefig(D+'bron2/annwn-design-plan.png',bbox_inches='tight',facecolor='white');print('ok')

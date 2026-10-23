import json, glob, base64, zlib, ast, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Patch
from matplotlib.lines import Line2D
from matplotlib.path import Path
D = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
T = json.load(open('/home/claude/pdc-design-map/map/sites/nac/terrain.json'))
lot = np.array(T['lot']).reshape(-1, 2)
d1 = T['meta']['dem1']; d1 = ast.literal_eval(d1) if isinstance(d1, str) else d1
A = np.frombuffer(zlib.decompress(base64.b64decode(d1['b64'])), np.uint16).reshape(d1['h'], d1['w']).astype(float) / 10
from scipy.ndimage import gaussian_filter
A = gaussian_filter(A, 3)
F = [json.load(open(f)) for f in sorted(glob.glob(D + 'nac_db/nac_features/*.json'))]; F = [f.get('data', f) for f in F]
X = lambda p: (p[0], -p[1])
fig, ax = plt.subplots(figsize=(11, 5.6), dpi=170)
# root zone (5 m) around gums and ironbark, clipped to lot
gx, gy = np.meshgrid(np.arange(960, 1036, .2), np.arange(984, 1016, .2))
P = np.c_[gx.ravel(), gy.ravel()]; ins = Path(lot).contains_points(P).reshape(gx.shape)
trees = np.array([f['geom']['pts'][0] for f in F if f['kind'] == 'nativetree'])
dmin = np.min(np.hypot(gx[..., None] - trees[:, 0], gy[..., None] - trees[:, 1]), axis=2)
root = np.where(ins & (dmin < 5), 1.0, np.nan)
ax.add_patch(Polygon([X(p) for p in lot], closed=True, fc='#eef3e6', ec='none'))
ax.imshow(root, extent=(960, 1036, -1016, -984), origin='upper', cmap=matplotlib.colors.ListedColormap(['#e9d7a5']), alpha=.9, interpolation='nearest', zorder=1.5)
# contours
yy, xx = np.mgrid[0:d1['h'], 0:d1['w']]
cs = ax.contour(xx + d1['x0'] + .5, -(yy + d1['y0'] + .5), A, levels=np.arange(15.5, 19.5, .5), colors='#9a8c78', linewidths=.6)
lp=Polygon([X(p) for p in lot], closed=True, transform=ax.transData)
cs.set_clip_path(lp)
ax.clabel(cs, fmt='%.1f m', fontsize=5.5, inline=True)
ax.add_patch(Polygon([X(p) for p in lot], closed=True, fill=False, ec='#444', lw=1.5))
col = {'building': '#b9b1a6', 'shed': '#c9c1b6', 'carport': '#d8d2c9', 'solar': '#5b6f8a', 'driveway': '#dcd6cc', 'zone1': '#cfe5b4', 'raisedbed': '#b07a2a', 'herbs': '#7fb069', 'bed': '#c8b89a'}
for f in sorted(F, key=lambda f: {'driveway': 0, 'zone1': 1}.get(f['kind'], 2)):
    g = f['geom']; pts = [X(p) for p in g['pts']]; k = f['kind']
    if g['g'] == 'polygon':
        ax.add_patch(Polygon(pts, closed=True, fc=col.get(k, '#ccc'), ec='#6d655c', lw=.6, alpha=.9 if k != 'zone1' else .6, zorder=3 if k != 'zone1' else 2))
    elif g['g'] == 'line': ax.plot(*zip(*pts), color='#8a7a6a', lw=1.4, ls=(0, (2, 1)), zorder=4)
    elif k == 'nativetree':
        ax.add_patch(plt.Circle(pts[0], 1.6 if 'Ironbark' in f['name'] else 1.1, fc='#55704b', ec='white', lw=.6, zorder=5))
    elif k == 'fruittree': ax.add_patch(plt.Circle(pts[0], .8, fc='#e08a1e', ec='white', lw=.6, zorder=6))
    elif k == 'tank': ax.add_patch(plt.Circle(pts[0], 1.8 if '30' in f['name'] else .7, fc='#3a8fd6', ec='#1d5b91', lw=.8, zorder=6))
    elif k == 'structure': ax.add_patch(plt.Circle(pts[0], .5, fc='white', ec='#7a3b9a', lw=1.2, zorder=6))
    else: ax.add_patch(plt.Circle(pts[0], .5, fc='#9cc27a', ec='white', lw=.4, zorder=5))
lab = lambda x, y, s, **k: ax.text(x, -y, s, fontsize=k.pop('fs', 7), zorder=9, **k)
lab(1004.5, 1003.5, 'House', ha='center', va='center', fs=9, weight='bold', color='#3d362f')
lab(988.8, 993.0, 'Garage', ha='center', fs=6.5); lab(975, 990.4, 'Driveway', ha='center', fs=6.5, color='#6d655c')
lab(997.3, 990.6, 'Tanks 30 kL + 5 kL', ha='center', fs=6.5, color='#1d5b91')
lab(1010.4, 994.3, 'Raised beds', ha='center', fs=6.5, color='#7a5418')
lab(1000.5, 1009.2, 'Herbs (shade)', ha='center', fs=6.5, color='#3e6b2b')
lab(1019.2, 995.6, 'Fruit trees', ha='center', fs=6.5, color='#a35400')
lab(1025.7, 996.3, 'Ironbark', ha='center', fs=6.5, color='#33472d')
lab(977, 999.0, 'Gums & small natives', ha='center', fs=6.5, color='#33472d')
ax.annotate('', xy=(1031, -987.5), xytext=(1031, -992.5), arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.1)); ax.text(1031, -986.8, 'N', ha='center', fontsize=9, weight='bold')
ax.annotate('falls north', xy=(1013, -1000.5), xytext=(1013, -1006.0), zorder=9, fontsize=6, ha='center', color='#6d655c', arrowprops=dict(arrowstyle='->', color='#9a8c78', lw=.8))
ax.plot([962, 972], [-1015, -1015], color='#333', lw=2); ax.text(967, -1014.4, '10 m', ha='center', fontsize=7)
ax.set_xlim(961, 1036); ax.set_ylim(-1016.5, -984); ax.set_aspect('equal'); ax.axis('off')
h = [Patch(fc='#e9d7a5', label='Within 5 m of a gum: root competition'), Patch(fc='#cfe5b4', alpha=.6, label='Zone 1 kitchen garden'),
     Line2D([], [], color='#9a8c78', lw=.8, label='Contour, 0.5 m (smoothed 5 m data)'), Line2D([], [], marker='o', ls='', mfc='#e08a1e', mec='white', ms=7, label='Fruit tree (Ange\'s plan)'),
     Line2D([], [], marker='o', ls='', mfc='#55704b', mec='white', ms=7, label='Gum / ironbark'), Line2D([], [], marker='o', ls='', mfc='#3a8fd6', mec='#1d5b91', ms=7, label='Tank')]
ax.legend(handles=h, loc='upper center', bbox_to_anchor=(.5, -.01), ncol=3, fontsize=6.8, frameon=False)
ax.set_title('NAC: Ange\'s plan on the land', loc='left', fontsize=12.5, weight='bold', pad=14)
ax.text(0, 1.0, 'Positions from Ange\'s sketch, about ±1–2 m. The shaded band shows where eucalypt roots will compete with beds and fruit trees.', transform=ax.transAxes, fontsize=7, color='#555', va='bottom')
fig.savefig('/home/claude/annwn-out/nac-site-plan.png', bbox_inches='tight', facecolor='white'); print('ok')

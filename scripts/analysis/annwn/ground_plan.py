"""Annwn: how the ground falls. 0.25 m contours from the 1 m Queensland LiDAR over the lot, with the house and sheds,
the high and low points, and arrows showing where rain runs. Writes annwn-ground-plan.png next to the sewer plan.
usage: python3 ground_plan.py"""
import json, glob, math, numpy as np, tifffile, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import Polygon, Patch
from matplotlib.lines import Line2D
from scipy.ndimage import gaussian_filter

D = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
SD = '/mnt/user-data/uploads/Claude Access--Permiculture Noosa PDC/Annwn/Site data/'
T = json.load(open('/home/claude/pdc-design-map/map/sites/annwn/terrain.json'))
lot = np.array(T['lot'], float).reshape(-1, 2)
F = [json.load(open(f)) for f in sorted(glob.glob(D + 'annwn_db/annwn_features/*.json'))]
F = [f.get('data', f) for f in F]
X = lambda p: (p[0], -p[1])   # map y grows southward; flip so north is up

z = tifffile.imread(SD + 'dem_DEM_TimeSeries_AllUsers.tif').astype(float)   # 1 m cells, row 0 at the north edge of the 2 km window
x0, x1, y0, y1 = 976, 1018, 970, 1022
zz = gaussian_filter(z[y0:y1, x0:x1], 0.7)
xs = np.arange(x0, x1) + .5; ys = np.arange(y0, y1) + .5; gx, gy = np.meshgrid(xs, ys)
inside = Path(lot).contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
zl = np.where(inside, z[y0:y1, x0:x1], np.nan)
lo = np.unravel_index(np.nanargmin(zl), zl.shape); hi = np.unravel_index(np.nanargmax(zl), zl.shape)
zmin, zmax = float(np.nanmin(zl)), float(np.nanmax(zl))
# steepest-descent paths from a few points inside the lot
def descend(x, y, n=40):
    p = [(x, y)]
    for _ in range(n):
        best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == dy == 0: continue
                v = z[int(y + dy), int(x + dx)]
                if best is None or v < best[0]: best = (v, x + dx, y + dy)
        if best[0] >= z[int(y), int(x)]: break
        x, y = best[1], best[2]; p.append((x, y))
    return p

fig, ax = plt.subplots(figsize=(8.3, 9.6), dpi=170)
lv = np.arange(math.floor(zmin * 4) / 4 - .5, zmax + .75, .25)
cf = ax.contourf(gx, -gy, zz, levels=np.arange(20.4, 22.9, .1), cmap='YlGn_r', alpha=.55)
cs = ax.contour(gx, -gy, zz, levels=lv, colors='#6b4b2a', linewidths=[1.4 if abs(l * 2 - round(l * 2)) < 1e-6 else .6 for l in lv])
ax.clabel(cs, levels=[l for l in lv if abs(l * 2 - round(l * 2)) < 1e-6], fmt='%.1f m', fontsize=6.5, inline=True)
ax.add_patch(Polygon([X(p) for p in lot], closed=True, fill=False, ec='#444', lw=1.8, zorder=4))
col = {'building': '#b9b1a6', 'shed': '#c9c1b6'}
for f in F:
    g = f['geom']; pts = [X(p) for p in g['pts']]; k = f['kind']
    if g['g'] == 'polygon' and k in col: ax.add_patch(Polygon(pts, closed=True, fc=col[k], ec='#6d655c', lw=1, zorder=5))
ax.text(993, -997, 'House', ha='center', va='center', fontsize=10, color='#3d362f', weight='bold', zorder=9)
ax.text(998.6, -984.6, 'Main\nshed', ha='center', va='center', fontsize=8, color='#3d362f', zorder=9)
ax.text(990.6, -987.1, 'Small\nshed', ha='center', va='center', fontsize=6, color='#3d362f', zorder=9)
for s in [(1006, 983), (1004, 1000), (990, 1008), (987, 990), (1001, 990)]:
    p = descend(*s)
    if len(p) > 2:
        ax.annotate('', xy=X(p[-1]), xytext=X(p[0]), arrowprops=dict(arrowstyle='-|>', color='#1d5b91', lw=1.6, shrinkA=0, shrinkB=0, connectionstyle='arc3,rad=0.08'), zorder=8)
ax.scatter(*X((gx[hi], gy[hi])), marker='^', s=90, c='#c0392b', zorder=10, ec='white'); ax.text(gx[hi] + .8, -gy[hi], f'high {zmax:.1f} m', fontsize=7.5, color='#c0392b', va='center', zorder=10)
ax.scatter(*X((gx[lo], gy[lo])), marker='v', s=90, c='#1d5b91', zorder=10, ec='white'); ax.text(gx[lo] - .8, -gy[lo] - .9, f'low {zmin:.1f} m', fontsize=7.5, color='#1d5b91', ha='right', zorder=10)
ax.text(1012, -1000, 'Street', rotation=90, ha='center', va='center', fontsize=8, color='#777')
ax.text(994, -1019, 'Street', ha='center', va='center', fontsize=8, color='#777')
ax.set_xlim(977, 1017); ax.set_ylim(-1021, -971); ax.set_aspect('equal'); ax.axis('off')
h = [Line2D([], [], color='#6b4b2a', lw=1.4, label='Contours every 0.5 m (thin: 0.25 m)'), Line2D([], [], color='#1d5b91', lw=1.6, label='Where rain runs'),
     Line2D([], [], marker='^', color='w', markerfacecolor='#c0392b', markersize=9, label='Highest ground'), Line2D([], [], marker='v', color='w', markerfacecolor='#1d5b91', markersize=9, label='Lowest corner')]
ax.legend(handles=h, loc='lower center', bbox_to_anchor=(.5, -.1), ncol=2, fontsize=7.2, frameon=False)
ax.set_title('Annwn: how the ground falls', fontsize=13, loc='left', weight='bold', color='#222', pad=16)
ax.text(0, 1.0, f'1 m Queensland Government LiDAR. The block falls about {zmax - zmin:.1f} m from the house pad to the back north-east corner.', fontsize=7.5, color='#555', transform=ax.transAxes, va='bottom')
ax.annotate('', xy=(1015.5, -973), xytext=(1015.5, -976.5), arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.2)); ax.text(1015.5, -972.6, 'N', ha='center', fontsize=9, weight='bold')
ax.plot([979, 984], [-1020.3, -1020.3], color='#333', lw=2); ax.text(981.5, -1019.9, '5 m', ha='center', fontsize=7)
fig.savefig(D + 'bron/annwn-ground-plan.png', bbox_inches='tight', facecolor='white')
json.dump({'zmin': round(zmin, 2), 'zmax': round(zmax, 2), 'low': [float(gx[lo]), float(gy[lo])], 'high': [float(gx[hi]), float(gy[hi])]}, open(D + 'bron/ground.json', 'w'))
print('ok', round(zmin, 2), round(zmax, 2))

import json, glob, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import Polygon, Rectangle, FancyBboxPatch
from matplotlib.colors import ListedColormap

D = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
T = json.load(open('/home/claude/pdc-design-map/map/sites/annwn/terrain.json'))
lot = np.array(T['lot'], float).reshape(-1, 2)
F = [json.load(open(f)) for f in sorted(glob.glob(D + 'annwn_db/annwn_features/*.json'))]
F = [f.get('data', f) for f in F]
X = lambda p: (p[0], -p[1])          # north up

# assumed sewer: ~1 m inside the back (north) fence, then to the round feature in the NE corner (inspection opening?)
a, b = np.array([988.6, 976.9]), np.array([1010.2, 980.3])
u = (b - a) / np.linalg.norm(b - a); n = np.array([-u[1], u[0]])
if n[1] < 0: n = -n
sew = [a + n * 1.0 + u * 0.8, b + n * 1.0 - u * 2.6, np.array([1007.5, 987.3])]
def segd(P, A, B):
    AB = B - A; t = np.clip(((P - A) @ AB) / (AB @ AB), 0, 1); return np.linalg.norm(P - (A + t[:, None] * AB), axis=1)
xs = np.arange(980, 1014, .1); ys = np.arange(974, 1018, .1)
gx, gy = np.meshgrid(xs, ys); P = np.c_[gx.ravel(), gy.ravel()]
d = np.minimum.reduce([segd(P, sew[i], sew[i + 1]) for i in range(len(sew) - 1)]).reshape(gx.shape)
inside = Path(lot).contains_points(P).reshape(gx.shape)
band = np.full(gx.shape, np.nan); band[inside & (d < 2)] = 0; band[inside & (d >= 2) & (d < 5)] = 1; band[inside & (d >= 5)] = 2

fig, ax = plt.subplots(figsize=(8.3, 9.6), dpi=170)
ax.imshow(band, extent=(xs[0], xs[-1], -ys[-1], -ys[0]), origin='upper', cmap=ListedColormap(['#e8a7a0', '#f3d58a', '#cfe5b4']), vmin=0, vmax=2, alpha=.85, interpolation='nearest')
ax.add_patch(Polygon([X(p) for p in lot], closed=True, fill=False, ec='#444', lw=1.6))
col = {'building': '#b9b1a6', 'shed': '#c9c1b6'}
for f in F:
    g = f['geom']; pts = [X(p) for p in g['pts']]; k = f['kind']
    if g['g'] == 'polygon':
        if k in col: ax.add_patch(Polygon(pts, closed=True, fc=col[k], ec='#6d655c', lw=1))
        else: ax.add_patch(Polygon(pts, closed=True, fc='#b07a2a', ec='#7a5418', lw=.8, alpha=.8))
    elif g['g'] == 'line': ax.plot(*zip(*pts), color='#3b7a3a', lw=4, solid_capstyle='round')
    elif k in ('fruittree', 'tree'):
        c = '#2f7d32' if k == 'fruittree' else ('#b23a2e' if 'Callistemon' in f['name'] else '#55704b')
        ax.add_patch(plt.Circle(pts[0], .7, fc=c, ec='white', lw=.8, zorder=5))
    elif k == 'structure':
        ax.add_patch(plt.Circle(pts[0], .55, fc='white', ec='#7a3b9a', lw=1.6, zorder=6))
    else: ax.add_patch(plt.Circle(pts[0], .35, fc='#7aa35a', ec='white', lw=.5, zorder=5))
ax.plot(*zip(*[X(p) for p in sew]), color='#7a3b9a', lw=2.2, ls=(0, (5, 3)), zorder=4)

lab = lambda x, y, s, **k: ax.text(x, -y, s, fontsize=k.pop('fs', 7.5), zorder=9, **k)
lab(993, 997, 'House', ha='center', va='center', fs=10, color='#3d362f', weight='bold')
lab(998.6, 984.6, 'Main\nshed', ha='center', va='center', fs=8, color='#3d362f')
lab(990.6, 987.1, 'Small\nshed', ha='center', va='center', fs=6, color='#3d362f')
lab(1003.2, 981.4, 'Sewer? (from sketch)', ha='center', fs=7, color='#5d2a78', style='italic')
lab(1006.6, 986.2, 'Inspection\nopening?', ha='right', va='center', fs=6.5, color='#5d2a78')
lab(1003.2, 989.3, 'Bottlebrush\n(check)', ha='left', va='bottom', fs=6.5, color='#8c2a20')
lab(1005.2, 995.5, 'Citrus &\njaboticaba', ha='left', va='center', fs=6.5, color='#1f5a22')
lab(984.4, 997.5, 'Camellias', rotation=86, ha='center', va='center', fs=6.5, color='#1f5a22')
lab(992.0, 1008.2, 'Front garden', ha='center', fs=7, color='#4a4a4a')
# trellis on shed W and N walls
for (p, q) in [((995.0, 987.6), (995.0, 981.4)), ((995.5, 980.9), (1001.8, 981.2))]:
    ax.plot([p[0], q[0]], [-p[1], -q[1]], color='#e07b00', lw=3.2, zorder=7)
lab(994.6, 982.6, 'Vine trellis\n(passionfruit\n+ kiwi)', ha='right', va='center', fs=6.5, color='#a35400')
# candidate tank spots
for (x0, y0, w, h, t) in [(1001.9, 982.3, .7, 2.4, 'A'), (997.75, 991.0, .7, 2.4, 'B')]:
    ax.add_patch(Rectangle((x0, -(y0 + h)), w, h, fc='#3a8fd6', ec='#1d5b91', lw=1, zorder=8))
    lab(x0 + w + .25, y0 + h / 2, t, va='center', fs=8, color='#1d5b91', weight='bold')
lab(997.9, 993.9, 'New 5,000 L\nslimline:\nspot A or B', ha='left', va='top', fs=6.5, color='#1d5b91')

ax.set_xlim(980.5, 1013.5); ax.set_ylim(-1017, -974.5); ax.set_aspect('equal'); ax.axis('off')
# legend
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
h = [Patch(fc='#e8a7a0', label='Within 2 m: herbs, veg, wicking beds, pots'), Patch(fc='#f3d58a', label='2-5 m: small shrubs and dwarf fruit under 2.5 m'),
     Patch(fc='#cfe5b4', label='5 m+: avocado, custard apple, larger fruit trees'), Line2D([], [], color='#7a3b9a', ls=(0, (5, 3)), lw=2, label='Sewer line (assumed)'),
     Patch(fc='#3a8fd6', label='Possible new tank spot'), Line2D([], [], color='#e07b00', lw=3, label='Vine trellis on shed')]
ax.legend(handles=h, loc='lower center', bbox_to_anchor=(.5, -.13), ncol=2, fontsize=7.2, frameon=False)
ax.set_title('Annwn: planting distances from the sewer', fontsize=13, loc='left', weight='bold', color='#222', pad=16)
ax.text(0, 1.0, 'Bands assume the sewer follows the dashed line on Bronwen\'s sketch. Confirm the real line before planting trees.', fontsize=7.5, color='#555', transform=ax.transAxes, va='bottom')
# north arrow + scale
ax.annotate('', xy=(1012, -976), xytext=(1012, -979.5), arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.2))
ax.text(1012, -975.6, 'N', ha='center', fontsize=9, weight='bold')
ax.plot([982, 987], [-1016.3, -1016.3], color='#333', lw=2); ax.text(984.5, -1015.9, '5 m', ha='center', fontsize=7)
fig.savefig(D + 'bron/annwn-sewer-plan.png', bbox_inches='tight', facecolor='white')
print('ok')

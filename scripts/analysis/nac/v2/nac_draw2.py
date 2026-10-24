"""Shared drawing of Ange's updated plan (feats2.json) for the NAC PDFs. Map coordinates: x east, y south (metres from the map window origin)."""
import json, os, math, base64, zlib, ast, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Patch, Circle, Wedge, Arc
from matplotlib.lines import Line2D
import matplotlib.patheffects
from matplotlib.path import Path
from scipy.ndimage import gaussian_filter
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, '../../../../map/sites/nac')
T = json.load(open(os.path.join(SITE, 'terrain.json')))
LOT = np.array(T['lot']).reshape(-1, 2)
F = json.load(open(os.path.join(HERE, 'feats2.json')))
d1 = T['meta']['dem1']; d1 = ast.literal_eval(d1) if isinstance(d1, str) else d1
DEM = gaussian_filter(np.frombuffer(zlib.decompress(base64.b64decode(d1['b64'])), np.uint16).reshape(d1['h'], d1['w']).astype(float) / 10, 3)
X = lambda p: (p[0], -p[1])
ZCOL = {'zone1': '#9fcf7a', 'zone2': '#cfe3a8', 'zone3': '#dfe8cf', 'zone4': '#cfd9c3'}
FILL = {'building': '#b9b1a6', 'shed': '#c9c1b6', 'carport': '#d8d2c9', 'solar': '#4f6480', 'driveway': '#dcd6cc', 'raisedbed': '#b07a2a',
        'herbs': '#7fb069', 'bed': '#c8b89a', 'lawn': '#cfe4a6', 'pond': '#8fc3e8'}
ORDER = {'driveway': 0, 'zone4': 1, 'zone3': 1, 'zone2': 1.2, 'zone1': 1.4, 'lawn': 1.6}
IDEA = ('idea', 'proposed')

def tree_r(f):
    n = f['name'].lower(); k = f['kind']
    if k == 'nativetree': return 2.0 if any(s in n for s in ('ironbark', 'mahogany', 'tallowwood', 'grey gum')) else 1.3
    return f['geom'].get('r', 0.7)

def draw(ax, base=None, zones=True, contours=True, roots=False, labels=True, sectors=False, idea_labels=True, zone_labels=True, lw_scale=1.0):
    """base = (image, extent_in_map_coords) drawn under everything."""
    if base is not None:
        im, (x0, x1, y0, y1) = base; ax.imshow(im, extent=(x0, x1, -y1, -y0), zorder=0, interpolation='bilinear')
    lotp = Polygon([X(p) for p in LOT], closed=True, transform=ax.transData)
    if base is None: ax.add_patch(Polygon([X(p) for p in LOT], closed=True, fc='#f1f3ea', ec='none', zorder=0))
    feats = sorted(F.items(), key=lambda kv: ORDER.get(kv[1]['kind'], 3))
    for fid, f in feats:
        g = f['geom']; k = f['kind']; idea = f['status'] in IDEA
        if g['g'] == 'polygon':
            pts = [X(p) for p in g['pts']]
            if k.startswith('zone'):
                if not zones: continue
                ax.add_patch(Polygon(pts, closed=True, fc=ZCOL[k], ec='#6b7a5a', lw=.5 * lw_scale, alpha=.45 if base is None else .35, zorder=ORDER.get(k, 2)))
            else:
                ax.add_patch(Polygon(pts, closed=True, fc=FILL.get(k, '#ccc'), ec='#6d655c', lw=.6 * lw_scale, ls='--' if idea else '-', alpha=.55 if idea else .92, zorder=ORDER.get(k, 3)))
        elif g['g'] == 'line':
            pts = np.array(g['pts']); xs, ys = pts[:, 0], -pts[:, 1]
            st = {'path': dict(color='#8a7a6a', lw=1.4, ls=(0, (2, 1))), 'steps': dict(color='#6d655c', lw=2.2), 'swale': dict(color='#2f6fb3', lw=2.6, ls=(0, (3, 1.5))),
                  'pipe': dict(color='#6a8fa8', lw=1.3, ls=(0, (1, 1))), 'sewer': dict(color='#8b5e3c', lw=1.3, ls=(0, (4, 2))), 'flow': dict(color='#3a8fd6', lw=1.2)}.get(k, dict(color='#888', lw=1))
            st['lw'] *= lw_scale; ax.plot(xs, ys, zorder=4, **st)
            if k == 'flow': ax.annotate('', xy=(xs[-1], ys[-1]), xytext=(xs[-2], ys[-2]), arrowprops=dict(arrowstyle='-|>', color='#3a8fd6', lw=1.2 * lw_scale), zorder=4)
        elif g['g'] == 'point':
            x, y = X(g['pts'][0])
            if k == 'nativetree': ax.add_patch(Circle((x, y), tree_r(f), fc='#4f6b45', ec='white', lw=.5 * lw_scale, zorder=5))
            elif k == 'shrub': ax.add_patch(Circle((x, y), .55 if 'gum' not in f['name'].lower() else .9, fc='#8fb07a', ec='white', lw=.4 * lw_scale, zorder=5))
            elif k == 'fruittree': ax.add_patch(Circle((x, y), .9, fc='#e08a1e', ec='white', lw=.5 * lw_scale, zorder=6))
            elif k == 'tank': ax.add_patch(Circle((x, y), 1.8 if '30' in f['name'] else .8, fc='#3a8fd6', ec='#1d5b91', lw=.8 * lw_scale, zorder=6))
            elif k == 'structure': ax.add_patch(Circle((x, y), .6, fc='white', ec='#7a3b9a', lw=1.2 * lw_scale, ls='--' if idea else '-', zorder=6))
            elif k == 'compost': ax.add_patch(plt.Rectangle((x - .7, y - .5), 1.4, 1.0, fc='#6b4f2a', ec='white', lw=.5 * lw_scale, zorder=6))
            elif k == 'herbspiral':
                th = np.linspace(0, 4 * math.pi, 80); ax.plot(x + .15 * th * np.cos(th) * .7, y + .15 * th * np.sin(th) * .7, color='#3e6b2b', lw=1.2 * lw_scale, zorder=6)
            elif k == 'guild': ax.add_patch(Circle((x, y), 2.6, fc='#f6d77a', ec='#a35400', lw=1.1 * lw_scale, ls='--', alpha=.55, zorder=4.5))
            elif k == 'soak': ax.add_patch(plt.Rectangle((x - .6, y - .6), 1.2, 1.2, fc='#8fc3e8', ec='#1d5b91', lw=.7 * lw_scale, zorder=6))
            elif k == 'gathering': ax.add_patch(Circle((x, y), 1.0, fc='#f3c1a0', ec='#c0392b', lw=1.1 * lw_scale, ls='--', zorder=6))
            else: ax.add_patch(Circle((x, y), .5, fc='#9cc27a', ec='white', lw=.4 * lw_scale, zorder=5))
        elif g['g'] == 'sector' and sectors:
            c = {'fire': '#e05a2b', 'wind': '#4f8fc9', 'view': '#7a3b9a'}.get(k, '#888')
            ax.add_patch(Wedge((g['cx'], -g['cy']), g['r'], 90 - g['a1'], 90 - g['a0'], fc=c, ec=c, lw=1, alpha=.22, zorder=1.8))
        elif g['g'] == 'sun' and sectors:
            # summer and winter sun arcs at 32.7° S: rise/set azimuths about 117°/243° (summer) and 63°/297°... drawn as arrows of the sun's sweep
            for az0, az1, rr, c in [(117, 243, .92, '#e9a820'), (63, 297, .82, '#c0392b')]:   # (rise azimuth, set azimuth): summer is the wider arc, north side
                ax.add_patch(Arc((g['cx'], -g['cy']), 2 * g['r'] * rr, 2 * g['r'] * rr, theta1=90 - az0, theta2=90 - az1 + 360, ec=c, lw=2.2, zorder=1.9))
    if contours:
        yy, xx = np.mgrid[0:d1['h'], 0:d1['w']]
        cs = ax.contour(xx + d1['x0'] + .5, -(yy + d1['y0'] + .5), DEM, levels=np.arange(15.0, 20.0, .5), colors='#9a8c78' if base is None else '#fff7d6', linewidths=.6 * lw_scale, zorder=2.5)
        cs.set_clip_path(lotp); ax.clabel(cs, fmt='%.1f m', fontsize=5.5, inline=True)
    if roots:
        gx, gy = np.meshgrid(np.arange(960, 1036, .2), np.arange(984, 1016, .2))
        P = np.c_[gx.ravel(), gy.ravel()]; ins = Path(LOT).contains_points(P).reshape(gx.shape)
        trees = np.array([f['geom']['pts'][0] for f in F.values() if f['kind'] == 'nativetree'])
        dmin = np.min(np.hypot(gx[..., None] - trees[:, 0], gy[..., None] - trees[:, 1]), axis=2)
        ax.imshow(np.where(ins & (dmin < 5), 1.0, np.nan), extent=(960, 1036, -1016, -984), origin='upper', cmap=matplotlib.colors.ListedColormap(['#e9d7a5']), alpha=.6, interpolation='nearest', zorder=1.7)
    ax.add_patch(Polygon([X(p) for p in LOT], closed=True, fill=False, ec='#222' if base is None else '#ffe34d', lw=1.6 * lw_scale, zorder=7))
    if labels:
        dark = base is not None
        def lab(x, y, s, fs=6.5, color='#3d362f', **k):
            ax.text(x, -y, s, fontsize=fs, zorder=9, ha='center', color=color if not dark else 'white',
                    path_effects=[matplotlib.patheffects.withStroke(linewidth=2, foreground='black')] if dark else None, **k)
        lab(1008.5, 1000.6, 'House', fs=9, weight='bold'); lab(988.5, 989.3, 'Garage'); lab(976, 987.2, 'Driveway', color='#6d655c')
        lab(995.8, 988.6, '30 kL', color='#1d5b91'); lab(992.9, 989.4, '5 kL', color='#1d5b91', fs=5.5)
        lab(1009.5, 990.0, 'Raised vegie beds', color='#7a5418'); lab(1007.5, 1008.9, 'Herb bed', color='#3e6b2b', fs=6)
        lab(1021.5, 997.5, 'Fruit trees', color='#a35400'); lab(1027.0, 998.8, 'Rock garden', color='#6d655c', fs=5.5)
        lab(996.3, 998.4, 'Lawn', color='#4f7a2b'); lab(979.5, 996.6, 'Ironbarks, tallowwoods,\nflowering natives', color='#33472d', fs=6)
        lab(1021.0, 1011.0, 'Gum cluster', color='#33472d', fs=6); lab(1004.5, 1011.5, 'Swale drain and berm', color='#2f6fb3', fs=5.5)
        if zone_labels:
            for fid, f in F.items():
                if f['kind'].startswith('zone') and f['kind'] != 'zone1':
                    pts = np.array(f['geom']['pts']); cx, cy = pts.mean(0); lab(cx, cy, f['name'].split('·')[0].strip(), fs=6.5, color='#4a5a3a', style='italic', alpha=.9)
            for fid, f in F.items():
                if f['kind'] == 'nativetree' and f['name'][:2].isdigit():
                    x, y = f['geom']['pts'][0]; ax.text(x, -y, f['name'][:2], fontsize=5, color='white', ha='center', va='center', zorder=9, weight='bold')
        if idea_labels:
            for fid, f in F.items():
                if f['status'] in IDEA and f['geom']['g'] in ('point', 'polygon'):
                    pts = np.array(f['geom']['pts']); cx, cy = pts.mean(0)
                    nm = f['name'].split('(')[0].strip()
                    if 'Verge break' in nm: nm = 'verge break' if 'break 1' in f['name'] else ''
                    if nm: lab(cx, cy - 1.7, nm, fs=5.5, color='#a35400', style='italic')
    ax.set_aspect('equal'); ax.axis('off')

def north_scale(ax, x=1031, y=987, sx=962, sy=1015.3):
    ax.annotate('', xy=(x, -y - .5), xytext=(x, -y - 5.5), arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.1)); ax.text(x, -y + .2, 'N', ha='center', fontsize=9, weight='bold')
    ax.plot([sx, sx + 10], [-sy, -sy], color='#333', lw=2); ax.text(sx + 5, -sy + .6, '10 m', ha='center', fontsize=7)

def legend_handles(base=False):
    return [Patch(fc=ZCOL['zone1'], alpha=.6, label='Zone 1 (daily: vegies, herbs)'), Patch(fc=ZCOL['zone2'], alpha=.7, label='Zone 2 (fruit, guilds)'),
            Patch(fc=ZCOL['zone3'], alpha=.9, label='Zone 3 (natives, rock garden)'), Patch(fc=ZCOL['zone4'], alpha=.9, label='Zone 4 (gum pockets, kept wild)'),
            Line2D([], [], marker='o', ls='', mfc='#e08a1e', mec='white', ms=7, label='Fruit tree'), Line2D([], [], marker='o', ls='', mfc='#4f6b45', mec='white', ms=8, label='Gum / ironbark (numbered on the plan)'),
            Line2D([], [], marker='o', ls='', mfc='#8fb07a', mec='white', ms=5, label='Flowering native / small gum'), Line2D([], [], marker='o', ls='', mfc='#3a8fd6', mec='#1d5b91', ms=7, label='Tank'),
            Line2D([], [], color='#2f6fb3', lw=2.4, ls=(0, (3, 1.5)), label='Swale drain and berm'), Line2D([], [], marker='s', ls='', mfc='#8fc3e8', mec='#1d5b91', ms=6, label='Verge break (soak)'),
            Line2D([], [], color='#3a8fd6', lw=1.2, label='Surface water flow'), Line2D([], [], color='#6a8fa8', lw=1.3, ls=(0, (1, 1)), label='Greywater / overflow pipe'),
            Patch(fc='#f6d77a', ec='#a35400', ls='--', alpha=.6, label='Guild (idea)'), Line2D([], [], marker='o', ls='', mfc='#f3c1a0', mec='#c0392b', ms=7, label='Fire pit (idea)'),
            Patch(fc='#8fc3e8', ec='#6d655c', ls='--', alpha=.6, label='Pond (idea, place to choose)'), Line2D([], [], color='#9a8c78', lw=.8, label='Contour 0.5 m (smoothed 5 m data)')]

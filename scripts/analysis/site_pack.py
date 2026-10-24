#!/usr/bin/env python3
"""Design graphics pack for any design-map site: one A4-landscape PDF, one graphic per page.

usage: python3 scripts/analysis/site_pack.py <site-id> <features-dir> <out.pdf>
  site-id       as in SITES in map/index.html (its terrain.json, hydro.json, veg.json are read)
  features-dir  folder of the site's feature JSON files (an ArtifactData list with out_dir)
Pages: at a glance · design plan · rain · night temperatures · slope share · low-to-high profile · sun ·
water and erosion · forest structure (if LiDAR canopy) · design inventory · twelve principles (from PACK_TEXT).
Privacy: first names only, no addresses; the plan uses the hillshade, not the aerial photo.
"""
import ast, base64, glob, json, math, os, re, sys, textwrap, zlib
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Polygon, Circle
from matplotlib.path import Path as MPath
from scipy.ndimage import gaussian_filter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'map')
GREY, ACC, INK, SUB = '#b8b8b2', '#2f6fb3', '#222', '#666'
A4 = (11.69, 8.27)
M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
PAL = ['#e6efc4', '#f9d3c4', '#e3efc9', '#f3d6e2', '#f8efb8', '#d7ecd6', '#e6dcf1', '#d9def3', '#f8e1b8', '#f6cfcf', '#fbd9bf', '#d3e7ef']
PRINCIPLES = ['Observe & interact', 'Use small & slow solutions', 'Catch & store energy', 'Design from patterns to details',
              'Creatively use & respond to change', 'Obtain a yield', 'Produce no waste', 'Use & value renewable resources',
              'Use edges & value the marginal', 'Integrate rather than segregate', 'Use & value diversity', 'Apply self-regulation & accept feedback']
PACK_TEXT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pack_text.json')))


def dec(v):
    v = ast.literal_eval(v) if isinstance(v, str) else v
    a = np.frombuffer(zlib.decompress(base64.b64decode(v['b64'])), np.uint16).reshape(v['h'], v['w']).astype(float) / 10
    return v, a


def tank_test(DL, lat, roof=200.0, store=20000.0, house=300.0, garden=0.0):
    """The design map's tank simulation (tkSim in index.html), day by day over the SILO record.
    Rain tops the tank up from the roof (85% collected); the house draws its daily use; a 25 mm soil store is
    watered only when it runs down. Returns the share of demand met, the share of days with water in the tank,
    the longest empty run and when it ended, and the annual rain totals."""
    import datetime
    E = [6.0, 5.3, 4.6, 3.6, 2.8, 2.4, 2.6, 3.5, 4.6, 5.4, 5.9, 6.3] if lat > -29.5 else [5.3, 4.6, 3.8, 2.8, 2.0, 1.6, 1.8, 2.5, 3.4, 4.3, 4.8, 5.4]   # mm/day ETo: SE Qld, or NSW coast
    d0 = datetime.date.fromisoformat(DL['start']); r = DL['rain10']
    s, soil, sup, dem = store, 25.0, 0.0, 0.0; annual = {}; days_with = 0; run = 0; longest = 0; longest_when = ''
    for i, r10 in enumerate(r):
        dt = d0 + datetime.timedelta(days=i); rain = r10 / 10; m = dt.month - 1
        s = min(store, s + rain * roof * .85)
        et = E[m] * .6; soil = min(25.0, soil + rain) - et; need = -soil if soil < 0 else 0.0; soil = max(soil, 0.0)
        want = need * garden + house; take = min(s, want); s -= take; sup += take; dem += want
        annual[dt.year] = annual.get(dt.year, 0.0) + rain
        if s > 1: days_with += 1; run = 0
        else:
            run += 1
            if run > longest: longest, longest_when = run, dt.strftime('%b %Y')
    return dict(share=sup / dem if dem else 1.0, days_with=days_with / len(r), longest=longest, longest_when=longest_when, annual=annual, roof=roof, store=store, house=house)


def kinds():
    s = open(os.path.join(ROOT, 'index.html')).read()
    out = {}
    for k, g, lab, geom, col in re.findall(r"  ([a-z0-9]+):\{g:'([A-Za-z]+)',label:'([^']*)',geom:'([a-z]+)',color:'(#[0-9a-fA-F]+)'", s):
        out[k] = dict(g=g, label=lab, geom=geom, color=col)
    sites = {m[0]: m[1] for m in re.findall(r"\{id:'([\w-]+)'[^}]*?(?:base:'([^']*)')?[^}]*\}", s)}
    return out, s


def main(site, fdir, out):
    K, html = kinds()
    m = re.search(r"\{id:'%s'([^}]*)\}" % re.escape(site), html); base = re.search(r"base:'([^']*)'", m.group(1))
    sb = os.path.join(ROOT, base.group(1) if base else f'sites/{site}/')
    T = json.load(open(os.path.join(sb, 'terrain.json'))); meta = T['meta']; S = meta['site']
    txt = PACK_TEXT[site]
    lot = np.array(T['lot']).reshape(-1, 2)
    dv, D2 = dec(meta['dem'])                       # 2 m grid over the 2 km window
    H = json.load(open(os.path.join(sb, 'hydro.json'))) if os.path.exists(os.path.join(sb, 'hydro.json')) else None
    VEG = json.load(open(os.path.join(sb, 'veg.json'))) if os.path.exists(os.path.join(sb, 'veg.json')) else None
    F = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(fdir, '*.json')))]; F = [f.get('data', f) for f in F]
    F = [f for f in F if f.get('geom') and f['kind'] in K and not f.get('hidden')]
    rain = S.get('rain') or {}
    name = txt.get('name', S['name']); foot_site = f'{name} · preliminary design · Oct 2026'
    pdf = PdfPages(out)

    def page(title, sub, foot):
        fig = plt.figure(figsize=A4)
        fig.text(.06, .93, title, fontsize=19, weight='bold', color=INK)
        fig.text(.06, .895, sub, fontsize=10.5, color=SUB)
        fig.text(.06, .035, foot, fontsize=7.5, color='#888'); fig.text(.94, .035, foot_site, fontsize=7.5, color='#888', ha='right')
        return fig

    def save(fig): pdf.savefig(fig); plt.close(fig)

    # lot statistics from the 2 m grid
    yy, xx = np.mgrid[0:1000, 0:1000]; X = xx * 2 + 1; Y = yy * 2 + 1
    ins = MPath(lot).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
    z = D2[ins]; ha = ins.sum() * 4 / 1e4
    share = {f'{a}-{b}' if b else f'{a}+': v for a, b, v in [(c[0], c[1], c[2]) for c in meta['lotSlopeShare']]}
    sl = meta['lotSlopeShare']
    under10 = sl[0][2] * 100; over50 = sl[-1][2] * 100
    ann = sum(rain['mean']) if rain.get('mean') else None
    dry = sum(rain['mean'][6:9]) / ann * 100 if ann else None

    # 1 at a glance
    fig = page(f'{name} at a glance', txt['sub'], 'Sources: ' + txt['sources'])
    tiles = [(f'{ha:.1f} ha' if ha >= 1 else f'{ha*1e4:,.0f} m²', 'design area (property boundary)'),
             (f'{z.min():.0f}–{z.max():.0f} m', 'above sea level'),
             (f'{under10:.0f}%', 'gentle ground, under 10% slope'), (f'{over50:.0f}%', 'steep ground, over 50% slope'),
             (f'{ann:,.0f} mm' if ann else 'to come', 'rain in an average year'), (f'{dry:.0f}%' if dry else '–', 'of the rain falls Jul–Sep'),
             (f"{min(rain['tmin']):.1f} °C" if rain.get('tmin') else '–', 'coldest month, mean minimum'),
             (f"{meta['sun_winter_lotmean']:.1f} h", 'midwinter sun, terrain only')]
    for i, (big, small) in enumerate(tiles):
        x = .06 + (i % 4) * .225; y = .56 - (i // 4) * .25
        fig.patches.append(FancyBboxPatch((x, y), .2, .2, boxstyle='round,pad=0.005,rounding_size=0.015', transform=fig.transFigure, fc='#f3f2ee', ec='none'))
        fig.text(x + .015, y + .11, big, fontsize=22, weight='bold', color=INK); fig.text(x + .015, y + .05, small, fontsize=9.5, color=SUB)
    fig.text(.06, .2, 'The big picture', fontsize=12, weight='bold')
    fig.text(.06, .178, '\n'.join('• ' + textwrap.fill(b, 165, subsequent_indent='  ') for b in txt['big']), fontsize=9.6, color=INK, linespacing=1.55, va='top')
    save(fig)

    # 2 design plan
    view = txt.get('view')
    if view: x0, y0, x1, y1 = view
    else:
        x0, y0 = lot.min(0) - 25; x1, y1 = lot.max(0) + 25
    fig = page(txt.get('plan_title', 'The design on the land'), txt.get('plan_sub', 'Design features from the map over the terrain, with the property boundary and 5 m contours.'),
               'Terrain: ' + S.get('source', 'LiDAR').split(',')[0] + '. Shaded relief, not the aerial photo. Positions as drawn on the design map.')
    ax = fig.add_axes([.05, .07, .66, .8])
    hs = plt.imread(os.path.join(sb, 'hillshade.jpg'))
    ax.imshow(hs, extent=(0, 2000, 2000, 0), cmap='gray', alpha=.55)
    Ds = gaussian_filter(D2, 1.2)
    step = 5 if (z.max() - z.min()) < 120 else 10
    cs = ax.contour(X, Y, Ds, levels=np.arange(math.floor(z.min() / step) * step - step, z.max() + step, step), colors='#8a6a45', linewidths=.45, alpha=.7)
    ax.add_patch(Polygon(lot, closed=True, fill=False, ec='#c2185b', lw=1.6, ls=(0, (6, 3))))
    used = {}
    order = lambda f: (0 if K[f['kind']]['geom'] == 'polygon' else 1, -len(f['geom'].get('pts') or []))
    for f in sorted(F, key=order):
        k = K[f['kind']]; g = f['geom']; c = k['color']; pts = g.get('pts') or []
        if g['g'] == 'polygon' and len(pts) > 2:
            ax.add_patch(Polygon(pts, closed=True, fc=c, ec=c, alpha=.33, lw=.8)); used[k['label']] = c
        elif g['g'] == 'line' and len(pts) > 1:
            p = np.array(pts); ax.plot(p[:, 0], p[:, 1], color=c, lw=1.8, solid_capstyle='round'); used[k['label']] = c
        elif g['g'] == 'point' and pts:
            ax.add_patch(Circle(pts[0], max(1.2, (x1 - x0) / 220), fc=c, ec='white', lw=.5, zorder=5)); used[k['label']] = c
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values(): s_.set_visible(False)
    span = x1 - x0; sb_len = 10 ** math.floor(math.log10(span / 4)); sb_len = sb_len * (5 if span / sb_len > 20 else 2 if span / sb_len > 8 else 1)
    ax.plot([x0 + span * .04, x0 + span * .04 + sb_len], [y1 - (y1 - y0) * .04] * 2, color='#222', lw=2.2); ax.text(x0 + span * .04 + sb_len / 2, y1 - (y1 - y0) * .055, f'{sb_len:g} m', ha='center', fontsize=8)
    ax.annotate('N', xy=(x1 - span * .04, y0 + (y1 - y0) * .05), xytext=(x1 - span * .04, y0 + (y1 - y0) * .13), ha='center', fontsize=10, weight='bold', arrowprops=dict(arrowstyle='-|>', color='#222'))
    lg = fig.add_axes([.73, .1, .24, .76]); lg.axis('off')
    items = sorted(used.items())[:30]
    for i, (lab, c) in enumerate(items):
        lg.add_patch(FancyBboxPatch((0, 1 - (i + 1) * .032), .06, .02, boxstyle='round,pad=0.002', fc=c, ec='none', alpha=.8, transform=lg.transAxes))
        lg.text(.09, 1 - (i + 1) * .032 + .01, textwrap.shorten(lab, 38), fontsize=7.6, va='center', transform=lg.transAxes)
    lg.text(0, 1 - (len(items) + 1.6) * .032, '- - -  property boundary', color='#c2185b', fontsize=7.6, transform=lg.transAxes)
    save(fig)

    # 3 rain, 4 temps
    if rain.get('mean'):
        mean = rain['mean']; med = rain.get('median') or mean
        fig = page(txt.get('rain_title', 'Rain by month'), 'Monthly rainfall, mm: bars show a typical (median) month, ticks the average. July–September, the dry spring, is highlighted.',
                   f"Rainfall: {rain.get('station', 'SILO')}, {rain.get('period', '')}.")
        ax = fig.add_axes([.08, .14, .86, .68]); ax.bar(M, med, color=[ACC if i in (6, 7, 8) else GREY for i in range(12)], width=.62)
        for i, (md, mn) in enumerate(zip(med, mean)):
            ax.plot([i - .36, i + .36], [mn, mn], color='#555', lw=2); ax.text(i, md / 2, f'{md:.0f}', ha='center', color='white', fontsize=10, weight='bold')
        ax.set_yticks([]); [ax.spines[s_].set_visible(False) for s_ in ('top', 'right', 'left')]
        ax.text(11.4, max(mean) * .98, f'Average year: {ann:,.0f} mm\nJul–Sep: {dry:.0f}% of the year', ha='right', va='top', fontsize=10, color=SUB)
        save(fig)
    if rain.get('tmin'):
        tm = rain['tmin']
        fig = page('Night temperatures through the year', 'Average night-time minimum by month. Frost risk sits in the valley floors on still winter nights (see the cold-air layer on the map), not on the slopes.',
                   f"Minimum temperature: {rain.get('tminStation', 'SILO gridded')}.")
        ax = fig.add_axes([.08, .14, .86, .68]); ax.bar(M, tm, color=[ACC if i in (5, 6, 7) else GREY for i in range(12)], width=.62)
        for i, a in enumerate(tm): ax.text(i, a + .4, f'{a:.1f}°', ha='center', fontsize=9.5)
        ax.set_yticks([]); [ax.spines[s_].set_visible(False) for s_ in ('top', 'right', 'left')]
        save(fig)

    # 4b 30-year rain test (SILO daily rain, when the site has it)
    dpath = os.path.join(sb, 'rain_daily.json')
    if os.path.exists(dpath):
        DL = json.load(open(dpath)); res = tank_test(DL, S['lat'])
        yrs = sorted(res['annual']); tot = [res['annual'][y] for y in yrs]; mean_a = float(np.mean(tot))
        full = [y for y in yrs if y < int(DL['end'][:4])]; tot_f = [res['annual'][y] for y in full]
        fig = page('Thirty years of rain, day by day', f"Rain that actually fell at the property each year since {yrs[0]}, and what it would have meant for a typical house tank.",
                   f"SILO gridded daily rainfall at the property, {DL['start'][:4]}–{DL['end'][:4]}, Queensland Government, CC BY 4.0.")
        ax = fig.add_axes([.07, .36, .58, .46])
        driest = sorted(full, key=lambda y: res['annual'][y])[:3]
        ax.bar(full, tot_f, color=[ '#d9534f' if y in driest else GREY for y in full], width=.72)
        ax.axhline(mean_a, color=ACC, lw=1.6); ax.text(full[-1] + 1.1, mean_a, f'average\n{mean_a:,.0f} mm', color=ACC, fontsize=9, va='center')
        for y in driest: ax.text(y, res['annual'][y] + max(tot_f) * .015, f'{y}\n{res["annual"][y]:,.0f}', ha='center', fontsize=8, color='#a33')
        ax.set_ylabel('mm in the year', color=SUB); [ax.spines[s_].set_visible(False) for s_ in ('top', 'right')]; ax.set_xlim(full[0] - .8, full[-1] + 5); ax.set_xticks([y for y in full if y % 5 == 0])
        ax.text(.01, .97, 'The three driest years are in red', transform=ax.transAxes, fontsize=9, color='#a33', va='top')
        # tank panel
        px0 = .70; fig.patches.append(FancyBboxPatch((px0, .36), .26, .46, boxstyle='round,pad=0.005,rounding_size=0.015', transform=fig.transFigure, fc='#f3f2ee', ec='none'))
        fig.text(px0 + .015, .78, 'A typical house tank, run through every day', fontsize=10.5, weight='bold', va='top')
        fig.text(px0 + .015, .72, f"{res['share']*100:.0f}%", fontsize=26, weight='bold', color=INK, va='top'); fig.text(px0 + .015, .655, 'of the household water came from the tank', fontsize=9, color=SUB, va='top')
        fig.text(px0 + .015, .60, f"{res['days_with']*100:.0f}%", fontsize=26, weight='bold', color=INK, va='top'); fig.text(px0 + .015, .535, 'of days the tank had water in it', fontsize=9, color=SUB, va='top')
        fig.text(px0 + .015, .48, f"{res['longest']} days", fontsize=26, weight='bold', color='#a33' if res['longest'] > 30 else INK, va='top')
        fig.text(px0 + .015, .415, f"longest run empty, ending {res['longest_when']}" if res['longest'] else 'the tank never ran dry', fontsize=9, color=SUB, va='top')
        fig.text(px0 + .015, .375, textwrap.fill(f"Assumes a {res['roof']:.0f} m² roof, {res['store']/1000:.0f},000 L of storage, {res['house']:.0f} L a day in the house and 85% of roof rain collected.", 44), fontsize=7.8, color=SUB, va='top')
        fig.text(.07, .27, textwrap.fill(f"How to read it: the chart is the real record, not an average. A design that only works in an average year fails in {driest[0]}. "
                 f"The tank panel runs the same arithmetic the design map uses: each day's rain tops the tank up from the roof, the house draws its daily use, and a small garden store (25 mm of soil moisture) is watered only when it runs down. "
                 f"Bigger storage or a bigger roof moves the numbers; the map's Tools tab lets you try your own.", 170), fontsize=9.4, color=INK, linespacing=1.5, va='top')
        save(fig)

    # 5 slope share
    labs = ['Under 10%', '10–18%', '18–25%', '25–33%', '33–50%', 'Over 50%']; uses = ['tracks, beds, buildings', 'contour beds, orchards', 'terraces, tree crops', 'tree crops on contour', 'forest, light grazing', 'keep in forest']
    vals = [c[2] * 100 for c in sl]
    fig = page('How steep is the land?', 'Share of the property in each slope class, with what each class suits.', 'Slope from the elevation model at 1–2 m resolution.')
    ax = fig.add_axes([.25, .14, .65, .7]); cols = ['#2ea05a', '#aac846', '#f0c83c', '#f08c32', '#dc5032', '#8c1e3c']
    ax.barh(labs, vals, color=cols); ax.invert_yaxis()
    for i, v in enumerate(vals): ax.text(v + .8, i, f'{v:.0f}%  ·  {uses[i]}', va='center', fontsize=10)
    ax.set_xticks([]); [ax.spines[s_].set_visible(False) for s_ in ('top', 'right', 'bottom')]; ax.set_xlim(0, max(vals) * 1.6)
    save(fig)

    # 6 profile: lowest to highest point of the lot
    zi = np.where(ins, Ds, np.nan); lo = np.unravel_index(np.nanargmin(zi), zi.shape); hi = np.unravel_index(np.nanargmax(zi), zi.shape)
    a, b = np.array([X[lo], Y[lo]]), np.array([X[hi], Y[hi]]); L = np.linalg.norm(b - a); n = max(30, int(L / 2))
    pts = [a + (b - a) * t for t in np.linspace(0, 1, n)]; zz = [Ds[int(p[1] / 2), int(p[0] / 2)] for p in pts]; dd = np.linspace(0, L, n)
    az = (math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1]))) + 360) % 360; dn = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'][round(az / 45) % 8]
    fig = page('From the lowest point to the highest', f'A straight line across the property from its lowest ground ({min(zz):.0f} m) to its highest ({max(zz):.0f} m), heading {dn}.', 'Elevation model, lightly smoothed. Distances are horizontal.')
    ax = fig.add_axes([.08, .16, .86, .66]); ax.fill_between(dd, min(zz) - 2, zz, color='#e8e2d4'); ax.plot(dd, zz, color='#6d5a3a', lw=2.2)
    ax.set_xlabel('Distance (m)', color=SUB); ax.set_ylabel('Height above sea level (m)', color=SUB); [ax.spines[s_].set_visible(False) for s_ in ('top', 'right')]
    ax.set_ylim(min(zz) - 2, max(zz) + (max(zz) - min(zz)) * .1); avg = (max(zz) - min(zz)) / L * 100
    ax.text(.02, .92, f'Average grade along the line: {avg:.0f}%', transform=ax.transAxes, fontsize=10.5)
    save(fig)

    # 7 sun
    lat = math.radians(S['lat'])
    fig = page('Sun through the year', f"Sun paths at {abs(S['lat']):.1f}° S, and the hours of direct sun the property gets once the hills are taken into account.",
               'Sun hours: terrain shading only (trees not counted), averaged over the property.')
    ax = fig.add_axes([.06, .12, .5, .72])
    for dec_, c, lab in [(23.44, '#c0392b', 'Midwinter'), (0, '#e08a1e', 'Equinox'), (-23.44, ACC, 'Midsummer')]:
        d = math.radians(dec_); pp = []
        for hh in np.linspace(-180, 180, 721):
            h = math.radians(hh); alt = math.asin(math.sin(lat) * math.sin(d) + math.cos(lat) * math.cos(d) * math.cos(h))
            if alt <= 0: continue
            azm = math.atan2(-math.sin(h), math.tan(d) * math.cos(lat) - math.sin(lat) * math.cos(h)); r = 90 - math.degrees(alt); pp.append((r * math.sin(azm), r * math.cos(azm)))
        pp = np.array(pp); ax.plot(pp[:, 0], pp[:, 1], color=c, lw=2.2, label=lab)
    for r in (30, 60, 90): ax.add_patch(Circle((0, 0), r, fill=False, ec='#ddd', lw=.8)); ax.text(2, r - 4, f'{90 - r}°', fontsize=7, color='#aaa')
    for t, (x, y) in {'N': (0, 96), 'E': (96, 0), 'S': (0, -100), 'W': (-100, 0)}.items(): ax.text(x, y, t, ha='center', va='center', weight='bold')
    ax.set_xlim(-105, 105); ax.set_ylim(-105, 105); ax.set_aspect('equal'); ax.axis('off'); ax.legend(loc='lower left', frameon=False, fontsize=9)
    ax2 = fig.add_axes([.62, .2, .33, .55]); hrs = {'Midwinter': meta['sun_winter_lotmean'], 'Equinox': meta['sun_equinox_lotmean'], 'Midsummer': meta['sun_summer_lotmean']}
    for i, (k_, v) in enumerate(hrs.items()):
        ax2.barh(i, v, color=ACC if k_ == 'Midwinter' else GREY, height=.55); ax2.text(v + .2, i, f'{v:.1f} h', va='center', fontsize=10.5)
    ax2.set_yticks(range(3)); ax2.set_yticklabels(list(hrs)); ax2.invert_yaxis(); ax2.set_xticks([]); ax2.set_xlim(0, 16); [ax2.spines[s_].set_visible(False) for s_ in ('top', 'right', 'bottom')]
    ax2.set_title('Direct sun on the property (average)', fontsize=10, color=SUB)
    save(fig)

    # 8 water & erosion
    if H:
        w = H['wet']; w = ast.literal_eval(w) if isinstance(w, str) else w; e = H['erosion']; e = ast.literal_eval(e) if isinstance(e, str) else e
        fig = page('Where water gathers, and where soil could move', 'Share of the property in each wetness class (where water collects after rain) and each erosion-risk class (if the ground were left bare).',
                   'Wetness: topographic wetness index. Erosion: slope-length and steepness factor (RUSLE LS). Both computed by the map from the terrain.')
        for j, (dd_, ttl, cl) in enumerate([(w, 'Wetness', ['#e9e4d6', '#aad2eb', '#5aa0dc', '#1e64c8', '#0a288c']), (e, 'Erosion risk if bare', ['#e9e4d6', '#f5d750', '#f09628', '#d73c28', '#781450'])]):
            ax = fig.add_axes([.17 + j * .45, .16, .3, .64]); labs_ = [c[3].split(':')[0] for c in dd_['classes']]; v = [x * 100 for x in dd_['lotShare']]
            ax.barh(labs_, v, color=cl); ax.invert_yaxis(); ax.set_title(ttl, fontsize=11, loc='left')
            for i, x in enumerate(v): ax.text(x + 1, i, f'{x:.0f}%', va='center', fontsize=10)
            ax.set_xticks([]); ax.set_xlim(0, 115); [ax.spines[s_].set_visible(False) for s_ in ('top', 'right', 'bottom')]
        save(fig)

    # 9 forest structure
    if VEG:
        fig = page('Forest structure from the LiDAR', 'Share of the property in each vegetation height class, from the 2022 laser survey of the canopy.', 'Source: ' + VEG.get('source', 'LiDAR canopy'))
        ax = fig.add_axes([.36, .14, .55, .7]); cl = [VEG['classes'][i] for i in range(len(VEG['classes']))]
        ax.barh([textwrap.shorten(c['label'], 48) for c in cl], [c['lotShare'] * 100 for c in cl], color=[tuple(x / 255 for x in c['rgba'][:3]) for c in cl]); ax.invert_yaxis()
        for i, c in enumerate(cl): ax.text(c['lotShare'] * 100 + .8, i, f"{c['lotShare']*100:.0f}% · {c['lotHa']:.1f} ha", va='center', fontsize=10)
        ax.set_xticks([]); ax.set_xlim(0, max(c['lotShare'] for c in cl) * 140); [ax.spines[s_].set_visible(False) for s_ in ('top', 'right', 'bottom')]
        save(fig)

    # 9b natural vegetation types (Queensland regional ecosystems)
    epath = os.path.join(sb, 'ecosystems.json')
    if os.path.exists(epath):
        ECO = json.load(open(epath)); cat = ECO['cat']
        COL = {'Endangered': '#c62828', 'Of concern': '#ef8c1e', 'Least concern': '#3c9650', 'water': '#4682c8', 'plantation': '#82724a'}
        def status(lab):
            c = lab.split('/')[0].strip()
            return c if c in COL else (cat.get(c, {}).get('vm') or '')
        fig = page('What grows here naturally', 'Regional ecosystems around the property: the vegetation each patch carries when left alone, coloured by Vegetation Management Act status.',
                   'Source: Qld Herbarium regional ecosystem mapping (VM Act labels), CC BY 4.0, 24 Oct 2026; descriptions and status: REDD v13.1. Mapped ~1:100,000, so edges can be 50 m or more out.')
        ax = fig.add_axes([.04, .07, .55, .8])
        ax.imshow(hs, extent=(0, 2000, 2000, 0), cmap='gray', alpha=.5)
        area_by = {}
        for p in ECO['polys']:
            st = status(p['re']); c = COL.get(st)
            for r in p['rings']:
                ax.add_patch(Polygon(r, closed=True, fc=c if c else 'none', ec='#3a4a3a', lw=.45, alpha=.42 if c else 1))
            a_ = max(abs(np.dot(np.array(r)[:, 0], np.roll(np.array(r)[:, 1], 1)) - np.dot(np.array(r)[:, 1], np.roll(np.array(r)[:, 0], 1))) / 2 for r in p['rings'])
            area_by[p['re']] = area_by.get(p['re'], 0) + a_
            if c and a_ > 12000:
                r = max(p['rings'], key=len); rr = np.array(r); cx, cy = rr.mean(0)
                if MPath(rr).contains_point((cx, cy)) and 0 < cx < 2000 and 0 < cy < 2000 and p['re'] not in COL: ax.text(cx, cy, p['re'].split('/')[0], fontsize=6.2, ha='center', va='center', color='#102010', clip_on=True)
        ax.add_patch(Polygon(lot, closed=True, fill=False, ec='#c2185b', lw=1.7, ls=(0, (6, 3)), zorder=6))
        ax.set_xlim(0, 2000); ax.set_ylim(2000, 0); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        for s_ in ax.spines.values(): s_.set_visible(False)
        ax.plot([80, 580], [1930, 1930], color='#222', lw=2.2); ax.text(330, 1890, '500 m', ha='center', fontsize=8)
        ax.annotate('N', xy=(1900, 100), xytext=(1900, 260), ha='center', fontsize=10, weight='bold', arrowprops=dict(arrowstyle='-|>', color='#222'))
        lg = fig.add_axes([.61, .07, .36, .8]); lg.axis('off')
        yy_ = 1.0
        for st, c in COL.items():
            if any(status(p['re']) == st for p in ECO['polys']):
                lg.add_patch(FancyBboxPatch((0, yy_ - .018), .05, .018, boxstyle='round,pad=0.002', fc=c, ec='none', alpha=.75, transform=lg.transAxes))
                lg.text(.07, yy_ - .009, {'water': 'Water', 'plantation': 'Plantation'}.get(st, st + ' (VM Act status)'), fontsize=8.2, va='center', transform=lg.transAxes); yy_ -= .032
        lg.add_patch(FancyBboxPatch((0, yy_ - .018), .05, .018, boxstyle='round,pad=0.002', fc='white', ec='#777', lw=.6, transform=lg.transAxes))
        lg.text(.07, yy_ - .009, 'Non-remnant: cleared, built on, or young regrowth', fontsize=8.2, va='center', transform=lg.transAxes); yy_ -= .05
        lg.text(0, yy_, 'Types within the 2 km square, largest first', fontsize=9.5, weight='bold', va='top', transform=lg.transAxes); yy_ -= .035
        for lab in sorted(area_by, key=lambda k: -area_by[k]):
            if lab in COL or lab == 'non-rem': continue
            parts = []
            for c_ in lab.split('/'):
                c_ = c_.strip(); e = cat.get(c_)
                parts.append(f"{c_}: {e['d']} ({e['vm']})" if e else c_)
            s_ = textwrap.fill(' / '.join(parts) + ('   [a mix, in order of area]' if '/' in lab else ''), 66)
            nl = s_.count('\n') + 1
            if yy_ - nl * .0235 < 0: break
            lg.text(0, yy_, s_, fontsize=7.4, va='top', transform=lg.transAxes, color=INK, linespacing=1.3); yy_ -= nl * .0235 + .012
        save(fig)

    # 10 inventory
    groups = {}
    for f in F:
        k = K[f['kind']]; g = f['geom']; a_ = 0
        if g['g'] == 'polygon' and len(g.get('pts') or []) > 2:
            p = np.array(g['pts']); a_ = abs(np.dot(p[:, 0], np.roll(p[:, 1], 1)) - np.dot(p[:, 1], np.roll(p[:, 0], 1))) / 2
        d = groups.setdefault(k['g'], {}); r_ = d.setdefault(k['label'], [0, 0.]); r_[0] += 1; r_[1] += a_
    fig = page("What's in the design so far", f'Everything drawn on the {name} design map, grouped by type: {len(F)} items.', 'Counts and areas from the design map as of 24 Oct 2026.')
    ax = fig.add_axes([.06, .08, .88, .78]); ax.axis('off')
    col = 0; row = 0; per = 15
    for gname in sorted(groups, key=lambda g: -sum(v[0] for v in groups[g].values())):
        lines = [(lab, n, a_) for lab, (n, a_) in sorted(groups[gname].items(), key=lambda t: -t[1][0])]
        need = len(lines) + 2
        if row + need > per * 2.2: col += 1; row = 0
        if col > 2: break
        x = col * .34; y = 1 - row * .045
        ax.text(x, y, gname, fontsize=11.5, weight='bold', transform=ax.transAxes); row += 1
        for lab, n, a_ in lines[:10]:
            y = 1 - row * .045; s_ = f'{n} × {textwrap.shorten(lab, 32)}' + (f'  ({a_/1e4:.2f} ha)' if a_ >= 2000 else f'  ({a_:,.0f} m²)' if a_ else '')
            ax.text(x + .01, y, s_, fontsize=9.2, transform=ax.transAxes); row += 1
        row += .6
    save(fig)

    # 11 principles
    fig = page(f'Twelve principles at {name}', "One line for each of Holmgren's design principles.", 'Principles: David Holmgren, Permaculture: Principles and Pathways Beyond Sustainability.')
    for i, (t, s_) in enumerate(zip(PRINCIPLES, txt['principles'])):
        x = .06 + (i % 4) * .225; y = .62 - (i // 4) * .25
        fig.patches.append(FancyBboxPatch((x, y), .205, .21, boxstyle='round,pad=0.004,rounding_size=0.012', transform=fig.transFigure, fc=PAL[i], ec='none'))
        fig.text(x + .012, y + .19, textwrap.fill(t, 24), fontsize=10.5, weight='bold', va='top'); fig.text(x + .012, y + .095, textwrap.fill(s_, 31), fontsize=9, va='top', color='#333')
    save(fig)
    pdf.close(); print('saved', out, len(F), 'features')


if __name__ == '__main__':
    main(*sys.argv[1:4])

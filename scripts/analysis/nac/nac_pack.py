import textwrap, json, base64, zlib, ast, math, numpy as np, matplotlib, datetime as dt
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Wedge, Polygon
from scipy.ndimage import gaussian_filter
D = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
OUT = '/home/claude/annwn-out/NAC design graphics.pdf'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
GREY, ACC, INK, SUB = '#b8b8b2', '#2f6fb3', '#222', '#666'
A4 = (11.69, 8.27)

S = json.load(open('/mnt/user-data/uploads/Permiculture Noosa PDC/NAC/Lidar-survey data/NSW site pack nac/silo_daily.json'))
dates = [dt.date.fromisoformat(r['date']) for r in S['data']]
val = lambda r, c: next(x['value'] for x in r['variables'] if x['variable_code'] == c)
R = np.array([val(r, 'daily_rain') for r in S['data']]); TN = np.array([val(r, 'min_temp') for r in S['data']])
mon = np.array([d.month for d in dates]); yrs = np.array([d.year for d in dates])
M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def page(title, sub, foot):
    fig = plt.figure(figsize=A4)
    fig.text(.06, .93, title, fontsize=19, weight='bold', color=INK)
    fig.text(.06, .895, sub, fontsize=10.5, color=SUB)
    fig.text(.06, .035, foot, fontsize=7.5, color='#888')
    fig.text(.94, .035, 'NAC · preliminary design · Oct 2026', fontsize=7.5, color='#888', ha='right')
    return fig

pdf = PdfPages(OUT)

# 1 cover / at a glance
fig = page('NAC at a glance', 'North Arm Cove, Mid Coast NSW · a first look at the land, water and climate behind Ange\'s plan',
           'Sources: NSW 5 m elevation and property register; SILO daily climate 1995–2025; Ange\'s landscaping sketch.')
tiles = [('1,125 m²', 'block, about 66 m × 17 m'), ('2.5 m fall', 'gently to the north (10–15%)'), ('1,300 mm', 'rain in an average year'),
         ('Aug–Oct', 'the dry gap: 17% of the rain'), ('35,000 L', 'tanks already on site'), ('0 frosts', 'in 30 years; coldest 0.4 °C'),
         ('~10 h', 'midwinter daylight (before trees)'), ('52 days', 'longest dry spell (2005)')]
for i, (big, small) in enumerate(tiles):
    x = .06 + (i % 4) * .225; y = .56 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .2, .2, boxstyle='round,pad=0.005,rounding_size=0.015', transform=fig.transFigure, fc='#f3f2ee', ec='none'))
    fig.text(x + .015, y + .11, big, fontsize=24, weight='bold', color=ACC if i in (4,) else INK)
    fig.text(x + .015, y + .05, small, fontsize=10, color=SUB, wrap=True)
fig.text(.06, .2, 'The big picture', fontsize=12, weight='bold')
fig.text(.06, .1, '• Water is already in good shape: connect the garage and carport roofs and it covers even the 2019 drought.\n'
                   '• Sunlight under the gums is the real limit for fruit; plant food in the sunniest northern ground, outside gum root reach.\n'
                   '• Keep koala food trees, check bush fire prone mapping, and decide about the gum beside the house first.', fontsize=10.5, color=INK, linespacing=1.6)
pdf.savefig(fig); plt.close(fig)

# 2 site plan
fig = page('Ange\'s plan on the land', 'Everything from the sketch, fitted to the boundary, with contours and the 5 m root zone around the gums',
           'Positions about ±1–2 m. Contours from NSW 5 m elevation, smoothed. Root zone = within 5 m of a gum or the ironbark.')
ax = fig.add_axes([.04, .07, .92, .8]); ax.imshow(plt.imread('/home/claude/annwn-out/nac-site-plan.png')); ax.axis('off')
pdf.savefig(fig); plt.close(fig)

# 3 rain
mean = [R[mon == m].sum() / 31 for m in range(1, 13)]
med = [np.median([R[(mon == m) & (yrs == y)].sum() for y in range(1995, 2026)]) for m in range(1, 13)]
fig = page('Rain falls mostly February to July', 'Monthly rainfall, mm: bars show a typical (median) month, ticks the average. August–October is the dry gap, just as spring growth starts.',
           'SILO gridded daily rainfall at the block, 1995–2025.')
ax = fig.add_axes([.08, .14, .86, .68])
cols = [ACC if m in (8, 9, 10) else GREY for m in range(1, 13)]
b = ax.bar(M, med, color=cols, width=.62)
for i, (md, mn) in enumerate(zip(med, mean)):
    ax.plot([i - .36, i + .36], [mn, mn], color='#555', lw=2)
    ax.text(i, md / 2, f'{md:.0f}', ha='center', color='white', fontsize=10, weight='bold')
ax.set_yticks([]); [ax.spines[s].set_visible(False) for s in ('top', 'right', 'left')]
ann = [R[yrs == y].sum() for y in range(1995, 2026)]
ax.text(11.4, max(mean) * .98, f'Driest year: 2019, {min(ann):.0f} mm\nWettest day: 216 mm (Apr 2015)\nAbout 3 days a year bring 50 mm+', ha='right', va='top', fontsize=9.5, color=SUB)
pdf.savefig(fig); plt.close(fig)

# 4 water
ETO = [5.3, 4.6, 3.8, 2.8, 2.0, 1.6, 1.8, 2.5, 3.4, 4.3, 4.8, 5.4]
def sim(roof, store, garden, house, year=None):
    s = store; soil = 25.; sup = dem = 0; lvl = []
    for i, r in enumerate(R):
        s = min(store, s + r * roof * .85); et = ETO[mon[i] - 1] * .6; soil = min(25, soil + r) - et; need = -soil if soil < 0 else 0; soil = max(soil, 0)
        want = need * garden + house; take = min(s, want); s -= take
        if year is None or yrs[i] == year: sup += take; dem += want
        if yrs[i] == 2019: lvl.append(s)
    return sup / dem, np.array(lvl)
fig = page('Connecting every roof carries the tanks through a drought', 'Tank level through 2019, the driest year on record (783 mm): a household using 300 L a day plus a 40 m² watered garden, 35,000 L of tanks.',
           'Daily simulation with SILO rainfall; 85% of roof rain reaches the tank; garden water from a simple soil-moisture balance. A guide, not a guarantee.')
ax = fig.add_axes([.08, .16, .86, .66])
_, l1 = sim(135, 35000, 40, 300); _, l2 = sim(172, 35000, 40, 300)
dd = np.arange(len(l1))
ax.plot(dd, l1 / 1000, color=GREY, lw=2); ax.plot(dd, l2 / 1000, color=ACC, lw=2.4)
ax.text(dd[-1] + 3, l2[-1] / 1000, 'House + garage\n+ carport roofs\n(172 m²)', color=ACC, fontsize=9.5, va='center')
ax.text(dd[-1] + 3, l1[-1] / 1000, 'House roof only\n(135 m²)', color='#777', fontsize=9.5, va='center')
ax.set_xlim(0, 400); ax.set_ylim(0, 37)
ax.set_xticks([sum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][:k]) for k in range(12)]); ax.set_xticklabels(M)
ax.set_ylabel('Water in tanks (thousand litres)', color=SUB); [ax.spines[s].set_visible(False) for s in ('top', 'right')]
ax.axhline(0, color='#c0392b', lw=.8); ax.text(5, .8, 'empty: the house goes short', color='#c0392b', fontsize=8.5)
r1, _ = sim(135, 35000, 40, 300, 2019); r2, _ = sim(172, 35000, 40, 300, 2019)
ax.text(10, 34.5, f'Share of water needs met in 2019:  house roof only {r1*100:.0f}%   ·   all roofs {r2*100:.0f}%', fontsize=10.5, color=INK)
pdf.savefig(fig); plt.close(fig)

# 5 sun and shade
fig = page('Winter sun is low: shadows fall long to the south', 'At 32.7° S a 25 m gum casts a 37 m noon shadow in midwinter but only 4 m in midsummer. Trees on the north and east cost the garden the most sun.',
           'Sun positions calculated for 32.7° S. Shadow length = tree height ÷ tan(sun height). Tree heights are examples; confirm on site.')
ax = fig.add_axes([.06, .12, .5, .72])
lat = math.radians(-32.67)
for dec, c, lab in [(23.44, '#c0392b', 'Midwinter'), (0, '#e08a1e', 'Equinox'), (-23.44, ACC, 'Midsummer')]:
    d = math.radians(dec); pts = []
    for hh in np.linspace(-180, 180, 721):
        h = math.radians(hh); alt = math.asin(math.sin(lat) * math.sin(d) + math.cos(lat) * math.cos(d) * math.cos(h))
        if alt <= 0: continue
        az = math.atan2(-math.sin(h), math.tan(d) * math.cos(lat) - math.sin(lat) * math.cos(h))
        r = 90 - math.degrees(alt); pts.append((r * math.sin(az), r * math.cos(az)))
    p = np.array(pts); ax.plot(p[:, 0], p[:, 1], color=c, lw=2.2, label=lab)
for r in (30, 60, 90): ax.add_patch(Circle((0, 0), r, fill=False, ec='#ddd', lw=.8)); ax.text(2, r - 4, f'{90 - r}°', fontsize=7, color='#aaa')
for t, (x, y) in {'N': (0, 96), 'E': (96, 0), 'S': (0, -100), 'W': (-100, 0)}.items(): ax.text(x, y, t, ha='center', va='center', weight='bold')
ax.set_xlim(-105, 105); ax.set_ylim(-105, 105); ax.set_aspect('equal'); ax.axis('off'); ax.legend(loc='lower left', frameon=False, fontsize=9)
ax.set_title('Sun path (centre = overhead)', fontsize=10, color=SUB)
ax2 = fig.add_axes([.62, .18, .33, .6])
alts = {'Midwinter': 33.9, 'Equinox': 57.3, 'Midsummer': 80.7}
for i, (k, a) in enumerate(alts.items()):
    L = 25 / math.tan(math.radians(a))
    ax2.barh(i, L, color=ACC if k == 'Midwinter' else GREY, height=.55); ax2.text(L + .8, i, f'{L:.0f} m', va='center', fontsize=10)
ax2.set_yticks(range(3)); ax2.set_yticklabels(list(alts)); ax2.invert_yaxis(); ax2.set_xticks([]); [ax2.spines[s].set_visible(False) for s in ('top', 'right', 'bottom')]
ax2.set_title('Noon shadow of a 25 m gum', fontsize=10, color=SUB)
ax2.text(0, 3.0, 'The block is only 17 m deep, so one tall tree\nnorth of the beds can shade them all winter.', fontsize=9, color=INK)
pdf.savefig(fig); plt.close(fig)

# 6 slope profile
T = json.load(open('/home/claude/pdc-design-map/map/sites/nac/terrain.json'))
d1 = T['meta']['dem1']; d1 = ast.literal_eval(d1) if isinstance(d1, str) else d1
A = gaussian_filter(np.frombuffer(zlib.decompress(base64.b64decode(d1['b64'])), np.uint16).reshape(d1['h'], d1['w']).astype(float) / 10, 7)
z = lambda x, y: A[int(y - d1['y0']), int(x - d1['x0'])]
fig = page('A gentle, even slope to the north', 'Cross-section from the south boundary to the north boundary through the house and through the fruit area (height above sea level).',
           'NSW 5 m elevation from aerial photos (smooths out small banks and terraces). Vertical scale exaggerated ×4. Check falls on site with a level.')
ax = fig.add_axes([.08, .16, .86, .64])
for x0, nm, c in [(1005, 'Through the house', GREY), (1019, 'Through the fruit trees', ACC)]:
    ys = np.linspace(1011.5 if x0 < 1010 else 1010.5, 997.5 if x0 < 1010 else 996.0, 15); dist = (ys[0] - ys); zz = [z(x0, y) for y in ys]
    ax.plot(dist, zz, color=c, lw=2.6, label=nm)
ax.set_xlabel('Distance from the south boundary (m)  →  north', color=SUB); ax.set_ylabel('Height (m)', color=SUB)
ax.set_aspect(4); [ax.spines[s].set_visible(False) for s in ('top', 'right')]; ax.legend(frameon=False)
ax.text(.02, .97, 'South boundary (higher)', transform=ax.transAxes, fontsize=9, color=SUB, ha='left'); ax.text(.99, .2, 'North (lower, sunnier)', transform=ax.transAxes, ha='right', fontsize=9, color=SUB)
pdf.savefig(fig); plt.close(fig)

# 7 night temps
mmin = [TN[mon == m].mean() for m in range(1, 13)]; low = [TN[mon == m].min() for m in range(1, 13)]
fig = page('Mild, frost-free winters', 'Average night-time minimum by month, with the coldest night recorded. No frost in 30 years, so citrus and bush foods are safe; plums need low-chill varieties.',
           'SILO gridded daily minimum temperature at the block, 1995–2025.')
ax = fig.add_axes([.08, .14, .86, .68])
ax.bar(M, mmin, color=[ACC if m in (6, 7, 8) else GREY for m in range(1, 13)], width=.62)
ax.scatter(range(12), low, color='#555', zorder=5, s=18);
for i, (a, l) in enumerate(zip(mmin, low)): ax.text(i, a + .5, f'{a:.1f}°', ha='center', fontsize=9.5)
ax.text(6, low[6] - 1.6, f'coldest {min(low):.1f}°', ha='center', fontsize=8.5, color='#555')
ax.axhline(0, color='#c0392b', lw=.8); ax.text(11.4, .4, 'frost line', color='#c0392b', fontsize=8.5, ha='right')
ax.set_yticks([]); ax.set_ylim(-2, 22); [ax.spines[s].set_visible(False) for s in ('top', 'right', 'left')]
pdf.savefig(fig); plt.close(fig)

# 8 plant light guide
fig = page('Right plant, right light', 'Where each plant on Ange\'s plan, and some suggested additions, will do best on this shaded bush block.',
           'Additions in italics. Root reach: keep thirsty fruit more than about 5 m from large gums.')
ax = fig.add_axes([.06, .1, .88, .74]); ax.axis('off')
cols = [('Full sun, 6 h+\n(open northern ground, outside gum roots)', ['Plum ×2 (low-chill)', 'Mandarin', 'Orange', 'Vegetable beds'], '#f6d77a'),
        ('Sun to part shade', ['Dwarf mulberry', 'Yuzu', 'Cumquat', 'Banksia, leucadendron', '*Finger lime*'], '#cfe5b4'),
        ('Part shade, forest edge\n(under or beside the gums)', ['Lemon myrtle', 'Herb bed (south side)', '*Midyim berry*', '*Native raspberry*', '*Warrigal greens*', '*Davidson plum*'], '#a9cfa0')]
for i, (h, items, c) in enumerate(cols):
    x = i / 3 + .01
    ax.add_patch(FancyBboxPatch((x, .02), .3, .95, boxstyle='round,pad=0.005,rounding_size=0.02', fc=c, ec='none', alpha=.55))
    ax.text(x + .015, .9, h, fontsize=11.5, weight='bold', va='top')
    for j, it in enumerate(items):
        ital = it.startswith('*'); ax.text(x + .02, .72 - j * .1, '• ' + it.strip('*'), fontsize=11, style='italic' if ital else 'normal')
pdf.savefig(fig); plt.close(fig)

# 9 principles
P = [('Observe & interact', 'Winter sun log, tree ID and a soil test before planting.'), ('Use small & slow solutions', 'Hand-dug swales; one guild and two beds first.'),
     ('Catch & store energy', '35 kL tanks, every roof connected, solar, mulch basins.'), ('Design from patterns to details', 'Zones from the house out; slope and sun before plants.'),
     ('Creatively use & respond to change', 'Fire-wise near the house; drier springs; koala trees kept.'), ('Obtain a yield', 'Veg, herbs, citrus, plums, mulberry, bush foods.'),
     ('Produce no waste', 'Scraps to compost or worms; laundry water to fruit trees.'), ('Use & value renewable resources', 'Gum-leaf mulch, rainwater, birds and bees.'),
     ('Use edges & value the marginal', 'Shade herbs and bush foods on the rooty edges; curved beds.'), ('Integrate rather than segregate', 'Guilds; garage roof feeds its own garden tank.'),
     ('Use & value diversity', 'Exotic fruit, bush foods, natives and herbs in layers.'), ('Apply self-regulation & accept feedback', 'Watch tank levels each spring; expand what thrives.')]
pal = ['#e6efc4', '#f9d3c4', '#e3efc9', '#f3d6e2', '#f8efb8', '#d7ecd6', '#e6dcf1', '#d9def3', '#f8e1b8', '#f6cfcf', '#fbd9bf', '#d3e7ef']
fig = page('Twelve principles at NAC', 'One line for each of Holmgren\'s design principles, for the group presentation.', 'Principles: David Holmgren, Permaculture: Principles and Pathways Beyond Sustainability.')
for i, (t, s) in enumerate(P):
    x = .06 + (i % 4) * .225; y = .62 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .205, .21, boxstyle='round,pad=0.004,rounding_size=0.012', transform=fig.transFigure, fc=pal[i], ec='none'))
    fig.text(x + .012, y + .19, textwrap.fill(t, 24), fontsize=10.5, weight='bold', va='top')
    fig.text(x + .012, y + .095, textwrap.fill(s, 30), fontsize=9, va='top', color='#333')
pdf.savefig(fig); plt.close(fig)

# 10 staging
fig = page('A staged order of work', 'Each stage is done once and done well, and tells you something before spending on the next.', 'Costs are rough 2026 retail ranges; get local quotes.')
ax = fig.add_axes([.06, .12, .88, .7]); ax.axis('off')
st = [('1 · Now', 'mostly free', 'Sun log · identify the gums · soil pH test · check bush fire prone map and RFS 10/50 tool · clear gutters'),
      ('2 · Before summer', '$300–1,500', 'Connect garage and carport roofs · leaf guards and first-flush · slimline as garden tank with small pump or gravity drip'),
      ('3 · Autumn 2027', '$500–1,500', 'Fill raised beds with good soil · first fruit guild in the sunniest spot · mulched swale on contour below the house'),
      ('4 · Later', 'as budget allows', 'Remaining fruit and bush foods · laundry greywater to fruit trees · seat or fire pit · native bees')]
import textwrap
for i, (a, c, w) in enumerate(st):
    y = .8 - i * .24; x = .02 + i * .04
    ax.add_patch(FancyBboxPatch((x, y), .9 - i * .04, .18, boxstyle='round,pad=0.005,rounding_size=0.02', fc=ACC if i == 0 else '#eef2f7', ec='none'))
    colr = 'white' if i == 0 else INK
    ax.text(x + .02, y + .12, a, fontsize=13, weight='bold', color=colr); ax.text(x + .02, y + .04, c, fontsize=10, color=colr)
    ax.text(x + .25, y + .09, textwrap.fill(w, 70), fontsize=10.5, color=colr, va='center')
pdf.savefig(fig); plt.close(fig)

pdf.close(); print('saved', OUT)

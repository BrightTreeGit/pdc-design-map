import textwrap, json, base64, zlib, ast, math, numpy as np, matplotlib, datetime as dt
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Wedge, Polygon
from scipy.ndimage import gaussian_filter
D = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
OUT = '/home/claude/annwn-out/Annwn design graphics.pdf'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
GREY, ACC, INK, SUB = '#b8b8b2', '#2f6fb3', '#222', '#666'
A4 = (11.69, 8.27)

S = json.load(open('/mnt/user-data/uploads/Claude Access--Permiculture Noosa PDC/Annwn/Site data/silo_daily.json'))
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
    fig.text(.94, .035, 'Annwn · preliminary design · Oct 2026', fontsize=7.5, color='#888', ha='right')
    return fig

pdf = PdfPages(OUT)


ann = {y: R[yrs == y].sum() for y in range(1995, 2026)}
mean = [R[mon == m].sum() / 31 for m in range(1, 13)]
med = [np.median([R[(mon == m) & (yrs == y)].sum() for y in range(1995, 2026)]) for m in range(1, 13)]
run = best = 0
for r in R:
    run = run + 1 if r < 2 else 0; best = max(best, run)
mmin = [TN[mon == m].mean() for m in range(1, 13)]; low = [TN[mon == m].min() for m in range(1, 13)]
dry3 = sum(mean[6:9]) / sum(mean) * 100

# 1 at a glance
fig = page('Annwn at a glance', 'Capalaba, Redlands Qld · a first look at the water, climate and planting behind Bronwen\'s garden',
           'Sources: Queensland cadastre; SILO daily climate 1995–2025; Bronwen\'s sketch.')
tiles = [('770 m²', 'level corner block'), (f'{np.mean(list(ann.values())):,.0f} mm', 'rain in an average year'), ('Jul–Sep', f'the dry stretch: {dry3:.0f}% of the rain'),
         (f'{best} days', 'longest dry spell in 30 years'), ('5,000 L', 'tanks now (3,000 L + 2,000 L)'), ('10,000 L', 'recommended: add one slimline'),
         ('0 frosts', f'in 30 years; coldest {min(low):.1f} °C'), ('2.5 m', 'tree height kept for picking from the ground')]
for i, (big, small) in enumerate(tiles):
    x = .06 + (i % 4) * .225; y = .56 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .2, .2, boxstyle='round,pad=0.005,rounding_size=0.015', transform=fig.transFigure, fc='#f3f2ee', ec='none'))
    fig.text(x + .015, y + .11, big, fontsize=24, weight='bold', color=ACC if i == 5 else INK)
    fig.text(x + .015, y + .05, small, fontsize=10, color=SUB)
fig.text(.06, .2, 'The big picture', fontsize=12, weight='bold')
fig.text(.06, .1, '• One more 5,000 L tank, linked to the two you have, covers about 90% of a 120 m² garden\'s watering.\n'
                   '• Find the sewer line first; keep stronger-rooted fruit trees 5 m or more from it.\n'
                   '• Small trees, waist-high beds and drip on a timer keep the garden easy to run for the next 20 years.', fontsize=10.5, color=INK, linespacing=1.6)
pdf.savefig(fig); plt.close(fig)

# 2 sewer plan
fig = page('Planting distances from the sewer', 'Colour bands show what can grow where, assuming the sewer follows the dashed line on Bronwen\'s sketch. Two possible new tank spots and the shed trellis are marked.',
           'Confirm the real sewer line with Redland City Council\'s property plan and a Before You Dig enquiry before planting trees.')
ax = fig.add_axes([.2, .06, .6, .82]); ax.imshow(plt.imread('/home/claude/annwn-out/annwn-sewer-plan.png')); ax.axis('off')
pdf.savefig(fig); plt.close(fig)

# 3 tanks
fig = page('One more tank lifts the garden to 90% tank water', 'Share of a 120 m² garden\'s watering met from the tanks, from a day-by-day run through 30 years of real rainfall.',
           'House roof about 165 m². Rough cost for the new tank, base, pump and drip timer: $2,500–4,000. A sound second-hand tank can halve it.')
ax = fig.add_axes([.12, .08, .76, .8]); ax.imshow(plt.imread('/home/claude/annwn-out/annwn-tank-chart.png')); ax.axis('off')
pdf.savefig(fig); plt.close(fig)

# 4 rain
fig = page('Wet summers, a dry late winter and spring', 'Monthly rainfall, mm: bars show a typical (median) month, ticks the average. July–September is when stored water matters most.',
           'SILO gridded daily rainfall at the block, 1995–2025.')
ax = fig.add_axes([.08, .14, .86, .68])
ax.bar(M, med, color=[ACC if m in (7, 8, 9) else GREY for m in range(1, 13)], width=.62)
for i, (md, mn) in enumerate(zip(med, mean)):
    ax.plot([i - .36, i + .36], [mn, mn], color='#555', lw=2); ax.text(i, md / 2, f'{md:.0f}', ha='center', color='white', fontsize=10, weight='bold')
ax.set_yticks([]); [ax.spines[s].set_visible(False) for s in ('top', 'right', 'left')]
dmax = R.max(); dday = dates[R.argmax()]
ax.text(11.4, max(mean) * .98, f'Driest year: {min(ann, key=ann.get)}, {min(ann.values()):.0f} mm\nWettest day: {dmax:.0f} mm ({dday:%b %Y})\nAbout {(R >= 50).sum() / 31:.0f} days a year bring 50 mm+', ha='right', va='top', fontsize=9.5, color=SUB)
pdf.savefig(fig); plt.close(fig)

# 5 temps
fig = page('Frost-free: tropical fruit is safe', 'Average night-time minimum by month, with the coldest night recorded. No frost in 30 years, so custard apple, avocado, banana and dragon fruit all grow here.',
           'SILO gridded daily minimum temperature at the block, 1995–2025.')
ax = fig.add_axes([.08, .14, .86, .68])
ax.bar(M, mmin, color=[ACC if m in (6, 7, 8) else GREY for m in range(1, 13)], width=.62); ax.scatter(range(12), low, color='#555', zorder=5, s=18)
for i, a in enumerate(mmin): ax.text(i, a + .5, f'{a:.1f}°', ha='center', fontsize=9.5)
ax.text(6, low[6] - 1.6, f'coldest {min(low):.1f}°', ha='center', fontsize=8.5, color='#555')
ax.axhline(0, color='#c0392b', lw=.8); ax.text(11.4, .4, 'frost line', color='#c0392b', fontsize=8.5, ha='right')
ax.set_yticks([]); ax.set_ylim(-2, 24); [ax.spines[s].set_visible(False) for s in ('top', 'right', 'left')]
pdf.savefig(fig); plt.close(fig)

# 6 sun
fig = page('Winter sun is low: the house and shed cast long shadows', 'At 27.5° S the midwinter noon sun is 39° up; summer sun is almost overhead. Shadows fall south, so the back yard north of the house is the sunniest ground.',
           'Sun positions calculated for 27.5° S. Shadow length = height ÷ tan(sun height).')
ax = fig.add_axes([.06, .12, .5, .72]); lat = math.radians(-27.54)
for dec, c, lab in [(23.44, '#c0392b', 'Midwinter'), (0, '#e08a1e', 'Equinox'), (-23.44, ACC, 'Midsummer')]:
    d = math.radians(dec); pts = []
    for hh in np.linspace(-180, 180, 721):
        h = math.radians(hh); alt = math.asin(math.sin(lat) * math.sin(d) + math.cos(lat) * math.cos(d) * math.cos(h))
        if alt <= 0: continue
        az = math.atan2(-math.sin(h), math.tan(d) * math.cos(lat) - math.sin(lat) * math.cos(h)); r = 90 - math.degrees(alt); pts.append((r * math.sin(az), r * math.cos(az)))
    p = np.array(pts); ax.plot(p[:, 0], p[:, 1], color=c, lw=2.2, label=lab)
for r in (30, 60, 90): ax.add_patch(Circle((0, 0), r, fill=False, ec='#ddd', lw=.8)); ax.text(2, r - 4, f'{90 - r}°', fontsize=7, color='#aaa')
for t, (x, y) in {'N': (0, 96), 'E': (96, 0), 'S': (0, -100), 'W': (-100, 0)}.items(): ax.text(x, y, t, ha='center', va='center', weight='bold')
ax.set_xlim(-105, 105); ax.set_ylim(-105, 105); ax.set_aspect('equal'); ax.axis('off'); ax.legend(loc='lower left', frameon=False, fontsize=9); ax.set_title('Sun path (centre = overhead)', fontsize=10, color=SUB)
ax2 = fig.add_axes([.62, .18, .33, .6]); alts = {'Midwinter': 39.0, 'Equinox': 62.5, 'Midsummer': 86.0}
for i, (k, a) in enumerate(alts.items()):
    L = 4 / math.tan(math.radians(a)); ax2.barh(i, L, color=ACC if k == 'Midwinter' else GREY, height=.55); ax2.text(L + .1, i, f'{L:.1f} m', va='center', fontsize=10)
ax2.set_yticks(range(3)); ax2.set_yticklabels(list(alts)); ax2.invert_yaxis(); ax2.set_xticks([]); [ax2.spines[s].set_visible(False) for s in ('top', 'right', 'bottom')]
ax2.set_title('Noon shadow of a 4 m shed wall', fontsize=10, color=SUB)
ax2.text(0, 3.0, 'Keep sun-loving fruit north of buildings;\nuse the shaded south side for ferns, herbs\nand shade-tolerant understorey.', fontsize=9, color=INK)
pdf.savefig(fig); plt.close(fig)

# 7 plants by distance and care
fig = page('Right plant, right place', 'Bronwen\'s fruit list sorted by how far it should be from the sewer, with the care each needs. Every tree kept to about 2.5 m for picking from the ground.',
           'Distances follow council guidance on trees near sewers: too far from a pipe is much better than too close.')
ax = fig.add_axes([.06, .1, .88, .74]); ax.axis('off')
cols = [('Over the pipe to 2 m', ['Herbs and vegetables', 'Wicking beds', 'Groundcovers, turmeric, ginger', 'Pots of anything', 'Nothing woody'], '#e8a7a0'),
        ('2–5 m: small fruit', ['Pomegranate (easy)', 'Tahitian lime, dwarf citrus (easy)', 'Jaboticaba (very easy)', 'Dragon fruit (very easy)', 'Feijoa, acerola (easy)', 'Passionfruit vine (easy)'], '#f3d58a'),
        ('5 m and more', ['Custard apple (easy)', 'Avocado on a mound (medium)', 'Dwarf mango (medium)', 'Lychee (medium-high, unreliable)', 'Banana (medium)'], '#cfe5b4')]
for i, (h, items, c) in enumerate(cols):
    x = i / 3 + .01
    ax.add_patch(FancyBboxPatch((x, .02), .3, .95, boxstyle='round,pad=0.005,rounding_size=0.02', fc=c, ec='none', alpha=.6))
    ax.text(x + .015, .9, h, fontsize=12, weight='bold', va='top')
    for j, it in enumerate(items): ax.text(x + .02, .74 - j * .1, '• ' + it, fontsize=11)
pdf.savefig(fig); plt.close(fig)

# 8 easy care
fig = page('Easy to run for the next 20 years', 'Choices that keep the garden manageable at 67 and at 87.', 'Ideas drawn from the PDC urban permaculture session and the report.')
ax = fig.add_axes([.06, .1, .88, .74]); ax.axis('off')
items = [('Trees kept under 2.5 m', 'Pick and prune from the ground. No ladders, and small enough to net.'), ('Waist-high wicking beds', 'No bending; watered from below every week or two.'),
         ('Drip on a timer from the tanks', 'No hoses or cans to carry; a pump switches to mains if the tanks run dry.'), ('Wide, level paths', '1.0–1.2 m of crusher dust or pavers, wide enough for a cart.'),
         ('Deep free mulch', '10 cm of arborist chip: the biggest single saver of water and weeding.'), ('Fewer species, done well', 'Five fruits you love beat twenty you don\'t.')]
for i, (t, s) in enumerate(items):
    x = (i % 2) * .5; y = .78 - (i // 2) * .3
    ax.add_patch(FancyBboxPatch((x + .01, y - .08), .47, .25, boxstyle='round,pad=0.005,rounding_size=0.02', fc='#eef2f7', ec='none'))
    ax.text(x + .03, y + .11, t, fontsize=13, weight='bold', va='top'); ax.text(x + .03, y + .02, textwrap.fill(s, 55), fontsize=10.5, va='top', color='#333')
pdf.savefig(fig); plt.close(fig)

# 9 principles
P = [('Observe & interact', 'A season noting ponding, hot sun and possum paths before planting trees.'), ('Use small & slow solutions', 'One tank, one guild, one bed at a time, done well.'),
     ('Catch & store energy', 'Linked tanks, mulch basins, deep mulch; pump on the solar.'), ('Design from patterns to details', 'Zones and sectors first, plant choice last.'),
     ('Creatively use & respond to change', 'Designed for Bronwen at 67 and at 87.'), ('Obtain a yield', 'Fruit she loves, herbs, greens, and shade on the shed.'),
     ('Produce no waste', 'Scraps to worms or compost; prunings as mulch.'), ('Use & value renewable resources', 'Chop-and-drop pigeon pea and comfrey; free arborist chip.'),
     ('Use edges & value the marginal', 'Shed walls for vines; street edges for a low native screen.'), ('Integrate rather than segregate', 'Shed roof catches water, walls hold vines, vines shade the shed.'),
     ('Use & value diversity', 'Many species in small numbers: a harvest most months.'), ('Apply self-regulation & accept feedback', 'Start with two or three guilds; expand what thrives.')]
pal = ['#e6efc4', '#f9d3c4', '#e3efc9', '#f3d6e2', '#f8efb8', '#d7ecd6', '#e6dcf1', '#d9def3', '#f8e1b8', '#f6cfcf', '#fbd9bf', '#d3e7ef']
fig = page('Twelve principles at Annwn', 'One line for each of Holmgren\'s design principles.', 'Principles: David Holmgren, Permaculture: Principles and Pathways Beyond Sustainability.')
for i, (t, s) in enumerate(P):
    x = .06 + (i % 4) * .225; y = .62 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .205, .21, boxstyle='round,pad=0.004,rounding_size=0.012', transform=fig.transFigure, fc=pal[i], ec='none'))
    fig.text(x + .012, y + .19, textwrap.fill(t, 24), fontsize=10.5, weight='bold', va='top'); fig.text(x + .012, y + .095, textwrap.fill(s, 30), fontsize=9, va='top', color='#333')
pdf.savefig(fig); plt.close(fig)

# 10 staging
fig = page('A staged, budget-wise order of work', 'Do it once, do it well, spread over time.', 'Costs are rough 2026 South-East Queensland retail ranges; get local quotes.')
ax = fig.add_axes([.06, .12, .88, .7]); ax.axis('off')
st = [('1 · Now', '$0–300', 'Sewer plan from council and Before You Dig · drainage test · free arborist mulch, 10 cm deep on trees and beds'),
      ('2 · Before summer', '$2,500–4,000', 'Add a 5,000 L slimline, link all three tanks on a level base · pump with mains switch-over · drip on a timer'),
      ('3 · Autumn–winter 2027', '$600–1,500', 'Plant 2–3 fruit tree guilds where the sewer bands allow · shed trellis with passionfruit and kiwi'),
      ('4 · Later', 'as budget allows', 'More wicking beds · wide level paths · a shaded seat · tropical understorey')]
for i, (a, c, w) in enumerate(st):
    y = .8 - i * .24; x = .02 + i * .04
    ax.add_patch(FancyBboxPatch((x, y), .9 - i * .04, .18, boxstyle='round,pad=0.005,rounding_size=0.02', fc=ACC if i == 0 else '#eef2f7', ec='none'))
    colr = 'white' if i == 0 else INK
    ax.text(x + .02, y + .12, a, fontsize=13, weight='bold', color=colr); ax.text(x + .02, y + .04, c, fontsize=10, color=colr)
    ax.text(x + .27, y + .09, textwrap.fill(w, 68), fontsize=10.5, color=colr, va='center')
pdf.savefig(fig); plt.close(fig)
pdf.close(); print('saved', OUT)

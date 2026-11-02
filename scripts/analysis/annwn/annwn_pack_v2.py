import textwrap, json, base64, zlib, ast, math, numpy as np, matplotlib, datetime as dt
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Wedge, Polygon
from scipy.ndimage import gaussian_filter
D = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
OUT = '/home/claude/annwn-out/v2/Annwn design graphics v2.pdf'
G = json.load(open(D + 'bron/ground.json'))
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
    fig.text(.94, .035, 'Annwn · preliminary design v2 · Nov 2026', fontsize=7.5, color='#888', ha='right')
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
           'Sources: Queensland cadastre; 1 m Queensland Government LiDAR; SILO daily climate 1995–2025; Bronwen\'s sketch and answers; council drainage plan (1983).')
tiles = [('770 m²', f'corner block, {G["zmax"]-G["zmin"]:.1f} m fall'), (f'{np.mean(list(ann.values())):,.0f} mm', 'rain, average year'), ('2.2 m', 'sewer depth at manhole'),
         (f'{best} days', 'longest dry spell'), ('3,000 L', 'working tank (30 years old)'), ('+5,000 L', 'new tank on the shed'),
         ('$15,000', 'budget over a few years'), ('35 m²', 'sunny vegetable garden')]
for i, (big, small) in enumerate(tiles):
    x = .06 + (i % 4) * .225; y = .56 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .2, .2, boxstyle='round,pad=0.005,rounding_size=0.015', transform=fig.transFigure, fc='#f3f2ee', ec='none'))
    fig.text(x + .015, y + .11, big, fontsize=24, weight='bold', color=ACC if i == 5 else INK)
    fig.text(x + .015, y + .05, small, fontsize=10, color=SUB)
fig.text(.06, .2, 'The big picture', fontsize=12, weight='bold')
fig.text(.06, .1, '• Locate the house drain first, then add the 5,000 L tank on the shed: about 88% of a 120 m² garden\'s watering from tanks.\n'
                   '• Bronwen\'s first priority: a small creek and frog pond, fed by the soggy west side and the neighbour\'s runoff.\n'
                   '• Vegetables in full sun north of the big shed; the covered carport in the south-west corner comes last.', fontsize=10.5, color=INK, linespacing=1.6)
pdf.savefig(fig); plt.close(fig)

# 2 ground
fig = page('How the ground falls', f'A gentle 2–3% fall from the house pad ({G["zmax"]:.1f} m) east and north to the back corner ({G["zmin"]:.1f} m); the front yard drains to the street.',
           'Queensland Government LiDAR DEM, 1 m (state elevation service, Oct 2026; survey year to confirm). Contours at 0.25 m; check falls with a level before digging.')
ax = fig.add_axes([.02, .06, .55, .82]); ax.imshow(plt.imread(D + 'bron/annwn-ground-plan.png')); ax.axis('off')
fig.text(.6, .83, 'What it means', fontsize=12, weight='bold')
fig.text(.6, .79, textwrap.fill('Soggy spots: the west side sits low against the house pad and takes the neighbour\'s patio water, so a rain-garden trench there feeds the new creek and pond.', 44) + '\n\n' +
         textwrap.fill('Overflow and rain garden: everything in the back yard runs to the north-east corner, so that is where a mulch basin or rain garden belongs, kept 2 m or more off the sewer line.', 44) + '\n\n' +
         textwrap.fill('Sewer: confirmed by the 1983 council plan along the back and east fences to the manhole in the low north-east corner, where the fall takes it.', 44) + '\n\n' +
         textwrap.fill('Beds: with under 1 m of fall across the back yard, beds can run level without terracing; a few centimetres of fall toward the basin is all the drainage they need.', 44),
         fontsize=9.5, va='top', color=INK, linespacing=1.45)
pdf.savefig(fig); plt.close(fig)

# 3 sewer plan
fig = page('The updated plan', 'Colour bands show what can grow where, measured from the sewer main and house drain on the 1983 council plan.',
           'Positions approximate. Have a plumber locate the house drain and lodge a Before You Dig enquiry before digging.')
ax = fig.add_axes([.2, .06, .6, .82]); ax.imshow(plt.imread(D + 'bron2/annwn-design-plan.png')); ax.axis('off')
pdf.savefig(fig); plt.close(fig)

# 3 tanks
fig = page('A new tank on the shed lifts the garden to about 88% tank water', 'Share of a 120 m² garden\'s watering from the tanks: a day-by-day run through 1995–2026 rain and evaporation.',
           'Roof areas feeding each tank are estimates. Tank, base, charged line, pump and drip: about $3,000–4,800.')
ax = fig.add_axes([.06, .1, .88, .76]); ax.imshow(plt.imread('/home/claude/annwn-out/v2/annwn-tank-chart-v2.png')); ax.axis('off')
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
fig = page('Right plant, right place', 'Bronwen\'s food list sorted by how far each plant should be from the sewer. Annual vegetables grow happily over the sewer band.',
           'Distances follow council guidance on trees near sewers: too far from a pipe is much better than too close.')
ax = fig.add_axes([.06, .1, .88, .74]); ax.axis('off')
cols = [('Over the pipe to 2 m', ['Herbs and vegetables', 'Wicking beds', 'Groundcovers, turmeric, ginger', 'Pots of anything', 'Nothing woody'], '#e8a7a0'),
        ('2–5 m: small fruit', ['Tahitian lime, dwarf citrus (easy)', 'Jaboticaba (very easy)', 'Lemon myrtle, hedged to 3 m', 'Pineapple, dragon fruit (very easy)', 'Native screen shrubs', 'Passionfruit vine (easy)'], '#f3d58a'),
        ('5 m and more', ['Custard apple (easy)', 'Low-chill stone fruit, netted (medium)', 'Banana, 3 m+ (medium)', 'Avocado on a mound (medium)', 'Dwarf mango (medium)'], '#cfe5b4')]
for i, (h, items, c) in enumerate(cols):
    x = i / 3 + .01
    ax.add_patch(FancyBboxPatch((x, .02), .3, .95, boxstyle='round,pad=0.005,rounding_size=0.02', fc=c, ec='none', alpha=.6))
    ax.text(x + .015, .9, h, fontsize=12, weight='bold', va='top')
    for j, it in enumerate(items): ax.text(x + .02, .74 - j * .1, '• ' + it, fontsize=11)
pdf.savefig(fig); plt.close(fig)

# 8 easy care
fig = page('Easy to run for the next 20 years', 'Choices that keep the garden manageable for the next twenty years.', 'Ideas drawn from the PDC urban permaculture session and the report.')
ax = fig.add_axes([.06, .1, .88, .74]); ax.axis('off')
items = [('Heavy jobs to the handyman', 'Digging, trenching and moving soil and mulch; Bronwen plants, picks and enjoys.'), ('Waist-high wicking beds', 'No bending; watered from below every week or two.'),
         ('Drip on a timer from the tanks', 'No hoses or cans to carry; a pump switches to mains if the tanks run dry.'), ('Wide, level paths', '1.0–1.2 m of crusher dust or pavers, wide enough for a cart.'),
         ('Deep free mulch', '10 cm of arborist chip: the biggest single saver of water and weeding.'), ('Garden rooms', 'Pond court, vegetable room, shade garden and service strip: not seen all at once.')]
for i, (t, s) in enumerate(items):
    x = (i % 2) * .5; y = .78 - (i // 2) * .3
    ax.add_patch(FancyBboxPatch((x + .01, y - .08), .47, .25, boxstyle='round,pad=0.005,rounding_size=0.02', fc='#eef2f7', ec='none'))
    ax.text(x + .03, y + .11, t, fontsize=13, weight='bold', va='top'); ax.text(x + .03, y + .02, textwrap.fill(s, 55), fontsize=10.5, va='top', color='#333')
pdf.savefig(fig); plt.close(fig)

# 9 principles
P = [('Observe & interact', 'A season noting ponding, hot sun and possum paths before planting trees.'), ('Use small & slow solutions', 'One tank, one guild, one bed at a time, done well.'),
     ('Catch & store energy', 'Shed tank, rain-garden trench and pond; pumps run on the solar by day.'), ('Design from patterns to details', 'Zones and sectors first, plant choice last.'),
     ('Creatively use & respond to change', 'Designed to stay easy as the years go by.'), ('Obtain a yield', 'Fruit she loves, herbs, greens, and shade on the shed.'),
     ('Produce no waste', 'Scraps to worms or compost; prunings as mulch.'), ('Use & value renewable resources', 'Chop-and-drop pigeon pea and comfrey; free arborist chip.'),
     ('Use edges & value the marginal', 'Soggy west strip becomes a rain garden; the sewer band grows vegetables.'), ('Integrate rather than segregate', 'Neighbour\'s runoff feeds the creek; the pond feeds frogs that eat pests.'),
     ('Use & value diversity', 'Many species in small numbers: a harvest most months.'), ('Apply self-regulation & accept feedback', 'Start with two or three guilds; expand what thrives.')]
pal = ['#e6efc4', '#f9d3c4', '#e3efc9', '#f3d6e2', '#f8efb8', '#d7ecd6', '#e6dcf1', '#d9def3', '#f8e1b8', '#f6cfcf', '#fbd9bf', '#d3e7ef']
fig = page('Twelve principles at Annwn', 'One line for each of Holmgren\'s design principles.', 'Principles: David Holmgren, Permaculture: Principles and Pathways Beyond Sustainability.')
for i, (t, s) in enumerate(P):
    x = .06 + (i % 4) * .225; y = .62 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .205, .21, boxstyle='round,pad=0.004,rounding_size=0.012', transform=fig.transFigure, fc=pal[i], ec='none'))
    fig.text(x + .012, y + .19, textwrap.fill(t, 24), fontsize=10.5, weight='bold', va='top'); fig.text(x + .012, y + .095, textwrap.fill(s, 30), fontsize=9, va='top', color='#333')
pdf.savefig(fig); plt.close(fig)

# 10 staging
fig = page('A staged order of work within $15,000', 'Water and the drain first, then running water, then food, with the carport last.', 'Costs are rough 2026 South-East Queensland retail ranges; get local quotes.')
ax = fig.add_axes([.06, .12, .88, .7]); ax.axis('off')
st = [('1 · Now', '$300–700', 'Locate the house drain · Before You Dig · soil test · free arborist mulch · pull Singapore daisy · worm farm'),
      ('2 · Summer 2027', '$3,000–4,800', '5,000 L slimline on the shed\'s south wall with a charged line · new pump and timer drip · move the clothes line'),
      ('3 · Autumn 2027', '$1,200–2,800', 'Rain-garden trench, creek and frog pond with a solar pump · seat pad from the pavers on hand'),
      ('4 · 2027–2028', '$5,800–12,500', 'Vegetable beds and paths · lemon myrtle and south-east screen · shed vine and foil · then the covered carport')]
for i, (a, c, w) in enumerate(st):
    y = .8 - i * .24; x = .02 + i * .04
    ax.add_patch(FancyBboxPatch((x, y), .9 - i * .04, .18, boxstyle='round,pad=0.005,rounding_size=0.02', fc=ACC if i == 0 else '#eef2f7', ec='none'))
    colr = 'white' if i == 0 else INK
    ax.text(x + .02, y + .12, a, fontsize=13, weight='bold', color=colr); ax.text(x + .02, y + .04, c, fontsize=10, color=colr)
    ax.text(x + .27, y + .09, textwrap.fill(w, 68), fontsize=10.5, color=colr, va='center')
pdf.savefig(fig); plt.close(fig)
pdf.close(); print('saved', OUT)

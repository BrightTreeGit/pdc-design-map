"""NAC design graphics (v2, 24 Oct 2026): Ange's updated plan, sectors, plan as drawn, rain, the real tank test, sun, slope, night temps,
plant light guide, principles and staging. Writes 'NAC design graphics.pdf' and 'NAC design on aerial.pdf' to OUTDIR."""
import textwrap, json, math, os, sys, numpy as np, matplotlib, datetime as dt
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Circle, Wedge, Polygon, Patch
from matplotlib.lines import Line2D
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nac_draw2 as D
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/nac_out'
os.makedirs(OUTDIR, exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
GREY, ACC, INK, SUB = '#b8b8b2', '#2f6fb3', '#222', '#666'
A4 = (11.69, 8.27)
S = json.load(open(os.path.join(D.SITE, 'silo_full.json')))
d0 = dt.date.fromisoformat(S['start']); R = np.array(S['rain10']) / 10.0; TN = np.array(S['tmin10']) / 10.0; TN[TN < -50] = np.nan
n = len(R); dates = [d0 + dt.timedelta(days=i) for i in range(n)]
mon = np.array([d.month for d in dates]); yrs = np.array([d.year for d in dates]); full = sorted(set(yrs))[:-1]
SIM = json.load(open(os.path.join(HERE, 'nac_sim2.json')))
M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ann = {y: R[yrs == y].sum() for y in full}; annmean = np.mean(list(ann.values()))

def page(title, sub, foot):
    fig = plt.figure(figsize=A4)
    fig.text(.06, .93, title, fontsize=19, weight='bold', color=INK)
    fig.text(.06, .895, textwrap.fill(sub, 150), fontsize=10.5, color=SUB, va='top', linespacing=1.3)
    fig.text(.06, .045, textwrap.fill(foot, 135), fontsize=7.5, color='#888', va='top', linespacing=1.3)
    fig.text(.94, .045, 'NAC · preliminary design · Oct 2026\nfirst names only', fontsize=7.5, color='#888', ha='right', va='top', linespacing=1.3)
    return fig

def runs(mask):
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0; best = max(best, cur)
    return best

pdf = PdfPages(os.path.join(OUTDIR, 'NAC design graphics.pdf'))

# 1 at a glance
fig = page('NAC at a glance', "North Arm Cove, Mid Coast NSW · the land, water and climate behind Ange's plan, updated with her answers and new plan (24 Oct 2026)",
           "Sources: NSW 5 m elevation and property register; SILO daily climate 1995–2026 (Qld Govt, CC BY 4.0); Ange's plan, sector map and answers; NSW Bush Fire Prone Land map.")
tiles = [('1,125 m²', 'block, about 66 m × 17 m'), ('2.5 m fall', 'gently to the north'), (f'{annmean:,.0f} mm', 'rain in an average year'),
         ('Aug–Oct', 'the dry gap: 17% of the rain'), ('35,000 L', '30 kL house tank + 5 kL garden tank'), ('BAL 29', 'house built to bushfire level 29'),
         ('24 kW solar', 'with battery; surplus sold'), ('0 frosts', f'in {len(full)} years; coldest {np.nanmin(TN):.1f} °C')]
for i, (big, small) in enumerate(tiles):
    x = .06 + (i % 4) * .225; y = .56 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .2, .2, boxstyle='round,pad=0.005,rounding_size=0.015', transform=fig.transFigure, fc='#f3f2ee', ec='none'))
    fig.text(x + .015, y + .11, big, fontsize=22, weight='bold', color=ACC if i in (4, 5) else INK)
    fig.text(x + .015, y + .05, small, fontsize=10, color=SUB, wrap=True)
fig.text(.06, .2, 'The big picture', fontsize=12, weight='bold')
fig.text(.06, .085, '• Water: the 30,000 L tank on 191 m² of roof carries the household (300 L/day) through every year since 1995, including 2019, with 9,900 L to spare.\n'
                    '• The 5,000 L garden tank on 36 m² waters about 20 m² of beds by can in any year, 40 m² in all but the driest; link the tanks for more.\n'
                    '• Sun under the gums is the limit for fruit: keep the sunny north-east for fruit and vegies, put guilds and shade herbs under the trees.\n'
                    '• Fire from the west and north-west, cold wind from the south-east, the view to the north-east: Ange\'s sectors set where screens and openings go.', fontsize=10, color=INK, linespacing=1.6)
pdf.savefig(fig); plt.close(fig)

# 2 site plan
fig = page("Ange's plan on the land", 'Everything from the updated plan fitted to the boundary and the house, with zones, contours and the 5 m root zone around the gums',
           'Positions about ±1 m. Contours from NSW 5 m elevation, smoothed. Root zone = within 5 m of a gum. Dashed = ideas not yet built.')
ax = fig.add_axes([.03, .2, .94, .66]); D.draw(ax, roots=True); D.north_scale(ax); ax.set_xlim(961, 1036); ax.set_ylim(-1016.5, -984)
ax.legend(handles=D.legend_handles(), loc='upper center', bbox_to_anchor=(.5, -.02), ncol=4, fontsize=7, frameon=False)
pdf.savefig(fig); plt.close(fig)

# 3 sectors
fig = page("Sectors: what comes at the block from where", "From Ange's sector map: fire from the west to north-west, cool and cold wind from the south to south-east, the view to the north-east, and the sun's arc",
           'Sun arcs calculated for 32.7° S (summer rises ESE, sets WNW; winter rises ENE, sets WSW). Sector angles as Ange drew them. Fire: block is mapped Bush Fire Prone Land.')
ax = fig.add_axes([.03, .07, .6, .8]); D.draw(ax, sectors=True, labels=False, contours=False, zones=True, idea_labels=False)
cx, cy = 1008.6, 1000.6
for r in (20, 40, 60): ax.add_patch(Circle((cx, -cy), r, fill=False, ec='#ccc', lw=.6, zorder=1))
for t, a in {'N': 0, 'E': 90, 'S': 180, 'W': 270}.items(): ax.text(cx + 66 * math.sin(math.radians(a)), -cy + 66 * math.cos(math.radians(a)), t, ha='center', va='center', weight='bold', fontsize=11)
for nm, a, c in [('FIRE\nW to NW', 288, '#e05a2b'), ('COLD WIND\nS to SE', 157, '#2f6fb3'), ('VIEW\nNE', 52, '#7a3b9a'), ('summer sun', 0, '#e9a820'), ('winter sun', 300, '#c0392b')]:
    rr = 50 if 'sun' not in nm else (68 if 'summer' in nm else 50); ax.text(cx + rr * math.sin(math.radians(a)), -cy + rr * math.cos(math.radians(a)), nm, ha='center', va='center', fontsize=9 if 'sun' not in nm else 8, color=c, weight='bold')
ax.set_xlim(cx - 72, cx + 72); ax.set_ylim(-cy - 72, -cy + 72)
fig.text(.66, .78, 'What the sectors mean for the design', fontsize=12, weight='bold')
fig.text(.66, .34, textwrap.fill('Fire (W–NW): the garage, driveway and west gum pocket face the fire side. Keep the asset protection zone there low and lean: short grass, no mulch piles '
                                 'against buildings, gutters clear, and the hose reach checked. The house is BAL 29.', 60) + '\n\n' +
         textwrap.fill('Cold wind (S–SE): the south verge and gum cluster already break it. A hedge or trellis along the south strip (Zone 2) shelters the herb bed and the banana guild.', 48) + '\n\n' +
         textwrap.fill('View (NE): keep the north-east corner open and low: fruit trees and the rock garden, nothing tall.', 48) + '\n\n' +
         textwrap.fill('Sun: the north and north-east ground gets the most winter sun; the gums to the south-east and west shade the ends of the block.', 48), fontsize=9, color=INK, va='bottom', linespacing=1.5)
pdf.savefig(fig); plt.close(fig)

# 4 plan as drawn
fig = page('The plan as drawn, and fitted to the land', "Left: Ange's sketch (1:200, address masked). Right: the same sketch warped onto the boundary and the house so each item lands where it is on the ground.",
           'Fitted with six boundary corners and four house corners (errors 0.4–1.5 m). The warped sketch is the "Ange\'s plan" overlay on the map.')
sk = Image.open(os.path.join(HERE, 'plan2_masked.jpg')); ax = fig.add_axes([.04, .18, .45, .66]); ax.imshow(sk); ax.axis('off')
ov = Image.open(os.path.join(HERE, 'ange_plan2.png')); oj = json.load(open(os.path.join(HERE, 'ange_plan2.json')))
ax2 = fig.add_axes([.51, .18, .46, .66]); ax2.set_facecolor('#eef1e6')
ax2.imshow(ov, extent=(oj['x0'], oj['x0'] + oj['w'] * oj['res'], -(oj['y0'] + oj['h'] * oj['res']), -oj['y0']), zorder=1)
ax2.add_patch(Polygon([D.X(p) for p in D.LOT], closed=True, fill=False, ec='#c0392b', lw=1.4, zorder=3)); ax2.set_xlim(961, 1036); ax2.set_ylim(-1016.5, -984); ax2.set_aspect('equal'); ax2.axis('off')
ax2.text(961, -983, 'Red: property boundary from the NSW register', fontsize=7.5, color='#c0392b')
pdf.savefig(fig); plt.close(fig)

# 5 rain
mean = [R[mon == m].sum() / len(full) for m in range(1, 13)]
med = [np.median([R[(mon == m) & (yrs == y)].sum() for y in full]) for m in range(1, 13)]
fig = page('Rain falls mostly February to July', 'Monthly rainfall, mm: bars show a typical (median) month, ticks the average. August–October is the dry gap, just as spring growth starts.',
           f'SILO gridded daily rainfall at the block, {full[0]}–{full[-1]} (Queensland Government, CC BY 4.0).')
ax = fig.add_axes([.08, .14, .86, .68])
ax.bar(M, med, color=[ACC if m in (8, 9, 10) else GREY for m in range(1, 13)], width=.62)
for i, (md, mn) in enumerate(zip(med, mean)):
    ax.plot([i - .36, i + .36], [mn, mn], color='#555', lw=2); ax.text(i, md / 2, f'{md:.0f}', ha='center', color='white', fontsize=10, weight='bold')
ax.set_yticks([]); [ax.spines[s].set_visible(False) for s in ('top', 'right', 'left')]
dmax = max(R); dmax_i = int(np.argmax(R)); big = (R >= 50).sum() / len(full); dry = runs(R < 1)
ax.text(11.4, max(mean) * .98, f'Driest year: {min(ann, key=ann.get)}, {min(ann.values()):.0f} mm · wettest {max(ann, key=ann.get)}, {max(ann.values()):.0f} mm\nWettest day: {dmax:.0f} mm ({dates[dmax_i]:%b %Y})\nAbout {big:.0f} days a year bring 50 mm+ · longest dry spell {dry} days', ha='right', va='top', fontsize=9.5, color=SUB)
pdf.savefig(fig); plt.close(fig)

# 6 tank test
fig = page("The tank test with Ange's real set-up", 'Share of water needs met, every day 1995–2026: the 30,000 L house tank on 191 m² of roof, and the 5,000 L garden tank on 36 m².',
           'Daily simulation: SILO rain and FAO56 reference evapotranspiration; 85% of roof rain reaches the tank; beds watered by can from a soil-moisture balance (25 mm store, crop factor 0.6). A guide, not a guarantee.')
ax = fig.add_axes([.06, .12, .88, .72]); ax.axis('off')
rows = [('House tank 30,000 L · 191 m² roof', None), ('household 200 L/day', SIM['house_200']), ('household 300 L/day', SIM['house_300']), ('household 400 L/day', SIM['house_400']),
        ('Garden tank 5,000 L · 36 m² roof', None), ('watering 20 m² of beds', SIM['garden_20']), ('watering 40 m² of beds', SIM['garden_40']), ('watering 80 m² of beds', SIM['garden_80']),
        ('House tank also watering the garden (300 L/day)', None), ('+ 40 m² of beds', SIM['combined_40']), ('+ 80 m² of beds', SIM['combined_80']),
        ('Both tanks linked: 35,000 L on 227 m²', None), ('300 L/day + 40 m² of beds', SIM['all_linked'])]
hdr = ['Scenario', 'Needs met', 'Short days / year', 'Longest run short', 'Lowest in 2019']
for j, h in enumerate(hdr): ax.text([.0, .5, .64, .79, .93][j], .97, h, fontsize=9.5, weight='bold', ha='left' if j == 0 else 'right', color=SUB)
y = .91
for nm, r in rows:
    if r is None: ax.text(0, y, nm, fontsize=10.5, weight='bold', color=INK); y -= .065; continue
    met = r['met']; c = '#2e7d32' if met >= .999 else ('#e08a1e' if met >= .97 else '#c0392b')
    ax.text(.03, y, nm, fontsize=10); ax.add_patch(FancyBboxPatch((.33, y - .012), .11 * met, .028, boxstyle='square,pad=0', fc=c, ec='none'))
    ax.text(.5, y, f'{met*100:.0f}%', fontsize=10, ha='right', color=c, weight='bold'); ax.text(.64, y, f'{r["short_days_per_yr"]:.1f}', fontsize=10, ha='right')
    ax.text(.79, y, f'{r["longest_short"]} days' + (f' ({r["longest_end"][:7]})' if r['longest_short'] else ''), fontsize=10, ha='right')
    ax.text(.93, y, f'{r["low2019"]:,.0f} L' if r['low2019'] else 'empty', fontsize=10, ha='right'); y -= .058
ax.text(0, .02, f'Roof yield in an average year: 191 m² → {annmean*191*.85:,.0f} L; 36 m² → {annmean*36*.85:,.0f} L. The house tank has spare: linking it to the garden tap is the cheap way to water more beds.', fontsize=9.5, color=INK)
pdf.savefig(fig); plt.close(fig)

# 7 sun and shade
fig = page('Winter sun is low: shadows fall long to the south', 'At 32.7° S a 25 m gum casts a 37 m noon shadow in midwinter but only 4 m in midsummer. Trees on the north and east cost the garden the most sun.',
           'Sun positions calculated for 32.7° S. Shadow length = tree height ÷ tan(sun height). Tree heights are examples; confirm on site.')
ax = fig.add_axes([.06, .12, .5, .72]); lat = math.radians(-32.67)
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
ax2 = fig.add_axes([.62, .18, .33, .6]); alts = {'Midwinter': 33.9, 'Equinox': 57.3, 'Midsummer': 80.7}
for i, (k, a) in enumerate(alts.items()):
    L = 25 / math.tan(math.radians(a)); ax2.barh(i, L, color=ACC if k == 'Midwinter' else GREY, height=.55); ax2.text(L + .8, i, f'{L:.0f} m', va='center', fontsize=10)
ax2.set_yticks(range(3)); ax2.set_yticklabels(list(alts)); ax2.invert_yaxis(); ax2.set_xticks([]); [ax2.spines[s].set_visible(False) for s in ('top', 'right', 'bottom')]
ax2.set_title('Noon shadow of a 25 m gum', fontsize=10, color=SUB); ax2.text(0, 3.0, 'The block is only 17 m deep, so one tall tree\nnorth of the beds can shade them all winter.', fontsize=9, color=INK)
pdf.savefig(fig); plt.close(fig)

# 8 slope profile
z = lambda x, y: D.DEM[int(y - D.d1['y0']), int(x - D.d1['x0'])]
fig = page('A gentle, even slope to the north', 'Cross-section from the south boundary to the north boundary through the house and through the fruit area (height above sea level).',
           'NSW 5 m elevation from aerial photos (smooths out small banks and terraces). Vertical scale exaggerated ×4. Check falls on site with a level.')
ax = fig.add_axes([.08, .16, .86, .64])
for x0, nm, c in [(1008, 'Through the house', GREY), (1020, 'Through the fruit trees', ACC)]:
    ys = np.linspace(1010.5, 995.5, 16); zz = [z(x0, y) for y in ys]; ax.plot(ys[0] - ys, zz, color=c, lw=2.6, label=nm)
ax.set_xlabel('Distance from the south boundary (m)  →  north', color=SUB); ax.set_ylabel('Height (m)', color=SUB); ax.set_aspect(4); [ax.spines[s].set_visible(False) for s in ('top', 'right')]; ax.legend(frameon=False)
ax.text(.02, .97, 'South boundary (higher)', transform=ax.transAxes, fontsize=9, color=SUB); ax.text(.99, .2, 'North (lower, sunnier)', transform=ax.transAxes, ha='right', fontsize=9, color=SUB)
pdf.savefig(fig); plt.close(fig)

# 9 night temps
mmin = [np.nanmean(TN[mon == m]) for m in range(1, 13)]; low = [np.nanmin(TN[mon == m]) for m in range(1, 13)]
fig = page('Mild, frost-free winters', 'Average night-time minimum by month, with the coldest night recorded. No frost in 31 years, so citrus, banana and bush foods are safe; plums need low-chill varieties.',
           f'SILO gridded daily minimum temperature at the block, {full[0]}–{full[-1]}.')
ax = fig.add_axes([.08, .14, .86, .68]); ax.bar(M, mmin, color=[ACC if m in (6, 7, 8) else GREY for m in range(1, 13)], width=.62); ax.scatter(range(12), low, color='#555', zorder=5, s=18)
for i, (a, l) in enumerate(zip(mmin, low)): ax.text(i, a + .5, f'{a:.1f}°', ha='center', fontsize=9.5)
ax.text(6, low[6] - 1.6, f'coldest {min(low):.1f}°', ha='center', fontsize=8.5, color='#555'); ax.axhline(0, color='#c0392b', lw=.8); ax.text(11.4, .4, 'frost line', color='#c0392b', fontsize=8.5, ha='right')
ax.set_yticks([]); ax.set_ylim(-2, 22); [ax.spines[s].set_visible(False) for s in ('top', 'right', 'left')]
pdf.savefig(fig); plt.close(fig)

# 10 plant light guide
fig = page('Right plant, right light', "Where each plant on Ange's plan, and some suggested additions, will do best on this shaded bush block.",
           'Additions in italics. Root reach: keep thirsty fruit more than about 5 m from large gums. Banana guild: banana, comfrey, nasturtium, sweet potato.')
ax = fig.add_axes([.06, .1, .88, .74]); ax.axis('off')
cols = [('Full sun, 6 h+\n(north-east ground, outside gum roots)', ['Plum ×2 (low-chill)', 'Mandarin', 'Orange', 'Raised vegie beds ×4', 'Dwarf mulberry'], '#f6d77a'),
        ('Sun to part shade', ['Yuzu', 'Cumquat', 'Lemon myrtle, cinnamon myrtle', 'Banksia, leucadendron', 'Banana guild (south strip)', '*Finger lime*'], '#cfe5b4'),
        ('Part shade, under the gums\n(south-west guild, forest edge)', ['Herb bed and spiral (south side)', '*Midyim berry*', '*Native raspberry*', '*Warrigal greens*', '*Davidson plum*', '*Lomandra, dianella (fire-wise)*'], '#a9cfa0')]
for i, (h, items, c) in enumerate(cols):
    x = i / 3 + .01; ax.add_patch(FancyBboxPatch((x, .02), .3, .95, boxstyle='round,pad=0.005,rounding_size=0.02', fc=c, ec='none', alpha=.55)); ax.text(x + .015, .9, h, fontsize=11.5, weight='bold', va='top')
    for j, it in enumerate(items): ax.text(x + .02, .7 - j * .1, '• ' + it.strip('*'), fontsize=11, style='italic' if it.startswith('*') else 'normal')
pdf.savefig(fig); plt.close(fig)

# 11 principles
P = [('Observe & interact', "Ange's sector map and 35 answers; a winter sun log before the next planting."), ('Use small & slow solutions', 'Verge breaks by hand; one guild at a time.'),
     ('Catch & store energy', '35 kL tanks, 24 kW solar with battery, verge soaks, mulch.'), ('Design from patterns to details', 'Sectors and zones first; plants last.'),
     ('Creatively use & respond to change', 'BAL 29 house; fire-wise west side; drier springs.'), ('Obtain a yield', 'Vegies, herbs, citrus, plums, mulberry, bananas, bush foods.'),
     ('Produce no waste', 'Scraps to compost; laundry water to the fruit trees.'), ('Use & value renewable resources', 'Gum-leaf mulch, rainwater, sun, birds and bees.'),
     ('Use edges & value the marginal', 'Guild under the gums; verge soaks; herbs on the shady side.'), ('Integrate rather than segregate', 'Guilds; tanks linked; garage roof feeds the garden tank.'),
     ('Use & value diversity', 'Exotic fruit, bush foods, natives and herbs in layers.'), ('Apply self-regulation & accept feedback', 'Watch tank levels each spring; expand what thrives.')]
pal = ['#e6efc4', '#f9d3c4', '#e3efc9', '#f3d6e2', '#f8efb8', '#d7ecd6', '#e6dcf1', '#d9def3', '#f8e1b8', '#f6cfcf', '#fbd9bf', '#d3e7ef']
fig = page('Twelve principles at NAC', "One line for each of Holmgren's design principles, for the group presentation.", 'Principles: David Holmgren, Permaculture: Principles and Pathways Beyond Sustainability.')
for i, (t, s) in enumerate(P):
    x = .06 + (i % 4) * .225; y = .62 - (i // 4) * .25
    fig.patches.append(FancyBboxPatch((x, y), .205, .21, boxstyle='round,pad=0.004,rounding_size=0.012', transform=fig.transFigure, fc=pal[i], ec='none'))
    fig.text(x + .012, y + .19, textwrap.fill(t, 24), fontsize=10.5, weight='bold', va='top'); fig.text(x + .012, y + .095, textwrap.fill(s, 30), fontsize=9, va='top', color='#333')
pdf.savefig(fig); plt.close(fig)

# 12 staging
fig = page('A staged order of work', 'Each stage is done once and done well, and tells you something before spending on the next.', 'Costs are rough 2026 retail ranges; get local quotes.')
ax = fig.add_axes([.06, .12, .88, .7]); ax.axis('off')
st = [('1 · Now (spring)', 'mostly free', 'Verge breaks (plan item 1) · spiral herb garden · banana guild in the south strip · fire pit clearance checked · gutters and leaf guards checked before summer'),
      ('2 · Before summer', '$200–800', 'Link the house tank to the garden tap (valve or small pump) · first-flush diverter · mulch the fruit trees · hose from the laundry made permanent (ag pipe)'),
      ('3 · Autumn 2027', '$300–1,000', 'Guild under the south-west gums (dry shade: lomandra, dianella, midyim, native raspberry) · soil test the beds · compost in use'),
      ('4 · Later', 'as budget allows', 'Pond (place to choose) · stone oven · more bush foods · native bees · a hedge on the south-east wind side')]
for i, (a, c, w) in enumerate(st):
    y = .8 - i * .24; x = .02 + i * .04
    ax.add_patch(FancyBboxPatch((x, y), .9 - i * .04, .18, boxstyle='round,pad=0.005,rounding_size=0.02', fc=ACC if i == 0 else '#eef2f7', ec='none')); colr = 'white' if i == 0 else INK
    ax.text(x + .02, y + .12, a, fontsize=13, weight='bold', color=colr); ax.text(x + .02, y + .04, c, fontsize=10, color=colr); ax.text(x + .25, y + .09, textwrap.fill(w, 72), fontsize=10.5, color=colr, va='center')
pdf.savefig(fig); plt.close(fig)
pdf.close(); print('saved graphics')

# ---- NAC design on aerial.pdf ----
pdf = PdfPages(os.path.join(OUTDIR, 'NAC design on aerial.pdf'))
ins = json.load(open(os.path.join(HERE, 'inset.json'))); aer = Image.open(os.path.join(HERE, 'nac_closeup_2021.jpg'))
ext = (ins['x0'], ins['x0'] + ins['w'] * ins['res'], ins['y0'], ins['y0'] + ins['h'] * ins['res'])
fig = page("Ange's design on the aerial photo", 'Features and zones over the NSW aerial photo of the block (captured 1 Sep 2021, before the house was built in 2024). Yellow line: the property boundary.',
           'Aerial: NSW Spatial Services imagery, captured 1 Sep 2021, 7 cm (CC BY 4.0). Boundary: NSW property register. Features: Ange\'s plan, fitted ±1 m. Lot plus about 30 m shown.')
ax = fig.add_axes([.03, .2, .94, .66]); D.draw(ax, base=(aer, ext), contours=False, roots=False, zone_labels=False, lw_scale=1.1); D.north_scale(ax, x=1058, y=975, sx=940, sy=1038)
ax.set_xlim(936, 1063); ax.set_ylim(-1042, -957)
ax.legend(handles=D.legend_handles(), loc='upper center', bbox_to_anchor=(.5, -.02), ncol=4, fontsize=7, frameon=False)
pdf.savefig(fig); plt.close(fig)
# page 2: zones only, lot + 30 m
fig = page('Zones on the aerial photo', 'Zone 1 daily (vegie beds, herbs); Zone 2 fruit and guilds; Zone 3 natives and rock garden; Zone 4 the gum pockets, kept wild. Sectors as Ange drew them.',
           'Aerial: NSW Spatial Services imagery, captured 1 Sep 2021 (CC BY 4.0). Zones and sectors from Ange\'s plan and sector map, Oct 2026.')
ax = fig.add_axes([.03, .2, .94, .66]); D.draw(ax, base=(aer, ext), contours=False, roots=False, labels=False, sectors=True, lw_scale=1.1); D.north_scale(ax, x=1058, y=975, sx=940, sy=1038)
ax.set_xlim(936, 1063); ax.set_ylim(-1042, -957)
for fid, f in D.F.items():
    if f['kind'].startswith('zone'):
        pts = np.array(f['geom']['pts']); cx, cy = pts.mean(0); ax.text(cx, -cy, f['name'].split('·')[0].strip().replace('Zone ', 'Z'), fontsize=8, color='white', ha='center', va='center', weight='bold', zorder=9, path_effects=[matplotlib.patheffects.withStroke(linewidth=2.5, foreground='black')])
ax.legend(handles=[Patch(fc=D.ZCOL['zone1'], label='Zone 1'), Patch(fc=D.ZCOL['zone2'], label='Zone 2'), Patch(fc=D.ZCOL['zone3'], label='Zone 3'), Patch(fc=D.ZCOL['zone4'], label='Zone 4'),
                   Patch(fc='#e05a2b', alpha=.3, label='Fire sector (W–NW)'), Patch(fc='#4f8fc9', alpha=.3, label='Cold wind (S–SE)'), Patch(fc='#7a3b9a', alpha=.3, label='View (NE)'),
                   Line2D([], [], color='#e9a820', lw=2, label='Summer sun arc'), Line2D([], [], color='#c0392b', lw=2, label='Winter sun arc')], loc='upper center', bbox_to_anchor=(.5, -.02), ncol=5, fontsize=7.5, frameon=False)
pdf.savefig(fig); plt.close(fig)
pdf.close(); print('saved aerial')

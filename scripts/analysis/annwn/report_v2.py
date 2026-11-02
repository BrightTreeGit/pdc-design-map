"""Annwn preliminary design report, version 2 (2 Nov 2026).

Rebuilds the report from Bronwen's interview answers (27 Oct 2026) and the 1983 council house-drainage plan.
Writes a .docx (styles reused from version 1) and a tank chart PNG. Convert to PDF with LibreOffice afterwards.
PRIVACY: shared output. First names only, no street address, no lot or plan numbers, no health details.
"""
import json, datetime as dt, copy
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import docx
from docx.shared import Cm, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT

SCR = '/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/'
OUT = '/home/claude/annwn-out/v2/'
SITE = '/home/claude/pdc-design-map/map/sites/annwn/'
import os; os.makedirs(OUT, exist_ok=True)

# ---------- tank model (same daily method as the map's tank calculator) ----------
S = json.load(open(SITE + 'soils.json')); A = S['centre']['AWC']
SC = sum(A[k] * w for k, w in [('0-5', 50), ('5-15', 100), ('15-30', 150)]) / 100
D = json.load(open(SITE + 'rain_daily.json')); Fu = json.load(open(SITE + 'silo_full.json'))
r = D['rain10']; d0 = dt.date.fromisoformat(D['start']); off = (d0 - dt.date.fromisoformat(Fu['start'])).days; e = Fu['eto10']

def sim(cfg, garden=120):
    st = [s for _, s in cfg]; soil = SC; sup = dem = 0; yr = {}
    for i, v in enumerate(r):
        rain = v / 10; y = (d0 + dt.timedelta(i)).year
        for k, (roof, cap) in enumerate(cfg): st[k] = min(cap, st[k] + rain * roof * .85)
        ev = e[i + off] / 10 if i + off < len(e) and e[i + off] >= 0 else 3
        soil = min(SC, soil + rain) - ev * .6; need = -soil if soil < 0 else 0; soil = max(soil, 0)
        want = need * garden
        if want > 0:
            take = 0
            for k in range(len(st)):
                t = min(st[k], want - take); st[k] -= t; take += t
            sup += take; dem += want; Y = yr.setdefault(y, [0, 0]); Y[0] += take; Y[1] += want
    return sup / dem, yr[2019][0] / yr[2019][1]

SCEN = [('Now: 3,000 L on the carport', [(70, 3000)]),
        ('Add 5,000 L on the shed, shed roof only', [(70, 3000), (37, 5000)]),
        ('Add 5,000 L on the shed + charged line from the house', [(70, 3000), (77, 5000)]),
        ('Later: swap the old 3,000 L for a new 5,000 L', [(70, 5000), (77, 5000)])]
RES = [(n, *sim(c)) for n, c in SCEN]

fig, ax = plt.subplots(figsize=(9, 3.6), dpi=170)
y = np.arange(len(RES))[::-1]
ax.barh(y + .18, [x[1] * 100 for x in RES], .34, color='#2f6fb3', label='Typical year')
ax.barh(y - .18, [x[2] * 100 for x in RES], .34, color='#9cc0e6', label='2019 drought year')
for yy, x in zip(y, RES):
    ax.text(x[1] * 100 + 1, yy + .18, f'{x[1]:.0%}', va='center', fontsize=8.5, color='#1d4f86')
    ax.text(x[2] * 100 + 1, yy - .18, f'{x[2]:.0%}', va='center', fontsize=8.5, color='#5a7fa8')
ax.set_yticks(y); ax.set_yticklabels([x[0] for x in RES], fontsize=8.5); ax.set_xlim(0, 105)
ax.set_xlabel("Share of a 120 m² garden's watering met from the tanks (%)", fontsize=8.5)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
ax.legend(fontsize=8, frameon=False, loc='lower right')
ax.set_title('A new 5,000 L tank on the shed, linked to the house roof, does most of the work', fontsize=10, loc='left', weight='bold')
fig.text(.01, .005, 'Day-by-day run through SILO rainfall and evaporation at the block, 1995–2026, with the top 30 cm of soil as a buffer.', fontsize=6.8, color='#666')
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(OUT + 'annwn-tank-chart-v2.png', facecolor='white'); plt.close(fig)

# ---------- document ----------
doc = docx.Document('/home/claude/annwn-out/Annwn preliminary design report.docx')
body = doc.element.body
for el in list(body):
    if el.tag.endswith('sectPr'): continue
    body.remove(el)

H = lambda t, l=1: doc.add_heading(t, l)
def P(t='', bold_lead=None):
    p = doc.add_paragraph()
    if bold_lead: p.add_run(bold_lead).bold = True
    p.add_run(t); return p
def B(t, lead=None):
    p = doc.add_paragraph(style='List Paragraph')
    p.paragraph_format.left_indent = Cm(.6); p.paragraph_format.first_line_indent = Cm(-.4)
    p.add_run('•  ')
    if lead: p.add_run(lead).bold = True
    p.add_run(t); return p
def TBL(head, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(head)); t.style = 'Table Grid' if 'Table Grid' in [s.name for s in doc.styles] else None
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ''; run = c.paragraphs[0].add_run(h); run.bold = True; run.font.size = Pt(9)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ''; run = cells[i].paragraphs[0].add_run(str(v)); run.font.size = Pt(9)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    doc.add_paragraph(); return t
def IMG(path, w=16, cap=None):
    doc.add_picture(path, width=Cm(w))
    if cap:
        p = doc.add_paragraph(); run = p.add_run(cap); run.italic = True; run.font.size = Pt(8.5); run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

now_s, sh_s, link_s, later_s = RES[0][1], RES[1][1], RES[2][1], RES[3][1]

doc.add_heading('Annwn: preliminary design report (version 2)', 0)
P('2 November 2026 · Brett · updated with Bronwen\'s answers and the council house-drainage plan')

H('Summary')
P('Annwn can become the peaceful, joyful sanctuary Bronwen describes and grow about half of her food, inside her $15,000 budget, '
  'if the work is done in the right order: water and the sewer first, then the creek and pond, then the vegetable garden, with the carport move last.')
B(f'The sewer is now confirmed. It runs about 1 m inside the back (north) and east fences to the manhole in the north-east corner, about 2.2 m deep there. '
  'A house drain also runs along the house\'s east wall and across to the manhole. Annual vegetables can grow right over the sewer band; trees go 5 m or more away.', 'Sewer: ')
B(f'Only the 3,000 L tank on the carport is working, and it is about 30 years old with a 20-year-old pump. '
  f'Bronwen\'s idea of a new 5,000 L slimline on the big shed\'s south wall works well. Linked to a house downpipe, it lifts the garden from about {now_s:.0%} to about {link_s:.0%} tank water in a typical year.', 'Water: ')
B('Her first priority, a small creek running to a pond, fits the sunny grass north of the carport. It can be fed by the soggy west side and the neighbour\'s patio runoff, '
  'with a small solar pump keeping it running on fine days.', 'Running water: ')
B('About 50 m² of raised and wicking beds in full sun north of the big shed, plus the existing fruit trees and a few more, is a realistic path to half her food.', 'Food: ')
B('A covered carport in the south-west corner is possible but is the biggest single cost and needs council permits (a new driveway crossover, and the water meter sits there).', 'Car parking: ')
P('What changed since version 1: the sewer position (confirmed, and now on two sides), the tank plan (the earlier spots A and B are out), '
  'the soggy spots, the wind, the budget and Bronwen\'s priorities. Everything is on the trial design map as the "Annwn" site.')

IMG(SCR + 'bron2/annwn-design-plan.png', 15.5, 'The updated plan. Colours show what can grow where, measured from the sewer main and the house drain. Positions are approximate until the drain is located on site.')

H('What Bronwen told us, and what it means')
TBL(['She said', 'Design response'], [
    ('A peaceful, joyful sanctuary that provides at least 50% of my food', 'Garden "rooms" with a pond and seats, plus about 50 m² of productive beds in full sun and the fruit already growing'),
    ('Lush, easy to move around, ordered in the main vegetable areas', 'Wide, level, firm paths; beds in straight rows in the vegetable room; the lush planting around the pond and edges'),
    ('Taller trees and shrubs, sun-filled areas in winter, "rooms" so you don\'t see everything at once', 'Shrub screens divide the block into rooms; tall plants kept to the south and east edges so winter sun reaches the beds and seats'),
    ('About 8 hours a week now, more from the new year; help needed with heavy manual work', 'Low-lift garden: waist-high beds, no ladders, drip on a timer, mulch delivered close to where it is used; the handyman does the digging jobs'),
    ('Priorities: 1 running water, a small creek to a pond; 2 covered car parking in the south-west corner', 'Creek and pond come first in the staged plan; the carport is planned for when the budget allows'),
    ('$15,000 over the next few years; a mix of do-it-yourself and hired help', 'Staged budget below, with the jobs split between Bronwen and the handyman'),
    ('Pavers (about 10 m²) and stepping stones on hand', 'Used for the seat pad by the pond and stepping stones through the beds'),
    ('Water collects on the west side (worst at the north-west corner) and along the front east of the driveway', 'A rain-garden trench on the west side; moisture-tolerant screen plants at the front'),
    ('Wind from the south-east most of the year, from the west in August; privacy and a windbreak needed in the south-east corner', 'A low native screen and a lemon myrtle in the south-east corner'),
    ('Full sun on the grass north of the carport and south of the big shed, and on the shed\'s north side; the front yard is shaded in winter', 'Vegetables and pond in the sun; the front becomes a shade garden'),
    ('The big shed\'s west wall feels hottest; ideas for insulation please', 'Vine screen outside plus foil insulation inside (see the shed section)'),
    ('Tank water for the garden only, not toilets or the washing machine; ideas for washing-machine greywater', 'Tanks sized for the garden; a simple greywater hose option and a plumber-fitted option'),
    ('Solar 2.5 kW, no battery, exporting most of it; an electric car is planned', 'Run the pond and tank pumps by day; plan a bigger system when the car comes'),
    ('Possums, bats, birds, frogs, toads, skinks and a family of blue-tongues; two native bee hives; wants more birds; no European bees', 'Frog-friendly pond, bird-attracting natives, no garden chemicals'),
    ('Include a lemon myrtle tree', 'In the south-east corner, kept hedged to about 3 m'),
], widths=[7.5, 9])

H('The site, updated')
P('Annwn is a 770 m² corner block in Capalaba, about 22 m wide and 35 m deep, with streets on the south and east. The ground falls gently (2–3%) from the house pad, about 22.5 m above sea level, east and north to the back corner at 21.0 m.')
B('the house with 2.5 kW of solar in the south-west, and the carport on its south-east corner (the original 1983 garage position).', 'Buildings: ')
B('the big shed in the back yard, with its roller door facing east and a standard door 1–2 m from the south-east corner on the south side; the small shed by the west fence.', 'Sheds: ')
B('Bronwen has lived here 17 years. It was all grass with six palm trees; she has added the retaining walls along the east side, the fruit trees, the wicking beds and the hedges.', 'History: ')
B('colour-bond fencing all round, which gives a solid wall for the wind to hit and some reflected heat.', 'Fences: ')

H('Sewer and drains', 2)
P('Bronwen confirmed the dashed lines on her sketch are the sewer, and the council\'s 1983 house-drainage plan shows the same thing:')
B('the sewer main runs about 1 m inside the back (north) fence and the east fence, meeting at the manhole in the north-east corner. The plan gives the surface there as 21.96 m and the pipe at 19.79 m, so the pipe is about 2.2 m deep at the manhole. It was last inspected about 6 years ago.', 'Main: ')
B('the house drain runs along the house\'s east wall, then diagonally across to the manhole. It is shallower than the main and, read off the plan, may pass under the big shed\'s south-east corner and near the new tank spot.', 'House drain: ')
B('the water meter is in the south-west corner and the water line runs across the front of the house before turning north into it.', 'Water service: ')
P('Before digging the pond or pouring a tank base, have a plumber locate the house drain with a locator or camera (about $200–300), and lodge a free Before You Dig Australia enquiry. '
  'A deep main is good news: roots rarely reach a pipe 2 m down, so the risk is mostly from the shallower house drain and the junctions.')
TBL(['Distance from a sewer line', 'What fits'], [
    ('Over the pipe and up to 2 m', 'Vegetables, herbs, raised and wicking beds, groundcovers, pots, seats. Nothing woody. Keep the manhole clear.'),
    ('2–5 m', 'Small shrubs and dwarf fruit kept under 2.5 m: Tahitian lime, dwarf citrus, jaboticaba, pomegranate, native shrubs'),
    ('5 m and more', 'Stronger-rooted fruit: avocado, custard apple, dwarf mango, larger citrus'),
    ('Not on this block', 'Figs, umbrella tree, poinciana, camphor laurel, eucalypts, running bamboo, large weeping bottlebrush'),
], widths=[5, 11.5])
P('The citrus and jaboticaba along the east side sit 2–5 m from the east main, which is fine for small trees kept pruned. The callistemon is on most councils\' keep-away lists; if drains ever run slowly, a camera check is the first step.')

H('Ground, sun and wind', 2)
IMG('/home/claude/annwn-out/annwn-ground-plan.png', 13, 'How the ground falls: 0.25 m contours from the 1 m Queensland LiDAR.')
B('the back yard drains to the north-east corner and the front to the street. The soggy west side is low against the house pad and takes the neighbour\'s patio water.', 'Water on the ground: ')
B('at 27.5° S the midwinter noon sun is 39° up, so the house shades the front yard all winter. Full sun is on the grass north of the carport, south of the big shed and along the shed\'s north side.', 'Sun: ')
B('from the south-east most of the year and from the west in August. A screen in the south-east corner shelters the pond and seats.', 'Wind: ')
B('still unknown. The modelled soil grid suggests sandy clay loam over heavier clay, which fits the soggy spots. A soil test (pH, nutrients, and lead, as on any older suburban block) is the first job; a kit or lab test costs $40–120.', 'Soil: ')

H('Water: tanks')
P(f'With the 2,000 L tank out of use, Annwn runs on one 3,000 L tank, which meets only about {now_s:.0%} of a 120 m² garden\'s watering in a typical year. '
  'The tank is about 30 years old and the pump about 20, so both are near the end of their life.')
IMG(OUT + 'annwn-tank-chart-v2.png', 16)
TBL(['Set-up', 'Typical year', '2019 drought'], [(n, f'{a:.0%}', f'{b:.0%}') for n, a, b in RES], widths=[10, 3, 3])
P('Recommendation:')
B('a 5,000 L slimline (about $1,600–2,400) along the big shed\'s south wall, west of the door, where the clothes line is now. It takes the shed roof and a "charged" line from the nearest house downpipe: a pipe that runs underground and rises into the tank, so the house roof fills it too.', 'Bronwen\'s spot works: ')
B('a full 5,000 L tank weighs over 5 tonnes. It needs a level compacted base and must not sit on the house drain, so locate the drain first and slide the tank west if needed.', 'Check first: ')
B('the clothes line can move to a fold-down line on the house\'s west wall, or under the old carport once the cars move.', 'Clothes line: ')
B('one new pump with automatic mains switch-over ($450–900), drip lines on a tap timer ($60–150), leaf guards and first-flush diverters.', 'Pump and drip: ')
B('when the old 3,000 L tank fails, replace it with another 5,000 L to reach about 92%. If the 2,000 L tank is sound (no light through the walls, no cracks), it can serve the pond as a header or top-up tank.', 'Later: ')
P('A domestic tank in Queensland needs no building approval unless it is both over 10 m² in plan and over 2.4 m tall. Check Redland\'s rules for the exact spot, and whether a rebate is running.')

H('Running water: the creek and frog pond')
P('This is Bronwen\'s first priority, and it solves the soggy west side at the same time.')
B('a shallow gravel trench with a slotted pipe along the west side of the house catches the neighbour\'s patio runoff and the soggy strip. Edge it with moisture-lovers (ginger, turmeric, lomandra, native violet).', 'Catch it: ')
B('a pipe along the north side of the house carries the surplus to a small rocky creek, about 4–5 m long, lined with pond liner and river stones, running down to the pond.', 'Lead it: ')
B('about 2.5 × 2 m in the sunny grass north of the carport, 40–50 cm deep in the middle, with a shallow pebble beach and rocks for frogs and skinks. Native Pacific blue-eye fish keep mosquito larvae down. Keep it 1.5 m or more off the house drain.', 'The pond: ')
B('a small pond pump (25–40 W) on a timer during the day, run from the house solar, lifts water back to the creek head so it runs on fine days. A stand-alone solar pond pump kit ($150–300) avoids any wiring.', 'Keep it running: ')
B('the pond overflows to a mulched rain-garden dip, then on through the yard\'s natural fall to the north-east, not onto the sewer manhole.', 'In big storms: ')
P('About the neighbour\'s patio water: asking her to drain it to the street is fair, but catching it in the trench turns a nuisance into the creek\'s supply. Water must not then be passed back onto her side.')
P('Rough cost: $1,200–2,800 for liner, rock, pump, trench, pipe and plants, less with the pavers and stepping stones on hand.')

H('Car parking in the south-west corner')
B('a single carport is roughly 3 × 6 m. A kit costs $2,500–6,000, plus a concrete slab or gravel pad, plus a new driveway crossover.', 'Size and cost: ')
B('Redland City Council needs a permit for any new or changed driveway crossover. Relocating a water meter needs a separate council assessment first, and the meter is in the south-west corner. A carport also needs a building approval through a private certifier.', 'Permits: ')
B('the old carport becomes a covered outdoor room, a dry spot for the clothes line, or potting space, and the old driveway strip can become garden.', 'What it frees up: ')
P('This is the largest item on the list and could take a third or more of the $15,000. It is placed last so the water, pond and food garden come first.')

H('Food: growing half of it')
P('Half of one person\'s fruit and vegetables is realistic on this block with about 50 m² of well-run beds and the fruit trees already in. The plan:')
B('raised and wicking beds along the north side of the big shed, in full sun all year. They sit over the sewer band, which suits annual vegetables; no deep digging, and keep the manhole clear.', 'Main vegetable garden: ')
B('the existing wicking beds by the clothes line and on the east side for salad greens and herbs, close to the back door.', 'Kitchen beds: ')
B('a worm farm by the back door turns scraps into castings for the beds.', 'Worm farm: ')
P('Bronwen\'s list, placed for this block:')
TBL(['She eats', 'Where it grows best'], [
    ('Bananas, pineapple', 'Bananas 3 m+ from the sewer in the sunny back yard; pineapples in the beds and along path edges'),
    ('Stone fruit', 'Only low-chill types (e.g. \'Tropic Beauty\' peach, \'Sherriff\' or \'Gulf\' nectarine), kept small, netted against fruit fly; in the green zone 5 m+ from the sewer'),
    ('Citrus, custard apple', 'Citrus already along the east side; a custard apple in the green zone west of the big shed'),
    ('Asian greens, lettuce, kale, silverbeet, broccoli, alliums', 'The main vegetable garden; brassicas and lettuce in the cool season (March–August)'),
    ('Sweet potato, yams', 'A low bed by the pond or as groundcover under the fruit trees'),
    ('Asparagus', 'A permanent raised bed at one end of the vegetable garden'),
    ('Rosemary, oregano, thyme, parsley, coriander', 'Kitchen beds by the back door; the rosemary and bay are already there'),
    ('Ginger, turmeric, galangal', 'The rain-garden trench edge and part-shade under the citrus'),
    ('Lemon myrtle', 'South-east corner, kept hedged to about 3 m with a root barrier on its east side (it is about 2.6 m from the east main)'),
], widths=[5.5, 11])
P('Fruit fly and possums: reusable exclusion bags or netting over small trees ($20–60 a tree) and fruit-fly traps. Keeping trees small is what makes netting possible.')

H('Garden rooms, seats and easy care')
P('Bronwen wants "rooms" so the garden is not seen all at once. Four rooms suit the block:')
B('the shaded front garden: ferns, camellias, native ginger and the lemon myrtle screen.', 'Front: ')
B('the sunny east court with the frog pond, the creek and one or two seats under a small grape pergola (summer shade, winter sun).', 'Pond court: ')
B('the vegetable garden north of the big shed: ordered beds and straight paths.', 'Vegetable room: ')
B('the west side and the small shed: the rain-garden trench, the clothes line and storage.', 'Service strip: ')
P('Movable seats for the north-west and north-east corners, and a seat on the front porch, as she asked. To keep the garden easy for the next 20 years:')
B('wide (1.0–1.2 m), level, firm paths with no steps on daily routes to the car and bins;')
B('waist-high beds, small trees picked from the ground, drip irrigation on a timer;')
B('mulch and soil delivered close to the beds, and the digging, trenching and lifting done by the handyman;')
B('taps and tank outlets at waist height.')
P('A dog is planned, so fence the vegetable room and the pond edge with a low fence or a hedge, and keep snail and rat baits out of the garden.')

H('Wildlife, bees and weeds')
B('the pond, rocks and log piles suit the frogs, skinks and blue-tongues already there. Avoid snail pellets and garden sprays, which harm them. Cane toads breed in still water: remove their egg strings (long black strings) when seen.', 'Habitat: ')
B('her two Tetragonula hockingsi hives pollinate the citrus and custard apple. Flowering natives such as grevillea, callistemon (away from the sewer), westringia and native violet feed them and bring in small birds. Dense shrubs give small birds cover.', 'Bees and birds: ')
B('Singapore daisy is a restricted invasive plant in Queensland: dig it out, bag it and do not compost it. Cobbler\'s pegs: pull before it seeds. The "white root" weed needs a photo to identify.', 'Weeds: ')

H('The big shed: cooling the west wall')
P('The west wall takes the hottest sun. Ideas from cheapest up:')
B('a trellis 30–50 cm off the west wall with passionfruit, which shades the metal before it heats ($150–400).', 'Vine screen outside: ')
B('reflective foil insulation (sisalation or foil-backed bubble wrap, foil facing an air gap) fixed inside the west wall and under the roof ($300–800 for a shed this size).', 'Foil inside: ')
B('a light-coloured "cool roof" paint on the roof and west wall ($300–700 in materials).', 'Cool paint: ')
B('a roof whirlybird or louvre vents high on the walls to let hot air out ($100–250 each).', 'Ventilation: ')
P('The stored items along the north wall already act as insulation, as Bronwen suspected.')

H('Washing-machine greywater')
P('Queensland allows laundry greywater on the garden from a sewered house. Two ways round the brick wall and hot-water system:')
B('a flexible hose from the machine\'s outlet through a small sealed hole in the wall (a plumber or the handyman can core-drill above or beside the hot-water system), switched by hand back to the laundry tub in wet weather. Cheapest, but the hose has to be moved around.', 'Simple: ')
B('a licensed plumber fits a WaterMark-approved greywater diversion device on the outside waste pipe, with a lint filter and a switch, feeding drip lines under the mulch ($600–1,500). Check with Redland City Council first.', 'Plumbed: ')
P('Either way: use it the same day (never store it), keep it off vegetables you eat raw, use plant-friendly low-salt detergents, and send it to the bananas, citrus and ornamentals.')

H('Solar and the future electric car')
P('The 2.5 kW system exports most of its power now. Run the pond and tank pumps during the day to use it. An electric car driving 30–40 km a day needs about 5–7 kWh a day, which is about half of what a 2.5 kW system makes in an average day. '
  'When the car comes, a larger system (6.6 kW is common) is the better first step before a battery.')

H('Budget: a staged plan for $15,000')
TBL(['Stage', 'What', 'Rough cost', 'Who'], [
    ('1. Now (Nov–Dec 2026)', 'Locate the house drain; Before You Dig; soil test; free arborist mulch; pull Singapore daisy; worm farm', '$300–700', 'Plumber; Bronwen'),
    ('2. Summer 2027', 'New 5,000 L slimline on the shed, base, charged line, new pump and timer drip; move the clothes line', '$3,000–4,800', 'Handyman and plumber'),
    ('3. Autumn 2027', 'Rain-garden trench, creek and frog pond with solar pump; seat pad from the pavers', '$1,200–2,800', 'Handyman digs; Bronwen plants'),
    ('4. Autumn–winter 2027', 'Main vegetable beds and paths; lemon myrtle and south-east screen; shed vine trellis and foil', '$1,800–3,500', 'Mix'),
    ('5. 2028 onward', 'Covered carport in the south-west corner with crossover and permits; greywater line', '$4,000–9,000+', 'Builder; plumber'),
    ('Total', '', 'about $10,300–20,800', ''),
], widths=[3.5, 7.5, 3, 2.5])
P('Stages 1–4 come to about $6,300–11,800, leaving room in the $15,000 for a modest carport or a second tank. A full carport with a new crossover could push the total over budget, so get quotes before committing.')

H('Still to check')
B('Where exactly the house drain runs (plumber locate).')
B('Where the 2,000 L tank sits and whether it is sound.')
B('Where the two native bee hives sit, so the pond pump and paths keep clear of their flight path.')
B('A photo of the "white root" weed.')
B('Soil test results.')
B('Which way the existing driveway runs, so the south-east screen and lemon myrtle sit clear of it.')

H('Sources')
for s in ['Bronwen\'s interview answers (27 Oct 2026), sketch (24 Oct 2026) and the council\'s 1983 house-drainage plan',
          'Ground levels: Queensland Government LiDAR DEM, 1 m, CC BY 4.0; lot boundary from the Queensland cadastre',
          'Climate: SILO gridded daily rainfall and evapotranspiration at the block, 1995–2026 (Queensland Government, CC BY 4.0)',
          'Soil: Soil and Landscape Grid of Australia (CSIRO/TERN), modelled',
          'Greywater: Business Queensland, Installing greywater systems (business.qld.gov.au)',
          'Driveways: Redland City Council, Domestic driveways and crossovers (redland.qld.gov.au)',
          'Tank rules: Business Queensland, rainwater tank installation requirements',
          'PDC Noosa 2026 lecture notes: Urban Permaculture, Water, Methods of Design',
          'Prices are rough 2026 South-East Queensland ranges; get local quotes.']:
    B(s)
doc.save(OUT + 'Annwn preliminary design report v2.docx')
print('saved', [(n, round(a, 3), round(b, 3)) for n, a, b in RES])

"""NAC features from Ange's updated plan (24 Oct 2026): sketch pixels -> map metres through planH2.json. Writes feats2.json (id -> doc)."""
import json, numpy as np, cv2, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
H = np.array(json.load(open(os.path.join(HERE, 'planH2.json')))['H'])
def T(pts): return [[round(float(x), 1), round(float(y), 1)] for x, y in cv2.perspectiveTransform(np.float32([pts]), H)[0]]
NOW = '2026-10-24T08:00:00.000Z'; SRC = "Ange's updated plan (24 Oct 2026)"
S = "From Ange's updated plan, fitted to the boundary and the house (positions about ±1 m)."
F = {}; n = [0]
def add(id, kind, name, g, pts, stage='existing', status='built', r=None, notes='', **kw):
    if id is None: n[0] += 1; id = f'bq{n[0]:02d}'
    geom = {'g': g, 'pts': T(pts)}
    if r: geom['r'] = r
    d = {'kind': kind, 'name': name, 'status': status, 'stage': stage, 'notes': (S + ' ' + notes).strip(), 'geom': geom, 'createdBy': None, 'createdAt': NOW, 'updatedAt': NOW, 'source': SRC}
    d.update(kw); F[id] = d; return id
# built
add('ap01', 'building', 'Home', 'polygon', [(725, 262), (1065, 262), (1065, 492), (725, 492)], notes='173 m² roof, all to the 30,000 L tank. Built to BAL 29. Completed Sept 2024.', roof=True)
add('ap02', 'solar', 'Solar 24 kW with battery', 'polygon', [(740, 300), (865, 300), (865, 370), (740, 370)], notes='Surplus sold to the grid.')
add('ap03', 'shed', 'Garage', 'polygon', [(450, 183), (560, 183), (560, 265), (450, 265)], notes='Roof 36 m²: half to the 30,000 L tank, half to the 5,000 L tank.', roof=True)
add('ap04', 'carport', 'Carport', 'polygon', [(450, 265), (560, 265), (560, 315), (450, 315)], notes='Roof to the 5,000 L tank.', roof=True)
add('ap05', 'driveway', 'Driveway', 'polygon', [(130, 172), (450, 178), (450, 315), (330, 310), (250, 250), (140, 215)])
add('ap06', 'tank', 'Water tank 30,000 L', 'point', [(628, 228)], notes='Fed by the house roof (173 m²) and half the garage (18 m²), 191 m² in all. Electric pump supplies the house. Overflow runs to the street gutter. Leaf guards on every gutter.', vol=30000)
add('ap07', 'tank', 'Slimline tank 5,000 L', 'point', [(575, 232)], notes='Fed by the carport and half the garage (36 m²). Tap only, for the watering can; not on the pump.', vol=5000)
add('ap08', 'structure', 'Septic (pump-out)', 'point', [(600, 290)], notes='Pump-out line runs to the boundary on the side street.')
add('ap09', 'structure', 'Septic tank', 'point', [(640, 290)])
add('ap10', 'zone1', 'Zone 1 · Raised vegie beds', 'polygon', [(795, 195), (960, 195), (960, 262), (795, 262)], notes='Lettuce, tomatoes, silverbeet, beetroot, cauliflower, brussels sprouts, celery, chilli, cucumbers, potatoes.')
for i, x in enumerate([815, 853, 891, 929]): add(f'ap{11+i}', 'raisedbed', f'Raised bed {i+1}', 'polygon', [(x, 205), (x + 28, 205), (x + 28, 255), (x, 255)])
add('ap15', 'zone1', 'Zone 1 · Herbs', 'polygon', [(838, 495), (958, 495), (958, 528), (838, 528)])
add('ap16', 'herbs', 'Herb bed', 'polygon', [(840, 497), (956, 497), (956, 526), (840, 526)], notes='Mint, basil, dill, parsley, ginger.')
add('ap17', 'path', 'Path (south of house)', 'line', [(725, 490), (1070, 490)])
add('ap18', 'steps', 'Steps (west)', 'line', [(708, 345), (722, 345)])
add('ap19', 'steps', 'Steps (east)', 'line', [(1068, 368), (1082, 368)])
add('bq01', 'path', 'Path (tank to house)', 'line', [(585, 318), (720, 335)])
add('ap20', 'bed', 'Rock garden', 'polygon', [(1225, 325), (1275, 325), (1275, 375), (1225, 375)], notes='Small to medium rocks (answer 12).')
# fruit and planted trees
fr = [('ap21', 'Plum', 990, 237), ('ap22', 'Plum', 1062, 237), ('ap23', 'Dwarf mulberry', 1140, 240), ('ap24', 'Mandarin', 1140, 326), ('ap25', 'Orange', 1140, 428), ('ap26', 'Yuzu', 1206, 510), ('ap27', 'Cumquat', 1234, 474), ('ap28', 'Lemon myrtle', 1172, 490)]
for id, nm, x, y in fr: add(id, 'fruittree', nm, 'point', [(x, y)], r=2, notes='Planted.')
add('ap29', 'shrub', 'Planted native (red on the plan)', 'point', [(1130, 498)], r=1.2, notes='Name to confirm with Ange.')
add('ap30', 'shrub', 'Leucadendron', 'point', [(1318, 358)], r=1)
add('ap31', 'shrub', 'Banksia ‘Bird Song’', 'point', [(1324, 326)], r=1)
# numbered gums (species from the plan's tree list)
gums = [('ap34', '19 · Grey ironbark (E. paniculata)', 330, 312, 4), ('ap35', '20 · Grey ironbark (E. paniculata)', 142, 367, 4), ('ap36', '21 · White mahogany (E. acmenoides)', 140, 337, 4),
        ('ap37', '22 · Tallowwood (E. microcorys)', 97, 445, 4), ('ap38', '23 · Grey ironbark (E. paniculata)', 175, 437, 4), ('ap39', '24 · Tallowwood (E. microcorys)', 215, 460, 4),
        ('ap40', '25 · Grey ironbark (E. paniculata)', 285, 407, 4), ('ap41', '26 · Grey ironbark (E. paniculata)', 450, 465, 4), ('ap43', '27 · Grey gum (E. punctata)', 522, 462, 4),
        ('ap50', '4 · Grey ironbark (E. paniculata)', 1230, 236, 4), ('ap42', 'Gum (south of house)', 1040, 525, 4)]
for id, nm, x, y, r in gums: add(id, 'nativetree', nm, 'point', [(x, y)], r=r, notes='Existing tree, numbered as on the plan.')
for i, (x, y) in enumerate([(1258, 510), (1260, 542), (1222, 542), (1170, 550), (1130, 570), (1074, 574), (1118, 602)]): add(f'ap{44+i}', 'nativetree', f'Gum cluster {i+1} (south-east)', 'point', [(x, y)], r=3, notes='Existing gums at the south-east corner, by the side street.')
for i, (x, y) in enumerate([(1224, 300), (1290, 390), (1278, 430)]): add(f'ap{51+i}', 'shrub', f'Small gum {i+1} (east)', 'point', [(x, y)], r=1.2, notes='Young native, east garden.')
# flowering natives (yellow on the plan): 12
yl = [(227, 260), (262, 265), (280, 290), (365, 342), (400, 335), (465, 440), (537, 445), (195, 515), (272, 520), (367, 520), (455, 527), (532, 540)]
for i, (x, y) in enumerate(yl): add(f'ap{54+i}', 'shrub', f'Flowering native {i+1}', 'point', [(x, y)], r=0.9, notes='Natives only on the verge and the west end (answer 33).')
add('ap66', 'shrub', 'Succulents (by the septic)', 'point', [(618, 292)], r=1)
# zones
add('bq02', 'zone2', 'Zone 2 · Fruit trees (north-east)', 'polygon', [(965, 195), (1185, 200), (1185, 470), (1070, 470), (1070, 262), (965, 262)], notes='Plums, dwarf mulberry, mandarin, orange; greywater from the laundry arrives here by hose.')
add('bq03', 'zone2', 'Zone 2 · South strip (guild planting planned)', 'polygon', [(720, 492), (1070, 492), (1070, 600), (720, 600)], notes='Herb bed, spiral herb garden and the banana guild (plan items 2 and 3).')
add('bq04', 'zone3', 'Zone 3 · West (gums and flowering natives)', 'polygon', [(120, 222), (560, 230), (560, 320), (720, 330), (720, 490), (660, 500), (560, 560), (300, 585), (140, 595), (95, 480)], notes='Existing ironbarks, tallowwoods and the grey gum with flowering natives under them. Ange wants guild planting in the south-west part of this zone.')
add('bq05', 'zone3', 'Zone 3 · East (rock garden, banksia)', 'polygon', [(1185, 200), (1250, 204), (1338, 310), (1300, 470), (1185, 470)])
add('bq06', 'zone4', 'Zone 4 · South-west gum pocket', 'polygon', [(100, 330), (200, 330), (240, 430), (240, 480), (130, 480), (95, 420)], notes='Trees 20–24.')
add('bq07', 'zone4', 'Zone 4 · South-east gum cluster', 'polygon', [(1070, 480), (1290, 480), (1274, 598), (1070, 600)])
add('bq08', 'lawn', 'Lawn square (keep)', 'polygon', [(585, 335), (720, 345), (720, 488), (585, 488)], notes='Ange: keep the square of lawn on the west side of the house (answer 35).')
# water and services
add('bq09', 'swale', 'Swale drain and berm (south verge)', 'line', [(720, 600), (1070, 603)], notes='Existing drain along the side-street verge. Plan item 4: block the ends so it holds water.')
add('bq10', 'pipe', 'Laundry greywater hose', 'line', [(1070, 470), (1250, 420)], notes='Laundry water diverted to the east garden by hose (ag pipe on the plan).')
add('bq11', 'pipe', 'Tank overflow to the street gutter', 'line', [(575, 200), (330, 185), (130, 170), (80, 60)], notes='Overflow is taken to the gutter on the front street (answer 16).')
add('bq12', 'sewer', 'Septic pump-out line', 'line', [(600, 300), (560, 320), (700, 540), (712, 600)], notes='Pump-out pipe from the septic tank to the boundary on the side street (answer 19). Keep trees 2 m+ away.')
add('bq13', 'compost', 'Compost bins', 'point', [(690, 215)], notes='Kitchen scraps, garden biomass and dog poo, with cardboard and leaves. Position approximate (not on the plan).')
# plan items (ideas)
add('bq14', 'herbspiral', 'Spiral herb garden (plan item 2)', 'point', [(800, 522)], stage='now', status='idea', notes='Drawn as a spiral south of the house.')
add('bq15', 'guild', 'Banana guild (plan item 3)', 'point', [(930, 560)], stage='now', status='idea', notes='Banana, comfrey, nasturtium and sweet potato in Zone 2.')
add('bq16', 'guild', 'Guild under the gums (south-west Zone 3)', 'point', [(300, 470)], stage='y2', status='idea', notes='Ange would like guild planting here: dry, shaded clay under grey ironbark and tallowwood. See the report for species.')
for i, (x, y) in enumerate([(305, 500), (500, 520), (1320, 520), (1360, 450)]): add(f'bq{17+i}', 'soak', f'Verge break {i+1} (plan item 1)', 'point', [(x, y)], stage='now', status='idea', notes='Break in the verge edge so road runoff soaks into the lot instead of running past.')
add('bq21', 'gathering', 'Fire pit (between trees 25 and 26)', 'point', [(370, 440)], stage='now', status='idea', notes='Circular fire pit (answers 10 and 32). Check the clearance to the gums and the BAL 29 rules before building.')
add('bq22', 'structure', 'Stone oven (idea)', 'point', [(640, 470)], stage='y2', status='idea', notes='Wanted (answer 10); location to be chosen, shown near the lawn for now.')
add('bq23', 'pond', 'Water pond (idea)', 'polygon', [(620, 420), (660, 415), (670, 445), (630, 450)], stage='y2', status='idea', notes='Wanted (answer 10); location to be chosen. Shown at the low side of the lawn for now.')
json.dump(F, open(os.path.join(HERE, 'feats2.json'), 'w'), indent=0)
print(len(F), 'features')

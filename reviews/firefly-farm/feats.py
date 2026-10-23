import json,os
SRC='Firefly Farm group draft (23 Oct 2026): annotated drone plan, zone sketch, sector analysis and design brief'
IND=' (Position indicative: traced from the group\'s drone photo and sketches onto the 2019 aerial; check on site.)'
T0='2026-10-23T10:00:00.000Z'
def F(kind,name,g,pts=None,status='built',stage='existing',notes='',src=SRC,**geom):
    gg={'g':g}
    if pts is not None: gg['pts']=pts
    lit=geom.pop('litres',None)
    gg.update(geom)
    d={'kind':kind,'name':name,'geom':gg,'status':status,'stage':stage,'notes':notes,'source':src,'createdBy':None,'createdAt':T0,'updatedAt':T0}
    if lit: d['litres']=lit
    return d
H=(574,863)
existing=[
 F('building','Main house',"polygon",[[566,855],[584,855],[584,872],[566,872]],notes='Existing house with solar panels; four 10,000 L tanks on the west side.'+IND),
 F('shed','Four-bay shed',"polygon",[[570,828],[590,828],[590,837],[570,837]],notes='Existing four-bay shed, about 160 m² of roof.'+IND),
 F('cabin','Cabin (family member)',"polygon",[[590,860],[600,860],[600,871],[590,871]],notes='Existing cabin, occupied by a family member and two children.'+IND),
 *[F('tank','Water tank %d (about 10,000 L)'%(i+1),'point',[[563,857+i*4]],notes='One of four existing tanks of about 10,000 L each.'+IND,litres=10000) for i in range(4)],
 F('road','Driveway loop','line',[[431,875],[470,898],[500,908],[522,902],[531,878],[534,850],[541,828],[560,819],[590,818],[615,822],[630,830]],notes='Existing driveway: crosses the creek (floods regularly) and loops round the orchard to the shed and house.'+IND),
 F('road','Driveway spur to the house and cabin','line',[[603,820],[598,832],[590,843],[586,852]],notes='Existing spur from the driveway loop down past the shed.'+IND),
 F('crossing','Creek crossing (floods)','point',[[431,876]],notes='The driveway crosses the creek here; about 160 ha drains to this point, so it floods regularly.'+IND),
 F('foodforest','Existing orchard (citrus and mango)','polygon',[[534,830],[562,830],[565,852],[561,876],[538,873],[533,850]],notes='Existing citrus and mango orchard: lemon, bush lemon, pink grapefruit, Valencia orange, quince, jaboticaba.'+IND),
]
group=[
 F('herbspiral','Herb spiral','point',[[575,846]],status='proposed',stage='now',notes='Group plan: herb spiral beside the house, between it and the shed.'+IND),
 F('compost','Compost bays','point',[[566,836]],status='proposed',stage='now',notes='Group plan: compost bays at the end of the shed.'+IND),
 F('bed','Annual vegetable garden','polygon',[[577,874],[591,874],[591,884],[577,884]],status='proposed',stage='now',notes='Group plan: annual vegetable and herb garden south of the house.'+IND),
 F('chickens','Chicken enclosure','polygon',[[554,852],[564,852],[564,872],[576,872],[576,892],[554,892]],status='proposed',stage='now',notes='Group plan: chickens fenced in a run along the west and south of the house, reaching the kitchen window for scraps. 5–8 birds; at least 0.5 m² coop and 1 m² run per bird.'+IND),
 F('structure','Chicken coop (mobile)','point',[[562,888]],status='proposed',stage='now',notes='Group plan: mobile coop south of the house for shade, trees between coop and house for noise.'+IND),
 F('swale','Swale and drain (privacy screen on the berm)','line',[[591,842],[591,860],[591,875],[592,892]],status='idea',stage='y2',notes='Group plan: swale on contour between house and cabin to hold water coming down the slope and divert it from the boggy patch at the driveway; water-tolerant plants on its edge, a privacy screen under about 2 m on the berm. Needs deeper observation first.'+IND),
 F('screen','Privacy trees along the driveway','line',[[598,834],[607,839],[616,845]],status='proposed',stage='now',notes='Group plan: privacy trees between the driveway and the house and cabin.'+IND),
 F('foodforest','Food forest (orchard expansion)','polygon',[[530,876],[561,878],[556,905],[530,905]],status='idea',stage='y2',notes='Group plan: expand and integrate the orchard into a diverse food forest with understorey, shrub, ground and root layers.'+IND),
 F('guild','Lemon guild','point',[[550,845]],status='proposed',stage='now',notes='Group plan: sub-canopy guild under the lemon: comfrey on the drip line, dandelion, yarrow, white clover, nasturtium, borage, alyssum.'+IND),
 F('zone0','Zone 0 · house','polygon',[[566,855],[584,855],[584,872],[566,872]],notes='Group zone sketch.'+IND),
 F('zone1','Zone 1 · house, shed and cabin surrounds','polygon',[[562,838],[604,838],[606,880],[586,886],[562,880]],status='proposed',stage='now',notes='Group zone sketch: daily-use area around the house, shed and cabin.'+IND),
 F('zone2','Zone 2 · orchard','polygon',[[532,826],[562,826],[566,878],[532,878]],status='proposed',stage='now',notes='Group zone sketch: orchard west of the house.'+IND),
 F('zone2','Zone 2 · south lawn and food forest','polygon',[[530,880],[606,884],[606,915],[530,915]],status='idea',stage='y2',notes='Group zone sketch: open ground south of the house for food forest expansion.'+IND),
 F('zone3','Zone 3 · east slope and lower west slope','polygon',[[606,826],[631,820],[640,885],[608,890]],status='idea',stage='y2',notes='Group zone sketch: outer areas.'+IND),
 F('sunW','Winter sun','sun',cx=H[0],cy=H[1],r=90,notes='Group sector analysis. The map draws the correct bearings for this latitude (sunrise about 63°, sunset about 297°).'),
 F('sunS','Summer sun','sun',cx=H[0],cy=H[1],r=90,notes='Group sector analysis. The map draws the correct bearings (sunrise about 117°, sunset about 243°).'),
 F('wind','Prevailing winds (S–SE–E)','sector',cx=H[0],cy=H[1],r=80,a0=100,a1=200,notes='Group sector analysis: prevailing winds from the south to east; the brief also records easterlies in summer. Validate against Bureau wind roses and observation.'),
 F('wind','Spring winds (N)','sector',cx=H[0],cy=H[1],r=70,a0=330,a1=30,notes='Group sector analysis: northerly winds in spring (and autumn and winter in the brief).'),
 F('view','View (south-west, to the ranges)','sector',cx=H[0],cy=H[1],r=100,a0=195,a1=235,notes='Group sector analysis: the view.'),
 F('view','Privacy (north-north-east)','sector',cx=H[0],cy=H[1],r=60,a0=15,a1=60,notes='Group sector analysis: privacy toward the north-north-east.'),
]
R='Review suggestion (Firefly Farm design review, 23 Oct 2026)'
extra=[
 F('swale','Swale on contour (from elevation), spillway south','line',[[597,840],[592,850],[589,860],[588,870]],status='proposed',stage='y2',src=R,notes='Suggested: set out the level line on site with an A-frame after a wet season of watching. From the 5 m elevation the level line here is about 119 m and runs north–south between the house and cabin. About 1 ha of slope drains to it. Spill at the south end into the rain garden, never toward the house.'),
 F('flow','Swale spillway','line',[[588,870],[592,880],[588,893],[581,899]],status='proposed',stage='y2',src=R,notes='Suggested: rock-lined spillway from the swale end to the rain garden.'),
 F('raingarden','Rain garden / overflow basin','polygon',[[574,896],[586,896],[586,906],[574,906]],status='proposed',stage='y2',src=R,notes='Suggested: mulched basin with water-tolerant plants (Lomandra, native ginger, bananas at its edge) that takes the swale and tank overflows.'),
 F('screen','Privacy screen on the swale berm (under 2 m)','line',[[595,840],[590,850],[587,860],[586,870]],status='proposed',stage='y2',src=R,notes='Suggested species under about 2 m: native ginger, cordyline, lilly pilly hedge kept clipped, finger lime, midyim. Keeps morning sun on the house.'),
 F('tank','Garden tank on the high side (proposed)','point',[[605,856]],status='proposed',stage='now',src=R,notes='Suggested: a garden tank at about 121 m, fed by the cabin roof and topped up from the shed. About 3–4 m above the vegetable beds gives about 30 kPa for drip and soaker lines.',litres=10000),
 F('pipe','Garden tank to vegetable beds','line',[[605,856],[600,874],[588,879]],status='proposed',stage='now',src=R,notes='Suggested: 25 mm poly from the garden tank to the beds and the chicken waterer.'),
 F('raisedbed','Raised or wicking beds over the clay','polygon',[[577,874],[589,874],[589,883],[577,883]],status='proposed',stage='now',src=R,notes='Suggested: start with 3–4 beds (about 30–50 m²) on raised or wicking beds over the clay, after a soil test that includes arsenic and organochlorines (old banana land).'),
 F('obs','Soil test: vegetable patch','point',[[583,879]],status='proposed',stage='now',src=R,notes='Suggested: lab soil test plus arsenic and organochlorine screen before growing vegetables (NSW EPA names arsenic and dieldrin as the main leftovers on old banana land).'),
 F('obs','Soil test: orchard','point',[[548,856]],status='proposed',stage='now',src=R,notes='Suggested: standard lab test; 10–15 cores mixed.'),
 F('obs','Soil test and infiltration: boggy patch','point',[[586,852]],status='proposed',stage='now',src=R,notes='Suggested: test the boggy ground by the driveway (slake and infiltration tests too) to see whether it is seepage, compaction or sodic clay.'),
 F('obs','Soil test: chicken run','point',[[565,885]],status='proposed',stage='now',src=R,notes='Suggested: screen the chicken run too, as chickens forage in the soil.'),
 F('guild','Mango guild','point',[[545,866]],status='proposed',stage='y2',src=R,notes='Suggested guild: mulched to 1 m from the trunk; comfrey and turmeric at the drip line; pigeon pea outside it on the north, cut twice a year; ginger, arrowroot and sweet potato between trees; bananas on the sunny edge with greywater.'),
 F('greywater','Laundry greywater to bananas and citrus','polygon',[[548,874],[558,874],[558,884],[548,884]],status='idea',stage='y2',src=R,notes='Suggested: a greywater diverter from the laundry to a mulched banana circle; not on leafy greens; keep clear of the septic field (location to confirm) and check council rules.'),
 *[F('fruittree',nm,'point',[pt],status='idea',stage='y2',src=R,notes=nt) for nm,pt,nt in [
   ('Macadamia (local native)',[538,888],'Suggested: native to the region; canopy layer of the food forest extension.'),
   ('Macadamia (local native)',[550,898],'Suggested: native to the region.'),
   ('Lychee (netted)',[541,840],'Group addition: on the bench (frost-free); net with white mesh no wider than 5 × 5 mm.'),
   ('Low-chill peach (netted)',[556,836],'Group addition: net or bag against Queensland fruit fly.'),
   ('Custard apple / atemoya',[536,860],'Group addition: frost-tender, keep on the bench.')]],
 *[F('shrub',nm,'point',[pt],status='idea',stage='y2',src=R,notes=nt) for nm,pt,nt in [
   ('Davidson\'s plum (local native)',[535,895],'Suggested native understorey.'),
   ('Finger lime (local native)',[545,903],'Suggested native understorey; thorny, good near the chicken run edge.'),
   ('Midyim (local native)',[558,842],'Group addition; good under the citrus edge.'),
   ('Grumichama (check label: Eugenia brasiliensis)',[540,848],'Group addition; make sure it is not Surinam or Brazilian cherry (E. uniflora).')]],
 F('hives','Native stingless bee hive','point',[[560,834]],status='idea',stage='y2',src=R,notes='Suggested: Tetragonula hive at the orchard edge, morning sun and afternoon shade. Honey bees need NSW DPI registration.'),
 F('apz','Low-fuel zone round the house and cabin','polygon',[[548,822],[620,822],[620,898],[548,898]],status='proposed',stage='now',src=R,notes='Suggested: keep fuel low here (mown lawn, irrigated gardens, no lantana or dense dry shrubs). Check NSW bushfire-prone land mapping and Planning for Bush Fire Protection.'),
 F('fire','Fire approach (W–NW, upslope from the creek)','sector',cx=H[0],cy=H[1],r=110,a0=250,a1=330,status='proposed',stage='existing',src=R,notes='Suggested sector: hot dry westerlies in late winter–spring, and fire runs fastest upslope from the creek.'),
 F('wind','Winter westerlies (check)','sector',cx=H[0],cy=H[1],r=75,a0=240,a1=290,status='idea',stage='existing',src=R,notes='Suggested to check: cold dry westerlies are common inland of the coast in winter and spring. Confirm with the Lismore wind roses and observation.'),
 F('note','Correction: sun angles','point',[[620,870]],status='proposed',stage='existing',src=R,notes='The draft sector diagram has the angles swapped: winter sunrise about 63°, sunset about 297°; summer sunrise about 117°, sunset about 243° (at about 28.6° S).'),
]
whole=[
 F('zone3','Zone 3 · creek flats and lower west slope','polygon',[[436,936],[436,878],[464,864],[495,862],[528,862],[528,910],[505,930],[470,940]],status='idea',stage='y5',src=R,notes='Suggested: flood-prone flats and the lower slope: pasture for a few sheep, flood-tolerant trees, a possible pond site out of flood reach. Cold air settles here: no frost-tender trees.'),
 F('zone4','Zone 4 · lower forested slopes','polygon',[[622,842],[689,823],[708,840],[735,844],[790,873],[760,1127],[561,1094],[575,900],[631,888]],status='idea',stage='y5',src=R,notes='Suggested: managed bush and lower slopes: lantana control from the good bush outward, firewood, a trail on contour.'),
 F('zone5','Zone 5 · upper bush (habitat and corridor)','polygon',[[790,873],[871,866],[953,805],[1083,733],[1212,750],[1243,774],[1329,795],[1334,842],[1611,1269],[760,1127]],status='idea',stage='existing',src=R,notes='Suggested: steep forest (over a third of the property is steeper than 50%). Habitat, corridor, Land for Wildlife; possible conservation agreement.'),
 F('customzone','Creek riparian buffer (at least 10–20 m)','polygon',[[405,790],[421,790],[438,850],[446,878],[451,905],[445,942],[426,948],[431,905],[428,880],[416,838]],status='proposed',stage='now',src=R,notes='Suggested: no cultivation, stock camping or fertiliser along the creek; riparian planting may get Landcare support.'),
 F('structure','Water-powered creek pump (option)','point',[[438,890]],status='idea',stage='y5',src=R,notes='Long-term option: a ram or Bunyip pump on the permanent creek lifting water about 24 m to a header tank above the gardens. Try the Ram & Bunyip pumps tool. Domestic and stock use only unless licensed.'),
 F('path','Bush walking trail on contour (idea)','line',[[640,880],[700,905],[760,930],[820,950]],status='idea',stage='y10',src=R,notes='Long-term idea: a walking or bike trail on contour with drainage turnouts every 20–30 m.'),
]
import copy
G=existing+group
Cb=copy.deepcopy(existing+group)+extra+whole
# in combined, mark the group's swale as superseded note
for f in Cb:
    if f['kind']=='swale' and f['source']==SRC: f['notes']+=' Combined version: see the suggested level line beside it, traced from the elevation.'
out='/home/claude/pdc-design-map/data-snapshots/trial-firefly'
os.makedirs(out,exist_ok=True)
gd={('ff%02d'%(i+1)):f for i,f in enumerate(G)};cd={('fc%02d'%(i+1)):f for i,f in enumerate(Cb)}
json.dump(gd,open(out+'/nimbin-group_features.json','w'),indent=0);json.dump(cd,open(out+'/nimbin-combined_features.json','w'),indent=0)
print(len(gd),len(cd))

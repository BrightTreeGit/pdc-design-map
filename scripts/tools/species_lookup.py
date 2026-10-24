"""Small offline lookup used by ingest_extras.py when the Atlas didn't send groups or common names.
Common names and groups for species often recorded around the PDC sites, a genus-to-group table for the rest,
known conservation listings (Q = Queensland Nature Conservation Act, N = NSW Biodiversity Conservation Act,
C = Commonwealth EPBC Act) and pest species. Listings change: the card says to confirm them on the current lists."""

NAMES = {  # scientific: (common, group)
 'Phascolarctos cinereus': ('Koala', 'Mammals'), 'Manorina melanocephala': ('Noisy miner', 'Birds'), 'Dacelo novaeguineae': ('Laughing kookaburra', 'Birds'),
 'Gymnorhina tibicen': ('Australian magpie', 'Birds'), 'Corvus orru': ('Torresian crow', 'Birds'), 'Meliphaga lewinii': ("Lewin's honeyeater", 'Birds'),
 'Trichoglossus moluccanus': ('Rainbow lorikeet', 'Birds'), 'Hirundo neoxena': ('Welcome swallow', 'Birds'), 'Cracticus nigrogularis': ('Pied butcherbird', 'Birds'),
 'Psophodes olivaceus': ('Eastern whipbird', 'Birds'), 'Strepera graculina': ('Pied currawong', 'Birds'), 'Alisterus scapularis': ('Australian king-parrot', 'Birds'),
 'Coracina novaehollandiae': ('Black-faced cuckoo-shrike', 'Birds'), 'Geopelia humeralis': ('Bar-shouldered dove', 'Birds'), 'Platycercus eximius': ('Eastern rosella', 'Birds'),
 'Cracticus torquatus': ('Grey butcherbird', 'Birds'), 'Colluricincla harmonica': ('Grey shrike-thrush', 'Birds'), 'Neochmia temporalis': ('Red-browed finch', 'Birds'),
 'Rhipidura leucophrys': ('Willie wagtail', 'Birds'), 'Ptilonorhynchus violaceus': ('Satin bowerbird', 'Birds'), 'Platycercus elegans': ('Crimson rosella', 'Birds'),
 'Sphecotheres vieilloti': ('Australasian figbird', 'Birds'), 'Macropygia phasianella': ('Brown cuckoo-dove', 'Birds'), 'Sericornis frontalis': ('White-browed scrubwren', 'Birds'),
 'Alectura lathami': ('Australian brush-turkey', 'Birds'), 'Columba leucomela': ('White-headed pigeon', 'Birds'), 'Malurus cyaneus': ('Superb fairy-wren', 'Birds'),
 'Acanthiza pusilla': ('Brown thornbill', 'Birds'), 'Rhipidura albiscapa': ('Grey fantail', 'Birds'), 'Egretta novaehollandiae': ('White-faced heron', 'Birds'),
 'Chalcophaps longirostris': ('Pacific emerald dove', 'Birds'), 'Grallina cyanoleuca': ('Magpie-lark', 'Birds'), 'Litoria fallax': ('Eastern sedge frog', 'Amphibians'),
 'Dicrurus bracteatus': ('Spangled drongo', 'Birds'), 'Zanda funerea': ('Yellow-tailed black-cockatoo', 'Birds'), 'Eopsaltria australis': ('Eastern yellow robin', 'Birds'),
 'Limnodynastes peronii': ('Striped marsh frog', 'Amphibians'), 'Philemon corniculatus': ('Noisy friarbird', 'Birds'), 'Adelotus brevis': ('Tusked frog', 'Amphibians'),
 'Litoria peronii': ("Peron's tree frog", 'Amphibians'), 'Pachycephala pectoralis': ('Golden whistler', 'Birds'), 'Zosterops lateralis': ('Silvereye', 'Birds'),
 'Oriolus sagittatus': ('Olive-backed oriole', 'Birds'), 'Malurus melanocephalus': ('Red-backed fairy-wren', 'Birds'), 'Acanthorhynchus tenuirostris': ('Eastern spinebill', 'Birds'),
 'Lichmera indistincta': ('Brown honeyeater', 'Birds'), 'Cacatua galerita': ('Sulphur-crested cockatoo', 'Birds'), 'Centropus phasianinus': ('Pheasant coucal', 'Birds'),
 'Sericulus chrysocephalus': ('Regent bowerbird', 'Birds'), 'Chenonetta jubata': ('Australian wood duck', 'Birds'), 'Myzomela sanguinolenta': ('Scarlet honeyeater', 'Birds'),
 'Vanellus miles': ('Masked lapwing', 'Birds'), 'Spilopelia chinensis': ('Spotted dove (introduced)', 'Birds'), 'Eudynamys orientalis': ('Pacific koel', 'Birds'),
 'Ocyphaps lophotes': ('Crested pigeon', 'Birds'), 'Microcarbo melanoleucos': ('Little pied cormorant', 'Birds'), 'Caligavis chrysops': ('Yellow-faced honeyeater', 'Birds'),
 'Mixophyes fasciolatus': ('Great barred frog', 'Amphibians'), 'Cacatua sanguinea': ('Little corella', 'Birds'), 'Podargus strigoides': ('Tawny frogmouth', 'Birds'),
 'Synoicus ypsilophora': ('Brown quail', 'Birds'), 'Lopholaimus antarcticus': ('Topknot pigeon', 'Birds'), 'Chroicocephalus novaehollandiae': ('Silver gull', 'Birds'),
 'Entomyzon cyanotis': ('Blue-faced honeyeater', 'Birds'), 'Haliaeetus leucogaster': ('White-bellied sea-eagle', 'Birds'), 'Pardalotus striatus': ('Striated pardalote', 'Birds'),
 'Litoria tyleri': ("Tyler's tree frog", 'Amphibians'), 'Elanus axillaris': ('Black-shouldered kite', 'Birds'), 'Pachycephala rufiventris': ('Rufous whistler', 'Birds'),
 'Cacomantis variolosus': ('Brush cuckoo', 'Birds'), 'Uperoleia fusca': ('Dusky toadlet', 'Amphibians'), 'Pelecanus conspicillatus': ('Australian pelican', 'Birds'),
 'Eolophus roseicapilla': ('Galah', 'Birds'), 'Lalage leucomela': ('Varied triller', 'Birds'), 'Trichoglossus chlorolepidotus': ('Scaly-breasted lorikeet', 'Birds'),
 'Aquila audax': ('Wedge-tailed eagle', 'Birds'), 'Myiagra rubecula': ('Leaden flycatcher', 'Birds'), 'Crinia signifera': ('Common eastern froglet', 'Amphibians'),
 'Leucosarcia melanoleuca': ('Wonga pigeon', 'Birds'), 'Melithreptus albogularis': ('White-throated honeyeater', 'Birds'), 'Anas superciliosa': ('Pacific black duck', 'Birds'),
 'Scythrops novaehollandiae': ('Channel-billed cuckoo', 'Birds'), 'Limosa lapponica': ('Bar-tailed godwit', 'Birds'), 'Thalasseus bergii': ('Greater crested tern', 'Birds'),
 'Cacomantis flabelliformis': ('Fan-tailed cuckoo', 'Birds'), 'Threskiornis moluccus': ('Australian white ibis', 'Birds'), 'Temnosewellia christineae': ('Temnocephalan flatworm', 'Animals'),
 'Dianella caerulea': ('Blue flax-lily', 'Plants'), 'Dodonaea triquetra': ('Large-leaf hop-bush', 'Plants'), 'Lantana camara': ('Lantana (weed)', 'Plants'),
 'Phalacrocorax varius': ('Australian pied cormorant', 'Birds'), 'Myiagra inquieta': ('Restless flycatcher', 'Birds'), 'Themeda triandra': ('Kangaroo grass', 'Plants'),
 'Lepidosperma laterale': ('Variable sword-sedge', 'Plants'), 'Haematopus longirostris': ('Australian pied oystercatcher', 'Birds'), 'Eustrephus latifolius': ('Wombat berry', 'Plants'),
 'Platycercus adscitus': ('Pale-headed rosella', 'Birds'), 'Aviceda subcristata': ('Pacific baza', 'Birds'), 'Entolasia stricta': ('Wiry panic', 'Plants'),
 'Merops ornatus': ('Rainbow bee-eater', 'Birds'), 'Cormobates leucophaea': ('White-throated treecreeper', 'Birds'), 'Litoria gracilenta': ('Dainty green tree frog', 'Amphibians'),
 'Rhinella marina': ('Cane toad (pest)', 'Amphibians'), 'Threskiornis spinicollis': ('Straw-necked ibis', 'Birds'), 'Todiramphus sanctus': ('Sacred kingfisher', 'Birds'),
 'Hydroprogne caspia': ('Caspian tern', 'Birds'), 'Anas castanea': ('Chestnut teal', 'Birds'), 'Anhinga novaehollandiae': ('Australasian darter', 'Birds'),
 'Breynia oblongifolia': ('Coffee bush', 'Plants'), 'Litoria caerulea': ('Green tree frog', 'Amphibians'), 'Lobelia purpurascens': ('White root', 'Plants'),
 'Notelaea longifolia': ('Large mock-olive', 'Plants'), 'Pardalotus punctatus': ('Spotted pardalote', 'Birds'), 'Phalacrocorax sulcirostris': ('Little black cormorant', 'Birds'),
 'Gerygone olivacea': ('White-throated gerygone', 'Birds'), 'Lomandra longifolia': ('Spiny-head mat-rush', 'Plants'), 'Mallotus philippensis': ('Red kamala', 'Plants'),
 'Malurus lamberti': ('Variegated fairy-wren', 'Birds'), 'Rhipidura rufifrons': ('Rufous fantail', 'Birds'), 'Litoria verreauxii': ("Verreaux's frog", 'Amphibians'),
 'Pteropus poliocephalus': ('Grey-headed flying-fox', 'Mammals'), 'Pteropus alecto': ('Black flying-fox', 'Mammals'), 'Macropus giganteus': ('Eastern grey kangaroo', 'Mammals'),
 'Notamacropus rufogriseus': ("Red-necked wallaby", 'Mammals'), 'Wallabia bicolor': ('Swamp wallaby', 'Mammals'), 'Trichosurus vulpecula': ('Common brushtail possum', 'Mammals'),
 'Pseudocheirus peregrinus': ('Common ringtail possum', 'Mammals'), 'Tachyglossus aculeatus': ('Short-beaked echidna', 'Mammals'), 'Petaurus breviceps': ('Sugar glider', 'Mammals'),
 'Vulpes vulpes': ('Red fox (pest)', 'Mammals'), 'Felis catus': ('Cat (pest)', 'Mammals'), 'Acridotheres tristis': ('Common myna (pest)', 'Birds'),
 'Varanus varius': ('Lace monitor', 'Reptiles'), 'Intellagama lesueurii': ('Eastern water dragon', 'Reptiles'), 'Pogona barbata': ('Eastern bearded dragon', 'Reptiles'),
 'Morelia spilota': ('Carpet python', 'Reptiles'), 'Dendrelaphis punctulatus': ('Common tree snake', 'Reptiles'), 'Pseudechis porphyriacus': ('Red-bellied black snake', 'Reptiles'),
 'Lampropholis delicata': ('Dark-flecked garden sunskink', 'Reptiles'), 'Eulamprus quoyii': ('Eastern water skink', 'Reptiles'), 'Tiliqua scincoides': ('Eastern blue-tongue', 'Reptiles'),
}

NAMES.update({
 'Calyptorhynchus lathami': ('Glossy black-cockatoo', 'Birds'), 'Ninox strenua': ('Powerful owl', 'Birds'), 'Ornithoptera richmondia': ('Richmond birdwing', 'Insects'),
 'Petaurus australis': ('Yellow-bellied glider', 'Mammals'), 'Petauroides volans': ('Greater glider', 'Mammals'), 'Climacteris erythrops': ('Red-browed treecreeper', 'Birds'),
 'Tyto tenebricosa': ('Sooty owl', 'Birds'), 'Ptilinopus regina': ('Rose-crowned fruit-dove', 'Birds'), 'Ptilinopus magnificus': ('Wompoo fruit-dove', 'Birds'),
 'Macadamia tetraphylla': ('Rough-shelled bush nut', 'Plants'), 'Macadamia integrifolia': ('Macadamia nut', 'Plants'), 'Numenius madagascariensis': ('Far eastern curlew', 'Birds'),
 'Haematopus fuliginosus': ('Sooty oystercatcher', 'Birds'), 'Daphoenositta chrysoptera': ('Varied sittella', 'Birds'), 'Lathamus discolor': ('Swift parrot', 'Birds'),
 'Pandion haliaetus': ('Eastern osprey', 'Birds'), 'Burhinus grallarius': ('Bush stone-curlew', 'Birds'), 'Turnix melanogaster': ('Black-breasted button-quail', 'Birds'),
 'Anthochaera phrygia': ('Regent honeyeater', 'Birds'), 'Erythrotriorchis radiatus': ('Red goshawk', 'Birds'), 'Esacus magnirostris': ('Beach stone-curlew', 'Birds'),
 'Calidris ferruginea': ('Curlew sandpiper', 'Birds'), 'Tyto novaehollandiae': ('Masked owl', 'Birds'), 'Glossopsitta pusilla': ('Little lorikeet', 'Birds'),
 'Ephippiorhynchus asiaticus': ('Black-necked stork', 'Birds'), 'Hieraaetus morphnoides': ('Little eagle', 'Birds'), 'Lophoictinia isura': ('Square-tailed kite', 'Birds'),
 'Phascogale tapoatafa': ('Brush-tailed phascogale', 'Mammals'), 'Dasyurus maculatus': ('Spotted-tailed quoll', 'Mammals'), 'Potorous tridactylus': ('Long-nosed potoroo', 'Mammals'),
 'Miniopterus australis': ('Little bent-winged bat', 'Mammals'), 'Myotis macropus': ('Large-footed myotis', 'Mammals'), 'Mixophyes iteratus': ('Giant barred frog', 'Amphibians'),
 'Crinia tinnula': ('Wallum froglet', 'Amphibians'), 'Litoria olongburensis': ('Wallum sedge frog', 'Amphibians'), 'Cyclopsitta coxeni': ("Coxen's fig-parrot", 'Birds'),
 'Ligustrum lucidum': ('Broad-leaf privet (weed)', 'Plants'), 'Ligustrum sinense': ('Small-leaf privet (weed)', 'Plants'), 'Passiflora suberosa': ('Corky passionvine (weed)', 'Plants'),
 'Asparagus aethiopicus': ('Asparagus fern (weed)', 'Plants'), 'Ochna serrulata': ('Mickey Mouse bush (weed)', 'Plants'), 'Celtis sinensis': ('Chinese elm (weed)', 'Plants'),
 'Anredera cordifolia': ('Madeira vine (weed)', 'Plants'), 'Cinnamomum camphora': ('Camphor laurel (weed)', 'Plants'), 'Ageratina adenophora': ('Crofton weed', 'Plants'),
 'Cenchrus clandestinus': ('Kikuyu (weed)', 'Plants'), 'Senna pendula': ('Easter cassia (weed)', 'Plants'), 'Solanum mauritianum': ('Wild tobacco (weed)', 'Plants'),
 'Megathyrsus maximus': ('Guinea grass (weed)', 'Plants'), 'Melinis minutiflora': ('Molasses grass (weed)', 'Plants'), 'Schinus terebinthifolius': ('Broad-leaved pepper tree (weed)', 'Plants'),
 'Sphagneticola trilobata': ('Singapore daisy (weed)', 'Plants'), 'Eugenia uniflora': ('Brazilian cherry (weed)', 'Plants'), 'Baccharis halimifolia': ('Groundsel bush (weed)', 'Plants'),
 'Sus scrofa': ('Feral pig (pest)', 'Mammals'), 'Oryctolagus cuniculus': ('European rabbit (pest)', 'Mammals'), 'Rattus rattus': ('Black rat (pest)', 'Mammals'),
 'Mus musculus': ('House mouse (pest)', 'Mammals'), 'Gambusia holbrooki': ('Gambusia (pest fish)', 'Fishes'),
})

GENUS = {}
for g in ('Litoria Limnodynastes Crinia Mixophyes Uperoleia Adelotus Pseudophryne Assa Rhinella Platyplectrum Lechriodus').split(): GENUS[g] = 'Amphibians'
for g in ('Varanus Intellagama Pogona Morelia Dendrelaphis Pseudechis Lampropholis Eulamprus Tiliqua Ctenotus Anomalopus Hemiaspis Demansia Pseudonaja Cacophis Boiga Tropidonophis Amalosia Diplodactylus Christinus Gehyra Emydura Chelodina Saproscincus Concinnia Calyptotis Cyclodomorphus Egernia Bellatorias Amphibolurus Diporiphora Hoplocephalus Furina Antaioserpens Ramphotyphlops Anilios Aspidites Antaresia').split(): GENUS[g] = 'Reptiles'
for g in ('Phascolarctos Pteropus Macropus Notamacropus Wallabia Trichosurus Pseudocheirus Tachyglossus Petaurus Petauroides Acrobates Vulpes Felis Canis Rattus Melomys Antechinus Planigale Isoodon Perameles Potorous Thylogale Dasyurus Phascogale Miniopterus Myotis Nyctophilus Chalinolobus Vespadelus Scotorepens Austronomus Ozimops Rhinolophus Syconycteris Hydromys Oryctolagus Lepus Sus Bos Equus Mus Ornithorhynchus Cercartetus Aepyprymnus Osphranter').split(): GENUS[g] = 'Mammals'
for g in ('Papilio Ornithoptera Graphium Delias Eurema Danaus Euploea Hypolimnas Junonia Tisiphone Heteronympha Hypocysta Acraea Catopsilia Belenois Cressida Jalmenus Candalides Psychonotis Nacaduba Jamides Zizina Theclinesthes Ocybadistes Trapezites Apis Tetragonula Amegilla Xylocopa Camponotus Iridomyrmex Polyrhachis Myrmecia Oecophylla Rhytidoponera Tropidoderus Cyclochila Psaltoda Thopha Ischnura Austrolestes Diplacodes Orthetrum Hemicordulia Rhyothemis Xanthagrion Pseudagrion Tramea Anax Mantis Tenodera Pseudomantis Valanga Goniaea Austracris Coccinella Harmonia Micraspis Hippodamia Lagria Chauliognathus Anoplognathus Repsimus Diphucephala').split(): GENUS[g] = 'Insects'
for g in ('Nephila Trichonephila Argiope Gasteracantha Austracantha Latrodectus Isopeda Holconia Hortophora Eriophora Nephila Cyrtophora Leucauge Phonognatha Badumna Maratus Servaea Hypoblemum Opisthoncus Mopsus Sandalodes').split(): GENUS[g] = 'Arachnids'

LISTED = {  # scientific: [(jurisdiction, status)]
 'Phascolarctos cinereus': [('Q', 'Endangered'), ('N', 'Endangered'), ('C', 'Endangered (Qld, NSW, ACT)')],
 'Pteropus poliocephalus': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')], 'Calyptorhynchus lathami': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')],
 'Ninox strenua': [('Q', 'Vulnerable'), ('N', 'Vulnerable')], 'Crinia tinnula': [('Q', 'Vulnerable'), ('N', 'Vulnerable')], 'Mixophyes iteratus': [('Q', 'Endangered'), ('N', 'Endangered'), ('C', 'Endangered')],
 'Litoria olongburensis': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')], 'Petauroides volans': [('Q', 'Endangered'), ('N', 'Endangered'), ('C', 'Endangered')],
 'Petaurus australis': [('N', 'Vulnerable'), ('C', 'Vulnerable (Wet Tropics)')], 'Turnix melanogaster': [('Q', 'Vulnerable'), ('N', 'Endangered'), ('C', 'Vulnerable')],
 'Lathamus discolor': [('N', 'Endangered'), ('C', 'Critically Endangered')], 'Anthochaera phrygia': [('N', 'Critically Endangered'), ('C', 'Critically Endangered')],
 'Erythrotriorchis radiatus': [('Q', 'Endangered'), ('N', 'Critically Endangered'), ('C', 'Vulnerable')], 'Ornithoptera richmondia': [('Q', 'Vulnerable')],
 'Macadamia integrifolia': [('Q', 'Vulnerable'), ('N', 'Endangered'), ('C', 'Vulnerable')], 'Macadamia tetraphylla': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')],
 'Limosa lapponica': [('Q', 'Vulnerable'), ('C', 'Vulnerable (baueri) / Critically Endangered (menzbieri)')], 'Numenius madagascariensis': [('Q', 'Endangered'), ('N', 'Critically Endangered'), ('C', 'Critically Endangered')],
 'Calidris ferruginea': [('Q', 'Critically Endangered'), ('N', 'Endangered'), ('C', 'Critically Endangered')], 'Esacus magnirostris': [('Q', 'Vulnerable'), ('N', 'Critically Endangered')],
 'Burhinus grallarius': [('N', 'Endangered')], 'Haematopus fuliginosus': [('N', 'Vulnerable')], 'Haematopus longirostris': [('N', 'Endangered')],
 'Tyto tenebricosa': [('N', 'Vulnerable')], 'Tyto novaehollandiae': [('N', 'Vulnerable')], 'Glossopsitta pusilla': [('N', 'Vulnerable')], 'Daphoenositta chrysoptera': [('N', 'Vulnerable')],
 'Ptilinopus magnificus': [('N', 'Vulnerable')], 'Ptilinopus regina': [('N', 'Vulnerable')], 'Ephippiorhynchus asiaticus': [('N', 'Endangered')], 'Pandion haliaetus': [('N', 'Vulnerable')],
 'Hieraaetus morphnoides': [('N', 'Vulnerable')], 'Lophoictinia isura': [('N', 'Vulnerable')], 'Phascogale tapoatafa': [('N', 'Vulnerable')],
 'Dasyurus maculatus': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Endangered')], 'Potorous tridactylus': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')],
 'Miniopterus australis': [('N', 'Vulnerable')], 'Myotis macropus': [('N', 'Vulnerable')], 'Mixophyes fleayi': [('Q', 'Endangered'), ('N', 'Endangered'), ('C', 'Endangered')],
 'Coeranoscincus reticulatus': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')], 'Climacteris erythrops': [('Q', 'Vulnerable'), ('N', 'Vulnerable')],
 'Cyclopsitta coxeni': [('Q', 'Endangered'), ('N', 'Critically Endangered'), ('C', 'Endangered')], 'Atrichornis rufescens': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Endangered')],
 'Melanodryas cucullata': [('N', 'Vulnerable')], 'Neophema pulchella': [('N', 'Vulnerable')], 'Stagonopleura guttata': [('N', 'Vulnerable')],
 'Pseudomys novaehollandiae': [('N', 'Vulnerable'), ('C', 'Vulnerable')], 'Petrogale penicillata': [('Q', 'Vulnerable'), ('N', 'Endangered'), ('C', 'Vulnerable')],
 'Syzygium hodgkinsoniae': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')], 'Davidsonia johnsonii': [('Q', 'Endangered'), ('N', 'Endangered'), ('C', 'Endangered')],
 'Fontainea venosa': [('Q', 'Vulnerable'), ('C', 'Vulnerable')], 'Romnalda strobilacea': [('Q', 'Vulnerable'), ('N', 'Vulnerable'), ('C', 'Vulnerable')],
}
PESTS = {'Rhinella marina', 'Lantana camara', 'Vulpes vulpes', 'Felis catus', 'Acridotheres tristis', 'Sus scrofa', 'Oryctolagus cuniculus', 'Rattus rattus', 'Mus musculus',
         'Sphagneticola trilobata', 'Cinnamomum camphora', 'Ochna serrulata', 'Senna pendula', 'Asparagus aethiopicus', 'Anredera cordifolia', 'Ageratina adenophora',
         'Ligustrum lucidum', 'Ligustrum sinense', 'Melinis minutiflora', 'Megathyrsus maximus', 'Cenchrus clandestinus', 'Passiflora suberosa', 'Eugenia uniflora',
         'Schinus terebinthifolius', 'Celtis sinensis', 'Solanum mauritianum', 'Baccharis halimifolia', 'Gambusia holbrooki'}


def enrich(name, e, state):
    """Fill group/common/status from the tables when the Atlas left them empty. state: 'Q' or 'N' (the site's state)."""
    c, g = NAMES.get(name, (None, None))
    e['common'] = e.get('common') or c
    e['group'] = e.get('group') or g or GENUS.get(name.split()[0])
    if not e.get('status') and name in LISTED:
        tags = [f"{'Qld' if j == 'Q' else 'NSW' if j == 'N' else 'National'} {s}" for j, s in LISTED[name] if j in (state, 'C')]
        if tags: e['status'] = '; '.join(tags) + ' (from known listings; confirm on the current list)'
    e['pest'] = name in PESTS
    return e

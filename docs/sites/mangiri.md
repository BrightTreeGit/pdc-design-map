# Mangiri

PRIVATE (repo only): Mully's group site at Mongarlowe, Southern Tablelands NSW (Queanbeyan-Palerang). The register
address and the lot/plan are below and in Mangiri\Site data\private_notes.md on Brett's PC; never put them in anything
shared. Map name: "Mangiri", area "Mongarlowe, NSW".

- NSW property register: property id 468928, register address Northangera Road, Budawang, lot 3 DP629016.
- Neighbouring lot to the south of the road strip: register "446", property 468883 (not loaded; Brett: this lot only for now).
- The register property is a MultiPolygon of three parts: 32.99 ha (the main lot north of the road strip, used as the
  map's lot), 8.43 ha and 1.62 ha south of a ~20 m strip. The two small parts are drawn as a thin dashed outline
  (terrain.json `lotParts`) but are not in the lot statistics.

## Built 25 Oct 2026 (trial v38)
- Pack: NSW 5 m DEM (2 km window, MGA zone 55), 10 m catchment DEM (8 km, not needed: the catchment closes inside
  the 2 km window), SILO daily 1995–2025, imagery dates (Braidwood block, captured 28 Jan 2014, 50 cm).
- Aerial: the imagery server refused custom-size images, so scripts/analysis/mangiri/stitch.py stitches the zoom-17
  web-map tiles (about 0.97 m per pixel) and reprojects them onto the 2 km MGA window. The inset_tiles_z19/z20 folders
  held only index.json (no tiles came back), so there is no close-up aerial.
- Focus area (terrain.json `focus`, scripts/analysis/mangiri/focus.json): the clearing round the driveway end, the
  buildings and the partly cleared ground running north-east, traced from the stitched aerial, about 4.5 ha. The map
  opens zoomed to it.
- Build: python3 scripts/analysis/mangiri/prep.py (stages expected under /mnt/user-data/uploads).

## Key numbers
- Lot 33.0 ha; elevation 632–671 m (window 623–698 m); focus area 657–667 m.
- Slope (lot): 69% under 10%, 26% 10–18%, 4% 18–25%, 1% 25–33%, ~0% steeper.
- Catchment draining through the lot 51.8 ha (inflows 9.6, 3.5 and 1.4 ha); outlet on the west/north-west side, 20.2 ha.
- Rain 904 mm a year (SILO 1995–2025). Sun (terrain only): 8.9 h winter, 11.6 h equinox, 13.9 h summer.

## Buildings vs the lot line (from the 2014 aerial, ~1 m pixels; boundary ±1–2 m)
About nine roofed buildings in the clearing. Five sit wholly inside the main lot (the big shed and four smaller roofs),
one straddles the southern line, and three lie mostly in the ~20 m strip south of it (the strip between the main lot
and the two small parts). By roof area roughly 70% is inside the lot, 30% outside.

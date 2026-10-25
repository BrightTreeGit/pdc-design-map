# Changelog: PDC Design Map

Newest first. Version numbers match the published map and the git tags (`v77`, `v76`…).

**How this was made.** From v77 on, entries are written as each change is published. Earlier entries were rebuilt by comparing the saved copies of the map code: tools, layers, panels, buttons and drawing types added or removed between each pair. The code behind each entry is exact. Where no copy was saved for every version, the entry covers a range (for example v66–v68), meaning the change landed somewhere in that range. Small fixes and wording tweaks don't show up in that comparison, so they're only listed where known. Times are Brisbane time.

## Version index
Each version is one commit on the `main` branch. Click a link to see the code exactly as it was, and what changed.

| Version | Saved | Commit |
|---|---|---|
| v86 | 23 Oct 2026 07:20 | see commit history |
| v85 | 23 Oct 2026 07:00 | (published, no separate commit; included in v86) |
| v84 | 23 Oct 2026 07:10 | see commit history |
| v83 | 22 Oct 2026 15:25 | see commit history |
| v82 | 22 Oct 2026 11:05 | see commit history |
| v81 | 22 Oct 2026 11:00 | see commit history |
| v80 | 22 Oct 2026 10:55 | see commit history |
| v79 | 22 Oct 2026 10:40 | see commit history |
| v78 | 22 Oct 2026 10:30 | see commit history |
| v77 | 22 Oct 2026 05:45 | [aa9b476](https://github.com/BrightTreeGit/pdc-design-map/commit/aa9b476c9e2b1fc3d5c8d2eb783c391851c92325) |
| v75–v76 | 21 Oct 2026 22:36 | [97ce1ac](https://github.com/BrightTreeGit/pdc-design-map/commit/97ce1ac25c0d146368745872be00726181241d2f) |
| v74 | 21 Oct 2026 18:18 | [383f2db](https://github.com/BrightTreeGit/pdc-design-map/commit/383f2dbf3dd5fcedb35606207343f9403a66e0af) |
| v71–v73 | 21 Oct 2026 17:21 | [e037170](https://github.com/BrightTreeGit/pdc-design-map/commit/e0371701597a1a12d04ac65f6021ff37eb0a5786) |
| v69–v70 | 21 Oct 2026 16:44 | [2dcc51d](https://github.com/BrightTreeGit/pdc-design-map/commit/2dcc51dc5e7ead1e120fbb8538e2fd077e73cb4e) |
| v66–v68 | 20 Oct 2026 15:32 | [9d4bc4b](https://github.com/BrightTreeGit/pdc-design-map/commit/9d4bc4b098ad25a9c1369781991ee8e16b6df514) |
| v65 | 20 Oct 2026 15:15 | [133bad0](https://github.com/BrightTreeGit/pdc-design-map/commit/133bad0e680f398b2b8a1f3b929f24c883d0af3f) |
| v64 | 20 Oct 2026 15:07 | [e166c43](https://github.com/BrightTreeGit/pdc-design-map/commit/e166c4358e78238aa0a38966955868408692a034) |
| v60–v63 | 20 Oct 2026 14:32 | [05c7fef](https://github.com/BrightTreeGit/pdc-design-map/commit/05c7fef6b1f3e6d519efc2f4884d51e733138b37) |
| v59 | 20 Oct 2026 11:38 | [c379fba](https://github.com/BrightTreeGit/pdc-design-map/commit/c379fbaf009a1ab5d45a6458334533a26c32f76c) |
| v58 | 20 Oct 2026 11:14 | [dad8e5d](https://github.com/BrightTreeGit/pdc-design-map/commit/dad8e5d521a2f0da80fde01278e0285a501391e9) |
| v54–v57 | 20 Oct 2026 11:06 | [abe484d](https://github.com/BrightTreeGit/pdc-design-map/commit/abe484dd4a65fc4324f493850a64053220ad797a) |
| v50–v53 | 20 Oct 2026 09:38 | [1f22e98](https://github.com/BrightTreeGit/pdc-design-map/commit/1f22e98f496055618d72520a2ec0ad76e4fe1690) |
| v28–v49 | 20 Oct 2026 07:15 | [ac5eb51](https://github.com/BrightTreeGit/pdc-design-map/commit/ac5eb513340e435acccaa30af78b465be58231b2) |
| v27 | 19 Oct 2026 11:57 | [5222062](https://github.com/BrightTreeGit/pdc-design-map/commit/5222062ec5a140528dcedf4b637e58374384bd41) |
| v26 | 19 Oct 2026 05:27 | [6cc3f73](https://github.com/BrightTreeGit/pdc-design-map/commit/6cc3f739f88974908c77e821eb90235b79ab9643) |
| v16–v25 | 18 Oct 2026 23:51 | [2431f35](https://github.com/BrightTreeGit/pdc-design-map/commit/2431f351940fe300f6554980c8b0cb983ca98439) |
| v15 | 18 Oct 2026 22:08 | [bb766f1](https://github.com/BrightTreeGit/pdc-design-map/commit/bb766f13db6928a9c9e3ddf34d0371477f03795b) |

The v77 row is the commit that added this index; later versions are listed in the commit history.

## Trial and beta maps
Experiments are published to the trial map (https://claude.ai/artifact/CCUp4A9sdGDGXoKdh4ocpL) from a trial branch, and the
per-group mapping-only beta maps (docs/beta-maps.md) from `beta/group-maps`. They have their own numbers ("Trial v38",
"Beta v2"), separate from the live map's v-numbers, and reach the live map only when Brett approves.

| Version | Saved | Branch | What |
|---|---|---|---|
| Trial v39 | 25 Oct 2026 | trial/willow-vale-team | Draw, select, move and reshape in 3D; upright 3D labels |
| Beta v2 | 25 Oct 2026 | beta/group-maps | Mangiri beta map (8th group) |
| Trial v38 | 25 Oct 2026 | trial/willow-vale-team | Mangiri site |
| Beta v1 | 25 Oct 2026 | beta/group-maps | Mapping-only maps for 7 groups |
| Trial v37 | 25 Oct 2026 | trial/willow-vale-team | Regenify site |

### Trial v39 (25 Oct 2026)
**Added**
- Drawing in the 3D view: with 3D open, pick a tool in the Draw tab and click on the ground to place points, corners
  or a tank; the shape follows the terrain as you draw, with the side length and area shown by the cursor. Finish with
  double-click, Enter or the Finish button; Esc or Cancel stops, Backspace takes off the last point, as in 2D.
- Select and edit in 3D: click a drawing to select it; drag inside it to move it, drag a white corner to reshape it,
  and the round-arrow and curved-arrow handles resize and rotate it, all sitting on the ground. Changes save and undo
  (Ctrl+Z / Ctrl+Shift+Z) exactly as in 2D. Dragging empty ground still turns the view; a tap or click (no drag)
  places a point, so it works with a finger on a phone too.
- Upright labels in 3D: zone and feature names stand up facing you at the middle of each shape, readable from any
  angle, and step aside or hide so they don't pile up (labels behind a hill are hidden).
- QA test `scripts/qa/check_3d_edit.py`: draws, selects, moves, reshapes and undoes in 3D on one site, and taps on a
  touch screen.

**Changed**
- While you drag in 3D only the shape you are moving is redrawn; the rest of the map is draped again once at the start
  and end of the drag. The 3D view now refreshes by itself after a change (no need to press Refresh).
- The sketch, box and auto-shape modes are hidden in 3D (dragging turns the view there); use them in 2D.

**Fixed**
- 3D labels no longer lie flat and sideways along the shape, and the selection handles no longer hang in the air on
  dashed lines.
- The drawing bar and the pop-up messages now show above the 3D view (they were hidden behind it). The drawing bar
  also hides properly when the map is opened straight from the repo for testing.
### Beta v2 (25 Oct 2026)
**Added**
- A mapping-only beta map for Mangiri, built and checked like the other seven (they were not rebuilt).

### Trial v38 (25 Oct 2026)
**Added**
- Mangiri (Mongarlowe, NSW) in the site picker: NSW 5 m elevation, contours, flow lines, catchments, slope and the
  other terrain layers, SILO rain (1995–2025), and the 2014 NSW aerial stitched from the imagery server's map tiles.
- A "Focus area" outline for sites that have one: Mangiri's follows the clearing round the driveway end and the
  buildings, and the site opens zoomed to it. The other parts of a multi-part property show as a thin dashed outline.
- Layer list says where the boundary and focus area come from (e.g. "NSW cadastre 2026", "NSW aerial 2014").

**Fixed**
- NSW sites built from the 5 m elevation no longer say "LiDAR survey" under the Layers tab, and the A3 sheet footer
  no longer calls an NSW boundary the Queensland cadastre.

**Changed**
- Site extras tool: each geology request gives up after 60 seconds, and a site where the geology services have no
  polygons (Willow Vale) is remembered as "checked, none there" so the run doesn't hang on it; `--refresh-geology`
  asks again. Mangiri added to the extras, ingest and seasonal outlook tools.

---

## v86 (23 Oct 2026, 07:20)
**Changed**
- Privacy zones now show the area at low detail, like a standard satellite view (10 m pixels by default; 5 or 30 m to choose), fading out over about 15 m beyond the edge so the area doesn't draw the eye. Other looks per zone: map colours (tree cover and open ground only) or blank. The zone's own outline and label only show when it is selected.

## v85 (23 Oct 2026, 07:00)
**Added**
- Draw → Zones → Privacy zone: a landholder can hide part of the map. Photos (government aerial, photo history, uploads, drone) and shading are covered inside it for everyone, including prints, 3D and exports, and map items inside are hidden (optional). The drone processing script also blanks privacy zones from the surface model and photo.

## v84 (23 Oct 2026, 07:10)
**Changed**
- Phones: the map fills the screen and the panel is a bottom sheet (peek, half, full). Drag or tap the handle, or drag the tab bar; the tabs have icons. Picking a drawing tool drops the sheet to peek. Scrolling now reaches the bottom of every tab in the app. (Tested on the trial map first.)
- Light & lopping planner: light is now also given as a share of open-field light, counting the open sky (diffuse light) as well as direct sun, with a map view for it, the area with 30% light or more, and what crops suit that light.

**Added**
- Light & lopping planner: "Compare winter, equinox and summer" table, before and after the lopping.
- Tools → Drone survey changes: after a drone flight, the changes found against the 2022 LiDAR (trees gone, new roofs, new clearings) show as pink dashed outlines to accept or reject one by one. Accepted trees gone become lopping jobs marked Built, so the light planner counts them.

**Fixed**
- Saving test lopping as planned jobs always used "Now"; it now keeps the stage you pick.

## v83 (22 Oct 2026, 15:25)
**Added**
- Grazing & paddocks (Tools): goat fencing. It measures the fence line round all goat zones and paddocks along the ground, counting shared sides once. For mesh, electric wires or portable netting it lists rolls, posts, strainers and gates, with a rough cost from a price per metre you enter.
- Grazing & paddocks: drinking water. Litres a day for the herd (cool or hot weather, extra for animals in milk), a year's total, storage for a chosen number of days and trough advice. One button adds it to the water balance.
- Water balance & tanks: a field for animals' drinking water (litres a day, all year).

**Fixed**
- Sites with no dams or ponds drawn stopped loading part-way since v77 (the dam list's Show all / Hide all buttons were missing). Fixed.

## v82 (22 Oct 2026, 11:05)
**Added**
- Light & lopping planner: "✓ Already removed" in the top bar. Click each tree cut since the 2022 LiDAR survey; it saves as a lopping job marked Built at stage Existing, and the planner treats that crown as gone.
- "Start from": Today (the survey plus trees already removed) or the 2022 survey as measured.
- "Add planned lopping jobs": none, Year 0–1, to year 2, to year 5, or all. Saved jobs are applied by their stage, so you can compare the light at each stage. Mark a job Built when it's done and it moves into today's light.
- Saved jobs show on the map while the planner is open: grey for done, orange for planned (dashed when that stage is switched off).

**Changed**
- Test-lopping buttons renamed "Test thin" and "Test remove". Saving them now asks for a stage and saves them as Proposed without leaving the planner, and undo (Ctrl+Z) works on them.

## v81 (22 Oct 2026, 11:00)
**Fixed**
- Light & lopping planner: where drawn zones overlap (the Hairpin Fruit Forest and Zone 3 Broadacre), a click in the overlap picked the smaller zone. Now every zone under the click is offered as a button, plus "Square", and a zone you've selected first is used by default.
- The light result is drawn as crisp 1–2 m cells instead of a smoothed blur, so it no longer looks stretched when zoomed in on a small bed.

## v80 (22 Oct 2026, 10:55)
**Changed**
- Light & lopping planner: the test square is now a slider from 10 to 160 m (default 30 m, was 120 m), and can also be changed from the drawing bar while you work.
- Squares up to 50 m are worked out at 1 m detail instead of 2 m.

**Added**
- "Fit to the bed or zone I click inside": click inside a drawn bed or zone (up to 160 × 160 m) and the planner tests exactly that shape, outlined on the map, with its area shown. The smallest shape under the click wins.

## v79 (22 Oct 2026, 10:40)
**Changed**
- *Observation* (with categories such as Water / drainage) is now in the basic drawing tools, not only the Designer level.
- Planting niches now use wet spots marked on the map: the new eastern-catchment rock pool counts as wet ground (10 m around it). Niche data also records the hairpin fruit forest as drawn (about 170 m², 0.3 h of winter sun at ground today).

## v78 (22 Oct 2026, 10:30)
**Added**
- Bright Tree forest layer *Planting niches (light, slope, moisture, frost)*: where each kind of planting fits today, from light at ground (terrain plus measured crowns), slope, wetness from water flow and cold-air pooling. Classes: full sun, part sun, dappled shade, deep moist shade, openable with lopping, forest only (over 27°), plus frost-prone dots.
- Numbered best patches within about 80 m of the house, focused on the hairpin fruit forest.

## v77 (21 Oct 2026, 22:37)
**Added**
- Layers → *Dams and ponds (show / hide each)*: a tickbox and Zoom for every drawn pond, dam wall and rock pool, and for the computed pond sites P1–P8, plus Show all / Hide all.
- Features → *Hide on map / Show on map* for any drawn item; hidden items carry a "hidden" tag in the list.

**Changed**
- Hidden dams and items are left out of the water totals and can't be clicked. Hiding only affects your own browser.

**Project**
- Version archive set up: this repository, changelog and data snapshots.

## v76 (21 Oct 2026, 22:21)
**Added**
- Photo history extended back to 1953 with scanned film photos for 1953, 1954, 1979, 1981, 1988, 1991 and 1997. They were lined up by matching gully tree lines and creeks to the LiDAR flow lines, accurate to about 20–40 m, and the slider labels them as scanned.

**Not included**
- 1958, 1961, 1967, 1971, 1974, 1975, 1977, 1986, 1992 and 1995 (no reliable match).

## v75 (21 Oct 2026, 18:20)
**Added**
- Layers → *Photo history (slider)* for Bright Tree: 18 government orthophotos from 1994 to 2022, with capture dates and detail level, Earlier/Later buttons, ▶ Play, Fade, the ← → keys and a year badge on the map.

**Project**
- First full snapshot of all drawings and notes (data-snapshots/2026-10-21_v74).

## v74 (21 Oct 2026)
**Added**
- Forest layer *Growing power (growth vs typical)*.
- Tools → *Light & lopping planner*: pick a spot to see winter, equinox and summer sun hours; edit crowns; *Suggest the trees to lop*; save the results as *Lopping / thinning job* items (new drawing type).

## v71–v73 (21 Oct 2026)
**Added**
- Forest layers from the LiDAR (2008–2022): canopy height and tall trees, canopy growth since 2008, dense understorey, fuel structure, and light at ground in winter and at the equinox.
- Root protection rings around big trees, and warnings for big trees within falling distance of buildings, tanks or gathering spots.

## v69–v70 (20–21 Oct 2026)
**Added**
- Undo and redo for every edit.
- Multi-select (Shift-click, Shift-drag or the ⬚ select tool) with delete, duplicate, clear and change stage for many items at once.
- Duplicate and lock, a right-click menu, and deleting a single corner point.
- *Notebook* tab per site: thoughts, differences, questions and decisions, with replies. You can also add a note about a feature from its panel.

## v66–v68 (20 Oct 2026)
**Added**
- Layers → *Design overlays*: hand sketches and site plans shown above the photo and terrain (used for Ange's NAC sketch).
- Drawing tools in unlock levels (basic → more), with a *Recently used* row.
- *Other zone* (custom zones) with your own names and colours.
- Deleting an item shows a toast with Undo (replacing the old Keep/Delete prompt).
- Live updates reconnect by themselves after a dropped connection.
- 16 new drawing types: fruit tree, native tree / gum, shrub, herb / kitchen bed, raised or wicking bed, groundcover, screen planting, tree protection zone, rain garden, retaining wall / terrace edge, steps, driveway area, pergola / trellis, clothesline, bushfire asset protection zone, other zone.

## v65 (20 Oct 2026)
**Added**
- NAC (small block, NSW) added as a site.

## v64 (20 Oct 2026)
**Added**
- Tools → *Micro-hydro power*: pick intake and turbine sites, see head, pipe friction and power, and save the scheme to the design.

## v60–v63 (20 Oct 2026)
**Added**
- Tools → *Cross-section A–B*: draw up to 3 sections, with lettered ends and profiles, available on presentation sheets.

**Changed**
- Nimbin site renamed *Firefly Farm*.

## v59 (20 Oct 2026)
**Added**
- 3D view panel on presentation sheets, with automatic best viewing direction.

## v58 (20 Oct 2026)
**Changed**
- Presentation sheet is now an A3 PDF (previously PNG only) with a *Suggested set* of panels. Panels: legend, north arrow and scale, locator inset, coordinate grid, zone table, water summary, water balance by month, sun summary, sector wheel, staging timeline, planting list, feature schedule, contour profile, climate chart, fire panel, slope bar, and numbered callouts. Sheets can be landscape or portrait, with ink-saving and clean-paper styles.

## v54–v57 (20 Oct 2026)
**Added**
- Names drawn on structures and features, with smart label placement.
- New drawing types: cabin / accommodation, toilets / amenities, shipping container, pond / dam water outline.

## v50–v53 (19–20 Oct 2026)
**Added**
- Layers → *Prospects (computed sites)*: pond and small dam sites, building pads, header tank and gully flats found by scanning the terrain, with Zoom and *Add to my design*.
- Zone 0 counts as roof catchment until a building is drawn.

**Changed**
- "Bright Tree (Gemini data)" renamed "Bright Tree (auto data)".

## v28–v49 (19–20 Oct 2026)
**Added**
- PDC sites: a site picker for Bellbunya, Bright Tree (manual and auto data), Nimbin, Noosa Forest Retreat, Regenify and Willow Vale, plus a "Back to Bright Tree" banner.
- 3D view (terrain, photo and design) with a sun toggle and ▶ Play day.
- Sun times and sun track for the site.
- Goat zone (browse and paddock) drawing type.

## v27 (19 Oct 2026)
**Added**
- Pipe sizing: length, friction loss and maximum flow for drawn pipes.

## v26 (19 Oct 2026)
**Added**
- Property boundary editor: redraw the lot and reset to the original.

## v16–v25 (18 Oct 2026)
**Added**
- New layout: Layers / Draw / Features / Plan / Tools tabs with collapsible sections.
- Tools:
  - dam & pond calculator
  - water balance & tanks
  - track route finder
  - distance & area
  - height & water pressure
  - bushfire site check
  - grazing & paddocks
  - A3 presentation sheet (PNG)
  - 3D print
  - export to GeoJSON or KML
- Shade at a chosen date and time, with ▶ Play the day.
- Ground change since 2008 and 2014.
- Staging from now to years 5–10.
- Feature status (existing, proposed, done).
- Tasks, observations with photos, weed watch, climate and soil panels, zone areas.
- About 30 new drawing types: dam wall, reed bed, soak pit, greywater zone, irrigation line, rock pool, road, gate, parking, creek crossing, firebreak, shed, carport, greenhouse / zome, solar array, nursery, chickens, beehives, worm farm, compost bays, herb spiral, mushroom logs, hugelkultur, habitat boxes, seating, paddock, observation and more.

## v15 (18 Oct 2026): earliest saved copy
- Bright Tree terrain map from 1 m LiDAR: relief and hillshade base maps, slope, aspect, cold-air pooling, and winter, equinox and summer sun hours.
- 1 m and 5 m contours, flow lines, catchment and keypoint candidates.
- About 35 drawing types, including zones 0–5, sectors (sun, wind, fire, cold air, view), water features, plants and buildings.
- Click any feature to see area, length, slope and an elevation profile measured from the LiDAR.

*Versions before v15 weren't saved.*

# Changelog: PDC Design Map

Newest first. Version numbers match the published map and the git tags (`v77`, `v76`…).

**How this was made.** From v77 on, entries are written as each change is published. Earlier entries were rebuilt by comparing the saved copies of the map code: tools, layers, panels, buttons and drawing types added or removed between each pair. The code behind each entry is exact. Where no copy was saved for every version, the entry covers a range (for example v66–v68), meaning the change landed somewhere in that range. Small fixes and wording tweaks don't show up in that comparison, so they're only listed where known. Times are Brisbane time.

---

## v77 (22 Oct 2026, 22:37)
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

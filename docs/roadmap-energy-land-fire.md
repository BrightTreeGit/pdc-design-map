# Design Map roadmap: energy, land and fire tools

Lessons from the Bright Tree solar, trees and gas work (11–12 Nov 2026), and the tool changes they point to. The reports are "Bright Tree solar and tree plan" (claude.ai/artifact/382NhxHDVZv9SNfUaNCQ3e) and "Bright Tree house solar, trees and backup".

## What we learned

1. **The LiDAR is out of date where it matters most.** T1, T6 and the Zone 3 solar area had all been cleared since 2022. Each one changed the results. The tools need a quick way to say "cleared since", plus a drone canopy refresh.
2. **Arrays must come from drawn features, not typed coordinates.** The hairpin array was first modelled about 20 m from its real spot, and the answer flipped (1.8 against 3.1 kWh per kW). Every array should start from a polygon on the map.
3. **The real limit is often inverter inputs, not roof space.** Four inputs, one string each, with 600 V or 1,000 V caps, decided the plan more than kWh per kW did.
4. **Measured fuel beats planning loads.** The gas receipts showed about 3 kWh a day of electric replacement, not 7. The load builder should start from what is actually being bought (kg of gas, litres of petrol).
5. **Tree work needs three answers at once:** sun gained, vegetation category (X or B, lop or clear), and bushfire clearing distance (1.5 × canopy height). Today these come from three separate overlays and hand work.
6. **People decide in stages.** The useful output was a staged roadmap with flat-battery days at each step, not a single total.
7. **Removed trees should flow through.** Marking a lop job "Already removed" already feeds the Energy tool's "today" run, so keeping the lop list current keeps the solar numbers current.

## Roadmap

### Next trial version (after Brett's approval)

| # | Tool | Change | Why |
| --- | --- | --- | --- |
| 1 | Energy | **Tree ranking panel:** top 10 trees by kWh a year, each with height, distance and bearing from the house, vegetation category, bushfire class, and an "Add to lop list" button that writes the notes | Replaces the hand-built T1–T9 list |
| 2 | Lop list / layers | **Rules at a point:** clicking a lop job shows the RVM category and regional ecosystem, "lopping only, keep alive" for Category B, the bushfire class, and whether it sits inside 1.5 × canopy height of a building | Lesson 5 |
| 3 | Fire | **Clearing distance ring:** for each building, a ring at 1.5 × the predominant canopy height (from the canopy grid), and a running total of cleared m² against council's 600 m² | Lesson 5 |
| 4 | Energy | **Array from a zone:** a "Make solar array here" action on any drawn zone or roof, which takes bearing and pitch from the user | Lesson 2 |

### Following versions

| # | Tool | Change | Why |
| --- | --- | --- | --- |
| 5 | Energy | **Inverter planner:** number of inputs, arrays assigned to inputs, string voltage cold and hot at 600 V and 1,000 V, total panels against the inverter (133% STC note), and a warning for mixed directions in one string | Lesson 3 |
| 6 | Energy | **Load builder from receipts:** gas kg a year to heat pump and induction kWh (COP, efficiencies, hot water and cooking split), and petrol L to EV kWh | Lesson 4 |
| 7 | Energy | **Roadmap mode:** an ordered list of steps (tree work, arrays) that runs each one and draws the output and flat-battery chart | Lesson 6 |
| 8 | Canopy | **"Cleared since" polygons and drone canopy refresh:** zero the canopy grid inside a drawn area, or replace it with an OpenDroneMap surface over the LiDAR ground | Lesson 1 |

### Later

| # | Tool | Change |
| --- | --- | --- |
| 9 | Land | Flag features drawn on mapped Category B remnant (for example the Zone 3 solar area), with a gentle "check the clearing rules" note |
| 10 | Energy | Optimiser and mismatch estimate when a string spans two directions or shade levels |
| 11 | Fire | Fuel-reduction view: palms and understorey cleared near buildings, shown against the bushfire overlay |
| 12 | Energy | Per-site energy report export (one page), matching the Docs report layout |

## Done in this session (trial map data only, no code change)

- Lop jobs T1–T9 on the Bright Tree trial map, with T1 and T6 marked "Already removed".
- Library files in "03 Water, energy and waste": roadmap, site plan, vegetation and bushfire maps, options and zones CSVs, and the gas-to-electric payback.

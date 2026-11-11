# Energy tool (Design Map, Tools → Energy)

The engine lives in `map/index.html` (block starting "Energy tool: solar arrays, shade, SILO weather"); `energy_block.js` is a copy for reading.
- Arrays are `solar` features (polygons) with a `pv` object: bearing, tilt, h (panel centre above ground), panel, count, device, per (panels per string), edge, feeds.
- Shade: sky transmittance per array from dem1/dem2 + canopy grid (CG), lop list applied via cgAt().
- Weather: silo_full.json (rad10, tmax10, tmin10); Erbs daily diffuse split; Collares-Pereira & Rabl / Liu & Jordan hourly spread.
- Test: `python3 test_bright_tree_house.py` with `python3 -m http.server 8766` running in map/ (adds the house roof faces, runs, writes report.pdf and r2.json).
- `house_arrays.json`: house roof faces derived with the roof_shade.py method (LiDAR footprint centre, ridge 141°).

# Drone survey processing

1. Fly the missions (drone/missions, field checklist artifact: https://claude.ai/artifact/CRW5fesR1Cep53cmWykCDe).
2. WebODM: boundary = BrightTree_boundary.geojson; orthophoto resolution 5 cm, DSM resolution 10 cm (keeps files manageable).
3. Stage dsm.tif (+ odm_orthophoto.tif) and run:
   python3 scripts/drone/process_drone.py --dsm dsm.tif --ortho odm_orthophoto.tif --out <dir> --date YYYY-MM-DD
   -> drone_changes.json (summary + suggestions), canopy_grid_drone.png, drone_ortho_1m.jpg (+ bounds).
4. Write each suggestion to the map database collection `suggest` (Bright Tree; `<site>_suggest` for other sites) with ArtifactData batch.
   They appear in Tools > Drone survey changes for review (v84+).
5. Once reviewed, publish canopy_grid_drone.png as the light planner's "today" canopy (next step: a switch in the planner).
Tested on a synthetic flight (2022 LiDAR surface with two crowns removed, a 6 x 8 m roof and a cleared strip, shifted 3 m E, 2 m S, +25 m): shift and offset recovered exactly, all changes found.

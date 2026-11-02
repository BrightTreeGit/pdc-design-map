
## Drone quick-look (2 Nov 2026, unpublished, trial branch)
- 275 nadir photos flown 26 Oct 2026 (DJI, 24 mm eq., about 75 m AGL terrain-follow). Only 66 staged so far (every 3rd up to photo 198; the PC
  disconnected). GPS-placed mosaic, no photogrammetry: scripts/drone/quicklook/gps_mosaic.py (footprint = 1.394 x AGL, AGL = abs alt - 45 m
  geoid guess - LiDAR ground). Placement within ~5-10 m.
- Added as the newest run of the photo-history slider: history/h2026_drone.jpg (drone part over a dimmed 2022 photo). phLabel handles r.drone.
- To finish: stage photos 201-300 (south and east), rerun gps_mosaic.py 45 1.6 549 516 1600 1600 <out>, rebuild h2026_drone.jpg, QA, publish
  as Trial v59. A real orthomosaic still needs WebODM on Brett's PC.

Retired scripts (kept for the record, not copied to the laptop)
- fetch_elvis.py + Annwn - get elevation (ELVIS).bat: the ELVIS download host (elvis2018-ga.fmecloud.com) no longer resolves
  (Geoscience Australia moved ELVIS to elevation.fsdf.org.au, which needs a browser order). Queensland sites now get 1 m LiDAR
  straight from the state elevation service via fetch_qld_site.py; NSW sites via scripts/lidar/fetch_nsw_site.py.
- fetch_terrain_tiles.py + Annwn - get placeholder elevation.bat: the level-ground placeholder used while the state server was
  offline. Not needed now that the real LiDAR is in.

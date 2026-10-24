PDC tools: one place for the download scripts
==============================================
First time on a computer: double-click "0 - Setup" once. After that, double-click any "get ..." file;
results go into that site's own folder (or "Services data" / "Site extras" for the all-sites ones).
Keeping one copy of each script here means a fix reaches every site at once.

  0 - Setup (run once, installs Python packages).bat   installs requests, pillow, numpy

  Annwn - get site data.bat                     boundary, 1 m LiDAR elevation, aerial and rainfall -> Annwn\Site data
  Bellbunya - get photo history.bat             all aerial photos 1950s to now -> Bellbunya\Aerial and Google Maps
  Noosa Forest Retreat - get photo history.bat  same for Noosa Forest Retreat
  Bright Tree water - get heights to the coast.bat   the creek's fall from Bright Tree to the sea
  Get power network (Energex).bat               poles, pillars and street lines for the Queensland sites -> Services data
  Get site extras (rain, ecosystems, species).bat   30-year daily rain (all sites), Queensland regional ecosystems,
                                                Atlas of Living Australia species within 1 km -> Site extras
                                                (safe to run again: it only fetches what is missing, e.g. ALA after a 503)

When a run finishes, tell Claude "<site> site data is ready", "<site> photo history is ready",
"services data is ready" or "site extras are ready", and the results go into the map.
Master copies of every script are kept in the private GitHub archive (BrightTreeGit/pdc-design-map, scripts/tools/).

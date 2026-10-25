# Separate artifacts

- East Ridge Catchments: https://claude.ai/artifact/Xq2z1pgS9VU66tiJ6DFYCd (contours and catchments east of Bright Tree, 2022 LiDAR). Build: scripts/analysis/east/build.py then page.py.
- Bright Tree Water: https://claude.ai/artifact/AxpMF7rbPaxmaiKh7Qc2Vw (route of Bright Tree water to the sea, 15 m Qld DEM). Build: _tools fetch_water_to_coast.py, then scripts/analysis/coast hydro.py, anal.py, estuary.py, assets.py, page.py.

- Group beta maps (mapping only, one per PDC group): see docs/beta-maps.md for the seven links. Build: scripts/beta/build_beta.py, QA: scripts/qa/check_beta.py.

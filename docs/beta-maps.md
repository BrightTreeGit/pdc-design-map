# Group beta maps

One mapping-only map per PDC group, so each group can be shared as **Editor** on its own map (on Brett's personal
account, Editor is the only role that lets outside invitees save drawings). Each group downloads only its own site's
data, and the tools stay out.

Published 25 Oct 2026 as Beta v1, from branch `beta/group-maps` (full map at trial v37 plus the 25 Oct site extras).
Beta v2 (25 Oct 2026) added Mangiri, built from trial v38; the other seven were not rebuilt or republished then
(rebuild them with `build_beta.py all` to pick up trial v38's map changes: focus-area outline, NSW source wording).
Beta v3 (25 Oct 2026) rebuilt and republished Mangiri only, from trial v40 (whole lot as the focus, 3D editing,
green firebreak tools).

| Group | Site id (db prefix) | Beta map | Seeded drawings |
|---|---|---|---|
| Firefly Farm (Group 1) | `nimbin-group` | https://claude.ai/artifact/5RQZ3yddKCudVZcTXPeWUb | 45 features |
| Bellbunya (Group 2) | `bellbunya` | https://claude.ai/artifact/McJHxqLkxs9jmJxwPSFTey | 34 features, 1 plan overlay |
| Willow Vale (Group 4) | `willow-vale-team` | https://claude.ai/artifact/3FE1jhfh4hmFi8KLZq8u1c | 47 features |
| Noosa Forest Retreat | `noosa-forest-retreat` | https://claude.ai/artifact/MX4e2unz4LUnYcZiqs8EpC | 4 features |
| NAC | `nac` | https://claude.ai/artifact/EgJNQ5fnEdS4t2MfFRokZ9 | 93 features, 2 overlays |
| Annwn | `annwn` | https://claude.ai/artifact/8Aw2uJ8dpYfBoBinq5ehET | 25 features, 2 overlays |
| Regenify | `regenify` | https://claude.ai/artifact/JwYsuca86oQAeydC41vNbw | none yet |
| Mangiri (Mully) | `mangiri` | https://claude.ai/artifact/K75efkDtfLMqjyxQALt7Px | none yet |

All eight are private until Brett shares each one (Share menu → invite the group as Editor).

## What's in a beta
- **Layers**: base maps (relief, hillshade, aerial), terrain analysis overlays with source and year in each legend,
  photo history (Bellbunya, Noosa Forest Retreat), uploaded plans and photos, dams list (show/hide only), services,
  native vegetation, geology, rules and hazards, flow lines, contours, prospects, and **Wildlife recorded nearby (ALA)**:
  names and counts only, no locations; threatened species listed as counts.
- **Draw** and **Features**: every drawing tool, the features list and editor, undo/redo, lock, duplicate, privacy zones, 3D view.
- Same database collection names as the trial and live maps (`<site>_features`, `<site>_imagery`, `<site>_settings/zones`,
  `<site>_meta/lot`), so drawings copy straight across in either direction.
- Beta terms (shown once) and a footer: © Bright Tree, beta access for that group only, the site data stays theirs.
- Capabilities: db, user (names), comments (Send feedback only), assets (Editors upload plans and photos).
  Downloads is not declared, since nothing in the beta exports files.

## What's left out
Plan, Notes, Tools and Site tabs and the code behind them: water balance and tank simulations, dam calculator and
dry-season simulation, season outlook and analogue years, 137-year climate record, IFD, soil and wildlife cards,
energy, light and lopping planner, route finder, ram and hydro pumps, natural patterns, A3 presentation sheet,
3D print export, GeoJSON/KML export, design checks, brief and notebook. The site picker and every other site are gone too.
The data files only those tools read (silo_full, silo_long, outlook, rain_daily, ifd, soils) are not published.

## Rebuilding after a map change
```
python3 scripts/beta/build_beta.py all          # rebuilds beta/<site>/index.html and copies each site's data
python3 scripts/qa/check_beta.py                # must print OK for all eight
```
Then republish each page with the Artifact tool: `file_path` beta/<folder>/index.html, `root` beta/<folder>,
`files` = the keys of beta/<folder>/files.json, same URL. The copied data files are not committed (they are
rebuilt from map/sites); only index.html and files.json are.

`build_beta.py` edits a copy of map/index.html: every edit must match exactly once, so if the full map changes
underneath, the build stops and names the edit that no longer fits. `strip.cjs` then empties the removed tabs'
functions and deletes every function and table nothing else uses any more (about 230 KB of the 495 KB script),
and esbuild minifies the result. The readable source stays in this repo only.

## Privacy
- Page and data scrubbed of street names and numbers, lot/plan numbers, emails and phone numbers (QA checks it).
- Seeded drawings: one Bellbunya note had an email and a surname (removed); "Browns Rd" became "the road";
  the site-plan drawing number was dropped from 15 notes.
- NAC's "Google satellite, recent" overlay was **not** copied: the screenshot shows the street address and house numbers.
  The other five overlays were checked by eye and copied (the NAC plan and Bellbunya site plan already had addresses blanked).
- Images carry no EXIF.

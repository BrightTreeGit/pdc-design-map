# PDC Design Map: private archive

**Private repository: keep it that way.** It holds the map's source code, method and analysis scripts, and group site data.

The live map is a Claude artifact. This repository is the separate, permanent archive of every saved version, so any version can be looked at or brought back.

## What's in here
| Folder | What it is |
|---|---|
| `map/` | The map itself: `index.html` (the program) plus every layer image and data file it loads (terrain, canopy, aerial photos, photo history), one subfolder per site under `map/sites/`. |
| `data-snapshots/` | Exports of everything people drew and wrote in the map (features, notebook notes, imagery settings), dated. The live drawings live in the map's database, not in the code, so they are backed up separately. |
| `scripts/` | The download and analysis scripts: aerial photos and photo history, LiDAR and canopy, NSW sites, photo alignment, print sheets. |
| `CHANGELOG.md` | One line per version: what changed. |
| `VERSIONING.md` | How saving, comparing and reverting works. |

## Versions
Every published map version is one commit on `main` whose message starts with the version number (for example `v76: …`), matching the version number on the artifact. CHANGELOG.md has a version index with a link to each one; on GitHub, **Commits** shows them all, and clicking one shows exactly what changed.

Versions up to v76 were rebuilt from copies of the code saved at the time. Their descriptions come from comparing those copies, so they're accurate, but some entries cover a range of versions (for example v66–v68) because not every version was saved. See CHANGELOG.md.

Imagery © State of Queensland and NSW Spatial Services (CC BY 4.0). LiDAR from Elvis / Geoscience Australia.

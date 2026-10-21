# How versions are kept

## Three layers of safety
1. **This repository (the archive).** Every time the map is published, Claude commits the new code and files here with the version tag (v78, v79…) and a changelog line. Nothing is ever overwritten: old versions stay in the history for good.
2. **Data snapshots.** Drawings and notes live in the map's database, not in the code. Claude exports them to `data-snapshots/<date>_v<NN>/` before any big change and at least weekly.
3. **The artifact's own version history.** claude.ai keeps each published version too. That's handy for a quick undo, but this repository is the permanent, browsable record.

## Day to day (what to ask Claude)
- **"Save a version"**: commit and tag the current map with a note.
- **"What changed since v70?"**: Claude compares the two versions and lists the differences.
- **"Revert the map to v74"**: Claude republishes the v74 code to the same link (people's drawings are kept) and records the revert as a new version, so even the revert can be undone.
- **"Restore NAC drawings from the 21 Oct snapshot"**: Claude writes the saved drawings back into the map's database.
- **"Try X in a branch"**: for big experiments Claude works on a separate branch and a test copy of the map, then merges it into the live map once you're happy.

## Rules of thumb
- One live map link for everyone; versions and branches live here.
- Keep the repository private: it holds the method, scripts and site data.
- Big files (photos, layers) are fine here up to 50 MB each.

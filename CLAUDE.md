# Working on the PDC Design Map

- The live map is the claude.ai artifact https://claude.ai/artifact/UBiGj6XL3CwhpRCv6aZfEu. `map/index.html` plus the files under `map/` are its source: publish with the Artifact tool using `file_path` = map/index.html and `files` for any changed assets, passing the same `url`.
- Before every publish, run `python3 scripts/qa/check_map.py` (loads every site headless; exit 1 = don't publish).
- Every publish = one commit on `main`. The message starts with the artifact version number ("v78: …"). Add a matching entry at the top of CHANGELOG.md (Added / Changed / Fixed, plain language) and a row in its version index.
- Before a big change, export the map database (ArtifactData list with out_dir, for every non-empty `<site>_<collection>`; Bright Tree collections have no prefix) to `data-snapshots/<date>_v<NN>/` and commit it. Do this at least weekly.
- Revert = republish the old commit's map/ files to the same artifact URL, then commit that as a new version ("v80: revert to v74"). Never rewrite history on main.
- Experiments go on a branch plus a separate test artifact; merge to main only when Brett approves.
- The repo is private: it holds the method, scripts and site data. Public-facing outputs use first names only and no addresses or lot numbers.
- The session's git proxy allows branch pushes but not tags, so versions are marked by commit messages rather than git tags.

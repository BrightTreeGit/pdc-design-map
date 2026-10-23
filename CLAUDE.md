# Working on the PDC Design Map

- The live map is the claude.ai artifact https://claude.ai/artifact/UBiGj6XL3CwhpRCv6aZfEu. `map/index.html` plus the files under `map/` are its source: publish with the Artifact tool using `file_path` = map/index.html and `files` for any changed assets, passing the same `url`.
- Before every publish, run `python3 scripts/qa/check_map.py` (loads every site headless; exit 1 = don't publish).
- Every publish = one commit on `main`. The message starts with the artifact version number ("v78: …"). Add a matching entry at the top of CHANGELOG.md (Added / Changed / Fixed, plain language) and a row in its version index.
- Before a big change, export the map database (ArtifactData list with out_dir, for every non-empty `<site>_<collection>`; Bright Tree collections have no prefix) to `data-snapshots/<date>_v<NN>/` and commit it. Do this at least weekly.
- Revert = republish the old commit's map/ files to the same artifact URL, then commit that as a new version ("v80: revert to v74"). Never rewrite history on main.
- Experiments go on a branch plus a separate test artifact; merge to main only when Brett approves.
- The repo is private: it holds the method, scripts and site data. Public-facing outputs use first names only and no addresses or lot numbers.
- The session's git proxy allows branch pushes but not tags, so versions are marked by commit messages rather than git tags.

## Brett's workflow (agreed 24 Oct 2026)

Brett isn't a programmer, but he grew up with DOS, did Visual Basic at university and wants to learn. Use the proper term now and then (commit, branch, function, JSON, raster…) with a one-line plain explanation the first time, so he picks it up as he goes.

1. **Feedback lives on the map.** Groups leave comments on the trial map (https://claude.ai/artifact/CCUp4A9sdGDGXoKdh4ocpL) or live map. "Go through the map comments" = read them all (ArtifactComments), sort into fix now / later / no, reply on each thread, and log the "later" ones in docs/feedback-log.md.
2. **One-line approvals.** "Approve X for live" = move that change from the trial branch to main, publish to the live map, give it a version number, CHANGELOG entry and commit. Nothing reaches the live map without that.
3. **Privacy check before anything leaves.** "Privacy check" (and automatically before any email, share or export to people outside): scan the file, page, email or photos for full addresses, lot/plan numbers, surnames, phone numbers, emails other than the recipient's, and GPS/EXIF in photos. Report what was found and fix it before it goes.
4. **Every layer says where it came from.** Each map layer or overlay shows its source and year (e.g. "LiDAR 2022", "SILO rainfall 1889–2025") in its legend. New layers must include one.
5. **"Wrap up" ends a session.** Commit and push everything, update tools/work-program in the Project, and list what is waiting on Brett (shares, drafts to send, approvals, things to fly or download).
6. **"What's new" notes.** When the trial map changes in a way a group would notice, draft a short friendly what's-new email per affected group (Gmail draft, never sent without Brett's OK; first names only).

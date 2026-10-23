# Water-powered pumps: data behind the Ram & Bunyip pump tool

Test artifact: https://claude.ai/artifact/FNkTiU7t6fLgJ5RGVPuhkB (branch trial/ram-pump, local-only: no shared database).

## Bunyip (Porta's Engineering, Qld)
- PA-13 output table (litres/24 h vs fall 0.3–5 m, input 0.1–6 L/s, delivery head 10–150 m, piston letters a–i, c = 60 mm): transcribed from "Output Table 10.6.21" on https://www.bunyipwaterpumps.com/about. Stored in map/index.html as BUNYIP.T.
- PA-8: about 30% of PA-13 outputs, less again below 1.8 m fall; $2,425 ex GST, 17 kg.
- PA-13: $2,930 ex GST, 28 kg. PA-16: about 2.5 × PA-13, max input 15 L/s, $4,212 ex GST, 40 kg. High-head stainless valves over 70 m extra.
- Example: 1 m fall, 6 L/s, 50 m head = 4,600 L/day (piston c); 2 L/s = 1,500 L/day. 5,000 L/day over 5 km to 100 m in 25 mm poly with minor friction.
- Fall 300 mm to 5 m; self-regulating, restarts by itself (permaculturecourseonline.com).
- Their Advanced Output Calculator (xlsx) is on the About page; not yet read (download blocked from the workspace).
- Independent CFD study (Inventions 2023, 8(6):147, mdpi.com/2411-5134/8/6/147): about 2% of drive water delivered, modelled efficiency about 15% at 3 m head; validation partial. The manufacturer table implies 40–55% at good sites.

## Ram pumps
- NC State Extension, Hydraulic Ram Pumps (content.ces.ncsu.edu/hydraulic-ram-pumps): Q = E × S × F / L, E typically 0.6; min fall about 0.9 m; drive pipe at least 5 × fall; delivery pipe about half the drive diameter; sizes table (drive ¾"–3", min source flow 2–60 gpm, max 1,000–20,000 gpd).
- Tool uses efficiency falling with lift ratio (70% at 2:1 to 20% at 30:1) and no ram beyond 30:1.

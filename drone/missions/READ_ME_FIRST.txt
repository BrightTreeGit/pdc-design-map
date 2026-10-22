BRIGHT TREE MAPPING FLIGHTS (DJI Mini 5 Pro, DJI Fly)

WHAT'S HERE
  0 m inside boundary (test)\   the drone stays inside the boundary the whole time, turns and
                                 transit included. 2 missions + 2 cross. Fly this first.
                                 (Edges will be a bit soft in the results: fine for a test.)
  Inside + half Cumner Rd reserve\  as the 0 m test, but on the west side it may use the near half of
                                 the Cumner Road reserve (taken as 20 m wide, so up to 10 m out).
                                 Better west edge with nothing over the neighbours. 2 + 2 cross.
                                 Pause if a car or person is on the road below.
  15 m past boundary\           the full-quality version: lines run 15 m past the boundary.
                                 3 missions + 2 cross.
  In each folder: _SW_ files take off at the SW corner (recommended, 151 m high),
                  _SE_ files at the SE corner (124 m); preview_main / preview_cross images;
                  .kml files to view the paths in 3D in Google Earth.
  BrightTree_boundary.geojson    the boundary, for cropping the results (privacy)
  Put mission into DJI Fly.bat   loads a mission into DJI Fly (see below)

THE PLAN
  Lines 16 m apart (cross pass 20 m), each stretch 45 m above the tallest crown under it
  (2022 LiDAR), never closer than 30 m, never more than 117 m above the ground below.
  Heights are measured from the take-off spot: TAKE OFF AT THE CORNER YOU CHOSE (within ~10 m,
  open sky). Somewhere else: tell Claude and the files get re-made.
  Each mission climbs over the take-off spot, crosses high to its first line, flies the lines,
  crosses back high and lands at home. 13-18 min each, one battery each.
  Return-to-home height in DJI Fly settings: SW take-off 65 m, SE take-off 90 m.

LOADING A MISSION (once per mission)
  1. DJI Fly > camera view > Waypoints > drop 2 points anywhere > save. One dummy per mission.
  2. Controller to PC by USB-C. Open Internal storage\Android\data\dji.go.v5\files\waypoint\
     Open the newest folder; copy its .kmz (long name) into THIS (top) folder.
  3. Double-click "Put mission into DJI Fly.bat", pick the mission number.
     It writes a file with the same long name into the to_controller folder, using your drone's
     own details from the dummy.
  4. Copy that file back over the dummy on the controller. Restart DJI Fly, open the mission:
     you should see the grid. Delete the dummy .kmz from this folder before doing the next one.

CAMERA (photos, not video)
  Photo mode: Timed Shot, every 2 s, 12 MP, 4:3, JPEG. Gimbal straight down (-90).
  Shutter 1/1000 s or faster if you can set it (Pro mode), ISO auto, EV -0.3 to -0.7.
  Focus: tap far away, then lock it. White balance: fixed (Sunny or Cloudy), not Auto.
  START the timed shot when the drone reaches the first line; STOP it when it heads home.

ON THE DAY
  Calm: under 10 km/h at tree-top height. Bright overcast is best; otherwise 10 am - 2 pm.
  Obstacle avoidance: leave on for the take-off and climb.
  Keep the drone in sight (it reaches 450-550 m away on the far lines). A spotter helps.
  Put 5-6 targets (A3 checkerboard / painted cross) in open spots: driveway, house clearing,
  dam walls, track. No need to survey them.
  Fly mission 1 first and check the photos before doing 2 and 3.

CROSS PASS (optional, recommended for the forest)
  North-south lines 20 m apart, same height rule and camera settings.
  Same day and similar light as the main pass if you can (shadows move). Fly it after the main
  pass looks good; it can be another day if the weather is calm and the light is similar.

AFTER
  Process in WebODM: outputs Orthophoto GeoTIFF + DSM GeoTIFF. Send both to Claude.
  PRIVACY: in WebODM's task options, set "boundary" to BrightTree_boundary.geojson. The photo,
  surface model and 3D model then stop at the boundary, so neighbours' land isn't in the results.
  (Use all the photos for processing - the edge ones are needed - just crop the outputs.)
  Keep the raw photos private: don't share or upload them anywhere public, and delete any taken
  outside the block (e.g. during take-off and transit) once processing is done.
  Or send the raw photos (all three folders) and Claude can advise.

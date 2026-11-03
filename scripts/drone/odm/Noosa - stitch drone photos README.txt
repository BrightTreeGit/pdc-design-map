Stitching the Noosa drone photos (OpenDroneMap)

Run this on the desktop with the RTX 3070 (30-60 min); the laptop works too but takes hours.

One-off setup on that computer
  1. Install Docker Desktop for Windows (docker.com). It will ask to turn on WSL 2; say yes and restart.
  2. Start Docker Desktop and wait until it says "Engine running".
  3. For the graphics card: NVIDIA driver up to date (GeForce Experience or nvidia.com). Docker Desktop
     picks the GPU up by itself on recent versions. If the GPU run fails, the script falls back to CPU.
  4. The first run downloads the ODM program (about 2 GB), so leave it a few minutes before it starts.

Each time
  Double-click "Noosa - stitch drone photos (ODM, needs Docker).bat". It copies the 270 straight-down photos
  into Noosa Forest Retreat\Drone\odm\images, runs ODM with the lot boundary, and writes the results to
  Noosa Forest Retreat\Drone\odm. Needs about 25 GB free.

What you get
  odm_orthophoto\odm_orthophoto.tif   the stitched aerial, 5 cm per pixel
  odm_dem\dsm.tif                     the surface model (tree tops and roofs), 10 cm
  odm_dem\dtm.tif is NOT made (we already have the 1 m LiDAR ground); Claude uses dsm - LiDAR ground for tree heights.

Then tell Claude "Noosa orthophoto is ready" and it becomes the 2026 aerial on the map, with tree heights,
canopy cover, gaps and the change since the 2022 LiDAR.

If the photos are on the laptop only: copy the whole Noosa Forest Retreat\Drone folder (about 6 GB with the videos;
the JPGs alone are 3.5 GB) to the same place on the desktop first, along with this _tools folder.

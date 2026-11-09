"""Line-of-sight helpers for Bright Tree (1 m map grid, x = E - 492000, y = 7043000 - N).
viewshed(): radial sweep from one observer over a height surface. A cell counts as seen when the sight line reaches a
target height above its ground (or its top surface), without being blocked by the surface in between (canopy treated
as solid from the ground up, so views between trunks are under-counted)."""
import numpy as np

def viewshed(top, ground, ox, oy, eye, maxr, res=1.0, target=None, clear_r=0.0, curv=False):
    """top, ground: 2-D arrays (rows = y). ox, oy in cells. eye: observer eye elevation (m).
    target: None = see the top surface; a number = see a point that high above the ground.
    clear_r: metres around the observer treated as cleared (top = ground). Returns bool array (same shape)."""
    H, W = top.shape
    Z = top.astype(np.float64).copy()
    if clear_r > 0:
        yy, xx = np.ogrid[:H, :W]
        m = (xx - ox) ** 2 + (yy - oy) ** 2 <= (clear_r / res) ** 2
        Z[m] = ground[m]
    T = Z if target is None else ground.astype(np.float64) + target
    R = int(maxr / res)
    # rays to every cell on the square perimeter
    p = []
    for k in range(-R, R + 1):
        p += [(k, -R), (k, R), (-R, k), (R, k)]
    p = np.array(sorted(set(p)), float)
    ang = np.arctan2(p[:, 1], p[:, 0]); cs, sn = np.cos(ang), np.sin(ang)
    vis = np.zeros((H, W), bool)
    best = np.full(len(p), -np.inf)
    step = 0.5
    for i in range(1, int(R * 1.42 / step) + 1):
        d = i * step
        x = np.rint(ox + cs * d).astype(int); y = np.rint(oy + sn * d).astype(int)
        ok = (x >= 0) & (x < W) & (y >= 0) & (y < H) & (np.maximum(np.abs(x - ox), np.abs(y - oy)) <= R)
        if not ok.any(): break
        xi, yi = x[ok], y[ok]
        dm = d * res
        drop = (dm * dm) * (0.87 / 12.74e6) if curv else 0.0     # earth curvature with standard refraction
        at = (T[yi, xi] - drop - eye) / dm
        az = (Z[yi, xi] - drop - eye) / dm
        b = best[ok]
        seen = at >= b
        vis[yi[seen], xi[seen]] = True
        best[ok] = np.maximum(b, az)
    vis[int(oy), int(ox)] = True
    return vis

def horizon(top, ox, oy, eye, maxr, res=1.0, nb=360, clear_r=0.0, ground=None):
    """Highest elevation angle (tan) of the surface in each of nb azimuth bins (0 = north, clockwise)."""
    H, W = top.shape
    Z = top.astype(np.float64)
    if clear_r > 0 and ground is not None:
        Z = Z.copy(); yy, xx = np.ogrid[:H, :W]; m = (xx - ox) ** 2 + (yy - oy) ** 2 <= (clear_r / res) ** 2; Z[m] = ground[m]
    R = int(maxr / res); y0, y1, x0, x1 = max(0, int(oy) - R), min(H, int(oy) + R + 1), max(0, int(ox) - R), min(W, int(ox) + R + 1)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx, dy = (xx - ox) * res, (yy - oy) * res; d = np.hypot(dx, dy); m = (d > 1.5 * res) & (d <= maxr)
    t = (Z[y0:y1, x0:x1] - eye) / np.where(d > 0, d, 1)
    az = (np.degrees(np.arctan2(dx, -dy)) + 360) % 360
    b = (az[m] / (360 / nb)).astype(int) % nb
    out = np.full(nb, -np.inf); np.maximum.at(out, b, t[m])
    return out

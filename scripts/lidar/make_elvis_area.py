"""Write the small zipped shapefile that the ELVIS download page accepts as an "upload area", from a site's
terrain.json (lot outline in MGA zone 56 metres), buffered by a margin. Also prints the WGS84 box for the
Copernicus Browser. No GIS libraries needed.

usage: python3 make_elvis_area.py <site-id> <Name> [margin m, default 120]
"""
import json, math, struct, sys, zipfile, os, numpy as np

site, name = sys.argv[1], sys.argv[2]; margin = float(sys.argv[3]) if len(sys.argv) > 3 else 120
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
T = json.load(open(os.path.join(root, 'map', 'sites', site, 'terrain.json')))
lot = np.array(T['lot'], float).reshape(-1, 2); E = T['E0'] + lot[:, 0]; N = T['N0'] - lot[:, 1]
x0, x1, y0, y1 = E.min() - margin, E.max() + margin, N.min() - margin, N.max() + margin

def utm_to_ll(e, n, zone=56, south=True):          # GRS80 (GDA94/GDA2020 ≈ WGS84 to within a metre)
    a, f = 6378137.0, 1 / 298.257222101; k0 = 0.9996; e2 = f * (2 - f); ep2 = e2 / (1 - e2)
    x = e - 500000.0; y = n - (10000000.0 if south else 0)
    m = y / k0; mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu) + (151 * e1 ** 3 / 96) * math.sin(6 * mu)
    n1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2); t1 = math.tan(phi1) ** 2; c1 = ep2 * math.cos(phi1) ** 2
    r1 = a * (1 - e2) / (1 - e2 * math.sin(phi1) ** 2) ** 1.5; d = x / (n1 * k0)
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24 + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / math.cos(phi1)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    return math.degrees(lat), math.degrees(lon0 + lon)

corners = [utm_to_ll(x, y) for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
lats = [c[0] for c in corners]; lons = [c[1] for c in corners]
ring = [(lons[0], lats[0]), (lons[1], lats[1]), (lons[2], lats[2]), (lons[3], lats[3]), (lons[0], lats[0])]  # clockwise for shapefiles
# ensure clockwise (signed area negative in lon/lat)
area = sum((ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]) for i in range(4))
if area > 0: ring = ring[::-1]
bx = (min(lons), min(lats), max(lons), max(lats))

# .shp: one polygon record
rec = struct.pack('<i', 5) + struct.pack('<4d', *bx) + struct.pack('<ii', 1, 5) + struct.pack('<i', 0) + b''.join(struct.pack('<2d', *p) for p in ring)
shp = struct.pack('>i', 9994) + b'\0' * 20 + struct.pack('>i', (100 + 8 + len(rec)) // 2) + struct.pack('<ii', 1000, 5) + struct.pack('<4d', *bx) + struct.pack('<4d', 0, 0, 0, 0)
shp += struct.pack('>ii', 1, len(rec) // 2) + rec
shx = struct.pack('>i', 9994) + b'\0' * 20 + struct.pack('>i', (100 + 8) // 2) + struct.pack('<ii', 1000, 5) + struct.pack('<4d', *bx) + struct.pack('<4d', 0, 0, 0, 0) + struct.pack('>ii', 50, len(rec) // 2)
# .dbf: one text field "name"
fld = b'name'.ljust(11, b'\0') + b'C' + b'\0' * 4 + bytes([32]) + b'\0' * 15
dbf = struct.pack('<BBBBIHH', 3, 26, 11, 2, 1, 32 + 32 + 1, 33) + b'\0' * 20 + fld + b'\r' + b' ' + name.encode()[:32].ljust(32) + b'\x1a'
prj = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'elvis_areas', f'{name}_ELVIS_area.zip')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for ext, data in [('shp', shp), ('shx', shx), ('dbf', dbf), ('prj', prj.encode())]: z.writestr(f'{name}_ELVIS_area.{ext}', data)
print('wrote', out)
print(f'MGA56 box: E {x0:.0f}–{x1:.0f}, N {y0:.0f}–{y1:.0f} ({x1 - x0:.0f} × {y1 - y0:.0f} m)')
print(f'WGS84 box (lon/lat): W {bx[0]:.5f}  S {bx[1]:.5f}  E {bx[2]:.5f}  N {bx[3]:.5f}')

"""Carbon stored in Bright Tree's trees, from the LiDAR canopy (2008, 2014, 2022).
Method: find each tree crown in the canopy height model (tops = local maxima, crowns by watershed), then estimate
above-ground biomass per tree from its height and crown width with the global remote-sensing allometry of
Jucker et al. 2017 (Global Change Biology 23:177-190, Eq. 7, angiosperms): AGB kg = 0.016 (H x CD)^2.013 x exp(0.204^2/2).
Roots add a root:shoot ratio of 0.22 (Mokany et al. 2006, forests); carbon = 0.47 of dry biomass (IPCC 2006 default);
CO2-e = C x 44/12. Indicative only (about +/-35% for the lot); not an ACCU or carbon-market method.
usage: python3 carbon.py <work dir> <out dir>"""
import sys, json, numpy as np
from scipy import ndimage
from skimage.segmentation import watershed
from PIL import Image
W, OUT = sys.argv[1:3]
P = "/mnt/user-data/uploads/Permiculture Noosa PDC/Bright Tree/Lidar-survey data/QLD Government/Canopy outputs/"
inlot = np.load(W + 'inlot.npy')
RS, CF, CO2 = 0.22, 0.47, 44 / 12
def crowns(year):
    z = np.load(P + f'canopy_bright-tree_{year}.npz'); g = z['ground'].astype(np.float64); t = z['top'].astype(np.float64)
    bad = ~np.isfinite(g); idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True); g = g[tuple(idx)]
    chm = np.clip(np.nan_to_num(t - g, nan=0), 0, 80)
    s = ndimage.gaussian_filter(chm, 1.0)
    mx = ndimage.maximum_filter(s, size=5); tops = (s == mx) & (s >= 5)
    mk, n = ndimage.label(tops)
    lab = watershed(-s, mk, mask=s >= 2)
    ids = np.arange(1, n + 1)
    area = ndimage.sum(np.ones_like(s), lab, ids)
    H = ndimage.maximum(chm, lab, ids)
    CD = 2 * np.sqrt(area / np.pi)
    CD = np.minimum(CD, 0.6 * H + 6)                         # cap merged crowns at a plausible width for that height
    agb = 0.016 * (H * CD) ** 2.013 * np.exp(0.204 ** 2 / 2) / 1000     # tonnes dry matter
    agb[H < 5] = 0
    dens = np.zeros(s.shape); dens[lab > 0] = (agb / np.maximum(area, 1))[lab[lab > 0] - 1]   # t per m2 spread over each crown
    cy, cx = ndimage.center_of_mass(np.ones_like(s), lab, ids) if False else (None, None)
    return chm, lab, H, CD, agb, dens, n
res = {}; dens22 = None
for y in (2008, 2014, 2022):
    chm, lab, H, CD, agb, dens, n = crowns(y)
    inl = dens[inlot].sum()                                   # t AGB on the lot
    ntrees = int(len(np.unique(lab[inlot & (lab > 0)])))
    big = int(((H >= 40)).sum())
    tot = inl * (1 + RS); c = tot * CF
    res[y] = dict(trees=ntrees, agb_t=round(inl), total_t=round(tot), carbon_t=round(c), co2e_t=round(c * CO2), agb_tha=round(inl / (inlot.sum() / 1e4)),
                  meanH=round(float(chm[inlot].mean()), 1))
    if y == 2022: dens22 = dens; lab22, H22, CD22, agb22 = lab, H, CD, agb
    print(y, res[y])
lotha = inlot.sum() / 1e4
for a, b in ((2008, 2022), (2014, 2022)):
    d = res[b]['co2e_t'] - res[a]['co2e_t']; res[f'{a}-{b}'] = dict(co2e_t=d, per_year=round(d / (b - a)), per_ha_year=round(d / (b - a) / lotha, 1))
    print(a, b, res[f'{a}-{b}'])
# share of the lot's carbon in the biggest trees
on = np.unique(lab22[inlot & (lab22 > 0)]); a_on = agb22[on - 1]; o = np.sort(a_on)[::-1]
top10 = float(o[:max(1, len(o) // 10)].sum() / o.sum())
big40 = float(a_on[H22[on - 1] >= 40].sum() / o.sum())
res['top10share'] = round(top10, 2); res['big40share'] = round(big40, 2); res['big40n'] = int((H22[on - 1] >= 40).sum())
print('top 10% of trees hold', round(top10, 2), 'trees >=40 m hold', round(big40, 2), 'n', res['big40n'])
# map: total carbon density (t CO2-e per ha, above + below ground), 2 m cells, smoothed over ~10 m
d2 = dens22.reshape(1000, 2, 1000, 2).sum(axis=(1, 3))                 # t AGB per 4 m2
co2ha = ndimage.uniform_filter(d2, 5) * (1 + RS) * CF * CO2 * 1e4 / 4
np.save(W + 'co2ha.npy', co2ha.astype(np.float32))
stops = [(0, (250, 245, 210)), (300, (200, 225, 140)), (700, (110, 180, 90)), (1200, (40, 120, 70)), (2000, (20, 70, 60)), (3000, (60, 30, 90))]
rgb = np.zeros((1000, 1000, 4), np.uint8)
for c in range(3): rgb[..., c] = np.interp(co2ha, [s for s, _ in stops], [col[c] for _, col in stops]).astype(np.uint8)
rgb[..., 3] = np.where(co2ha > 20, 175, 0).astype(np.uint8)
Image.fromarray(rgb).save(OUT + '/carbon.png', optimize=True)
res['lotHa'] = round(lotha, 2)
res['method'] = 'Tree crowns found in the LiDAR canopy model; biomass per tree from height and crown width (Jucker et al. 2017, Global Change Biology 23:177-190); roots +22% (Mokany et al. 2006); carbon 47% of dry biomass (IPCC 2006); CO2-e = carbon x 44/12. Indicative, about +/-35%.'
res['caveat2008'] = 'The 2008 survey had about 3 points per m2 (2022: about 53), so 2008 heights and crowns read low; changes from 2008 overstate growth. 2014 (about 14 per m2) to 2022 is the fairer comparison.'
json.dump(res, open(OUT + '/carbon.json', 'w'), separators=(',', ':'), default=lambda o: o)

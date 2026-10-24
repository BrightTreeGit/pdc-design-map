"""NAC tank test with Ange's real set-up (24 Oct 2026): 30,000 L on 191 m² (house + half garage) with the household on the pump,
and 5,000 L on 36 m² (carport + half garage) for the garden tap. Daily, 1995–2026, SILO rain and FAO56 ETo at the block."""
import json, numpy as np, datetime as dt, os
HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, '../../../../map/sites/nac/silo_full.json')))
d0 = dt.date.fromisoformat(S['start']); R = np.array(S['rain10']) / 10.0; E = np.array(S['eto10']) / 10.0
n = len(R); dates = [d0 + dt.timedelta(days=i) for i in range(n)]; yrs = np.array([d.year for d in dates])
full = sorted(set(yrs))[:-1]  # drop the part year
ann = {y: R[yrs == y].sum() for y in full}
def sim(roof, store, garden_m2, house_lpd, kc=0.6, eff=0.85, soilcap=25.0):
    s = store; soil = 12.0; sup = dem = 0.0; short = 0; low_year = {}; empty_run = best = 0; best_end = None; dry_years = set()
    for i in range(n):
        r = R[i]; s = min(store, s + r * roof * eff)
        et = E[i] * kc if E[i] >= 0 else 3.0 * kc
        soil = min(soilcap, soil + r) - et; need = -soil if soil < 0 else 0.0; soil = max(soil, 0.0)
        want = need * garden_m2 + house_lpd
        take = min(s, want); s -= take; sup += take; dem += want
        if take < want - 1e-6: short += 1; empty_run += 1; dry_years.add(yrs[i])
        else:
            if empty_run > best: best, best_end = empty_run, dates[i - 1]
            empty_run = 0
        low_year[yrs[i]] = min(low_year.get(yrs[i], store), s)
    return {'met': sup / dem if dem else 1.0, 'short_days_per_yr': short / len(full), 'longest_short': best, 'longest_end': str(best_end), 'dry_years': sorted(dry_years), 'low2019': low_year.get(2019)}
out = {}
print('annual mean', round(np.mean(list(ann.values()))), 'driest', sorted(ann.items(), key=lambda t: t[1])[:3])
for house in (200, 300, 400):
    r = sim(191, 30000, 0, house); out[f'house_{house}'] = r
    print(f'30,000 L on 191 m², house {house} L/day, no garden: met {r["met"]*100:.0f}%, short {r["short_days_per_yr"]:.1f} d/yr, longest {r["longest_short"]} d to {r["longest_end"]}, years with shortfall {r["dry_years"]}, lowest in 2019 {r["low2019"]:.0f} L')
for g in (20, 40, 80):
    r = sim(36, 5000, g, 0); out[f'garden_{g}'] = r
    print(f'5,000 L on 36 m², watering {g} m² of beds by can: met {r["met"]*100:.0f}%, short {r["short_days_per_yr"]:.0f} d/yr, longest {r["longest_short"]} d to {r["longest_end"]}')
for g in (40, 80):
    r = sim(191, 30000, g, 300); out[f'combined_{g}'] = r
    print(f'If the 30,000 L also watered {g} m² (house 300 L/day): met {r["met"]*100:.0f}%, longest {r["longest_short"]} d to {r["longest_end"]}')
r = sim(227, 35000, 40, 300); out['all_linked'] = r
print(f'Both tanks linked (35,000 L on 227 m²), house 300 + 40 m² garden: met {r["met"]*100:.0f}%, longest {r["longest_short"]} d')
print('roof yield L/yr: 191 m²', round(np.mean(list(ann.values())) * 191 * .85), '; 36 m²', round(np.mean(list(ann.values())) * 36 * .85))
json.dump(out, open(os.path.join(HERE, 'nac_sim2.json'), 'w'), indent=1, default=lambda o: int(o) if hasattr(o, '__int__') else str(o))

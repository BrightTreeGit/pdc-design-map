import json, numpy as np, datetime as dt
S = json.load(open('/mnt/user-data/uploads/Permiculture Noosa PDC/NAC/Lidar-survey data/NSW site pack nac/silo_daily.json'))
dates = [dt.date.fromisoformat(r['date']) for r in S['data']]
v = lambda r, c: next(x['value'] for x in r['variables'] if x['variable_code'] == c)
R = np.array([v(r, 'daily_rain') for r in S['data']]); TN = np.array([v(r, 'min_temp') for r in S['data']])
yrs = np.array([d.year for d in dates]); mon = np.array([d.month for d in dates])
ann = {y: R[yrs == y].sum() for y in range(1995, 2026)}
print('annual mean', round(np.mean(list(ann.values()))), 'median', round(np.median(list(ann.values()))))
print('driest', sorted(ann.items(), key=lambda t: t[1])[:4]); print('wettest', sorted(ann.items(), key=lambda t: -t[1])[:3])
# dry spells (<2mm)
best = (0, None); run = 0
for i, r in enumerate(R):
    run = run + 1 if r < 2 else 0
    if run > best[0]: best = (run, dates[i])
print('longest dry spell', best)
print('days >=50mm/yr', round((R >= 50).sum() / 31, 1), 'max', R.max(), dates[R.argmax()])
print('Jul mean min', round(TN[mon == 7].mean(), 1), 'lowest', TN.min(), dates[TN.argmin()], 'nights <=2C per yr', round((TN <= 2).sum() / 31, 1), 'nights<=0', (TN <= 0).sum())
for m in range(1, 13): pass
mm = [R[mon == m].sum() / 31 for m in range(1, 13)]; print('monthly mean', [round(x) for x in mm])
print('Jul-Sep share', round(sum(mm[6:9]) / sum(mm) * 100), '%; Aug-Oct', round(sum(mm[7:10])))

ETO = [5.3, 4.6, 3.8, 2.8, 2.0, 1.6, 1.8, 2.5, 3.4, 4.3, 4.8, 5.4]   # mm/day, coastal Hunter/Port Stephens typical
def sim(roof, store, garden, house_lpd, kc=0.6, start=None):
    s = store; soil = 25.0; sup = dem = 0; short_days = 0; yr_rel = {}
    for i, r in enumerate(R):
        s = min(store, s + r * roof * 0.85)
        et = ETO[mon[i] - 1] * kc
        soil = min(25, soil + r) - et; need = max(0, -soil) if soil < 0 else 0
        soil = max(soil, 0)
        g = need * garden
        want = g + house_lpd
        if want > 0:
            take = min(s, want); s -= take; sup += take; dem += want
            if take < want - 1e-6: short_days += 1
    return sup / dem if dem else 1, short_days / 31
roofs = {'home': 135, 'home+garage+carport': 172}
for roof in (135, 172):
    for hl in (0, 200, 300):
        for g in (0, 40, 80):
            if hl == 0 and g == 0: continue
            out = []
            for st in (5000, 20000, 35000, 50000):
                rel, sd = sim(roof, st, g, hl); out.append(f'{st//1000}kL {rel*100:.0f}% ({sd:.0f}d)')
            print(f'roof {roof} house {hl} L/d garden {g} m2:', ' | '.join(out))
print('roof yield avg L/yr home only', round(np.mean(list(ann.values())) * 135 * 0.85), 'all', round(np.mean(list(ann.values())) * 172 * .85))
# drought year 2019-ish: driest year
dry = min(ann, key=ann.get)

def sim_year(roof, store, garden, house_lpd, year, kc=.6):
    s = store; soil = 25.; sup = dem = 0; low = store
    for i, r in enumerate(R):
        s = min(store, s + r * roof * .85); et = ETO[mon[i]-1]*kc; soil = min(25, soil + r) - et; need = -soil if soil < 0 else 0; soil = max(soil, 0)
        want = need*garden + house_lpd; take = min(s, want); s -= take
        if yrs[i] == year: sup += take; dem += want; low = min(low, s)
    return sup/dem, low
for st in (5000, 20000, 35000, 50000):
    print('2019', st, [ (round(a*100), round(b)) for a, b in [sim_year(135, st, 40, 300, 2019), sim_year(172, st, 40, 300, 2019), sim_year(172, st, 80, 300, 2019)]])

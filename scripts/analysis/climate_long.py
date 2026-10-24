"""137 years of climate at a site, from SILO's full daily record (silo_long.json, 1889 to now).

Used by site_pack.py for the "137-year climate record" page, and the same arithmetic as the map's Site-tab card
(longStats in map/index.html), so the two agree:
  - annual rain for every complete year, the mean of five 30-year windows, the five driest and wettest years
  - the longest run of days under 2 mm (and the longest such run inside each year, for the trend test)
  - days over 35 °C and nights under 2 °C per year since 1957 (temperatures before 1957 are too sparse)
  - Mann-Kendall trend test and Sen's slope on annual rain, yearly longest dry spell, hot days and frost nights
  - the driest run of three consecutive calendar years, for the tank stress test
Caveat carried on every output: pre-1910 rain and pre-1957 temperatures are interpolated from sparse stations.
"""
import datetime as dt, math

WINDOWS = [(1889, 1918), (1919, 1948), (1949, 1978), (1979, 2008), (1996, 2025)]


def _ncdf(x):
    t = 1 / (1 + .2316419 * x); d = .3989423 * math.exp(-x * x / 2)
    return 1 - d * t * (.3193815 + t * (-.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))


def mann_kendall(v):
    n = len(v); S = 0
    for i in range(n - 1):
        for k in range(i + 1, n):
            d = v[k] - v[i]; S += (d > 0) - (d < 0)
    cnt = {}
    for x in v: cnt[x] = cnt.get(x, 0) + 1
    tc = sum(c * (c - 1) * (2 * c + 5) for c in cnt.values() if c > 1)
    var = (n * (n - 1) * (2 * n + 5) - tc) / 18
    z = (S - 1) / math.sqrt(var) if S > 0 else (S + 1) / math.sqrt(var) if S < 0 else 0
    p = 2 * (1 - _ncdf(abs(z)))
    sl = sorted((v[k] - v[i]) / (k - i) for i in range(n - 1) for k in range(i + 1, n))
    m = len(sl); sen = sl[(m - 1) // 2] if m % 2 else (sl[m // 2 - 1] + sl[m // 2]) / 2
    return {'S': S, 'z': z, 'p': p, 'sen': sen, 'n': n}


def stats(L):
    d0 = dt.date.fromisoformat(L['start']); R, X, N = L['rain10'], L['tmax10'], L['tmin10']
    yr = {}; cur = 0; best = (0, None)
    for i, r in enumerate(R):
        d = d0 + dt.timedelta(days=i); y = d.year
        Y = yr.setdefault(y, {'rain': 0.0, 'miss': 0, 'days': 0, 'hot': 0, 'frost': 0, 'tdays': 0, 'run': 0, 'maxrun': 0, 'i0': i, 'i1': i})
        Y['days'] += 1; Y['i1'] = i
        if r < 0: Y['miss'] += 1
        else: Y['rain'] += r / 10
        if 0 <= r < 20:
            cur += 1; Y['run'] += 1; Y['maxrun'] = max(Y['maxrun'], Y['run'])
            if cur > best[0]: best = (cur, d)
        else: cur = 0; Y['run'] = 0
        if y >= 1957 and X[i] > -900 and N[i] > -900:
            Y['tdays'] += 1; Y['hot'] += X[i] > 350; Y['frost'] += N[i] < 20
    full = [y for y in sorted(yr) if yr[y]['days'] >= 365 and yr[y]['miss'] < 10]
    rain = {y: yr[y]['rain'] for y in full}
    mean = sum(rain.values()) / len(rain)
    win = []
    for a, b in WINDOWS:
        w = [rain[y] for y in full if a <= y <= b]
        if w: win.append({'a': a, 'b': b, 'mean': sum(w) / len(w), 'min': min(w)})
    order = sorted(full, key=lambda y: rain[y])
    tyears = [y for y in full if y >= 1957 and yr[y]['tdays'] >= 360]
    worst = None
    for y in full:
        if y + 1 in rain and y + 2 in rain:
            s = rain[y] + rain[y + 1] + rain[y + 2]
            if worst is None or s < worst['rain']: worst = {'y0': y, 'rain': s, 'i0': yr[y]['i0'], 'i1': yr[y + 2]['i1']}
    since95 = [y for y in full if y >= 1995]; d95 = min(since95, key=lambda y: rain[y])
    return {
        'years': full, 'rain': rain, 'mean': mean, 'windows': win, 'driest': order[:5], 'wettest': order[::-1][:5],
        'longest': best[0], 'longest_end': best[1], 'tyears': tyears,
        'hot': {y: yr[y]['hot'] for y in tyears}, 'frost': {y: yr[y]['frost'] for y in tyears},
        'maxrun': {y: yr[y]['maxrun'] for y in full}, 'worst': worst, 'driest95': d95, 'driest95_rank': order.index(d95) + 1,
        'mk': {'rain': mann_kendall([round(rain[y]) for y in full]), 'run': mann_kendall([yr[y]['maxrun'] for y in full]),
               'hot': mann_kendall([yr[y]['hot'] for y in tyears]), 'frost': mann_kendall([yr[y]['frost'] for y in tyears])},
    }


def _ord(n): return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _pf(p): return 'p < 0.01' if p < .01 else f'p = {p:.2f}'


def trend_line(label, r, unit, dec=1, series=None):
    if r['p'] > .1: return f"{label}: no clear trend since {'1889' if r['n'] > 100 else '1957'} ({_pf(r['p'])})."
    word = 'clear' if r['p'] < .05 else 'weak'
    d = 'rising' if r['z'] > 0 else 'falling'
    v = abs(r['sen'] * 10)
    if round(v, dec) == 0 and series:   # count data with many zero years: Sen's slope is 0, so compare the first and last 15 years
        ys = sorted(series); a, b = ys[:15], ys[-15:]
        ma = sum(series[y] for y in a) / len(a); mb = sum(series[y] for y in b) / len(b)
        return f"{label}: a {word} {d} trend, from {ma:.1f} a year in {a[0]}–{str(a[-1])[2:]} to {mb:.1f} in {b[0]}–{str(b[-1])[2:]} ({_pf(r['p'])})."
    return f"{label}: a {word} {d} trend, about {v:.{dec}f} {unit} per decade ({_pf(r['p'])})."


def findings(s):
    out = []
    w = s['windows']; ranks = sorted(range(len(w)), key=lambda i: w[i]['mean'])
    if len(w) == 5 and set(ranks[:2]) == {3, 4}: out.append('The last two 30-year windows are the driest of the five.')
    last = w[-1]; pct = (last['mean'] / s['mean'] - 1) * 100
    out.append(f"The latest 30 years ({last['a']}–{last['b']}) averaged {last['mean']:,.0f} mm, {abs(pct):.0f}% {'below' if pct < 0 else 'above'} the {len(s['years'])}-year mean of {s['mean']:,.0f} mm.")
    y = s['driest95']; r = s['driest95_rank']; dmin = s['driest'][0]
    if r == 1: out.append(f"{y}, the driest year since 1995 ({s['rain'][y]:,.0f} mm), is also the driest on record.")
    else: out.append(f"{y}, the driest year since 1995 ({s['rain'][y]:,.0f} mm), is only the {_ord(r)} driest since {s['years'][0]}; the driest was {dmin} ({s['rain'][dmin]:,.0f} mm).")
    if s['longest_end']: out.append(f"The longest run of days with under 2 mm was {s['longest']} days, ending {s['longest_end'].strftime('%-d %b %Y')}.")
    t = s['tyears']
    if t:
        def m(a, b, k): v = [s[k][y] for y in t if a <= y <= b]; return sum(v) / len(v) if v else 0
        out.append(f"Days over 35 °C averaged {m(1957, 1986, 'hot'):.1f} a year in 1957–86 and {m(1996, 2025, 'hot'):.1f} in 1996–2025; nights under 2 °C {m(1957, 1986, 'frost'):.1f} and {m(1996, 2025, 'frost'):.1f}.")
    wo = s['worst']
    if wo: out.append(f"The driest three years in a row were {wo['y0']}–{wo['y0'] + 2}, {wo['rain']:,.0f} mm in total ({wo['rain'] / 3:,.0f} mm a year).")
    return out


def trends(s):
    k = s['mk']
    return [trend_line('Annual rain', k['rain'], 'mm', 0, s['rain']), trend_line('Longest dry spell each year', k['run'], 'days', 1, s['maxrun']),
            trend_line('Days over 35 °C', k['hot'], 'days', 1, s['hot']), trend_line('Nights under 2 °C', k['frost'], 'nights', 1, s['frost'])]


ETO_QLD = [6.0, 5.3, 4.6, 3.6, 2.8, 2.4, 2.6, 3.5, 4.6, 5.4, 5.9, 6.3]
ETO_NSW = [5.3, 4.6, 3.8, 2.8, 2.0, 1.6, 1.8, 2.5, 3.4, 4.3, 4.8, 5.4]


def worst_tank(L, s, lat, roof=200.0, store=20000.0, house=300.0, garden=0.0):
    """The map's daily tank model run through the driest three consecutive years on record (monthly ETo table)."""
    wo = s['worst']; E = ETO_QLD if lat > -29.5 else ETO_NSW; d0 = dt.date.fromisoformat(L['start'])
    st = store; soil = 25.0; dry = 0; mn = store; sup = dem = 0.0
    for i in range(wo['i0'], wo['i1'] + 1):
        m = (d0 + dt.timedelta(days=i)).month - 1; rain = max(0, L['rain10'][i]) / 10
        st = min(store, st + rain * roof * .85); soil = min(25, soil + rain) - E[m] * .6
        need = -soil if soil < 0 else 0; soil = max(soil, 0); want = need * garden + house
        if want > 0:
            take = min(st, want); st -= take; sup += take; dem += want
            if take < want - 1e-6: dry += 1
        mn = min(mn, st)
    return {'dry': dry, 'min': mn, 'share': sup / dem if dem else 1, 'label': f"{wo['y0']}–{wo['y0'] + 2}", 'rain': wo['rain']}


def draw_page(fig_factory, L, lat, save):
    """One A4 page: 137-year strip with window steps, hot/frost strip, findings and trend lines, tank stress test."""
    import matplotlib.pyplot as plt, numpy as np, textwrap
    s = stats(L); yrs = s['years']; tot = [s['rain'][y] for y in yrs]
    fig = fig_factory('137 years of rain and temperature',
                      f"Every complete year at the property since {yrs[0]}, from the national gridded climate record, and what the long view adds to the last 30 years.",
                      f"SILO gridded daily climate, {L['start'][:4]}–{L['end'][:4]} (Qld Government, CC BY 4.0). Pre-1910 rain and pre-1957 temperatures are indicative only.")
    ax = fig.add_axes([.06, .50, .62, .34])
    col = ['#d9534f' if y in s['driest'] else '#2f6fb3' if y in s['wettest'] else '#b8b8b2' for y in yrs]
    ax.bar(yrs, tot, color=col, width=.8)
    for w in s['windows']:
        ax.plot([w['a'] - .4, w['b'] + .4], [w['mean']] * 2, color='#222', lw=1.8)
        ax.text((w['a'] + w['b']) / 2, w['mean'] + max(tot) * .02, f"{w['mean']:,.0f}", ha='center', fontsize=8, color='#222')
    for y in s['driest']: ax.text(y, s['rain'][y] + max(tot) * .015, str(y), ha='center', fontsize=6.5, color='#a33', rotation=90, va='bottom')
    for y in s['wettest']: ax.text(y, s['rain'][y] + max(tot) * .015, str(y), ha='center', fontsize=6.5, color='#2f6fb3', rotation=90, va='bottom')
    ax.set_ylabel('mm in the year', color='#666', fontsize=9); [ax.spines[k].set_visible(False) for k in ('top', 'right')]
    ax.set_xlim(yrs[0] - 1, yrs[-1] + 1); ax.set_ylim(0, max(tot) * 1.16); ax.tick_params(labelsize=8)
    ax.text(.01, .98, 'Black steps: mean of each 30-year window · red: five driest years · blue: five wettest', transform=ax.transAxes, fontsize=8, color='#444', va='top')
    if s['tyears']:
        bx = fig.add_axes([.06, .30, .62, .14]); t = s['tyears']
        bx.bar(t, [s['hot'][y] for y in t], color='#d9534f', width=.8); bx.bar(t, [-s['frost'][y] for y in t], color='#5b8fd6', width=.8)
        bx.axhline(0, color='#888', lw=.6); [bx.spines[k].set_visible(False) for k in ('top', 'right')]
        bx.set_xlim(yrs[0] - 1, yrs[-1] + 1); bx.tick_params(labelsize=8)
        bx.set_yticks(bx.get_yticks()); bx.set_yticklabels([f'{abs(int(v))}' for v in bx.get_yticks()])
        bx.text(.01, .98, 'Since 1957: days over 35 °C (red, up) and nights under 2 °C (blue, down)', transform=bx.transAxes, fontsize=8, color='#444', va='top')
    wt = worst_tank(L, s, lat)
    fig.text(.71, .84, 'What the long record says', fontsize=10.5, weight='bold', va='top')
    yy = .80
    for f in findings(s):
        txt = textwrap.fill('• ' + f, 50); fig.text(.71, yy, txt, fontsize=8.2, va='top', linespacing=1.3); yy -= .0195 * (txt.count('\n') + 1) + .008
    fig.text(.71, yy - .005, 'Trends (Mann–Kendall test, Sen\'s slope)', fontsize=9.5, weight='bold', va='top'); yy -= .035
    for f in trends(s):
        txt = textwrap.fill(f, 52); fig.text(.71, yy, txt, fontsize=7.8, va='top', color='#333', linespacing=1.25); yy -= .0185 * (txt.count('\n') + 1) + .006
    msg = (f"The same typical house tank (200 m² roof, 20,000 L, 300 L a day) run through {wt['label']}, the driest three years in a row "
           f"({wt['rain']:,.0f} mm): {'it ran short on ' + str(wt['dry']) + ' days' if wt['dry'] else 'it never ran dry'}, met {wt['share'] * 100:.0f}% of household use, "
           f"and its lowest point was {wt['min'] / 20000 * 100:.0f}% full. Plan storage for this run of years, not the average one.")
    fig.text(.06, .23, 'Worst years on record', fontsize=10.5, weight='bold', va='top')
    fig.text(.06, .20, textwrap.fill(msg, 112), fontsize=9.2, va='top', linespacing=1.45)
    save(fig)
    return s, wt

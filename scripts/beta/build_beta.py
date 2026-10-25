#!/usr/bin/env python3
"""Build a mapping-only "beta" map for one PDC group from the full map (map/index.html).

usage: python3 scripts/beta/build_beta.py <site-id> [--debug]
       python3 scripts/beta/build_beta.py all

Writes beta/<folder>/index.html (minified) plus that one site's data files next to it, and
beta/<folder>/files.json: the published-path -> repo-path map to pass to the Artifact tool as `files`.
--debug also writes index.debug.html (stripped but not minified) for testing.

What the beta keeps: the Layers, Draw and Features tabs, the 3D view, uploads of photos and plans,
and the shared drawings (same database collection names as the trial and live maps, so drawings
copy straight across). What goes: the Plan, Notes, Tools and Site tabs and the code behind them
(water balance, tank and dam simulations, season outlook, climate record, soil and wildlife cards,
energy, presentation sheet, 3D print, route finder, lopping planner, ram and hydro pumps, patterns),
the site picker and every other site. Wildlife recorded nearby is kept as a short Layers section.

Every text edit below must match exactly once: if the full map changes underneath, the build stops
and says which edit no longer fits, rather than quietly shipping something half-stripped.
"""
import sys, os, re, json, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'map' / 'index.html'
OUT = ROOT / 'beta'
ESBUILD = os.environ.get('ESBUILD', '/opt/npm-tools/node_modules/esbuild/bin/esbuild')
NODE_TOOLS = os.environ.get('NODE_TOOLS', '/opt/npm-tools/node_modules')

# the groups that get a beta (site id in SITES -> folder under map/sites and beta/)
GROUPS = {'nimbin-group': 'nimbin', 'bellbunya': 'bellbunya', 'willow-vale-team': 'willow-vale',
          'noosa-forest-retreat': 'noosa-forest-retreat', 'nac': 'nac', 'annwn': 'annwn', 'regenify': 'regenify', 'mangiri': 'mangiri'}

# data the kept layers read; everything else in the site folder (silo_*, outlook, rain_daily, ifd, soils) is tools-only
LAYER_FILES = ['terrain.json', 'hydro.json', 'extra.json', 'prospects.json', 'geology.json', 'hazard.json', 'services.json',
               'ecosystems.json', 'species.json', 'aerial.jpg', 'relief.jpg', 'hillshade.jpg', 'slope.png', 'aspect.png', 'cold.png',
               'sun_winter.png', 'sun_equinox.png', 'sun_summer.png', 'fire.png', 'wet.png', 'erosion.png']

# removed tabs' renderers and the tool modes: empty bodies, then strip.cjs drops what only they used
STUBS = {
    'renderPlan': '{}', 'renderTools': '{}', 'renderSite': '{}', 'renderNotes': '{}', 'ensureLong': '{return Promise.resolve(null)}',
    'renderSiteSel': '{}', 'siteBanner': '{}', 'sitesHTML': "{return ''}", 'featTasksHTML': "{return ''}",
    'startMT': '{}', 'resizeDam': '{}', 'startPattern': '{}', 'startBound': '{}', 'mtClick': '{}', 'drawMT': '{}', 'lopRun': '{}',
    'renderMTBar': "{const b=$('#drawbar');if(!mt)b.hidden=true}", 'damWBHTML': "{return ''}", 'wireDamWB': '{}', 'exportFile': '{}',
    # declarations whose initialiser only builds a table or reads a setting: safe to drop when nothing uses them
    '__pure__': ['slug', 'P3', 'CRC', 'WB', 'FB', 'bandOf', 'RT', 'planFilter', 'HY', 'PUMPS', 'RP', 'SKY', 'PIPE', 'savePAT', 'designFeats',
                 'TK', 'lpf', 'saveSO', 'dirOf', 'fmtHa', 'notes', 'nbName', 'DWB', 'PAT', 'LOP', 'GZ', 'SH'],
}

# public-facing: no street names or numbers, lot/plan numbers, emails or phone numbers
ROAD = r"(?:Road|Rd|Street|St|Lane|Ln|Drive|Dr|Avenue|Ave|Court|Ct|Place|Pl|Crescent|Cres|Parade|Pde|Close|Terrace|Tce|Highway|Hwy)"
SCRUB = [
    (re.compile(r"\b\d{1,5}[A-Za-z]?\s+[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s" + ROAD + r"\b\.?"), 'the road'),
    (re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s" + ROAD + r"\b\.?"), 'the road'),
    (re.compile(r"\bLots?\s?\d+[A-Za-z]?(?:\s?(?:on\s)?(?:RP|SP|DP|CP|BUP|GTP)\s?\d+)?", re.I), 'the lot'),
    (re.compile(r"\b(?:RP|SP|DP|CP|BUP|GTP)\s?\d{3,}\b"), 'the plan'),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), ''),
    (re.compile(r"\b(?:\+?61\s?|0)[2-478](?:[ -]?\d){8}\b"), ''),
    (re.compile(r"\s*\(DD1-01 D\)"), ''),
]


def scrub(s):
    for rx, rep in SCRUB:
        s = rx.sub(rep, s)
    return s


def scrub_obj(o):
    """scrub every short string in a JSON value (long strings are base64 rasters)"""
    if isinstance(o, str):
        return scrub(o) if len(o) < 2000 else o
    if isinstance(o, list):
        return [scrub_obj(v) for v in o]
    if isinstance(o, dict):
        return {k: scrub_obj(v) for k, v in o.items()}
    return o


class Doc:
    def __init__(self, text, what):
        self.t, self.what = text, what

    def sub(self, old, new, count=1):
        n = self.t.count(old)
        if n != count:
            sys.exit(f'build_beta: {self.what}: expected {count} match(es) for {old[:90]!r}, found {n}')
        self.t = self.t.replace(old, new)

    def resub(self, rx, new, flags=0):
        r = re.compile(rx, flags)
        if len(r.findall(self.t)) != 1:
            sys.exit(f'build_beta: {self.what}: regex {rx[:80]!r} must match once, found {len(r.findall(self.t))}')
        self.t = r.sub(lambda m: new, self.t)

    def drop_line(self, prefix):
        lines = self.t.split('\n')
        hit = [i for i, l in enumerate(lines) if l.lstrip().startswith(prefix)]
        if len(hit) != 1:
            sys.exit(f'build_beta: {self.what}: line starting {prefix[:70]!r} found {len(hit)} times')
        del lines[hit[0]]
        self.t = '\n'.join(lines)


WILD_JS = r"""
/* wildlife recorded nearby (Atlas of Living Australia): names and counts only, no locations */
function wildHTML(){if(!WILD||!WILD.groups)return '';const src=WILD.source||'Atlas of Living Australia';const when=WILD.fetched?new Date(WILD.fetched).toLocaleDateString('en-AU',{month:'short',year:'numeric'}):'';
 const nm=x=>x.common?`${esc(x.common)} <i>${esc(x.sci)}</i>`:`<i>${esc(x.sci)}</i>`;
 const listed=WILD.listed||[],pests=WILD.pests||[];
 const groups=Object.entries(WILD.groups).filter(([g,a])=>a&&a.length).sort((a,b)=>b[1].length-a[1].length);
 return `<p class="hint">${(WILD.total||0).toLocaleString()} records of ${groups.reduce((s,[g,a])=>s+a.length,0)} species within about 1 km of the block. Names and counts only: no locations are stored or shown.</p>
  ${listed.length?`<div class="sub2">Threatened or listed · ${listed.length}</div><p class="hint">${listed.map(x=>`${x.common?esc(x.common):'<i>'+esc(x.sci)+'</i>'} (${x.n})`).join(' · ')}</p><p class="hint">Shown as counts only. Status from known listings; confirm on the current state and national lists.</p>`:''}
  ${pests.length?`<div class="sub2">Pest plants and animals · ${pests.length}</div><p class="hint">${pests.map(x=>`${x.common?esc(x.common):'<i>'+esc(x.sci)+'</i>'} (${x.n})`).join(' · ')}</p>`:''}
  ${groups.map(([g,a])=>`<details class="mini"><summary>${esc(g)} · ${a.length}</summary><p class="hint">${a.filter(x=>!x.status).slice(0,40).map(x=>`${nm(x)} (${x.n})`).join(' · ')}${a.length>40?' …':''}</p></details>`).join('')}
  <div class="hint" style="margin-top:4px">Source: ${esc(src)}${when?', downloaded '+esc(when):''}. Record years vary; older records may be of species no longer present.</div>`}
"""

BETA_CSS = """
.betafoot{flex:none;border-top:1px solid var(--line);padding:6px 16px calc(6px + env(safe-area-inset-bottom,0px));font-size:10.5px;line-height:1.35;color:var(--muted);background:var(--panel)}
.betafoot button{font:inherit;color:var(--accent);background:none;border:0;padding:0;text-decoration:underline;cursor:pointer}
.betaterms{position:fixed;inset:0;z-index:50;display:grid;place-items:center;background:rgba(10,14,12,.45);padding:16px}
.betaterms[hidden]{display:none!important}
.betaterms .box{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:10px;max-width:440px;width:100%;padding:18px 20px;box-shadow:0 10px 40px rgba(0,0,0,.3);max-height:calc(100dvh - 32px);overflow:auto}
.betaterms h2{margin:0 0 8px;color:var(--ink)}
.betaterms ol{margin:0 0 12px;padding-left:20px;font-size:13.5px;line-height:1.5}.betaterms li{margin:0 0 6px}
.betabadge{display:inline-block;font:600 10px/1 var(--f-mono);letter-spacing:.06em;text-transform:uppercase;background:var(--accent);color:var(--accent-ink);border-radius:9px;padding:3px 7px;vertical-align:4px;margin-left:6px}
@media (max-width:760px){#panel>.betafoot{order:4}#panel.min .betafoot{display:none}}
"""


def terms_html(name):
    return f"""<div class="betaterms" id="betaTerms" role="dialog" aria-modal="true" aria-labelledby="btTitle" hidden><div class="box">
<h2 id="btTitle">Beta terms</h2>
<p class="hint">This is an early test version of the design map, made for {name} only.</p>
<ol>
<li>It is for evaluating the map and working on your own design.</li>
<li>Please don't copy or redistribute the map, its code or its method.</li>
<li>Your site data and drawings stay yours. Bright Tree may use them, with first names only and no addresses, to improve the tool.</li>
<li>Feedback is very welcome: use Send feedback or leave a comment on the page.</li>
</ol>
<p class="hint">Using the map means you accept these terms.</p>
<button class="btn primary" id="btOk">I understand</button></div></div>
"""


def footer_html(name):
    return (f'<div class="betafoot" id="betaFoot">© Bright Tree. Beta access for {name} only: please don\'t copy or reuse the map or its data. '
            f'Your site data stays yours. <button id="btShow">Beta terms</button></div>\n')


TERMS_JS = r"""
/* beta terms: shown once per browser */
(function(){const k='bt.betaTerms.v1',box=$('#betaTerms');let seen=false;try{seen=localStorage.getItem(LSK(k))==='1'}catch(e){}
 const close=()=>{box.hidden=true;try{localStorage.setItem(LSK(k),'1')}catch(e){}};
 $('#btOk').onclick=close;$('#btShow').onclick=()=>{box.hidden=false;$('#btOk').focus()};box.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
 if(!seen){box.hidden=false;setTimeout(()=>{try{$('#btOk').focus()}catch(e){}},50)}})();
"""


def site_entry(js, sid):
    m = re.search(r"^ \{id:'" + re.escape(sid) + r"',.*?\}(?=,?\]?;?$)", js, re.M)
    if not m:
        sys.exit(f'build_beta: site {sid} not in SITES')
    e = m.group(0).strip()
    e = re.sub(r",base:'[^']*'", '', e)
    e = re.sub(r",area:'[^']*'", '', e)
    e = e[:-1] + ",base:''}"
    return e


def build(sid, debug=False):
    folder = GROUPS[sid]
    sdir = ROOT / 'map' / 'sites' / folder
    terr = json.load(open(sdir / 'terrain.json'))
    ms = terr['meta']['site']
    name = ms['name']
    html = SRC.read_text()
    i0 = html.index('<script>')
    i1 = html.index('</script>', i0)
    head, js, tail = html[:i0], html[i0 + 8:i1], html[i1 + 9:]

    # ---------- page ----------
    H = Doc(head, 'page')
    H.resub(r'<title>[^<]*</title>', f'<title>{name} Design Map · Beta</title>')
    for t in ('plan', 'notes', 'tools', 'site'):
        H.resub(r'\n\s*<button role="tab" id="t-' + t + r'"[^\n]*</button>', '')
    H.resub(r'\n\s*<div class="sitesel">.*?</select></div>', '')
    H.sub('<h1 id="siteName">Design Map</h1>', f'<h1 id="siteName">{name} Design Map<span class="betabadge">Beta</span></h1>')
    H.sub('  </aside>', '    ' + footer_html(name) + '  </aside>')
    H.sub('</style>', BETA_CSS + '</style>')
    head = H.t.replace('<script>', '')
    head = head.rstrip() + '\n' + terms_html(name)

    # ---------- script ----------
    J = Doc(js, 'script')
    J.resub(r"let SITE=\{name:'Bright Tree'.*?\};\n", "let SITE={name:" + json.dumps(name) + ",subtitle:'',state:'',council:'',lfw:false,main:'',res:'',years:[],changeYears:[],boundaryNote:'',source:'',soilNote:''};\n", re.S)
    J.resub(r"let E0=\d+, N0=\d+;", f"let E0={terr['E0']}, N0={terr['N0']};")
    J.resub(r"let LAT=[-\d.]+, LON=[-\d.]+, ZONE=\d+;", f"let LAT={ms['lat']}, LON={ms['lon']}, ZONE={ms['zone']};")
    J.resub(r"const SITES=\[\n.*?\];\n", 'const SITES=[' + site_entry(js, sid) + '];\n', re.S)
    J.resub(r"const SITE_ALIAS=\{[^\n]*\};", 'const SITE_ALIAS={};')
    J.resub(r"const SITEID=\(\(\)=>\{[^\n]*\}\)\(\);", f"const SITEID='{sid}';")
    J.sub("document.title=SITE.name+' Design Map';$('#siteName').textContent=SITE.name+' Design Map';",
          "document.title=SITE.name+' Design Map · Beta';$('#siteName').innerHTML=esc(SITE.name)+' Design Map<span class=\"betabadge\">Beta</span>';")
    # tabs
    J.sub("for(const id of ['layers','draw','feat','plan','notes','tools','site'])$('#tab-'+id).hidden=id!==t;sheetOpen();lsSet('bt.tab',t);if(t==='site'||t==='tools')ensureLong();if(t==='tools')renderTools();if(t==='notes')renderNotes()}",
          "for(const id of ['layers','draw','feat','plan','notes','tools','site'])$('#tab-'+id).hidden=id!==t;sheetOpen();lsSet('bt.tab',t)}")
    J.sub("function showTab(t){", "function showTab(t){if(!['layers','draw','feat'].includes(t))t='layers';")
    # data the removed tools read
    for f in ('rain_daily', 'silo_full', 'outlook', 'soils'):
        J.drop_line("try{const " + {'rain_daily': 'dr', 'silo_full': 'sf', 'outlook': 'so', 'soils': 'so2'}[f] + "=await fetch(SB+'" + f + ".json')")
    # live sync of the removed tabs' collections (tasks, notebook, drone suggestions, water settings)
    J.drop_line("if(db)keepLive('suggest'")
    J.drop_line("if(db)keepLive('tasks'")
    J.drop_line("if(db)keepLive('notebook'")
    J.drop_line("else{const ln=lsGet('bt.notes'")
    J.drop_line("if(db)keepLive('water'")
    J.drop_line("try{downloads=window.claude?await window.claude.use('downloads')")
    # features panel: no tasks or notebook links, no roof-to-tank setting
    J.resub(r"\$\{featTasksHTML\(selected\)\}\$\{\(\(\)=>\{const ns=.*?\}\)\(\)\}", '')
    J.resub(r"\$\{ROOF_KINDS\.includes\(f\.kind\).*?</label></div>`:''\}", '', re.S)
    J.drop_line("$('#fAddTask').onclick=")
    J.sub("$('#fNote').onclick=()=>{showTab('notes');setTimeout(()=>{const a=$('#nbAbout');if(a)a.value=selected;const t=$('#nbTxt');if(t)t.focus()},40)};", '')
    J.sub("if($('#froof'))$('#froof').onchange=e=>{saveFields(selected,{roof:e.target.checked});renderTools()};", '')
    # layers: dams list without the dam calculator and dry-season simulation
    J.sub("+`<div id=\"damWB\">${damWBHTML()}</div>`", '')
    J.sub("${rs?`<button class=\"btn\" data-rs=", "${false?`<button class=\"btn\" data-rs=")
    J.sub("${p.kind==='pond'&&p.wall?` <button class=\"btn\" data-prs=", "${false?` <button class=\"btn\" data-prs=")
    J.sub(" (test it in Tools → Light & lopping planner)", '')
    J.sub("Sun sectors draw themselves for 26.7°S", "Sun sectors draw themselves for ${Math.abs(LAT).toFixed(1)}°S")
    # layers: wildlife recorded nearby
    J.sub("   (HAZ?sec('haz','Rules and hazards',hazHTML(),false):'')+",
          "   (HAZ?sec('haz','Rules and hazards',hazHTML(),false):'')+\n   (WILD?sec('wild','Wildlife recorded nearby (ALA)',wildHTML(),false):'')+")
    J.sub("function renderLayers(){", WILD_JS.strip() + "\nfunction renderLayers(){")
    # start-up
    J.sub("showTab(lsGet('bt.tab','layers')==='feat'?'layers':lsGet('bt.tab','layers'));", "showTab(lsGet('bt.tab','layers')==='draw'?'draw':'layers');" + TERMS_JS)

    tmp = Path(tempfile.mkdtemp(prefix='beta-'))
    (tmp / 'in.js').write_text(J.t)
    (tmp / 'stubs.json').write_text(json.dumps(STUBS))
    r = subprocess.run(['node', str(ROOT / 'scripts/beta/strip.cjs'), str(tmp / 'in.js'), str(tmp / 'out.js'), str(tmp / 'stubs.json')],
                       capture_output=True, text=True, env={**os.environ, 'NODE_TOOLS': NODE_TOOLS})
    if r.returncode:
        sys.exit('strip failed:\n' + r.stdout + r.stderr)
    stripped = (tmp / 'out.js').read_text()
    strip_report = r.stdout.strip().splitlines()[-1]
    m = subprocess.run([ESBUILD, str(tmp / 'out.js'), '--minify', '--format=iife', '--target=es2020', '--legal-comments=none', '--charset=utf8'],
                       capture_output=True, text=True)
    if m.returncode:
        sys.exit('esbuild failed:\n' + m.stderr)
    minjs = m.stdout
    # css: drop comments, minify
    css_m = re.search(r'<style>\n(.*?)</style>', head, re.S)
    c = subprocess.run([ESBUILD, '--loader=css', '--minify', '--charset=utf8'], input=css_m.group(1), capture_output=True, text=True)
    if c.returncode:
        sys.exit('css minify failed:\n' + c.stderr)
    head_min = head[:css_m.start()] + '<style>' + c.stdout.strip() + '</style>' + head[css_m.end():]
    page = scrub(head_min) + '<script>' + minjs + '</script>' + tail

    od = OUT / folder
    if od.exists():
        shutil.rmtree(od)
    od.mkdir(parents=True)
    (od / 'index.html').write_text(page)
    if debug:
        (od / 'index.debug.html').write_text(head + '<script>' + stripped + '</script>' + tail)

    # ---------- data ----------
    files = {}
    for f in LAYER_FILES:
        p = sdir / f
        if not p.exists():
            continue
        if f.endswith('.json'):
            d = json.load(open(p))
            if f == 'terrain.json':
                d['meta']['site'] = scrub_obj(d['meta']['site'])
            else:
                d = scrub_obj(d)
            (od / f).write_text(json.dumps(d, separators=(',', ':'), ensure_ascii=False))
        else:
            shutil.copy(p, od / f)
        files[f] = str((od / f).relative_to(ROOT))
    for y in ms.get('changeYears') or []:
        f = f'change_{y}.png'
        if (sdir / f).exists():
            shutil.copy(sdir / f, od / f); files[f] = str((od / f).relative_to(ROOT))
    sdef = site_entry(js, sid)
    if 'history:true' in sdef and (sdir / 'history').is_dir():
        (od / 'history').mkdir()
        hj = scrub_obj(json.load(open(sdir / 'history' / 'history.json')))
        (od / 'history' / 'history.json').write_text(json.dumps(hj, separators=(',', ':'), ensure_ascii=False))
        files['history/history.json'] = str((od / 'history' / 'history.json').relative_to(ROOT))
        for run in hj['runs']:
            src = sdir / 'history' / run['f']
            if src.exists():
                shutil.copy(src, od / 'history' / run['f']); files['history/' + run['f']] = str((od / 'history' / run['f']).relative_to(ROOT))
    (od / 'files.json').write_text(json.dumps(files, indent=1))
    size = sum((ROOT / v).stat().st_size for v in files.values())
    print(f"{sid:22s} page {len(page.encode())/1024:6.1f} KB  data {len(files):3d} files {size/1e6:6.2f} MB  | {strip_report}")
    return od


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    ids = list(GROUPS) if args[0] == 'all' else args
    for s in ids:
        if s not in GROUPS:
            sys.exit(f'unknown site {s}; one of {", ".join(GROUPS)}')
        build(s, '--debug' in sys.argv)

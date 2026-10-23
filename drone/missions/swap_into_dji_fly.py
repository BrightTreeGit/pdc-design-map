"""Put Bright Tree mapping missions into DJI Fly (DJI RC 2).

1. In DJI Fly save one dummy waypoint mission (2 points anywhere) per mission you want.
2. Plug the controller into the PC. Open: Internal storage > Android > data > dji.go.v5 > files > waypoint
   Copy the long-named folders (not 'capability') into this folder. Copying just the .kmz files works too.
3. Run this script (or the .bat). Press Enter to fill the dummies automatically in this order:
     SW inside M1, M2, cross 1, cross 2 · SW half-Cumner-Rd M1, M2, cross 1, cross 2 ·
     SE inside M1, M2, cross 1, cross 2 · SE half-Cumner-Rd M1, M2, cross 1, cross 2
   (fewer dummies = the first ones in that list), or type your own numbers.
4. Drag every folder inside 'to_controller' onto the controller's waypoint folder and choose Replace.
   Restart DJI Fly. A list of which folder holds which mission is saved as to_controller/WHICH_IS_WHICH.txt.
"""
import zipfile, re, sys, os, glob, shutil

here = os.path.dirname(os.path.abspath(__file__))
missions = sorted(glob.glob(os.path.join(here, '**', 'BrightTree_*.kmz'), recursive=True))
missions = [m for m in missions if os.sep + 'to_controller' + os.sep not in m]
UUID = re.compile(r'^[0-9A-Fa-f]{6,}(-[0-9A-Fa-f]{2,}){2,}$')

# dummies: <uuid>/<uuid>.kmz folders copied from the controller, or loose <uuid>.kmz files
dummies = []
for d in sorted(os.listdir(here)):
    p = os.path.join(here, d)
    if os.path.isdir(p) and UUID.match(d):
        k = os.path.join(p, d + '.kmz')
        if not os.path.exists(k):
            ks = glob.glob(os.path.join(p, '*.kmz')); k = ks[0] if ks else None
        if k: dummies.append((d, k, True))
    elif d.lower().endswith('.kmz') and not d.startswith('BrightTree_') and UUID.match(d[:-4]):
        dummies.append((d[:-4], p, False))
if not dummies: sys.exit('No dummy missions found. Copy the long-named folders (or their .kmz files) from the controller into this folder.')

def find(tag):
    for i, m in enumerate(missions):
        if os.path.basename(m) == tag: return i
    return None
AUTO = ['BrightTree_SW_inside_mission1of2.kmz', 'BrightTree_SW_inside_mission2of2.kmz', 'BrightTree_SW_inside_cross1of2.kmz', 'BrightTree_SW_inside_cross2of2.kmz',
        'BrightTree_SW_road_mission1of2.kmz', 'BrightTree_SW_road_mission2of2.kmz', 'BrightTree_SW_road_cross1of2.kmz', 'BrightTree_SW_road_cross2of2.kmz',
        'BrightTree_SE_inside_mission1of2.kmz', 'BrightTree_SE_inside_mission2of2.kmz', 'BrightTree_SE_inside_cross1of2.kmz', 'BrightTree_SE_inside_cross2of2.kmz',
        'BrightTree_SE_road_mission1of2.kmz', 'BrightTree_SE_road_mission2of2.kmz', 'BrightTree_SE_road_cross1of2.kmz', 'BrightTree_SE_road_cross2of2.kmz']
auto = [find(t) for t in AUTO]; auto = [a for a in auto if a is not None]

print(f'{len(dummies)} dummy mission(s) found.')
print('Bright Tree missions:')
for i, m in enumerate(missions): print(f'  {i+1}. {os.path.relpath(m, here)}')
ans = input(f'\nPress Enter to fill them automatically (SW inside, SW half Cumner Rd, SE inside, SE half Cumner Rd),\nor type mission numbers separated by spaces: ').strip()
picks = [int(x) - 1 for x in ans.replace(',', ' ').split()] if ans else auto
picks = picks[:len(dummies)]

def blocks(z):
    t = z.read('wpmz/template.kml').decode('utf-8'); out = {}
    for tag in ('droneInfo', 'payloadInfo'):
        m = re.search(rf'<wpml:{tag}>.*?</wpml:{tag}>', t, re.S); out[tag] = m.group(0) if m else ''
    return out

outdir = os.path.join(here, 'to_controller')
if os.path.isdir(outdir): shutil.rmtree(outdir)
os.makedirs(outdir)
log = []
for (name, kmz, isdir), pi in zip(dummies, picks):
    pick = missions[pi]
    with zipfile.ZipFile(kmz) as z: B = blocks(z)
    if not B['droneInfo']: print('  could not read the drone details in', name[:13], '- skipped'); continue
    if isdir:
        # copy the whole folder so anything else DJI keeps there (thumbnails) stays, then replace the .kmz
        dst_dir = os.path.join(outdir, name); shutil.copytree(os.path.dirname(kmz), dst_dir)
        dst = os.path.join(dst_dir, os.path.basename(kmz))
    else:
        dst = os.path.join(outdir, name + '.kmz')
    with zipfile.ZipFile(pick) as zi, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in zi.namelist():
            s = zi.read(n).decode('utf-8')
            s = re.sub(r'<wpml:droneInfo>.*?</wpml:droneInfo>', B['droneInfo'], s, flags=re.S)
            if n.endswith('template.kml') and B['payloadInfo'] and '<wpml:payloadInfo>' not in s:
                s = s.replace('</wpml:missionConfig>', '</wpml:missionConfig>' + B['payloadInfo'], 1)
            zo.writestr(n, s)
    label = os.path.basename(pick).replace('BrightTree_', '').replace('.kmz', '')
    log.append(f'{name}  =  {label}'); print(f'  {name[:13]}...  ->  {label}')
open(os.path.join(outdir, 'WHICH_IS_WHICH.txt'), 'w').write('\n'.join(log) + '\n')
left = len(dummies) - len(log)
print(f'\nDone: {len(log)} mission(s) ready in to_controller.' + (f' {left} dummy(s) left unused.' if left > 0 else ''))
print('Drag every folder inside to_controller onto the controller\'s waypoint folder and choose Replace, then restart DJI Fly.')
print('Which is which: to_controller/WHICH_IS_WHICH.txt')
try: input('\nPress Enter to close.')
except EOFError: pass

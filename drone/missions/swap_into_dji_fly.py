"""Put a Bright Tree mapping mission into DJI Fly.
1. In DJI Fly make one dummy waypoint mission (2 points anywhere) per mission you want, and save each.
   Make them in order (dummy 1 for mission 1, and so on): the script lists them oldest first.
2. Plug the controller into the PC (USB-C). Open: Internal storage > Android > data > dji.go.v5 > files > waypoint
   Each long-named folder holds one dummy .kmz. Copy all of those .kmz files into this folder (keep their long names).
3. Run this script (or the .bat). It writes a new file with the SAME long name into the 'to_controller' folder,
   using the drone details from your dummy mission and the flight path from the Bright Tree mission you choose.
4. Copy that file back into the same waypoint folder on the controller, replacing the dummy. Restart DJI Fly.
"""
import zipfile, re, sys, os, glob
here=os.path.dirname(os.path.abspath(__file__))
missions=sorted(glob.glob(os.path.join(here,'**','BrightTree_*.kmz'),recursive=True))
dummies=sorted([f for f in glob.glob(os.path.join(here,'*.kmz')) if not os.path.basename(f).startswith('BrightTree_')],key=os.path.getmtime)
if not dummies: sys.exit('Copy the dummy mission .kmz file(s) from the controller into this folder first.')
print('Bright Tree missions:')
for i,m in enumerate(missions): print(f'  {i+1}. {os.path.relpath(m,here)}')
def blocks(z):
    t=z.read('wpmz/template.kml').decode('utf-8')
    out={}
    for tag in ('droneInfo','payloadInfo'):
        m=re.search(rf'<wpml:{tag}>.*?</wpml:{tag}>',t,re.S); out[tag]=m.group(0) if m else ''
    return out
os.makedirs(os.path.join(here,'to_controller'),exist_ok=True)
done=[]
print(f'\n{len(dummies)} dummy mission(s) found, oldest first (the order you saved them in DJI Fly).')
for dummy in dummies:
    ans=input(f'\nDummy {os.path.basename(dummy)[:13]}... : which mission number goes in it? (Enter to skip) ').strip()
    if not ans: continue
    pick=missions[int(ans)-1]
    with zipfile.ZipFile(dummy) as z: B=blocks(z)
    if not B['droneInfo']: print('   Could not find the drone details in this dummy; skipped.'); continue
    dst=os.path.join(here,'to_controller',os.path.basename(dummy))
    with zipfile.ZipFile(pick) as zi, zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as zo:
        for n in zi.namelist():
            s_=zi.read(n).decode('utf-8')
            s_=re.sub(r'<wpml:droneInfo>.*?</wpml:droneInfo>',B['droneInfo'],s_,flags=re.S)
            if n.endswith('template.kml') and B['payloadInfo'] and '<wpml:payloadInfo>' not in s_: s_=s_.replace('</wpml:missionConfig>','</wpml:missionConfig>'+B['payloadInfo'],1)
            zo.writestr(n,s_)
    done.append((os.path.basename(dummy),os.path.basename(pick)))
    print('   ready:',os.path.basename(pick),'->',os.path.basename(dummy)[:13]+'...')
print('\nCopy each file in to_controller back into the waypoint folder on the controller with the SAME long name')
print('(each goes into its own long-named folder, replacing the dummy). Then restart DJI Fly.')
for d,m in done: print('  ',d[:13]+'...','=',m)
try: input('\nPress Enter to close.')
except EOFError: pass

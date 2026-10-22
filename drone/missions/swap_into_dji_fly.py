"""Put a Bright Tree mapping mission into DJI Fly.
1. In DJI Fly make a dummy waypoint mission (2 points anywhere) and save it.
2. Plug the controller into the PC (USB-C). Open: Internal storage > Android > data > dji.go.v5 > files > waypoint
   Open the newest folder. Copy the .kmz inside it to this folder (keep its long name).
3. Run this script (or the .bat). It writes a new file with the SAME long name into the 'to_controller' folder,
   using the drone details from your dummy mission and the flight path from the Bright Tree mission you choose.
4. Copy that file back into the same waypoint folder on the controller, replacing the dummy. Restart DJI Fly.
"""
import zipfile, re, sys, os, glob
here=os.path.dirname(os.path.abspath(__file__))
missions=sorted(glob.glob(os.path.join(here,'**','BrightTree_*.kmz'),recursive=True))
dummies=[f for f in glob.glob(os.path.join(here,'*.kmz')) if not os.path.basename(f).startswith('BrightTree_')]
if not dummies: sys.exit('Copy the dummy mission .kmz from the controller into this folder first.')
dummy=max(dummies,key=os.path.getmtime)
print('Dummy mission from the controller:',os.path.basename(dummy))
for i,m in enumerate(missions): print(f'  {i+1}. {os.path.relpath(m,here)}')
pick=missions[int(input('Which mission number? '))-1]
def blocks(z):
    t=z.read('wpmz/template.kml').decode('utf-8')
    out={}
    for tag in ('droneInfo','payloadInfo'):
        m=re.search(rf'<wpml:{tag}>.*?</wpml:{tag}>',t,re.S); out[tag]=m.group(0) if m else ''
    return out
with zipfile.ZipFile(dummy) as z: B=blocks(z)
if not B['droneInfo']: sys.exit('Could not find the drone details in the dummy mission.')
os.makedirs(os.path.join(here,'to_controller'),exist_ok=True)
dst=os.path.join(here,'to_controller',os.path.basename(dummy))
with zipfile.ZipFile(pick) as zi, zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as zo:
    for n in zi.namelist():
        s=zi.read(n).decode('utf-8')
        s=re.sub(r'<wpml:droneInfo>.*?</wpml:droneInfo>',B['droneInfo'],s,flags=re.S)
        if n.endswith('template.kml') and B['payloadInfo'] and '<wpml:payloadInfo>' not in s: s=s.replace('</wpml:missionConfig>','</wpml:missionConfig>'+B['payloadInfo'],1)
        zo.writestr(n,s)
print('\nReady:',dst,'\nCopy it back into the same waypoint folder on the controller, replacing the dummy file, then restart DJI Fly.')
try: input('Press Enter to close.')
except EOFError: pass

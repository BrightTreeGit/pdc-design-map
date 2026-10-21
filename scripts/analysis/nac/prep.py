import json,sys,numpy as np,math,statistics,subprocess
sys.path.insert(0,'/tmp/claude-0/scripts'); from build_site import ll2mga,mga2ll
from PIL import Image; from scipy import ndimage
D='/mnt/user-data/uploads/Permiculture Noosa PDC/NAC/Lidar-survey data/NSW site pack nac/'
OUT='/tmp/claude-0/-home-claude/683a26ba-af7b-52db-b3e7-8ba1d74ca58c/scratchpad/brighttree-map/sites/nac'
w=json.load(open(D+'window.json'))
Image.open(D+'aerial_nac.jpg').convert('RGB').resize((3000,3000),Image.LANCZOS).save('aerial.jpg',quality=84)
# rain
j=json.load(open(D+'silo_daily.json'));rain={};tmin={}
for r in j['data']:
  y,m=int(r['date'][:4]),int(r['date'][5:7])
  for v in r['variables']:
    if v['variable_code']=='daily_rain': rain.setdefault((y,m),[]).append(v['value'])
    if v['variable_code']=='min_temp': tmin.setdefault(m,[]).append(v['value'])
years=sorted({y for y,m in rain});mean=[];med=[];days=[];tm=[]
for m in range(1,13):
  tot=[sum(rain[(y,m)]) for y in years if (y,m) in rain]; dd=[sum(1 for v in rain[(y,m)] if v>=1) for y in years if (y,m) in rain]
  mean.append(round(sum(tot)/len(tot),1));med.append(round(statistics.median(tot),1));days.append(round(sum(dd)/len(dd),1));tm.append(round(sum(tmin[m])/len(tmin[m]),1))
R={'station':'SILO gridded data at the property (BoM)','distanceKm':0,'elevDiffM':0,'period':f'{years[0]}–{years[-1]}','mean':mean,'median':med,'days':days,'tmin':tm,'tminStation':'SILO gridded'}
print('rain/yr',round(sum(mean)),R)
g=json.load(open(D+'boundary.geojson'));c=g['features'][0]['geometry']['coordinates'][0]
cfg={'name':'NAC','subtitle':'North Arm Cove, Mid Coast NSW','state':'NSW','council':'MidCoast','dem':{'2019':[D+'dem_5m.tif']},'boundary':{'lonlat':c},'zone':56,
 'window':[w['E0'],w['N0']],'lfw':False,'rain':R,
 'source':'NSW 5 m elevation (DCS Spatial Services, from aerial stereo imagery), resampled to the 1 m map grid',
 'boundaryNote':'Property outline from the NSW property register (about ±1–2 m). A small block: zoom in to work on it.',
 'soilNote':'Elevation is 5 m from aerial photos: on a small block, banks, driveways and garden levels are smoothed out. Check falls on site with a level.','out':OUT}
json.dump(cfg,open('cfg.json','w'))
r=subprocess.run(['python3','/tmp/claude-0/scripts/build_site.py','cfg.json'],capture_output=True,text=True);print(r.stdout[-1500:],r.stderr[-1500:])
import shutil;shutil.copy('aerial.jpg',OUT+'/aerial.jpg')

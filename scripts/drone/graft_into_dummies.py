"""Write Bright Tree missions into DJI Fly's own file layout, using dummy missions saved on the controller.

DJI Fly (Mini 4/5 Pro, RC 2) stores each mission as <uuid>/<uuid>.kmz with:
  wpmz/template.kml   only the mission settings (namespace http://www.uav.com/wpmz/1.0.2)
  wpmz/waylines.wpml  the settings plus a Folder of Placemarks (the waypoints)
This keeps the dummy's own template and header exactly and replaces only the waypoints, so the file
matches what the app wrote itself.

usage: python3 graft_into_dummies.py <dummies_dir> <out_dir>
       dummies are filled oldest first in the AUTO order below.
"""
import sys, os, re, json, zipfile, glob, shutil, math

PLANS = {'inside': ('mission_plan_main_buf0.json', 'mission_plan_cross_buf0.json'),
         'road': ('mission_plan_main_road.json', 'mission_plan_cross_road.json')}
AUTO = [('SW', 'inside', 'main', 0), ('SW', 'inside', 'main', 1), ('SW', 'inside', 'cross', 0), ('SW', 'inside', 'cross', 1),
        ('SW', 'road', 'main', 0), ('SW', 'road', 'main', 1), ('SW', 'road', 'cross', 0), ('SW', 'road', 'cross', 1),
        ('SE', 'inside', 'main', 0), ('SE', 'inside', 'main', 1), ('SE', 'inside', 'cross', 0), ('SE', 'inside', 'cross', 1),
        ('SE', 'road', 'main', 0), ('SE', 'road', 'main', 1), ('SE', 'road', 'cross', 0), ('SE', 'road', 'cross', 1)]
SPEED, TRANSIT = 4.5, 8.0

def placemark(i, w, n):
    lo, la = w['ll']; h = round(w['rel'], 1); sp = TRANSIT if w['transit'] else SPEED
    acts = ''
    if i == 0:
        acts += f'''
        <wpml:actionGroup>
          <wpml:actionGroupId>1</wpml:actionGroupId>
          <wpml:actionGroupStartIndex>0</wpml:actionGroupStartIndex>
          <wpml:actionGroupEndIndex>0</wpml:actionGroupEndIndex>
          <wpml:actionGroupMode>parallel</wpml:actionGroupMode>
          <wpml:actionTrigger>
            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
          </wpml:actionTrigger>
          <wpml:action>
            <wpml:actionId>1</wpml:actionId>
            <wpml:actionActuatorFunc>gimbalRotate</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:gimbalHeadingYawBase>aircraft</wpml:gimbalHeadingYawBase>
              <wpml:gimbalRotateMode>absoluteAngle</wpml:gimbalRotateMode>
              <wpml:gimbalPitchRotateEnable>1</wpml:gimbalPitchRotateEnable>
              <wpml:gimbalPitchRotateAngle>-90</wpml:gimbalPitchRotateAngle>
              <wpml:gimbalRollRotateEnable>1</wpml:gimbalRollRotateEnable>
              <wpml:gimbalRollRotateAngle>0</wpml:gimbalRollRotateAngle>
              <wpml:gimbalYawRotateEnable>0</wpml:gimbalYawRotateEnable>
              <wpml:gimbalYawRotateAngle>0</wpml:gimbalYawRotateAngle>
              <wpml:gimbalRotateTimeEnable>0</wpml:gimbalRotateTimeEnable>
              <wpml:gimbalRotateTime>0</wpml:gimbalRotateTime>
              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
        </wpml:actionGroup>'''
    if i < n - 1:
        acts += f'''
        <wpml:actionGroup>
          <wpml:actionGroupId>{i + 2}</wpml:actionGroupId>
          <wpml:actionGroupStartIndex>{i}</wpml:actionGroupStartIndex>
          <wpml:actionGroupEndIndex>{i + 1}</wpml:actionGroupEndIndex>
          <wpml:actionGroupMode>parallel</wpml:actionGroupMode>
          <wpml:actionTrigger>
            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
          </wpml:actionTrigger>
          <wpml:action>
            <wpml:actionId>{i + 2}</wpml:actionId>
            <wpml:actionActuatorFunc>gimbalEvenlyRotate</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:gimbalPitchRotateAngle>-90</wpml:gimbalPitchRotateAngle>
              <wpml:gimbalRollRotateAngle>0</wpml:gimbalRollRotateAngle>
              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
        </wpml:actionGroup>'''
    return f'''      <Placemark>
        <Point>
          <coordinates>
            {lo:.12f},{la:.12f}
          </coordinates>
        </Point>
        <wpml:index>{i}</wpml:index>
        <wpml:executeHeight>{h}</wpml:executeHeight>
        <wpml:waypointSpeed>{sp}</wpml:waypointSpeed>
        <wpml:waypointHeadingParam>
          <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
          <wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle>
          <wpml:waypointPoiPoint>0.000000,0.000000,0.000000</wpml:waypointPoiPoint>
          <wpml:waypointHeadingAngleEnable>0</wpml:waypointHeadingAngleEnable>
          <wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode>
          <wpml:waypointHeadingPoiIndex>0</wpml:waypointHeadingPoiIndex>
        </wpml:waypointHeadingParam>
        <wpml:waypointTurnParam>
          <wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode>
          <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>
        </wpml:waypointTurnParam>
        <wpml:useStraightLine>1</wpml:useStraightLine>{acts}
        <wpml:waypointGimbalHeadingParam>
          <wpml:waypointGimbalPitchAngle>-90</wpml:waypointGimbalPitchAngle>
          <wpml:waypointGimbalYawAngle>0</wpml:waypointGimbalYawAngle>
        </wpml:waypointGimbalHeadingParam>
      </Placemark>
'''

def build(dummy_kmz, m, dst):
    z = zipfile.ZipFile(dummy_kmz)
    tmpl = z.read('wpmz/template.kml').decode('utf-8'); wl = z.read('wpmz/waylines.wpml').decode('utf-8')
    W = m['wps']; n = len(W)
    dist = 0.0
    for a, b in zip(W, W[1:]): dist += math.hypot(b['x'] - a['x'], b['y'] - a['y'])
    pm = ''.join(placemark(i, w, n) for i, w in enumerate(W))
    head = wl[:wl.index('<Folder>')]
    head = re.sub(r'<wpml:globalTransitionalSpeed>[^<]*</wpml:globalTransitionalSpeed>', f'<wpml:globalTransitionalSpeed>{TRANSIT}</wpml:globalTransitionalSpeed>', head)
    tmpl = re.sub(r'<wpml:globalTransitionalSpeed>[^<]*</wpml:globalTransitionalSpeed>', f'<wpml:globalTransitionalSpeed>{TRANSIT}</wpml:globalTransitionalSpeed>', tmpl)
    folder = f'''<Folder>
      <wpml:templateId>0</wpml:templateId>
      <wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode>
      <wpml:waylineId>0</wpml:waylineId>
      <wpml:distance>{int(dist)}</wpml:distance>
      <wpml:duration>{int(m['minutes'] * 60)}</wpml:duration>
      <wpml:autoFlightSpeed>{SPEED}</wpml:autoFlightSpeed>
{pm}    </Folder>
  </Document>
</kml>
'''
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zo:
        zo.writestr('wpmz/template.kml', tmpl); zo.writestr('wpmz/waylines.wpml', head + folder)

def main():
    src, out = sys.argv[1], sys.argv[2]
    here = os.path.dirname(os.path.abspath(__file__)); pdir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, '..', '..', 'drone', 'missions')
    plans = {k: [json.load(open(os.path.join(pdir, f))) for f in v] for k, v in PLANS.items()}
    dummies = []
    for d in os.listdir(src):
        k = os.path.join(src, d, d + '.kmz')
        if os.path.exists(k): dummies.append((os.path.getmtime(k), d, k))
    dummies.sort()
    if os.path.isdir(out): shutil.rmtree(out)
    os.makedirs(out); log = []
    for (t, d, k), (corner, ver, pas, idx) in zip(dummies, AUTO):
        P = plans[ver][0 if pas == 'main' else 1]['plans'][corner]; m = P['missions'][idx]
        od = os.path.join(out, d); shutil.copytree(os.path.join(src, d), od)
        build(k, m, os.path.join(od, d + '.kmz'))
        name = f"{corner} {'Inside' if ver == 'inside' else 'Half Cumner Rd'} {'M' if pas == 'main' else 'Cross '}{idx + 1}"
        log.append(f'{d}  =  {name}   ({m["n"]} waypoints, about {round(m["minutes"])} min, first height {m["wps"][0]["rel"]:.0f} m)')
    open(os.path.join(out, 'WHICH_IS_WHICH.txt'), 'w').write('\n'.join(log) + '\n')
    print('\n'.join(log))

if __name__ == '__main__':
    main()

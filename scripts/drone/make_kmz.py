"""Write DJI Fly waypoint missions (KMZ, WPML 1.0.6) + a Google Earth KML from mission_plan.json.
The droneInfo block is a placeholder: swap_into_dji_fly.py copies the real one from a dummy
mission saved on your own controller, so the file matches your drone exactly."""
import json, sys, zipfile, time, math, os
src,out=sys.argv[1],sys.argv[2]; os.makedirs(out,exist_ok=True)
d=json.load(open(src)); M=d['meta']; now=int(time.time()*1000)
NS='xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.6"'
DRONE='<wpml:droneInfo><wpml:droneEnumValue>68</wpml:droneEnumValue><wpml:droneSubEnumValue>0</wpml:droneSubEnumValue></wpml:droneInfo>'
def mission_cfg(rth):
    return f'''<wpml:missionConfig><wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode><wpml:finishAction>goHome</wpml:finishAction><wpml:exitOnRCLost>executeLostAction</wpml:exitOnRCLost><wpml:executeRCLostAction>goBack</wpml:executeRCLostAction><wpml:takeOffSecurityHeight>20</wpml:takeOffSecurityHeight><wpml:globalTransitionalSpeed>8</wpml:globalTransitionalSpeed><wpml:globalRTHHeight>{rth}</wpml:globalRTHHeight>{DRONE}</wpml:missionConfig>'''
def pm(i,w,speed,tmpl):
    sp=8 if w['transit'] else speed; lo,la=w['ll']; h=w['rel']
    act=''
    if i==0: act=f'<wpml:actionGroup><wpml:actionGroupId>0</wpml:actionGroupId><wpml:actionGroupStartIndex>0</wpml:actionGroupStartIndex><wpml:actionGroupEndIndex>0</wpml:actionGroupEndIndex><wpml:actionGroupMode>sequence</wpml:actionGroupMode><wpml:actionTrigger><wpml:actionTriggerType>reachPoint</wpml:actionTriggerType></wpml:actionTrigger><wpml:action><wpml:actionId>0</wpml:actionId><wpml:actionActuatorFunc>gimbalRotate</wpml:actionActuatorFunc><wpml:actionActuatorFuncParam><wpml:gimbalRotateMode>absoluteAngle</wpml:gimbalRotateMode><wpml:gimbalPitchRotateEnable>1</wpml:gimbalPitchRotateEnable><wpml:gimbalPitchRotateAngle>-90</wpml:gimbalPitchRotateAngle><wpml:gimbalRollRotateEnable>0</wpml:gimbalRollRotateEnable><wpml:gimbalRollRotateAngle>0</wpml:gimbalRollRotateAngle><wpml:gimbalYawRotateEnable>0</wpml:gimbalYawRotateEnable><wpml:gimbalYawRotateAngle>0</wpml:gimbalYawRotateAngle><wpml:gimbalRotateTimeEnable>0</wpml:gimbalRotateTimeEnable><wpml:gimbalRotateTime>0</wpml:gimbalRotateTime><wpml:payloadPositionIndex>0</wpml:payloadPositionIndex></wpml:actionActuatorFuncParam></wpml:action></wpml:actionGroup>'
    common=f'<Point><coordinates>{lo},{la}</coordinates></Point><wpml:index>{i}</wpml:index>'
    if tmpl:
        return f'<Placemark>{common}<wpml:ellipsoidHeight>{h}</wpml:ellipsoidHeight><wpml:height>{h}</wpml:height><wpml:useGlobalHeight>0</wpml:useGlobalHeight><wpml:useGlobalSpeed>0</wpml:useGlobalSpeed><wpml:waypointSpeed>{sp}</wpml:waypointSpeed><wpml:useGlobalHeadingParam>1</wpml:useGlobalHeadingParam><wpml:useGlobalTurnParam>1</wpml:useGlobalTurnParam><wpml:useStraightLine>1</wpml:useStraightLine><wpml:gimbalPitchAngle>-90</wpml:gimbalPitchAngle>{act}</Placemark>'
    return f'<Placemark>{common}<wpml:executeHeight>{h}</wpml:executeHeight><wpml:waypointSpeed>{sp}</wpml:waypointSpeed><wpml:waypointHeadingParam><wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode><wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle><wpml:waypointPoiPoint>0.000000,0.000000,0.000000</wpml:waypointPoiPoint><wpml:waypointHeadingAngleEnable>0</wpml:waypointHeadingAngleEnable><wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode></wpml:waypointHeadingParam><wpml:waypointTurnParam><wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode><wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist></wpml:waypointTurnParam><wpml:useStraightLine>1</wpml:useStraightLine><wpml:waypointGimbalHeadingParam><wpml:waypointGimbalPitchAngle>-90</wpml:waypointGimbalPitchAngle><wpml:waypointGimbalYawAngle>0</wpml:waypointGimbalYawAngle></wpml:waypointGimbalHeadingParam>{act}</Placemark>'
kml=[]
for c,P in d['plans'].items():
    for k,m in enumerate(P['missions']):
        W=m['wps']; sp=M['speed']; rth=P['rth_rel']
        tmpl=f'''<?xml version="1.0" encoding="UTF-8"?>
<kml {NS}><Document><wpml:author>Bright Tree map</wpml:author><wpml:createTime>{now}</wpml:createTime><wpml:updateTime>{now}</wpml:updateTime>{mission_cfg(rth)}<Folder><wpml:templateType>waypoint</wpml:templateType><wpml:templateId>0</wpml:templateId><wpml:waylineCoordinateSysParam><wpml:coordinateMode>WGS84</wpml:coordinateMode><wpml:heightMode>relativeToStartPoint</wpml:heightMode></wpml:waylineCoordinateSysParam><wpml:autoFlightSpeed>{sp}</wpml:autoFlightSpeed><wpml:globalHeight>{W[0]['rel']}</wpml:globalHeight><wpml:caliFlightEnable>0</wpml:caliFlightEnable><wpml:gimbalPitchMode>usePointSetting</wpml:gimbalPitchMode><wpml:globalWaypointHeadingParam><wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode><wpml:waypointHeadingAngle>0</wpml:waypointHeadingAngle><wpml:waypointPoiPoint>0.000000,0.000000,0.000000</wpml:waypointPoiPoint><wpml:waypointHeadingPathMode>followBadArc</wpml:waypointHeadingPathMode><wpml:waypointHeadingPoiIndex>0</wpml:waypointHeadingPoiIndex></wpml:globalWaypointHeadingParam><wpml:globalWaypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:globalWaypointTurnMode><wpml:globalUseStraightLine>1</wpml:globalUseStraightLine>{''.join(pm(i,w,sp,True) for i,w in enumerate(W))}</Folder></Document></kml>'''
        wl=f'''<?xml version="1.0" encoding="UTF-8"?>
<kml {NS}><Document>{mission_cfg(rth)}<Folder><wpml:templateId>0</wpml:templateId><wpml:executeHeightMode>relativeToStartPoint</wpml:executeHeightMode><wpml:waylineId>0</wpml:waylineId><wpml:distance>{int(m['km']*1000)}</wpml:distance><wpml:duration>{int(m['minutes']*60)}</wpml:duration><wpml:autoFlightSpeed>{sp}</wpml:autoFlightSpeed>{''.join(pm(i,w,sp,False) for i,w in enumerate(W))}</Folder></Document></kml>'''
        name=f'BrightTree_{c}_mission{k+1}of{len(P["missions"])}.kmz'
        with zipfile.ZipFile(os.path.join(out,name),'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('wpmz/template.kml',tmpl); z.writestr('wpmz/waylines.wpml',wl)
        coords=' '.join(f"{w['ll'][0]},{w['ll'][1]},{w['rel']+P['takeoff_elev']:.1f}" for w in W)
        col=['ff00a5ff','ff32cd32','ffff6400'][k%3]
        kml.append(f'<Placemark><name>{c} take-off · mission {k+1}</name><Style><LineStyle><color>{col}</color><width>2</width></LineStyle></Style><LineString><altitudeMode>absolute</altitudeMode><coordinates>{coords}</coordinates></LineString></Placemark>')
    lo,la=P['takeoff_ll']; kml.append(f'<Placemark><name>Take-off {c}</name><Point><coordinates>{lo},{la}</coordinates></Point></Placemark>')
open(os.path.join(out,'BrightTree_flight_plan.kml'),'w').write(f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Bright Tree mapping flights</name>{"".join(kml)}</Document></kml>')
print(sorted(os.listdir(out)))

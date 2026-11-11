/* ---- Energy tool: solar arrays, shade, SILO weather, battery and loads (Nov 2026) ----
   Method (screening, not a design certificate):
   - Shade: for sample points on each array, walk outward in 72 directions over the LiDAR ground (dem1/dem2) and the
     canopy grid (CG, 2 m). Terrain blocks fully; a crown band (0.45 h to h above its ground) lets through gp^0.35 per
     2 m crossing, as in the light planner. Result: sky transmittance T[az][alt] per array. Trees removed or thinned on
     the lop list are applied through cgAt().
   - Weather: SILO daily global radiation, max and min temperature at the property (silo_full.json).
     Daily diffuse share from Erbs et al. (1982); spread over the day with Collares-Pereira & Rabl (total) and
     Liu & Jordan (diffuse); beam on the plane x T(sun), diffuse x the plane's shaded sky view, ground reflection 0.2.
   - Power: kWp x plane irradiance/1000 x (1 + gamma (Tcell - 25)) x system derate; Tcell from NOCT. */
const EN_PANELS={
  jinko475:{label:'Jinko Tiger Neo JKM475N-60HL4 475 W',w:475,voc:43.45,isc:13.77,vmp:35.88,imp:13.24,bv:-0.25,g:-0.29,noct:45,len:1.906,wid:1.134,src:'Jinko datasheet JKM475-500N-60HL4-(V)'},
  longi425:{label:'LONGi Hi-MO 5m 54-cell 425 W (typical values: check the label)',w:425,voc:38.1,isc:14.0,vmp:32.1,imp:13.24,bv:-0.265,g:-0.34,noct:45,len:1.722,wid:1.134,src:'LONGi LR5-54 family datasheet; 425 W values estimated',check:true},
  generic440:{label:'Generic 440 W, 1.72 m (typical)',w:440,voc:39.5,isc:14.0,vmp:33.0,imp:13.33,bv:-0.25,g:-0.29,noct:45,len:1.722,wid:1.134,src:'typical 54-cell n-type',check:true}};
const EN_DEVICES={
  sig25:{label:'Sigenergy 25 kW three-phase, one input (MPPT)',vmax:1100,mppt:[160,1000],vstart:180,imax:16,iscmax:20,per:1,src:'Sigen Energy Storage System three-phase datasheet'},
  solarac:{label:'Solar AC DC hybrid air conditioner (own panels)',vmax:380,mppt:[80,380],vstart:80,imax:18,iscmax:18,per:2,src:'air-conditioner manual (from the scope draft)'},
  redearth:{label:'Red Earth BlackMax BMX-104 solar input',vmax:500,mppt:[120,450],vstart:120,imax:18,iscmax:18,per:1,src:'scope draft'}};
const EN_ARRAY_LIMIT=1000; // AS/NZS 5033:2021 domestic maximum; 600 V applies where AS/NZS 4777.1 (grid connection) applies
const EN_DEF={battery:40,reserve:10,eff:92,derate:88,albedo:0.2,trees:'today',
  loads:[['House: fridge, lights, power, internet',8,40],['Hot water (heat pump)',3,100],['Cooking (induction)',4,60],['Water pumps',2,100],['Treatment plant (aerator, UV)',2.5,50],['EV charging',8,100]]};
let ENS=Object.assign({},EN_DEF,lsGet('bt.energy',{}));let ENR=null;
function enSave(){lsSet('bt.energy',ENS);if(live&&db){clearTimeout(enSave.t);enSave.t=setTimeout(()=>db.doc(C('settings')+'/energy').set(Object.assign({},ENS,{loads:ENS.loads.map(l=>({n:l[0],k:l[1],d:l[2]})),updatedAt:new Date().toISOString()})).catch(()=>{}),800)}}
function enArrays(){const out=[];for(const [id,f] of features){if(f.kind!=='solar'||f.geom.g!=='polygon'||fHidden(f))continue;out.push([id,f])}return out}
function enPV(f){const p=Object.assign({bearing:null,tilt:20,h:1,panel:'longi425',count:0,device:'sig25',per:0,feeds:'battery'},f.pv||{});if(p.bearing==null)p.bearing=enGuessBearing(f.geom.pts);return p}
function enGuessBearing(pts){let best=0,az=0;for(let i=0;i<pts.length;i++){const a=pts[i],b=pts[(i+1)%pts.length],L=Math.hypot(b[0]-a[0],b[1]-a[1]);if(L>best){best=L;az=Math.atan2(b[0]-a[0],-(b[1]-a[1]))*180/Math.PI}}
  const c1=(az+90+360)%360,c2=(az+270)%360;const d=x=>Math.min(x,360-x);return Math.round(d(c1)<d(c2)?c1:c2)}
function enFrame(pts,bearing){const r=bearing*Math.PI/180,n=[Math.sin(r),-Math.cos(r)],a=[-n[1],n[0]];let c=[0,0];for(const p of pts){c[0]+=p[0]/pts.length;c[1]+=p[1]/pts.length}
  let a0=1e9,a1=-1e9,n0=1e9,n1=-1e9;for(const p of pts){const da=(p[0]-c[0])*a[0]+(p[1]-c[1])*a[1],dn=(p[0]-c[0])*n[0]+(p[1]-c[1])*n[1];a0=Math.min(a0,da);a1=Math.max(a1,da);n0=Math.min(n0,dn);n1=Math.max(n1,dn)}
  return {c,a,n,L:a1-a0,D:n1-n0,a0,a1,n0,n1}}
function enPack(f,p){const fr=enFrame(f.geom.pts,p.bearing),P=EN_PANELS[p.panel]||EN_PANELS.longi425,m=p.edge??0.3,g=0.02,S=fr.D/Math.cos(p.tilt*Math.PI/180);
  const fit=(w,l)=>{const cols=Math.floor((fr.L-2*m+g)/(w+g)),rows=Math.floor((S-2*m+g)/(l+g));return {cols:Math.max(0,cols),rows:Math.max(0,rows),n:Math.max(0,cols)*Math.max(0,rows)}};
  const po=fit(P.wid,P.len),la=fit(P.len,P.wid);return {L:fr.L,S,portrait:po,landscape:la,best:po.n>=la.n?['portrait',po]:['landscape',la]}}
function enStrings(p){const P=EN_PANELS[p.panel]||EN_PANELS.longi425,D=EN_DEVICES[p.device]||EN_DEVICES.sig25,n=p.count||0,per=p.per||n,strings=per?Math.ceil(n/per):0;
  const tmin=enTmin(),vocC=per*P.voc*(1+P.bv/100*(tmin-25)),vmpH=per*P.vmp*(1+P.bv/100*(70-25)),par=strings,isc=P.isc*Math.min(par,D.per),imp=P.imp*Math.min(par,D.per),inputs=Math.ceil(strings/D.per);
  const fl=[];if(n%(per||1))fl.push(['warn',`${n} panels do not split evenly into strings of ${per}`]);
  if(vocC>D.vmax)fl.push(['bad',`Cold open-circuit voltage ${vocC.toFixed(0)} V is over the ${D.vmax} V input limit`]);else fl.push(['ok',`Cold open-circuit ${vocC.toFixed(0)} V at ${tmin.toFixed(1)} °C (limit ${D.vmax} V)`]);
  if(vocC>EN_ARRAY_LIMIT)fl.push(['bad',`Over the ${EN_ARRAY_LIMIT} V domestic array limit (AS/NZS 5033)`]);else if(vocC>600)fl.push(['warn','Over 600 V: allowed off-grid, but AS/NZS 4777.1 limits grid-connected domestic arrays to 600 V']);
  if(vmpH<D.mppt[0]||vmpH<D.vstart)fl.push(['bad',`Hot working voltage ${vmpH.toFixed(0)} V is below the input's ${Math.max(D.mppt[0],D.vstart)} V start/tracking floor: string too short`]);else fl.push(['ok',`Hot working voltage ${vmpH.toFixed(0)} V (tracks from ${D.mppt[0]} V)`]);
  if(per*P.vmp>D.mppt[1])fl.push(['warn',`Working voltage ${(per*P.vmp).toFixed(0)} V is above the ${D.mppt[1]} V tracking range`]);
  if(imp>D.imax)fl.push(['warn',`Working current ${imp.toFixed(1)} A is over the ${D.imax} A input limit (the inverter clips it)`]);
  if(isc>D.iscmax)fl.push(['bad',`Short-circuit current ${isc.toFixed(1)} A is over the ${D.iscmax} A input limit`]);else fl.push(['ok',`Short-circuit ${isc.toFixed(1)} A (limit ${D.iscmax} A)`]);
  if(D.per===1&&strings>1)fl.push(['ok',`${strings} strings need ${inputs} inputs (one string per input)`]);
  return {strings,per,vocC,vmpH,isc,inputs,fl}}
function enTmin(){if(!SFULL)return 0;let m=99;for(const v of SFULL.tmin10)if(v>-900&&v/10<m)m=v/10;return m}
/* sample points on the array plane, with their elevation */
function enSamples(f,p){const fr=enFrame(f.geom.pts,p.bearing),zc=zAt(fr.c[0],fr.c[1])+p.h,tn=Math.tan(p.tilt*Math.PI/180),out=[];
  for(const u of [-.33,0,.33])for(const v of [-.3,0,.3]){const da=(fr.a0+fr.a1)/2+u*fr.L,dn=(fr.n0+fr.n1)/2+v*fr.D,x=fr.c[0]+fr.a[0]*da+fr.n[0]*dn,y=fr.c[1]+fr.a[1]*da+fr.n[1]*dn;
    out.push([x,y,zc-dn*tn])}return out}
const EN_AZ=72,EN_ALT=46,EN_TAN=Array.from({length:EN_ALT},(_,k)=>Math.tan(Math.min(89.5,k*2+1)*Math.PI/180));
/* transmittance of the sky from one point in one azimuth bin: Float32Array(EN_ALT) */
function enRay(x,y,z0,azb,edits,d0){const T=new Float32Array(EN_ALT).fill(1),az=(azb*5+2.5)*Math.PI/180,dx=Math.sin(az),dy=-Math.cos(az);
  for(let d=d0;d<1000;d+=2){const qx=x+dx*d,qy=y+dy*d,zt=zAt(qx,qy);if(!isFinite(zt))break;const tt=(zt-z0)/d;if(tt<-0.2&&d>200)break;
    for(let k=0;k<EN_ALT&&EN_TAN[k]<=tt;k++)T[k]=0;
    const [h,gp]=cgAt(qx,qy,edits);if(h>2){const t1=(zt+0.45*h-z0)/d,t2=(zt+h-z0)/d,tr=Math.pow(Math.max(gp,0.02),0.35);for(let k=0;k<EN_ALT;k++){const t=EN_TAN[k];if(t>t2)break;if(t>t1)T[k]*=tr}}
    if((zt+60-z0)/d<EN_TAN[0])break}
  return T}
function enShade(f,p,edits){const S=enSamples(f,p),rays=S.map(s=>{const r=[];for(let b=0;b<EN_AZ;b++)r.push(enRay(s[0],s[1],s[2],b,edits,3));return r});return enShadeFrom(rays,p)}
function enShadeFrom(rays,p){const T=Array.from({length:EN_AZ},()=>new Float32Array(EN_ALT));for(const r of rays)for(let b=0;b<EN_AZ;b++)for(let k=0;k<EN_ALT;k++)T[b][k]+=r[b][k]/rays.length;
  /* sky view of the tilted plane: isotropic sky weighted by incidence */
  const bt=p.tilt*Math.PI/180,pa=p.bearing*Math.PI/180;let sv=0,s0=0;for(let b=0;b<EN_AZ;b++){const az=(b*5+2.5)*Math.PI/180;for(let k=0;k<EN_ALT;k++){const al=Math.min(89.5,k*2+1)*Math.PI/180,ci=Math.sin(al)*Math.cos(bt)+Math.cos(al)*Math.sin(bt)*Math.cos(az-pa);if(ci<=0)continue;const w=ci*Math.cos(al);s0+=w;sv+=w*T[b][k]}}
  return {T,rays,svf:s0?sv/s0:1}}
function enTAt(T,az,alt){const b=Math.floor(((az%360)+360)%360/5)%EN_AZ,k=Math.min(EN_ALT-1,Math.max(0,Math.round((alt-1)/2)));return T[b][k]}
/* daily kWh per kWp for every SILO day, with or without shade */
function enDays(p,sh,opt){const n=SFULL.rad10.length,out=new Float32Array(n),phi=LAT*Math.PI/180,bt=p.tilt*Math.PI/180,pa=p.bearing*Math.PI/180,P=EN_PANELS[p.panel]||EN_PANELS.longi425,der=(opt.derate||88)/100,alb=opt.albedo||0.2;
  const t0=Date.parse(SFULL.start+'T00:00:00Z');const svf=sh?sh.svf:1;
  for(let i=0;i<n;i++){let H=SFULL.rad10[i]/10;if(!(H>=0)){out[i]=NaN;continue}const dt=new Date(t0+i*864e5),doy=Math.floor((dt-Date.UTC(dt.getUTCFullYear(),0,0))/864e5);
    const dec=23.45*Math.PI/180*Math.sin(2*Math.PI*(284+doy)/365),ws=Math.acos(Math.max(-1,Math.min(1,-Math.tan(phi)*Math.tan(dec)))),E0=1+0.033*Math.cos(2*Math.PI*doy/365);
    const H0=24*3600*1367/Math.PI*E0*(Math.cos(phi)*Math.cos(dec)*Math.sin(ws)+ws*Math.sin(phi)*Math.sin(dec))/1e6;const KT=Math.min(1,H/H0),wsd=ws*180/Math.PI;
    const fd=wsd<=81.4?(KT<0.715?1-0.2727*KT+2.4495*KT*KT-11.9514*KT**3+9.3879*KT**4:0.143):(KT<0.722?1+0.2832*KT-2.5557*KT*KT+0.8448*KT**3:0.175);
    const Hk=H/3.6,Hd=Hk*fd,tx=(SFULL.tmax10[i]>-900?SFULL.tmax10[i]:250)/10,tm=(SFULL.tmin10[i]>-900?SFULL.tmin10[i]:150)/10;
    const a=0.409+0.5016*Math.sin(ws-Math.PI/3),b=0.6609-0.4767*Math.sin(ws-Math.PI/3),den=Math.sin(ws)-ws*Math.cos(ws);let e=0;
    for(let s=0;s<48;s++){const t=(s+0.5)/2,w=(t-12)*15*Math.PI/180;if(Math.abs(w)>=ws)continue;
      const rd=Math.PI/24*(Math.cos(w)-Math.cos(ws))/den,rt=rd*(a+b*Math.cos(w)),I=rt*Hk,Id=Math.min(I,rd*Hd),Ib=I-Id;
      const sa=Math.sin(phi)*Math.sin(dec)+Math.cos(phi)*Math.cos(dec)*Math.cos(w);if(sa<=0)continue;const alt=Math.asin(sa),ca=Math.cos(alt);
      const az=Math.atan2(-Math.sin(w)*Math.cos(dec),Math.cos(phi)*Math.sin(dec)-Math.sin(phi)*Math.cos(dec)*Math.cos(w));
      const ci=sa*Math.cos(bt)+ca*Math.sin(bt)*Math.cos(az-pa);let beam=0;if(alt>3*Math.PI/180&&ci>0){beam=Ib*Math.min(ci/sa,6);if(sh)beam*=enTAt(sh.T,az*180/Math.PI,alt*180/Math.PI)}
      const G=beam+Id*svf*(1+Math.cos(bt))/2+I*alb*(1-Math.cos(bt))/2; // kWh/m2 in this hour
      const Ta=t<6?tm:t<15?tm+(tx-tm)*(1-Math.cos(Math.PI*(t-6)/9))/2:tm+(tx-tm)*(1+Math.cos(Math.PI*(t-15)/9))/2,Tc=Ta+G*1000*(P.noct-20)/800;
      e+=G*(1+P.g/100*(Tc-25))*0.5}
    out[i]=e*der}
  return out}
function enKW(p){const P=EN_PANELS[p.panel]||EN_PANELS.longi425;return (p.count||0)*P.w/1000}
/* statistics over every day on record */
function enStats(day){const t0=Date.parse(SFULL.start+'T00:00:00Z'),n=day.length,mon=Array.from({length:12},()=>[0,0]),yr={},ym={};let tot=0,cnt=0;const rain=SFULL.rain10;
  for(let i=0;i<n;i++){const v=day[i];if(!isFinite(v))continue;const d=new Date(t0+i*864e5),m=d.getUTCMonth(),y=d.getUTCFullYear();mon[m][0]+=v;mon[m][1]++;tot+=v;cnt++;(yr[y]=yr[y]||[0,0,0])[0]+=v;yr[y][1]++;yr[y][2]+=(rain[i]>0?rain[i]/10:0);const k=y*12+m;(ym[k]=ym[k]||[0,0])[0]+=v;ym[k][1]++}
  const full=Object.entries(yr).filter(([y,a])=>a[1]>=365).map(([y,a])=>({y:+y,kwh:a[0],day:a[0]/a[1],rain:a[2]}));
  const months=Object.entries(ym).filter(([k,a])=>a[1]>=28).map(([k,a])=>({y:Math.floor(k/12),m:k%12,day:a[0]/a[1]})).sort((p,q)=>p.day-q.day);
  const p10=months[Math.floor(months.length*0.1)];const run=L=>{let best=1e9,at=0,s=0;for(let i=0;i<n;i++){s+=isFinite(day[i])?day[i]:0;if(i>=L)s-=isFinite(day[i-L])?day[i-L]:0;if(i>=L-1&&s<best){best=s;at=i-L+1}}return {mean:best/L,from:new Date(t0+at*864e5),L}};
  const lowIn=(ms,filt)=>{let b=1e9,at=-1;for(let i=0;i<n;i++){const d=new Date(t0+i*864e5);if(!ms.includes(d.getUTCMonth())||!isFinite(day[i])||(filt&&!filt(d)))continue;if(day[i]<b){b=day[i];at=i}}return at<0?null:{v:b,d:new Date(t0+at*864e5),rain:rain[at]/10}};
  /* wettest summer (Dec-Feb) */const sr={};for(let i=0;i<n;i++){const d=new Date(t0+i*864e5),m=d.getUTCMonth();if(m===11||m<2){const s=m===11?d.getUTCFullYear()+1:d.getUTCFullYear();sr[s]=(sr[s]||0)+Math.max(0,rain[i]/10)}}
  const wetS=+Object.entries(sr).sort((a,b)=>b[1]-a[1])[0][0];
  const dry=full.slice().sort((a,b)=>a.rain-b.rain)[0],wet=full.slice().sort((a,b)=>b.rain-a.rain)[0],lowY=full.slice().sort((a,b)=>a.day-b.day)[0],hiY=full.slice().sort((a,b)=>b.day-a.day)[0];
  return {mean:tot/cnt,annual:tot/cnt*365.25,mon:mon.map(a=>a[0]/a[1]),dry,wet,lowY,hiY,p10,worstMonth:months[0],r3:run(3),r7:run(7),r14:run(14),winter:lowIn([5,6,7]),summer:lowIn([11,0,1]),wetSummer:lowIn([11,0,1],d=>{const m=d.getUTCMonth();return (m===11?d.getUTCFullYear()+1:d.getUTCFullYear())===wetS}),wetS,years:full.length,from:SFULL.start,to:SFULL.end}}
/* battery: every day on record; load split into daytime (served first from the sun) and night */
function enBattery(gen,o){const cap=o.battery*(1-o.reserve/100),ef=Math.sqrt(o.eff/100),L=o.loads.reduce((s,l)=>s+(+l[1]||0),0),Ld=o.loads.reduce((s,l)=>s+(+l[1]||0)*(+l[2]||0)/100,0),Ln=L-Ld;
  const sim=m=>{let soc=cap,flat=0,un=0,worst=0,runs=[],cur=0,curun=0,days=0;for(let i=0;i<gen.length;i++){const g=gen[i];if(!isFinite(g))continue;days++;let u=0;let net=g*m-Ld;
      if(net>=0)soc=Math.min(cap,soc+net*ef);else{const need=-net/ef;if(need<=soc)soc-=need;else{u+=(need-soc)*ef;soc=0}}
      const nn=Ln/ef;if(nn<=soc)soc-=nn;else{u+=(nn-soc)*ef;soc=0}
      if(u>0.01){flat++;un+=u;worst=Math.max(worst,u);cur++;curun+=u}else if(cur){runs.push([cur,curun]);cur=0;curun=0}}
    if(cur)runs.push([cur,curun]);return {flat,un,worst,runs,days}};
  const base=sim(1),need=lim=>{let lo=1,hi=1;if(base.flat<=lim)return 1;hi=1.5;while(sim(hi).flat>lim&&hi<12)hi*=1.5;for(let k=0;k<16;k++){const mid=(lo+hi)/2;if(sim(mid).flat>lim)lo=mid;else hi=mid}return hi};
  return Object.assign(base,{need1:need(base.days/365.25),L,Ld,Ln,cap,needMult:need(0),years:base.days/365.25,longest:base.runs.reduce((m,r)=>Math.max(m,r[0]),0)})}
/* trees that cost the most energy: canopy tops within 70 m of the arrays; each removed in turn (crown circle) */
function enTreeCands(arrs){const seen=[],c=[];if(!CG)return c;for(const a of arrs){const fr=enFrame(a.f.geom.pts,a.p.bearing);for(let j=-35;j<=35;j++)for(let i=-35;i<=35;i++){const x=fr.c[0]+i*2,y=fr.c[1]+j*2,d=Math.hypot(i*2,j*2);if(d>70||d<4)continue;const ix=Math.floor(x/2),iy=Math.floor(y/2),h=CG.h[iy*CG.w+ix];if(!(h>10))continue;
    let mx=true;for(let v=-2;v<=2&&mx;v++)for(let u=-2;u<=2;u++){if(!u&&!v)continue;if(CG.h[(iy+v)*CG.w+ix+u]>h){mx=false;break}}if(!mx)continue;if(seen.some(s=>Math.hypot(s[0]-x,s[1]-y)<4))continue;seen.push([x,y]);c.push({x:ix*2+1,y:iy*2+1,h,r:Math.max(3,Math.min(8,0.18*h+1))})}}return c}
function enTreeGain(arrs,cands,edits,opt){const res=[];for(const t of cands){let gain=0;const e=edits.concat([{x:t.x,y:t.y,r:t.r,mode:'remove'}]);
    for(const a of arrs){if(!a.batt&&!opt.all)continue;const S=enSamples(a.f,a.p);let changed=false;const rays=a.sh.rays.map((r,si)=>{const s=S[si],d=Math.hypot(t.x-s[0],t.y-s[1]);if(d<3||d>1000)return r;const brg=(Math.atan2(t.x-s[0],-(t.y-s[1]))*180/Math.PI+360)%360,half=Math.asin(Math.min(1,t.r/d))*180/Math.PI+2.5;const nr=r.slice();
      for(let b=0;b<EN_AZ;b++){const mid=b*5+2.5;let dd=Math.abs(mid-brg);dd=Math.min(dd,360-dd);if(dd<=half){nr[b]=enRay(s[0],s[1],s[2],b,e,3);changed=true}}return nr});
      if(!changed)continue;const sh=enShadeFrom(rays,a.p);const d2=enDays(a.p,sh,opt);let s=0,s0=0;for(let i=0;i<d2.length;i++){if(isFinite(d2[i])){s+=d2[i];s0+=a.day1[i]}}gain+=(s-s0)/a.yrs*a.kw}
    res.push(Object.assign({gain},t))}return res.sort((p,q)=>q.gain-p.gain)}
async function enRun(withTrees){if(!SFULL){toast('This site has no SILO daily weather yet.');return}await loadCG();const A=enArrays();if(!A.length){toast('Draw a solar array first (Draw tab, Solar array), or add the house test arrays.');return}
  const J=typeof lopJobs==='function'?lopJobs():{done:[],plan:[]},edits=ENS.trees==='survey'?[]:ENS.trees==='planned'?J.done.concat(J.plan):J.done;
  const opt={derate:ENS.derate,albedo:ENS.albedo};const st=$('#enStat');const say=t=>{if(st)st.textContent=t};const arrs=[];
  for(const [id,f] of A){say('Shade for '+(f.name||'array')+'…');await new Promise(r=>setTimeout(r,20));const p=enPV(f),kw=enKW(p);const sh=enShade(f,p,edits);const day1=enDays(p,sh,opt),day0=enDays(p,null,opt);
    let s1=0,s0=0,j1=0,j0=0;const t0=Date.parse(SFULL.start+'T00:00:00Z');for(let i=0;i<day1.length;i++){if(!isFinite(day1[i]))continue;s1+=day1[i];s0+=day0[i];if(new Date(t0+i*864e5).getUTCMonth()===5){j1+=day1[i];j0+=day0[i]}}
    const yrs=day1.filter(isFinite).length/365.25;arrs.push({id,f,p,kw,sh,day1,yrs,batt:p.feeds!=='own',str:enStrings(p),pack:enPack(f,p),loss:1-s1/s0,lossJun:1-j1/j0,yieldKw:s1/yrs/365.25,stats:null})}
  for(const a of arrs){const d=new Float32Array(a.day1.length);for(let i=0;i<d.length;i++)d[i]=a.day1[i]*a.kw;a.kwh=d;a.stats=enStats(d)}
  const tot=new Float32Array(arrs[0].kwh.length);for(const a of arrs)if(a.batt)for(let i=0;i<tot.length;i++)tot[i]+=a.kwh[i];
  const S=enStats(tot),B=enBattery(tot,ENS);let trees=null;
  if(withTrees){say('Testing which trees cost the most energy…');await new Promise(r=>setTimeout(r,20));const c=enTreeCands(arrs.filter(a=>a.batt)).filter(t=>!edits.some(e=>Math.hypot(e.x-t.x,e.y-t.y)<e.r));trees=enTreeGain(arrs,c,edits,opt).slice(0,10)}
  ENR={arrs,tot,S,B,trees,edits:edits.length,treesMode:ENS.trees,at:new Date()};say('');const el=$('#enRes');if(el)el.innerHTML=enResHTML();wireEnergyRes();draw()}
function enBars(vals,load,w=300,h=120,cols){const mx=Math.max(...vals.flat(),load||0)*1.1||1,bw=w/12,mm='JFMAMJJASOND';let s=`<svg viewBox="0 0 ${w} ${h+16}" width="100%" style="max-width:520px;display:block" role="img" aria-label="Monthly kWh per day">`;
  for(let m=0;m<12;m++){let y=h;const st=Array.isArray(vals[m])?vals[m]:[vals[m]];st.forEach((v,k)=>{const bh=v/mx*h;s+=`<rect x="${m*bw+2}" y="${y-bh}" width="${bw-4}" height="${bh}" fill="${(cols||['#3a5a8c','#7fa3d6','#b9cbe8'])[k%3]}"/>`;y-=bh});s+=`<text x="${m*bw+bw/2}" y="${h+12}" font-size="9" text-anchor="middle" fill="currentColor">${mm[m]}</text>`}
  if(load){const y=h-load/mx*h;s+=`<line x1="0" x2="${w}" y1="${y}" y2="${y}" stroke="#c0392b" stroke-dasharray="4 3"/><text x="${w-2}" y="${y-3}" font-size="9" text-anchor="end" fill="#c0392b">load ${load.toFixed(0)} kWh/day</text>`}
  return s+'</svg>'}
const enD=d=>d?d.toISOString().slice(0,10):'–',enF=(v,k=1)=>isFinite(v)?(+v).toFixed(k):'–';
function enResHTML(){const R=ENR;if(!R)return '';const S=R.S,B=R.B,mn='Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
  const rows=R.arrs.map(a=>`<tr><td>${esc(a.f.name||'Array')}${a.batt?'':' <span class="hint">(own load)</span>'}</td><td>${a.kw.toFixed(1)}</td><td>${a.p.bearing}° / ${a.p.tilt}°</td><td>${enF(a.stats.mean)}</td><td>${enF(a.yieldKw,2)}</td><td>${Math.round(a.loss*100)}% · ${Math.round(a.lossJun*100)}%</td><td>${Math.round(a.sh.svf*100)}%</td></tr>`).join('');
  const wc=[['Average day (all years)',S.mean],[`Lowest year (${S.lowY.y})`,S.lowY.day],[`Driest year (${S.dry.y}, ${Math.round(S.dry.rain)} mm)`,S.dry.day],[`Wettest year (${S.wet.y}, ${Math.round(S.wet.rain)} mm)`,S.wet.day],[`10th-percentile month (${mn[S.p10.m]} ${S.p10.y})`,S.p10.day],[`Worst month (${mn[S.worstMonth.m]} ${S.worstMonth.y})`,S.worstMonth.day],[`Worst 3 days (from ${enD(S.r3.from)})`,S.r3.mean],[`Worst 7 days (from ${enD(S.r7.from)})`,S.r7.mean],[`Worst 14 days (from ${enD(S.r14.from)})`,S.r14.mean],[`Lowest winter day (${enD(S.winter&&S.winter.d)})`,S.winter&&S.winter.v],[`Lowest day, wettest summer ${S.wetS-1}–${String(S.wetS).slice(2)} (${enD(S.wetSummer&&S.wetSummer.d)}, ${S.wetSummer?Math.round(S.wetSummer.rain):0} mm rain)`,S.wetSummer&&S.wetSummer.v]];
  const runs=B.runs.slice().sort((a,b)=>b[0]-a[0]).slice(0,3);
  return `<p><b>${enF(S.mean)} kWh a day</b> on average into the battery system (${Math.round(S.annual).toLocaleString()} kWh a year), from ${R.arrs.filter(a=>a.batt).reduce((s,a)=>s+a.kw,0).toFixed(1)} kW. ${R.treesMode==='survey'?'Trees as in the 2022 survey.':R.treesMode==='planned'?`Trees: 2022 survey minus ${R.edits} removed or planned lopping jobs.`:`Trees: 2022 survey minus ${R.edits} removed since.`}</p>
  <table class="mini"><tr><th>Array</th><th>kW</th><th>Faces / pitch</th><th>kWh/day</th><th>per kW</th><th>Shade loss year · June</th><th>Sky seen</th></tr>${rows}</table>
  <div style="margin:6px 0">${enBars(S.mon.map((v,m)=>R.arrs.filter(a=>a.batt).map(a=>a.stats.mon[m])),B.L)}</div><p class="hint">Average kWh a day each month, one colour per array; the dashed line is your daily load.</p>
  <b>Worst cases (${S.from.slice(0,4)}–${S.to.slice(0,4)}, SILO)</b><table class="mini">${wc.map(([k,v])=>`<tr><td>${k}</td><td><b>${enF(v)}</b> kWh/day</td></tr>`).join('')}</table>
  <b>Battery (${ENS.battery} kWh, ${ENS.reserve}% kept in reserve)</b><p>Daily load ${B.L.toFixed(1)} kWh (${B.Ld.toFixed(1)} in daylight, ${B.Ln.toFixed(1)} at night). Over ${Math.round(B.years)} years the battery runs flat on <b>${B.flat} days</b> (${(B.flat/B.years).toFixed(1)} a year)${B.flat?`, the longest run ${B.longest} day${B.longest===1?'':'s'}; short ${Math.round(B.un/B.years)} kWh a year, worst day ${B.worst.toFixed(1)} kWh`:''}.</p>
  ${B.flat?`<p>To avoid it: a generator covering about ${Math.round(B.un/B.years)} kWh a year (worst day ${B.worst.toFixed(0)} kWh, e.g. ${Math.max(2,Math.ceil(B.worst/5))} kW for 5 hours), or more panels shaded like these: about <b>${((B.need1-1)*R.arrs.filter(a=>a.batt).reduce((s,a)=>s+a.kw,0)).toFixed(1)} kW more</b> to get down to one flat day a year, ${B.needMult>=12?'and more than 11 times the panels':'and '+((B.needMult-1)*R.arrs.filter(a=>a.batt).reduce((s,a)=>s+a.kw,0)).toFixed(0)+' kW more'} to never run flat (the long wet spells decide that, so a generator is the cheaper cover). Longest flat spells: ${runs.map(r=>`${r[0]} day${r[0]>1?'s':''}`).join(', ')}.</p>`:''}
  ${R.trees?`<b>Trees that cost the most energy</b><table class="mini"><tr><th>Tree</th><th>Height</th><th>From the roof</th><th>Gain if removed</th><th></th></tr>${R.trees.filter(t=>t.gain>20).slice(0,6).map((t,k)=>{const a=R.arrs[0].f.geom.pts,c=enFrame(a,R.arrs[0].p.bearing).c;return `<tr><td>T${k+1}</td><td>${Math.round(t.h)} m</td><td>${Math.round(Math.hypot(t.x-c[0],t.y-c[1]))} m ${['N','NE','E','SE','S','SW','W','NW'][Math.round(((Math.atan2(t.x-c[0],-(t.y-c[1]))*180/Math.PI+360)%360)/45)%8]}</td><td><b>${Math.round(t.gain)}</b> kWh/yr</td><td><button class="btn" data-enlop="${k}">Add to lop list</button></td></tr>`}).join('')||'<tr><td colspan="5">No single tree is worth more than 20 kWh a year.</td></tr>'}</table>`:''}
  <div class="row" style="margin-top:8px"><button class="btn primary" id="enReport">One-page report</button><button class="btn" id="enCsv">Daily kWh (CSV)</button></div>
  <p class="hint">Screening estimate. Shade from the 2022 LiDAR with trees on the lop list applied; crowns let some light through, terrain blocks it. Weather: SILO daily radiation and temperature at the property; diffuse split from Erbs et al. (1982). System losses ${ENS.derate}% kept (soiling, wiring, mismatch, inverter); partial shade on part of a string can cost more than this shows.</p>`}
function wireEnergyRes(){const el=$('#enRes');if(!el)return;el.querySelectorAll('[data-enlop]').forEach(b=>b.onclick=()=>{const t=ENR.trees[+b.dataset.enlop];lopAddJob({x:+t.x.toFixed(1),y:+t.y.toFixed(1),r:t.r,mode:'remove'},{name:`Tree for the solar roof (${Math.round(t.gain)} kWh/yr)`,stage:'now',status:'idea',notes:`Energy tool, ${new Date().toISOString().slice(0,10)}: about ${Math.round(t.h)} m tall; removing it adds about ${Math.round(t.gain)} kWh a year to the solar arrays.`});toast('Added to the lop list as an idea.')});
  const r=$('#enReport');if(r)r.onclick=enReport;const c=$('#enCsv');if(c)c.onclick=()=>{const t0=Date.parse(SFULL.start+'T00:00:00Z');let s='date,'+ENR.arrs.map(a=>'"'+(a.f.name||'array').replace(/"/g,'')+' kWh"').join(',')+',battery system kWh,rain mm\n';for(let i=0;i<ENR.tot.length;i++)s+=new Date(t0+i*864e5).toISOString().slice(0,10)+','+ENR.arrs.map(a=>enF(a.kwh[i],2)).join(',')+','+enF(ENR.tot[i],2)+','+(SFULL.rain10[i]/10)+'\n';enDownload(s,`energy-${SITEID}-daily.csv`,'text/csv')}}
function enReportHTML(){const R=ENR;const box=$('#enRes');const body=box?box.innerHTML:enResHTML();return `<div class="enrep"><h1>${esc(SITEDEF.name)}: solar, battery and loads</h1><p class="hint">Design Map energy tool · computed ${R.at.toLocaleDateString('en-CA')} · SILO ${R.S.from.slice(0,4)}–${R.S.to.slice(0,4)} · Queensland LiDAR 2022 canopy and ground</p>
  <table class="mini"><tr><th>Array</th><th>Panels</th><th>Strings</th><th>Checks</th></tr>${R.arrs.map(a=>`<tr><td>${esc(a.f.name||'Array')}</td><td>${a.p.count} × ${esc((EN_PANELS[a.p.panel]||{}).label||'')} (${a.kw.toFixed(2)} kW); fits ${a.pack.best[1].n} (${a.pack.best[0]})</td><td>${a.str.strings} × ${a.str.per} on ${esc((EN_DEVICES[a.p.device]||{}).label||'')}</td><td>${a.str.fl.filter(f=>f[0]!=='ok').map(f=>f[1]).join('; ')||'All within limits'}</td></tr>`).join('')}</table>${body.replace(/<div class="row" style="margin-top:8px">[\s\S]*?<\/div>/,'').replace(/<button[^>]*>[^<]*<\/button>/g,'')}</div>`}
function enReport(){let m=$('#enModal');if(!m){m=document.createElement('div');m.id='enModal';document.body.appendChild(m)}
  m.innerHTML=`<div class="enbar"><button class="btn primary" id="enPrint">Print or save as PDF</button><button class="btn" id="enClose">Close</button></div>${enReportHTML()}`;m.hidden=false;document.body.classList.add('enprint');
  $('#enClose').onclick=()=>{m.hidden=true;document.body.classList.remove('enprint')};$('#enPrint').onclick=()=>window.print()}
function energyHTML(){if(!SFULL)return '<p class="hint">Needs the SILO daily weather for this site (radiation and temperature). Ask Claude to fetch it.</p>';const A=enArrays();
  const card=([id,f])=>{const p=enPV(f),pk=enPack(f,p),st=enStrings(p),kw=enKW(p),o=(k,list,v)=>`<select data-enf="${id}" data-k="${k}" style="max-width:100%">${Object.entries(list).map(([a,b])=>`<option value="${a}" ${a===v?'selected':''}>${esc(b.label||b)}</option>`).join('')}</select>`,
      num=(k,l,v,step,t)=>`<label class="enfl" ${t?`title="${t}"`:''}><span>${l}</span><input type="number" ${step?`step="${step}"`:''} data-enf="${id}" data-k="${k}" value="${v}"></label>`;
    return `<div class="encard"><b>${esc(f.name||'Solar array')}</b> · ${kw.toFixed(2)} kW
    <div class="enrow">${num('bearing','Faces °',p.bearing)}${num('tilt','Pitch °',p.tilt)}${num('h','Height m',p.h,0.1,'Height of the middle of the panels above the ground directly below')}${num('count','Panels',p.count)}${num('per','Per string',p.per||p.count)}${num('edge','Edge m',p.edge??0.3,0.05,'Clear edge kept around the panels')}</div>
    <div class="enrow"><label class="enfl wide"><span>Panel</span>${o('panel',EN_PANELS,p.panel)}</label><label class="enfl wide"><span>Into</span>${o('device',EN_DEVICES,p.device)}</label><label class="enfl wide"><span>Feeds</span>${o('feeds',{battery:{label:'the battery system'},own:{label:'its own load only (e.g. air con)'}},p.feeds)}</label></div>
    <p class="hint">Fits ${pk.best[1].n} panels ${pk.best[0]} (${pk.best[1].cols} × ${pk.best[1].rows}) on ${pk.L.toFixed(1)} × ${pk.S.toFixed(1)} m of slope, ${p.edge??0.3} m edges${p.count>pk.best[1].n?` <b style="color:#b3261e">· ${p.count} will not fit</b>`:''}.${(EN_PANELS[p.panel]||{}).check?' Panel values are typical: check the label.':''}</p>
    <ul class="hint" style="margin:2px 0 0 16px;padding:0">${st.fl.map(([k,t])=>`<li style="color:${k==='bad'?'#b3261e':k==='warn'?'#9a6700':'inherit'}">${t}</li>`).join('')}</ul></div>`};
  return `<p class="hint">Draw each roof face or ground array as a <b>Solar array</b> (Draw tab), then set where it faces, its pitch and panels here. The tool traces tree and terrain shade from the LiDAR, runs every day of SILO weather since ${SFULL.start.slice(0,4)}, and tests your battery against your loads.</p>
   <div class="row"><button class="btn" id="enDraw">Draw a solar array</button>${SITEID==='bright-tree'&&!A.some(([i,f])=>/house/i.test(f.name||''))?'<button class="btn" id="enHouse">Add the house roof faces (test)</button>':''}</div>
   ${A.map(card).join('')||'<p class="hint">No solar arrays drawn yet.</p>'}
   <details class="mini" open><summary>Loads and battery</summary><table class="mini"><tr><th>Load</th><th>kWh/day</th><th>% in daylight</th><th></th></tr>${ENS.loads.map((l,k)=>`<tr><td><input data-enl="${k}" data-i="0" value="${esc(l[0])}"></td><td><input type="number" step="0.1" data-enl="${k}" data-i="1" value="${l[1]}" style="width:60px"></td><td><input type="number" data-enl="${k}" data-i="2" value="${l[2]}" style="width:50px"></td><td><button class="btn" data-endel="${k}" title="Remove">×</button></td></tr>`).join('')}</table>
   <div class="row"><button class="btn" id="enAddLoad">Add a load</button><label>Battery kWh</label><input type="number" id="enBat" value="${ENS.battery}" style="width:60px"><label>Reserve %</label><input type="number" id="enRes0" value="${ENS.reserve}" style="width:50px"></div>
   <div class="row"><label>Trees</label>${segHTML('enTrees',[['survey','2022 survey'],['today','Today (removed trees gone)'],['planned','With planned lopping']],ENS.trees)}</div>
   <div class="row"><label>System losses kept %</label><input type="number" id="enDer" value="${ENS.derate}" style="width:55px"></div></details>
   <div class="row" style="margin-top:6px"><button class="btn primary" id="enRun">Work it out</button><button class="btn" id="enRunT">…and find the costly trees</button><span id="enStat" class="hint"></span></div>
   <div id="enRes">${ENR?enResHTML():''}</div>`}
function wireEnergy(el){const q=s=>el.querySelector(s);if(!q('#enRun'))return;
  el.querySelectorAll('[data-enf]').forEach(i=>i.onchange=()=>{const id=i.dataset.enf,f=features.get(id);if(!f)return;const p=enPV(f);const k=i.dataset.k;p[k]=['panel','device','feeds'].includes(k)?i.value:+i.value;saveFields(id,{pv:p})});
  el.querySelectorAll('[data-enl]').forEach(i=>i.onchange=()=>{const k=+i.dataset.enl,j=+i.dataset.i;ENS.loads[k][j]=j?+i.value:i.value;enSave()});
  el.querySelectorAll('[data-endel]').forEach(b=>b.onclick=()=>{ENS.loads.splice(+b.dataset.endel,1);enSave();renderTools()});
  const n=(id,k)=>{const i=q(id);if(i)i.onchange=()=>{ENS[k]=+i.value;enSave()}};n('#enBat','battery');n('#enRes0','reserve');n('#enDer','derate');
  q('#enAddLoad').onclick=()=>{ENS.loads.push(['New load',1,50]);enSave();renderTools()};
  el.querySelectorAll('#enTrees button').forEach(b=>b.onclick=()=>{ENS.trees=b.dataset.v;enSave();renderTools()});
  q('#enRun').onclick=()=>enRun(false);q('#enRunT').onclick=()=>enRun(true);q('#enDraw').onclick=()=>{showTab('draw');startTool('solar')};
  const h=q('#enHouse');if(h)h.onclick=enAddHouse;wireEnergyRes()}
async function enAddHouse(){const H=[['House roof: front main plane (test)',[[899.37,934.89],[907.37,944.76],[910.73,942.03],[902.74,932.17]],{bearing:50,tilt:23,h:7.1,panel:'jinko475',count:20,device:'sig25',per:20,feeds:'battery'}],
   ['House roof: back main plane (test)',[[899.37,934.89],[907.37,944.76],[904.08,947.42],[896.08,937.55]],{bearing:230,tilt:23,h:5.4,panel:'jinko475',count:20,device:'sig25',per:20,feeds:'battery'}],
   ['House roof: front deck roof, air con (test)',[[902.73,931.98],[910.91,942.08],[912.41,940.87],[904.23,930.77]],{bearing:50,tilt:9,h:6.5,panel:'longi425',count:9,device:'solarac',per:9,feeds:'own',edge:0.1}]];
  for(const [name,pts,pv] of H){const id=newId(),now=new Date().toISOString();const doc={kind:'solar',name,status:'idea',notes:'Test array from the energy tool; roof faces from the drone photo of 23 Oct 2026 and the 2022 LiDAR (estimates).',stage:'now',geom:{g:'polygon',pts},pv,createdBy:myId||null,createdAt:now,updatedAt:now};
    features.set(id,doc);if(live){try{await db.collection(C('features')).doc(id).set(doc)}catch(e){toast('A test array did not save.')}}}
  if(!live)saveLocal();renderTools();draw();toast('Added the three house roof faces. Check them, then Work it out.')}

function enDownload(s,name,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([s],{type}));a.download=name;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},500)}

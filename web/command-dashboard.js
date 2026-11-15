/* AgriORBIT Phase 7 | Interactive mission dashboard.
   Keeps evidence and simulation provenance separate. No physical rover commands. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const clamp = (n,a,b) => Math.max(a,Math.min(b,n));
const safe = v => String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let model=null, shared=null, lastPoll=0, lastEnvironmentalAt=0, envTimeout=null, hydrated=false;
let trace=[], active=false;let postFX=false, quality='fps100';
const cached={};
function write(id,value){const el=$(id);if(el)el.textContent=String(value??'—');}
function status(){return $('view-command')?.classList.contains('active')&&!document.hidden;}
function value(sample,group,metric){const v=sample?.[group]?.[metric]?.value;return typeof v==='number'&&Number.isFinite(v)?v:null;}
function number(v,d=0){return typeof v==='number'&&Number.isFinite(v)?v.toFixed(d):'—';}
function spark(){
 const cv=$('cmd-moisture-chart');if(!cv)return;const w=Math.max(180,cv.clientWidth||300),h=105,dpr=Math.min(window.devicePixelRatio||1,2);
 cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr);const ctx=cv.getContext('2d');ctx.scale(dpr,dpr);ctx.fillStyle='#05182a';ctx.fillRect(0,0,w,h);
 ctx.strokeStyle='#1d5368';ctx.lineWidth=.7;for(let i=0;i<5;i++){const y=8+i*22;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}
 if(trace.length>1){ctx.strokeStyle='#00f0ff';ctx.shadowColor='#00f0ff';ctx.shadowBlur=8;ctx.lineWidth=2;ctx.beginPath();trace.forEach((v,i)=>{const x=i/(trace.length-1)*(w-16)+8,y=h-12-v/100*(h-24);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();ctx.shadowBlur=0;}
 ctx.font='9px Consolas,monospace';ctx.fillStyle='#7baebd';ctx.fillText('100%',4,11);ctx.fillText('0%',4,h-4);
}
function renderSample(sample){
 if(sample?.source_type!=='simulated'||sample.hardware_connected!==false)return; // Only this simulator drives demo HUD.
 const bat=value(sample,'structural','battery_percent'),temp=value(sample,'diagnostics','motor_temp_c'),slip=value(sample,'diagnostics','wheel_slip_pct');
 const moisture=value(sample,'payload','soil_moisture_relative'),soiltemp=value(sample,'payload','soil_temperature'),humidity=value(sample,'payload','humidity');
 write('cmd-stat-moisture',number(moisture,1)+'%');write('cmd-rover-battery',number(bat,0)+'%');write('cmd-rover-temp',number(temp,1));write('cmd-rover-slip',number(slip,1)+'%');
 write('cmd-rover-phase',sample.phase_name?.toUpperCase()||'STANDBY');write('cmd-waypoint','WAYPOINT: '+sample.waypoint);
 write('cmd-tel-waypoint',sample.waypoint);write('cmd-tel-moisture',number(moisture,1)+'%');write('cmd-tel-temp',number(soiltemp,1)+'°C');write('cmd-tel-humidity',number(humidity,0)+'%');
 if(moisture!==null){trace.push(moisture);if(trace.length>42)trace.shift();spark();}
}
async function fetchSimulation(){
 if(!model||!status())return; const progress=clamp(model.progress,0,1);
 try{const response=await fetch('/api/mission/simulate?progress='+progress.toFixed(3),{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);const sample=await response.json();renderSample(sample);}
 catch{write('cmd-stat-moisture','API OFFLINE');write('cmd-rover-phase','SIMULATION API OFFLINE');}
}
function drawMosaic(){const el=$('cmd-health-matrix'); if(!el)return;
 const colors=['#08d966','#00ff66','#2dd42e','#a5cb1b','#ffb703','#ef8129','#ff0055'];
 const list=[];for(let i=0;i<60;i++){
   const c=Math.floor(i/12),j=i%12;const wave=.5+.5*Math.sin(j*.87+c*1.21)+.23*Math.cos(j*2.1-c*.4);
   const idx=clamp(Math.floor(wave*3.25),0,6);list.push(`<i style="background:${colors[idx]}"></i>`);
 }el.innerHTML=list.join('');
}
function renderBoundary(){
 const p=$('cmd-boundary-shape'),raw=shared?.boundary||'';
 const defaultPath='M35 102L49 45L123 27L257 58L239 111L127 119Z';
 if(!raw){p.setAttribute('d',defaultPath);write('cmd-boundary-status','ILLUSTRATIVE SHAPE');write('cmd-boundary-info','No field polygon entered; drawing is a placeholder.');return;}
 try{
  const obj=JSON.parse(raw),g=obj.type==='Feature'?obj.geometry:obj,ring=g?.coordinates?.[0];
  if(g?.type!=='Polygon'||!Array.isArray(ring)||ring.length<4||ring.length>2000||!ring.every(q=>Array.isArray(q)&&Number.isFinite(q[0])&&Number.isFinite(q[1])))throw Error('Unsupported polygon');
  const xs=ring.map(q=>q[0]),ys=ring.map(q=>q[1]),dx=Math.max(...xs)-Math.min(...xs),dy=Math.max(...ys)-Math.min(...ys);
  if(!(dx>0&&dy>0))throw Error('Degenerate polygon');
  const scale=Math.min(246/dx,100/dy),padx=(300-dx*scale)/2,pady=(134-dy*scale)/2;
  const minX=Math.min(...xs),minY=Math.min(...ys);
  p.setAttribute('d',ring.map((q,i)=>`${i?'L':'M'}${(padx+(q[0]-minX)*scale).toFixed(1)} ${(134-pady-(q[1]-minY)*scale).toFixed(1)}`).join(' ')+'Z');
  write('cmd-boundary-status','USER-ENTERED GEOJSON');write('cmd-boundary-info','Geometry from farm profile; not GPS-surveyed or registered to the 3D scene.');
 }catch{p.setAttribute('d',defaultPath);write('cmd-boundary-status','INVALID POLYGON');write('cmd-boundary-info','Unable to parse GeoJSON; illustrative placeholder shown.');}
}
function sync(){
 if(!shared)return;
 const farm=shared.farm||{},climate=shared.climate,comparison=shared.comparison;
 write('cmd-stat-area',number(farm.area_ha,1)+' ha');write('cmd-stat-field',(farm.name||'BOTOLAN').slice(0,21).toUpperCase());
 write('cmd-soil-texture',farm.texture||'Unknown');write('cmd-soil-ph',number(farm.soil_ph,1));write('cmd-soil-organic',farm.organic_matter_pct==null?'NOT ENTERED':number(farm.organic_matter_pct,1)+'%');write('cmd-soil-irrigation',farm.irrigation||'Unknown');
 write('cmd-stat-scenarios',comparison?.scenarios?.length||'03');
 const scenarioHTML=(comparison?.scenarios||[]).map(s=>`<button type="button" data-cmd-scenario="${safe(s.id)}" class="${model?.scenario===s.id?'current':''}" title="${safe(s.description)}"><span>${safe(s.id)}</span><label>${safe(s.title)}</label><b>${Number.isFinite(s.score)?s.score+'/100':'—'}</b></button>`).join('');
 $('cmd-scenario-list').innerHTML=scenarioHTML||'<small>Score engine not connected. Open Rotation Studio.</small>';
 document.querySelectorAll('[data-cmd-scenario]').forEach(el=>el.addEventListener('click',()=>{model.scenario=el.dataset.cmdScenario;model.needsDraw=true;sync();scheduleEnv();}));
 const type=climate?.source_type;
 let climateBadge='NOT FETCHED';if(type==='synthetic')climateBadge='SYNTHETIC';else if(type==='nasa_cached')climateBadge='NASA CACHED';else if(type==='nasa_api')climateBadge='NASA HISTORICAL';
 write('cmd-stat-nasa',climateBadge);write('cmd-climate-tag',climateBadge);write('cmd-stat-nasa-detail',climate?'source · '+(climate.year||'—'):'historical POWER data');
 write('cmd-climate-year',climate?.year||'—');write('cmd-climate-source',climateBadge);
 const months=climate?.months||[],sumRain=months.reduce((sum,m)=>sum+(Number.isFinite(m.precipitation_mm)?m.precipitation_mm:0),0);
 const hasRain=months.some(m=>Number.isFinite(m.precipitation_mm));
 const temps=months.map(m=>m.temperature_c).filter(v=>Number.isFinite(v));
 write('cmd-climate-rain',hasRain?number(sumRain,0)+' mm':'—');write('cmd-climate-temp',temps.length?number(temps.reduce((a,b)=>a+b,0)/temps.length,1)+'°C':'—');
 // A 0% NASA coverage is not silently replaced by invented dashboard numbers.
 renderBoundary();
}
let envRequest=0;
async function updateEnvironment(){
 if(!shared?.farm||!model)return;
 const farm=shared.farm,weather=$('cmd-weather').value,overlay=$('cmd-overlay').value,day=$('cmd-light').value;
 const irrigation_percent=Number($('cmd-irrigation').value),drainage_percent=Number($('cmd-drainage').value);
 model.weather=weather;model.overlay=overlay;model.day=day;model.irrigation=irrigation_percent;model.drainage=drainage_percent;model.needsDraw=true;
 write('cmd-irrigation-value',irrigation_percent+'%');write('cmd-drainage-value',drainage_percent+'%');
 const seq=++envRequest;
 try{
  const response=await fetch('/api/mission/environment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({farm,scenario:model.scenario,weather,irrigation_percent,drainage_percent,day_phase:day})});
  if(!response.ok)throw Error('HTTP '+response.status);const d=await response.json();if(seq!==envRequest)return;
  model.setEnv(d);write('cmd-stat-water',typeof d.average_stress_index==='number'?d.average_stress_index+'/100':'—');
  write('cmd-env-description',`${weather.toUpperCase()} • hypothetical exposure ${d.average_stress_index}/100; not a predictive irrigation prescription.`);
 }catch{if(seq===envRequest){write('cmd-stat-water','API OFFLINE');write('cmd-env-description','Environmental model is unavailable. No calculated index.');}}
}
function scheduleEnv(){clearTimeout(envTimeout);envTimeout=setTimeout(updateEnvironment,160)}
function onView(view){active=view==='command';if(!active&&$('cmd-scene')?.classList.contains('cmd-fullscreen')){$('cmd-immersive')?.click();}if(active&&model){model.resize();model.needsDraw=true;sync();scheduleEnv();fetchSimulation();}}
function init(state){
 shared=state;
 try{
   model=new window.AgriOrbitHologram($('cmd-viewport'),{transparent:true});
   model.zoom=.86;model.yaw=.6;model.pitch=.64;model.scenario='B';model.needsDraw=true;
 }
 catch(e){write('cmd-api-status','3D CANVAS UNAVAILABLE');write('cmd-rover-phase','NO RENDERER: '+e.message);return;}
 // Restore local render preferences only; never reinterpret synthetic data as measured.
 try{
   const saved=JSON.parse(localStorage.getItem('agriorbit-phase32-graphics')||'null');
   if(saved&&['fps100','ultra','high','auto','eco','boost'].includes(saved.quality)){quality=saved.quality;postFX=saved.postFX===true;}
   else if(window.matchMedia('(max-width: 760px)').matches)quality='high';
 }catch{}
 function setQuality(q){
   quality=['fps100','ultra','high','auto','eco','boost'].includes(q)?q:'auto';
   model.quality=quality;document.body.classList.toggle('agri-perf-100',quality==='fps100');model.postFX=(quality==='boost'||quality==='fps100')?false:postFX;model.bloom=(quality==='boost'||quality==='fps100')?false:postFX;
   model.resize();model.needsDraw=true;
   $('cmd-quality').value=quality;$('cmd-postfx').checked=(quality==='boost'||quality==='fps100')?false:postFX;$('cmd-postfx').disabled=(quality==='boost'||quality==='fps100');
   $('cmd-scene').classList.toggle('ultra-mode',quality==='ultra');
   $('cmd-scene').classList.toggle('fx-off',!postFX);
   write('cmd-ultra-tag',(quality==='ultra'?'✦ ULTRA':quality==='boost'?'⚡ FPS BOOST':quality==='fps100'?'⚡ 100 FPS TARGET':quality.toUpperCase())+' GRAPHICS · SYNTHETIC · PHASE 32 PERFORMANCE');
   try{localStorage.setItem('agriorbit-phase32-graphics',JSON.stringify({quality,postFX}));}catch{}
 }
 setQuality(quality);
 $('cmd-quality').addEventListener('change',e=>setQuality(e.target.value));
 $('cmd-postfx').addEventListener('change',e=>{postFX=e.target.checked;setQuality(quality);});
 $('cmd-sun').addEventListener('input',e=>{model.sunAngle=Number(e.target.value);model.needsDraw=true;write('cmd-sun-value',model.sunAngle+'°');});
 model.onFrameStats=(fps,stats={})=>write('cmd-render-stats',fps+' ACTUAL FPS'+(quality==='fps100'?' / 100 TARGET':'')+' · '+(stats.drawMs??'—')+'ms CPU · '+(model.dpr||1).toFixed(2)+'×'+(model.adaptiveScale<.99?' · ADAPTIVE':'') );
 function setImmersive(enabled){
   $('cmd-scene').classList.toggle('cmd-fullscreen',enabled);
   $('cmd-immersive').setAttribute('aria-pressed',String(enabled));
   $('cmd-immersive').textContent=enabled?'✕ EXIT IMMERSIVE':'⛶ IMMERSIVE';
   document.body.classList.toggle('cmd-immersive-body',enabled);
   requestAnimationFrame(()=>model.resize());
 }
 $('cmd-immersive').addEventListener('click',()=>setImmersive(!$('cmd-scene').classList.contains('cmd-fullscreen')));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('cmd-scene').classList.contains('cmd-fullscreen'))setImmersive(false)});
 drawMosaic();sync();spark();
 for(const b of document.querySelectorAll('[data-cmd-layer]'))b.addEventListener('click',()=>{model.layer=b.dataset.cmdLayer;model.needsDraw=true;document.querySelectorAll('[data-cmd-layer]').forEach(el=>{let pressed=el===b;el.classList.toggle('active',pressed);el.setAttribute('aria-pressed',pressed);});});
 $('cmd-run').addEventListener('click',()=>{if(model.progress>=1){model.progress=0;}model.playing=!model.playing;model.motion=true;write('cmd-run',model.playing?'❚❚ PAUSE ROVER MISSION':'▶ CONTINUE ROVER MISSION');model.needsDraw=true;});
 $('cmd-restart').addEventListener('click',()=>{model.playing=false;model.progress=0;model.needsDraw=true;write('cmd-run','▶ START ROVER MISSION');write('cmd-progress','0');write('cmd-progress-label','0%');fetchSimulation();});
 $('cmd-progress').addEventListener('input',e=>{model.progress=clamp(Number(e.target.value)/100,0,1);model.playing=false;model.needsDraw=true;write('cmd-progress-label',e.target.value+'%');write('cmd-run','▶ START ROVER MISSION');fetchSimulation();});
 model.onProgress=p=>{const n=Math.round(p*100);$('cmd-progress').value=String(n);write('cmd-progress-label',n+'%');if(n>=100&&!model.loop)write('cmd-run','▶ REPLAY ROVER MISSION');};
 $('cmd-speed').addEventListener('change',e=>{model.speed=Number(e.target.value);});
 $('cmd-scanlines').addEventListener('change',e=>$('cmd-scene').classList.toggle('scanlines-on',e.target.checked));
 $('cmd-reset-camera').addEventListener('click',()=>model.reset());$('cmd-zoom-plus').addEventListener('click',()=>{model.zoom=clamp(model.zoom*1.14,.6,1.8);model.needsDraw=true;});$('cmd-zoom-minus').addEventListener('click',()=>{model.zoom=clamp(model.zoom*.88,.6,1.8);model.needsDraw=true;});
 for(const id of ['cmd-overlay','cmd-weather','cmd-light'])$(id).addEventListener('change',scheduleEnv);
 for(const id of ['cmd-irrigation','cmd-drainage'])$(id).addEventListener('input',scheduleEnv);
 $('cmd-blend').addEventListener('input',e=>{const v=clamp(Number(e.target.value),0,100);$('cmd-viewport').style.opacity=(v/100).toFixed(2);write('cmd-blend-value',v+'%');});
 $('cmd-nasa-fetch').addEventListener('click',()=>{window.fetchClimate?.('nasa');});
 // A real health check, not a false assertion about NASA availability or rover hardware.
 fetch('/api/health',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('unavailable');return r.json()}).then(d=>{write('cmd-api-status',d.status==='ok'?'LOCAL API CONNECTED':'API ISSUE')}).catch(()=>write('cmd-api-status','LOCAL API OFFLINE'));
 updateEnvironment();fetchSimulation();
 setInterval(()=>{if(status())fetchSimulation();},1300);
 window.addEventListener('resize',()=>spark());
 active=status();hydrated=true;
}
window.AgriOrbitCommand={init,onView,sync,renderSample};
})();

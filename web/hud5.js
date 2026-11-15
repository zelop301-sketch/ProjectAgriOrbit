/* Phase 5: user-controlled HUD effects, synthetic plot overlays, camera scout, widget docking.
   No NASA raster ingestion or instrument calibration is performed here. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const clamp = (n,a,b)=>Math.max(a,Math.min(b,n));
let renderer=null, farmState=null, stream=null, trace=[];
const DEFAULTS={crt:false,bloom:true,quality:'fps100',sun:55};
let config={...DEFAULTS};
function readSaved(key,fallback){try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}}
function save(key,v){try{localStorage.setItem(key,JSON.stringify(v))}catch{}}
function announce(msg){$('hud-effects-status').textContent=msg;}
function apply(){
 const wrap=$('holo-canvas-wrap');
 wrap.classList.toggle('scanlines-on',config.crt);
 wrap.classList.toggle('bloom-on',config.bloom);
 renderer.bloom=(config.quality==='boost'||config.quality==='fps100')?false:config.bloom;renderer.postFX=(config.quality==='boost'||config.quality==='fps100')?false:config.bloom;
 renderer.quality=config.quality;
 renderer.sunAngle=config.sun;
 renderer.resize();renderer.needsDraw=true;
 announce(`Local 3D · ${config.quality.toUpperCase()} render · ${config.sun}° illustrative solar angle · ECOSTRESS raster not loaded`);
 save('agriorbit-phase32-hud',config);
}
function widgetOrder(){return [...document.querySelectorAll('.holo-data-sidebar [data-hud-widget]')].map(x=>x.dataset.hudWidget)}
function updateDock(){
 const widgets=[...document.querySelectorAll('.holo-data-sidebar [data-hud-widget]')];
 widgets.forEach((card,i)=>{
  const up=card.querySelector('[data-dock-up]');const down=card.querySelector('[data-dock-down]');
  up.disabled=i===0;down.disabled=i===widgets.length-1;
 });
}
function mountDock(){
 const side=document.querySelector('.holo-data-sidebar');
 const valid=[...side.querySelectorAll('[data-hud-widget]')];
 const saved=readSaved('agriorbit-phase5-order',[]);
 if(Array.isArray(saved))saved.forEach(id=>{const card=valid.find(el=>el.dataset.hudWidget===id);if(card)side.appendChild(card)});
 [...side.querySelectorAll('[data-hud-widget]')].forEach(card=>{
  const tools=document.createElement('div');tools.className='hud-widget-reorder';
  const caption=document.createElement('small');caption.textContent='WIDGET ORDER';
  const up=document.createElement('button');up.type='button';up.dataset.dockUp='1';up.textContent='↑';up.setAttribute('aria-label',`Move ${card.dataset.hudWidget} widget up`);
  const down=document.createElement('button');down.type='button';down.dataset.dockDown='1';down.textContent='↓';down.setAttribute('aria-label',`Move ${card.dataset.hudWidget} widget down`);
  tools.append(caption,up,down);card.prepend(tools);
  up.addEventListener('click',()=>{const prev=card.previousElementSibling;if(prev){side.insertBefore(card,prev);save('agriorbit-phase5-order',widgetOrder());updateDock();}});
  down.addEventListener('click',()=>{const next=card.nextElementSibling;if(next){side.insertBefore(next,card);save('agriorbit-phase5-order',widgetOrder());updateDock();}});
 });updateDock();
}
function plotBoundary(){
 const raw=farmState?.boundary||'';
 const node=$('hud-boundary-path');
 node.setAttribute('d','');
 $('hud-boundary-status').textContent=raw?'USER GEOJSON':'POINT ONLY';
 if(!raw)return;
 try{
  const o=JSON.parse(raw),g=o.type==='Feature'?o.geometry:o,ring=g?.coordinates?.[0];
  if(g.type!=='Polygon'||!Array.isArray(ring)||ring.length<4||ring.length>2000)throw Error('Invalid polygon');
  if(!ring.every(p=>Array.isArray(p)&&Number.isFinite(p[0])&&Number.isFinite(p[1])))throw Error('Invalid coordinates');
  const xs=ring.map(p=>p[0]),ys=ring.map(p=>p[1]);
  const minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);
  const dx=maxx-minx,dy=maxy-miny;
  if(dx<=0||dy<=0)throw Error('Degenerate polygon');
  const scale=Math.min(224/dx,80/dy);
  const xpad=(260-dx*scale)/2,ypad=(105-dy*scale)/2;
  node.setAttribute('d',ring.map((p,i)=>`${i?'L':'M'}${(xpad+(p[0]-minx)*scale).toFixed(1)} ${(105-ypad-(p[1]-miny)*scale).toFixed(1)}`).join(' ')+' Z');
  $('hud-boundary-status').textContent='USER POLYGON (PREVIEW)';
 }catch{$('hud-boundary-status').textContent='INVALID GEOJSON';}
}
function updateClimate(){
 const cl=farmState?.climate;
 $('hud-climate-status').textContent=!cl?'NOT FETCHED':cl.source_type==='synthetic'?'SYNTHETIC':cl.source_type==='nasa_cached'?'NASA CACHED':cl.source_type==='nasa_api'?'NASA HISTORICAL':'CHECK SOURCE';
}
function drawTrace(){
 const c=$('hud-trace');if(!c)return;
 const dpr=Math.min(2,window.devicePixelRatio||1);const width=Math.max(220,c.clientWidth||300),height=94;
 c.width=Math.round(width*dpr);c.height=Math.round(height*dpr);
 const ctx=c.getContext('2d');ctx.scale(dpr,dpr);
 ctx.fillStyle='#091b2c';ctx.fillRect(0,0,width,height);
 ctx.strokeStyle='#1a465a';ctx.lineWidth=1;for(let i=1;i<4;i++){ctx.beginPath();ctx.moveTo(8,i*height/4);ctx.lineTo(width-8,i*height/4);ctx.stroke()}
 if(trace.length){
  ctx.beginPath();trace.forEach((v,i)=>{const x=9+i/Math.max(trace.length-1,1)*(width-18),y=height-12-(v/100)*(height-24);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});
  ctx.strokeStyle='#00F0FF';ctx.lineWidth=2;ctx.shadowBlur=7;ctx.shadowColor='#00F0FF';ctx.stroke();ctx.shadowBlur=0;
 }
 $('hud-trace-count').textContent=`${trace.length} points`;
}
function onSample(sample){
 const m=sample?.payload?.soil_moisture_relative?.value;
 if(Number.isFinite(m)){trace.push(clamp(m,0,100));if(trace.length>36)trace.shift();drawTrace();}
}
function closeAR(){
 if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
 const video=$('hud-ar-video');video.pause();video.srcObject=null;
 $('hud-ar-panel').hidden=true;
}
async function openAR(){
 const panel=$('hud-ar-panel');panel.hidden=false;
 $('hud-ar-message').textContent='Requesting optional camera permission…';
 if(!navigator.mediaDevices?.getUserMedia){$('hud-ar-message').textContent='Camera capture unavailable. Use localhost or a secure HTTPS origin with a compatible browser.';return;}
 try{
  stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280}}});
  if(panel.hidden){closeAR();return;}
  const video=$('hud-ar-video');video.srcObject=stream;await video.play();
  $('hud-ar-message').textContent='Camera image is local to this browser. Markers are decorative and NOT anchored to field positions; no camera frames are uploaded.';
 }catch(e){$('hud-ar-message').textContent='Camera unavailable or permission denied: '+(e.name||'error')+'. No camera data recorded.';closeStreamOnly();}
}
function closeStreamOnly(){if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}}
function init(holo,farm){
 if(renderer)return;
 renderer=holo;farmState=farm;
 const user=readSaved('agriorbit-phase32-hud',{});
 if(user&&typeof user==='object')config={crt:!!user.crt,bloom:user.bloom!==false,quality:['fps100','boost','auto','high','ultra','eco'].includes(user.quality)?user.quality:'auto',sun:clamp(Number(user.sun)||55,5,85)};
 $('hud-crt').checked=config.crt;$('hud-bloom').checked=config.bloom;$('hud-quality').value=config.quality;$('hud-sun').value=config.sun;$('hud-sun-value').textContent=config.sun+'°';
 $('hud-crt').addEventListener('change',e=>{config.crt=e.target.checked;apply()});
 $('hud-bloom').addEventListener('change',e=>{config.bloom=e.target.checked;apply()});
 $('hud-quality').addEventListener('change',e=>{config.quality=e.target.value;apply()});
 $('hud-sun').addEventListener('input',e=>{config.sun=+e.target.value;$('hud-sun-value').textContent=config.sun+'°';apply()});
 $('hud-ar').addEventListener('click',openAR);$('hud-ar-close').addEventListener('click',closeAR);
 document.addEventListener('visibilitychange',()=>{if(document.hidden)closeAR()});
 window.addEventListener('pagehide',closeAR);
 window.addEventListener('resize',drawTrace);
 mountDock();plotBoundary();updateClimate();drawTrace();apply();
}
function onView(v){if(v!=='rover')closeAR();else{plotBoundary();updateClimate();drawTrace();}}
window.AgriOrbitHUD5={init,onSample,onView};
})();

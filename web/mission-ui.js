/* Live client ↔ provenance-tagged simulator interface. No physical commands. */
(() => {
'use strict';
const $=id=>document.getElementById(id);
let globe=null, farmState=null, latestModel=null, simFetchAt=0, envTimer=null, lastProgress=-1;
const esc=x=>String(x??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
function text(id,v){const el=$(id);if(el)el.textContent=String(v??'—');}
async function getJSON(url,opts={}) {const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),url.includes("/api/earth/granules") ? 18000 : 6000);try {const r=await fetch(url,{...opts,signal:controller.signal});if(!r.ok)throw Error(`HTTP ${r.status}`);return await r.json();}finally{clearTimeout(timer)}}
function metric(group,name,digits=0,suffix=''){const v=latestModel?.[group]?.[name]?.value;return typeof v==='number' ? v.toFixed(digits)+suffix+'*' : '—';}
function renderSample(d){latestModel=d; window.AgriOrbitHUD5?.onSample(d); text('holo-waypoint',d.waypoint);text('holo-phase',d.phase_name);
 text('holo-battery',metric('structural','battery_percent',0,'%'));text('holo-solar',metric('structural','solar_assist_percent',0,'%'));
 text('holo-suspension',metric('structural','suspension_load_index',2));
 text('moisture',metric('payload','soil_moisture_relative',0,'%'));$('moisture-bar').style.width=String(d.payload.soil_moisture_relative.value)+'%';
 text('soil-temp',metric('payload','soil_temperature',1,' °C'));text('holo-ndvi',metric('payload','ndvi_proxy',3));
 text('holo-compaction',metric('payload','soil_compaction_proxy',0,' kPa'));
 text('holo-atmos',metric('payload','co2',0,' ppm')+' / '+metric('payload','humidity',0,'%'));
 text('holo-slip',metric('diagnostics','wheel_slip_pct',1,'%'));text('holo-motor',metric('diagnostics','motor_temp_c',1,' °C'));text('holo-dust',metric('diagnostics','lens_dust_pct',0,'%'));
 text('gps-reading','NO GPS • u='+d.position.u+' v='+d.position.v);text('telemetry-time',d.timestamp);
 text('holo-link-status','SIMULATED');
}
async function refreshTelemetry(progress){try{const d=await getJSON('/api/mission/simulate?progress='+Math.min(1,Math.max(0,progress)).toFixed(3));renderSample(d);}catch(e){text('holo-link-status','API OFFLINE');text('holo-phase','Simulation API unavailable');}}
async function updateEnvironment(){if(!farmState||!globe)return;const f=farmState.farm;
 const payload={farm:f,scenario:globe.scenario,weather:$('env-weather').value,irrigation_percent:+$('env-irrigation').value,drainage_percent:+$('env-drainage').value,day_phase:$('env-light').value};
 text('env-irrigation-value',payload.irrigation_percent+'%');text('env-drainage-value',payload.drainage_percent+'%');
 globe.day=payload.day_phase;globe.weather=payload.weather;globe.overlay=$('env-overlay').value;globe.needsDraw=true;
 try{const d=await getJSON('/api/mission/environment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
   globe.setEnv(d);text('env-index','');$('env-index').innerHTML='<b>HYPOTHETICAL EXPOSURE INDEX</b><span>Average '+d.average_stress_index+'/100 • '+d.weather_mode.toUpperCase()+'</span>';
   $('env-zones').innerHTML=d.zones.map(z=>`<div class="env-zone ${z.health_band==='lower_exposure'?'':z.health_band}"><span>${esc(z.id)} • ${esc(z.health_band).replace('_',' ')}</span><b>${z.stress_index}<small>/100</small></b><span>Deficit ${z.water_deficit_index} · Excess ${z.excess_water_index}</span></div>`).join('');
 }catch(e){text('env-index','Environment model unavailable: '+e.message);}
}
function scheduleEnv(){clearTimeout(envTimer);envTimer=setTimeout(updateEnvironment,100)}
async function renderDataSources(){try{const d=await getJSON('/api/earth/sources');$('holo-earth-sources').innerHTML=d.datasets.map(s=>`<div class="source-entry"><strong>${esc(s.provider)}</strong><span>${esc(s.status).replaceAll('_',' ')} · ${esc(s.integration)}</span></div>`).join('');}catch(e){text('holo-earth-sources','Earth source registry unavailable.');}}
async function refreshIngest(){try{const d=await getJSON('/api/mission/telemetry?limit=4');text('holo-ingest-log',d.samples.length?d.samples.map(s=>`${s.source_type.toUpperCase()} · ${s.metric}: ${s.value} ${s.unit} · ${s.timestamp}`).join('\n'):'No stored telemetry packets. Demonstration route never records itself as measured data.');}catch(e){text('holo-ingest-log','Stored telemetry unavailable: '+e.message);}}
async function lookupCatalog(){
  const btn=$('earth-catalog-fetch');btn.disabled=true;text('earth-catalog-results','Looking up public NASA Earthdata catalog metadata…');
  try{
    const f=farmState.farm, product=$('earth-catalog-product').value;
    const d=await getJSON('/api/earth/granules?product='+encodeURIComponent(product)+'&lat='+encodeURIComponent(f.latitude)+'&lon='+encodeURIComponent(f.longitude)+'&year=2025');
    $('earth-catalog-results').innerHTML=`<strong>${esc(d.provider)}</strong><p>${d.granules.length} catalog records found · ${d.query_year} · NO RASTER PIXELS LOADED</p>`+
       d.granules.map(g=>`<p><b>${esc(g.time_start||'Undated')}</b> ${esc(g.title)}</p>`).join('')+
       `<p class="catalog-warning">${esc(d.warning)}</p>`;
  }catch(e){text('earth-catalog-results','Lookup unavailable: '+e.message+'. Existing simulation is unaffected.');}
  finally{btn.disabled=false;}
}
function setScenario(s){if(!globe)return;globe.scenario=s;globe.needsDraw=true;document.querySelectorAll('[data-holo-scenario]').forEach(b=>b.classList.toggle('active',b.dataset.holoScenario===s));
 text('holo-scenario-note',`Scenario ${s} visible as an illustrative colored farm grid only. It is NOT a crop suitability map.`);scheduleEnv();}
function setLayer(layer){if(!globe)return;globe.layer=layer;globe.needsDraw=true;document.querySelectorAll('[data-holo-layer]').forEach(b=>{b.classList.toggle('active',b.dataset.holoLayer===layer);b.setAttribute('aria-pressed',String(b.dataset.holoLayer===layer))});text('holo-layer-label',layer.toUpperCase()+' • ALL SYNTHETIC');}
function repaintStatus(){if(!farmState)return;
 text('mission-farm',farmState.farm.name.toUpperCase());
 const climate=farmState.climate;const status=climate ? ((climate.source_type==='synthetic')?'SYNTHETIC':climate.source_type==='nasa_cached'?'NASA / CACHED':climate.provider?.includes('NASA')?'NASA / HISTORICAL':'UNVERIFIED') : 'NOT LOADED';
 text('holo-nasa-status',status);
}
function init(farm){farmState=farm;
 try{globe=new window.AgriOrbitHologram($('holo-viewport'));text('holo-engine-status','LOCAL 3D ACTIVE');}catch(err){text('holo-engine-status','UNAVAILABLE');$('holo-fallback').hidden=false;text('holo-fallback',err.message);return;}
 const motionAllowed=!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
 globe.onFrameStats=fps=>{text('holo-render-fps',fps+' FPS');text('holo-animation-state',globe.motion?'SCENE IN MOTION':'AMBIENT PAUSED');};
 globe.onCinematicStage=i=>{const labels=['DEPARTURE / BASE','CROP ZONE TRANSIT','SOIL SCAN / WAYPOINT','SATELLITE DATA UPLINK'];
  text('holo-stage','SCENE '+(i+1)+'/4 · '+labels[i]);
  if(globe.cinematic)setLayer(['structural','navigation','diagnostic','navigation'][i]);
 };
 $('holo-speed').addEventListener('change',e=>{globe.speed=Number(e.target.value);});
 $('holo-loop').addEventListener('change',e=>{globe.loop=e.target.checked;});
 $('holo-ambient').checked=globe.motion;
 $('holo-ambient').addEventListener('change',e=>{globe.motion=e.target.checked;globe.needsDraw=true;
  text('holo-animation-guide',globe.motion?'Cyan scan, crop wind and irrigation particles are simulated.':'Ambient motion paused; rover route can still play.');});
 $('holo-orbit').addEventListener('change',e=>{globe.autoOrbit=e.target.checked&&globe.motion;});
 $('holo-viewport').addEventListener('pointerdown',()=>{$('holo-orbit').checked=false;});
 $('holo-cinematic').addEventListener('click',()=>{
  globe.cinematic=true;globe.stage=-1;globe.progress=0;globe.playing=true;globe.motion=true;globe.autoOrbit=motionAllowed;
  globe.speed=2;globe.loop=false;globe.needsDraw=true;
  $('holo-loop').checked=false;$('holo-ambient').checked=true;$('holo-orbit').checked=globe.autoOrbit;$('holo-speed').value='2';
  text('holo-play','❚❚ Pause simulation');text('holo-stage','SCENE 1/4 · DEPARTURE / BASE');
  text('holo-animation-guide','Cinematic mode: illustrated animations, not observations or hardware operations.');
 });
 globe.onProgress=p=>{const n=Math.round(p*100);$('holo-timeline').value=n;text('holo-progress-text',n+'%');if(p===1&&!globe.loop){text('holo-play','▶ Replay simulated mission');text('holo-stage','MISSION COMPLETE · SYNTHETIC');}if(Math.abs(p-lastProgress)>.025&&Date.now()-simFetchAt>350){lastProgress=p;simFetchAt=Date.now();refreshTelemetry(p);}};
 $('holo-play').addEventListener('click',()=>{if(globe.progress>=1){globe.progress=0;globe.needsDraw=true;}globe.playing=!globe.playing;text('holo-play',globe.playing?'❚❚ Pause simulation':'▶ Start simulated mission');});
 $('holo-restart').addEventListener('click',()=>{globe.playing=false;globe.cinematic=false;globe.progress=0;globe.needsDraw=true;text('holo-stage','STANDBY · 4 WAYPOINT DEMO');$('holo-timeline').value='0';text('holo-progress-text','0%');text('holo-play','▶ Start simulated mission');refreshTelemetry(0);});
 $('holo-timeline').addEventListener('input',e=>{globe.playing=false;globe.cinematic=false;globe.progress=+e.target.value/100;globe.needsDraw=true;text('holo-progress-text',e.target.value+'%');text('holo-play','▶ Start simulated mission');refreshTelemetry(globe.progress);});
 $('holo-reset').addEventListener('click',()=>globe.reset());
 $('holo-zoom-in').addEventListener('click',()=>{globe.zoom=Math.min(1.8,globe.zoom*1.12);globe.needsDraw=true});
 $('holo-zoom-out').addEventListener('click',()=>{globe.zoom=Math.max(.6,globe.zoom*.89);globe.needsDraw=true});
 document.querySelectorAll('[data-holo-layer]').forEach(b=>b.addEventListener('click',()=>setLayer(b.dataset.holoLayer)));
 document.querySelectorAll('[data-holo-scenario]').forEach(b=>b.addEventListener('click',()=>setScenario(b.dataset.holoScenario)));
 ['env-weather','env-overlay','env-light','env-irrigation','env-drainage'].forEach(id=>$(id).addEventListener(id.includes('irrigation')||id.includes('drainage')?'input':'change',scheduleEnv));
 $('holo-refresh').addEventListener('click',refreshIngest);
 $('earth-catalog-fetch').addEventListener('click',lookupCatalog);
 renderDataSources();refreshTelemetry(0);refreshIngest();repaintStatus();updateEnvironment();
 window.AgriOrbitHUD5?.init(globe, farmState);
 getJSON('/api/mission/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(farmState.farm)}).then(d=>text('mission-id',d.id.toUpperCase())).catch(()=>{});
}
function onView(view){window.AgriOrbitHUD5?.onView(view);if(view==='rover'&&globe){globe.resize();globe.needsDraw=true;repaintStatus();scheduleEnv();}}
window.AgriOrbitMission={init,onView,refreshTelemetry,repaintStatus};
})();

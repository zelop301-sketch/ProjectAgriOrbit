/* Phase 22 — user-supplied geospatial hazard screening, not an official PHIVOLCS service. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let hazardLayer = null;
  let latest = null;
  let sampleMode = false;
  const namespace = 'http://www.w3.org/2000/svg';
  function msg(message){$('h22-status').textContent = message;}
  function getSaved(){return window.AgriOrbitGetFarm?.() || {farm:null,boundary:''};}
  const source = () => ({
    agency_declared: sampleMode ? 'FICTIONAL SIMULATOR — NOT PHIVOLCS' : 'DOST-PHIVOLCS (user declaration, unverified)',
    title:$('h22-title').value.trim(),source_url:$('h22-source-url').value.trim() || null,
    map_date:$('h22-map-date').value || null,edition:$('h22-edition').value.trim(),
    use_permission:$('h22-permission').value,
    permission_notes: sampleMode ? 'Entirely synthetic demonstration geometry' : 'User assertion only; not authenticated by software.'
  });
  function parseField(){
    const raw=$('h22-farm').value.trim();
    if(!raw)throw new Error('Enter a real or explicitly fictional farm GeoJSON Polygon.');
    let value;try {value=JSON.parse(raw)} catch {throw new Error('Farm boundary is not valid GeoJSON JSON.');}
    return value;
  }
  function coords(geo){
    if(!geo)return [];
    if(geo.type==='Feature')return coords(geo.geometry);
    if(geo.type==='Polygon')return geo.coordinates || [];
    if(geo.type==='MultiPolygon')return (geo.coordinates || []).flatMap(p=>p);
    return [];
  }
  function makeSVG(tag,attrs){const n=document.createElementNS(namespace,tag);for(const [k,v] of Object.entries(attrs||{}))n.setAttribute(k,String(v));return n;}
  function draw(result){
    const svg=$('h22-svg');svg.replaceChildren();
    svg.appendChild(makeSVG('rect',{x:0,y:0,width:620,height:360,fill:'#041a29'}));
    for(let x=18;x<=602;x+=32){svg.appendChild(makeSVG('line',{x1:x,y1:0,x2:x,y2:360,stroke:'#1f5363','stroke-opacity':.19}));}
    for(let y=18;y<=342;y+=32){svg.appendChild(makeSVG('line',{x1:0,y1:y,x2:620,y2:y,stroke:'#1f5363','stroke-opacity':.19}));}
    const polygons=[...coords(result.farm_geometry)];
    for(const f of result.clipped_overlays.features)polygons.push(...coords(f.geometry));
    const points=polygons.flat();
    if(!points.length)return;
    const xs=points.map(a=>Number(a[0])),ys=points.map(a=>Number(a[1]));
    const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
    const xspan=Math.max(.00001,xmax-xmin),yspan=Math.max(.00001,ymax-ymin);
    const sc=Math.min(550/xspan,282/yspan),left=(620-sc*xspan)/2,top=(360-sc*yspan)/2;
    const project=([x,y])=>[left+(Number(x)-xmin)*sc,360-top-(Number(y)-ymin)*sc];
    const path=(rings)=>rings.map(r=>r.map((v,i)=>{const [x,y]=project(v);return `${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`;}).join(' ')+' Z').join(' ');
    const farmRing=coords(result.farm_geometry);
    svg.appendChild(makeSVG('path',{d:path(farmRing),fill:'#08c583', 'fill-opacity':.12,stroke:'#52ffc3','stroke-width':2.4,'fill-rule':'evenodd'}));
    for(const zone of result.clipped_overlays.features){
      svg.appendChild(makeSVG('path',{d:path(coords(zone.geometry)),fill:'#ffb703','fill-opacity':.46,stroke:'#ffcf7a','stroke-width':2,'fill-rule':'evenodd'}));
    }
    svg.appendChild(makeSVG('text',{x:18,y:28,fill:'#88edda','font-size':12,'font-family':'monospace'}));
    svg.lastChild.textContent = sampleMode ? 'FICTIONAL SHAPES — NOT PHIVOLCS' : 'USER-SUPPLIED, UNVERIFIED MAP';
    const marker=makeSVG('text',{x:18,y:345,fill:'#b7cbd6','font-size':11,'font-family':'monospace'});
    marker.textContent='Green = supplied field | Amber = mapped intersection';svg.appendChild(marker);
  }
  function outcome(result){
    const pct=result.mapped_overlap_percent;
    const headline={mapped_overlap_detected:'MAPPED OVERLAP DETECTED — NOT A FORECAST',no_overlap_in_supplied_layers:'NO OVERLAP WITH SUPPLIED LAYERS — NOT A SAFETY CLAIM',not_assessed_no_map:'NOT ASSESSED — MAP MISSING'}[result.status]||result.status;
    $('h22-summary').replaceChildren();
    const title=document.createElement('strong');title.textContent=headline;$('h22-summary').appendChild(title);
    const p=document.createElement('p');p.textContent=`Approximate field area ${result.farm_area_ha_utm_approx} ha · Mapped overlap ${pct===null?'UNKNOWN':pct+'%'} (indicative UTM area).`;$('h22-summary').appendChild(p);
    const ul=document.createElement('ul');result.flags.forEach(flag=>{const li=document.createElement('li');li.textContent=flag;ul.appendChild(li)});$('h22-summary').appendChild(ul);
    msg(`${result.status.replaceAll('_',' ').toUpperCase()} · Provenance: user-supplied, unverified. ${result.overlap_by_source_feature.length} intersecting mapped feature(s).`);
    const climate=result.nasa_climate_context;
    if(climate && climate.status!=='not_requested')$('h22-climate').textContent=`${climate.data_class} / ${climate.status}. Historical rainfall departure: ${climate.rainfall_anomaly_pct===null?'unavailable':climate.rainfall_anomaly_pct+'%'}. NOT A LAHAR FORECAST.`;
    draw(result);
  }
  async function screen(mode='none'){
    if(hazardLayer && sampleMode===false && !$('h22-file').files.length){throw new Error('Hazard layer is missing; choose your local GeoJSON file.');}
    const saved=getSaved(), farm=saved.farm;
    if(mode!=='none' && !farm)throw new Error('Save a farm profile for NASA climate context first.');
    const payload={farm_geometry:parseField(),hazard_geojson:hazardLayer,source:source(),
      climate_mode:mode,farm:mode==='none'?null:farm,
      climate_end_year:Number(document.getElementById('precision-year')?.value||2025),
      climate_baseline_years:Number(document.getElementById('precision-years')?.value||5)};
    if(mode!=='none' && (!farm || typeof farm.latitude!=='number'))throw new Error('Farm profile must contain latitude/longitude.');
    ['h22-run','h22-nasa','h22-synthetic'].forEach(id=>$(id).disabled=true);
    msg(mode==='nasa'?'Retrieving NASA historical data (no simulated fallback)...':'Screening user-supplied geometry…');
    try {
      const response=await fetch('/api/hazards/screen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const data=await response.json();
      if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail||`HTTP ${response.status}`));
      latest=data;$('h22-export').disabled=false;outcome(data);
    } finally {['h22-run','h22-nasa','h22-synthetic'].forEach(id=>$(id).disabled=false);}
  }
  async function run(mode){try{await screen(mode)}catch(e){msg('Assessment unavailable: '+e.message);$('h22-export').disabled=true;latest=null;}}
  function fileReady(){
    $('h22-file').addEventListener('change',async e=>{
      hazardLayer=null;sampleMode=false;latest=null;$('h22-export').disabled=true;
      const file=e.target.files?.[0];if(!file){msg('No local file selected.');return;}
      if(file.size>2_000_000){msg('File exceeds local 2 MB limit. Clip to your study area first.');return;}
      try{hazardLayer=JSON.parse(await file.text());msg(`Loaded ${file.name} locally for analysis. Source authenticity and map rights NOT VERIFIED.`)}
      catch{msg('Could not parse GeoJSON. Select a valid .geojson or .json file.');}
    });
  }
  function loadFarm(){const saved=getSaved();if(saved.boundary){$('h22-farm').value=saved.boundary;msg('Copied saved farm boundary (user supplied, not surveyed).');}else{msg('No saved boundary. Open Farm Profile to add a GeoJSON polygon or load the FICTIONAL example.');}}
  async function demo(){
    try{const r=await fetch('/api/hazards/demo');if(!r.ok)throw new Error('Demo endpoint failed.');const data=await r.json();
      hazardLayer=data.hazard_geojson;$('h22-farm').value=JSON.stringify(data.farm_geometry,null,2);
      $('h22-title').value='FICTIONAL example, not PHIVOLCS';$('h22-source-url').value='';$('h22-edition').value='Synthetic';$('h22-map-date').value='';$('h22-permission').value='local_review_only';
      $('h22-file').value='';sampleMode=true;msg('FICTIONAL field and fictional hazard zone loaded. Not a representation of any real Philippine site.');
    }catch(e){msg(e.message);}
  }
  function exportLatest(){if(!latest)return;const file=new Blob([JSON.stringify(latest,null,2)],{type:'application/json'});const url=URL.createObjectURL(file),a=document.createElement('a');a.href=url;a.download='AgriORBIT_Phase22_Hazard_Exposure_Evidence.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function boot(){if(!$('h22-run'))return;fileReady();$('h22-demo').addEventListener('click',demo);$('h22-from-farm').addEventListener('click',loadFarm);$('h22-run').addEventListener('click',()=>run());$('h22-nasa').addEventListener('click',()=>run('nasa'));$('h22-synthetic').addEventListener('click',()=>run('synthetic'));$('h22-export').addEventListener('click',exportLatest);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

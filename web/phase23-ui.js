/* Phase 23: real POWER historical data + local PHIVOLCS rights review.
   This client never asserts that a government data-use agreement was granted. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let lastNasa = null;
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function status(id,text,issue=false) {
    const target=$(id); if(!target) return;
    target.textContent = text;
    target.dataset.issue = String(Boolean(issue));
  }
  function el(tag,text){const node=document.createElement(tag);node.textContent=String(text);return node;}
  async function readJson(res){
    let data={};try{data=await res.json();}catch{}
    if(!res.ok) throw new Error(typeof data.detail==='string'?data.detail:`Request failed (HTTP ${res.status}).`);
    return data;
  }
  function safeNumber(id,min,max){const n=Number($(id).value);if(!Number.isFinite(n)||n<min||n>max)throw new Error(`Invalid ${id}; use a value from ${min} to ${max}.`);return n;}
  function download(name,object){
    const url=URL.createObjectURL(new Blob([JSON.stringify(object,null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1200);
  }
  async function permissionCheck(){
    const btn=$('p23-check-rights'); btn.disabled=true;
    status('p23-rights-result','Reviewing user declaration — not contacting PHIVOLCS…');
    try {
      const payload={intended_use:$('p23-purpose').value,agreement_reference:$('p23-agreement').value.trim(),
        signed_agreement_attested:$('p23-signed').checked,
        explicit_redistribution_permission_attested:$('p23-public').checked,
        official_layer_loaded_by_user:Boolean($('h22-file')?.files?.length)};
      const response=await fetch('/api/phase23/phivolcs/permission-review',{
        method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const info=await readJson(response);
      const block=$('p23-rights-result');block.replaceChildren();
      block.appendChild(el('strong',info.status.replaceAll('_',' ').toUpperCase()));
      block.appendChild(el('p','Official agency approval granted by app: NO. Agreement status is self-reported only.'));
      const ul=document.createElement('ul');
      info.warnings.forEach(t=>ul.appendChild(el('li',t)));block.appendChild(ul);
      block.dataset.issue='true';
    } catch(e){status('p23-rights-result','Permission review error: '+e.message,true);}
    finally {btn.disabled=false;}
  }
  function savedFarm(){const saved=window.AgriOrbitGetFarm?.();return saved?.farm || null;}
  function useFarm(){const farm=savedFarm();
    if(!farm || !Number.isFinite(Number(farm.latitude)) || !Number.isFinite(Number(farm.longitude))){
      status('p23-nasa-result','Save a valid field location in Farm Profile first. The existing default is an illustrative area coordinate.',true);return;
    }
    $('p23-lat').value=Number(farm.latitude).toFixed(5);
    $('p23-lon').value=Number(farm.longitude).toFixed(5);
    status('p23-nasa-result','Using saved farm coordinates. POWER still represents a regional grid, not direct plot measurements.');
  }
  function populateMonths(rows){const target=$('p23-months');target.replaceChildren();
    for (const row of rows){
      const tr=document.createElement('tr');
      const rain=row.precipitation_mm===null?'missing':String(row.precipitation_mm)+(row.precipitation_is_partial?' *':'');
      [MONTHS[row.month-1]||String(row.month),rain,row.temperature_c??'missing',
       (row.coverage_pct_by_variable?.PRECTOTCORR??0)+'%'].forEach(v=>tr.appendChild(el('td',v)));
      target.appendChild(tr);
    }
  }
  function presentNasa(info){
    const meta=info.metadata;
    const desc=meta.access==='cached_official_response'?'CACHED NASA RESPONSE':'NEW NASA API DOWNLOAD';
    const block=$('p23-nasa-result');block.replaceChildren();
    const head=el('strong',desc+' — '+info.year);block.appendChild(head);
    const lines=[
      `Provider: ${meta.provider} | ${meta.product}`,
      `Source type: ${meta.source_type} | Retrieved: ${meta.retrieved_at}`,
      `Location: ${meta.coordinates.latitude}, ${meta.coordinates.longitude}`,
      `Annual precipitation quality gate: ${info.annual_quality_gate.annual_precipitation_ready?'PASS':'INSUFFICIENT COVERAGE'}`,
      `Annual rainfall: ${info.annual_summary.annual_precipitation_mm??'withheld'} mm`,
      `Daily observations in cache: ${info.daily_records}`,
      `Raw payload SHA-256: ${meta.raw_payload_sha256}`,
      `Official request URL: ${meta.request_url}`,
      meta.retrieval_warning||'No retrieval warnings returned.',
      'Historical regional context, not a field gauge, current lahar warning, or planting recommendation.'
    ];
    lines.forEach(line=>block.appendChild(el('p',line)));
    block.dataset.issue=String(!info.annual_quality_gate.annual_precipitation_ready);
    populateMonths(info.monthly);
  }
  async function fetchNasa(){
    const btn=$('p23-fetch-nasa');btn.disabled=true;lastNasa=null;$('p23-export-nasa').disabled=true;
    status('p23-nasa-result','Connecting to the official NASA POWER API... This requires internet access; no synthetic fallback.');
    try{
      const lat=safeNumber('p23-lat',-90,90),lon=safeNumber('p23-lon',-180,180),year=safeNumber('p23-year',1981,2025);
      if(!Number.isInteger(year))throw new Error('Year must be a whole number.');
      const q=new URLSearchParams({lat:String(lat),lon:String(lon),year:String(year),include_daily:'true'});
      const res=await fetch('/api/phase23/nasa/observations?'+q.toString(),{cache:'no-store'});
      const info=await readJson(res);
      if(info.data_class!=='historical_nasa'||!['nasa_api','nasa_cached'].includes(info.metadata?.source_type))
        throw new Error('Response was not confirmed as a NASA API or NASA cache record.');
      lastNasa=info;$('p23-export-nasa').disabled=false;presentNasa(info);
    }catch(e){status('p23-nasa-result','NASA POWER retrieval unavailable: '+e.message+'. No synthetic data were substituted.',true);$('p23-months').replaceChildren(el('tr',''));const td=el('td','No NASA evidence available.');td.colSpan=4;$('p23-months').firstChild.appendChild(td);}
    finally{btn.disabled=false;}
  }
  function init(){if(!$('p23-fetch-nasa'))return;
    $('p23-check-rights').addEventListener('click',permissionCheck);
    $('p23-use-farm').addEventListener('click',useFarm);
    $('p23-fetch-nasa').addEventListener('click',fetchNasa);
    $('p23-export-nasa').addEventListener('click',()=>{if(lastNasa)download(`AgriORBIT_Phase23_NASA_POWER_${lastNasa.year}_Evidence.json`,lastNasa);});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

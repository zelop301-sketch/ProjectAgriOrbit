/* Phase 21 evidence-gated science tools. No client-provided NASA provenance. */
'use strict';
(() => {
  const $s = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const getFarm = () => window.AgriOrbitGetFarm?.()?.farm;
  let lastScreening = null;
  const text = (id,message) => { if($s(id)) $s(id).textContent = message; };
  const number = v => Number.isFinite(v) ? v.toFixed(1) : '—';
  async function api(path, payload) {
    const res=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const body=await res.json();
    if(!res.ok) {const detail=body.detail;throw new Error(typeof detail==='string' ? detail : JSON.stringify(detail || `HTTP ${res.status}`));}
    return body;
  }
  function toggleBusy(busy) {
    for(const id of ['science21-run-nasa','science21-run-demo']) $s(id).disabled=busy;
  }
  function renderScreen(report) {
    const view=report.scientific_screening;
    const b=report.benchmark;
    const demo=b.data_class==='synthetic_demo';
    const actual=b.status==='ready' && b.data_class==='historical_nasa';
    const badge=$s('science21-state');
    badge.textContent=demo?'SYNTHETIC / NOT NASA':actual?'NASA HISTORY / NOT PLANTING READY':'DATA INSUFFICIENT';
    badge.style.color=actual?'#a6ffd1':'#ffd780';
    const gates=view.quality_gates.map(g=>`${g.passed?'✓':'○'} ${g.key.replaceAll('_',' ')}: ${g.passed?'gate passed':'not verified'}`).join('\n');
    text('science21-screen-status',`Source: ${b.data_class}. 3-month historic rainfall departure: ${view.historical_climate.rainfall_anomaly_pct===null?'not available':number(view.historical_climate.rainfall_anomaly_pct)+'%'}.\n${gates}\nNO PLANTING AUTHORIZATION. Checked source and quality gates only; NASA POWER spatial grid is not a plot rain gauge.`);
    $s('science21-screen-status').style.whiteSpace='pre-line';
    $s('science21-screen-results').innerHTML=`<div class="science21-scenarios">${view.scenarios.map(sc=>`
      <article class="science21-scenario"><h4>${esc(sc.scenario_id)} — ${esc(sc.title)}</h4>
      <div class="science21-tags"><span>${esc(sc.screening_status.replaceAll('_',' ').toUpperCase())}</span><span>NOT A YIELD FORECAST</span></div>
      <p>${esc(sc.crops.join(' → '))}</p>
      <p><b>Reviewed conflicts:</b> ${sc.constraints_from_reviewed_rules.length?esc(sc.constraints_from_reviewed_rules.join('; ')):'None demonstrated — not proof of suitability.'}</p>
      <p><b>Evidence gaps / precautions</b></p><ul>${sc.missing_and_precautions.slice(0,7).map(n=>`<li>${esc(n)}</li>`).join('')}</ul>
      <p>Legacy prototype score: ${esc(sc.legacy_illustrative_score)} / 100 — <b>not used for scientific screening.</b></p></article>`).join('')}</div>`;
    $s('science21-export').disabled=false;
  }
  async function runScreen(mode) {
    const farm=getFarm();if(!farm){text('science21-screen-status','Save a farm profile first.');return;}
    let crop_rules;
    try {crop_rules=JSON.parse($s('science21-rules').value||'[]');if(!Array.isArray(crop_rules))throw new Error('Rule JSON must be an array.');}
    catch(e){text('science21-screen-status','Invalid crop rules JSON: '+e.message);return;}
    toggleBusy(true);text('science21-screen-status',mode==='nasa'?'Loading NASA POWER multi-year history and checking 95% daily coverage (this can require internet and time)…':'Preparing SYNTHETIC rehearsal only — no NASA record will be claimed…');
    try{
      const year=Number($s('precision-year')?.value||2025),years=Number($s('precision-years')?.value||5);
      lastScreening=await api('/api/science/screen',{farm,end_year:year,baseline_years:years,mode,crop_rules});
      renderScreen(lastScreening);
    }catch(e){lastScreening=null;$s('science21-export').disabled=true;text('science21-screen-status','Screening unavailable: '+e.message+' No synthetic data substituted.');}
    finally{toggleBusy(false);}
  }
  function exportReport(){if(!lastScreening)return;const b=new Blob([JSON.stringify(lastScreening,null,2)],{type:'application/json'}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='AgriORBIT_Phase21_Evidence.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  function parseReadings() {
    const raw=$s('science21-gauge-data').value.trim().split(/\n/).filter(Boolean);
    if(!raw.length)throw new Error('Supply at least one YYYY-MM-DD,mm line.');
    return raw.map((line,i)=>{const m=line.trim().match(/^(\d{4}-\d{2}-\d{2}),\s*(\d+(?:\.\d+)?)\s*$/);if(!m)throw new Error(`Invalid reading on line ${i+1}.`);return {day:m[1],precipitation_mm:Number(m[2])};});
  }
  async function gauge(mode){
    try{const farm=getFarm();if(!farm)throw new Error('Save farm profile first.');
      text('science21-gauge-results','Pairing gauge and NASA historical records…');
      const result=await api('/api/science/validate/rainfall',{latitude:farm.latitude,longitude:farm.longitude,
        year:Number($s('precision-year')?.value||2025),gauge_id:$s('science21-gauge-id').value,
        gauge_calibrated:$s('science21-gauge-calibrated').checked,mode,observations:parseReadings()});
      text('science21-gauge-results',`${result.source_type} • ${result.paired_days}/${result.total_gauge_days} daily pairs.\n${result.statistics?`MAE ${result.statistics.mae_mm} mm/day; bias (POWER−gauge) ${result.statistics.bias_power_minus_gauge_mm} mm/day; RMSE ${result.statistics.rmse_mm} mm/day`:'At least 5 matched days required for metrics.'}\nGauge identity and calibration are self-reported; these error statistics are not a model certificate.`);
      $s('science21-gauge-results').style.whiteSpace='pre-line';
    }catch(e){text('science21-gauge-results','Cannot validate: '+e.message);}
  }
  async function water(){
    const v=id=>Number($s(id).value);
    try{const result=await api('/api/science/water-balance',{period_days:v('sw-days'),starting_storage_mm:v('sw-start'),soil_capacity_mm:v('sw-capacity'),precipitation_mm:v('sw-rain'),irrigation_mm:v('sw-irrigation'),etc_mm:v('sw-etc'),runoff_mm:v('sw-runoff'),drainage_mm:v('sw-drainage'),source_type:'user_entered'});
      text('science21-water-results',`Change in storage: ${result.net_change_mm} mm; ending storage before bounds: ${result.unbounded_end_storage_mm} mm. Accounted bounded storage: ${result.bounded_storage_mm} mm. Unaccounted shortfall/excess: ${result.unaccounted_shortfall_mm} / ${result.unaccounted_excess_mm} mm.\nThis is user-supplied arithmetic, not a calibrated NASA water model or irrigation instruction.`);
      $s('science21-water-results').style.whiteSpace='pre-line';
    }catch(e){text('science21-water-results','Budget validation failed: '+e.message);}
  }
  async function findHls(){
    const farm=getFarm();if(!farm)return text('science21-hls-results','Save farm profile first.');
    text('science21-hls-results','Searching NASA CMR metadata. No raster pixels will be downloaded…');
    const params=new URLSearchParams({product:$s('science21-product').value,lat:String(farm.latitude),lon:String(farm.longitude),year:String($s('precision-year')?.value||2025)});
    try{const resp=await fetch('/api/earth/granules?'+params);const r=await resp.json();if(!resp.ok)throw new Error(r.detail||'Unavailable');
      text('science21-hls-results',`NASA catalog only · ${r.granules.length} granules (max 3 shown).\n${r.granules.map(g=>`${g.time_start||'unknown date'} · ${g.title}`).join('\n')}\nNo raster data ingested or NDVI established. Obtain authenticated COGs and use optional script with Fmask.`);
      $s('science21-hls-results').style.whiteSpace='pre-line';
    }catch(e){text('science21-hls-results','NASA HLS catalog unavailable: '+e.message);}
  }
  async function readHlsFile(e){const file=e.target.files?.[0];if(!file)return;
    if(file.size>200000)return text('science21-hls-results','Report exceeds 200 KB; rejected.');
    try{const d=JSON.parse(await file.text());if(d.product!=='NASA HLS v2 (user-supplied local COG bands)')throw new Error('Not a Phase 21 HLS report.');
      text('science21-hls-results',`USER-SUPPLIED HLS REPORT — NOT VERIFIED. Clear pixels: ${d.clear_valid_pixels}/${d.field_pixels_total} (${d.valid_pixel_coverage_pct}%). Median NDVI: ${d.ndvi_median??'—'}. Field statistic usable under prototype QA? ${d.field_statistic_usable?'YES (not crop suitability)':'NO'}. Product provenance and farm boundary must be independently checked.`);
    }catch(error){text('science21-hls-results','Cannot parse report: '+error.message);}
  }
  function init(){if(!$s('science21-lab'))return;
    document.querySelectorAll('[data-science-panel]').forEach(btn=>btn.addEventListener('click',()=>{
      document.querySelectorAll('[data-science-panel]').forEach(x=>{const active=x===btn;x.classList.toggle('active',active);x.setAttribute('aria-selected',String(active));});
      ['screen','validation','water','imagery'].forEach(panel=>$s('science21-'+panel).hidden=btn.dataset.sciencePanel!==panel);
    }));
    $s('science21-run-nasa').addEventListener('click',()=>runScreen('nasa'));
    $s('science21-run-demo').addEventListener('click',()=>runScreen('synthetic'));
    $s('science21-export').addEventListener('click',exportReport);
    $s('science21-gauge-run').addEventListener('click',()=>gauge('nasa'));
    $s('science21-gauge-demo').addEventListener('click',()=>gauge('synthetic'));
    $s('science21-water-run').addEventListener('click',water);
    $s('science21-hls-find').addEventListener('click',findHls);
    $s('science21-hls-file').addEventListener('change',readHlsFile);
  }
  window.addEventListener('DOMContentLoaded',init);
})();

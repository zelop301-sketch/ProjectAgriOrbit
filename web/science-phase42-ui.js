/* Phase 42 additive seasonal science view: never alters the original mission-control dashboard. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let last = null;
  const crops = ['Rice','Corn','Mungbean'];
  const node = (tag, className, content) => {
    const n = document.createElement(tag);
    if (className) n.className = className;
    if (content !== undefined) n.textContent = String(content);
    return n;
  };
  const say = (parent, tag, cls, text) => { const n=node(tag,cls,text);parent.append(n);return n; };
  const num = (v,dec=1) => Number.isFinite(v) ? (Math.abs(Number(v))<0.000001?0:Number(v)).toLocaleString('en-US',{maximumFractionDigits:dec,minimumFractionDigits:dec}) : 'Not available';
  const range = (metric,unit) => metric ? `Historical P10–P90: ${num(metric.p10)}–${num(metric.p90)} ${unit}` : 'Insufficient complete historical seasons';

  function parseStages(crop) {
    const value = $('kc-'+crop).value.trim();
    if (!value) return null;
    const stages = value.split(',').map(s => {
      const fields=s.split(':');
      if (fields.length!==2 || fields.some(v=>!v.trim() || !Number.isFinite(Number(v)))) throw Error(`${crop}: use days:Kc,days:Kc`);
      return {days:Number(fields[0]),kc:Number(fields[1])};
    });
    const source_url = $('url-'+crop).value.trim();
    if (!/^https:\/\/[^\s/]+\.[^\s/]+/.test(source_url)) throw Error(`${crop}: enter a public HTTPS agronomy source URL (not independently verified)`);
    return {
      stages,source_url,source_title:$('title-'+crop).value.trim()||null,
      source_publisher:$('publisher-'+crop).value.trim()||null,
      crop_variety:$('variety-'+crop).value.trim()||null,
      review_note:'User-entered values; source content, crop stages and local applicability NOT independently reviewed'
    };
  }

  function getRequest() {
    const q = {};
    for (const id of ['mode','location_source','irrigation','soil','farmer_priority']) q[id]=$(id).value;
    for (const id of ['latitude','longitude','planting_month','planting_day','gap_days']) {
      if (!$(id).value.trim()) throw Error(`Enter ${id.replaceAll('_',' ')}`);
      q[id]=Number($(id).value);
    }
    q.crop_days={};q.crop_profiles={};
    for (const crop of crops) {
      const raw=$(crop).value;
      if (!raw.trim()) throw Error(`Enter duration for ${crop}`);
      q.crop_days[crop]=Number(raw);
      const profile=parseStages(crop);
      if (profile) q.crop_profiles[crop]=profile;
    }
    return q;
  }

  function stat(label,value) {
    const n=node('div','stat');say(n,'div','muted',label);say(n,'b','',value);$('stats').append(n);
  }
  function metric(parent,label,value,subtitle,unavailable=false) {
    const box=node('div','measurement');say(box,'div','label-row',label);
    say(box,'strong',unavailable?'unavailable':'',value);
    say(box,'small','',subtitle);
    parent.append(box);
  }
  function displayCard(item,index) {
    const card=node('article','rotation-card');
    const head=node('div','rotation-head');
    say(head,'div','rotation-number',`ROTATION ${String(index+1).padStart(2,'0')} / HISTORICAL SCREENING`);
    say(head,'h3','',item.name||item.id);
    say(head,'div','rotation-timing',`${item.crop_days_per_rotation??'—'} occupied crop days · does not count fallow gap`);
    card.append(head);
    const rain=item.historical_rain_mm;
    metric(card,'Historical rainfall across occupied crop days',rain?`${num(rain.median)} mm`:'Withheld',range(rain,'mm'),!rain);
    const perDay=item.historical_rain_mm_per_crop_day;
    metric(card,'Historical rainfall per occupied crop day (duration-normalised)',perDay?`${num(perDay.median,2)} mm/day`:'Withheld',range(perDay,'mm/day'),!perDay);
    const eto=item.historical_eto_mm;
    metric(card,'FAO-56 reference evapotranspiration (ET₀)',eto?`${num(eto.median)} mm`:'Withheld',range(eto,'mm'),!eto);
    const dry=item.historical_longest_dry_spell_days_lt_1mm;
    metric(card,'Longest dry spell per historical growing window',dry?`${num(dry.median)} days`:'Withheld',dry?`${range(dry,'days')} · daily rainfall <1 mm`:'A complete rainfall record is needed',!dry);
    const etc=item.illustrative_et_c_mm;
    metric(card,'Conditional crop evapotranspiration (ETc)',etc?`${num(etc.median)} mm`:(item.valid_eto_years<8?'WITHHELD — ETo incomplete':'WITHHELD — sourced Kc needed'),etc?`${range(etc,'mm')} · unverified user-supplied Kc, not irrigation demand`:'Requires a complete sourced Kc schedule for both crops AND complete meteorological seasons',!etc);
    if (etc) say(card,'div','source-tag','ETc MODEL: Kc provenance user supplied / NOT independently reviewed');
    const check=node('div','check-panel');say(check,'b','','');
    check.querySelector('b').textContent='FIELD CHECKS BEFORE ANY FARM DECISION';
    const ul=node('ul');
    (item.farmer_field_checks||[]).forEach(line=>say(ul,'li','',line));
    check.append(ul);card.append(check);
    return card;
  }

  function sourceReceipt(result) {
    const p=result.provenance||{}, b=$('receipt-meta');b.replaceChildren();
    const line=node('div','receipt-source');
    say(line,'div','',`Source type: ${p.source_type||'unavailable'} · Retrieval time: ${p.retrieved_at||'NONE — synthetic example'} · Location: ${result.location?.coordinate_source||'unknown'}`);
    if (p.request_url && /^https:\/\/power\.larc\.nasa\.gov\//.test(p.request_url)) {
      const a=node('a','','Open source NASA POWER query');a.href=p.request_url;a.target='_blank';a.rel='noopener noreferrer';line.append(a);
    } else say(line,'div','',`NASA source URL: not available${result.data_class==='SYNTHETIC_REHEARSAL_NOT_NASA'?' (synthetic demonstration)':''}`);
    say(line,'div','',`NASA raw-payload SHA-256: ${p.raw_payload_sha256||'NONE — not NASA data'}`);
    b.append(line);
    $('receipt').textContent=JSON.stringify(result,null,2);
  }

  function render(result) {
    last=result;
    const isSynthetic=result.data_class==='SYNTHETIC_REHEARSAL_NOT_NASA';
    const pill=$('source-pill');pill.className='source-pill '+(isSynthetic?'synthetic':'nasa');
    pill.textContent=isSynthetic?'SYNTHETIC DEMO — NOT NASA':'NASA POWER HISTORICAL DATA';
    $('results').classList.remove('hide');
    $('disclaimer').textContent=isSynthetic
      ? 'SYNTHETIC REHEARSAL ONLY: all climate observations are fabricated. Do not show as observed NASA results, farmer impact, rainfall evidence, or operational recommendations.'
      : 'NASA POWER HISTORY: gridded historical conditions, not verified plot readings, forecasts, crop suitability, or planting recommendations. Verify source receipt and temporal coverage.';
    $('stats').replaceChildren();
    stat('Planting cohorts',result.years?.planting_cohorts||'Unknown');
    stat('Coordinates',`${num(result.location?.latitude,4)}, ${num(result.location?.longitude,4)}`);
    stat('Input location',result.location?.coordinate_source==='farmer_report'?'Farmer-reported · unverified':'Town reference · not field');
    stat('Historical seasons required',`${result.years?.minimum_complete_seasons||'—'} of 10`);
    stat('Source type',result.provenance?.source_type||'Not available');
    stat('Suitability',result.validated_crop_recommendation?'Validated':'NOT VALIDATED');
    const body=$('rotations');body.replaceChildren();
    const items=result.candidates||[];
    if (!items.length) say(body,'p','', 'Comparison unavailable: no crop-rotation results returned.');
    for (const [index,item] of items.entries()) body.append(displayCard(item,index));
    sourceReceipt(result);
    $('export').disabled=false;
  }

  $('location_source').addEventListener('change',()=>{
    if ($('location_source').value==='botolan_reference') { $('latitude').value='15.289';$('longitude').value='120.024'; }
  });
  for (const coord of ['latitude','longitude']) $(coord).addEventListener('input',()=>{
    if ($('location_source').value==='botolan_reference' && (Number($('latitude').value)!==15.289||Number($('longitude').value)!==120.024)) $('location_source').value='farmer_report';
  });
  $('run').addEventListener('click',async()=>{
    const btn=$('run');btn.disabled=true;last=null;$('export').disabled=true;$('results').classList.add('hide');
    $('status').textContent='Checking historical growing-season coverage and source provenance…';
    try {
      const request=getRequest();
      const res=await fetch('/api/botolan/seasonal',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request)});
      const result=await res.json();
      if (!res.ok) throw Error(typeof result.detail==='string'?result.detail:JSON.stringify(result.detail||result));
      render(result);
      $('status').textContent='Analysis complete. Review the field constraints and source receipt before exporting.';
      $('results').scrollIntoView({behavior:'smooth',block:'start'});
    } catch(e) {
      $('status').textContent='Analysis withheld — '+e.message+'. No earlier result or synthetic substitute was retained.';
    } finally { btn.disabled=false; }
  });
  $('export').addEventListener('click',()=>{
    if (!last) return;
    const blob=new Blob([JSON.stringify(last,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;
    a.download=last.data_class==='SYNTHETIC_REHEARSAL_NOT_NASA'?'AgriORBIT_SYNTHETIC_NOT_NASA_evidence.json':'AgriORBIT_NASA_POWER_seasonal_evidence.json';
    document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
})();

/* Phase 33 • Botolan Field Shift — a NASA-when-fetched, provenance-first judge demo.
   No browser-provided NASA JSON; the server obtains and validates responses. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct'];
  const REFERENCE = '2021–2025 matching-month mean (not climate normal)';
  const OPTIONS = [
    ['Rice → Rice','Continuous paddy sequence','Assess water access across both seasons; a second rice crop is NOT presumed feasible.'],
    ['Rice → Mungbean','Diversification candidate','Review rice harvest date, mungbean planting calendar, drainage and irrigation before considering it.'],
    ['Corn → Mungbean','Alternative sequence','Confirm maize water demand, suitable soils, planting dates and local market feasibility.'],
  ];
  let data = null;
  let controller = null;
  let previousMode = null;
  let initiated = false;

  function num(value, n=1) { return typeof value==='number' && Number.isFinite(value) ? value.toFixed(n) : '—'; }
  function text(id, value) { const el=$(id); if(el)el.textContent=String(value); }
  function elt(tag, attrs={}, children=[]) {
    const e = document.createElement(tag);
    for(const [k,v] of Object.entries(attrs)) {
      if(k==='class') e.className=v;
      else if(k==='text') e.textContent=String(v);
      else e.setAttribute(k,String(v));
    }
    for(const child of children)e.append(child);
    return e;
  }
  function empty(id, message) { const e=$(id); if(e)e.replaceChildren(elt('div',{class:'b33-chart-empty',text:message})); }
  function state(message,isError=false) {
    const e=$('b33-status'); if(!e)return;
    e.textContent=message;
    e.classList.toggle('b33-error',isError);
  }
  function setLoading(loading) {
    $('b33-fetch').disabled=loading;
    $('b33-demo').disabled=loading;
    $('b33-export').disabled=loading || !data;
    if(loading)state('Requesting NASA POWER on the server. The six calendar years may take some time; values will appear only after evidence quality checks.');
  }
  function chart(id, targetKey, referenceKey, unit, baseline=0) {
    const e=$(id); if(!e)return;
    if(!data || !Array.isArray(data.months)) {empty(id,'No verified climate data loaded.'); return;}
    const rows=data.months;
    const vals=rows.flatMap(r=>[r[targetKey],r[referenceKey]]).filter(v=>typeof v==='number'&&Number.isFinite(v));
    if(!vals.length) {empty(id,'No months passed the NASA quality gate. Insufficient evidence.');return;}
    const yMin=targetKey.includes('temp')?Math.floor(Math.min(...vals)-1):baseline;
    const yMax=targetKey.includes('temp')?Math.ceil(Math.max(...vals)+1):Math.ceil((Math.max(...vals)*1.12||10)/10)*10;
    const X=i=>54+i*(666/9), Y=v=>199-(v-yMin)/Math.max(0.5,yMax-yMin)*156;
    const NS='http://www.w3.org/2000/svg';
    const svg=document.createElementNS(NS,'svg'); svg.setAttribute('viewBox','0 0 760 238');svg.setAttribute('role','img');
    svg.setAttribute('aria-label', `Plot of ${unit}, monthly ${data.data_class==='SYNTHETIC_DEMO_NOT_NASA'?'synthetic simulated':'NASA POWER observed'} 2026 and reference, January to October. Missing months are gaps.`);
    const node=(type,attributes={},content)=>{
      const n=document.createElementNS(NS,type);
      Object.entries(attributes).forEach(([key,val])=>n.setAttribute(key,String(val)));
      if(content!==undefined)n.textContent=String(content);
      svg.appendChild(n);
      return n;
    };
    node('rect',{x:0,y:0,width:760,height:238,fill:'transparent'});
    for(let j=0;j<=4;j++){
      const value=yMin+(yMax-yMin)*j/4, y=Y(value);
      node('line',{x1:53,y1:y,x2:730,y2:y,stroke:'#285360','stroke-width':0.7});
      node('text',{x:45,y:y+4,fill:'#abcbd1','font-size':11,'text-anchor':'end'},num(value,unit==='mm'?0:1));
    }
    node('text',{x:13,y:24,fill:'#a9dbdf','font-size':11},unit);
    MONTHS.forEach((m,i)=>node('text',{x:X(i),y:226,fill:'#b2cbd1','font-size':12,'text-anchor':'middle'},m));
    const draw=(key,color,opacity)=>{
      let segment=[];
      function flush(){
        if(segment.length>1)node('polyline',{points:segment.join(' '),fill:'none',stroke:color,'stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round',opacity});
        segment=[];
      }
      rows.forEach((row,i)=>{
        const v=row[key];
        if(typeof v!=='number'||!Number.isFinite(v)){flush();return;}
        const x=X(i),y=Y(v);
        segment.push(`${x.toFixed(1)},${y.toFixed(1)}`);
        node('circle',{cx:x,cy:y,r:key===targetKey?3.8:3,fill:color,opacity});
      });flush();
    };
    draw(referenceKey,'#42d8eb',0.95);
    draw(targetKey,'#74f6a6',1);
    e.replaceChildren(svg);
  }
  function renderScenarios() {
    const host=$('b33-rotations');if(!host)return;
    const irrigation=$('b33-irrigation')?.value||'limited';
    const soil=$('b33-soil')?.value||'unknown';
    const anomaly=data?.summary?.rain_anomaly_pct;
    host.replaceChildren();
    const waterNote=irrigation==='none'?'Rainfed field: planting dates and confirmed local rainfall are essential.':irrigation==='limited'?'Limited irrigation: quantify available water before comparing sequences.':'Reliable irrigation reported by farmer; supply, costs and field verification remain unverified.';
    const soilNote=soil==='unknown'?'Soil not tested: all soil suitability remains unknown.':`Farmer-reported ${soil} soil is unverified; laboratory/extension confirmation is needed.`;
    const climateNote=typeof anomaly==='number' && previousMode==='nasa' ?
      (anomaly < -10 ? `NASA Jan–Oct rain was ${Math.abs(anomaly).toFixed(1)}% below the five-year same-month reference; discuss water exposure, not drought attribution.`:
       `NASA Jan–Oct rain was ${num(anomaly)}% versus the five-year same-month reference; do not assume local water is sufficient.`):
      previousMode==='synthetic'?'Only synthetic rehearsal is available: no current farm-water conclusion.':'No validated local climate conclusion has been loaded.';
    OPTIONS.forEach(([title,focus,question],i)=>{
      const item=elt('article',{class:'b33-rotation'});
      item.append(elt('span',{class:'b33-rotation-num',text:`0${i+1}`}));
      const body=elt('div',{});
      body.append(elt('h3',{text:title}),elt('small',{text:focus}),elt('p',{text:question}));
      item.append(body,elt('span',{class:'b33-need-review',text:'REVIEW NEEDED'}));
      host.append(item);
    });
    const insight=$('b33-insight');insight.replaceChildren();
    insight.append(elt('strong',{text:'Evidence-led discussion, not a crop recommendation'}),
      elt('p',{text:climateNote}),elt('p',{text:waterNote}),elt('p',{text:soilNote}));
  }
  function renderTable() {
    const body=$('b33-table');body.replaceChildren();
    if(!data){body.append(elt('tr',{},[elt('td',{colspan:6,text:'Awaiting NASA observations or an explicitly synthetic rehearsal.'})]));return;}
    for(const row of data.months){
      const vals=[row.label,num(row.rain_2026_mm),num(row.rain_reference_mm),
                  typeof row.rain_anomaly_pct==='number'?num(row.rain_anomaly_pct)+'%':'—',
                  num(row.target_rain_coverage_pct,0)+'%',String(row.valid_reference_years)+'/5'];
      const tr=elt('tr');
      vals.forEach((v,i)=>tr.append(elt(i===0?'th':'td',i===0?{scope:'row',text:v}:{text:v})));
      if(!row.has_comparison)tr.classList.add('b33-missing');
      body.append(tr);
    }
  }
  function renderProvenance() {
    const target=$('b33-sources');target.replaceChildren();
    if(!data)return;
    for(const item of data.provenance||[]){
      const div=elt('div',{class:'b33-source-row'});
      div.append(elt('strong',{text:`${item.year} · ${item.source_type||'unknown'}`}));
      div.append(elt('span',{text:`Retrieved: ${item.retrieved_at||'not available'} · SHA-256: ${item.sha256||'not available (modified rehearsal)'}`}));
      if(previousMode==='nasa'&&item.request_url){
        try{
          const url=new URL(item.request_url);
          if(url.protocol==='https:'&&url.hostname==='power.larc.nasa.gov'){
            const a=elt('a',{href:url.toString(),target:'_blank',rel:'noopener noreferrer',text:'Original POWER request ↗'});
            div.append(a);
          }
        }catch{/* URL omitted */}
      }
      target.append(div);
    }
    if(data.failed_years?.length)target.append(elt('p',{class:'b33-error',text:`Unable to retrieve: ${data.failed_years.map(y=>y.year).join(', ')}. Coverage and missing values were NOT invented.`}));
  }
  function render() {
    const demo=previousMode==='synthetic';
    text('b33-source', !data?'NO NASA DATA LOADED':demo?'SYNTHETIC · NOT NASA':'NASA POWER · AUDITED');
    $('b33-source').classList.toggle('b33-synthetic',demo);
    text('b33-rain-legend-recent',demo?'2026 synthetic stress scenario':'2026 NASA observation (if available)');
    text('b33-temp-legend-recent',demo?'2026 synthetic temperature scenario':'2026 NASA observation (if available)');
    if(!data){
      text('b33-anomaly','—');text('b33-anomaly-detail','Requires enough NASA observations');text('b33-coverage','— / 10');
      text('b33-trace-summary','No climate response loaded. Measurements and departures are unavailable.');
    }else{
      const sum=data.summary,available=typeof sum.rain_anomaly_pct==='number';
      text('b33-anomaly',available?`${sum.rain_anomaly_pct>0?'+':''}${num(sum.rain_anomaly_pct)}%`:'—');
      text('b33-anomaly-detail',demo?'Fabricated rainfall stress test, NOT actual 2026 rainfall':
        available?'2026 Jan–Oct vs. 2021–25 monthly mean':'No complete Jan–Oct comparison; avoid drought claims');
      text('b33-coverage',`${sum.months_usable} / ${sum.months_requested}`);
      text('b33-trace-summary',`${demo?'SYNTHETIC rehearsal only.':'NASA POWER gridded climate context.'} ${sum.signal}. Minimum 95% monthly precipitation coverage; at least three valid reference years per month. Five-year reference is NOT a climate normal. ${data.simulation_assumption||''}`);
    }
    chart('b33-rain-chart','rain_2026_mm','rain_reference_mm','mm');
    chart('b33-temp-chart','temp_2026_c','temp_reference_c','°C');
    renderScenarios();renderTable();renderProvenance();
    $('b33-export').disabled=!data;
  }
  function clear() {
    controller?.abort();controller=null;data=null;previousMode=null;
    render();setLoading(false);state('Cleared. No NASA observation is loaded. Select live NASA data or the explicitly synthetic rehearsal.');
  }
  async function load(mode) {
    controller?.abort();const own = new AbortController();controller=own;
    // Clear old NASA/synthetic values before starting a new request.
    data=null;previousMode=null;render();setLoading(true);
    const timeout=window.setTimeout(()=>own.abort(),140000);
    try{
      const resp=await fetch('/api/botolan/climate?mode='+encodeURIComponent(mode),{cache:'no-store',signal:own.signal});
      const body=await resp.json();
      if(!resp.ok)throw Error(body?.detail||'NASA POWER request failed');
      if(own.signal.aborted)return;
      if(mode==='nasa' && body.data_class!=='HISTORICAL_NASA_POWER')throw Error('Rejected response: cannot verify NASA provenance.');
      if(mode==='synthetic' && body.data_class!=='SYNTHETIC_DEMO_NOT_NASA')throw Error('Rejected rehearsal provenance mismatch.');
      data=body;previousMode=mode;
      render();
      const a=body.summary;
      state(mode==='synthetic'?'SYNTHETIC REHEARSAL ONLY: artificial 35% precipitation reduction and +1°C. No NASA observations shown.':
        `NASA POWER server response: ${a.months_usable}/10 matching months usable. ${a.signal}. ${body.failed_years?.length?'Some records unavailable; check source trace.':''}`);
    }catch(err){
      if(own.signal.aborted)return;
      data=null;previousMode=null;render();
      state('Data unavailable: '+err.message+'. No synthetic fallback occurred. Use the separate rehearsal button if needed.',true);
    }finally{
      window.clearTimeout(timeout);
      if(controller===own){controller=null;setLoading(false);}
    }
  }
  function exportBriefing() {
    if(!data)return;
    const f=$('b33-irrigation').selectedOptions[0].textContent,soil=$('b33-soil').selectedOptions[0].textContent;
    const lines=[
      '# AgriORBIT • Botolan El Niño Field Shift — Evidence Briefing','',
      `Generated UTC: ${new Date().toISOString()}`,
      `MODE: ${data.data_class}`,
      'INDEPENDENT SAMMIUM SMART LABS PROTOTYPE; NOT A NASA OR PAGASA ENDORSED RECOMMENDATION.','',
      '## Problem','Botolan farmers face uncertainty around rainfall, irrigation, and crop-rotation decisions. El Niño changes risk at broad scale but does not establish drought in a specific field.','',
      '## Official climate advisory',`DOST-PAGASA very strong El Niño in the tropical Pacific, issued 2026-11-04: ${data.advisory.source_url}`,
      'This is an official national/regional ENSO context, not a Botolan farm-level drought classification.','',
      '## NASA POWER comparison', 'Town reference coordinate: 15.289 N, 120.024 E (not a farm boundary).',
      `Window: January–October 2026 versus ${REFERENCE}.`,
      'Min. precipitation coverage 95% per month; min. 3 of 5 reference years per month.',
      `Usable matching months: ${data.summary.months_usable}/10`,
      `Total 2026 rain (if all months valid): ${num(data.summary.target_rain_jan_oct_mm)} mm`,
      `Total 2021–25 monthly mean (if all months valid): ${num(data.summary.reference_rain_jan_oct_mm)} mm`,
      `Departure: ${num(data.summary.rain_anomaly_pct)}%`,
      `Signal: ${data.summary.signal}`,
      data.simulation_assumption||'', '',
      '| Month | 2026 rain mm | Recent mean mm | Departure % | Coverage % | Reference years |',
      '|---|---:|---:|---:|---:|---:|',
      ...data.months.map(m=>`| ${m.label} | ${num(m.rain_2026_mm)} | ${num(m.rain_reference_mm)} | ${num(m.rain_anomaly_pct)} | ${num(m.target_rain_coverage_pct)} | ${m.valid_reference_years}/5 |`),
      '', '## Farmer reports (unverified)',`Irrigation: ${f}`,`Soil texture: ${soil}`,'',
      '## Rotation candidates — not scientifically ranked',
      ...OPTIONS.map(([name,focus,warning])=>`- ${name}: ${focus}; ${warning}`),
      '', '## Provenance',
      ...data.provenance.map(p=>`- ${p.year}: ${p.source_type}, ${p.retrieved_at||'unknown'}, SHA-256 ${p.sha256||'unavailable'}, ${p.request_url||'NO NASA URL: SYNTHETIC DEMO'}`),
      ...(data.failed_years||[]).map(y=>`- FAILED ${y.year}: ${y.reason}`),
      '', '## Scientific cautions',...data.cautions.map(v=>'- '+v),
      '', '## Field-validation checklist',...data.next_steps.map(v=>'- '+v),
      '', '## Attribution',data.official_challenge,data.advisory.source_url,
      'https://power.larc.nasa.gov/docs/services/api/temporal/daily/'
    ];
    const blob=new Blob([lines.join('\n')],{type:'text/markdown;charset=utf-8'});
    const url=URL.createObjectURL(blob);const a=elt('a',{href:url,download:'AgriORBIT_Botolan_Field_Shift_Evidence.md'});
    document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
    state('Auditable briefing exported. Verify sources, local farmer facts and submission requirements before sharing.');
  }
  function init(){
    if(initiated)return;initiated=true;
    $('b33-fetch')?.addEventListener('click',()=>load('nasa'));
    $('b33-demo')?.addEventListener('click',()=>load('synthetic'));
    $('b33-reset')?.addEventListener('click',clear);
    $('b33-export')?.addEventListener('click',exportBriefing);
    $('b33-irrigation')?.addEventListener('change',renderScenarios);
    $('b33-soil')?.addEventListener('change',renderScenarios);
    render();
  }
  window.AgriOrbitBotolan={init,onView(view){if(view==='botolan')init();}};
  document.addEventListener('DOMContentLoaded',init);
})();

/* AgriORBIT Phase 34 — working server-connected scientific demo.
 * All climate provenance arrives ONLY from server. This browser cannot submit a
 * purported NASA record; synthetic mode is a separate, prominently labeled route.
 */
(()=>{'use strict';
const $ = id=>document.getElementById(id);
const NAMES=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct'];
const NS='http://www.w3.org/2000/svg';
let data=null,mode=null,controller=null,debounce=null,busy=false,started=false;
let rules=[];
const fmt=(v,n=1)=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(n):'—';
const elem=(tag,cls,txt)=>{const a=document.createElement(tag);if(cls)a.className=cls;if(txt!==undefined)a.textContent=String(txt);return a;};
function text(id,value){if($(id))$(id).textContent=String(value);}
function notice(msg,error=false){text('b34-status',msg);$('b34-status')?.classList.toggle('b34-error',error);}
function farm(){
  const value=$('b34-ph').value.trim();
  const soil_ph=value===''?null:Number(value);
  if(value!==''&&(!Number.isFinite(soil_ph)||soil_ph<0||soil_ph>14))throw new Error('Soil pH must be between 0 and 14, or blank.');
  return {irrigation:$('b34-irrigation').value,soil:$('b34-soil').value,soil_ph,
          soil_source:$('b34-soil-source').value,planting_month:Number($('b34-month').value),
          priority:$('b34-priority').value,irrigation_source:'farmer_report',crop_rules:rules};
}
function buttons(loading){
 busy=loading;
 for(const id of ['b34-fetch','b34-demo','b34-reset'])if($(id))$(id).disabled=loading;
 if($('b34-report'))$('b34-report').disabled=loading||!data;
}
function renderChart(){
 const host=$('b34-chart');if(!host)return;host.replaceChildren();
 const rows=data?.evidence?.months;
 if(!rows){host.append(elem('p',null,'Awaiting NASA climate observations or an explicitly synthetic rehearsal.'));return;}
 const vals=rows.flatMap(r=>[r.rain_2026_mm,r.rain_reference_mm]).filter(v=>typeof v==='number'&&Number.isFinite(v));
 if(!vals.length){host.append(elem('p',null,'Insufficient coverage: no verified rainfall comparison is available.'));return;}
 const svg=document.createElementNS(NS,'svg');svg.setAttribute('viewBox','0 0 740 228');
 svg.setAttribute('role','img');svg.setAttribute('aria-label',(mode==='synthetic'?'Synthetic rehearsal':'NASA POWER')+' monthly rainfall values for 2026 and 1991–2020 reference; missing data shown as gaps.');
 const shape=(type,props,content)=>{const e=document.createElementNS(NS,type);for(const [k,v] of Object.entries(props||{}))e.setAttribute(k,String(v));if(content!==undefined)e.textContent=String(content);svg.appendChild(e);return e;};
 const max=Math.max(10,...vals)*1.13,Y=v=>188-v/max*154,X=i=>52+i*666/9;
 for(let i=0;i<=4;i++){
   const val=max*i/4,y=Y(val);
   shape('line',{x1:52,y1:y,x2:724,y2:y,stroke:'#285f6a','stroke-width':.8});
   shape('text',{x:46,y:y+4,'text-anchor':'end',fill:'#c5e4e1','font-size':12},fmt(val,0));
 }
 NAMES.forEach((m,i)=>shape('text',{x:X(i),y:213,'text-anchor':'middle',fill:'#bde4de','font-size':12},m));
 const line=(key,color)=>{
   let prev=[];
   function flush(){if(prev.length>1)shape('polyline',{points:prev.join(' '),fill:'none',stroke:color,'stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round'});prev=[];}
   rows.forEach((r,i)=>{const v=r[key];if(typeof v!=='number'||!Number.isFinite(v)){flush();return;}
     prev.push(`${X(i).toFixed(1)},${Y(v).toFixed(1)}`);
     shape('circle',{cx:X(i),cy:Y(v),r:key==='rain_2026_mm'?4:3,fill:color});
   });flush();
 };
 line('rain_reference_mm','#49d9ef');line('rain_2026_mm','#73ffa9');
 host.append(svg);
}
function renderCandidates(){
 const host=$('b34-candidates');host.replaceChildren();
 for(const [i,s] of (data?.screening?.candidates||[]).entries()){
   const article=elem('article','b34-candidate');
   const title=elem('div','b34-candidate-head');title.append(elem('span','b34-count',`0${i+1}`),elem('h4',null,s.name),elem('span','b34-badge','REVIEW REQUIRED'));article.append(title);
   const focus=elem('p','b34-note',s.focus+' · No validated crop suitability rank.');article.append(focus);
   const highlights=elem('div','b34-flags');
   for(const f of s.flags){const item=elem('div','b34-flag b34-flag-'+f.type);
     item.append(elem('strong',null,f.label),elem('p',null,f.reason));highlights.append(item);}
   article.append(highlights);
   for(const q of s.questions)article.append(elem('p','b34-note',q));
   host.append(article);
 }
 if(!host.children.length)host.append(elem('p','b34-note','No scientific screening loaded.'));
 text('b34-sensitivity',data?.screening?.sensitivity?.explanation||'Change irrigation after loading a comparison.');
}
function renderGates(){
 const host=$('b34-gates');host.replaceChildren();
 if(!data){host.append(elem('p','b34-note','Awaiting data. No scientific gates have been passed.'));return;}
 for(const gate of data.screening.quality_gates){
   const div=elem('div','b34-gate');div.append(elem('span','b34-gate-icon',gate.passed?'✓':'!'));
   const content=elem('div');content.append(elem('strong',null,gate.name),elem('p',null,gate.note));div.append(content);host.append(div);
 }
}
function renderTrace(){
 const host=$('b34-provenance');host.replaceChildren();if(!data)return;
 const detail=data.evidence;
 for(const p of detail.provenance){
   const row=elem('div','b34-trace-row');row.append(elem('strong',null,p.label+' · '+p.source_type),
     elem('span',null,'Retrieved: '+(p.retrieved_at||'synthetic; no NASA timestamp')),
     elem('span',null,'Raw payload SHA-256: '+(p.raw_payload_sha256||'not available — simulation')));
   if(mode==='nasa'&&p.request_url){try{const u=new URL(p.request_url);
     if(u.protocol==='https:'&&u.hostname==='power.larc.nasa.gov'){
       const a=elem('a',null,'Open original NASA request ↗');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';row.append(a);
     }}catch{/*invalid or untrusted link omitted*/}}
   host.append(row);
 }
 const note=elem('p','b34-note',detail.period.reference_method+' Reference: '+detail.period.reference+'. Valid sample years are required in each month.');host.append(note);
}
function render(){
 const e=data?.evidence,screen=data?.screening;
 const synthetic=mode==='synthetic';
 text('b34-data-state',!e?'NO OBSERVATIONS LOADED':synthetic?'SYNTHETIC REHEARSAL · NOT NASA':'NASA POWER · SOURCE AUDITED');
 $('b34-data-state')?.classList.toggle('b34-synthetic',synthetic);
 text('b34-departure',typeof e?.summary?.rain_departure_pct==='number'?(e.summary.rain_departure_pct>0?'+':'')+fmt(e.summary.rain_departure_pct)+'%':'—');
 text('b34-departure-caption',!e?'30-year reference requires verified NASA records':synthetic?'FABRICATED stress scenario · not an observation':e.summary.message);
 text('b34-months',e?e.summary.months_usable+' / '+e.summary.months_requested:'— / 10');
 text('b34-coverage-caption',!e?'2026 target ≥95% daily coverage; reference ≥24/30 years':synthetic?'FABRICATED coverage for interface rehearsal only':'2026 target ≥95% daily coverage; reference ≥24/30 years');
 text('b34-signal',!e?'UNKNOWN':e.summary.signal.replaceAll('_',' '));
 text('b34-science-note',!e?'NASA POWER is gridded context; no field rainfall measured.':
  (synthetic?'SIMULATED; NOT NASA DATA. ':'30-year NASA study reference; ')+'This is not a plot-scale drought index, an El Niño causal test, or a forecast. '+e.summary.alert_threshold);
 renderChart();renderCandidates();renderGates();renderTrace();
 $('b34-report').disabled=!data||busy;
}
async function run(nextMode,quiet=false){
 if(controller)controller.abort();
 const own=new AbortController();controller=own;
 let f;try{f=farm();}catch(e){notice(e.message,true);return;}
 if(!quiet){data=null;mode=null;render();}
 mode=nextMode;buttons(true);
 notice(nextMode==='nasa'?'Requesting NASA POWER 2026 daily values and 1991–2020 monthly reference. No simulated fallback will be used.':
              'Running the clearly labeled synthetic rehearsal. These are fabricated values, NOT NASA records.');
 const timeout=setTimeout(()=>own.abort(),95000);
 try{
   const resp=await fetch('/api/botolan/decision',{method:'POST',headers:{'Content-Type':'application/json'},
     body:JSON.stringify({mode:nextMode,farm:f,refresh:false}),signal:own.signal,cache:'no-store'});
   let payload=await resp.json();
   if(!resp.ok)throw new Error(typeof payload.detail==='string'?payload.detail:`Request failed (${resp.status}).`);
   if(own!==controller)return;
   if(payload.evidence?.source_mode!==nextMode || (nextMode==='nasa'&&payload.evidence.data_class!=='HISTORICAL_NASA_POWER')||
      (nextMode==='synthetic'&&payload.evidence.data_class!=='SYNTHETIC_REHEARSAL_NOT_NASA'))throw new Error('Climate provenance mismatch: source withheld.');
   data=payload;mode=nextMode;render();
   const x=payload.evidence.summary;
   notice((nextMode==='synthetic'?'SYNTHETIC JUDGE REHEARSAL — no NASA observations. ':'NASA POWER historical comparison. ')+
     `${x.months_usable}/10 months available. Irrigation, soil, and evidence rules change review flags; no planting authorization.`);
 }catch(err){
   if(own.signal.aborted){if(own===controller)notice('Request timed out or was cancelled; no evidence was fabricated.',true);return;}
   if(own!==controller)return;
   data=null;mode=null;render();
   notice('Evidence unavailable: '+err.message+' No synthetic fallback occurred.',true);
 }finally{
   clearTimeout(timeout);
   if(own===controller){controller=null;buttons(false);render();}
 }
}
function changed(){if(!mode||busy)return;clearTimeout(debounce);debounce=setTimeout(()=>run(mode,true),180);}
function ruleList(){
 const box=$('b34-rule-list');box.replaceChildren();
 if(!rules.length){box.textContent='No user-asserted rule supplied. Crop requirements remain unverified.';return;}
 rules.forEach(r=>{const row=elem('div','b34-rule-item');row.append(elem('span',null,r.crop+' · '+(r.source_url||'No HTTPS source')+' · '+(r.reviewed_by||'Unreviewed')));
   const remove=elem('button','btn btn-muted','Remove');remove.type='button';remove.addEventListener('click',()=>{rules=rules.filter(a=>a.crop!==r.crop);ruleList();changed();});row.append(remove);box.append(row);});
}
function addRule(){
 const val=id=>$(id).value.trim(), min=val('b34-rule-phmin'),max=val('b34-rule-phmax');
 if(min&&max&&Number(min)>Number(max)){notice('Crop pH minimum cannot exceed maximum.',true);return;}
 const source=val('b34-rule-url');
 if(source&&!source.startsWith('https://')){notice('A source citation must start with https://.',true);return;}
 const crop=val('b34-rule-crop');
 const r={crop,minimum_irrigation:val('b34-rule-irrigation'),
   ph_min:min?Number(min):null,ph_max:max?Number(max):null,allowed_textures:[],
   reviewed_by:val('b34-rule-reviewer'),reviewed_on:val('b34-rule-date')||null,source_url:source};
 rules=rules.filter(a=>a.crop!==crop).concat(r);ruleList();changed();
 notice('User-asserted '+crop+' rule recorded. Reviewer details are not independently authenticated.');
}
function saveReport(){
 if(!data)return;const {evidence:e,screening:s,farm:f}=data;
 const lines=[
  '# AgriORBIT Phase 34 — Botolan Evidence-to-Farmer-Decisions', '',
  'Produced: '+new Date().toISOString(),
  'SOURCE CLASS: '+e.data_class,
  'Independent Sammium Smart Labs research prototype; NOT NASA-endorsed or planting advice.', '',
  '## Research question','How do regional historical rainfall differences and farmer-reported constraints alter questions about rotation strategies in Botolan?', '',
  '## Data and quality',`Reference: ${e.period.reference}. Target: ${e.period.target}.`,e.period.reference_method,
  'Source: '+e.summary.message, 'Usable months: '+e.summary.months_usable+'/10',
  '2026 rain Jan–Oct (mm): '+fmt(e.summary.rain_2026_jan_oct_mm),
  'Reference rain Jan–Oct (mm): '+fmt(e.summary.rain_reference_jan_oct_mm),
  'Rain departure (%): '+fmt(e.summary.rain_departure_pct),
  'Policy: '+e.summary.alert_threshold,'',
  '| Month | 2026 mm | 30-year reference mm | Difference % | 2026 daily coverage % | Valid reference years |',
  '|---|---:|---:|---:|---:|---:|',
  ...e.months.map(m=>`| ${m.label} | ${fmt(m.rain_2026_mm)} | ${fmt(m.rain_reference_mm)} | ${fmt(m.rain_departure_pct)} | ${fmt(m.target_rain_coverage_pct)} | ${m.valid_reference_years}/30 |`), '',
  '## Farmer-declared context (NOT field authenticated)','```json',JSON.stringify(f,null,2),'```','',
  '## Candidate screening (NO SUITABILITY RANKING)',
  ...s.candidates.flatMap(c=>['### '+c.name,'Status: '+c.status,...c.flags.map(x=>'- '+x.label+': '+x.reason),...c.questions.map(x=>'- '+x)]),'',
  '## Evidence quality gates',...s.quality_gates.map(g=>`- ${g.passed?'MET (self-asserted where noted)':'NOT MET'}: ${g.name} — ${g.note}`),'',
  '## Provenance',...e.provenance.flatMap(p=>[p.label,`- Source type: ${p.source_type}`,
     `- Original POWER request: ${p.request_url||'NONE: SYNTHETIC'}`,
     `- Retrieved at: ${p.retrieved_at||'not applicable'}`,
     `- Payload SHA-256: ${p.raw_payload_sha256||'not available'}`]),'',
  '## Scientific limitations',...e.warnings.map(w=>'- '+w),'',
  '## Reference sources',e.official_sources.nasa_power,e.official_sources.fao_paddy,e.official_sources.pagasa,
  'https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/'
 ];
 const blob=new Blob([lines.join('\n')],{type:'text/markdown;charset=utf-8'});
 const url=URL.createObjectURL(blob);const a=elem('a');a.href=url;a.download='AgriORBIT_Phase34_Botolan_Evidence_Report.md';
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
 notice('Evidence report exported. Confirm source coverage and farmer declarations before presenting.');
}
function init(){if(started||!$('b34-mission'))return;started=true;
 $('b34-fetch').addEventListener('click',()=>run('nasa'));
 $('b34-demo').addEventListener('click',()=>run('synthetic'));
 $('b34-reset').addEventListener('click',()=>{if(controller)controller.abort();controller=null;data=null;mode=null;buttons(false);render();notice('Results cleared; NASA observations are no longer displayed.');});
 $('b34-report').addEventListener('click',saveReport);
 $('b34-rule-add').addEventListener('click',addRule);
 for(const id of ['b34-irrigation','b34-soil','b34-ph','b34-soil-source','b34-month','b34-priority'])$(id).addEventListener('change',changed);
 render();
}
window.AgriOrbitPhase34={init,onView(v){if(v==='botolan')init();},getData:()=>data};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

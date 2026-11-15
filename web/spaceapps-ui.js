/* AgriORBIT Phase 14: NASA guideline companion. Does NOT assert NASA eligibility. */
'use strict';
(() => {
  const el = id => document.getElementById(id);
  const escaped = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const criteria = [
    ['impact','Impact','Who benefits and how?','Show a farmer problem, local feedback and limits to adoption.'],
    ['creativity','Creativity','What is genuinely original?','Use 3D visuals to reveal evidence, not just appearance.'],
    ['validity','Validity','Does the approach work scientifically?','Show provenance, reproducibility, tests and unvalidated assumptions.'],
    ['relevance','Relevance','Does NASA data drive the solution?','Trace a NASA climate source through an agricultural comparison.'],
    ['presentation','Presentation','Is the story immediately clear?','Demonstrate one farmer workflow in 30 seconds or up to 7 slides.'],
  ];
  const manualItems = [
    ['registered_same_event','All members registered for the same Local or Universal Event'],
    ['members_tab_complete','All members appear on the team Members tab'],
    ['official_challenge','The official Field Shift challenge is selected'],
    ['fields_complete','Every required Project Submission field is complete'],
    ['materials_english','Project page and linked materials are in English'],
    ['video_english_subtitles','If necessary, the non-English demo video has English subtitles'],
    ['references_verified','All external code, data, images, music and text sources are credited'],
    ['copyright_permissions_confirmed','All third-party materials have the necessary permissions'],
    ['originality_attested','The team can truthfully confirm the original-work declaration'],
    ['terms_privacy_attested','The team has reviewed and agreed to applicable Terms and Privacy Policy'],
    ['submitted_on_time','Official website submission is confirmed before the applicable deadline'],
  ];
  const fields = ['event','team','format','slides','seconds','spoken','references'];
  let initialized = false;
  let guide = null;
  let latestAudit = null;
  let timerStart = null;
  let timerAnimation = 0;
  const store = 'agriorbit-phase14-readiness-draft-v1';

  function drawRubric(){
    el('sa-rubric').innerHTML = criteria.map(([id,name,question,proof],i) => `<div class="sa-rubric-card"><div class="sa-rubric-top"><span>0${i+1}</span><h4>${escaped(name)}</h4><label for="sa-grade-${id}">Team estimate</label><select id="sa-grade-${id}" data-sa-grade="${id}" aria-label="Team estimated ${escaped(name)} score"><option value="0">Not scored</option>${[1,2,3,4,5].map(n=>`<option value="${n}">${n} / 5</option>`).join('')}</select></div><p>${escaped(question)}</p><small>${escaped(proof)}</small><label class="sa-proof-label" for="sa-proof-${id}">What is our actual evidence?</label><textarea id="sa-proof-${id}" data-sa-proof="${id}" rows="2" placeholder="Write verified evidence; otherwise leave blank."></textarea></div>`).join('');
    for (const input of document.querySelectorAll('[data-sa-grade], [data-sa-proof]')) input.addEventListener('input',()=>{updateScore();saveDraft();});
    updateScore();
  }
  function drawChecklists(){
    el('sa-checkboxes').innerHTML=manualItems.map(([id,title])=>`<label class="sa-check-row" for="sa-check-${id}"><input type="checkbox" id="sa-check-${id}" data-sa-check="${id}"><span>${escaped(title)}</span><small>Manual confirmation</small></label>`).join('');
    document.querySelectorAll('[data-sa-check]').forEach(input=>input.addEventListener('change',saveDraft));
  }
  function updateScore(){
    let total=0, n=0;
    const bars = criteria.map(([id,name])=>{
      const value=Number(el('sa-grade-'+id).value);
      if (value) {total+=value; n++;}
      return `<div class="sa-score-row"><span>${escaped(name)}</span><div class="sa-score-track"><span style="width:${value?value*20:0}%"></span></div><b>${value?value+'/5':'—'}</b></div>`;
    });
    el('sa-score-bars').innerHTML=bars.join('');
    el('sa-score-summary').innerHTML = `${n ? total : '—'} <span>/ 25 team-estimated · ${n}/5 scored</span>`;
  }
  function evidence(){
    if (!initialized) return;
    const ctx=window.AgriOrbitReadinessContext?.() || {};
    const farm=ctx.farm || {}, climate=ctx.climate || {}, comp=ctx.comparison || {};
    const source=climate.source_type;
    let nasaText='No NASA climate record loaded in this browser session.';
    let nasaStatus='missing';
    if(source==='nasa_api') {nasaStatus='partial'; nasaText=`NASA POWER historical API record loaded for ${climate.year||'selected year'}; verify source metadata and coverage.`;}
    if(source==='nasa_cached') {nasaStatus='partial'; nasaText=`Cached NASA POWER historical record loaded; verify original retrieval time and source metadata.`;}
    if(source==='synthetic') {nasaStatus='demo'; nasaText='SYNTHETIC rehearsal data loaded — not NASA evidence.';}
    const coords=Number.isFinite(Number(farm.latitude))&&Number.isFinite(Number(farm.longitude));
    const scenarios=comp.scenarios?.length || 0;
    const items=[
      {title:'NASA integration', status:nasaStatus, body:nasaText},
      {title:'Farm context',status:coords?'partial':'missing',body:coords?`Profile point: ${Number(farm.latitude).toFixed(4)}, ${Number(farm.longitude).toFixed(4)}. Farmer-entered; plot accuracy unverified.`:'Missing farm coordinates.'},
      {title:'Rotation engine',status:scenarios===3?'partial':'missing',body:scenarios===3?'Three scenarios computed; scores remain experimental, not validated agronomic predictions.':`Only ${scenarios} scenarios loaded; run the comparison.`},
      {title:'Physical rover / 3D field',status:'demo',body:'Simulated scene and telemetry; not field-measured data or autonomous hardware.'}
    ];
    el('sa-evidence-indicators').innerHTML=items.map(i=>`<div class="sa-evidence-row"><span class="sa-pill ${i.status}">${i.status==='demo'?'SIMULATED':i.status==='partial'?'REVIEW':'NOT READY'}</span><div><strong>${escaped(i.title)}</strong><p>${escaped(i.body)}</p></div></div>`).join('');
  }
  function draft(){
    const out={
      event_type:el('sa-event').value,team_size:Number(el('sa-team').value)||0,
      demo_format:el('sa-format').value,slide_count:Number(el('sa-slides').value)||0,
      video_seconds:Number(el('sa-seconds').value)||0,
      video_spoken_english:el('sa-spoken').value==='true',
      references:el('sa-references').value.split('\n').map(s=>s.trim()).filter(Boolean).slice(0,200),
    };
    for(const [id] of manualItems)out[id]=Boolean(el('sa-check-'+id)?.checked);
    return out;
  }
  function selfGrades(){
    return Object.fromEntries(criteria.map(([id])=>[id,{estimate:Number(el('sa-grade-'+id).value)||null, explanation:el('sa-proof-'+id).value.trim()}]));
  }
  function saveDraft(){
    if(!initialized)return;
    if(latestAudit){latestAudit=null;el('sa-audit-summary').textContent='Draft changed; run the self-audit again. No eligibility has been verified.';el('sa-audit-results').textContent='';}
    try {localStorage.setItem(store,JSON.stringify({draft:draft(),grades:selfGrades()}));} catch {}
  }
  function restoreDraft(){
    let data=null;
    try{data=JSON.parse(localStorage.getItem(store)||'null');}catch{}
    if(!data)return;
    for (const [name,id] of [['event_type','event'],['team_size','team'],['demo_format','format'],['slide_count','slides'],['video_seconds','seconds']])
      if(data.draft?.[name]!=null) el('sa-'+id).value=data.draft[name];
    if(data.draft?.video_spoken_english!=null)el('sa-spoken').value=String(data.draft.video_spoken_english);
    if(Array.isArray(data.draft?.references))el('sa-references').value=data.draft.references.join('\n');
    for(const [id] of manualItems)if(el('sa-check-'+id))el('sa-check-'+id).checked=Boolean(data.draft?.[id]);
    for(const [id] of criteria){
      if(data.grades?.[id]?.estimate)el('sa-grade-'+id).value=String(data.grades[id].estimate);
      if(data.grades?.[id]?.explanation)el('sa-proof-'+id).value=data.grades[id].explanation;
    }
    updateScore();
  }
  function showAudit(data){
    latestAudit=data;
    el('sa-audit-summary').textContent=`${data.passed}/${data.total} checklist checks satisfied from this draft. ${data.disclaimer}`;
    el('sa-audit-results').innerHTML=data.checks.map(c=>`<div class="sa-audit-item"><span class="sa-audit-icon ${c.pass?'sa-yes':'sa-no'}">${c.pass?'✓':'!'}</span><span>${escaped(c.title)}<small>Guide page ${c.guide_page} · ${c.evidence_type==='structural'?'format/number check':'self-reported; not independently verified'}</small></span></div>`).join('');
  }
  async function runAudit(){
    saveDraft();
    el('sa-audit-summary').textContent='Checking structural rules and self-reported confirmations…';
    try {
      const res=await fetch('/api/spaceapps/audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(draft())});
      const data=await res.json();
      if(!res.ok)throw Error(JSON.stringify(data.detail||res.status));
      showAudit(data);
    }catch(error){latestAudit=null;el('sa-audit-summary').textContent='Could not perform self-audit: '+error.message+'. No eligibility result is available.';el('sa-audit-results').textContent='';}
  }
  function download(){
    const ctx=window.AgriOrbitReadinessContext?.() || {};
    const provenance=ctx.climate ? {source_type:ctx.climate.source_type,year:ctx.climate.year,provider:ctx.climate.source||ctx.climate.provider||null}:null;
    const bundle={schema:'agriorbit_2026_readiness_draft_v1',generated_at:new Date().toISOString(),
      source_guide:'User-provided NASA Space Apps 2026 Judging & Awards Guide, dated 2026-11-13',
      notice:'TEAM WORKING DRAFT ONLY. NOT AN OFFICIAL NASA SUBMISSION OR ELIGIBILITY CERTIFICATE.',
      self_report:draft(),team_judge_estimates:selfGrades(),last_local_check:latestAudit,
      available_climate_source_in_browser:provenance,
      unreconciled:['Official Project Submission Guide and terms','Pre-event portfolio work reuse','Human verification of images, code, licenses, NASA provenance','Agronomist and field validation']};
    const blob=new Blob([JSON.stringify(bundle,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download='AgriORBIT_NASA_2026_Readiness_DRAFT.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function switchPlan(which){
    const video=which==='video';
    el('sa-video-plan').hidden=!video;el('sa-slides-plan').hidden=video;
    el('sa-show-video').classList.toggle('active',video);el('sa-show-slides').classList.toggle('active',!video);
    el('sa-show-video').setAttribute('aria-pressed',String(video));el('sa-show-slides').setAttribute('aria-pressed',String(!video));
  }
  function tick(now){
    if(timerStart===null)return;
    const elapsed=Math.min(30,(now-timerStart)/1000);
    el('sa-timer-text').textContent=`00:${String(Math.floor(elapsed)).padStart(2,'0')} / 00:30`;
    el('sa-timer-fill').style.width=(elapsed/30*100)+'%';
    if(elapsed<30){timerAnimation=requestAnimationFrame(tick);}else{timerStart=null;el('sa-timer-start').textContent='↻ Restart rehearsal';el('sa-timer-text').textContent='00:30 / 00:30 — TIME LIMIT';}
  }
  function startTimer(){
    if(timerStart!==null){cancelAnimationFrame(timerAnimation);timerStart=null;el('sa-timer-start').textContent='▶ Resume from zero';return;}
    timerStart=performance.now();el('sa-timer-start').textContent='❚❚ Stop rehearsal';timerAnimation=requestAnimationFrame(tick);
  }
  function resetTimer(){cancelAnimationFrame(timerAnimation);timerStart=null;el('sa-timer-text').textContent='00:00 / 00:30';el('sa-timer-fill').style.width='0%';el('sa-timer-start').textContent='▶ Rehearse 30 seconds';}
  function clear(){
    if(!confirm('Reset the NASA self-audit selections and draft scores? Farm and NASA data will not be changed.'))return;
    try{localStorage.removeItem(store);}catch{}
    for(const id of fields) el('sa-'+id).value=({event:'local',team:'6',format:'none',slides:'0',seconds:'0',spoken:'true',references:''})[id];
    document.querySelectorAll('[data-sa-check]').forEach(x=>x.checked=false);
    for(const [id] of criteria){el('sa-grade-'+id).value='0';el('sa-proof-'+id).value='';}
    latestAudit=null;el('sa-audit-summary').textContent='Draft reset. This is not a NASA eligibility determination.';el('sa-audit-results').textContent='';updateScore();
  }
  async function init(){
    if(!el('sa-rubric'))return;
    drawRubric();drawChecklists();initialized=true;restoreDraft();evidence();
    for(const id of fields)el('sa-'+id).addEventListener('change',saveDraft);
    el('sa-references').addEventListener('input',saveDraft);
    el('sa-run-audit').addEventListener('click',runAudit);
    el('sa-export').addEventListener('click',download);
    el('sa-clear').addEventListener('click',clear);
    el('sa-refresh').addEventListener('click',evidence);
    el('sa-show-video').addEventListener('click',()=>switchPlan('video'));
    el('sa-show-slides').addEventListener('click',()=>switchPlan('slides'));
    el('sa-timer-start').addEventListener('click',startTimer);
    el('sa-timer-reset').addEventListener('click',resetTimer);
    try{const r=await fetch('/api/spaceapps/guide');if(r.ok){guide=await r.json();if(guide.scoring?.criteria?.length!==5)throw Error('rubric not received');}}catch{el('sa-audit-summary').textContent='Backend guide endpoint unavailable; static guide overview is still shown. Self-audit requires the server.';}
  }
  window.AgriOrbitSpaceApps={onView:view=>{if(view==='guidelines')evidence();},refresh:evidence};
  window.addEventListener('DOMContentLoaded',init);
})();

/* AgriORBIT MVP: zero-build UI. Data provenance is NEVER silently upgraded. */
'use strict';

const $ = (id) => document.getElementById(id);
const defaults = {
  name: 'Botolan pilot farm', latitude: 15.289, longitude: 120.024,
  area_ha: 1, texture: 'unknown', soil_ph: null, organic_matter_pct: null,
  irrigation: 'limited', current_crop: 'Rice', start_month: 6, soil_source: 'farmer_entered',
  priorities: {water: 5, soil_cover: 5, diversity: 5, affordability: 5, simplicity: 5},
};
const priorityNames = {water: 'Water feasibility', soil_cover: 'Soil cover', diversity: 'Crop diversity', affordability: 'Affordability', simplicity: 'Practice simplicity'};
let state = {farm: structuredClone(defaults), climate: null, comparison: null, boundary: '', view: 'command', requestId: 0};
let toastTimeout;

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function display(n, dec = 1) { return typeof n === 'number' && Number.isFinite(n) ? n.toFixed(dec) : '—'; }
function notify(message, isError = false) {
  const el = $('toast'); el.textContent = message; el.style.background = isError ? '#955735' : '#133f33';
  el.classList.add('show'); clearTimeout(toastTimeout); toastTimeout = setTimeout(() => el.classList.remove('show'), 4200);
}
// Phase 30: synchronous navigation with GPU-composited entrance animation.
// Do not unmount views: field inputs and simulation state survive every switch.
const AGRI_VIEWS = ['command','botolan','overview','farm','rotations','rover','evidence','guidelines','hazards'];
let agriNavAnimationTimer = 0;
let agriIndicatorFrame = 0;
let agriNavigationReady = false;
const agriMotionReduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function agriUpdateIndicators() {
  // A translate-only selection rail, independent of the view's graphics renderer.
  const sidebar = document.querySelector('.nav-v9');
  const mobile = document.querySelector('.mobile-workspace-tabs');
  for (const [host, className] of [[sidebar,'agri-nav-rail'],[mobile,'agri-mobile-rail']]) {
    if (!host) continue;
    const target = [...host.querySelectorAll('[data-view]')].find(b => b.dataset.view === state.view);
    const rail = host.querySelector('.'+className);
    if (!target || !rail) continue;
    // Rect differences stay correct even if the sidebar scrolls or changes width.
    const hostRect = host.getBoundingClientRect();
    const rect = target.getBoundingClientRect();
    const x = rect.left - hostRect.left + host.scrollLeft;
    const y = rect.top - hostRect.top + host.scrollTop;
    rail.style.transform = `translate3d(${Math.round(x)}px,${Math.round(y)}px,0)`;
    rail.style.width = `${Math.round(rect.width)}px`;
    if (className === 'agri-nav-rail') rail.style.height = `${Math.round(rect.height)}px`;
  }
}

function agriScheduleIndicators() {
  if (agriIndicatorFrame) cancelAnimationFrame(agriIndicatorFrame);
  agriIndicatorFrame = requestAnimationFrame(() => {
    agriIndicatorFrame = 0;
    agriUpdateIndicators();
  });
}
function agriInitNavigationMotion() {
  if (agriNavigationReady) return;
  agriNavigationReady = true;
  for (const [selector,cls] of [['.nav-v9','agri-nav-rail'],['.mobile-workspace-tabs','agri-mobile-rail']]) {
    const host = document.querySelector(selector);
    if (!host) continue;
    const rail = document.createElement('span');
    rail.className = cls;
    rail.setAttribute('aria-hidden','true');
    host.prepend(rail);
  }
  // Initialize without travelling from the first tab to the saved deep-link.
  document.documentElement.classList.add('agri-nav-no-motion');
  agriUpdateIndicators();
  requestAnimationFrame(() => document.documentElement.classList.remove('agri-nav-no-motion'));
  window.addEventListener('resize',agriScheduleIndicators,{passive:true});
  document.querySelector('.nav-v9')?.addEventListener('scroll',agriScheduleIndicators,{passive:true});
  document.querySelector('.mobile-workspace-tabs')?.addEventListener('scroll',agriScheduleIndicators,{passive:true});
  // Automatic height changes and orientation rotations reflow the rail correctly.
  if ('ResizeObserver' in window) {
    const ro = new ResizeObserver(agriScheduleIndicators);
    ['.nav-v9','.mobile-workspace-tabs'].forEach(sel=>{
      const el=document.querySelector(sel);
      if(el) ro.observe(el);
    });
  }
}

function setView(view) {
  if (!AGRI_VIEWS.includes(view)) return;
  const previous = state.view;
  const changed = previous !== view;
  const animated = changed && agriNavigationReady && !agriMotionReduced();
  if (!changed && agriNavigationReady) return; // Avoid flashing / resetting active modules.
  clearTimeout(agriNavAnimationTimer);
  document.querySelectorAll('.view.agri-view-entering').forEach(el => el.classList.remove('agri-view-entering'));
  const main = $('main');
  main?.classList.remove('agri-page-switching');
  state.view = view;
  document.querySelectorAll('.view').forEach(el => el.classList.toggle('active', el.id === 'view-' + view));
  document.querySelectorAll('[data-view]').forEach(el => {
    const selected = el.dataset.view === view;
    el.classList.toggle('active', selected);
    el.setAttribute('aria-current', selected ? 'page' : 'false');
    el.classList.remove('agri-tab-activated');
    if (selected && animated) { void el.offsetWidth; el.classList.add('agri-tab-activated'); }
  });
  $('crumb-view').textContent = {'botolan':'Botolan El Niño mission','command':'Mission control','overview':'NASA overview','farm':'Farm profile','rotations':'Rotation studio','rover':'Agro Sentinel','evidence':'Evidence & report','guidelines':'NASA Guidelines','hazards':'PHIVOLCS hazards'}[view];
  document.querySelector('.sidebar').classList.remove('open');
  window.scrollTo({top:0,behavior:'instant'});
  if (view === 'evidence') renderEvidence();
  if (view === 'overview') renderMap();
  document.body.classList.toggle('command-mode',view==='command');
  document.body.classList.toggle('botolan-mode',view==='botolan');
  // Refresh visualizations only when the destination is actually visible.
  window.AgriOrbitCommand?.onView(view);
  window.AgriOrbitBotolan?.onView(view);
  window.AgriOrbitMission?.onView(view);
  window.AgriOrbitSpaceApps?.onView(view);
  if (animated) {
    const incoming = $('view-'+view);
    incoming.classList.add('agri-view-entering');
    main?.classList.add('agri-page-switching');
    agriNavAnimationTimer = window.setTimeout(() => {
      incoming.classList.remove('agri-view-entering');
      main?.classList.remove('agri-page-switching');
      document.querySelectorAll('.agri-tab-activated').forEach(el=>el.classList.remove('agri-tab-activated'));
    },340);
  }
  agriScheduleIndicators();
  if (animated && window.innerWidth <= 750) {
    const strip = document.querySelector('.mobile-workspace-tabs');
    const tab = [...(strip?.querySelectorAll('[data-view]') || [])].find(t=>t.dataset.view===view);
    if (strip && tab) {
      const left=tab.offsetLeft+tab.offsetWidth/2-strip.clientWidth/2;
      strip.scrollTo({left:Math.max(0,left),behavior:'smooth'});
    }
  }
  if (location.hash !== '#'+view) location.hash=view;
}

function loadSaved() {
  try {
    const saved = JSON.parse(localStorage.getItem('agriorbit-farm-v1') || 'null');
    if (saved && saved.farm && typeof saved.farm.name === 'string') {
      state.farm = {...structuredClone(defaults), ...saved.farm, priorities: {...defaults.priorities, ...saved.farm.priorities}};
      state.boundary = saved.boundary || '';
    }
  } catch { /* Ignore malformed local storage */ }
}
function renderForm() {
  const f = state.farm;
  const fields = {'farm-name':f.name,'farm-lat':f.latitude,'farm-lon':f.longitude,'farm-area':f.area_ha,
    'farm-crop':f.current_crop,'farm-start-month':f.start_month,'farm-texture':f.texture,'farm-irrigation':f.irrigation,
    'farm-ph':f.soil_ph ?? '', 'farm-om':f.organic_matter_pct ?? '', 'farm-source':f.soil_source};
  for (const [key, val] of Object.entries(fields)) $(key).value = val;
  $('farm-geojson').value = state.boundary;
  $('priority-list').innerHTML = Object.entries(priorityNames).map(([key,name]) => `
    <div class="priority-row"><label for="priority-${key}">${esc(name)}</label>
    <input id="priority-${key}" type="range" min="0" max="10" step="1" value="${f.priorities[key]}" />
    <output id="output-${key}">${f.priorities[key]}</output></div>`).join('');
  for (const key of Object.keys(priorityNames)) {
    $('priority-' + key).addEventListener('input', () => { $('output-' + key).textContent = $('priority-' + key).value; });
  }
  $('farm-geojson').addEventListener('input', validateBoundary);
  validateBoundary();
}
function collectFarm() {
  if (!$('farm-form').reportValidity()) throw new Error('Please check the required farm fields.');
  const optional = (id) => $(id).value.trim() === '' ? null : Number($(id).value);
  const f = {
    name: $('farm-name').value.trim(), latitude: Number($('farm-lat').value), longitude: Number($('farm-lon').value),
    area_ha: Number($('farm-area').value), texture: $('farm-texture').value,
    soil_ph: optional('farm-ph'), organic_matter_pct: optional('farm-om'),
    irrigation: $('farm-irrigation').value, current_crop: $('farm-crop').value.trim(), start_month: Number($('farm-start-month').value),
    soil_source: $('farm-source').value, priorities: {},
  };
  Object.keys(priorityNames).forEach(key => f.priorities[key] = Number($('priority-' + key).value));
  if (!f.name || !f.current_crop) throw new Error('Farm name and current crop are required.');
  if ($('farm-geojson').value.trim()) parseBoundary($('farm-geojson').value.trim()); // validate newly entered geometry
  return f;
}
function saveFarm(e) {
  e.preventDefault();
  try {
    const f = collectFarm();
    const changedPoint = state.farm.latitude !== f.latitude || state.farm.longitude !== f.longitude;
    state.farm = f;
    if (changedPoint) state.climate = null; // NEVER show prior NASA data for a new coordinate.
    state.boundary = $('farm-geojson').value.trim();
    try {localStorage.setItem('agriorbit-farm-v1', JSON.stringify({farm:f, boundary:state.boundary}));} catch {}
    window.AgriOrbitPrecision?.invalidate();
    renderFarmSummary(); renderMap(); renderClimate(); runCompare();
    notify('Farm profile updated. Scenarios recalculated.');
    setView('rotations');
  } catch(err) { notify(err.message, true); }
}
function renderFarmSummary() {
  const f = state.farm;
  $('field-name').textContent = f.name;
  $('field-area').textContent = display(f.area_ha, 2) + ' ha';
  $('field-irrigation').textContent = f.irrigation[0].toUpperCase() + f.irrigation.slice(1);
  $('stat-coordinates').textContent = `${display(f.latitude, 4)}° N · ${display(f.longitude,4)}° E (editable)`;
}
function parseBoundary(text) {
  const val = JSON.parse(text);
  const geom = val.type === 'Feature' ? val.geometry : val;
  if (!geom || geom.type !== 'Polygon' || !Array.isArray(geom.coordinates?.[0])) throw new Error('Expected a GeoJSON Polygon or Feature containing a Polygon.');
  const ring = geom.coordinates[0];
  if (ring.length < 4 || ring.length > 2000) throw new Error('Polygon must contain between 4 and 2,000 positions.');
  ring.forEach(pt => {
    if (!Array.isArray(pt) || pt.length < 2 || !Number.isFinite(pt[0]) || !Number.isFinite(pt[1]) || Math.abs(pt[0]) > 180 || Math.abs(pt[1]) > 90) throw new Error('Invalid GeoJSON coordinates. Use [longitude, latitude].');
  });
  if (ring[0][0] !== ring[ring.length - 1][0] || ring[0][1] !== ring[ring.length - 1][1]) throw new Error('Polygon ring must be closed (last position = first).');
  return ring;
}
function validateBoundary() {
  const text = $('farm-geojson').value.trim();
  try {
    if (!text) { $('boundary-status').textContent = 'No polygon supplied — point location only.'; return; }
    const ring = parseBoundary(text);
    $('boundary-status').textContent = `Valid GeoJSON polygon (${ring.length-1} edges). Save to display outline.`;
    $('boundary-status').style.color = '#318663';
  } catch(err) {
    $('boundary-status').textContent = 'Invalid polygon: ' + err.message;
    $('boundary-status').style.color = '#ad663d';
  }
}
function renderMap() {
  const map = $('field-map');
  map.querySelector('.field-polygon')?.remove();
  const note = $('map-note');
  if (!state.boundary) {note.textContent = 'Point reference only — no surveyed field boundary has been supplied.';return;}
  try {
    const ring = parseBoundary(state.boundary);
    const xs = ring.map(p => p[0]), ys = ring.map(p => p[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    if (maxX - minX < 1e-10 || maxY - minY < 1e-10) throw new Error('Polygon has no area.');
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    const stretch = Math.max((maxX-minX) * Math.cos(cy*Math.PI/180), maxY) * 1.4;
    const points = ring.map(([x,y]) => {
      const px = 200 + (x-cx) * Math.cos(cy*Math.PI/180)/stretch * 155;
      const py = 115 - (y-cy)/stretch * 155;
      return `${px.toFixed(1)},${py.toFixed(1)}`;
    }).join(' ');
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 400 230'); svg.setAttribute('preserveAspectRatio','xMidYMid meet'); svg.classList.add('field-polygon');
    const poly = document.createElementNS('http://www.w3.org/2000/svg','polygon');
    poly.setAttribute('points', points); poly.setAttribute('stroke','#187b58'); poly.setAttribute('stroke-width','3');
    poly.setAttribute('stroke-linejoin','round');poly.setAttribute('fill','#59ba8540');
    svg.appendChild(poly); map.appendChild(svg);
    note.textContent = `User-entered GeoJSON outline (${ring.length-1} edges), not independently verified or a surveyed cadastral map.`;
  } catch(err) {note.textContent = 'Boundary could not be rendered: ' + err.message;}
}
async function runCompare() {
  // Once historical data is linked, always reassess against a server-controlled source.
  const id = ++state.requestId;
  const hasClimate = Boolean(state.climate);
  try {
    const endpoint = hasClimate ? '/api/assess' : '/api/compare';
    const params = hasClimate ? {farm:state.farm, year:state.climate.year,
      mode:state.climate.source_type==='synthetic'?'synthetic':'nasa'} : state.farm;
    const res = await fetch(endpoint, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params)});
    const payload = await res.json();
    if (!res.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : 'Comparison API error');
    if (id !== state.requestId) return;
    if (hasClimate) {state.climate=payload.climate;state.comparison=payload.comparison;renderClimate();}
    else state.comparison=payload;
    renderScenarios(); renderEvidence(); window.AgriOrbitCommand?.sync();
  } catch(err) {
    if (id !== state.requestId) return;
    if (hasClimate) {
      state.climate=null;
      renderClimate();
      notify('Climate unavailable: not applying a NASA adjustment. ' + err.message, true);
      await runCompare(); // Explicitly reverts to baseline, never retains stale climate claims.
    } else notify('Comparison failed: ' + err.message, true);
  }
}
function renderScenarios() {
  const scs = state.comparison?.scenarios || [];
  $('overview-scenarios').innerHTML = scs.map(s => `
    <div class="quick-scenario"><small>SCENARIO ${esc(s.id)}</small><strong>${esc(s.title)}</strong>
    <div class="seq">${s.crops.map(esc).join(' → ')}</div><div class="qscore">${s.score}<span> / 100 · heuristic</span></div>
    <div class="mini-bar"><span style="width:${s.score}%"></span></div></div>`).join('');
  $('rotation-cards').innerHTML = scs.map((s, index) => `
    <article class="scenario-card ${index === 0 ? 'best' : ''}"><div class="scenario-top"><div><span class="scenario-label">SCENARIO ${esc(s.id)} ${index===0?'· HIGHEST PROTOTYPE SCORE':''}</span>
    <h3>${esc(s.title)}</h3><div class="scenario-sub">${esc(s.description)}</div></div><div class="scenario-score">${s.score}<small>/100</small></div></div>
    <div class="sequence">${s.crops.map((crop,i) => `<span class="crop-chip">${esc(crop)}</span>${i<s.crops.length-1?'<span class="crop-sep">→</span>':''}`).join('')}</div>
    <div class="score-breakdown">${s.breakdown.map(b => `<div class="score-row"><span>${esc(b.label)}</span><div class="track"><div style="width:${b.score}%"></div></div><b>${b.score}</b></div>`).join('')}</div>
    ${s.rainfall_stress_test?`<div class="stress-strip"><strong>Rainfall stress test (simulated ±20%)</strong><span>Historical penalty ${s.climate_water_penalty} pts · Drier ${s.rainfall_stress_test.drier_20_pct_water_penalty} pts · Wetter ${s.rainfall_stress_test.wetter_20_pct_water_penalty} pts</span></div>`:''}
    ${s.evidence_references?.length?`<div class="evidence-refs"><strong>Research context — does not calibrate scores:</strong> ${s.evidence_references.map(r=>`<a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.title)} ↗</a>`).join('')}</div>`:''}
    <div class="scenario-foot"><strong>Review needed:</strong> ${esc(s.watchout)}
    ${s.adjustments.length?'<br/><strong>Prototype adjustments:</strong> '+s.adjustments.map(esc).join(' '):''}</div></article>`).join('');
  $('weight-breakdown').innerHTML = Object.entries(state.comparison.method.weights)
    .map(([k,v])=>`<div class="weight-line"><span>${esc(priorityNames[k])}</span><strong>${display(v,1)}%</strong></div>`).join('');
  $('evidence-gaps').innerHTML = state.comparison.missing_evidence.map(s => `<li>${esc(s)}</li>`).join('');
  renderSeason();
}
function climateStatusText(d) {
  if (!d) return 'No climate data has been fetched.';
  if (d.source_type === 'synthetic') return 'SYNTHETIC DEMO — values fabricated for interface testing; not NASA observations.';
  if (d.source_type === 'nasa_cached') return 'NASA POWER cached response — fetched ' + d.retrieved_at + '; not a live API result.';
  return 'NASA POWER API historical response — retrieved ' + d.retrieved_at + '.';
}
function renderClimate() {
  const d = state.climate;
  const label = $('climate-label');
  if (!d) {
    label.textContent = 'NO DATA'; label.className = 'data-tag';
    $('climate-chart').innerHTML = '<div class="chart-empty">No observations loaded<br/><small>Fetch real NASA data to populate the chart.</small></div>';
    $('climate-subtitle').textContent = 'Connect to NASA POWER or load synthetic values for UI rehearsal.';
    $('stat-data').textContent = 'Not connected'; $('stat-data-foot').textContent = 'Load NASA POWER historical data';
    $('climate-status').textContent = 'Historical year: 2025 • Data are not plot-level measurements.';
    return;
  }
  label.textContent = d.source_type === 'synthetic' ? 'SYNTHETIC' : d.source_type === 'nasa_cached' ? 'CACHED NASA' : 'NASA POWER';
  label.className = 'data-tag ' + (d.source_type === 'synthetic'?'synthetic':d.source_type==='nasa_cached'?'cached':'connected');
  $('climate-subtitle').textContent = `${d.period} · ${d.complete_days} complete days · ${d.provider}`;
  $('stat-data').textContent = d.source_type === 'synthetic' ? 'Demo only' : 'NASA POWER';
  $('stat-data-foot').textContent = `${d.source_type==='synthetic'?'Simulated':'Historical'} • ${display(d.summary.annual_precipitation_mm,0)} mm precipitation`;
  $('climate-status').textContent = climateStatusText(d);
  const allRain = d.months.map(m => m.precipitation_mm || 0);
  const maxRain = Math.max(10, ...allRain) * 1.18;
  const mon = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const left = 37, right = 530, span = right-left, col = span/12, top=14, bottom=155, height=bottom-top;
  let svg = `<svg viewBox="0 0 560 187" role="img" aria-label="Historical or synthetic monthly precipitation bars and mean temperature line">`;
  for(let i=0;i<4;i++){
    const y = top + height*i/3;
    svg += `<line x1="${left}" x2="${right}" y1="${y}" y2="${y}" stroke="#e9f0ea" stroke-dasharray="3 5"/><text x="29" y="${y+4}" text-anchor="end" fill="#96a79c" font-size="9">${Math.round(maxRain*(1-i/3))}</text>`;
  }
  const points = [];
  d.months.forEach((m,i)=>{
    const x=left+(i+.5)*col, rain=m.precipitation_mm||0, h=rain/maxRain*height;
    svg += `<rect x="${(x-11).toFixed(1)}" y="${(bottom-h).toFixed(1)}" width="22" height="${h.toFixed(1)}" rx="3" fill="#73ba94" opacity=".8"><title>${mon[i]} precipitation: ${display(m.precipitation_mm)} mm</title></rect>`;
    svg += `<text x="${x.toFixed(1)}" y="174" text-anchor="middle" fill="#8fa195" font-size="10">${mon[i]}</text>`;
    if(m.temperature_c!==null){const cy=bottom-Math.max(0,Math.min(1,(m.temperature_c-15)/25))*height; points.push([x,cy,m.temperature_c,mon[i]]);}
  });
  svg += `<polyline points="${points.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')}" stroke="#dca655" fill="none" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>`;
  for(const [x,y,temp,m] of points) svg += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.4" fill="#dca655" stroke="white" stroke-width="1.4"><title>${m} mean temperature: ${display(temp)} °C</title></circle>`;
  svg += `<text x="4" y="11" font-size="9" fill="#95a697">mm</text><text x="555" y="11" font-size="9" text-anchor="end" fill="#dca655">temp scale: 15–40 °C</text></svg>`;
  $('climate-chart').innerHTML = svg;
  window.AgriOrbitCommand?.sync();
}
async function fetchClimate(mode) {
  // The backend fetches NASA observations; the browser cannot supply fake NASA metadata.
  const requestId = ++state.requestId;
  const buttons = [$('fetch-nasa'),$('fetch-demo'),$('season-nasa'),$('season-demo')];
  buttons.forEach(b=>b.disabled=true);
  $('climate-status').textContent = mode==='nasa'?'Requesting NASA POWER and reassessing scenarios…':'Generating visibly synthetic rehearsal context…';
  try {
    const response = await fetch('/api/assess',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({farm:state.farm,year:2025,mode})});
    const payload=await response.json();
    if(!response.ok) throw new Error(typeof payload.detail==='string'?payload.detail:'Assessment failed.');
    if (requestId!==state.requestId) return;
    state.climate=payload.climate; state.comparison=payload.comparison;
    renderClimate();renderScenarios();renderEvidence();window.AgriOrbitCommand?.sync();
    notify(mode==='synthetic'?'Synthetic rehearsal linked — NOT NASA evidence.':'NASA POWER historical record linked to experimental seasonal screening.');
  }catch(err){
    if(requestId!==state.requestId)return;
    state.climate=null;renderClimate();
    notify('Could not link climate: '+err.message,true);
    await runCompare();
  }finally{buttons.forEach(b=>b.disabled=false);}
}
function renderSeason() {
  const comparison=state.comparison, context=comparison?.season_context;
  const badge=$('season-data-badge'), target=$('season-info');
  if(!context){
    badge.textContent='NOT LINKED'; badge.className='data-tag';
    target.textContent='No climate record is linked. The baseline experiment uses farmer-entered irrigation, soil texture and qualitative rotation assumptions only.';
    return;
  }
  badge.textContent=state.climate?.source_type==='synthetic'?'SYNTHETIC DEMO':(context.usable?'NASA HISTORICAL':'INSUFFICIENT COVERAGE');
  badge.className='data-tag '+(state.climate?.source_type==='synthetic'?'synthetic':context.usable?'connected':'cached');
  const status=context.usable?`<div class="season-stat"><div><small>Selected historical window</small><b>${esc(context.window)} ${state.climate.year}</b></div><div><small>3-month precipitation</small><b>${display(context.rainfall_mm,1)} mm</b></div><div><small>Share of annual precipitation</small><b>${display(context.rainfall_fraction_of_annual_pct,1)}%</b></div><div><small>Equal 3-month share benchmark</small><b>${display(context.three_month_annual_mean_mm,1)} mm</b></div></div>`:'';
  target.innerHTML=`${status}<p class="season-note">${esc(context.notice)}</p><p class="season-note"><strong>Interpretation:</strong> ${esc(context.method)}</p><p class="season-note"><strong>Monthly coverage:</strong> ${context.coverage_pct_by_month.map(v=>v+'%').join(' · ')} · <strong>Data type:</strong> ${esc(context.status)}</p>`;
}
function metaRow(k, v) {return `<div class="meta-line"><span>${esc(k)}</span><strong>${v}</strong></div>`;}
function renderEvidence() {
  const d = state.climate, c = state.comparison;
  $('provenance').innerHTML = !d ? '<p>No NASA record loaded. No historical observations or measured field data are claimed.</p>' : [
    metaRow('Data status', esc(d.source_type==='synthetic'?'SYNTHETIC — NOT NASA':d.source_type==='nasa_cached'?'NASA CACHED':'NASA API HISTORICAL')),
    metaRow('Provider', esc(d.provider)), metaRow('Period', esc(d.period)),
    metaRow('Coordinates', `${display(d.latitude,5)}°, ${display(d.longitude,5)}°`),
    metaRow('Data coverage', `${d.complete_days}/${d.expected_days} complete days (${display(d.data_coverage_pct,1)}%)`),
    metaRow('Raw payload SHA-256', `<span style="overflow-wrap:anywhere;font-size:11px">${esc(d.raw_payload_sha256 || 'n/a')}</span>`),
    metaRow('Variables', d.parameters.map(p=>`${esc(p.code)} (${esc(p.unit)})`).join('<br/>')),
    metaRow('Retrieved at (UTC)',esc(d.retrieved_at)),
    metaRow('Spatial limits',esc(d.spatial_note)),
    metaRow('Temporal limits',esc(d.temporal_note)),
    d.request_url ? metaRow('Source URL',`<a href="${esc(d.request_url)}" target="_blank" rel="noopener noreferrer">View exact NASA API request ↗</a>`) : '',
    d.fetch_warning ? metaRow('Fetch warning',esc(d.fetch_warning)) : '',
    c?.season_context ? metaRow('Chosen historical window',esc(c.season_context.window)+' · '+esc(c.season_context.status)) : '',
  ].join('');
  $('method-details').innerHTML = c ? `
    <p><strong>Experimental / not validated.</strong> ${esc(c.method.formula)}</p>
    <p><strong>Inputs:</strong> ${esc(c.method.scoring_input)}</p>
    <p><strong>Climate use:</strong> ${esc(c.method.climate_use)}</p>
    <p><strong>Calibration:</strong> ${esc(c.method.calibration)}</p>
    <p><strong>Historical climate formula:</strong> ${esc(c.method.climate_formula)}</p>
    <p><strong>Source categories:</strong> NASA API historical, user/farmer-entered, lab/field-reported (not independently verified), synthetic demo and prototype assumptions are kept separate.</p>` : '<p>Comparison has not been generated.</p>';
  $('report-preview').innerHTML = c ? `<h4>${esc(c.farm.name)} · ${esc(c.farm.area_ha)} ha</h4><p>${esc(c.farm.current_crop)} current crop · ${esc(c.farm.texture)} texture · ${esc(c.farm.irrigation)} irrigation</p>
    <h4>Comparison ranking (illustrative)</h4>${c.scenarios.map(s=>`<p><strong>${esc(s.id)}. ${esc(s.title)} — ${s.score}/100</strong>: ${s.crops.map(esc).join(' → ')}. ${esc(s.watchout)}</p>`).join('')}
    <h4>Evidence status</h4><p>${esc(climateStatusText(d))} Plot-specific soil tests, local agronomy and market conditions remain necessary.</p>
    <p><strong>Rainfall window:</strong> ${esc(c.season_context?.window||'Not assessed')} · ${esc(c.season_context?.status||'Not linked')}. This does not predict planting outcomes.</p>
    <p><strong>Notice:</strong> ${esc(c.advisory)}</p>` : '<p>Save a farm profile to populate the report preview.</p>';
}
function exportReport() {
  if (!state.comparison) { notify('Run a comparison first.', true); return; }
  const c=state.comparison, f=c.farm, d=state.climate;
  const lines=[
    '# AgriORBIT NASA — preliminary farm discussion report','',
    'Generated UTC: '+new Date().toISOString(), 'Status: PROTOTYPE / NOT AGRONOMICALLY VALIDATED','',
    '## Farm context', `- Farm: ${f.name}`,`- Coordinates: ${f.latitude}, ${f.longitude} (user-provided)`,
    `- Area: ${f.area_ha} ha`,`- Current crop: ${f.current_crop}`,`- Historical planning window starts in month: ${f.start_month}`,`- Soil: ${f.texture}; pH ${f.soil_ph ?? 'not supplied'}; organic matter ${f.organic_matter_pct ?? 'not supplied'}%`,
    `- Irrigation: ${f.irrigation}`,`- Soil information status: ${f.soil_source} (not independently verified)`,
    '', '## Climate evidence', climateStatusText(d),
  ];
  if (d) lines.push(`- Provider: ${d.provider}`,`- Period: ${d.period}`,`- Retrieved UTC: ${d.retrieved_at}`,`- Annual rainfall: ${d.summary.annual_precipitation_mm} mm`,`- Average air temperature: ${d.summary.average_temperature_c} °C`,`- Complete days: ${d.complete_days}/${d.expected_days}`,`- Raw payload SHA-256: ${d.raw_payload_sha256 || 'not available'}`,`- Source request: ${d.request_url || 'NONE — SYNTHETIC DATA'}`,`- Spatial limitation: ${d.spatial_note}`);
  if(c.season_context)lines.push('', '## Historical rainfall window',`- Months: ${c.season_context.window}`,`- Status: ${c.season_context.status}`,`- Three-month rainfall: ${c.season_context.rainfall_mm ?? 'insufficient coverage'} mm`,`- Equal 3-month share benchmark: ${c.season_context.three_month_annual_mean_mm ?? 'missing'} mm`,`- Within-year-relative rainfall method: ${c.season_context.method}`,`- Context warning: ${c.season_context.notice}`);
  lines.push('', '## Crop rotation scenarios (unvalidated proxy scores)');
  c.scenarios.forEach(s => lines.push(`### ${s.id}. ${s.title} — ${s.score}/100`,`- Sequence: ${s.crops.join(' -> ')}`,`- Explanation: ${s.description}`,`- Review needed: ${s.watchout}`,`- Heuristic breakdown: ${s.breakdown.map(b=>b.label+' '+b.score+'/100 (weight '+b.weight+'%)').join('; ')}`,`- Adjustments: ${s.adjustments.join(' ') || 'None'}`,`- Climate water penalty (prototype): ${s.climate_water_penalty ?? 0} points`,`- Hypothetical rainfall stress test: ${s.rainfall_stress_test ? JSON.stringify(s.rainfall_stress_test) : 'Not available'}`,`- General research references, NOT score calibration: ${(s.evidence_references || []).map(r=>r.title+' '+r.url).join('; ') || 'None'}`,''));
  lines.push('## Method and limitations',c.method.formula,c.method.scoring_input,c.method.climate_use,c.method.climate_formula,c.method.calibration,'', '## Required evidence before field decisions', ...c.missing_evidence.map(s=>'- '+s),'', '## Advisory',c.advisory,'', 'NASA POWER: https://power.larc.nasa.gov/','AgriORBIT NASA — research prototype.');
  const blob=new Blob([lines.join('\n')],{type:'text/markdown;charset=utf-8'});
  const url=URL.createObjectURL(blob); const a=document.createElement('a');a.href=url;a.download='AgriORBIT_Farm_Report.md';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  notify('Markdown field report exported.');
}
function simulate() {
  // Backed by server-generated deterministic simulation data. No physical rover.
  window.AgriOrbitMission?.refreshTelemetry(Math.random());
  notify('Requested a synthetic sample — not a field measurement.');
}

/* Phase 19 startup overlay. These are startup readiness checks, not sensor calibration. */
let calibrationRunning = false;
let calibrationAutoEnter = null;
function calStatus(id, status, label) {
  const el = $('cal-check-' + id);
  if (!el) return;
  el.dataset.status = status;
  el.querySelector('b').textContent = label;
  // Actual checks are reported independently of the fixed-duration cinematic bar.
  const ids = ['interface','farm','api','scenarios'];
  const checked = ids.filter(key => ['passed','warning'].includes($('cal-check-' + key)?.dataset.status)).length;
  const passed = ids.filter(key => $('cal-check-' + key)?.dataset.status === 'passed').length;
  const display = $('cal-check-count');
  if (display) display.textContent = `LOCAL CHECKS · ${passed}/4 PASSED${checked === 4 && passed !== 4 ? ' · REVIEW WARNINGS' : ''}`;
}
function calProgress(_value, note) {
  // The startup diagnostic message must never overwrite the 15-second visual bar.
  // Visual progress is controlled solely by AgriOrbitSeedlingBoot's elapsed-time clock.
  const display = $('cal-summary');
  if (display && note) display.textContent = `${note} · NASA data and physical hardware not verified at boot.`;
}
function closeCalibration() {
  if (calibrationAutoEnter) { clearTimeout(calibrationAutoEnter); calibrationAutoEnter = null; }
  const overlay = $('calibration');
  overlay.classList.add('is-hidden');
  overlay.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('calibrating');
  window.AgriOrbitBootFX?.stop();
  window.AgriOrbitSeedlingBoot?.stop();
  document.querySelector('.shell').inert = false;
  $('cal-replay').focus();
}
function showCalibration() {
  if (calibrationAutoEnter) { clearTimeout(calibrationAutoEnter); calibrationAutoEnter = null; }
  $('calibration').classList.remove('is-hidden');
  $('calibration').removeAttribute('aria-hidden');
  document.body.classList.add('calibrating');
  window.AgriOrbitBootFX?.start();
  window.AgriOrbitSeedlingBoot?.start();
  document.querySelector('.shell').inert = true;
  $('cal-enter').disabled = true;
  $('cal-enter').textContent = 'Running checks…';
  $('cal-retry').hidden = true;
  ['interface', 'farm', 'api', 'scenarios'].forEach(id => calStatus(id, 'queued', 'Queued'));
  calProgress(0, 'Starting real local system checks…');
  $('cal-summary').textContent = 'NASA data and physical rover hardware are not checked at startup.';
}
async function startupChecks() {
  if (calibrationRunning) return;
  calibrationRunning = true;
  showCalibration();
  let failures = 0;
  const waitFrame = () => new Promise(resolve => requestAnimationFrame(resolve));
  // Visual pacing only; each readiness result still comes from the real check.
  const visualPause = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches ? Promise.resolve() : new Promise(resolve => setTimeout(resolve, 300));
  try {
    await waitFrame();
    // DOM nodes are loaded, and the local application JS has entered its initialization code.
    calStatus('interface', 'passed', 'Ready');
    calProgress(25, 'Checking saved farm context…');
    await visualPause();
    if (state.farm && Number.isFinite(Number(state.farm.latitude)) && Number.isFinite(Number(state.farm.longitude))) {
      calStatus('farm', 'passed', 'Loaded');
    } else {
      calStatus('farm', 'warning', 'Needs input');
      failures++;
    }
    calProgress(50, 'Checking FastAPI service…');
    await visualPause();
    // Health endpoint is a real HTTP request with a bounded timeout.
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 4500);
      try {
        const response = await fetch('/api/health', {signal: controller.signal, cache: 'no-store'});
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const health = await response.json();
        if (health.status !== 'ok') throw new Error('API not ready');
        calStatus('api', 'passed', 'Online');
      } finally { clearTimeout(timer); }
    } catch(err) {
      failures++;
      calStatus('api', 'warning', 'Unavailable');
    }
    calProgress(75, 'Checking rotation engine…');
    await visualPause();
    // This is the same API call used by the dashboard and does not fetch NASA data on first run.
    try {
      await runCompare();
      if (state.comparison?.scenarios?.length >= 3) {
        calStatus('scenarios', 'passed', 'Ready');
      } else {
        failures++;
        calStatus('scenarios', 'warning', 'Unavailable');
      }
    } catch(err) {
      failures++;
      calStatus('scenarios', 'warning', 'Unavailable');
    }
    calProgress(100, failures ? 'Checks finished — review limitations' : 'Workspace initialized');
    await visualPause();
    const enter = $('cal-enter');
    enter.disabled = true;
    enter.innerHTML = failures ? 'Enter limited workspace <span aria-hidden="true">↗</span>' : 'Enter mission control <span aria-hidden="true">↗</span>';
    $('cal-retry').hidden = !failures;
    $('cal-summary').textContent = failures ?
      `${failures} startup check(s) need attention. You may enter in limited mode or retry. NASA data still requires manual retrieval.` :
      'Startup checks complete. NASA POWER has NOT been fetched; Agro Sentinel remains simulated.';
    // The 15-second cinematic timer is NOT a fifth system check. Both must finish independently.
    // Reduced-motion users are not forced to wait for decorative animation.
    $('cal-summary').textContent += ' Finishing the decorative 15-second growth sequence…';
    await (window.AgriOrbitSeedlingBoot?.wait() || Promise.resolve());
    enter.disabled = false;
    $('cal-summary').textContent = failures ?
      `${failures} startup check(s) need attention. Enter limited mode or retry. NASA retrieval has not been verified.` :
      'Ready: four local checks completed. NASA POWER has NOT been fetched; rover telemetry is simulated.';
    // Skip and held previews require a deliberate user action. Failures never auto-enter.
    if (!failures && !window.matchMedia('(prefers-reduced-motion: reduce)').matches &&
        !new URLSearchParams(location.search).has('calibration-hold')) {
      calibrationAutoEnter = setTimeout(closeCalibration, 650);
    }
  } finally { calibrationRunning = false; }
}

function init() {
  loadSaved();renderForm();renderFarmSummary();renderMap();renderClimate();renderEvidence();
  const initial = location.hash.replace('#','');
  setView(AGRI_VIEWS.includes(initial)?initial:'command');
  agriInitNavigationMotion();
  document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click',()=>setView(b.dataset.view)));
  document.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click',()=>setView(b.dataset.go)));
  $('mobile-menu').addEventListener('click',()=>document.querySelector('.sidebar').classList.toggle('open'));
  $('farm-form').addEventListener('submit',saveFarm);
  $('fetch-nasa').addEventListener('click',()=>fetchClimate('nasa'));
  $('fetch-demo').addEventListener('click',()=>fetchClimate('synthetic'));
  $('season-nasa').addEventListener('click',()=>fetchClimate('nasa'));
  $('season-demo').addEventListener('click',()=>fetchClimate('synthetic'));
  $('recompare').addEventListener('click',runCompare);
  $('simulate').addEventListener('click',simulate);
  $('download-report').addEventListener('click',exportReport);
  window.addEventListener('hashchange',()=>{const v=location.hash.slice(1);if(v && v!==state.view)setView(v)});
  $('cal-enter').addEventListener('click', closeCalibration);
  $('cal-retry').addEventListener('click', startupChecks);
  $('cal-replay').addEventListener('click', startupChecks);
  $('cal-skip').addEventListener('click', () => window.AgriOrbitSeedlingBoot?.skip());
  window.AgriOrbitMission?.init(state);
  window.AgriOrbitCommand?.init(state);
  startupChecks();
}
window.addEventListener('DOMContentLoaded',init);

// Read-only integration contract for NASA Precision Lab.
window.AgriOrbitGetFarm = () => ({farm: structuredClone(state.farm), boundary: state.boundary});

// Read-only guide UI bridge. Client state is not an independently authenticated NASA record.
window.AgriOrbitReadinessContext = () => ({farm:structuredClone(state.farm), climate:state.climate ? structuredClone(state.climate) : null, comparison:state.comparison ? structuredClone(state.comparison) : null});

/* AgriORBIT v1.3 precision add-on. Never infers live observations from visual assets. */
'use strict';
(() => {
  const $p = id => document.getElementById(id);
  const html = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = (value, digits = 1) => typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : '—';
  let last = null, fetching = false, runId = 0;
  const safeFarm = () => window.AgriOrbitGetFarm?.() || { farm: null, boundary: '' };
  const modeLabel = d => d?.data_class === 'synthetic_demo' ? 'SYNTHETIC REHEARSAL — NOT NASA' :
    d?.status === 'ready' ? 'NASA HISTORICAL / QUALITY GATE PASSED' : 'INSUFFICIENT NASA COVERAGE';
  const setStatus = s => { if ($p('precision-status')) $p('precision-status').textContent = s; };
  function invalidate() {
    runId++;
    last = null;
    if ($p('precision-badge')) { $p('precision-badge').textContent = 'NOT VERIFIED'; $p('precision-badge').dataset.state = 'missing'; }
    for (const id of ['precision-target', 'precision-mean', 'precision-anomaly', 'precision-coverage'])
      if ($p(id)) $p(id).textContent = '—';
    if ($p('precision-export')) $p('precision-export').disabled = true;
    if ($p('precision-season-table')) $p('precision-season-table').textContent = 'Farm profile changed. Request a fresh, coordinate-matched benchmark.';
    setStatus('Farm context changed; previous benchmark was cleared. Historical NASA data must be refetched for these coordinates.');
  }
  function render(payload) {
    last = payload;
    const b = payload.benchmark;
    const demo = b.data_class === 'synthetic_demo';
    const source = b.provenance;
    $p('precision-badge').textContent = demo ? 'SYNTHETIC DEMO' : b.status === 'ready' ? 'NASA HISTORICAL' : 'INSUFFICIENT DATA';
    $p('precision-badge').dataset.state = demo ? 'demo' : b.status === 'ready' ? 'ready' : 'missing';
    $p('precision-target').textContent = fmt(b.target_season.precipitation_mm, 1);
    $p('precision-mean').textContent = fmt(b.recent_mean_rainfall_mm, 1);
    $p('precision-anomaly').textContent = b.rainfall_anomaly_pct == null ? '—' :
      (b.rainfall_anomaly_pct > 0 ? '+' : '') + fmt(b.rainfall_anomaly_pct, 1) + '%';
    $p('precision-coverage').textContent = `${b.baseline_seasons_valid} / ${b.baseline_years_requested}`;
    $p('precision-export').disabled = false;
    const rejected = payload.failed_years?.length ? ` Missing upstream years: ${payload.failed_years.map(x => x.year).join(', ')}.` : '';
    setStatus(`${modeLabel(b)}. ${b.rainfall_context}. ${b.baseline_seasons_valid} valid reference seasons. ${demo ? 'All figures fabricated; not suitable for competition evidence. ' : ''}${rejected}`);
    const entries = [...b.reference_seasons, b.target_season];
    const rows = entries.map(row => `<tr><td>${html(row.end_year)} ${row.end_year === b.target_season.end_year ? '<strong>(target)</strong>' : ''}</td><td>${html(row.period.map(pair => `${pair[0]}-${String(pair[1]).padStart(2,'0')}`).join(' → '))}</td><td>${row.usable ? `${fmt(row.precipitation_mm, 1)} mm` : 'UNUSABLE'}</td><td>${html(row.coverage_pct_by_month?.map(x => `${fmt(x, 0)}%`).join(' / ') || row.reason || '—')}</td></tr>`).join('');
    $p('precision-season-table').innerHTML = `<div class="precision-table-scroll"><table><thead><tr><th>Season ends</th><th>Consecutive months</th><th>Rain total</th><th>Coverage / issue</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    const quality = [
      `<p><strong>Source:</strong> ${html(source.provider)}</p>`,
      `<p><strong>Data window:</strong> ${html(payload.years_received.join(', ') || 'No years loaded')}</p>`,
      `<p><strong>Coordinate source:</strong> Farmer-entered farm point (${fmt(payload.farm.latitude,5)}, ${fmt(payload.farm.longitude,5)})</p>`,
      `<p><strong>Coverage:</strong> Minimum 95% of days within each selected month. Partial months excluded.</p>`,
      `<p><strong>Previous-season mean:</strong> ${fmt(b.recent_mean_rainfall_mm, 1)} mm; standard deviation ${fmt(b.historical_stddev_mm, 1)} mm.</p>`,
      `<p><strong>Data hash count:</strong> ${source.raw_hashes.length}; copied in downloaded evidence JSON.</p>`,
      `<p><strong>Soil inputs:</strong> ${html(payload.farm.soil_source)} (not independently validated); pH ${fmt(payload.farm.soil_ph)}, organic matter ${fmt(payload.farm.organic_matter_pct)}%.</p>`,
      `<p><strong>Limits:</strong> ${html(source.spatial_scale)}. No parcel-scale NDVI, soil-water sensor values or crop-yield forecast is claimed.</p>`,
      '<p><strong>Source reference:</strong> <a href="https://power.larc.nasa.gov/docs/services/api/temporal/daily/" target="_blank" rel="noopener noreferrer">NASA POWER Daily API</a>.</p>',
      ...b.cautions.map(w => `<p class="precision-caution">⚠ ${html(w)}</p>`),
    ];
    $p('precision-quality').innerHTML = quality.join('');
  }
  async function fetchBench(mode) {
    if (fetching) return;
    const ctx = safeFarm();
    if (!ctx.farm) { setStatus('A saved farm profile is required.'); return; }
    const id = ++runId;
    fetching = true;
    for (const name of ['precision-fetch','precision-demo']) $p(name).disabled = true;
    setStatus(mode === 'nasa' ? 'Retrieving historical NASA POWER daily records, with bounded requests and cached results. May take longer on first use…' : 'Generating explicitly SYNTHETIC historical samples for UI rehearsal…');
    try {
      const res = await fetch('/api/precision/assess', {
        method:'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({farm:ctx.farm, baseline_years:Number($p('precision-years').value),
          end_year:Number($p('precision-year').value), mode})
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || `HTTP ${res.status}`);
      if (runId === id) render(result);
    } catch (err) { if (runId === id) { last = null; setStatus('NASA precision request failed: '+err.message+'. No missing values were fabricated.'); $p('precision-badge').textContent = 'UNAVAILABLE'; } }
    finally { fetching = false; for (const name of ['precision-fetch','precision-demo']) $p(name).disabled = false; }
  }
  async function checkBoundary() {
    const {farm, boundary} = safeFarm();
    const out = $p('precision-boundary-result');
    if (!boundary) { out.textContent = 'No saved GeoJSON polygon. Enter one in Farm Profile before checking area.'; return; }
    try {
      const response = await fetch('/api/precision/boundary', {method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({geometry:JSON.parse(boundary), reported_area_ha:farm.area_ha, farm_latitude:farm.latitude, farm_longitude:farm.longitude})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
      out.textContent = `Approximate polygon area: ${fmt(result.approximate_area_ha,3)} ha; reported: ${fmt(result.reported_area_ha,3)} ha; difference: ${fmt(result.difference_pct,1)}%. ${result.flags.join(' ') || 'No major consistency flags.'} NOT A SURVEY.`;
    } catch(err) { out.textContent = 'Cannot validate boundary: '+err.message; }
  }
  function exportEvidence() {
    if (!last) return;
    const blob = new Blob([JSON.stringify({...last, exported_at:new Date().toISOString(),
      export_notice:'Historical NASA data only if benchmark data_class is historical_nasa; never measured field data.'},null,2)],{type:'application/json'});
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = `AgriORBIT_NASA_Precision_${last.benchmark.target_season.end_year}.json`;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function init() {
    $p('precision-fetch')?.addEventListener('click',()=>fetchBench('nasa'));
    $p('precision-demo')?.addEventListener('click',()=>fetchBench('synthetic'));
    $p('precision-boundary')?.addEventListener('click',checkBoundary);
    $p('precision-export')?.addEventListener('click',exportEvidence);
  }
  window.AgriOrbitPrecision = { invalidate, status:()=>last?.benchmark?.status || 'none' };
  window.addEventListener('DOMContentLoaded',init);
})();

/** AgriORBIT Phase 27: strictly decorative 15-second seed-to-seedling sequence.
 * Fifteen static frames derived from the user-selected animation, 1 second each.
 * No NASA API, rover telemetry, or sensor calibration is implied.
 */
(() => {
  'use strict';
  const DURATION_MS = 15000;
  const FRAME_COUNT = 15;
  const ASSETS = document.querySelector('meta[name="agriorbit-asset-base"]')?.content || '/assets/';
  const image = document.getElementById('cal-sprout-image');
  const value = document.getElementById('cal-sprout-percent');
  const countdown = document.getElementById('cal-seed-countdown');
  const bar = document.getElementById('cal-seed-bar');
  const stage = document.getElementById('cal-sprout-stage');
  const note = document.getElementById('cal-cinematic-note');
  const mainBar = document.getElementById('cal-progress-fill');
  const mainMeter = document.getElementById('cal-progress');
  const mainValue = document.getElementById('cal-progress-value');
  const mainLabel = document.getElementById('cal-progress-label');
  const sequenceTime = document.getElementById('cal-sequence-time');
  const bootClock = document.getElementById('cal-boot-clock');
  const milestones = Array.from(document.querySelectorAll('[data-cal-stage]'));
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const overlay = document.getElementById('calibration');
  // An explicit preview override is essential if Windows has Reduce Motion enabled.
  const forceFullMotion = new URLSearchParams(location.search).has('force-15');
  if (!image || !value || !countdown || !bar || !stage || !note || !mainBar || !mainMeter || !mainValue || !mainLabel) return;

  let raf = 0;
  let begun = 0;
  let lastFrame = -1;
  let lastPhase = -1;
  let lastUiPaint = -Infinity;
  let done = true;
  let completion = Promise.resolve();
  let resolveCompletion = null;
  let runToken = 0;
  const engineStatus = document.getElementById('cal25-engine-state');
  const core = document.getElementById('cal26-living-core');
  const coreImage = document.getElementById('cal26-core-animation');
  const coreStatus = document.getElementById('cal26-core-status');
  const corePhases = ['CORE AWAKENING','GERMINATION SEQUENCE','ORBITAL FIELD MODEL','EMERALD LEAF UNFURL','CINEMATIC CORE READY'];
  function restartLivingCore(token) {
    if (!coreImage) return;
    // Phase 27: browser-composited motion around ONE static WebP. Avoid repeatedly
    // decoding an animated GIF (and downloading it again) at each boot replay.
    coreImage.src = `${ASSETS}agriorbit-living-core-fast.webp?v=phase28-official-leaf-cursor-2.8.0`;
    // Reset the CSS heartbeat and rotating aura on intentional replay.
    if (core) {
      core.classList.remove('cal27-restarting');
      void core.offsetWidth;
      core.classList.add('cal27-restarting');
    }
  }
  const preload = [];
  for (let i = 0; i < FRAME_COUNT; i++) {
    const pic = new Image();
    pic.src = `${ASSETS}boot-frames/seed-${String(i).padStart(2, '0')}.webp`;
    preload.push(pic);
  }
  // The single elapsed-time clock drives BOTH decorative bars and all five milestones.
  // Every 3 seconds advances a milestone; no milestone stands for NASA/rover validation.
  const phases = [
    {end: 3, text:'SEED DORMANT', label:'01 / ORBITAL INITIALIZATION'},
    {end: 6, text:'GERMINATION', label:'02 / GERMINATION'},
    {end: 9, text:'SPROUT EMERGING', label:'03 / SEEDLING EMERGENCE'},
    {end: 12, text:'FIRST TRUE LEAVES', label:'04 / LEAF UNFURLING'},
    {end: 15, text:'SEEDLING ESTABLISHED', label:'05 / CINEMATIC COMPLETE'}
  ];
  function draw(p) {
    const clamped = Math.max(0, Math.min(1, p));
    const percent = Math.round(clamped * 100);
    const elapsedSeconds = clamped * 15;
    const i = Math.min(FRAME_COUNT-1, Math.floor(Math.min(clamped, .999999) * FRAME_COUNT));
    const phase = Math.min(4, Math.floor(Math.min(clamped, .999999) * 5));
    if (i !== lastFrame) { image.src = preload[i]?.src || `${ASSETS}boot-frames/seed-${String(i).padStart(2,'0')}.webp`; lastFrame = i; }
    // Progress bars update on every requestAnimationFrame to remain smooth.
    // Labels, ARIA text, and stage lights update at ~10Hz instead of 60Hz.
    const clock = performance.now();
    const shouldPaintUI = clamped === 0 || clamped === 1 || i !== lastFrame || phase !== lastPhase || clock - lastUiPaint >= 100;
    if (!shouldPaintUI) {
      const scale = `scaleX(${clamped.toFixed(5)})`;
      mainBar.style.setProperty('transform', scale, 'important');
      bar.style.setProperty('transform', scale, 'important');
      return;
    }
    lastUiPaint=clock; lastPhase=phase;
    value.textContent = `${percent}%`;
    countdown.textContent = percent === 100 ? 'COMPLETE' : `${Math.ceil(15-elapsedSeconds)}s`;
    // The same monotonic timestamp drives image, text and BOTH visual fills.
    // Inline !important explicitly beats legacy Phase19 keyframes and stale CSS.
    // transform is compositor-friendly (no width reflow on every frame).
    const scale = `scaleX(${clamped.toFixed(5)})`;
    mainBar.style.setProperty('transform', scale, 'important');
    bar.style.setProperty('transform', scale, 'important');
    if (engineStatus) engineStatus.textContent =
      `PHASE 27 · LIVE AI CORE VISUAL · 15s TIMER · ${percent}% · ${Math.max(0, (15-elapsedSeconds)).toFixed(1)}s REMAINING`;
    stage.textContent = phases[phase].text;
    if (core) core.dataset.corePhase = String(phase);
    if (coreStatus) coreStatus.textContent = clamped === 1 ?
      'CINEMATIC CORE COMPLETE · NOT LIVE AI' : `${corePhases[phase]} · SIMULATED`;
    // The main bar and seedling mini-bar use the SAME CSS animation duration.
    mainMeter.setAttribute('aria-valuenow', String(percent));
    mainValue.textContent = `${percent}%`;
    mainLabel.textContent = phases[phase].label;
    mainMeter.style.setProperty('--cinematic-percent', `${clamped * 100}%`);
    const elapsedLabel = `00:${String(Math.min(15, Math.floor(elapsedSeconds))).padStart(2,'0')}`;
    if (sequenceTime) sequenceTime.textContent = `${elapsedLabel} / 00:15`;
    if (bootClock) bootClock.textContent = `BOOT SEQUENCE / ${elapsedLabel}`;
    for (let index = 0; index < milestones.length; index++) {
      milestones[index].classList.toggle('is-complete', clamped === 1 || index < phase);
      milestones[index].classList.toggle('is-active', clamped < 1 && index === phase);
    }
    window.AgriOrbitBootFX?.progress(percent);
    note.textContent = percent === 100 ?
      '15-second growth animation complete · Review independent readiness results.' :
      `Cinematic sequence 00:${String(Math.ceil(15-elapsedSeconds)).padStart(2,'0')} remaining · Local checks run independently.`;
  }
  function finish() {
    cancelAnimationFrame(raf); raf = 0;
    if (done) return;
    done = true;
    overlay?.classList.remove('boot19-playing');
    overlay?.classList.add('boot19-complete');
    draw(1);
    const resolve = resolveCompletion;
    resolveCompletion = null;
    if (resolve) resolve();
  }
  function animate(now, token) {
    if (done || token !== runToken) return;
    const p = Math.min(1, (now-begun)/DURATION_MS);
    draw(p);
    if (p >= 1) finish();
    else raf = requestAnimationFrame(n => animate(n, token));
  }
  function start() {
    stop();
    const token = ++runToken;
    lastFrame = -1;lastPhase=-1;lastUiPaint=-Infinity;
    done = false;
    restartLivingCore(token);
    // Remove and recreate animation state on replay, including after skipped runs.
    overlay?.classList.remove('boot19-playing', 'boot19-complete', 'boot19-force-full');
    void mainBar.offsetWidth;
    if (forceFullMotion) overlay?.classList.add('boot19-force-full');
    completion = new Promise(resolve => {resolveCompletion = resolve;});
    begun = performance.now();
    draw(0);
    if (reduced.matches && !forceFullMotion) {
      if (engineStatus) engineStatus.textContent = 'REDUCED MOTION ACTIVE · Add ?force-15=1 for the full 15-second intro';
      finish(); return;
    }
    overlay?.classList.add('boot19-playing', 'phase25-boot-engine', 'phase26-living-core-active');
    begun = performance.now();
    raf = requestAnimationFrame(n => animate(n, token));
  }
  function skip() { finish(); }
  function stop() {
    cancelAnimationFrame(raf); raf=0;
    ++runToken;
    if (!done) finish();
  }
  function wait() { return completion; }
  window.AgriOrbitSeedlingBoot = {
    start, stop, skip, wait,
    get durationMs(){return DURATION_MS;},
    get elapsedMs(){return done ? DURATION_MS : Math.min(DURATION_MS, performance.now()-begun);},
    get forced(){return forceFullMotion;}
  };
  reduced.addEventListener?.('change', () => { if (reduced.matches && !forceFullMotion) finish(); });
  // Independent bootstrap: even an unrelated dashboard initialization exception
  // must not silently leave the calibration animation stuck at 0%.
  if (overlay && !overlay.classList.contains('is-hidden')) start();
})();

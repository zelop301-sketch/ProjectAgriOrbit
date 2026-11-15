/* AgriORBIT Phase 28 • Official SVG Leaf Cursor + Green Orb Wind Trails
 * Cosmetic animation only. No cursor tracking leaves this browser.
 * One small, bounded 2D canvas paints short-lived aerodynamic wind ribbons.
 * Never intercepts mouse input; respects touch, editable fields and reduced motion.
 */
(() => {
  'use strict';
  const ENABLED_KEY = 'agriorbit:official-leaf:v4';
  const MOTION_KEY = 'agriorbit:official-leaf-motion:v4';
  const WIND_KEY = 'agriorbit:official-leaf-wind:v4';
  const MAX_RIBBONS = 75;
  const toggle = document.getElementById('agri-cursor-toggle');
  const toggleText = document.getElementById('agri-cursor-toggle-text');
  const windToggle = document.getElementById('agri-wind-toggle');
  const windToggleText = document.getElementById('agri-wind-toggle-text');
  const eligible = window.matchMedia('(any-pointer: fine)');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const textEditable = 'input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="color"]), textarea, [contenteditable="true"], [role="textbox"]';
  const interactive = 'a, button, select, label, summary, [role="button"], [role="link"], [data-view], [data-holo-layer]';
  let saved = 'on', windSaved = 'breeze', motionSaved = 'off';
  try {
    saved = localStorage.getItem(ENABLED_KEY) || 'on';
    motionSaved = localStorage.getItem(MOTION_KEY) || 'off';
    windSaved = localStorage.getItem(WIND_KEY) || 'breeze';
  } catch (_) { /* storage can be restricted; cosmetic effect still works */ }
  let wantsCursor = saved !== 'off';
  let explicitMotion = motionSaved === 'on';
  let windMode = ['off', 'breeze', 'gust'].includes(windSaved) ? windSaved : 'breeze';
  let active = false, pointerVisible = false, editingNow = false;
  let x = 0, y = 0, rafId = 0;
  let leaf = null, spark = null, windCanvas = null, windCtx = null;
  const trail = [];
  const ribbons = [];
  const trailPoints = Array.from({length: 7}, () => ({x: 0, y: 0}));
  let lastMove = null;
  let lastEmit = 0;
  let lastPointerAt = 0;
  let viewportWidth = 0, viewportHeight = 0;
  let windDirty = false;

  function resizeWind() {
    if (!windCanvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    viewportWidth = window.innerWidth;
    viewportHeight = window.innerHeight;
    windCanvas.width = Math.round(viewportWidth * dpr);
    windCanvas.height = Math.round(viewportHeight * dpr);
    windCanvas.style.width = `${viewportWidth}px`;
    windCanvas.style.height = `${viewportHeight}px`;
    windCtx = windCanvas.getContext('2d', { alpha: true });
    if (windCtx) windCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ribbons.length = 0;
    windDirty = false;
  }

  function create() {
    if (leaf) return;
    leaf = document.createElement('div');
    leaf.id = 'agri-leaf-cursor';
    leaf.className = 'agri-leaf-cursor agri-bio-leaf-cursor';
    leaf.setAttribute('aria-hidden', 'true');
    leaf.innerHTML = `
      <span class="leaf-cursor-halo"></span>
      <span class="leaf-cursor-ring leaf-cursor-ring-one"><i class="leaf-cursor-orb"></i></span>
      <span class="leaf-cursor-ring leaf-cursor-ring-two"><i class="leaf-cursor-orb"></i></span>
      <span class="leaf-cursor-ring leaf-cursor-ring-three"><i class="leaf-cursor-orb"></i></span>
      <span class="agri-leaf-vein-wrap">
        <svg class="agri-leaf-svg" viewBox="0 0 58 58" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
          <defs>
            <linearGradient id="agri-leaf-fill" x1=".17" y1=".1" x2=".87" y2=".85" gradientUnits="objectBoundingBox"><stop stop-color="#eaffb8"/><stop offset=".28" stop-color="#3cff7f"/><stop offset=".73" stop-color="#00b84b"/><stop offset="1" stop-color="#005c48"/></linearGradient>
          </defs>
          <path class="agri-leaf-body" d="M5 5 C26 2 48 10 47 29 C46 48 21 49 5 5 Z" fill="url(#agri-leaf-fill)" stroke="#bdffc3" stroke-width="1.4"/>
          <path class="agri-leaf-vein" d="M6 6 Q22 26 46 39 M19 20 L23 8 M27 28 L39 19 M33 34 L21 41" fill="none" stroke="#d6ffcc" stroke-width="1.7" stroke-linecap="round"/>
        </svg>
      </span>
      <span class="leaf-cursor-core"></span>
      <span class="agri-leaf-hotspot"></span>`;
    spark = document.createElement('div');
    spark.className = 'leaf-cursor-trail';
    spark.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < 7; i++) {
      const particle = document.createElement('span');
      particle.className = 'leaf-cursor-particle';
      particle.style.opacity = String(Math.max(0.12, 0.61 - i * 0.07));
      spark.appendChild(particle);
      trail.push(particle);
    }
    windCanvas = document.createElement('canvas');
    windCanvas.id = 'agri-leaf-wind';
    windCanvas.className = 'agri-leaf-wind';
    windCanvas.setAttribute('aria-hidden', 'true');
    document.body.append(windCanvas, spark, leaf);
    resizeWind();
  }

  function shouldUse() { return eligible.matches && wantsCursor && (!reduceMotion.matches || explicitMotion); }

  function updateButton() {
    const usable = eligible.matches;
    if (toggle) {
      toggle.hidden = !usable;
      toggle.setAttribute('aria-pressed', String(shouldUse()));
      toggle.setAttribute('aria-label', shouldUse() ? 'Disable AgriORBIT leaf cursor' : (reduceMotion.matches && wantsCursor ? 'Enable animated leaf cursor despite reduced-motion setting' : 'Enable AgriORBIT leaf cursor'));
      if (toggleText) toggleText.textContent = shouldUse() ? 'LEAF FX ON' : (reduceMotion.matches && wantsCursor ? 'ENABLE LEAF FX' : 'LEAF FX OFF');
      toggle.classList.toggle('is-on', shouldUse());
    }
    if (windToggle) {
      windToggle.hidden = !usable;
      windToggle.disabled = !shouldUse();
      windToggle.setAttribute('aria-pressed', String(windMode !== 'off'));
      windToggle.setAttribute('aria-label', `Wind trail intensity: ${windMode}. Click to change.`);
      windToggle.title = `Wind trail: ${windMode}. Click to cycle Breeze / Gust / Off.`;
      if (windToggleText) windToggleText.textContent = `WIND: ${windMode.toUpperCase()}`;
      windToggle.classList.toggle('is-on', windMode !== 'off' && shouldUse());
    }
  }

  function clearWind() {
    ribbons.length = 0;
    lastMove = null;
    lastEmit = 0;
    if (windCtx && windDirty) windCtx.clearRect(0, 0, viewportWidth, viewportHeight);
    windDirty = false;
  }

  function stop() {
    active = false;
    pointerVisible = false;
    editingNow = false;
    document.body.classList.remove('agri-leaf-enabled', 'agri-leaf-editing');
    document.documentElement.classList.remove('agri-leaf-explicit');
    if (leaf) leaf.classList.remove('leaf-cursor-visible', 'leaf-cursor-interactive');
    if (spark) spark.classList.remove('leaf-trail-visible');
    clearWind();
    if (rafId) cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function update() {
    if (!shouldUse()) { stop(); updateButton(); return; }
    create();
    active = true;
    document.documentElement.classList.toggle('agri-leaf-explicit', explicitMotion && reduceMotion.matches);
    document.body.classList.add('agri-leaf-enabled');
    updateButton();
  }

  // Ribbons point *against* the travel direction, like wind streaming from a leaf.
  // Distance, count and lifetime increase modestly with pointer speed, but remain bounded.
  function emitWind(px, py, now) {
    if (!windCtx || windMode === 'off' || editingNow || !lastMove) return;
    const dx = px - lastMove.x;
    const dy = py - lastMove.y;
    const distance = Math.hypot(dx, dy);
    const dt = now - lastMove.time;
    if (distance < 3 || distance > 220 || dt > 200 || dt <= 0 || now - lastEmit < 15) return;
    const speed = Math.min(2100, distance / Math.max(dt, 8) * 1000);
    if (speed < 65) return;
    lastEmit = now;
    const ux = dx / distance, uy = dy / distance;
    const nx = -uy, ny = ux;
    const intensity = Math.min(1, speed / 1500);
    const gust = windMode === 'gust';
    const count = gust ? (speed > 650 ? 3 : 2) : (speed > 800 ? 2 : 1);
    const countCap = Math.max(0, MAX_RIBBONS - ribbons.length);
    for (let i = 0; i < Math.min(count, countCap); i++) {
      const side = i % 2 === 0 ? 1 : -1;
      const spread = side * (6 + i * 6 + Math.random() * 7);
      const length = (gust ? 49 : 33) + intensity * (gust ? 79 : 57) + Math.random() * 18;
      const ribbon = {
        x: px - ux * (12 + Math.random() * 10) + nx * spread,
        y: py - uy * (12 + Math.random() * 10) + ny * spread,
        ux, uy, nx, ny, length,
        offset: 7 + i * 5,
        bend: side * (8 + Math.random() * 15),
        drift: (Math.random() - .5) * 18,
        born: now,
        lifetime: (gust ? 560 : 450) + Math.random() * 190,
        thickness: (gust ? 2.4 : 1.65) + intensity * 1.15,
        color: i % 3, // emerald, cyan, pale mint
        phase: Math.random() * Math.PI * 2,
      };
      ribbons.push(ribbon);
    }
  }

  function renderWind(now) {
    if (!windCtx) return;
    const ctx = windCtx;
    if (windMode === 'off' || editingNow) { clearWind(); return; }
    // Avoid clearing the entire viewport on every idle frame.
    if (ribbons.length === 0 && !windDirty) return;
    ctx.clearRect(0, 0, viewportWidth, viewportHeight);
    if (ribbons.length === 0) { windDirty = false; return; }
    windDirty = true;
    const colors = [
      ['rgba(0,255,102,0)', 'rgba(0,255,102,0.70)', 'rgba(191,255,209,0.98)'],
      ['rgba(0,240,255,0)', 'rgba(0,240,255,0.57)', 'rgba(146,255,249,0.95)'],
      ['rgba(176,255,179,0)', 'rgba(146,255,176,0.56)', 'rgba(235,255,238,0.99)'],
    ];
    for (let i = ribbons.length - 1; i >= 0; i--) {
      const r = ribbons[i];
      const age = (now - r.born) / r.lifetime;
      if (age >= 1) { ribbons.splice(i, 1); continue; }
      const remaining = 1 - age;
      const alpha = Math.pow(remaining, 1.6);
      const flutter = Math.sin(age * 9 + r.phase) * 7 * age;
      const flow = age * (10 + r.length * .19);
      const headX = r.x - r.ux * flow + r.nx * flutter;
      const headY = r.y - r.uy * flow + r.ny * flutter;
      const tailX = headX - r.ux * r.length;
      const tailY = headY - r.uy * r.length;
      const midX = (headX + tailX) / 2 + r.nx * r.bend * (1 + .4 * age);
      const midY = (headY + tailY) / 2 + r.ny * r.bend * (1 + .4 * age);
      const col = colors[r.color];
      const gradient = ctx.createLinearGradient(tailX, tailY, headX, headY);
      gradient.addColorStop(0, col[0]);
      gradient.addColorStop(.50, col[1]);
      gradient.addColorStop(1, col[2]);
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = gradient;
      ctx.lineWidth = r.thickness * (0.75 + remaining * .25);
      ctx.lineCap = 'round';
      ctx.shadowBlur = windMode === 'gust' ? 15 : 9;
      ctx.shadowColor = r.color === 1 ? '#00f0ff' : '#00ff66';
      ctx.beginPath();
      ctx.moveTo(tailX, tailY);
      ctx.quadraticCurveTo(midX, midY, headX, headY);
      ctx.stroke();
      // Tiny luminous airborne dust mote near the front of a ribbon.
      if (r.color !== 2 && age < .68) {
        ctx.shadowBlur = 8;
        ctx.fillStyle = r.color === 1 ? '#75fffa' : '#bcffce';
        ctx.beginPath();
        ctx.arc(headX, headY, Math.max(.6, r.thickness * .48 * remaining), 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
  }

  function frame(now) {
    if (!active || !pointerVisible) { rafId = 0; return; }
    // Follow the actual pointer exactly; decoration never changes click targets.
    leaf.style.transform = `translate3d(${x - 13}px, ${y - 13}px, 0)`;
    let fx = x, fy = y;
    for (let i = 0; i < trailPoints.length; i++) {
      const t = trailPoints[i];
      const smooth = 0.34 - i * .039;
      t.x += (fx - t.x) * smooth;
      t.y += (fy - t.y) * smooth;
      trail[i].style.transform = `translate3d(${t.x - 3}px,${t.y - 3}px,0)`;
      fx = t.x; fy = t.y;
    }
    renderWind(now);
    // Orbiting orbs are CSS animations; stop JS updates when pointer is idle.
    if (now - lastPointerAt < 420 || ribbons.length > 0) rafId = requestAnimationFrame(frame);
    else rafId = 0;
  }

  function onPointerMove(e) {
    if (!active || e.pointerType === 'touch') return;
    x = e.clientX; y = e.clientY;
    lastPointerAt = performance.now();
    const target = e.target instanceof Element ? e.target : null;
    const editing = Boolean(target && target.closest(textEditable));
    editingNow = editing;
    leaf.classList.toggle('leaf-cursor-interactive', Boolean(target && target.closest(interactive)) && !editing);
    leaf.classList.toggle('leaf-cursor-visible', !editing);
    spark.classList.toggle('leaf-trail-visible', !editing);
    if (editing) clearWind();
    const now = performance.now();
    if (!pointerVisible) {
      trailPoints.forEach(p => { p.x = x; p.y = y; });
      pointerVisible = true;
    } else if (!editing) {
      emitWind(x, y, now);
    }
    lastMove = editing ? null : { x, y, time: now };
    document.body.classList.toggle('agri-leaf-editing', editing);
    if (!rafId) rafId = requestAnimationFrame(frame);
  }

  function hideOutside(e) {
    if (e.relatedTarget !== null || !leaf) return;
    leaf.classList.remove('leaf-cursor-visible');
    if (spark) spark.classList.remove('leaf-trail-visible');
    pointerVisible = false;
    editingNow = false;
    document.body.classList.remove('agri-leaf-editing');
    clearWind();
  }

  function clickPulse(e) {
    if (!active || !leaf || (e.pointerType && e.pointerType !== 'mouse') || e.button !== 0 || editingNow) return;
    const pulse = document.createElement('span');
    pulse.className = 'leaf-cursor-click-pulse';
    pulse.style.left = `${e.clientX}px`;
    pulse.style.top = `${e.clientY}px`;
    pulse.setAttribute('aria-hidden', 'true');
    document.body.appendChild(pulse);
    pulse.addEventListener('animationend', () => pulse.remove(), {once: true});
  }

  if (toggle) toggle.addEventListener('click', () => {
    if (reduceMotion.matches && wantsCursor && !explicitMotion) {
      explicitMotion = true;
      try { localStorage.setItem(MOTION_KEY, 'on'); } catch (_) {}
    } else wantsCursor = !wantsCursor;
    try { localStorage.setItem(ENABLED_KEY, wantsCursor ? 'on' : 'off'); } catch (_) {}
    update();
  });
  if (windToggle) windToggle.addEventListener('click', () => {
    windMode = ({ breeze: 'gust', gust: 'off', off: 'breeze' })[windMode];
    try { localStorage.setItem(WIND_KEY, windMode); } catch (_) {}
    if (windMode === 'off') clearWind();
    updateButton();
  });
  document.addEventListener('pointermove', onPointerMove, {passive: true});
  // Fallback for mouse-capable browser configurations with limited pointer events.
  if (!window.PointerEvent) document.addEventListener('mousemove', onPointerMove, {passive: true});
  document.addEventListener('pointerdown', clickPulse, {passive: true});
  document.addEventListener('pointerout', hideOutside, {passive: true});
  document.addEventListener('visibilitychange', () => { if (document.hidden) hideOutside({relatedTarget: null}); });
  window.addEventListener('resize', resizeWind, {passive: true});
  reduceMotion.addEventListener?.('change', update);
  if (eligible.addEventListener) eligible.addEventListener('change', update);
  else if (eligible.addListener) eligible.addListener(update);
  window.AgriORBITCursor = { state: () => ({enabled: shouldUse(), wind:windMode, active, type:'native-svg-leaf', ribbons:ribbons.length}) };
  update();
})();

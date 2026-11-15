/* AgriORBIT Phase 31: visible droplet FX, real in-app mouse clicks.
 * A previous version could be silently disabled by hybrid pointer media queries,
 * reduced motion, saved mute preference, or a short ~0.8 second life.
 * Capture-phase pointerdown and a dedicated TEST button make this observable.
 * Visual only: never intercepts input, no background animation loop.
 */
(() => {
  'use strict';
  const PREF = 'agriorbit:splash-visual:v2'; // new default; don't inherit older OFF settings
  const OVERRIDE_PREF = 'agriorbit:splash-allow-motion:v2';
  const MAX_IMPACTS = 10;
  const MIN_GAP_MS = 90;
  const LIFETIME_MS = 1250;
  const toggle = document.getElementById('agri-drop-fx-toggle');
  const label = document.getElementById('agri-drop-fx-toggle-text');
  const testButton = document.getElementById('agri-splash-test');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let enabled = true, allowReducedMotion = false;
  try {
    enabled = localStorage.getItem(PREF) !== 'off';
    allowReducedMotion = localStorage.getItem(OVERRIDE_PREF) === 'on';
  } catch (_) { /* private browsing can disable storage */ }
  let lastImpact = -Infinity;
  let lastGesture = '';
  const active = new Set();
  const layer = document.createElement('div');
  layer.id = 'agri-droplet-layer';
  layer.className = 'agri-droplet-layer';
  layer.setAttribute('aria-hidden', 'true');
  document.body.appendChild(layer);

  function motionAllowed() { return !reducedMotion.matches || allowReducedMotion; }
  function playable() { return enabled && motionAllowed(); }
  function clear() { for (const el of [...active]) {active.delete(el);el.remove();} }
  function paintToggle() {
    if (toggle) {
      toggle.hidden = false; // always expose why effect is off, including hybrid devices
      toggle.disabled = false;
      const on = playable();
      toggle.classList.toggle('is-on', on);
      toggle.setAttribute('aria-pressed', String(on));
      toggle.setAttribute('aria-label', on ? 'Disable water droplet animation' : 'Enable water droplet animation');
      toggle.title = reducedMotion.matches && !allowReducedMotion
        ? 'Reduced motion enabled: click to explicitly enable animated splash'
        : 'Turn the visible click splash on or off';
      if (label) label.textContent = on ? 'SPLASH FX ON' :
        (reducedMotion.matches && !allowReducedMotion ? 'ENABLE SPLASH FX' : 'SPLASH FX OFF');
    }
    if (testButton) testButton.disabled = !playable();
    layer.classList.toggle('agri-drop-motion-override', allowReducedMotion);
  }
  function spawn(x, y, source = 'mouse') {
    if (!playable() || document.hidden) return false;
    if (active.size >= MAX_IMPACTS) {
      const oldest = active.values().next().value;
      if (oldest) { active.delete(oldest); oldest.remove(); }
    }
    const impact = document.createElement('span');
    impact.className = 'agri-droplet-impact';
    impact.style.left = `${Math.max(15, Math.min(innerWidth-15, x))}px`;
    impact.style.top = `${Math.max(15, Math.min(innerHeight-15, y))}px`;
    impact.setAttribute('aria-hidden','true');
    impact.innerHTML = `<span class="agri-droplet-flash"></span><span class="agri-droplet-bead"></span>
       <span class="agri-droplet-ring ring-1"></span><span class="agri-droplet-ring ring-2"></span>
       <span class="agri-droplet-ring ring-3"></span>`;
    for (let i = 0; i < 8; i++) {
      const sp = document.createElement('i');
      sp.className = 'agri-droplet-spark';
      const angle = i * Math.PI / 4 - Math.PI / 2;
      const distance = 44 + (i % 3) * 11;
      sp.style.setProperty('--dx', `${Math.cos(angle)*distance}px`);
      sp.style.setProperty('--dy', `${Math.sin(angle)*distance}px`);
      sp.style.setProperty('--delay', `${(i%3)*20}ms`);
      impact.appendChild(sp);
    }
    layer.appendChild(impact);
    active.add(impact);
    const cleanup = () => { if (active.delete(impact)) impact.remove(); };
    impact.addEventListener('animationend', e => { if (e.target === impact) cleanup(); }, {once:true});
    window.setTimeout(cleanup, LIFETIME_MS + 160);
    lastGesture = source;
    return true;
  }
  function mouseGesture(event) {
    // Capturing at window level works even if an application widget stops bubbling.
    if (event.button !== 0 || document.hidden) return;
    // The explicit diagnostic creates a single centered splash; do not double-trigger.
    if (testButton?.contains(event.target) || toggle?.contains(event.target)) return;
    if (event.type === 'pointerdown' && event.pointerType && event.pointerType !== 'mouse') return;
    if (!playable()) return;
    const now = performance.now();
    if (now - lastImpact < MIN_GAP_MS) return;
    lastImpact = now;
    spawn(event.clientX, event.clientY);
  }
  if (window.PointerEvent) window.addEventListener('pointerdown', mouseGesture, {capture:true, passive:true});
  else window.addEventListener('mousedown', mouseGesture, {capture:true, passive:true});

  toggle?.addEventListener('click', () => {
    if (reducedMotion.matches && !allowReducedMotion) {
      // Animation starts only after explicit user opt-in if reduced motion is set.
      allowReducedMotion = true; enabled = true;
      try {localStorage.setItem(OVERRIDE_PREF,'on');} catch (_) {}
    } else enabled = !enabled;
    try {localStorage.setItem(PREF, enabled ? 'on' : 'off');} catch (_) {}
    if (!playable()) clear();
    paintToggle();
  });
  testButton?.addEventListener('click', () => {
    // Explicit button is the diagnostic, not dependent on pointer media queries.
    spawn(innerWidth * 0.52, innerHeight * 0.42, 'test-button');
    if (testButton) {
      testButton.classList.add('splash-fired');
      window.setTimeout(() => testButton.classList.remove('splash-fired'),400);
    }
  });
  document.addEventListener('visibilitychange', () => {if (document.hidden) clear();});
  reducedMotion.addEventListener?.('change', () => {if (!motionAllowed()) clear(); paintToggle();});
  window.AgriORBITDropletFX = {
    state: () => ({enabled: playable(), active:active.size, mode:lastGesture, build:'phase32'}),
    test: () => spawn(innerWidth*.5, innerHeight*.45,'manual-test'),
    enable: () => { enabled=true; paintToggle(); },
    disable: () => {enabled=false;clear();paintToggle();}
  };
  paintToggle();
})();
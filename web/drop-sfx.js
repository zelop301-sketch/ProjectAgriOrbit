/* AgriORBIT Phase 12 | Original procedural water-drop click SFX.
 * Audio is generated locally by Web Audio, only after a trusted mouse click.
 * No downloaded sound files, background playback, or mouse telemetry collection.
 * Independent from cosmetic leaf/wind FX; muted state is saved in this browser.
 */
(() => {
  'use strict';
  const PREF = 'agriorbit:water-drop-sfx:v1';
  const toggle = document.getElementById('agri-drop-sfx-toggle');
  const label = document.getElementById('agri-drop-sfx-toggle-text');
  const mouseAvailable = window.matchMedia('(hover: hover) and (pointer: fine)');
  const AudioEngine = window.AudioContext || window.webkitAudioContext;
  const MIN_GAP_MS = 85;
  let enabled = true;
  try { enabled = localStorage.getItem(PREF) !== 'off'; } catch (_) {}
  let ctx = null;
  let lastClickMs = -Infinity;
  let unsupported = !AudioEngine;

  function paintToggle() {
    if (!toggle) return;
    const usable = Boolean(AudioEngine) && mouseAvailable.matches;
    toggle.hidden = !usable;
    toggle.disabled = !usable;
    toggle.classList.toggle('is-on', enabled && usable);
    toggle.setAttribute('aria-pressed', String(enabled && usable));
    toggle.setAttribute('aria-label', enabled ? 'Mute water drop click sounds' : 'Enable water drop click sounds');
    toggle.title = enabled ? 'Water drop sound on each mouse click. Click to mute.' : 'Click to enable water drop sounds.';
    if (label) label.textContent = enabled ? 'DROP SFX ON' : 'DROP SFX OFF';
    if (unsupported) toggle.title = 'This browser does not support Web Audio';
  }

  function audioContext() {
    if (!AudioEngine || !mouseAvailable.matches) return null;
    try {
      if (!ctx || ctx.state === 'closed') ctx = new AudioEngine({ latencyHint: 'interactive' });
      if (ctx.state === 'suspended') {
        // Called directly from the trusted mouse gesture to satisfy browser autoplay policy.
        ctx.resume().catch(() => {});
      }
      return ctx;
    } catch (_) {
      unsupported = true;
      paintToggle();
      return null;
    }
  }

  // A small pitched plip plus a resonant low droplet. No media files or looping audio.
  // All voices disconnect after ~0.23s so many clicks cannot accumulate live nodes.
  function chirp(context, start, fromHz, toHz, peak, length, type = 'sine') {
    const oscillator = context.createOscillator();
    const envelope = context.createGain();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(fromHz, start);
    oscillator.frequency.exponentialRampToValueAtTime(toHz, start + length * .85);
    envelope.gain.setValueAtTime(.0001, start);
    envelope.gain.exponentialRampToValueAtTime(peak, start + .009);
    envelope.gain.exponentialRampToValueAtTime(.0001, start + length);
    oscillator.connect(envelope);
    envelope.connect(context.destination);
    oscillator.onended = () => { oscillator.disconnect(); envelope.disconnect(); };
    oscillator.start(start);
    oscillator.stop(start + length + .012);
  }

  function playDrop() {
    if (!enabled || document.hidden || !mouseAvailable.matches) return false;
    const now = performance.now();
    if (now - lastClickMs < MIN_GAP_MS) return false;
    const context = audioContext();
    if (!context) return false;
    lastClickMs = now;
    const t = context.currentTime + .007;
    // At modest laptop volume: two quiet droplets, reminiscent of a tiny water plop.
    chirp(context, t, 1040, 485, .065, .145);
    chirp(context, t + .024, 420, 238, .028, .188);
    return true;
  }

  // Keep toggle click audible when turning sound ON, silent when turning it OFF.
  // Do not synthesize on touch, keyboard interactions, right-click, or autoplay.
  document.addEventListener('pointerdown', (event) => {
    if (!event.isTrusted || event.pointerType !== 'mouse' || event.button !== 0) return;
    if (event.target === toggle || (toggle && toggle.contains(event.target))) return;
    playDrop();
  }, { passive: true });

  if (toggle) toggle.addEventListener('click', (event) => {
    enabled = !enabled;
    try { localStorage.setItem(PREF, enabled ? 'on' : 'off'); } catch (_) {}
    paintToggle();
    if (enabled && event.detail > 0) playDrop();
  });

  if (mouseAvailable.addEventListener) mouseAvailable.addEventListener('change', paintToggle);
  else if (mouseAvailable.addListener) mouseAvailable.addListener(paintToggle);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && ctx && ctx.state === 'running') ctx.suspend().catch(() => {});
  });
  paintToggle();
})();

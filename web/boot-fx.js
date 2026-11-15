/** Phase 15: decorative boot particle environment.
 * Never represents live NASA data, calibrated sensors or authenticated rover telemetry.
 * Rendering runs only while the boot overlay is visible and motion is allowed.
 */
(() => {
  'use strict';
  const root = document.getElementById('calibration');
  const canvas = document.getElementById('cal-particle-canvas');
  if (!root || !canvas) return;
  const ctx = canvas.getContext('2d', { alpha: true });
  if (!ctx) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let running = false, frame = 0, lastPaint = 0, startAt = 0, completion = 0;
  let width = 0, height = 0, dpr = 1, particles = [];
  const cap = (v, lo, hi) => Math.max(lo,Math.min(hi,v));
  const random = (lo, hi) => lo + Math.random() * (hi-lo);
  function resize() {
    width = Math.max(root.clientWidth,1);
    height = Math.max(root.clientHeight,1);
    dpr = Math.min(window.devicePixelRatio || 1, 1.25);
    canvas.width = Math.round(width*dpr);
    canvas.height = Math.round(height*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    const quantity = width < 620 ? 16 : 30;
    particles = Array.from({ length: quantity }, () => ({
      x:random(0,width), y:random(0,height), vx:random(-.17,.17),vy:random(-.12,.12),
      r:random(.5,1.5), alpha:random(.16,.72),phase:random(0,6.283)
    }));
  }
  function paint(now) {
    if (!running) return;
    if (document.hidden || root.classList.contains('is-hidden') || reduceMotion.matches) { stop(); return; }
    if (now-lastPaint < 40) {frame=requestAnimationFrame(paint);return;}
    const dt=cap((now-lastPaint)/16.6 || 1,.5,2.0);lastPaint=now;
    ctx.clearRect(0,0,width,height);
    const phase=(now-startAt)*.00028;
    for (const p of particles) {
      p.x+=p.vx*dt; p.y+=p.vy*dt;
      if(p.x < -12) p.x=width+9;
      if(p.x > width+12) p.x=-9;
      if(p.y < -12) p.y=height+9;
      if(p.y > height+12) p.y=-9;
      ctx.globalAlpha=p.alpha*(.74+.26*Math.cos(phase*3+p.phase));
      ctx.fillStyle=p.r>1.1?'#6affc5':'#54dfff';
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();
      if(p.r>1.25){
        ctx.strokeStyle='rgba(60,253,213,.20)';ctx.lineWidth=.7;
        ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.x-p.vx*60,p.y-p.vy*60);ctx.stroke();
      }
    }
    ctx.globalAlpha=1;
    // Accent sweep across the radar viewport: purely decorative.
    const cx=width*(width < 840 ? .5 : .39), cy=height*.50;
    const radial=ctx.createRadialGradient(cx,cy,5,cx,cy,Math.min(width,height)*.47);
    radial.addColorStop(0,`rgba(45,239,177,${.018 + completion*.0001})`);
    radial.addColorStop(1,'rgba(15,155,235,0)');
    ctx.fillStyle=radial;ctx.fillRect(0,0,width,height);
    frame=requestAnimationFrame(paint);
  }
  function stop(){running=false;cancelAnimationFrame(frame);frame=0;ctx.clearRect(0,0,width,height);}
  function start(){
    stop();completion=0;resize();startAt=performance.now();lastPaint=0;
    if(reduceMotion.matches || document.hidden)return;
    running=true;frame=requestAnimationFrame(paint);
  }
  function progress(value){completion=cap(Number(value)||0,0,100);root.style.setProperty('--boot-progress',`${completion}%`);}
  window.AgriOrbitBootFX={start,stop,progress};
  window.addEventListener('resize',()=>{if(running)resize();},{passive:true});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();else if(!root.classList.contains('is-hidden')) start();});
  reduceMotion.addEventListener?.('change',()=>{if(reduceMotion.matches)stop();else if(!root.classList.contains('is-hidden'))start();});
})();

/* AgriORBIT Phase 8: Ultra procedural Canvas2D graphics built on the animated software mesh.
 * Meshes use x,y,z world coordinates with orbit camera, depth sorting and
 * perspective projection onto Canvas2D. No remote CDN or false NASA tiles.
 * All rendered terrain, fields, diagnostics, vehicle and lidar are SYNTHETIC.
 */
(() => {
 'use strict';
 const $ = id => document.getElementById(id);
 const clamp = (x,a,b) => Math.max(a,Math.min(b,x));
 const mix = (a,b,t) => a+(b-a)*t;
 function rgb(hex){const h=hex.replace('#','');return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16));}
 const blend=(a,b,t)=>{t=clamp(t,0,1);const ca=rgb(a),cb=rgb(b);return '#'+ca.map((v,i)=>Math.round(mix(v,cb[i],t)).toString(16).padStart(2,'0')).join('');};
 const route = [[.13,.78],[.29,.64],[.61,.56],[.78,.30],[.13,.78]];
 class Hologram {
   constructor(canvas, opts={}) {
     if(!canvas || !canvas.getContext) throw new Error('Canvas2D unavailable');
     this.transparent=Boolean(opts.transparent); this.canvas=canvas; this.ctx=canvas.getContext('2d',{alpha:this.transparent});
     if(!this.ctx) throw new Error('Canvas2D unavailable');
     this.yaw=.65; this.pitch=.68; this.zoom=1; this.layer='structural';
     this.scenario='B'; this.weather='normal'; this.overlay='health';
     this.quality='auto'; this.bloom=true; this.postFX=true; this.sunAngle=55;
     this.day='day'; this.progress=0; this.playing=false; this.selectedZone=1;
     this.irrigation=35; this.drainage=35; this.zones=[22,37,49];
     this.motion=true; this.speed=1; this.loop=false; this.autoOrbit=false; this.cinematic=false;
     this.time=0; this.frameCount=0; this.fps=0; this.fpsAt=0;
     this.drawMsEma=0; this.lastDrawMs=0; this.frameBudgetMs=10; this.refreshFps=0; this.rafFrames=0;this.lastRafSample=0;
     this.targetFPS=100; this.drawIntervalMs=10;this.cameraYawCache=NaN;this.cameraPitchCache=NaN;
     this.adaptiveScale=1; this.dynamicDetail=1; this.lowFpsStreak=0; this.highFpsStreak=0; this.lastAdapt=0;
     this.onFrameStats=null; this.onCinematicStage=null; this.stage=-1; this.roverTransform=null;
     this.reducedMotion=!!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
     if(this.reducedMotion)this.motion=false;
     this.last=0; this.lastDraw=0; this.needsDraw=true; this.disposed=false;
     this.drag=null; this.raf=null; this.onProgress=null;
     this.terrainCache=document.createElement('canvas');
     this.terrainCacheCtx=this.terrainCache.getContext('2d',{alpha:true});
     this.terrainCacheKey='';
     this.resizeObserver=window.ResizeObserver ? new ResizeObserver(()=>this.resize()) : null;
     this.resizeObserver?.observe(canvas.parentElement);
     window.addEventListener('resize',()=>this.resize());
     canvas.addEventListener('pointerdown',e=>{this.autoOrbit=false;this.drag={x:e.clientX,y:e.clientY,yaw:this.yaw,pitch:this.pitch};canvas.setPointerCapture(e.pointerId);});
     canvas.addEventListener('pointermove',e=>{if(!this.drag)return;this.yaw=this.drag.yaw+(e.clientX-this.drag.x)*.008;this.pitch=clamp(this.drag.pitch-(e.clientY-this.drag.y)*.006,.22,1.26);this.needsDraw=true;});
     canvas.addEventListener('pointerup',()=>{this.drag=null;});
     canvas.addEventListener('pointercancel',()=>{this.drag=null;});
     canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=clamp(this.zoom*(e.deltaY>0?.91:1.09),.6,1.8);this.needsDraw=true;},{passive:false});
     this.ca=Math.cos(this.yaw);this.sa=Math.sin(this.yaw);this.sp=Math.sin(this.pitch);this.cp=Math.cos(this.pitch);this.cx=0;this.cy=0;this.projectionScale=1;
     this.resize();this.tick(0);
   }
   resize() {
     const r=this.canvas.getBoundingClientRect();if(!r.width||!r.height)return;
     // Ultra increases geometric detail and pixel density; a hard pixel budget
     // avoids runaway memory use on 4K displays and high-DPR phones.
     const caps={fps100:.90,boost:1.05,eco:1,auto:r.width<660?1.25:1.55,high:1.9,ultra:2.5};
     const budget={fps100:420000,boost:540000,eco:700000,auto:1150000,high:1700000,ultra:2350000};
     const cap=caps[this.quality]||caps.auto;
     const dpr=Math.max(.65,Math.min(cap,window.devicePixelRatio||1,Math.sqrt((budget[this.quality]||budget.auto)/(r.width*r.height))*this.adaptiveScale));
     const w=Math.max(1,Math.round(r.width*dpr)),h=Math.max(1,Math.round(r.height*dpr));
     if(this.canvas.width!==w||this.canvas.height!==h){this.canvas.width=w;this.canvas.height=h;}
     this.dpr=dpr;this.w=w;this.h=h;this.ctx.imageSmoothingEnabled=true;
     this.ctx.imageSmoothingQuality=this.quality==='ultra'?'high':'medium';this.terrainCacheKey='';this.needsDraw=true;
   }
   reset(){this.yaw=.65;this.pitch=.68;this.zoom=1;this.needsDraw=true;}
   setEnv(data){this.weather=data.weather_mode;this.day=data.day_phase;this.irrigation=data.management.irrigation_intensity_pct;this.drainage=data.management.drainage_intensity_pct;this.zones=data.zones.map(z=>z.stress_index);this.needsDraw=true;}
   terrain(x,z) {return .15*Math.sin(1.0*x)+.12*Math.cos(z*1.42)+.055*Math.sin(x*1.8+z*1.3);}
   routePoint(t){const v=clamp(t,0,1)*(route.length-1),i=Math.min(route.length-2,Math.floor(v)),a=v-i;return [mix(route[i][0],route[i+1][0],a)*10-5,mix(route[i][1],route[i+1][1],a)*7-3.5];}
   project(p) {
     let [x,y,z]=p;
     // Transform rover-local solids around the current route tangent (drawRover only).
     if(this.roverTransform){const q=this.roverTransform,dx=x-q.x,dz=z-q.z;x=q.x+dx*q.c-dz*q.s;z=q.z+dx*q.s+dz*q.c;}
     // Trigonometric camera coefficients are updated once per draw, not per mesh vertex.
     const rx=x*this.ca-z*this.sa,rz=x*this.sa+z*this.ca;
     const denom=clamp(1+.045*rz,.5,1.7),scale=this.projectionScale/denom;
     return {x:this.cx+rx*scale,y:this.cy+(rz*this.sp-y*this.cp)*scale,depth:rz};
   }
   polygon(points,fill,stroke=null,width=1){const ctx=this.ctx,proj=points.map(p=>this.project(p));ctx.beginPath();proj.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.lineWidth=width*this.dpr;ctx.strokeStyle=stroke;ctx.stroke();}}
   line(points,color='#34f6d6',width=1,dash=[]){if(points.length<2)return;const ctx=this.ctx;ctx.beginPath();points.map(p=>this.project(p)).forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.strokeStyle=color;ctx.lineWidth=width*this.dpr;ctx.setLineDash(dash.map(d=>d*this.dpr));ctx.stroke();ctx.setLineDash([]);}
   dot(point,r=4,color='#7effdf'){const p=this.project(point),ctx=this.ctx;ctx.beginPath();ctx.arc(p.x,p.y,r*this.dpr,0,Math.PI*2);ctx.fillStyle=color;ctx.shadowBlur=this.bloom?r*2*this.dpr:0;ctx.shadowColor=color;ctx.fill();ctx.shadowBlur=0;}
   label(point,text,color='#cffcf1',fs=11){const p=this.project(point),ctx=this.ctx;ctx.font=`${fs*this.dpr}px ui-monospace,Consolas,monospace`;ctx.fillStyle=color;ctx.fillText(text,p.x+9*this.dpr,p.y-7*this.dpr);}
   box(x,z,w,d,height,y0,fill,top,stroke='#2ce9cf44'){
     const p=[[x-w/2,y0,z-d/2],[x+w/2,y0,z-d/2],[x+w/2,y0,z+d/2],[x-w/2,y0,z+d/2]],q=p.map(t=>[t[0],t[1]+height,t[2]]);
     const faces=[];for(let i=0;i<4;i++){const ps=[p[i],p[(i+1)%4],q[(i+1)%4],q[i]];faces.push({depth:ps.reduce((a,v)=>a+this.project(v).depth,0)/4,ps,fill});}
     faces.sort((a,b)=>a.depth-b.depth).forEach(f=>this.polygon(f.ps,f.fill,stroke,.6));this.polygon(q,top,stroke,.8);
   }
   healthColor(stress) {return stress>=67?'#FF0055':stress>=36?'#FFB700':'#00FF66';}
   // Smooth, illustrative color interpolation. Never call this a calibrated NDVI/thermal layer.
   tileColor(x,z,zone) {
     if(this.overlay==='topography'){
       const h=this.terrain(x,z);const t=clamp((h+.33)/.67,0,1);
       return t<.5?blend('#112c68','#26818b',t*2):blend('#26818b','#7ba48b',(t-.5)*2);
     }
     if(this.overlay==='thermal'){
       const pseudo=clamp(.5+.35*Math.sin(x*.91+z*1.3)+.16*Math.cos(z*2.3-x*.4),0,1);
       return pseudo<.5?blend('#127fa9','#FFB700',pseudo*2):blend('#FFB700','#FF0055',(pseudo-.5)*2);
     }
     if(this.overlay==='canopy'){
       const cover=clamp(.5+.25*Math.sin(x*1.3)+.22*Math.cos(z*1.12),0,1);
       return blend('#21444f','#00FF66',cover);
     }
     if(this.overlay==='irrigation'){
       const wet=this.weather==='surge' || (this.irrigation>65&&Math.abs(z)<1);
       return wet?'#2a7896':'#174b69';
     }
     const scaled=clamp((x+5)/10*3-.5,0,2),lo=Math.floor(scaled),hi=Math.min(2,lo+1);
     const stress=mix(this.zones[lo],this.zones[hi],scaled-lo);
     return stress<36?blend('#00FF66','#FFB700',stress/36):stress<67?blend('#FFB700','#FF0055',(stress-36)/31):'#FF0055';
   }
   drawBackground(){const c=this.ctx;if(this.transparent){c.clearRect(0,0,this.w,this.h);return;}const g=c.createLinearGradient(0,0,0,this.h);g.addColorStop(0,this.day==='night'?'#010a1c':'#06182b');g.addColorStop(1,this.day==='night'?'#07132a':'#073c45');c.fillStyle=g;c.fillRect(0,0,this.w,this.h);
     c.strokeStyle='rgba(76,234,230,.07)';c.lineWidth=this.dpr;for(let x=0;x<this.w;x+=44*this.dpr){c.beginPath();c.moveTo(x,0);c.lineTo(x,this.h);c.stroke();}for(let y=0;y<this.h;y+=44*this.dpr){c.beginPath();c.moveTo(0,y);c.lineTo(this.w,y);c.stroke();}
     const glow=c.createRadialGradient(this.w*.5,this.h*.52,10,this.w*.5,this.h*.52,this.w*.6);glow.addColorStop(0,'#20a5991c');glow.addColorStop(1,'#00000000');c.fillStyle=glow;c.fillRect(0,0,this.w,this.h);
   }
   drawTerrain(){const compact=this.quality==='eco'||this.quality==='boost'||this.quality==='fps100'||this.quality==='fps100'||(this.quality==='auto'&&this.w<900),ultra=this.quality==='ultra';const N=compact?12:ultra?(this.dynamicDetail<1?21:30):this.quality==='high'?27:22,M=compact?9:ultra?(this.dynamicDetail<1?15:21):this.quality==='high'?19:16,tiles=[];
     for(let i=0;i<N;i++)for(let j=0;j<M;j++){
       const x=-5+i*10/N,z=-3.5+j*7/M,x2=x+10/N,z2=z+7/M,cx=(x+x2)/2,cz=(z+z2)/2;
       const zone=clamp(Math.floor((cx+5)/10*3),0,2),h=(xx,zz)=>this.terrain(xx,zz);
       const pts=[[x,h(x,z),z],[x2,h(x2,z),z],[x2,h(x2,z2),z2],[x,h(x,z2),z2]];
       tiles.push({pts,depth:pts.reduce((a,p)=>a+this.project(p).depth,0)/4,color:this.tileColor(cx,cz,zone),zone});
     }
     tiles.sort((a,b)=>a.depth-b.depth);
     this.ctx.save();if(this.transparent)this.ctx.globalAlpha=ultra?.25:.42;
     tiles.forEach(t=>{
       const p0=this.project(t.pts[0]),p2=this.project(t.pts[2]);
       const grad=this.ctx.createLinearGradient(p0.x,p0.y,p2.x+0.01,p2.y+0.01);
       const mid=t.pts.reduce((a,v)=>[a[0]+v[0]/4,a[1]+v[1]/4,a[2]+v[2]/4],[0,0,0]);
       grad.addColorStop(0,this.tileColor(mid[0]-.18,mid[2]-.18,t.zone));
       grad.addColorStop(1,this.tileColor(mid[0]+.18,mid[2]+.18,t.zone));
       this.polygon(t.pts,grad,ultra?'rgba(33,244,215,.085)':'rgba(33,244,215,.13)',ultra?.25:.45);
     });
     this.ctx.restore();
     if(ultra){
       // Closely spaced relief/planting rows are procedural geometry, not elevation data.
       for(let k=0;k<22;k++){
         const z=-3.35+k*.31,pts=[];
         for(let q=0;q<=32;q++){
           const x=-5+q*10/32;
           pts.push([x,this.terrain(x,z)+.025,z]);
         }
         this.line(pts,k%3===0?'#aaffbb51':'#b9f8b22e',.45);
       }
     }
     // Synthetic soil strata visible as layered slices below an illustrative field boundary.
     const edges=[[-5,-3.5],[5,-3.5],[5,3.5],[-5,3.5]];
     for(let k=0;k<4;k++){const a=edges[k],b=edges[(k+1)%4];this.polygon([[a[0],this.terrain(...a),a[1]],[b[0],this.terrain(...b),b[1]],[b[0],-.62,b[1]],[a[0],-.62,a[1]]],k%2?'#132b36':'#173c47','#28bba955',.8);this.line([[a[0],-.25,a[1]],[b[0],-.25,b[1]]],'#5aa58b88',.6);this.line([[a[0],-.48,a[1]],[b[0],-.48,b[1]]],'#caaf6866',.5);}
     this.line(edges.map(([x,z])=>[x,this.terrain(x,z)+.035,z]).concat([[-5,this.terrain(-5,-3.5)+.035,-3.5]]),'#71fbe4',2);
     for(let a=0;a<3;a++)this.line([[ -5+10*a/3,.37,-3.4],[-5+10*a/3,.37,3.35]],'#b9fff1b3',1.4,[3,3]);
     // Crop canopies are illustrative models, never remotely sensed.
     for(let row=0;row<(compact?7:ultra?(this.dynamicDetail<1?8:12):9);row++)for(let col=0;col<(compact?16:ultra?(this.dynamicDetail<1?21:31):24);col++){
       const x=-4.75+col*(compact?.6:ultra?.305:.4)+((this.motion&&this.quality!=='eco')?.025*Math.sin(this.time*1.7+row*1.3+col*.31):0),z=-3.15+row*(compact?1.05:ultra?.53:.76);
       if(Math.abs(z)<.27 || (x>-.2&&x<.15))continue;
       const h=this.terrain(x,z),zone=clamp(Math.floor((x+5)/10*3),0,2);
       const stem=.11+.035*Math.sin(row+col*3),shade=this.day==='night'?'#4d8f93':this.scenario==='C'?'#a7f17b':this.scenario==='B'?'#8de4a4':'#87bd7c';
       // Sun-angle-driven *illustrative* planar shadow, not verified solar geometry.
       const shadowLen=.12+.54*(1-this.sunAngle/90);
       this.line([[x,h+.018,z],[x-shadowLen,h+.016,z+.12]],this.day==='night'?'#04101b88':'#0614218c',1.7);
       this.line([[x,h+.02,z],[x,h+.17+stem,z]],shade,.7);
       if((row+col)%3===0)this.dot([x,h+.19+stem,z],ultra?1.8:1.3,this.healthColor(this.zones[zone]));
       if(ultra){
         const sway=this.motion?.028*Math.sin(this.time*1.8+row*.8+col*.23):0;
         // Small paired leaf meshes catch the illustrative sun, not spectral reflectance.
         this.polygon([[x,h+.15,z],[x-.075+sway,h+.22,z-.043],[x,h+.25,z]],'#3de7829c');
         this.polygon([[x,h+.19,z],[x+.07+sway,h+.25,z+.05],[x,h+.27,z]],'#adffb78a');
       }
     }
     // Synthetic irrigation / drainage channels.
     this.line([[-4.95,.07,0],[-2,.12,.12],[1,.06,.15],[4.95,.04,.02]],'#4ceafa',3);
     this.line([[.12,.15,-3.3],[.16,.12,0],[.2,.08,3.3]],'#22c7fbbb',2);
   }
   drawTerrainCached(){
     // Most Canvas2D cost was repainting hundreds of static crop meshes on every frame.
     // Cache the static farm plate; only refresh twice a second for subtle crop sway,
     // or immediately when camera, scenario, lighting or soil context changes.
     if (!this.terrainCacheCtx) { this.drawTerrain(); return; }
     const bucket=this.motion&&this.quality!=='fps100'?Math.floor(this.time*2):0;
     const key=[this.w,this.h,this.quality,this.dynamicDetail,this.yaw.toFixed(3),
       this.pitch.toFixed(3),this.zoom.toFixed(3),this.overlay,this.scenario,
       this.day,this.sunAngle,this.zones.join(','),bucket].join('|');
     if(key!==this.terrainCacheKey){
       if(this.terrainCache.width!==this.w||this.terrainCache.height!==this.h){
         this.terrainCache.width=this.w;this.terrainCache.height=this.h;
       }
       const current=this.ctx;this.ctx=this.terrainCacheCtx;
       try { this.ctx.clearRect(0,0,this.w,this.h);this.drawTerrain(); }
       finally { this.ctx=current; }
       this.terrainCacheKey=key;
     }
     this.ctx.drawImage(this.terrainCache,0,0);
   }
   drawWind(){if(this.day==='night')return;for(let i=0;i<(this.quality==='ultra'?11:this.quality==='fps100'?3:5);i++){const x=-4.2+i*(this.quality==='ultra'?.82:1.75),z=-2.9+i*(this.quality==='ultra'?.24:.35),h=this.terrain(x,z)+.65;const slide=this.motion?.18*Math.sin(this.time*1.6+i):0;this.line([[x+slide,h,z],[x+.6+slide,h+.12,z-.16],[x+.75+slide,h+.18,z-.19]],'#72e9e696',1.1);this.line([[x+.57+slide,h+.19,z-.21],[x+.75+slide,h+.18,z-.19],[x+.6+slide,h+.08,z-.22]],'#72e9e696',1.1);}}
   drawRoute(){const pts=route.map(([u,v])=>{const x=u*10-5,z=v*7-3.5;return[x,this.terrain(x,z)+.23,z];});this.line(pts,'#00F0FF',2.5,[7,5]);
     if(this.motion){for(let k=0;k<(this.quality==='fps100'?4:8);k++){const denom=this.quality==='fps100'?4:8;const t=(this.time*.095+k/denom)%1;
       const [px,pz]=this.routePoint(t);this.dot([px,this.terrain(px,pz)+.25,pz],k%3===0?3:2,'#81fffb');}}pts.slice(0,-1).forEach((p,i)=>{this.dot(p,4,i===0?'#95ffa5':'#60faff');this.label([p[0],p[1]+.18,p[2]],i===0?'BASE':'P-0'+i,'#affff5',10);});
     if(this.playing){const p=this.routePoint(this.progress),y=this.terrain(p[0],p[1])+.32;this.dot([p[0],y,p[1]],7,'#00F0FF');}
   }
   drawLidar(){const grid=this.quality==='fps100'?5:8;for(let i=0;i<grid;i++)for(let j=0;j<grid;j++){const x=-5+i*10/grid,z=-3.5+j*7/grid,hit=(i+j)%11===2,q=[[x,.18,z],[x+10/grid,.18,z],[x+10/grid,.18,z+7/grid],[x,.18,z+7/grid]];this.polygon(q,hit?'#f05c4e83':'#3be9d315',hit?'#ff7869':'#3cf4db61',.8);}}
   drawBoxMesh(x,z,w,d,ht,y,colors){this.box(x,z,w,d,ht,y,colors[0],colors[1],colors[2]||'#9effea');}
   drawRover(){const [x,z]=this.routePoint(this.progress),h=this.terrain(x,z)+.16;
     const next=this.routePoint(Math.min(.9999,this.progress+.002)),prev=this.routePoint(Math.max(0,this.progress-.002));
     const heading=Math.atan2(next[1]-prev[1],next[0]-prev[0]);
     this.roverTransform={x,z,c:Math.cos(heading),s:Math.sin(heading)};
     // Four all-terrain wheel proxy solids with rotating cyan hub rings.
     for(const dx of [-.54,.54])for(const dz of [-.31,.31]){
       this.box(x+dx,z+dz,.29,.27,.27,h-.12,'#162b35','#294453','#32c9b699');
       this.dot([x+dx,h+.01,z+dz],3,'#4af5ed');
       // Pixel-space wheel hubs/spokes rotate in sync with the simulated drive.
       const c=this.ctx,center=this.project([x+dx,h+.01,z+dz]),angle=this.time*this.speed*5.6;
       c.save();c.strokeStyle='#04f0ff';c.globalAlpha=.9;c.lineWidth=1.1*this.dpr;
       c.beginPath();c.arc(center.x,center.y,6*this.dpr,0,Math.PI*2);c.stroke();
       for(let a=0;a<3;a++){const q=angle+a*Math.PI*2/3;
         c.beginPath();c.moveTo(center.x,center.y);c.lineTo(center.x+5*this.dpr*Math.cos(q),center.y+5*this.dpr*Math.sin(q));c.stroke();}c.restore();
     }
     this.drawBoxMesh(x,z,1.2,.73,.34,h+.05,['#547e8c','#b4f1dd','#3bfedb']);
     this.drawBoxMesh(x+.02,z,.88,.6,.1,h+.39,['#103a4b','#173952','#58fbda']);
     if(this.quality==='ultra'){
       // Extra structural CAD-style proxy geometry, panels and light elements.
       this.drawBoxMesh(x-.08,z,.81,.59,.04,h+.52,['#102b3a','#23617c','#8fe9e7']);
       this.drawBoxMesh(x-.26,z,.28,.37,.08,h+.55,['#0a2536','#155778','#59edff']);
       this.drawBoxMesh(x+.32,z,.18,.43,.10,h+.52,['#112b3b','#2b6071','#8ef6ff']);
       for(let i=0;i<9;i++)this.line([[x-.43+i*.09,h+.645,z-.25],[x-.43+i*.09,h+.645,z+.23]],'#45a6c8a0',.7);
       for(const side of [-1,1]){
         this.line([[x-.46,h+.12,z+side*.374],[x+.47,h+.12,z+side*.374]],'#68eeff',1.7);
         this.dot([x+.54,h+.29,z+side*.27],4.2,this.day==='night'?'#b3faff':'#7afef5');
         const front=this.project([x+.55,h+.29,z+side*.27]),c=this.ctx;
         c.save();c.globalCompositeOperation='screen';
         const beam=c.createRadialGradient(front.x,front.y,1,front.x,front.y,27*this.dpr);
         beam.addColorStop(0,'#bafffff0');beam.addColorStop(.18,'#00f0ff80');beam.addColorStop(1,'#00f0ff00');
         c.fillStyle=beam;c.fillRect(front.x-27*this.dpr,front.y-27*this.dpr,54*this.dpr,54*this.dpr);c.restore();
       }
       // Satellite receiver and antenna uplink geometry are concept illustrations.
       this.line([[x-.24,h+.59,z+.19],[x-.29,h+1.17,z+.19]],'#d0fff4',1.6);
       this.dot([x-.29,h+1.2,z+.19],3,'#42edff');
     }
     for(let i=0;i<5;i++)this.line([[x-.32+i*.16,h+.51,z-.22],[x-.32+i*.16,h+.51,z+.22]],'#35bfd9',.9);
     this.line([[x+.26,h+.5,z],[x+.26,h+1.05,z]],'#95f9e9',2.5);
     this.drawBoxMesh(x+.26,z,.3,.35,.17,h+1.02,['#386377','#a7e3f2','#84eeff']);
     this.dot([x+.27,h+1.13,z+.20],3,'#5eebff');
     this.line([[x-.35,h+.5,z-.18],[x-.65,h+.25,z-.45],[x-.68,h-.10,z-.42]],'#98dfed',2.2);
     this.line([[x-.66,h-.1,z-.45],[x-.74,h-.19,z-.45]],'#c8f2e6',2);
     this.dot([x-.69,h-.19,z-.45],3,this.layer==='diagnostic'?'#f7a55d':'#7cf7cd');
     if(this.layer==='diagnostic'){
       this.dot([x+.54,h+.26,z+.3],11,'#f77b51');this.dot([x-.54,h+.26,z-.3],8,'#ffc36c');
       this.line([[x+.52,h+.28,z+.3],[x+1.45,h+1.02,z+.5]],'#ff8964',1.8);this.label([x+1.45,h+1.05,z+.5],'MOTOR HEAT • SIM', '#ffc6a0',10);
       this.label([x-.9,h+.8,z-.45],'DUST / SLIP • SIM', '#ffe3ad',10);
     }
     if(this.layer==='navigation'){
       this.line([[x,h+.5,z],[x,h+1.7,z]],'#74ecfa80',1,[3,3]);
       for(let i=0;i<4;i++){const r=.25+i*.22,a=(i*.8+this.progress*8),p=[x+Math.cos(a)*r,h+.12,z+Math.sin(a)*r];this.dot(p,2,'#96efff');}
     }
     if(this.progress>.01&&this.progress<.98){this.dot([x,h+.14,z],4,'#b5ff9a');}
     this.roverTransform=null;
     // At 1/4 route intervals, illustrate a point measurement and radio uplink.
     if(this.motion&&this.playing){
       const phase=(this.progress*4)%1,distance=Math.min(phase,1-phase);
       if(distance<.16){const sample=this.project([x,h+.07,z]),c=this.ctx;
         const radius=(9+(1-distance/.16)*22)*this.dpr;
         c.save();c.strokeStyle='#00ff66';c.lineWidth=1.7*this.dpr;c.globalAlpha=.7*(1-distance/.16);
         c.beginPath();c.ellipse(sample.x,sample.y,radius,radius*.30,0,0,Math.PI*2);c.stroke();c.restore();
       }
     }
   }

   // Procedural orbital marker + optical sweep. This is ONLY a demo animation;
   // it does not visualize a real orbit, beam, scan or satellite raster.
   drawSatellite(){
     if(!this.motion)return;
     const c=this.ctx,d=this.dpr;
     const u=(Math.sin(this.time*.22)+1)/2,xx=(.12+.75*u)*this.w,yy=(.115+.025*Math.sin(this.time*.47))*this.h;
     const farm=this.project([2,this.terrain(2,-1)+.4,-1]);
     c.save();c.lineWidth=1.4*d;c.strokeStyle='#00f0ffbb';c.globalAlpha=.7;
     c.beginPath();c.moveTo(xx,yy);c.lineTo(farm.x-24*d,farm.y);c.lineTo(farm.x+24*d,farm.y);c.closePath();
     c.fillStyle='#00f0ff0a';c.fill();c.stroke();
     c.shadowColor='#00F0FF';c.shadowBlur=12*d;c.strokeStyle='#80efff';
     c.strokeRect(xx-9*d,yy-4*d,18*d,8*d);c.fillStyle='#167ea8';
     c.fillRect(xx-25*d,yy-7*d,13*d,13*d);c.fillRect(xx+12*d,yy-7*d,13*d,13*d);
     c.fillStyle='#a3ffff';c.beginPath();c.arc(xx,yy,2.5*d,0,2*Math.PI);c.fill();
     c.shadowBlur=0;c.font=`${9*d}px Consolas, monospace`;c.fillStyle='#80d5e8';c.fillText('SIMULATED SATELLITE LINK',xx-20*d,yy-14*d);
     c.restore();
   }
   drawWeatherEffects(){
     if(!this.motion)return;
     const c=this.ctx,d=this.dpr,amount=(this.quality==='eco'||this.quality==='boost'||this.quality==='fps100')?15:this.quality==='ultra'?130:this.quality==='high'?62:37;
     c.save();
     if(this.weather==='surge'){
       c.strokeStyle='#72dfff99';c.lineWidth=1.2*d;
       for(let i=0;i<amount;i++){
         const x=((i*149.29+this.time*120*d)%(this.w+50*d))-25*d;
         const y=((i*83.23+this.time*270*d)%(this.h+60*d))-30*d;
         c.beginPath();c.moveTo(x,y);c.lineTo(x-4*d,y+15*d);c.stroke();
       }
     } else if(this.weather==='drought'){
       c.fillStyle='#ffb7037b';
       for(let i=0;i<amount;i++){
         const x=((i*157.18+this.time*25*d)%(this.w+20*d));
         const y=((i*71.3-this.time*19*d)%(this.h+20*d)+this.h+20*d)%(this.h+20*d);
         c.fillRect(x,y,1.8*d,1.8*d);
       }
     }
     // Flowing pulses inside an illustrative irrigation line, not actual water routing.
     if(this.irrigation>10){for(let i=0;i<8;i++){
       const x=-4.6+((this.time*.8+i*1.3)%9.4),z=.1;
       this.dot([x,this.terrain(x,z)+.28,z],1.8,'#42cbff');
     }}
     c.restore();
   }
   drawSkyEffects(){
     if(!this.motion)return;
     const c=this.ctx,d=this.dpr,t=this.time;
     c.save();
     // Geometric target reticle scans synthetic projected farm geometry.
     const x=this.w*(.50+.17*Math.sin(t*.45)),y=this.h*(.37+.17*Math.cos(t*.3));
     c.strokeStyle='#00f0ff7a';c.lineWidth=d;
     for(let r=0;r<3;r++){
       const radius=(13+r*15+(t*9)%12)*d;
       c.globalAlpha=.28+(1-r*.08);c.beginPath();c.ellipse(x,y,radius,radius*.32,0,0,Math.PI*2);c.stroke();
     }
     c.restore();
   }
   // Ultra graphics effects operate only on PROCEDURAL scenes. No data provenance is inferred.
   drawUltraAtmosphere(){
     if(this.quality!=='ultra')return;
     const c=this.ctx,w=this.w,h=this.h,t=this.time,d=this.dpr;
     c.save();c.globalCompositeOperation='screen';
     const sunX=this.day==='night'?.78:.77,sunY=this.day==='night'?.14:.23;
     const sunlight=c.createRadialGradient(w*sunX,h*sunY,0,w*sunX,h*sunY,w*.41);
     sunlight.addColorStop(0,this.day==='night'?'#62caff4c':'#ffd79259');
     sunlight.addColorStop(.3,this.day==='night'?'#00dcff18':'#ffc27a1c');
     sunlight.addColorStop(1,'#00000000');c.fillStyle=sunlight;c.fillRect(0,0,w,h);
     const haze=c.createLinearGradient(0,h*.45,0,h*.90);
     haze.addColorStop(0,'#00ffc400');haze.addColorStop(.45,'#00edb30b');haze.addColorStop(1,'#00ffc400');
     c.fillStyle=haze;c.fillRect(0,h*.45,w,h*.45);
     c.restore();
   }
   drawUltraRouteGlow(){
     if(this.quality!=='ultra')return;
     const c=this.ctx,d=this.dpr,pts=route.map(([u,v])=>{const x=u*10-5,z=v*7-3.5;return this.project([x,this.terrain(x,z)+.22,z]);});
     c.save();c.globalCompositeOperation='screen';c.lineCap='round';
     const p=(width,stroke)=>{c.beginPath();pts.forEach((point,i)=>i?c.lineTo(point.x,point.y):c.moveTo(point.x,point.y));c.lineWidth=width*d;c.strokeStyle=stroke;c.stroke();};
     p(10,'#00ebff18');p(5,'#00ffa336');p(1.3,'#a9fffa8c');
     const q=(this.time*.078)%1,pos=this.routePoint(q),p2=this.project([pos[0],this.terrain(...pos)+.28,pos[1]]);
     const halo=c.createRadialGradient(p2.x,p2.y,1,p2.x,p2.y,25*d);halo.addColorStop(0,'#e0ffff');halo.addColorStop(.2,'#00f0ff99');halo.addColorStop(1,'#00f0ff00');
     c.fillStyle=halo;c.fillRect(p2.x-25*d,p2.y-25*d,50*d,50*d);c.restore();
   }
   drawUltraRoverShadow(){
     if(this.quality!=='ultra')return;
     const [x,z]=this.routePoint(this.progress),h=this.terrain(x,z),p=this.project([x,h+.012,z]);const c=this.ctx;
     const gradient=c.createRadialGradient(0,0,1,0,0,70*this.dpr);
     gradient.addColorStop(0,'#001319ae');gradient.addColorStop(.5,'#00151d5b');gradient.addColorStop(1,'#00151d00');
     c.save();c.translate(p.x,p.y);c.scale(1,.31);c.fillStyle=gradient;
     c.beginPath();c.arc(0,0,70*this.dpr,0,Math.PI*2);c.fill();c.restore();
   }
   drawUltraPostFX(){
     if(this.quality!=='ultra'||!this.postFX)return;
     const c=this.ctx,w=this.w,h=this.h,d=this.dpr;
     c.save();
     const vignette=c.createRadialGradient(w*.50,h*.48,w*.19,w*.50,h*.48,w*.79);
     vignette.addColorStop(0,'#00101900');vignette.addColorStop(.72,'#00101900');vignette.addColorStop(1,'#0010197d');
     c.fillStyle=vignette;c.fillRect(0,0,w,h);
     c.globalCompositeOperation='screen';
     c.strokeStyle='#36ffc816';c.lineWidth=d*.65;
     for(let i=0;i<7;i++){
       const y=(h*.19+i*h*.115+(this.motion?Math.sin(this.time*.48+i)*2*d:0));
       c.beginPath();c.moveTo(w*.29,y);c.lineTo(w*.94,y+h*.009);c.stroke();
     }
     c.restore();
   }
   drawHUD(){const c=this.ctx,w=this.w,h=this.h,fs=(n)=>`${n*this.dpr}px ui-monospace,Consolas,monospace`;
     c.fillStyle='#d1fff0';c.font=fs(12);c.fillText('AGRIORBIT / DIGITAL TWIN • SYNTHETIC',17*this.dpr,22*this.dpr);
     c.fillStyle='#7fdad3';c.font=fs(10);c.fillText(`SCENARIO ${this.scenario}   ${this.weather.toUpperCase()}   ${this.overlay.toUpperCase()} • SYNTHETIC`,17*this.dpr,40*this.dpr);
     c.fillStyle='#ffc479';c.fillText('ANIMATED SIMULATION • NO ACTUATOR CONTROL',17*this.dpr,h-16*this.dpr);
     c.textAlign='right';c.fillStyle='#a8fff1';c.fillText(`CAM ${Math.round(this.yaw*57.3)}°  /  ${Math.round(this.pitch*57.3)}°`,w-16*this.dpr,22*this.dpr);c.textAlign='left';
     const colors=['#00FF66','#FFB700','#FF0055'];c.font=fs(9);for(let i=0;i<3;i++){c.fillStyle=colors[i];c.fillRect(w-(110-i*1)*this.dpr,h-(72-i*17)*this.dpr,8*this.dpr,8*this.dpr);c.fillStyle='#e0fff2';c.fillText(['LOWER','MODERATE','CRITICAL'][i],w-94*this.dpr,h-(65-i*17)*this.dpr);}
   }
   draw(){if(!this.w||!this.h)return;
     // Cache the camera matrix once for every projection in this draw call.
     this.ca=Math.cos(this.yaw);this.sa=Math.sin(this.yaw);this.sp=Math.sin(this.pitch);this.cp=Math.cos(this.pitch);
     this.cx=this.w*.50;this.cy=this.h*.56;this.projectionScale=this.zoom*Math.min(this.w/12.4,this.h/8.8);
     this.drawBackground();this.drawUltraAtmosphere();this.drawTerrainCached();this.drawWind();
     if(this.layer==='navigation')this.drawLidar();
     this.drawRoute();this.drawUltraRouteGlow();this.drawSkyEffects();this.drawSatellite();
     this.drawUltraRoverShadow();this.drawRover();this.drawWeatherEffects();this.drawUltraPostFX();this.drawHUD();this.needsDraw=false;
     this.frameCount++;
   }
   tick(now){if(this.disposed)return;if(!this.last)this.last=now;const dt=clamp((now-this.last)/1000,0,.07);this.last=now;
     const visible=this.canvas.getClientRects().length>0&&!document.hidden;
     if(visible){
       if(this.motion){this.time+=dt;this.needsDraw=true;}
       if(this.autoOrbit&&this.motion&&!this.drag){this.yaw+=dt*.12;this.needsDraw=true;}
       if(this.playing){
         this.progress=clamp(this.progress+dt*this.speed/23,0,1);
         if(this.progress>=1){if(this.loop)this.progress=0;else{this.playing=false;this.cinematic=false;}}
         this.needsDraw=true;if(!this.lastProgressSignal||now-this.lastProgressSignal>75||this.progress>=1){this.lastProgressSignal=now;this.onProgress?.(this.progress);}
         if(this.cinematic){const stage=Math.min(3,Math.floor(this.progress*4));
           if(stage!==this.stage){this.stage=stage;this.onCinematicStage?.(stage);}}
       }
       const interval=this.quality==='fps100'?this.drawIntervalMs:this.quality==='boost'?15:this.quality==='eco'?65:this.quality==='ultra'?17:25;
       if(this.needsDraw&&now-this.lastDraw>=interval){
         this.lastDraw=now;
         const start=performance.now();this.draw();
         this.lastDrawMs=performance.now()-start;
         this.drawMsEma=this.drawMsEma?this.drawMsEma*.86+this.lastDrawMs*.14:this.lastDrawMs;
       }
       if(!this.fpsAt)this.fpsAt=now;
       if(now-this.fpsAt>=1000){
         const seconds=(now-this.fpsAt)/1000;
         this.fps=Math.round(this.frameCount/seconds);this.frameCount=0;this.fpsAt=now;
         this.onFrameStats?.(this.fps, {drawMs:Number(this.drawMsEma.toFixed(1)),target:this.quality==='fps100'?100:null,refreshLimit:true,megapixels:Number((this.w*this.h/1e6).toFixed(2)),scale:this.adaptiveScale});
         // Performance is measured, not promised. Lower real-time render cost if slow.
         if((this.quality==='ultra'||this.quality==='boost') && this.motion && now-this.lastAdapt>2700){
           if(this.fps>0&&this.fps<32){this.lowFpsStreak++;this.highFpsStreak=0;}
           else if(this.fps>48){this.highFpsStreak++;this.lowFpsStreak=0;}
           else {this.lowFpsStreak=0;this.highFpsStreak=0;}
           if(this.lowFpsStreak>=2){
             this.adaptiveScale=Math.max(this.quality==='boost'?.72:.66,this.adaptiveScale*.84);
             this.dynamicDetail=.72;
             this.resize();this.lastAdapt=now;this.lowFpsStreak=0;
           } else if(this.highFpsStreak>=4&&this.adaptiveScale<1){
             this.adaptiveScale=Math.min(1,this.adaptiveScale*1.10);
             if(this.adaptiveScale>.95)this.dynamicDetail=1;
             this.resize();this.lastAdapt=now;this.highFpsStreak=0;
           }
         }
         // 100-FPS *target*: adapt based on measured render cost, not a fake FPS counter.
         // A 60-Hz display will still schedule approximately 60 requestAnimationFrame callbacks.
         if(this.quality==='fps100' && this.motion && now-this.lastAdapt>2200){
           if(this.drawMsEma>8.8){
             this.adaptiveScale=Math.max(.60,this.adaptiveScale*.89);
             this.dynamicDetail=.72;
             this.resize();this.lastAdapt=now;
           } else if(this.drawMsEma<5.2 && this.adaptiveScale<1){
             this.adaptiveScale=Math.min(1,this.adaptiveScale*1.045);
             this.resize();this.lastAdapt=now;
           }
         }
       }
     }else{this.fpsAt=now;this.frameCount=0;}
     // Hidden views do not need a full requestAnimationFrame loop.
     if(visible) this.raf=requestAnimationFrame(t=>this.tick(t));
     else this.raf=setTimeout(()=>this.tick(performance.now()),240);
   }
 }
 window.AgriOrbitHologram=Hologram;
})();
